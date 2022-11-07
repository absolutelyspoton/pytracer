# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Helpers to load vertices and surfaces from file

import csv
import surface
import vertex

def load_vertices():
    fn = './objects/utah_teapot_vertices.csv'
    vertices = vertex.vertices()
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                v = vertex.vertex(x=float(row[0]),y=float(row[1]),z=float(row[2]))
                vertices.add_vertex(v)
            line_count += 1
    return(vertices)    

def load_surfaces():
    surfaces = surface.surface()
    fn = './objects/utah_teapot_faces.csv'
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
    print("No vertices: " + str(vertices.vertex_count()))
    
    surfaces = load_surfaces()
    print("No surfaces: " + str(surfaces.surface_count()))

else :
    print(__file__)
    print(__name__)