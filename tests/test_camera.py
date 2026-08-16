# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the camera / view plane projection

import math

import camera
import matrix
import vertex
import viewport


def make_camera():
    cam = camera.Camera(distance=6.5, fov_degrees=60.0, near=0.5)
    cam.attach_viewport(viewport.DEFAULT_VIEWPORT)
    return cam


def project(cam, x_view, y_view, z_view):
    v = vertex.vertex()
    v.x_view, v.y_view, v.z_view = x_view, y_view, z_view
    v.calc_screen_coordinates(cam.projection_matrix(), cam, viewport.DEFAULT_VIEWPORT)
    return v


def test_MatrixVectorH_w_component():
    # PerspectiveMatrix(d) must produce w = z / d
    P = matrix.PerspectiveMatrix(2.0)
    x, y, z, w = matrix.MatrixVectorH(P, [3.0, 4.0, 5.0])
    assert w == 5.0 / 2.0
    # Affine matrices have w = 1
    T = matrix.TranslateMatrix(1.0, 2.0, 3.0)
    assert matrix.MatrixVectorH(T, [3.0, 4.0, 5.0])[3] == 1.0


def test_axis_point_projects_to_pane_center():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    v = project(cam, 0.0, 0.0, 5.0)
    assert not v.clipped
    assert abs(v.x_screen - vp.center_x) < 1e-9
    assert abs(v.y_screen - vp.center_y) < 1e-9


def test_frustum_edge_projects_to_pane_edge():
    # A point whose slope y/z equals tan(fov/2) lands exactly on the pane's
    # vertical edge, at any depth
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    edge_slope = math.tan(math.radians(cam.fov_degrees) / 2.0)
    for z in (2.0, 6.5, 20.0):
        v = project(cam, 0.0, z * edge_slope, z)
        assert abs(v.y_screen - vp.y_max) < 1e-6


def test_perspective_divide_halves_offset_at_double_depth():
    cam = make_camera()
    vp = viewport.DEFAULT_VIEWPORT
    near_pt = project(cam, 1.0, 0.0, 4.0)
    far_pt = project(cam, 1.0, 0.0, 8.0)
    near_offset = near_pt.x_screen - vp.center_x
    far_offset = far_pt.x_screen - vp.center_x
    assert abs(near_offset - 2.0 * far_offset) < 1e-9


def test_point_behind_near_plane_is_clipped():
    cam = make_camera()
    for z in (0.0, cam.near, -3.0):
        v = project(cam, 1.0, 1.0, z)
        assert v.clipped
    assert not project(cam, 1.0, 1.0, cam.near + 0.01).clipped


def test_dolly_clamps_at_min_distance():
    cam = camera.Camera(distance=6.5, min_distance=1.0)
    cam.dolly(0.001)
    assert cam.distance == 1.0
    cam.dolly(2.0)
    assert cam.distance == 2.0
    cam.reset()
    assert cam.distance == 6.5
