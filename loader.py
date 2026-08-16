# Author: Dominic Williams
# Date created: 10 Aug 2022
#
# Loaders for mesh geometry from file or API. v3: both sources produce a
# mesh.Mesh (numpy arrays).

import numpy as np
import requests
import json
import mesh

DEV_API_ENDPOINT_VERTICES = 'http://127.0.0.1:8000/db/3dObjects/vertices/1'
DEV_API_ENDPOINT_SURFACES = 'http://127.0.0.1:8000/db/3dObjects/surfaces/1'

VERTICES_CSV = './objects/utah_teapot_vertices.csv'
FACES_CSV = './objects/utah_teapot_faces.csv'


def load_mesh_file():
    """Load the mesh from the CSV pair as numpy arrays.

    Face CSVs hold 1-based vertex indices; Mesh uses 0-based.
    """
    verts = np.genfromtxt(VERTICES_CSV, delimiter=',', skip_header=1,
                          dtype=np.float64)
    faces = np.genfromtxt(FACES_CSV, delimiter=',', skip_header=1,
                          dtype=np.int32) - 1
    return mesh.Mesh(verts, faces)


def load_mesh_api():
    """Load the mesh from the FastAPI service as numpy arrays."""
    rv = requests.get(DEV_API_ENDPOINT_VERTICES)
    rv.encoding = 'UTF-8'
    verts = [(item['x'], item['y'], item['z']) for item in json.loads(rv.text)]
    rf = requests.get(DEV_API_ENDPOINT_SURFACES)
    rf.encoding = 'UTF-8'
    faces = [(int(item['x']) - 1, int(item['y']) - 1, int(item['z']) - 1)
             for item in json.loads(rf.text)]
    return mesh.Mesh(verts, faces)
