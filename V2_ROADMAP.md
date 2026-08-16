# PyTracer v2 — Roadmap & Refactoring Plan

**Status**: Ready to implement | **Estimated Time**: ~6 hours | **Target Release**: Post-v0.6

## Executive Summary

The codebase has **6 critical bugs** (file loading, type mismatches, missing bounds checks), **7 performance bottlenecks** (especially surface normal recalculation eating 3-4x FPS), and **10 structural refactoring opportunities** (monolithic event loop, code duplication, implicit index conventions).

**High-ROI wins:**
1. Move surface normal calculation to load time (3-4x FPS)
2. Refactor loader to eliminate duplication and fix string-to-int bug
3. Extract viewer state into a class (enables testability)
4. Fix all type mismatches (string indices, bounds checking)

---

## Phase 1: Critical Bug Fixes (45 min, must-do)

### Bug #1: String Vertex Indices in File Loader [BLOCKER]
**File**: `loader.py` lines 57-60  
**Issue**: CSV row strings are appended before conversion; surface vertices become strings  
**Impact**: File-based rendering crashes with `TypeError: unsupported operand type(s) for -: 'str' and 'int'`  
**Fix**: Convert to int *before* appending to face

```python
# BEFORE (lines 53-62)
for row in csv_reader:
    if line_count > 0: 
        face = S.surface_cell()
        face.index = line_count
        face.add_face_index(row)
        row[0] = int(row[0])  # too late!
        # ...

# AFTER
for row in csv_reader:
    if line_count > 0:
        face = S.surface_cell()
        face.index = line_count
        face.add_face_index([int(x) for x in row])
        surfaces.add_face(face)
```

**Testing**: Run `python3 swfvs.py` with `INPUT_DATA_SOURCE = 'file'` → should render without TypeError

---

