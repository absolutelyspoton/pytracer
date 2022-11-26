# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for modelling vertices

from pydantic import BaseModel
from typing import List, Optional
import matrix

class vertex(BaseModel):
    x_world:float = 0.0
    y_world:float = 0.0
    z_world:float = 0.0
    x_view:Optional[float] = 0.0
    y_view:Optional[float] = 0.0
    z_view:Optional[float] = 0.0
    x_screen:Optional[float] = 0.0
    y_screen:Optional[float] = 0.0
    z_screen:Optional[float] = 0.0
    index:Optional[int] = 0
    normal:Optional[List] = []

    # calc linear transform of world coordinates to transformed coordinates, store results
    def calc_view_coordinates(self,I) -> None:
        t = matrix.MatrixVector(I,[self.x_world,self.y_world,self.z_world])
        self.x_view = t[0] 
        self.y_view = t[1] 
        self.z_view = t[2] 
        # s = matrix.MatrixMult(matrix.OrthographicMatrix(),[self.x_view,self.y_view,self.z_view])

        return None

    def calc_screen_coordinates(self,I) -> None:
        t = matrix.MatrixVector(I,[self.x_view,self.y_view,self.z_view])
        self.x_screen = t[0] 
        self.y_screen = t[1] 
        self.z_screen = t[2] 

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

    w1 = vertex(x_world=1.0,y_world=2.0,z_world=3.0)
    w2 = vertex(x_world=4.0,y_world=5.0,z_world=6.0)
    
    vl = vertices() 

    vl.add_vertex(w1)
    vl.add_vertex(w2)

    print(vl)
    
