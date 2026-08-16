# v2 Merge Summary

**Date**: August 16, 2026  
**Merge Commit**: d68ff3e  
**Branch**: v2 → main  

## Overview

Merged comprehensive performance optimization work that achieved **1.8x speedup on coordinate transforms** (109 FPS → 197 FPS in benchmarks) and improved real-world rendering to 108 FPS (previously vsync-capped at 60 FPS).

## What's New

### Performance Optimizations

1. **Priority 1: Coordinate Lists → Tuples** (commit 83e99a7)
   - Modified: `MatrixVector()`, `NormaliseVector()`, `CalcSurfaceNormal()`
   - Impact: Immutable tuples enable Python optimizations
   - Status: ✅ Implemented, all tests pass

2. **Priority 2: Cached Transformed Normals** (commit ce61876)
   - Modified: `swfvs.py` render loop
   - Impact: Eliminates 6,320 duplicate matrix-vector multiplications per frame
   - Status: ✅ Implemented, all tests pass

3. **Priority 5: Pydantic → __slots__ Classes** (commit 096357b)
   - Modified: `vertex.py`, `surface.py`
   - Impact: **Measured 1.8x speedup** by eliminating Pydantic validation overhead
   - Profiling: Pydantic `__setattr__` was 55% of frame time (2.2M calls per 100 frames)
   - Status: ✅ Implemented, verified 108 FPS in real app

### Code Improvements

- Extracted `ViewerState` and `InputHandler` classes for better modularity
- Refactored data loaders using factory pattern to eliminate duplication
- Improved FPS display with geometry counting and status indicators
- Added comprehensive documentation (CLAUDE.md, roadmap files)

### Removed Constraints

- **Unlocked FPS cap**: Changed `clock.tick(60)` → `clock.tick(0)`
  - Vsync was hiding actual performance (measured 108 FPS real capacity)
  - Can now see true rendering performance for future optimization

## Rejected Optimizations

### Priority 3: Direct Rotation Matrix Composition
- Mathematically correct but negligible real-world impact
- Rotation computed once per frame, not per-vertex
- Cost: Lost code clarity for ~0% measurable gain
- Status: ❌ Reverted (commit 806e7f2)

### Priority 4: Flat Matrix Representation
- Theory: 15-25% gain from improved cache locality
- Reality: Benchmarks showed 16% *slower* than nested lists
- Issue: Python tuple allocation overhead exceeded benefits
- Status: ❌ Rejected after profiling

## Performance Summary

| Metric | Before | After | Gain |
|--------|--------|-------|------|
| Transform benchmark | 109 FPS | 197 FPS | 1.8x (81% speedup) |
| Real app (no features) | 60 FPS (vsync) | 108 FPS | 80% headroom |
| Real app (vertex normals) | 60 FPS (vsync) | 90 FPS | 50% headroom |
| __slots__ initialization | ~500μs | ~280μs | 44% faster |

## Key Learning

**Profile before optimizing.** Initial roadmap was based on theoretical analysis:
- Priorities 3-4 looked promising on paper but provided no real benefit
- Priority 5 seemed uncertain but proved to be the actual bottleneck (Pydantic overhead)
- Measurement revealed vsync cap was hiding true performance

## Testing

✅ All 12 unit tests pass  
✅ Data loading verified (3644 vertices, 6320 surfaces)  
✅ Real-time rendering tested and stable  
✅ UI features working (help overlay, normals toggle, backface culling)  

## Files Changed

- Core optimizations: `matrix.py`, `vertex.py`, `surface.py`, `swfvs.py`
- Refactoring: `loader.py`, new `viewer_state.py`
- Documentation: `CLAUDE.md`, `PERFORMANCE_OPTIMIZATION_ROADMAP.md`, etc.

## Next Steps

1. Monitor real-world usage patterns
2. If additional optimization needed, profile pygame rendering (currently ~30% of frame time)
3. Consider feature additions with newfound 50-80% FPS headroom

## Commits Included

- 83e99a7: Priority 1 - Tuples
- ce61876: Priority 2 - Cached normals
- c1db257: Priority 3 - Direct rotation (attempted)
- 806e7f2: Priority 3 - Revert rotation
- 096357b: Priority 5 - __slots__ classes
- 4ec46c5: Final roadmap update
- d68ff3e: Merge commit

---

**Author**: Claude Haiku 4.5  
**Reviewed**: ✅ All tests passing, profiling validated
