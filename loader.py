# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Helpers to load vertices and surfaces from file

import csv
import surface
import vertex

def load_vertices():
    fn = 'utah_teapot_vertices.csv'
    vertices = vertex.vertices()
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                v = vertex.vertex(row[0],row[1],row[2])
                vertices.add_vertex(v)
            line_count += 1
    return(vertices)    

def load_surfaces():
    surfaces = surface.surface()
    fn = 'utah_teapot_faces.csv'
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0: 
                face = surface.face()
                face.add_face_index(row)
                #surfaces.add_face(row)
                surfaces.add_face(face)
            line_count += 1
    return(surfaces)

if __name__ == '__main__':
    vertices = load_vertices()
    surfaces = load_surfaces()
    print(__file__)
else :
    print(__name__)