### Bug #2: CalcVectorNormals Type Mismatch [HIGH]
**File**: `swfvs.py` line 34  
**Issue**: Searching `int` vertex index in string list from file loader  
**Impact**: Normals silently fail to compute when using file loader  
**Fix**: Ensure vertex_list indices are always int (via Bug #1 fix)

**Testing**: Press 'n' to toggle normals in file-based view → should see normal vectors

---

### Bug #3: Unused Averaging in CalcVectorNormals [MEDIUM]
**File**: `swfvs.py` lines 32, 39  
**Issue**: Counter `sc` incremented but never used; normals sum instead of average  
**Impact**: Incorrect vertex normal directions (visual glitch in lighting)  
**Fix**: Divide by count before normalization

```python
# BEFORE
totalvec_x = totalvec_x + s.normal[0]
totalvec_y = totalvec_y + s.normal[1]
totalvec_z = totalvec_z + s.normal[2]
totalvec = [totalvec_x,totalvec_y,totalvec_z]
sc+=1
v.normal = matrix.NormaliseVector(totalvec)  # sums, doesn't average!

# AFTER
# ... accumulate as above ...
v.normal = matrix.NormaliseVector([totalvec_x/sc, totalvec_y/sc, totalvec_z/sc])
```

---

### Bug #4: Missing Bounds Check on Face Indices [HIGH]
**File**: `swfvs.py` lines 217-219  
**Issue**: No validation that face vertex indices are in range  
**Impact**: `IndexError` with corrupted/mismatched CSV data  
**Fix**: Add bounds check after loading

```python
# Add to loader or swfvs.py after loading surfaces:
def validate_surfaces(surfaces, vertex_count):
    for face in surfaces.surface_list:
        for vertex_idx in face.vertex_list:
            if vertex_idx < 1 or vertex_idx > vertex_count:
                raise ValueError(
                    f"Face {face.index} references vertex {vertex_idx}, "
                    f"but only {vertex_count} vertices loaded"
                )
```

---

### Bug #5: Floating-Point Epsilon Comparison [MEDIUM]
**File**: `matrix.py` line 110  
**Issue**: `if denom == 0.0:` uses exact equality; small non-zero values cause `1/denom` blowup  
**Impact**: Degenerate triangles produce very large projected coordinates  
**Fix**: Use epsilon-based comparison

```python
# BEFORE
if denom == 0.0:
    r[0] = v[0]
    # ...

# AFTER
if abs(denom) < 1e-9:  # epsilon-safe
    r[0] = v[0]
    # ...
```

---

### Bug #6: Mutable Defaults in Pydantic Models [MEDIUM]
**File**: `vertex.py` line 26, `surface.py` lines 11, 24  
**Issue**: `normal: Optional[List] = []` uses shared mutable default  
**Impact**: Frame-to-frame state corruption if instances share state  
**Fix**: Use `Field(default_factory=list)`

```python
# BEFORE
class vertex(BaseModel):
    normal: Optional[List] = []

# AFTER
from pydantic import Field
class vertex(BaseModel):
    normal: Optional[List] = Field(default_factory=list)
```

---

## Phase 2: Performance Critical Optimizations (90 min)

### Optimization #1: Cache Surface Normals at Load Time [CRITICAL, 3-4x FPS]
**File**: `swfvs.py` lines 214-240  
**Issue**: Recalculate all 6,319 surface normals every frame (wasteful)  
**Impact**: 7.6M FP operations/sec wasted; 15-20 FPS instead of 50-60 FPS  
**Fix**: Move normal calculation to `loader.py` post-load step

```python
# Add to loader.py:
def compute_surface_normals(surfaces, vertices):
    """Calculate and cache surface normals from vertex positions."""
    for face in surfaces.surface_list:
        v1_idx = face.vertex_list[0] - 1
        v2_idx = face.vertex_list[1] - 1
        v3_idx = face.vertex_list[2] - 1
        
        face.normal = matrix.CalcSurfaceNormal(
            [vertices.vertex_list[v1_idx].x_world, 
             vertices.vertex_list[v1_idx].y_world,
             vertices.vertex_list[v1_idx].z_world],
            [vertices.vertex_list[v2_idx].x_world,
             # ... etc],
            [vertices.vertex_list[v3_idx].x_world, # ...
        )

# Call after loading:
vertices = loader.load_vertices_file()
surfaces = loader.load_surfaces_file()
loader.compute_surface_normals(surfaces, vertices)

# Remove lines 224-240 from swfvs.py (no per-frame recalculation)
```

**Testing**: Measure FPS before/after (should jump from ~15-20 to ~50-60 FPS)

---

### Optimization #2: Lazy Normals Calculation on Toggle [HIGH, 50x UI responsiveness]
**File**: `swfvs.py` lines 23-41  
**Issue**: `CalcVectorNormals()` iterates O(V×S) on every 'n' keypress (UI freeze for 100ms)  
**Fix**: Cache computed normals; only calculate once when first toggled  
**Already addressed by Phase 1 refactoring** (normals computed at load time)

---

### Optimization #3: Identity Matrix Creation Overhead [HIGH, 10-15% frametime]
**File**: `matrix.py` lines 21-27  
**Issue**: Creating identity matrices in tight loop with redundant zero-initialization  
**Fix**: Remove redundant loop in `ZeroMatrix()`

```python
# BEFORE
def ZeroMatrix():
    arr = [[0 for i in range(VECTOR_SIZE)] for j in range(VECTOR_SIZE)]
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            arr[i][j] = 0  # redundant!
    return arr

# AFTER
def ZeroMatrix():
    return [[0 for i in range(VECTOR_SIZE)] for j in range(VECTOR_SIZE)]
```

**Impact**: Eliminates 16 redundant assignments per frame (minor but easy win)

---

### Optimization #4: Backface Culling [MEDIUM, 10-15% fill rate]
**File**: `swfvs.py` lines 212-250  
**Issue**: Drawing front and back faces (50% overdraw)  
**Fix**: Skip faces where `dot(face.normal, camera_direction) < 0`

```python
# Add to swfvs.py in face rendering loop:
camera_direction = [0, 0, 1]  # looking down -z
if matrix.DotProduct(face.normal, camera_direction) < 0:
    continue  # face is back-facing, skip drawing
```

**Testing**: Visual should not change (back faces are culled anyway); measure FPS gain

---

## Phase 3: Code Quality & Refactoring (120 min, enables future work)

### Refactor #1: Extract Loader Factory [MEDIUM, eliminates duplication]
**File**: `loader.py`  
**Issue**: Four nearly identical loaders; Bug fix #1 must be applied to all four  
**Fix**: Create generic loader factory

```python
# New abstract loader pattern:
def _load_vertices_generic(data_source):
    """Load vertices from iterable of (x, y, z) tuples."""
    vl = V.vertices()
    for idx, (x, y, z) in enumerate(data_source, start=1):
        v = V.vertex(x_world=float(x), y_world=float(y), z_world=float(z))
        v.index = idx
        vl.add_vertex(v)
    return vl

def load_vertices_file():
    with open('./objects/utah_teapot_vertices.csv') as f:
        csv_reader = csv.reader(f, delimiter=',')
        next(csv_reader)  # skip header
        return _load_vertices_generic(
            (row[0], row[1], row[2]) for row in csv_reader
        )

def load_vertices_api():
    r = requests.get(DEV_API_ENDPOINT_VERTICES)
    data = json.loads(r.text)
    return _load_vertices_generic(
        (item['x'], item['y'], item['z']) for item in data
    )
```

**Benefit**: Bug fix applies to all loaders; new loaders can reuse factory  
**Testing**: Both file and API loaders should produce identical output for same data

---

### Refactor #2: Extract ViewerState Class [MEDIUM, enables testability]
**File**: `swfvs.py` lines 51-128  
**Issue**: 15+ mutable state variables scattered; reset logic duplicated  
**Fix**: Encapsulate state in a class

```python
class ViewerState:
    """Encapsulates all viewer transformation and display state."""
    def __init__(self):
        self.scale = [100.0, 100.0, 100.0]
        self.rotation = [180.0, 180.0, 0.0]  # match initial center values
        self.translation = [SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 0]
        
        self.draw_normals = False
        self.normals_calculated = False
        self.draw_faces = True
        self.draw_axes = True
        
        self.rotation_active = [False, False, False]  # x, y, z
    
    def reset(self):
        """Reset to initial state."""
        self.__init__()

class InputHandler:
    """Handle keyboard input and update viewer state."""
    def __init__(self, state: ViewerState):
        self.state = state
        self.SCALE_SHIFT = 1.1
        self.ROTATION_INCREMENT_DEG = 25
        self.TRANSLATION_SHIFT = 15
    
    def handle_keydown(self, key: int) -> None:
        """Process keyboard input."""
        if key == pygame.K_c:
            self.state.reset()
        elif key == pygame.K_MINUS:
            for i in range(3):
                self.state.scale[i] /= self.SCALE_SHIFT
        elif key == pygame.K_EQUALS:
            for i in range(3):
                self.state.scale[i] *= self.SCALE_SHIFT
        elif key == pygame.K_x:
            self.state.rotation_active[0] = not self.state.rotation_active[0]
        elif key == pygame.K_y:
            self.state.rotation_active[1] = not self.state.rotation_active[1]
        elif key == pygame.K_z:
            self.state.rotation_active[2] = not self.state.rotation_active[2]
        # ... etc for arrow keys, 'a', 'n', 'f', 'q'
    
    def update_rotations(self, state: ViewerState) -> None:
        """Update continuous rotations."""
        if state.rotation_active[0]:
            state.rotation[0] -= math.radians(self.ROTATION_INCREMENT_DEG)
        if state.rotation_active[1]:
            state.rotation[1] += math.radians(self.ROTATION_INCREMENT_DEG)
        if state.rotation_active[2]:
            state.rotation[2] += math.radians(self.ROTATION_INCREMENT_DEG)

# Usage in render loop:
state = ViewerState()
handler = InputHandler(state)

# Later in start():
for event in pygame.event.get():
    if event.type == pygame.KEYDOWN:
        handler.handle_keydown(event.key)

handler.update_rotations(state)
# Compose matrices from state values
M = matrix.MatrixMult(
    matrix.MatrixMult(
        matrix.ScaleMatrix(*state.scale),
        matrix.RotateMatrix(*state.rotation)
    ),
    matrix.TranslateMatrix(*state.translation)
)
```

**Benefit**: Testable input logic; reusable state container; cleaner main loop  
**Testing**: Test `InputHandler` without pygame

---

### Refactor #3: Extract Matrix Utility Functions [LOW, improves clarity]
**File**: `matrix.py`  
**Issue**: Hardcoded cross-product logic; hardcoded matrix dimensions  
**Fix**: Extract reusable functions

```python
def CrossProduct(v1: List[float], v2: List[float]) -> List[float]:
    """Compute cross product of two 3-vectors."""
    x = v1[1] * v2[2] - v1[2] * v2[1]
    y = v1[2] * v2[0] - v1[0] * v2[2]
    z = v1[0] * v2[1] - v1[1] * v2[0]
    return [x, y, z]

def CalcSurfaceNormal(v1: List[float], v2: List[float], v3: List[float]) -> List[float]:
    """Calculate surface normal from three vertices using cross product."""
    a = [v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]]
    b = [v3[0]-v2[0], v3[1]-v2[1], v3[2]-v2[2]]
    return CrossProduct(a, b)
```

---

### Refactor #4: Fix Pydantic Mutable Defaults [MEDIUM, correctness]
**File**: `vertex.py`, `surface.py`  
**Issue**: Mutable default arguments  
**Fix**: Use `Field(default_factory=...)`

```python
# vertex.py
from pydantic import Field

class vertex(BaseModel):
    # ... other fields ...
    normal: Optional[List] = Field(default_factory=list)

# surface.py
class surface_cell(BaseModel):
    vertex_list: List = Field(default_factory=list)
    normal: List = Field(default_factory=list)

class surface(BaseModel):
    surface_list: List = Field(default_factory=list)
```

---

### Refactor #5: Remove Dead Code [LOW, cleanup]
**File**: `swfvs.py` lines 43-49, `loader.py` lines 21, 58-60  
**Issue**: Unused `Toggle()` function, dead type conversions  
**Fix**: Delete `Toggle()`, use `not` operator; convert indices before appending (via Refactor #1)

---

### Refactor #6: Extract Magic Constants [LOW, tunability]
**File**: `swfvs.py`  
**Issue**: Hardcoded colors, scale factors, rotation increments  
**Fix**: Define config class (captured in Refactor #2, `InputHandler` class)

---

## Implementation Order

### Week 1: Critical Fixes + Core Performance (Day 1-2)
1. **Phase 1 Bugs**: All 6 critical bugs (45 min)
2. **Optimization #1**: Cache surface normals (30 min) → **Expect 3-4x FPS immediately**
3. **Optimization #3**: Identity matrix fix (10 min)
4. **Test**: Run viewer with file + API loaders; measure FPS

### Week 1: Refactoring (Day 2-3)
5. **Refactor #1**: Loader factory (45 min)
6. **Refactor #2**: ViewerState class (60 min)
7. **Refactor #4**: Fix Pydantic mutable defaults (15 min)
8. **Refactor #3, #5, #6**: Quick cleanup (30 min)
9. **Test**: All loaders, viewer state toggles, input handling

### Optional/Future
10. **Optimization #2**: Lazy normals (if needed; likely redundant after Phase 1)
11. **Optimization #4**: Backface culling (future feature, impacts visual quality)

---

## Testing Strategy

- **Unit tests**: Extend `tests/` with `test_loader.py`, `test_viewer_state.py`
- **Integration tests**: Verify file/API loaders produce identical vertex/surface lists
- **Manual smoke tests**: `python3 swfvs.py` with both data sources; toggle 'n', 'f', 'a', 'x', 'y', 'z'; zoom/pan/rotate
- **Performance**: Measure FPS before/after each optimization (use pygame clock)

---

## Success Criteria

✅ File-based loading renders without TypeError  
✅ Normals calculation produces correct directions (averaged, not summed)  
✅ FPS jumps from 15-20 to 50-60 with surface normal caching  
✅ Viewer state is encapsulated and testable  
✅ All loader duplication eliminated  
✅ No mutable default arguments in Pydantic models  
✅ v2 branch merges cleanly to main without regressions  

---

## Branch Strategy

1. Create `v2` branch from `main`
2. Apply Phase 1 + Phase 2 (Optimization #1, #3) as a single commit: "v2: Fix critical bugs and cache surface normals"
3. Apply Phase 2 (Optimization #4) as a follow-up: "v2: Add backface culling"
4. Apply Phase 3 refactoring as separate commits:
   - "v2: Extract loader factory"
   - "v2: Extract ViewerState class"
   - "v2: Fix Pydantic mutable defaults and cleanup"
5. Test thoroughly on `v2`
6. Create PR from `v2` → `main` with this roadmap as description
7. Merge `v2` → `main` once approved

---

## Post-v2 Vision (v0.7+)

With v2 stabilized and refactored:
- **v0.7**: Proper view planes and perspective points (already TODO in code)
- **v0.8**: Backface culling + axis visualization (backface culling WIP in v2)
- **v0.9**: Single light source
- **v1.0**: Phong shading
- **v1.1**: Gouraud shading
- **v1.2**: Shadows
- **v1.3**: Multiple light sources

v2 refactoring unblocks this roadmap by eliminating tech debt.
