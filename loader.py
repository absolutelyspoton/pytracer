# Author: Dominic Williams
# Date created: 10 Aug 2022
#
# Loaders for vertices and surfaces from file or API

import csv
import surface as S
import vertex as V
import requests
import json
import pymongo
import matrix

DEV_API_ENDPOINT_VERTICES = 'http://127.0.0.1:8000/db/3dObjects/vertices/1'
DEV_API_ENDPOINT_SURFACES = 'http://127.0.0.1:8000/db/3dObjects/surfaces/1'

def _load_vertices_generic(data_source):
    """Load vertices from an iterable of (x, y, z) tuples."""
    vl = V.vertices()
    for idx, (x, y, z) in enumerate(data_source, start=1):
        v = V.vertex(x_world=float(x), y_world=float(y), z_world=float(z))
        v.index = idx
        vl.add_vertex(v)
    return vl

def _load_surfaces_generic(data_source):
    """Load surfaces from an iterable of vertex-index lists."""
    surfaces = S.surface()
    for idx, indices in enumerate(data_source, start=1):
        face = S.surface_cell()
        face.index = idx
        face.add_face_index([int(x) for x in indices])
        surfaces.add_face(face)
    return surfaces

def load_vertices_file():
    """Load vertices from CSV file."""
    fn = './objects/utah_teapot_vertices.csv'
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)  # skip header
        return _load_vertices_generic((row[0], row[1], row[2]) for row in csv_reader)

def load_vertices_api():
    """Load vertices from API endpoint."""
    r = requests.get(DEV_API_ENDPOINT_VERTICES)
    r.encoding = 'UTF-8'
    data = json.loads(r.text)
    return _load_vertices_generic((item['x'], item['y'], item['z']) for item in data)

def load_surfaces_file():
    """Load surfaces from CSV file."""
    fn = './objects/utah_teapot_faces.csv'
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)  # skip header
        return _load_surfaces_generic((row[0], row[1], row[2]) for row in csv_reader)

def load_surfaces_api():
    """Load surfaces from API endpoint."""
    r = requests.get(DEV_API_ENDPOINT_SURFACES)
    r.encoding = 'UTF-8'
    data = json.loads(r.text)
    return _load_surfaces_generic((item['x'], item['y'], item['z']) for item in data)

def compute_surface_normals(surfaces, vertices):
    """Calculate and cache surface normals from vertex positions.

    Surface normals are mesh-invariant (never change), so they should be
    computed once at load time, not every frame. This function calculates
    normals for all surfaces and stores them.

    Args:
        surfaces: surface collection with faces
        vertices: vertices collection with world coordinates
    """
    print('computing surface normals from vertex positions ...')
    for face in surfaces.surface_list:
        # Surface vertex indices are 1-based; convert to 0-based for array access
        v1_idx = face.vertex_list[0] - 1
        v2_idx = face.vertex_list[1] - 1
        v3_idx = face.vertex_list[2] - 1

        # Get world coordinates for each vertex
        v1 = vertices.vertex_list[v1_idx]
        v2 = vertices.vertex_list[v2_idx]
        v3 = vertices.vertex_list[v3_idx]

        # Calculate and normalize the surface normal
        normal = matrix.CalcSurfaceNormal(
            [v1.x_world, v1.y_world, v1.z_world],
            [v2.x_world, v2.y_world, v2.z_world],
            [v3.x_world, v3.y_world, v3.z_world]
        )
        face.normal = matrix.NormaliseVector(normal)
    print('... done')

if __name__ == '__main__':

    print("Loading vertices from file")
    vertex_list = load_vertices_file()
    print("No vertices in file: " + str(vertex_list.vertex_count()))

    print("Loading surfaces from file")
    surface_list = load_surfaces_file()
    print("No surfaces in file: " + str(surface_list.surface_count()))

    print("Loading vertices from api")
    vertex_list2 = load_vertices_api()
    print("No vertices in db: " + str(vertex_list2.vertex_count()))

    print("Loading surfaces from api")
    surface_list2 = load_surfaces_api()
    print("No surfaces in db: " + str(surface_list2.surface_count()))

