# Author: Dominic Williams
# Date created: 14 Aug 2022
# 
# Unit tests for vertex module

import vertex 

def test_create_vertex_object():
    v = vertex.vertex(x_world=0.0,y_world=1.0,z_world=0.1)
    assert v.x_world == 0
    assert v.y_world == 1
    assert v.z_world == 0.1

def test_create_vertices_object():
    l = vertex.vertices()
    v = vertex.vertex(x_world=0.0,y_world=0.0,z_world=0.0)
    assert l.vertex_count() == 0
    l.add_vertex(v)
    assert l.vertex_count() == 1


