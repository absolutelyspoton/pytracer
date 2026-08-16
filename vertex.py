# Author: Dominic Williams
# Date created: 10 Aug 2022
# vertex: 3D vertex with world/view/screen coordinates
# vertices: Container for vertex collection

import matrix

class vertex:
    __slots__ = ['x_world', 'y_world', 'z_world',
                 'x_view', 'y_view', 'z_view',
                 'x_screen', 'y_screen', 'z_screen',
                 'index', 'normal']

    def __init__(self, x_world=0.0, y_world=0.0, z_world=0.0):
        self.x_world = x_world
        self.y_world = y_world
        self.z_world = z_world
        self.x_view = 0.0
        self.y_view = 0.0
        self.z_view = 0.0
        self.x_screen = 0.0
        self.y_screen = 0.0
        self.z_screen = 0.0
        self.index = 0
        self.normal = None

    def calc_view_coordinates(self, M) -> None:
        t = matrix.MatrixVector(M, [self.x_world, self.y_world, self.z_world])
        self.x_view = t[0]
        self.y_view = t[1]
        self.z_view = t[2]

    def calc_screen_coordinates(self, M) -> None:
        t = matrix.MatrixVector(M, [self.x_view, self.y_view, self.z_view])
        self.x_screen = t[0]
        self.y_screen = t[1]
        self.z_screen = t[2]

    def calc_normal(self, normal) -> None:
        self.normal = normal

class vertices:
    def __init__(self):
        self.vertex_list = []

    def add_vertex(self, v: vertex):
        self.vertex_list.append(v)

    def vertex_count(self):
        return len(self.vertex_list)

if __name__ == '__main__':

    w1 = vertex(x_world=1.0,y_world=2.0,z_world=3.0)
    w2 = vertex(x_world=4.0,y_world=5.0,z_world=6.0)
    
    vl = vertices() 

    vl.add_vertex(w1)
    vl.add_vertex(w2)

    print(vl)
    
