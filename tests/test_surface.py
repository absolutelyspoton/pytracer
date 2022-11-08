# Author: Dominic Williams
# Date created: 14 Aug 2022
# 
# Unit tests for vertex module

import surface 

def test_create_surface_object1():
    f = surface.face()
    s = surface.surface()
    s.add_face(f)
    assert s.surface_count() == 1
