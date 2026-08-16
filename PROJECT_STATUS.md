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

## v3: Numpy Array-Oriented Renderer (this branch)

Full feature-parity rewrite on numpy: `Mesh` arrays, batched transforms,
a fragment rasteriser with a z-buffer (`render.py`) replacing painter's
sorting, deferred batch shading, and per-frame shadow mapping. Notable
upgrades over v2:

- **Self-shadowing runs live in every filled mode** (v2: stills only).
- **The floor is scene geometry** - it occludes and receives mapped
  shadows; the v2 planar-projection special case is gone.
- **Exact per-pixel occlusion** (z-buffer) instead of per-face sorting.
- Adaptive quality: half-res interactive, cached 2x-supersampled still
  after ~0.25s of stillness (still renders in ~0.3-0.5s vs v2's ~1s).

### v2 vs v3 (measured, uncapped)

| Mode | v2 interactive | v3 interactive | v3 notes |
|------|----------------|----------------|----------|
| wireframe | 67 FPS | 79 FPS | AA + depth cue |
| solid | ~45 FPS | ~109 FPS | now with live self-shadowing |
| gouraud | 18 FPS | ~20 FPS | + live self-shadowing |
| phong | 11 FPS | ~23 FPS | + live self-shadowing |
| cached still redraw | ~130 FPS | ~215 FPS | |

The pipeline's flat-array shape (batch geometry in, batch shaded samples
out) is the same structure the ray tracer needs - rays replace fragments.

## Branches

- **main**: v2 complete (tagged `v2`)
- **v3**: numpy rewrite (current)
- **v2**: historical optimisation branch (superseded by main)
