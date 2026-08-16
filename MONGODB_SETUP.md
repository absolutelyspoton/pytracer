# MongoDB Setup Guide for PyTracer

You have two options: **Local MongoDB (Docker)** or **MongoDB Atlas (Cloud)**. Here's how to set up each.

---

## Option 1: MongoDB Atlas (Easiest for Development)

MongoDB Atlas is free, cloud-hosted, and requires no local setup.

### Steps

1. **Sign up** (if needed):
   - Go to https://www.mongodb.com/cloud/atlas
   - Create a free account or sign in

2. **Create a cluster** (if you don't have one):
   - Click "Create Deployment"
   - Choose **M0 (free tier)**
   - Select your region (closest to you)
   - Create cluster (takes 1-2 min)

3. **Get credentials**:
   - Go to "Database Access" in the left menu
   - Create a new database user:
     - Username: (your choice, e.g., `admin`)
     - Password: (generate a strong one)
     - Click "Create User"
   - Note down the username and password

4. **Allow network access**:
   - Go to "Network Access"
   - Click "Add IP Address"
   - Select "Allow access from anywhere" (for development only)
   - Click "Confirm"

5. **Run setup script**:
   ```bash
   python3 setup_mongodb.py atlas
   ```
   - When prompted, enter your username and password
   - Script will:
     - Create `credentials.py`
     - Connect to your Atlas cluster
     - Populate with Utah teapot data
     - Validate the data

6. **Verify**:
   ```bash
   python3 -c "
   from pymongo import MongoClient
   import credentials
   
   conn = 'mongodb+srv://' + credentials.MONGODB_ADMIN_USERNAME + ':' + credentials.MONGODB_ADMIN_PASSWORD + '@cluster0.iyzootc.mongodb.net/test'
   client = MongoClient(conn)
   db = client['3dObjects']
   print('Vertices:', db['vertices'].count_documents({}))
   print('Surfaces:', db['surfaces'].count_documents({}))
   "
   ```

---

## Option 2: Local MongoDB (Docker)

### Prerequisites

- Docker Desktop must be running
- If you don't have Docker: https://www.docker.com/products/docker-desktop

### Steps

1. **Start MongoDB container**:
   ```bash
   docker run --name mongodb -d -p 27017:27017 -v ~/mongodb_data:/data/db mongo
   ```
   - This creates a persistent volume in `~/mongodb_data/`
   - Next time, restart with: `docker restart mongodb`

2. **Verify container is running**:
   ```bash
   docker ps | grep mongodb
   ```
   Should show something like: `mongodb ... mongo`

3. **Run setup script**:
   ```bash
   python3 setup_mongodb.py local
   ```
   - Script will:
     - Create `credentials.py`
     - Connect to localhost:27017
     - Populate with Utah teapot data
     - Validate the data

4. **Verify**:
   ```bash
   python3 -c "
   from pymongo import MongoClient
   
   client = MongoClient('mongodb://localhost:27017/')
   db = client['3dObjects']
   print('Vertices:', db['vertices'].count_documents({}))
   print('Surfaces:', db['surfaces'].count_documents({}))
   "
   ```

---

## Running PyTracer

### Option A: Load from File (Default)
```bash
python3 swfvs.py
```
- Loads Utah teapot from CSV in `objects/`
- No MongoDB needed
- Fastest startup

### Option B: Load from MongoDB

#### 1. Start FastAPI server (in one terminal):
```bash
uvicorn server:app --reload
```
- Server runs on http://localhost:8000
- Exposes endpoints like: `/db/3dObjects/vertices/0` (all vertices)

#### 2. Run viewer (in another terminal):
```python
# In swfvs.py, change line 15:
INPUT_DATA_SOURCE = 'db'  # Instead of 'file'

# Then run:
python3 swfvs.py
```

---

## Troubleshooting

### "Connection refused" (Local MongoDB)

**Problem**: `docker: command not found` or Docker not running

**Solution**:
- Open Docker Desktop app
- Wait for it to start
- Run `docker run ...` command again

Or use Option 1 (MongoDB Atlas) instead.

### "Connection timeout" (Atlas)

**Problem**: Can't connect to cluster

**Checklist**:
- [ ] Correct username and password (case-sensitive!)
- [ ] Network access allows your IP ("Add IP Address" → "Allow access from anywhere")
- [ ] Cluster is running (check Atlas dashboard)
- [ ] Internet connection is working

### "Database 'test' not found"

**Problem**: Connection string points to wrong database

**Solution**: The connection string in `server.py` includes `/test` at the end. PyTracer creates `3dObjects` database automatically when you run the setup script.

### Script fails with "No module named 'pymongo'"

**Solution**: Install dependencies
```bash
pip3 install -r requirements.txt
```

---

## MongoDB Collections Schema

### vertices
```json
{
  "_id": ObjectId(...),
  "x": -3.0,
  "y": 1.8,
  "z": 0.0,
  "id": 1
}
```

### surfaces
```json
{
  "_id": ObjectId(...),
  "x": 2909,    // vertex index 1
  "y": 2921,    // vertex index 2
  "z": 2939,    // vertex index 3
  "id": 1
}
```

**Note**: The `id` field is included in MongoDB but filtered out by the API (projection: `{'id':0,'_id':0}`).

---

## Quick Start (Copy & Paste)

### Atlas (if you have credentials):
```bash
python3 setup_mongodb.py atlas
# Enter username when prompted
# Enter password when prompted
```

### Local (with Docker running):
```bash
python3 setup_mongodb.py local
```

### Test it:
```bash
# Load from file (always works):
python3 swfvs.py

# Load from MongoDB (after setup):
# Edit swfvs.py line 15: INPUT_DATA_SOURCE = 'db'
# In another terminal: uvicorn server:app --reload
# Then: python3 swfvs.py
```

---

## Verify Installation

After running `setup_mongodb.py`, you should have:
- ✅ `credentials.py` (gitignored, safe for secrets)
- ✅ MongoDB database `3dObjects` with 2 collections
- ✅ ~3,643 vertices and ~6,319 surfaces in MongoDB

Test with:
```bash
python3 -c "from credentials import *; print('credentials.py loaded')"
```

Should print: `credentials.py loaded`

---

## Next Steps

1. **Run setup**:
   - `python3 setup_mongodb.py atlas` (easiest)
   - or `python3 setup_mongodb.py local` (if Docker ready)

2. **Test file loading** (always works):
   - `python3 swfvs.py`
   - Should render teapot wireframe
   - Press 'c' to center, arrow keys to pan, +/- to zoom

3. **Test MongoDB loading** (optional):
   - Start server: `uvicorn server:app --reload`
   - Set `INPUT_DATA_SOURCE = 'db'` in `swfvs.py`
   - Run `python3 swfvs.py`
   - Should load same teapot from MongoDB

4. **Continue with v2 roadmap**:
   - `git checkout v2`
   - `cat V2_ROADMAP.md`
   - Start fixing bugs and optimizing
