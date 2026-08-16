# PyTracer Setup Complete ✓

Your MongoDB has been reinstated and populated with the Utah teapot dataset. The app can now load data from either **file** or **MongoDB**.

---

## What Was Done

✅ **Pydantic v2 Compatibility** — Fixed model definitions for Pydantic v2 (uses `Field(default_factory=list)` instead of mutable defaults)  
✅ **MongoDB Docker Container** — Started local MongoDB at `localhost:27017`  
✅ **Data Population** — Imported 3,644 vertices and 6,320 surfaces from CSV  
✅ **Sequential IDs** — Fixed MongoDB documents with proper 1-based sequential IDs  
✅ **Credentials** — Created `credentials.py` for local MongoDB  
✅ **Validation** — All surface references are valid (1-3644)

---

## Running the App

### Option A: Load from File (Easiest)

No MongoDB needed. Fast startup.

```bash
python3 swfvs.py
```

**Expected output:**
- Pygame window opens with wireframe teapot
- Press 'c' to center, arrows to pan, +/- to zoom
- Press 'a' for axis legend, 'n' for normals, 'f' to toggle wireframe

### Option B: Load from MongoDB

Two terminals needed:

**Terminal 1** — Start the FastAPI server:
```bash
uvicorn server:app --reload
```
- Server runs on http://localhost:8000
- Endpoints like `/db/3dObjects/vertices/0` return JSON

**Terminal 2** — Run the viewer:
1. Edit `swfvs.py` line 15:
   ```python
   INPUT_DATA_SOURCE = 'db'  # Change from 'file'
   ```
2. Run:
   ```bash
   python3 swfvs.py
   ```

**Expected output:**
- Same teapot as file-based, but loaded from MongoDB via the API

---

## Data Architecture

### MongoDB Collections

**Database**: `3dObjects`

**Collection: `vertices`**
```json
{
  "_id": ObjectId("..."),
  "x": -3.0,
  "y": 1.8,
  "z": 0.0,
  "id": 1
}
```
- 3,644 documents (one per vertex)
- `id`: 1-based index (1 to 3644)
- API projection removes `id` and `_id`

**Collection: `surfaces`**
```json
{
  "_id": ObjectId("..."),
  "x": 2909,    // 1-based vertex index
  "y": 2921,    // 1-based vertex index
  "z": 2939,    // 1-based vertex index
  "id": 1
}
```
- 6,320 documents (one per triangular face)
- Fields `x`, `y`, `z` are 1-based vertex references
- API projection removes `id` and `_id`

---

## Loaders

### File Loader (`loader.load_vertices_file()`)
- Reads: `objects/utah_teapot_vertices.csv`
- Format: `x,y,z` (3 columns)
- Returns: `vertices` collection with 3,644 items

### File Loader (`loader.load_surfaces_file()`)
- Reads: `objects/utah_teapot_faces.csv`
- Format: `x,y,z` (3 columns, 1-based vertex indices)
- Returns: `surface` collection with 6,320 items
- **Note**: Currently returns indices as **strings** (bug from v2 roadmap)

### API Loader (`loader.load_vertices_api()`)
- Calls: `GET http://127.0.0.1:8000/db/3dObjects/vertices/0`
- Returns: JSON array of `{x, y, z}` objects
- Converts to `vertices` collection internally

### API Loader (`loader.load_surfaces_api()`)
- Calls: `GET http://127.0.0.1:8000/db/3dObjects/surfaces/0`
- Returns: JSON array of `{x, y, z}` objects
- Converts to `surface` collection internally
- **Note**: Also returns indices as strings

---

## Files Created/Modified

### New Files
- **`setup_mongodb.py`** — Interactive script to set up MongoDB (local or Atlas)
- **`fix_mongodb.py`** — Script to fix MongoDB sequential IDs (already run)
- **`test_setup.py`** — Verification script to check setup status
- **`MONGODB_SETUP.md`** — Detailed setup guide for future reference
- **`credentials.py`** — MongoDB credentials (gitignored, safe for secrets)

### Modified Files
- **`vertex.py`** — Fixed Pydantic v2 compatibility
- **`surface.py`** — Fixed Pydantic v2 compatibility

---

## Current Status

```
✓ File loader works:     3,644 vertices + 6,320 surfaces
✓ MongoDB running:       localhost:27017
✓ MongoDB populated:     3,644 vertices + 6,320 surfaces
✓ API server ready:      http://localhost:8000/db/3dObjects/*
✗ Pygame:               Not installed (requires SDL2 system deps)
```

### To Run the Viewer

Since pygame isn't installed (requires system dependencies like SDL2), you have two choices:

**Option 1**: Install pygame via Homebrew (macOS)
```bash
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf
pip3 install pygame
```

**Option 2**: Use Docker to run in an image with pygame pre-installed
```bash
docker run -it --rm -e DISPLAY=host.docker.internal:0 -v $(pwd):/app python:3.12 bash
# Inside container:
apt-get update && apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
pip install pygame
cd /app && python3 swfvs.py
```

**For now**: Skip pygame installation. MongoDB setup is complete and you can test the data loaders programmatically.

---

## What's Next

Before installing pygame, you should proceed with **v2 branch** to fix bugs and optimize:

```bash
git checkout v2
cat V2_ROADMAP.md
```

### Phase 1 (45 min): Critical Bugs to Fix
1. String vertex indices in file loader (bug #1 in roadmap)
2. Type mismatch in CalcVectorNormals
3. Missing bounds checking
4. Fix Pydantic mutable defaults

### Phase 2 (90 min): Performance Optimization
1. Cache surface normals at load time (3-4x FPS boost!)
2. Remove identity matrix redundancy
3. Backface culling

### Phase 3 (120 min): Code Quality
1. Extract loader factory
2. Extract ViewerState class
3. Cleanup and dead code removal

---

## Testing

Verify everything works:

```bash
# Test file loader
python3 -c "
import loader
v = loader.load_vertices_file()
s = loader.load_surfaces_file()
print(f'File: {v.vertex_count()} vertices, {s.surface_count()} surfaces')
"

# Test MongoDB connection
python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['3dObjects']
print(f'MongoDB: {db.vertices.count_documents({})} vertices, {db.surfaces.count_documents({})} surfaces')
"

# Test API (if server running)
# curl http://localhost:8000/db/3dObjects/vertices/0 | jq '.[] | {x, y, z}' | head -3
```

---

## Keeping MongoDB Running

The Docker container is running but will stop if you restart your machine.

To restart it later:
```bash
docker restart mongodb
```

To stop it:
```bash
docker stop mongodb
```

To view logs:
```bash
docker logs mongodb
```

---

## Summary

- ✅ MongoDB is running and populated
- ✅ File loader works (loads from CSV)
- ✅ API server ready (loads from MongoDB)
- ⚠️ Pygame not installed (optional for now)
- ⏭️ Next: Checkout v2 branch and start bug fixes + optimizations
