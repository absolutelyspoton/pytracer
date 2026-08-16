# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A from-scratch 3D renderer / nascent ray tracer in Python. Through v2 (tag `v2`) all linear algebra was hand-rolled
scalar Python; **v3 (current) is an array-oriented rewrite on numpy** — batched transforms, a fragment rasteriser with
a z-buffer (`render.py`), deferred batch shading, and per-frame shadow mapping — in readiness for ray tracing.
`README.md` holds the Feature History table and the authoritative key-binding table for the viewer.

## Commands

```bash
python3 -m pytest -v          # run tests, from the project root (rootdir matters, see Testing)
python3 -m pytest -v tests/test_matrix.py::test_IdentityMatrix   # single test

python3 swfvs.py              # run the pygame viewer
uvicorn server:app --reload   # run the FastAPI service layer on :8000

python3 matrix.py             # each module has a __main__ block that exercises it as a smoke test
```

Dependencies are pinned in `requirements.txt` (Python 3.x, pydantic **v1** — not v2). There is no venv checked in and no
lint/typecheck config; the codebase relies on scattered `# type: ignore` comments rather than a configured type checker.

## Architecture

Rendering pipeline, driven by the main loop in `swfvs.py:start()`. All geometry lives in numpy arrays (`mesh.Mesh`:
vertices N×3, faces M×3 0-based, face/vertex normals) and every stage operates on whole meshes at once:

1. **Load** — `loader.load_mesh_file()` / `load_mesh_api()` (selected by `INPUT_DATA_SOURCE` in `swfvs.py`) return a `Mesh`.
2. **Transform** — one `verts @ M` per frame (`matrix.transform_points`); camera projection is vectorised
   (`camera.Camera.project` → screen coords + near-plane clip mask).
3. **Draw** — wireframe/hidden-line use pygame `aalines` (C-speed); solid/gouraud/phong go through the **fragment
   pipeline** (`render.rasterize`): flat arrays of every candidate pixel of every triangle, barycentric weights in bulk,
   a z-buffer resolve keeping the nearest fragment per pixel, deferred batch shading (`light.phong_shade_batch`), and one
   `surfarray.blit_array`. The floor is scene geometry; shadows come from a per-frame shadow map (`shadow.py`) built with
   the same rasteriser pointed down the light axis. Interactive frames render at half resolution; a supersampled still is
   rendered and cached when the view goes still (`SSAA_*` constants in `swfvs.py`).

### Modules

- `matrix.py` — numpy 4x4 builders + batch transforms. Note the convention: **row vectors multiplied on the left**
  (`v @ M`), so translation lives in row 3 (`m[3][0..2]`), not the last column. New matrix code must follow this or
  transforms compose incorrectly.
- `mesh.py` — `Mesh` arrays + vectorised normals; `floor_mesh()` builds the tessellated ground plane (tessellated because
  rasteriser cost scales with triangle bounding boxes).
- `render.py` / `light.py` / `shadow.py` / `camera.py` — the batch pipeline stages described above.
- `loader.py` — file loader reads the CSVs in `objects/` (faces are **1-based** in the CSVs, converted to 0-based on
  load); API loader GETs from the FastAPI service. Both paths must produce equivalent meshes.
- `server.py` — thin generic MongoDB read API. `GET /db/{database}/{table}/{id}` maps directly onto
  `client[database][table].find(...)`, with `id=0` meaning "all rows". Also exposes `/ping/{webserver|database|google}`
  returning a Prometheus-style metric line.

### Data

`objects/` holds the Utah teapot as CSV. Files come in pairs: `*_vertices.csv` / `*_faces.csv` for the file loader, and
`*_mdb.csv` variants that carry an extra `id` column for MongoDB import. Faces are triangles — several places assume
exactly 3 vertices per face and have TODOs noting the general-polygon case is unhandled.

## Credentials

`server.py` imports a `credentials.py` module (gitignored, **not** in the repo) providing `MONGODB_ADMIN_USERNAME` and
`MONGODB_ADMIN_PASSWORD`. It must be created locally or the server will not import. These were previously hardcoded and
removed in the two most recent commits — do not reintroduce literal credentials into `server.py`.

`DEV_MONGODB_ADDRESS` in `server.py` is assigned twice; the second assignment (MongoDB Atlas) wins. Switch to a local
Docker Mongo by reordering or commenting out the Atlas line — see `DEVLOG.md` for the `docker run` invocation.

## Testing

Tests live in `tests/` and import modules by bare name (`import matrix`). There is no `conftest.py`, `pytest.ini`, or
package `__init__.py`, so this only resolves when pytest is invoked **from the project root** — running from inside
`tests/` will fail on imports. Coverage is limited to the pure-logic modules (`matrix`, `vertex`, `surface`); the
pygame loop, loaders, and server are untested.
