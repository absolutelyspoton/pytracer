# pytracer

A 3D renderer and ray tracer built from scratch in Python — no graphics
engine, no OpenGL. It started life as a wireframe viewer and grew into a
full pipeline: perspective camera, z-buffer rasteriser, Phong lighting and
shading, shadow mapping, and a Whitted-style ray tracer with reflections,
refractive glass, and procedural materials, all vectorised on numpy and
displayed through pygame.

## Quick start

Requires **Python 3.10+**. From a fresh clone:

```bash
cd pytracer
pip3 install numpy pygame           # the only two packages the viewer needs
python3 swfvs.py
```

A window opens with the Utah teapot. **Always run from the repo root** —
data files and tests are found by relative path.

Things to try first:

1. Press `s` repeatedly to cycle the render modes:
   wireframe → hidden-line → solid → gouraud → phong → **raytrace**.
2. In raytrace mode, stop moving: after a moment the app ray-traces a full
   still (progress bar below the viewport, image paints in from the top,
   ~15–20 s) and caches it until you move again.
3. Press `m` to make the model glass (re-traces with refraction), `p` to
   change the floor pattern, `o` to pick a different object.
4. Spin it with `x` / `y` / `z`, dolly with `+` / `-`.

## Controls

|Key           |Description                                    |
|--------------|-----------------------------------------------|
|C             |Centre drawing / Reset (camera + transforms)   |
|Arrow Keys    |Shift Up/Down/Left/Right                       |
|+|-           |Dolly camera in/out                            |
|x|y|z         |Spin object through X-Axis, Y-Axis, Z-Axis     |
|a             |Display X/Y/Z Axis Legend                      |
|n|v           |Toggle display of vertex normals               |
|f             |Toggle display of surfaces (polygons)          |
|s             |Cycle render mode: wireframe / hidden-line / solid / gouraud / phong / raytrace |
|d             |Toggle shadows (live in raster modes; exact traced shadows in raytrace) |
|p             |Cycle ray-traced floor pattern: checker / stripes / rings / mandelbrot / plain |
|m             |Cycle ray-traced model material: silver / glass / wood / marble |
|o             |Object menu (1-9 selects: teapot, torus, Cobra Mk I, lamp-on-ball) |
|b             |Toggle backface culling (wireframe mode)       |
|h             |Toggle help overlay                            |
|q             |Quit                                           |

## Running the tests

```bash
pip3 install pytest
python3 -m pytest -v        # from the repo root (imports resolve by rootdir)
```

Covers the matrix maths, camera projection, rasteriser, reflection model,
shadow geometry, ray tracer (Snell/Fresnel/TIR), and object generators.

## Objects

Objects live in `objects/` as CSV pairs — `{name}_vertices.csv` (x,y,z
rows) and `{name}_faces.csv` (1-based vertex index triples). The in-app
object menu (`o`) is a directory scan: **drop a new pair in and it appears
in the menu**, framed and floored automatically from its bounding size.

Generated shapes (torus, Cobra Mk I, lamp-on-ball) are reproducible:

```bash
python3 generate_objects.py     # rewrites their CSVs from mesh.py generators
```

Add a shape by writing a `make_*()` in `mesh.py` (there's a primitive
toolkit: spheres, tubes/cones, mesh merging) and adding one line to the
`GENERATORS` table in `generate_objects.py`.

## Optional: serving objects from MongoDB

The app can load objects through a FastAPI service backed by MongoDB
instead of reading CSVs (`INPUT_DATA_SOURCE = 'db'` at the top of
`swfvs.py`). Setup from scratch:

```bash
pip3 install -r requirements.txt    # fastapi, uvicorn, pymongo, etc.

# 1. Start a local MongoDB
docker run --name mongodb -d -p 27017:27017 mongo

# 2. Create credentials.py and import every object in objects/
python3 setup_mongodb.py local

# 3. Start the API service
uvicorn server:app --reload         # serves on :8000

# 4. Point the app at the database
#    edit swfvs.py: INPUT_DATA_SOURCE = 'db'
python3 swfvs.py
```

Each object becomes a `{name}_vertices` / `{name}_surfaces` collection
pair in the `3dObjects` database (the teapot also fills legacy unprefixed
`vertices`/`surfaces` collections). The service route is generic —
`GET /db/{database}/{table}/{id}`, with `id=0` meaning all rows — so new
objects need no server changes. `credentials.py` is gitignored; the server
will not import without it (step 2 creates it).

## Project layout

| File | Role |
|------|------|
| `swfvs.py` | The app: window, input, render-loop, adaptive quality |
| `mesh.py` | Mesh arrays, normals, object generators |
| `matrix.py` | 4×4 transforms (row-vector convention: translation in row 3) |
| `camera.py` | Perspective camera: dolly, near plane, vectorised projection |
| `render.py` | Batched fragment rasteriser with z-buffer |
| `light.py` | Phong reflection model + material constants |
| `shadow.py` | Shadow mapping (raster modes) |
| `tracer.py` | Ray tracer: clusters, Möller–Trumbore, Fresnel/Snell, materials |
| `loader.py` | Object registry + CSV/API loaders |
| `viewer_state.py`, `viewport.py` | Input handling, state, view pane |
| `server.py`, `setup_mongodb.py` | Optional MongoDB service layer |

## Feature History

|Rev           |Description                                                              |
|--------------|------------------------------------------------------------------------ |
|0.11          |Basic Wireframe Drawing - Zoom, Translate, Rotate                        |
|0.2           |Object Classes                                                           |
|0.3           |Normals for surfaces and vertices                                        |
|0.4           |Test cases, and test harness (pytest)                                    |
|0.5           |3d to 2d View Transforms - Perspective & parallel projection             |
|0.6           |Loader supports files, MongoDB direct, and API to Mongo                  |
|0.7           |View plane & perspective camera (dolly, near-plane clipping, viewport)   |
|0.8           |Backface culling & hidden-surface removal (painter's algorithm)          |
|0.9           |Single light source (Phong reflection model: ambient/diffuse/specular)  |
|1.0           |Phong Shading (per-pixel normal interpolation, scanline rasteriser)      |
|1.1           |Gauraud Shading (per-vertex lighting, colour interpolation)              |
|1.2           |Shadows (planar projected on ground plane; shadow-mapped self-shadowing) |
|1.5           |v3: numpy array pipeline - z-buffer rasteriser, live self-shadowing      |
|2.0           |Ray tracing - primary/shadow/reflection rays, mirror materials           |
|2.1           |Refraction & glass (Snell, Fresnel/Schlick, total internal reflection)   |
|1.3 (todo)    |Multiple light source                                                    |
