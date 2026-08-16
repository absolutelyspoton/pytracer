# Author: Dominic Williams
# Date created: 10 Aug 2022
# surface_cell: Single triangular face with vertices and normal
# surface: Container for face collection

class surface_cell:
    __slots__ = ['vertex_list', 'normal', 'culled', 'index']

    def __init__(self):
        self.vertex_list = []
        self.normal = None
        self.culled = False
        self.index = 0

    def add_face_index(self, vl):
        self.vertex_list = vl

    def face_index_count(self):
        return len(self.vertex_list)

class surface:
    def __init__(self):
        self.surface_list = []

    def add_face(self, f: surface_cell) -> None:
        self.surface_list.append(f)

    def surface_count(self) -> int:
        return len(self.surface_list)


