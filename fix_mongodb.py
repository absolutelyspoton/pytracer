#!/usr/bin/env python3
"""
Fix MongoDB data: assign proper sequential IDs to vertices and surfaces.

The CSV import set all documents to id=1, but we need:
- Each vertex to have id=1 to 3644 (its row number)
- Surfaces already have correct x,y,z indices (1-based vertex references)
"""

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['3dObjects']

print("Fixing MongoDB data...")

# Fix vertices: assign sequential IDs
vertices = db['vertices']
vertex_docs = list(vertices.find().sort('_id', 1))

for i, doc in enumerate(vertex_docs, start=1):
    vertices.update_one({'_id': doc['_id']}, {'$set': {'id': i}})

print(f"✓ Updated {len(vertex_docs)} vertices with sequential IDs (1-{len(vertex_docs)})")

# Verify vertex IDs
max_v = vertices.find_one(sort=[('id', -1)])['id']
print(f"✓ Max vertex ID: {max_v}")

# Verify surfaces reference valid vertices
surfaces = db['surfaces']
surface_docs = list(surfaces.find())

invalid_count = 0
for i, doc in enumerate(surface_docs, start=1):
    # Check each vertex reference is within range
    for field in ['x', 'y', 'z']:
        if doc[field] < 1 or doc[field] > max_v:
            invalid_count += 1
            print(f"  Invalid reference in surface {i}: {field}={doc[field]}")

if invalid_count == 0:
    print(f"✓ All {len(surface_docs)} surfaces have valid vertex references (1-{max_v})")
else:
    print(f"⚠ {invalid_count} invalid references found")

# Fix surface IDs as well (should be 1 to num_surfaces)
for i, doc in enumerate(surface_docs, start=1):
    surfaces.update_one({'_id': doc['_id']}, {'$set': {'id': i}})

print(f"✓ Updated {len(surface_docs)} surfaces with sequential IDs (1-{len(surface_docs)})")

# Final validation
v_count = vertices.count_documents({})
s_count = surfaces.count_documents({})
print(f"\n✓ Setup Complete:")
print(f"  Vertices: {v_count}")
print(f"  Surfaces: {s_count}")

client.close()
