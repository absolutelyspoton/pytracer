# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for surfaces ( collection of faces ( list of indexes to vertices ))
 
class face:

    # list of indexes to vertices
    vertex_list = []
    normal = []

    # add index to the index list for this face
    def add_face_index(self,vl):
        self.vertex_list = vl

    # return the number of vertex indices for this face
    def face_index_count(self):
        return(len(self.index_list))

    def calcNormal(self,v1,v2,v3):
            
        # First calculate colinnear vectors
        vect1 = [v3[0]-v2[0],v3[1]-v2[1],v3[2]-v2[2]]
        vect2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        # Calculate the norm
        x = vect1[1] * vect2[2] - vect1[2] * vect2[1]
        y = vect1[2] * vect2[0] - vect1[0] * vect2[2]
        z = vect1[0] * vect2[1] - vect1[1] * vect2[0]
        # Store it
        self.normal = [x,y,z]

    # initialise class
    def __init__(self):
        return None

class surface:

    surface_list = []

    def add_face(self,face):
        self.surface_list.append(face)

    def surface_count(self):
        return(len(self.surface_list))

    def __init__(self):
        return
