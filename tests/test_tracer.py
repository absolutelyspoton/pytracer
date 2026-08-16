# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the batched ray tracer

import numpy as np

import light
import tracer
import viewport
import camera


def one_triangle_scene():
    # Triangle in the z=5 plane around the axis
    verts = np.array([[-1.0, -1.0, 5.0], [1.0, -1.0, 5.0], [0.0, 1.5, 5.0]])
    faces = np.array([[0, 1, 2]])
    vnorms = np.array([[0.0, 0.0, -1.0]] * 3)
    is_floor = np.array([False])
    return tracer.Scene(verts, faces, vnorms, is_floor)


def test_ray_hits_triangle_at_known_distance():
    scene = one_triangle_scene()
    o = np.array([[0.0, 0.0, 0.0]])
    d = np.array([[0.0, 0.0, 1.0]])
    hit = tracer.intersect(scene, o, d)
    assert hit['face'][0] == 0
    assert abs(hit['t'][0] - 5.0) < 1e-9
    # Hit point from barycentrics matches the ray equation
    u, v = hit['u'][0], hit['v'][0]
    p = (1 - u - v) * scene.vertices[0] + u * scene.vertices[1] \
        + v * scene.vertices[2]
    assert np.allclose(p, [0.0, 0.0, 5.0])


def test_ray_misses_beside_and_behind():
    scene = one_triangle_scene()
    o = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 10.0]])
    d = np.array([[1.0, 0.0, 0.1], [0.0, 0.0, 1.0]])  # beside; behind
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    hit = tracer.intersect(scene, o, d)
    assert hit['face'][0] == -1
    assert hit['face'][1] == -1
    assert np.isinf(hit['t']).all()


def test_two_sided_intersection():
    # Same triangle hit from behind still intersects
    scene = one_triangle_scene()
    o = np.array([[0.0, 0.0, 10.0]])
    d = np.array([[0.0, 0.0, -1.0]])
    hit = tracer.intersect(scene, o, d)
    assert hit['face'][0] == 0
    assert abs(hit['t'][0] - 5.0) < 1e-9


def test_any_hit_shadow_ray():
    scene = one_triangle_scene()
    lt = light.Light(direction=(0.0, 0.0, -1.0))  # light shines toward -z
    # Point behind the triangle looking toward the light (+z toward light
    # means to_light = (0,0,1)): the triangle blocks it
    o = np.array([[0.0, 0.0, 8.0], [5.0, 0.0, 8.0]])
    d = np.broadcast_to(np.asarray(lt.to_light), (2, 3)).copy()
    hit = tracer.intersect(scene, o, d, any_hit=True)
    assert hit['face'][0] == -1  # to_light = -direction = (0,0,1): away
    # Aim back toward the triangle instead
    d2 = np.array([[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]])
    hit2 = tracer.intersect(scene, o, d2, any_hit=True)
    assert hit2['face'][0] == 0   # occluded
    assert hit2['face'][1] == -1  # clear off to the side


def test_nearest_of_two_triangles_wins():
    verts = np.array([[-1, -1, 5.0], [1, -1, 5.0], [0, 1.5, 5.0],
                      [-1, -1, 3.0], [1, -1, 3.0], [0, 1.5, 3.0]])
    faces = np.array([[0, 1, 2], [3, 4, 5]])
    vnorms = np.array([[0.0, 0.0, -1.0]] * 6)
    scene = tracer.Scene(verts, faces, vnorms, np.array([False, False]))
    hit = tracer.intersect(scene, np.zeros((1, 3)),
                           np.array([[0.0, 0.0, 1.0]]))
    assert hit['face'][0] == 1
    assert abs(hit['t'][0] - 3.0) < 1e-9


def test_render_still_shadow_region_is_darker():
    # Small occluder above a floor, traced at low resolution
    verts = np.array([
        [-1.0, -1.0, 5.0], [1.0, -1.0, 5.0], [0.0, -2.5, 5.5],  # occluder
        [-30.0, 2.0, 0.5], [30.0, 2.0, 0.5],
        [30.0, 2.0, 30.0], [-30.0, 2.0, 30.0],                  # floor
    ])
    faces = np.array([[0, 1, 2], [3, 4, 5], [3, 5, 6]])
    vnorms = np.array([[0.0, 0.0, -1.0]] * 3 + [[0.0, -1.0, 0.0]] * 4)
    is_floor = np.array([False, True, True])

    vp = viewport.Viewport(x=0, y=0, width=80, height=60)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    lt = light.Light()

    img = tracer.render_still(verts, faces, vnorms, is_floor, cam, vp, lt,
                              shadows_on=True, bounces=1)
    assert img.shape == (80, 60, 3)
    # Shadowed floor pixels are markedly darker than lit floor pixels
    with_shadows = img[..., 0].astype(int)
    img_off = tracer.render_still(verts, faces, vnorms, is_floor, cam, vp,
                                  lt, shadows_on=False, bounces=1)
    diff = img_off[..., 0].astype(int) - with_shadows
    assert diff.max() > 30       # somewhere a shadow darkened the floor
    assert (diff >= -1).all()    # shadows only ever darken


def test_render_still_floor_shows_checkerboard():
    verts = np.array([
        [-30.0, 2.0, 0.5], [30.0, 2.0, 0.5],
        [30.0, 2.0, 30.0], [-30.0, 2.0, 30.0]])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    vnorms = np.array([[0.0, -1.0, 0.0]] * 4)
    is_floor = np.array([True, True])

    vp = viewport.Viewport(x=0, y=0, width=40, height=30)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    lt = light.Light()

    img = tracer.render_still(verts, faces, vnorms, is_floor, cam, vp, lt,
                              shadows_on=False, bounces=0)
    floor_rows = img[:, 25:, 0].astype(int)
    # Checkerboard: exactly two shades, strongly separated
    levels = np.unique(floor_rows)
    assert len(levels) == 2
    assert levels[1] - levels[0] > 60
