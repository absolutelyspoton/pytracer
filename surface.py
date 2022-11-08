# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for surfaces ( collection of faces ( list of indexes to vertices ))

from pydantic import BaseModel
from typing import List
from devtools import debug

class face:

    vertex_list: List = []
    normal: List = []

    # add index to the index list for this face
    def add_face_index(self,vl:List):
        self.vertex_list = vl

    # return the number of vertex indices for this face
    def face_index_count(self):
        return(len(self.vertex_list)) 

    def calcNormal(self,v1,v2,v3):
            
        # First calculate colinnear vectors
        vect1 = [v3[0]-v2[0],v3[1]-v2[1],v3[2]-v2[2]]
        vect2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]

        # Calculate the normal
        x = vect1[1] * vect2[2] - vect1[2] * vect2[1]
        y = vect1[2] * vect2[0] - vect1[0] * vect2[2]
        z = vect1[0] * vect2[1] - vect1[1] * vect2[0]

        # Store it
        self.normal = [x,y,z]

class surface:

    surface_list: List = []

    def add_face(self,f:face):
        self.surface_list.append(f)

    def surface_count(self):
        return(len(self.surface_list))


