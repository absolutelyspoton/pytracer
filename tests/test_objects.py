# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for object generation, the object registry, floor patterns,
# and ray-trace progress reporting

import numpy as np

import camera
import light
import loader
import mesh
import tracer
import viewport


def test_make_torus_geometry():
    t = mesh.make_torus(major=2.2, minor=1.0, seg_u=48, seg_v=24)
    assert t.vertex_count() == 48 * 24
    assert t.face_count() == 48 * 24 * 2
    # Unit normals
    assert np.allclose(np.linalg.norm(t.face_normals, axis=1), 1.0)
    # Normals point outward from the tube surface
    v = t.vertices
    spine = v.copy()
    spine[:, 1] = 0.0
    spine = spine / np.linalg.norm(spine, axis=1, keepdims=True) * 2.2
    outward = v - spine
    outward /= np.linalg.norm(outward, axis=1, keepdims=True)
    agree = np.einsum('ij,ij->i', t.vertex_normals, outward)
    assert agree.min() > 0.99


def test_torus_is_closed():
    # Every edge of a closed mesh is shared by exactly two faces
    t = mesh.make_torus(seg_u=12, seg_v=8)
    edges = {}
    for f in t.faces:
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            key = (min(a, b), max(a, b))
            edges[key] = edges.get(key, 0) + 1
    assert all(count == 2 for count in edges.values())


def test_list_objects_finds_both():
    names = loader.list_objects()
    assert 'utah_teapot' in names
    assert 'torus' in names


def test_load_torus_from_file():
    t = loader.load_mesh_file('torus')
    assert t.vertex_count() == 48 * 24


def floor_only_render(pattern):
    verts = np.array([
        [-30.0, 2.0, 0.5], [30.0, 2.0, 0.5],
        [30.0, 2.0, 30.0], [-30.0, 2.0, 30.0]])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    vnorms = np.array([[0.0, -1.0, 0.0]] * 4)
    vp = viewport.Viewport(x=0, y=0, width=40, height=30)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    return tracer.render_still(verts, faces, vnorms, np.array([True, True]),
                               cam, vp, light.Light(), shadows_on=False,
                               bounces=0, floor_pattern=pattern)


def test_floor_patterns_are_distinct():
    images = {p: floor_only_render(p) for p in
              ('checker', 'stripes', 'rings', 'plain')}
    # Plain has a single floor shade; the others have two
    assert len(np.unique(images['plain'][:, 20:, 0])) == 1
    for p in ('checker', 'stripes', 'rings'):
        assert len(np.unique(images[p][:, 20:, 0])) == 2
    # The patterned layouts differ from each other
    assert not np.array_equal(images['checker'], images['stripes'])
    assert not np.array_equal(images['checker'], images['rings'])
    assert not np.array_equal(images['stripes'], images['rings'])


def test_progress_is_monotonic_and_completes():
    fractions = []
    floor_only = floor_only_render  # reuse scene shape
    verts = np.array([
        [-30.0, 2.0, 0.5], [30.0, 2.0, 0.5],
        [30.0, 2.0, 30.0], [-30.0, 2.0, 30.0]])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    vnorms = np.array([[0.0, -1.0, 0.0]] * 4)
    vp = viewport.Viewport(x=0, y=0, width=40, height=30)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    tracer.render_still(verts, faces, vnorms, np.array([True, True]),
                        cam, vp, light.Light(), shadows_on=True, bounces=1,
                        progress=fractions.append)
    assert fractions
    assert fractions == sorted(fractions)
    assert 0.0 <= fractions[0]
    assert fractions[-1] == 1.0
