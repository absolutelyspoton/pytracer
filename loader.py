# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Helpers to load vertices and surfaces from file

import csv
import surface as S
import vertex as V
import requests
import json
import pymongo
import matrix

DEV_API_ENDPOINT_VERTICES = 'http://127.0.0.1:8000/db/3dObjects/vertices/1'
DEV_API_ENDPOINT_SURFACES = 'http://127.0.0.1:8000/db/3dObjects/surfaces/1'

def load_vertices_file():
    fn = './objects/utah_teapot_vertices.csv'
    vl = V.vertices()
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                v = V.vertex(x_world=float(row[0]),y_world=float(row[1]),z_world=float(row[2]))  # type: ignore
                v.index = line_count
                vl.add_vertex(v)
            line_count += 1
    return(vl)    

def load_vertices_api():

    r = requests.get(DEV_API_ENDPOINT_VERTICES)
    r.encoding='UTF-8'
    j = json.loads(r.text)
    
    vl = V.vertices()
    
    record_count = 1
    for i in j:
        v = V.vertex(x_world=i['x'],y_world=i['y'],z_world=i['z']) 
        v.index = record_count
        vl.add_vertex(v)
        record_count+=1

    return(vl)

def load_surfaces_file():
    surfaces = S.surface()
    fn = './objects/utah_teapot_faces.csv'
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                face = S.surface_cell()
                face.index = line_count
                face.add_face_index([int(x) for x in row])
                surfaces.add_face(face)
            line_count += 1
    return(surfaces)

def load_surfaces_api():
    surfaces = S.surface()
    r = requests.get(DEV_API_ENDPOINT_SURFACES)
    r.encoding='UTF-8'
    j = json.loads(r.text)

    index = 1
    for i in j:
        a = []
        a.append(i['x'])
        a.append(i['y'])
        a.append(i['z'])
        face = S.surface_cell()
        face.index = index
        face.add_face_index(a)
        surfaces.add_face(face)
        index +=1
    
    return(surfaces)

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

