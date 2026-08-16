# PyTracer - Project Status

**Last Updated**: August 16, 2026  
**Current Branch**: main  
**Version**: v2 (merged)

## Performance Summary

### Current Metrics
- **Average FPS**: 116.4 FPS (stable)
- **Range**: 114-119 FPS (95.4% stability)
- **Load Time**: ~0.1 seconds
- **Memory**: ~50MB (3644 vertices + 6320 surfaces)

### Optimizations Completed

| Priority | Optimization | Impact | Status |
|----------|--------------|--------|--------|
| 1 | Lists → Tuples | 10-15% theoretical | ✅ Done |
| 2 | Cache Normals | 3-5% theoretical | ✅ Done |
| 5 | __slots__ Classes | **1.8x speedup** | ✅ Done |
| 3 | Direct Rotation | Negligible | ❌ Reverted |
| 4 | Flat Matrix | -16% (slower) | ❌ Skipped |
| Culling | Backface Culling | -4.4% cost | ⚠️ Disabled |

### Real-World Improvements
- **Before v2**: 60 FPS (vsync capped)
- **After v2**: 116 FPS (unlimited)
- **Headroom**: 93% additional capacity

## Architecture

### Core Modules
- **matrix.py**: Linear algebra (4x4 matrices, vectors, transforms)
- **vertex.py**: Vertex data model with __slots__
- **surface.py**: Surface/face data model with __slots__
- **loader.py**: Data loading (file & API sources)
- **swfvs.py**: Main render loop with viewer state
- **viewer_state.py**: State management and input handling

### Data
- Utah teapot: 3,644 vertices, 6,320 triangular faces
- Loaded from CSV files in `objects/`
- Optional MongoDB backend support

## Features

### Rendering
- ✅ Wireframe 3D visualization
- ✅ Rotation (X/Y/Z axes independently controllable)
- ✅ Scaling (zoom in/out)
- ✅ Translation (pan)
- ✅ Perspective projection
- ✅ Vertex normal visualization
- ⚠️ Backface culling (disabled by default, -4.4% FPS cost)

### UI
- ✅ FPS counter (top-left)
- ✅ Geometry statistics (vertex/edge/face/normal counts)
- ✅ Help overlay (press 'h')
- ✅ Status indicators for active features
- ✅ Keyboard controls (arrows, +/-, x/y/z, n/v, b, f, a, c, q)

### Testing
- ✅ 12 unit tests (all passing)
- ✅ Data loading verified
- ✅ Matrix operations tested
- ✅ No regressions

## Known Limitations

1. **Backface Culling Cost**: Culling check (6,320 MatrixVector ops) costs more than polygon drawing saves (-4.4% FPS). Disabled by default for wireframe viewer.

2. **Pygame Rendering**: Still ~30% of frame time. Further optimization would require GPU acceleration or lower-level graphics API.

3. **Flat Matrix Representation**: Theoretical optimization (15-25% gain) turned out slower in practice (-16%) due to Python tuple overhead.

4. **Direct Rotation Composition**: Mathematically correct but negligible impact (once/frame) with poor code readability. Reverted.

## Key Learnings

1. **Profile First**: Theoretical analysis missed the actual bottleneck (Pydantic validation = 55% of time)
2. **Measure Carefully**: Real-world FPS differs from micro-benchmarks (culling: -38% in math, -4.4% in rendering)
3. **Data Structures Matter**: __slots__ conversion yielded actual 1.8x speedup despite being "just" a data structure change
4. **Diminishing Returns**: After optimizing hot path (__setattr__), remaining 30% is pygame I/O, which isn't easily optimizable

## Future Work

### If Further Optimization Needed
1. Profile pygame rendering (polygon drawing, display flip)
2. Consider GPU rendering with OpenGL/Vulkan
3. Implement sphere/frustum culling instead of per-face checks
4. Cache screen coordinates between frames if rotation static

### Feature Additions (With 93% FPS Headroom)
1. Phong/Gouraud shading
2. Lighting model
3. Texture mapping
4. Multiple object support
5. Animation/keyframes

## Testing Commands

```bash
# Run all tests
python3 -m pytest -v

# Run with data loading
python3 -c "import loader; vertices = loader.load_vertices_file(); print(f'{vertices.vertex_count()} vertices loaded')"

# Measure FPS (requires pygame display)
python3 swfvs.py
```

## Branch Status

- **main**: Latest stable, all optimizations merged
- **v2**: Optimization work (archived for reference)

---

**Status**: ✅ **HEALTHY**  
**Performance**: 116 FPS stable  
**Quality**: All tests passing  
**Ready for**: Feature development or additional optimization
