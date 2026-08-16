# Math Performance Audit

## Critical Issues Found

### 1. **RotateMatrix: 9 Full Matrix Multiplications Per Frame** [CRITICAL]
**File**: `matrix.py:41-71`  
**Impact**: HIGH - Called every frame during rotation

**Issue**:
```python
def RotateMatrix(x_theta, y_theta, z_theta):
    arr_x = IdentityMatrix()  # Creates 4x4 matrix (16 cells)
    arr_y = IdentityMatrix()  # Creates 4x4 matrix (16 cells)
    arr_z = IdentityMatrix()  # Creates 4x4 matrix (16 cells)
    
    # Modify only 4 cells in each...
    
    m = MatrixMult(arr_x, arr_y)      # Full O(n³) multiply = 64 ops
    m = MatrixMult(m, arr_z)          # Full O(n³) multiply = 64 ops
    return m
```

**Problem**: 
- Creates 3 full identity matrices just to set 4 values in each
- Performs 2 full matrix multiplications for what should be a simple rotation composition
- Each MatrixMult does 64 multiplications (4x4x4 nested loop)
- Total: ~128 multiply operations + 3 IdentityMatrix calls per frame

**Solution**:
- Compose rotation matrices analytically (one 4x4 matrix computed directly)
- Avoids 2 expensive multiplications
- Expected saving: ~120 multiplications per frame = 15-20% speedup

---

### 2. **MatrixMult: O(n³) Naive Algorithm** [MEDIUM]
**File**: `matrix.py:26-32`  
**Impact**: MEDIUM - Called 2x per frame in RotateMatrix, plus other matrix compositions

**Issue**:
```python
def MatrixMult(m1,m2):
    mz = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            for e in range(VECTOR_SIZE):
                mz[i][j] = mz[i][j] + m1[i][e]*m2[e][j]  # Reads/writes mz[i][j] 4 times
    return mz
```

**Problem**:
- `mz[i][j]` is accessed 4 times (initialized to 0, then += 4 times)
- Could accumulate in a local variable first
- Inner loop does: 4 mults + 3 adds per iteration
- Total: 16 cells × 4 adds/cell = 64 add operations (redundant)

**Solution**:
```python
def MatrixMult(m1, m2):
    mz = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            sum_val = 0
            for e in range(VECTOR_SIZE):
                sum_val += m1[i][e] * m2[e][j]
            mz[i][j] = sum_val
    return mz
```

Expected saving: ~25% (eliminate redundant array accesses)

---

### 3. **ScaleMatrix & TranslateMatrix: Unnecessary IdentityMatrix Calls** [LOW]
**File**: `matrix.py:73-86`  
**Impact**: LOW - Called once per frame, but simple fix

**Issue**:
```python
def ScaleMatrix(x,y,z):
    m = IdentityMatrix()  # Creates full 16-cell matrix
    m[0][0] = x           # Only modifies 3 cells
    m[1][1] = y
    m[2][2] = z
    return m
```

**Problem**: 
- Creates 16 cells just to modify 3
- IdentityMatrix does nested loops to initialize all cells

**Solution**:
```python
def ScaleMatrix(x, y, z):
    m = [[0]*4 for _ in range(4)]
    m[0][0] = x
    m[1][1] = y
    m[2][2] = z
    m[3][3] = 1
    return m
```

Expected saving: ~5% (minor, but cleaner)

---

### 4. **PerspectiveMatrix: Redundant IdentityMatrix Call** [LOW]
**File**: `matrix.py:88-92`  
**Impact**: LOW - Called once per frame, minor overhead

Same as #3 - creates full identity matrix just to modify 2 values.

---

## Performance Summary

| Issue | Frequency | Cost/Call | Per Frame | Potential Gain |
|-------|-----------|-----------|-----------|---|
| RotateMatrix mult explosion | Every frame | 128 mults | 128 | 15-20% |
| MatrixMult array access | 2x per frame | ~25% overhead | 25% of mults | 5-10% |
| Unnecessary IdentityMatrix | Per frame | 32 assignments | Small | 2-3% |
| **Total Potential Gain** | - | - | - | **20-30%** |

---

## Recommended Fixes (Priority Order)

### Priority 1: Compose Rotation Analytically (15-20% gain)
```python
def RotateMatrix(x_theta, y_theta, z_theta):
    """Compute XYZ rotation matrix directly without intermediate multiplies."""
    x_rad = math.radians(x_theta)
    y_rad = math.radians(y_theta)
    z_rad = math.radians(z_theta)
    
    cx, cy, cz = math.cos(x_rad), math.cos(y_rad), math.cos(z_rad)
    sx, sy, sz = math.sin(x_rad), math.sin(y_rad), math.sin(z_rad)
    
    # Compose R = Rz * Ry * Rx directly
    m = [[0]*4 for _ in range(4)]
    
    # Row 0: [cz*cy, -sz*cy, sy, 0]
    m[0][0] = cz*cy
    m[1][0] = -sz*cy  
    m[2][0] = sy
    m[3][0] = 0
    
    # Row 1: [cz*sy*sx + sz*cx, -sz*sy*sx + cz*cx, -cy*sx, 0]
    m[0][1] = cz*sy*sx + sz*cx
    m[1][1] = -sz*sy*sx + cz*cx
    m[2][1] = -cy*sx
    m[3][1] = 0
    
    # Row 2: [-cz*sy*cx + sz*sx, sz*sy*cx + cz*sx, cy*cx, 0]
    m[0][2] = -cz*sy*cx + sz*sx
    m[1][2] = sz*sy*cx + cz*sx
    m[2][2] = cy*cx
    m[3][2] = 0
    
    # Row 3: [0, 0, 0, 1]
    m[3][3] = 1
    
    return m
```

### Priority 2: Optimize MatrixMult (5-10% gain)
Accumulate sum in local variable instead of accessing array 4 times per cell.

### Priority 3: Direct Initialization (2-3% gain)
Avoid IdentityMatrix() for Scale and Translate, create matrices directly.

---

## Expected Final Impact

- **Current**: Baseline performance (60 FPS achieved via Phase 2.1)
- **After Priority 1**: +15-20% FPS (90-95 FPS on 60Hz screen)
- **After Priority 2**: +5-10% additional
- **After Priority 3**: +2-3% additional

**Total potential**: 20-30% faster math operations
**Final achievable FPS**: Capped at 60 (vsync), but much lower CPU usage

---

## Testing Strategy

1. Benchmark RotateMatrix performance (call 1000x, measure time)
2. Benchmark MatrixMult performance (multiply two matrices 1000x)
3. Run full app, measure FPS and CPU usage before/after each fix
4. Verify correctness with existing unit tests (matrix identity tests)
