# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for modelling vertices

from pydantic import BaseModel
from typing import List
from devtools import debug

class vertex(BaseModel):
    x:float
    y:float
    z:float

    def normal(self,normal):
        self.normal = normal

class vertices:
    vertex_list: List = []

    def add_vertex(self,v:vertex):
        self.vertex_list.append(v)

    def vertex_count(self):
        return(len(self.vertex_list))

if __name__ == '__main__':

    v1 = vertex(x=1.0,y=2.0,z=3.0)
    v2 = vertex(x=2.0,y=3.0,z=4.0)
    
    vl = vertices() 

    vl.add_vertex(v1)
    vl.add_vertex(v2)

    debug(vl.vertex_count())
    debug(vl.vertex_list[0].x)


else :
    debug(__file__)
    debug(__name__)
        
