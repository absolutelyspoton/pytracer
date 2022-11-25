# Author: Dominic Williams
# Date created: 14 Aug 2022
# 
# Unit tests for vertex module

import vertex 

def test_create_vertex_object1():
    v = vertex.vertex(x=0.0,y=0.0,z=0.0)
    assert v.wx ==0
    assert v.wy == 0
    assert v.wx == 0


def test_create_vertex_object2():    
    v = vertex.vertex(x=0.0,y=0.0,z=0.0)
    assert v.wx ==0
    assert v.wy == 0
    assert v.wx == 0

def test_create_vertices_object():
    l = vertex.vertices()
    v = vertex.vertex(wx=0.0,wy=0.0,wz=0.0)
    assert l.vertex_count() == 0
    l.add_vertex(v)
    assert l.vertex_count() == 1


