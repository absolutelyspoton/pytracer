# PyTracer - Project Status

**Last Updated**: August 16, 2026
**Current Branch**: main (v2 complete)
**Next**: v3 - numpy array-oriented rewrite, in readiness for ray tracing

## v2 Summary

v2 took the project from a flat wireframe viewer to a complete software
renderer covering README Feature History revs 0.7 through 1.2:

- **Perspective camera & view plane** (0.7): homogeneous perspective divide
  (`MatrixVectorH`), camera dolly on +/-, near-plane clipping, projection
  targeting an 800x600 viewport pane with pixel-level clipping.
- **Backface culling & hidden-surface removal** (0.8): geometrically correct
  facing test; painter's-algorithm depth sorting.
- **Single light source** (0.9): directional light, Phong reflection model
  (ambient/diffuse/specular), silver material.
- **Phong & Gouraud shading** (1.0/1.1): hand-written scanline rasteriser
  with DDA attribute interpolation; per-vertex (Gouraud) and per-pixel
  (Phong) lighting.
- **Shadows** (1.2): planar projected shadows on a ground plane (live, all
  filled modes) + shadow-mapped self-shadowing in anti-aliased stills.
- **Anti-aliasing**: native aalines (wireframe/hidden-line), 2x supersampled
  solid mode, adaptive quality for Gouraud/Phong - fast half-res while
  interacting, cached 2x-supersampled still after the view settles.

Render modes ('s' cycles): wireframe / hidden-line / solid / gouraud / phong.

### Performance (1024x800 window, 800x600 pane, Utah teapot 6,320 faces)

| Mode | Interactive | AA still |
|------|-------------|----------|
| wireframe (AA, depth-cued) | ~67 FPS | - |
| hidden-line | ~70 FPS | - |
| solid (2x SSAA, shadows) | ~45 FPS | - |
| gouraud | ~18 FPS (half-res) | ~0.3 s |
| phong | ~11 FPS (half-res, step-2 lighting) | ~1 s (with self-shadowing) |

Display-synced to 60 Hz when the window sits on a 60 Hz screen (vsync on
`flip`); the figures above are uncapped.

### Testing

31 pytest tests covering matrix maths, camera projection, the reflection
model, the rasteriser, and shadow geometry. Run from the project root:
`python3 -m pytest -v`.

## Key learnings (v2)

1. **Profile first**: Pydantic `__setattr__` (55% of frame time), vsync, and
   `int()` conversions were the real costs - not the matrix maths.
2. **Theoretical optimisations often lose**: flat matrices were 16% slower;
   per-triangle numpy rasterisation benchmarked *slower* than the scalar
   scanline for teapot-sized triangles.
3. **Adaptive quality beats raw speed**: half-res while moving + cached
   supersampled stills gives both interactivity and image quality.
4. **Pure-Python per-pixel work has a ceiling**: ~250k pixel writes/frame is
   the budget; only array-oriented restructuring (v3) moves it.

## v3 Direction

Rewrite the pipeline array-oriented on numpy - measured on this machine:
batch vertex transform 118x, batch lighting 8x, full-frame pixel writes
173x. The naive per-triangle port loses (0.9x), so v3 restructures around
flat arrays: batched transforms, a z-buffer instead of painter's sorting,
vectorised barycentric rasterisation, full-frame lighting, one
`surfarray.blit_array` per frame. This is the same array-first shape a ray
tracer needs (millions of batched rays), which is the point of v3.

## Branches

- **main**: v2 complete (this state, tagged `v2`)
- **v3**: numpy rewrite (branched from here)
- **v2**: historical optimisation branch (superseded by main)
