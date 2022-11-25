# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Helpers to load vertices and surfaces from file

import csv
import surface as S
import vertex as V
import requests
import json

DEV_API_ENDPOINT_VERTICES = 'http://127.0.0.1:8000/db/3dobject/vertices/1'
DEV_API_ENDPOINT_SURFACES = 'http://127.0.0.1:8000/db/3dobject/surfaces/1'

def load_vertices():
    fn = './objects/utah_teapot_vertices.csv'
    vl = V.vertices()
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                v = V.vertex(wx=float(row[0]),wy=float(row[1]),wz=float(row[2]))  # type: ignore
                vl.add_vertex(v)
            line_count += 1
    return(vl)    

def load_vertices_db():

    r = requests.get(DEV_API_ENDPOINT_VERTICES)
    r.encoding='UTF-8'
    j = json.loads(r.text)
    
    vl = V.vertices()
    
    for i in j:
        v = V.vertex(wx=float(i['x']),wy=float(i['y']),wz=float(i['z']))  # type: ignore
        vl.add_vertex(v)

    return(vl)

def load_surfaces():
    surfaces = S.surface()
    fn = './objects/utah_teapot_faces.csv'
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0: 
                face = S.surface_cell()
                face.add_face_index(row)
                surfaces.add_face(face)
            line_count += 1
    return(surfaces)

def load_surfaces_db():
    surfaces = S.surface()
    r = requests.get(DEV_API_ENDPOINT_SURFACES)
    r.encoding='UTF-8'
    j = json.loads(r.text)

    for i in j:
        a = []
        a.append(i['x'])
        a.append(i['y'])
        a.append(i['z'])
        face = S.surface_cell()
        face.add_face_index(a)
        surfaces.add_face(face)
    
    return(surfaces)

if __name__ == '__main__':

    vertex_list = load_vertices()
    print("No vertices in file: " + str(vertex_list.vertex_count()))
    
    surface_list = load_surfaces()
    print("No surfaces in file: " + str(surface_list.surface_count()))

    vertex_list2 = load_vertices_db()
    print("No vertices in db: " + str(vertex_list2.vertex_count()))

    surface_list2 = load_surfaces_db()
    print("No surfaces in db: " + str(surface_list2.surface_count()))

