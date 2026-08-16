# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A from-scratch 3D wireframe viewer / nascent ray tracer in Python. All linear algebra is hand-rolled (no numpy). The
long-term goal (see the Feature History table in `README.md`) is to progress from wireframe rendering toward backplane
culling, lighting, and Phong/Gouraud shading. `README.md` also holds the authoritative key-binding table for the viewer.

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

Rendering pipeline, driven by the main loop in `swfvs.py:start()`:

1. **Load** — `loader.py` builds a `vertices` collection and a `surface` collection from one of two sources, selected by
   the `INPUT_DATA_SOURCE` constant at the top of `swfvs.py` (`'db'` or `'file'`).
2. **Transform** — each frame composes scale × rotate × translate into a single 4x4 matrix `M` (`matrix.py`), applies it
   to every vertex to get *view* coordinates, then applies a projection matrix to get *screen* coordinates.
3. **Draw** — faces are drawn as pygame polygons from the screen coordinates; normals and axis legend are optional
   overlays toggled by key.

Coordinate spaces are the central concept: every `vertex` carries three coordinate triples — `*_world` (loaded, immutable),
`*_view` (post-transform), `*_screen` (post-projection). `calc_view_coordinates()` and `calc_screen_coordinates()` mutate
the vertex in place; the world coordinates are the only source of truth across frames.

### Modules

- `matrix.py` — pure functions over 4x4 matrices and 3-vectors. Note the convention: matrices are **row-major lists of
  lists**, and `MatrixVector` treats the vector as a row vector multiplied on the left, so translation lives in row 3
  (`m[3][0..2]`), not the last column. New matrix code must follow this or transforms compose incorrectly.
- `vertex.py` / `surface.py` — pydantic `BaseModel` classes (deliberately used instead of dataclasses, per `DEVLOG.md`, so
  the same models serve FastAPI). `surface_cell.vertex_list` holds **1-based indices** into the vertex list; call sites
  subtract 1 when indexing (see `swfvs.py`).
- `loader.py` — four loaders: `load_vertices_file` / `load_surfaces_file` read the CSVs in `objects/`;
  `load_vertices_api` / `load_surfaces_api` GET from the FastAPI service. Both paths must produce equivalent collections.
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
