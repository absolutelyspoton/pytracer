# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for modelling vertices

from pydantic import BaseModel
from typing import List, Optional
from devtools import debug
import matrix
import math

class vertex(BaseModel):
    wx:float = 0.0
    wy:float = 0.0
    wz:float = 0.0
    tx:Optional[float] = 0.0
    ty:Optional[float] = 0.0
    tz:Optional[float] = 0.0
    vx:Optional[float] = 0.0
    vy:Optional[float] = 0.0
    vz:Optional[float] = 0.0

    # calc linear transform of world coordinates to transformed coordinates, store results
    def calc_transform(self,I) -> None:
        t = matrix.MatrixVector(I,[self.wx,self.wy,self.wz])
        self.tx = t[0] 
        self.ty = t[1] 
        self.tz = t[2] 
        return None

    def calc_normal(self,normal) -> None:
        self.normal = normal
        return None


class vertices(BaseModel):
    vertex_list: List = []

    def add_vertex(self,v:vertex):
        self.vertex_list.append(v)

    def vertex_count(self):
        return(len(self.vertex_list))

if __name__ == '__main__':

    w1 = vertex(wx=1.0,wy=2.0,wz=3.0)
    w2 = vertex(wx=4.0,wy=5.0,wz=6.0)
    
    vl = vertices() 

    vl.add_vertex(w1)
    vl.add_vertex(w2)
    
