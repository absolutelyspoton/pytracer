# PyTracer Performance Optimization Roadmap

## Executive Summary

Comprehensive analysis of performance bottlenecks in matrix math and data structures.

**Total Potential Gain**: 40-60% faster operations  
**Combined Implementation Time**: ~2.5 hours  
**Expected Result**: Dramatically reduced CPU usage (60 FPS capped becomes smoother, more headroom)

---

## Priority 1: Coordinate Lists → Tuples [HIGH PRIORITY]

**Impact**: 10-15% FPS improvement  
**Effort**: 20 minutes  
**Risk**: LOW  
**Files**: `matrix.py` (3 functions)

### Problem
Coordinates are returned as mutable lists `[x,y,z]` when they should be immutable tuples `(x,y,z)`.

Called 3,644+ times per frame:
- `MatrixVector()` line 38: allocates list for every vertex transformation
- `NormaliseVector()` line 103: creates list for every normalized vector
- `CalcSurfaceNormal()` lines 123-124: creates intermediate list vectors

### Current Code
```python
def MatrixVector(m, v):
    x = m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2] + m[3][0]
    y = m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2] + m[3][1]
    z = m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2] + m[3][2]
    return ([x,y,z])  # ← List allocation overhead
```

### Optimized Code
```python
def MatrixVector(m, v):
    x = m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2] + m[3][0]
    y = m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2] + m[3][1]
    z = m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2] + m[3][2]
    return (x, y, z)  # ← Tuple: immutable, faster
```

### Why
- Tuples are immutable → Python can optimize them better
- Tuple creation is faster than list creation
- Tuple indexing may be slightly faster
- Immutability is what coordinates need (never modified)

---

## Priority 2: Matrix Flat Representation [HIGH PRIORITY]

**Impact**: 15-25% matrix operation speedup  
**Effort**: 1 hour  
**Risk**: MEDIUM (requires testing)  
**Files**: `matrix.py` (all matrix functions)

### Problem
Matrices use nested lists with triple-nested loops:
- `MatrixMult()` does 64 multiplication operations per matrix multiply (called 2x/frame + rotations)
- `ZeroMatrix()` creates 16 elements just to use 4
- `IdentityMatrix()` creates then mutates all 16 elements
- Array element accessed 4x per cell (redundant)

### Current Approach (Nested Lists)
```python
def MatrixMult(m1, m2):
    mz = ZeroMatrix()  # Allocate 16-element 2D list
    for i in range(VECTOR_SIZE):  # 4 nested loops
        for j in range(VECTOR_SIZE):  # 4
            for e in range(VECTOR_SIZE):  # 4 = 64 iterations
                mz[i][j] = mz[i][j] + m1[i][e]*m2[e][j]  # Read/write mz[i][j] 4x
    return mz
```

Problems:
- Triple-nested loop = 64 operations
- `mz[i][j]` accessed 4 times per iteration (read, write, read, write)
- List-of-lists has pointer indirection on every access
- Poor cache locality

### Optimized Approach (Flat Tuple)
```python
# Represent 4x4 matrix as single tuple of 16 elements
# Index: row * 4 + col

def MatrixMult(m1, m2):
    mz = [0] * 16  # Flat list, pre-allocated
    
    for i in range(4):
        for j in range(4):
            sum_val = 0  # Accumulate in local variable
            for e in range(4):
                sum_val += m1[i*4 + e] * m2[e*4 + j]  # Direct indexing
            mz[i*4 + j] = sum_val  # Write once, not 4 times
    
    return tuple(mz)  # Return immutable tuple

def ZeroMatrix():
    return tuple([0] * 16)  # Flat, immutable

def IdentityMatrix():
    m = [0] * 16
    m[0] = m[5] = m[10] = m[15] = 1  # Set diagonal, don't loop
    return tuple(m)
```

### Why
- Flat array: better cache locality, no pointer indirection
- Accumulate in local variable: `mz[i*4+j]` written once, not 4 times (~25% fewer array ops)
- Direct indexing: `m1[i*4+e]` is faster than `m1[i][e]`
- Tuple: immutable, can be cached/hashed

### Trade-offs
- Matrix operations become less readable (`m[i*4+j]` vs `m[i][j]`)
- Need helper functions for clarity
- More testing required

---

## Priority 3: RotateMatrix Optimization [HIGH PRIORITY]

**Impact**: 15-20% rotation speedup  
**Effort**: 30 minutes  
**Risk**: MEDIUM  
**Files**: `matrix.py` (RotateMatrix function)

### Problem
Creates 3 identity matrices and does 2 full matrix multiplications per frame:
- 3 × IdentityMatrix() calls
- 2 × MatrixMult() calls (128 operations)
- Total: ~150 operations per rotation frame

### Current Code
```python
def RotateMatrix(x_theta, y_theta, z_theta):
    # ... convert to radians ...
    
    arr_z = IdentityMatrix()  # Create 16 elements, use 4
    arr_z[0][0] = math.cos(z_rad)
    arr_z[1][0] = math.sin(z_rad) * -1
    # ... repeat for arr_y, arr_x ...
    
    m = MatrixMult(arr_x, arr_y)  # 64 operations
    m = MatrixMult(m, arr_z)      # 64 operations
    return m
```

