# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for planar shadow projection and the shadow map

import light
import matrix
import shadow


def test_light_basis_is_orthonormal():
    lt = light.Light()
    u, v, w = shadow.light_basis(lt)
    for vec in (u, v, w):
        assert abs(matrix.VectorMagnitude(vec) - 1.0) < 1e-9
    assert abs(matrix.DotProduct(u, v)) < 1e-9
    assert abs(matrix.DotProduct(u, w)) < 1e-9
    assert abs(matrix.DotProduct(v, w)) < 1e-9


def test_project_to_floor_lands_on_plane_along_light():
    lt = light.Light()
    p = (0.5, -1.0, 5.0)
    floor_y = 3.0
    q = shadow.project_to_floor(p, lt, floor_y)
    assert q is not None
    assert abs(q[1] - floor_y) < 1e-9
    # Displacement must be parallel to the light's travel direction
    d = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    disp = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
    cross = (disp[1] * d[2] - disp[2] * d[1],
             disp[2] * d[0] - disp[0] * d[2],
             disp[0] * d[1] - disp[1] * d[0])
    assert matrix.VectorMagnitude(cross) < 1e-9


def test_shadow_map_occludes_point_behind_triangle():
    lt = light.Light()
    tri = [(-1.0, 0.0, 4.0), (1.0, 0.0, 4.0), (0.0, 0.0, 6.0)]
    sm = shadow.build_shadow_map(tri, [(0, 1, 2)], lt)
    d = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    centroid = (0.0, 0.0, 14.0 / 3.0)
    behind = (centroid[0] + d[0], centroid[1] + d[1], centroid[2] + d[2])
    assert sm.is_shadowed(behind)


def test_shadow_map_point_beside_triangle_is_lit():
    lt = light.Light()
    tri = [(-1.0, 0.0, 4.0), (1.0, 0.0, 4.0), (0.0, 0.0, 6.0)]
    sm = shadow.build_shadow_map(tri, [(0, 1, 2)], lt)
    d = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    centroid = (0.0, 0.0, 14.0 / 3.0)
    beside = (centroid[0] + 5.0 + d[0], centroid[1] + d[1], centroid[2] + d[2])
    assert not sm.is_shadowed(beside)


def test_surface_is_not_self_shadowed():
    # Points on the occluder itself must not test shadowed (bias handles acne)
    lt = light.Light()
    tri = [(-1.0, 0.0, 4.0), (1.0, 0.0, 4.0), (0.0, 0.0, 6.0)]
    sm = shadow.build_shadow_map(tri, [(0, 1, 2)], lt)
    assert not sm.is_shadowed((0.0, 0.0, 14.0 / 3.0))
