# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for surfaces ( collection of faces ( list of indexes to vertices ))

from pydantic import BaseModel
from typing import List

class surface_cell(BaseModel):
    vertex_list: List = []
    normal: List = []
    culled = False

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


