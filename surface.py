class face:

    face_list = []

    def add_face_index(self,index):
        self.face_list.append(index)

    def face_count(self):
        return(len(self.face_list))

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