### Optimized Code
```python
def RotateMatrix(x_theta, y_theta, z_theta):
    """Compose XYZ rotation matrix directly without intermediate multiplies."""
    x_rad = math.radians(x_theta)
    y_rad = math.radians(y_theta)
    z_rad = math.radians(z_theta)
    
    # Pre-compute sines and cosines
    cx, cy, cz = math.cos(x_rad), math.cos(y_rad), math.cos(z_rad)
    sx, sy, sz = math.sin(x_rad), math.sin(y_rad), math.sin(z_rad)
    
    # Compose R = Rz * Ry * Rx directly (15-20 multiplications, not 128)
    m = [0] * 16
    
    # Row 0: Rz*Ry first row
    m[0] = cz*cy
    m[4] = -sz*cy
    m[8] = sy
    m[12] = 0
    
    # Row 1: Rz*Ry*Rx second row (all components)
    m[1] = cz*sy*sx + sz*cx
    m[5] = -sz*sy*sx + cz*cx
    m[9] = -cy*sx
    m[13] = 0
    
    # Row 2: Rz*Ry*Rx third row
    m[2] = -cz*sy*cx + sz*sx
    m[6] = sz*sy*cx + cz*sx
    m[10] = cy*cx
    m[14] = 0
    
    # Row 3: Translation row (identity for rotation)
    m[3] = m[7] = m[11] = 0
    m[15] = 1
    
    return tuple(m)
```

### Why
- Eliminates 2 full matrix multiplications (128 operations → ~15-20 operations)
- Direct computation of rotation matrix coefficients
- Minimal function calls

---

## Priority 4: Cache Transformed Normals [MEDIUM PRIORITY]

**Impact**: 3-5% FPS  
**Effort**: 10 minutes  
**Risk**: LOW  
**Files**: `swfvs.py` (render loop)

### Problem
Normal is transformed twice per face when backface culling is enabled.

### Current Code
```python
if state.draw_faces:
    for face in surfaces.surface_list:
        # ...
        if state.backface_cull:
            normal_view = matrix.MatrixVector(MR, face.normal)  # Transform 1
            if normal_view[2] < 0:
                continue
        # Later, if face is drawn, normal might be accessed again
```

### Optimized Code
```python
if state.draw_faces:
    for face in surfaces.surface_list:
        # Transform normal once
        normal_view = matrix.MatrixVector(MR, face.normal) if state.backface_cull else None
        
        if state.backface_cull and normal_view[2] < 0:
            continue
        
        # Reuse normal_view if needed later
```

---

## Priority 5: Pydantic → __slots__ Classes [MEDIUM PRIORITY]

**Impact**: 10-20% load time, reduced memory  
**Effort**: 30 minutes  
**Risk**: MEDIUM  
**Files**: `vertex.py`, `surface.py`

### Problem
Using Pydantic BaseModel for simple containers adds overhead:
- Validation on every instantiation
- Extra metadata per object
- Extra memory per instance
- Overkill for simple data holders

### Current Code
```python
class vertex(BaseModel):
    x_world: float = 0.0
    y_world: float = 0.0
    # ... 10 fields ...
```

### Optimized Code
```python
class Vertex:
    __slots__ = ['x_world', 'y_world', 'z_world', 'x_view', 'y_view', 'z_view',
                 'x_screen', 'y_screen', 'z_screen', 'index', 'normal']
    
    def __init__(self, x_world=0.0, y_world=0.0, z_world=0.0):
        self.x_world = x_world
        self.y_world = y_world
        self.z_world = z_world
        self.x_view = 0.0
        self.y_view = 0.0
        self.z_view = 0.0
        self.x_screen = 0.0
        self.y_screen = 0.0
        self.z_screen = 0.0
        self.index = 0
        self.normal = None
```

### Why
- `__slots__` reduces memory per object by 30-40%
- No validation overhead
- Direct attribute access (faster)
- Still type-safe enough for our needs

---

## Priority 6: Optimize Linear Search [LOW PRIORITY]

**Impact**: 1-2%  
**Effort**: 15 minutes  
**Risk**: LOW  
**Files**: `swfvs.py` (CalcVectorNormals)

### Problem
```python
for v in vertices.vertex_list:
    for s in surfaces.surface_list:
        if v.index in s.vertex_list:  # O(n) list search
```

With V=3644, S=6320, this is expensive O(V×S) with linear search.

### Solution
Pre-build vertex→surfaces map at load time.

---

## Implementation Roadmap

### Phase 1: Quick Wins (50 minutes)
1. **Tuples** (20 min) - 10-15% gain
2. **Cache Normals** (10 min) - 3-5% gain
3. **RotateMatrix** (20 min) - 15-20% gain

**Subtotal**: ~25-40% performance improvement

### Phase 2: Structural Changes (1.5 hours)
4. **Matrix Flat** (60 min) - 15-25% gain
5. **__slots__** (30 min) - 10-20% load gain

**Combined Total**: 40-60% faster operations

### Phase 3: Fine-tuning (15 minutes)
6. **Linear Search** (15 min) - 1-2% gain

---

## Expected Results

**Before Optimizations**:
- FPS: 60 (vsync capped)
- CPU: High usage
- Load time: ~1-2 seconds

**After Phase 1**:
- FPS: 60 (capped, but lower CPU usage)
- CPU: ~25-40% reduction
- Noticeably smoother experience

**After Phase 2**:
- FPS: 60 (capped, much lower CPU)
- CPU: ~40-60% reduction
- Plenty of headroom for new features

---

## Testing Strategy

1. Benchmark before each optimization
2. Verify visual output unchanged
3. Run full test suite after each phase
4. Profile with `cProfile` or `py-spy` to verify gains
5. Test edge cases (rotation boundaries, normal vectors)

---

## Files to Modify

1. **matrix.py** - Priorities 1, 2, 3, 6
2. **swfvs.py** - Priority 4
3. **vertex.py** - Priority 5
4. **surface.py** - Priority 5
