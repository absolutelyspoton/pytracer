# Author: Dominic Williams
# Date created: 10 Aug 2022
#
# Loaders for mesh geometry from file or API. v3: both sources produce a
# mesh.Mesh (numpy arrays).

import numpy as np
import requests
import json
import mesh

DEV_API_BASE = 'http://127.0.0.1:8000/db/3dObjects'
OBJECTS_DIR = './objects'
DEFAULT_OBJECT = 'utah_teapot'


def list_objects():
    """Object names available in objects/ (every *_vertices.csv pair)."""
    import glob
    import os
    names = []
    for path in glob.glob(f'{OBJECTS_DIR}/*_vertices.csv'):
        base = os.path.basename(path)
        if base.endswith('_vertices_mdb.csv'):
            continue
        name = base[:-len('_vertices.csv')]
        if os.path.exists(f'{OBJECTS_DIR}/{name}_faces.csv'):
            names.append(name)
    return sorted(names)


def load_mesh_file(name=DEFAULT_OBJECT):
    """Load an object's mesh from its CSV pair as numpy arrays.

    Face CSVs hold 1-based vertex indices; Mesh uses 0-based.
    """
    verts = np.genfromtxt(f'{OBJECTS_DIR}/{name}_vertices.csv',
                          delimiter=',', skip_header=1, dtype=np.float64)
    faces = np.genfromtxt(f'{OBJECTS_DIR}/{name}_faces.csv',
                          delimiter=',', skip_header=1, dtype=np.int32) - 1
    return mesh.Mesh(verts, faces)


def load_mesh_api(name=DEFAULT_OBJECT):
    """Load an object's mesh from the FastAPI service as numpy arrays.

    Objects live in collections named {name}_vertices / {name}_surfaces;
    the Utah teapot also exists in the legacy unprefixed collections, used
    as a fallback for older databases.
    """
    def fetch(table):
        r = requests.get(f'{DEV_API_BASE}/{table}/1')
        r.encoding = 'UTF-8'
        return json.loads(r.text)

    try:
        vdata = fetch(f'{name}_vertices')
        fdata = fetch(f'{name}_surfaces')
        if not vdata or not fdata:
            raise ValueError('empty collection')
    except Exception:
        if name != DEFAULT_OBJECT:
            raise
        vdata = fetch('vertices')     # legacy teapot collections
        fdata = fetch('surfaces')

    verts = [(item['x'], item['y'], item['z']) for item in vdata]
    faces = [(int(item['x']) - 1, int(item['y']) - 1, int(item['z']) - 1)
             for item in fdata]
    return mesh.Mesh(verts, faces)
