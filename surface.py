# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for surfaces ( collection of faces ( list of indexes to vertices ))

from pydantic import BaseModel
from typing import List, Optional

class surface_cell(BaseModel):
    vertex_list: List = []
    normal: List = []
    culled = False
    index:Optional[int] = 0

    def CalcNormal(self):
        
        for i in self.vertex_list:
            print(i)
            
            # # First calculate colinnear vectors
            # a = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
            # b = [v3[0]-v2[0],v3[1]-v2[1],v3[2]-v2[2]]

            # # Calculate the normal and return it
            # x = a[1] * b[2] - a[2] * b[1]
            # y = a[2] * b[0] - a[0] * b[2]
            # z = a[0] * b[1] - a[1] * b[0]

            # self.surface_normal = [x,y,z]

    # add index to the index list for this face
    def add_face_index(self,vl:List):
        self.vertex_list = vl

    # return the number of vertex indices for this face
    def face_index_count(self):
        return(len(self.vertex_list)) 

class surface(BaseModel):
    surface_list: List = []

    def add_face(self,f:surface_cell) -> None:
        self.surface_list.append(f)
        return None

    def surface_count(self) -> int:
        return(len(self.surface_list))


