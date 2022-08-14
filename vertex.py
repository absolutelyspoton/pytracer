# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for modelling vertices


class vertex:

    def normal(self,normal):
        self.normal = normal

    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z

class vertices:

    vertex_list = []

    def add_vertex(self,v):
        self.vertex_list.append(v)

    def vertex_count(self):
        return(len(self.vertex_list))

    def __init__(self):
        return


if __name__ == '__main__':

    print(__file__)

    v1 = vertex(1,2,3)
    v2 = vertex(2,3,4)
    
    vl = vertices() 

    vl.add_vertex(v1)
    vl.add_vertex(v2)

    print(vl.vertex_count())
    print(vl.vertex_list[0].x)


else :
    print(__name__)
        
