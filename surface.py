# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Classes for surfaces ( collection of faces ( list of indexes to vertices ))
 
class face:

    # list of indexes to vertices
    index_list = []

    # add index to the index list
    def add_face_index(self,index):
        self.index_list.append(index)

    def face_index_count(self):
        return(len(self.index_list))

    def __init__(self):
        return 0

class surface:

    surface_list = []

    def add_face(self,face):
        self.surface_list.append(face)

    def surface_count(self):
        return(len(self.surface_list))

    def __init__(self):
        return
