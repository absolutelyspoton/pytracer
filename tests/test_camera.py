# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the camera / view plane projection (v3 batch API)

import math

import numpy as np

import camera
import matrix
import viewport


def make_camera():
    cam = camera.Camera(distance=6.5, fov_degrees=60.0, near=0.5)
    cam.attach_viewport(viewport.DEFAULT_VIEWPORT)
    return cam


def project_one(cam, x, y, z):
    screen, clipped = cam.project(np.array([[x, y, z]]),
                                  viewport.DEFAULT_VIEWPORT)
    return screen[0], bool(clipped[0])


def test_MatrixVectorH_w_component():
    P = matrix.PerspectiveMatrix(2.0)
    x, y, z, w = matrix.MatrixVectorH(P, [3.0, 4.0, 5.0])
    assert w == 5.0 / 2.0
    T = matrix.TranslateMatrix(1.0, 2.0, 3.0)
    assert matrix.MatrixVectorH(T, [3.0, 4.0, 5.0])[3] == 1.0


def test_axis_point_projects_to_pane_center():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    (sx, sy), clipped = project_one(cam, 0.0, 0.0, 5.0)
    assert not clipped
    assert abs(sx - vp.center_x) < 1e-9
    assert abs(sy - vp.center_y) < 1e-9


def test_frustum_edge_projects_to_pane_edge():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    edge_slope = math.tan(math.radians(cam.fov_degrees) / 2.0)
    for z in (2.0, 6.5, 20.0):
        (sx, sy), clipped = project_one(cam, 0.0, z * edge_slope, z)
        assert abs(sy - vp.y_max) < 1e-6


def test_perspective_divide_halves_offset_at_double_depth():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    (nx, _), _ = project_one(cam, 1.0, 0.0, 4.0)
    (fx, _), _ = project_one(cam, 1.0, 0.0, 8.0)
    assert abs((nx - vp.center_x) - 2.0 * (fx - vp.center_x)) < 1e-9


def test_point_behind_near_plane_is_clipped():
    cam = make_camera()
    for z in (0.0, cam.near, -3.0):
        _, clipped = project_one(cam, 1.0, 1.0, z)
        assert clipped
    _, clipped = project_one(cam, 1.0, 1.0, cam.near + 0.01)
    assert not clipped


def test_batch_projection_matches_scalar():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    pts = np.array([[0.5, -0.25, 4.0], [1.0, 2.0, 9.0], [0.0, 0.0, 6.5]])
    screen, clipped = cam.project(pts, vp)
    for i, (x, y, z) in enumerate(pts):
        assert abs(screen[i, 0] - (vp.center_x + x / z * cam.pixels_per_unit)) < 1e-9
        assert abs(screen[i, 1] - (vp.center_y + y / z * cam.pixels_per_unit)) < 1e-9
        assert not clipped[i]


def test_dolly_clamps_at_min_distance():
    cam = camera.Camera(distance=6.5, min_distance=1.0)
    cam.dolly(0.001)
    assert cam.distance == 1.0
    cam.dolly(2.0)
    assert cam.distance == 2.0
    cam.reset()
    assert cam.distance == 6.5
