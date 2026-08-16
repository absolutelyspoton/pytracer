# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the batched fragment rasteriser (v3)

import numpy as np

import render


def two_triangle_scene():
    """A far triangle with a nearer one overlapping its middle."""
    pts = np.array([[2.0, 2.0], [18.0, 2.0], [10.0, 18.0],
                    [6.0, 4.0], [16.0, 6.0], [8.0, 16.0]])
    z = np.array([10.0, 10.0, 10.0, 5.0, 5.0, 5.0])
    faces = np.array([[0, 1, 2], [3, 4, 5]])
    return pts, z, faces


def test_zbuffer_near_triangle_wins_overlap():
    pts, z, faces = two_triangle_scene()
    frags = render.rasterize(pts, z, faces, 20, 20)
    assert len(frags['x']) > 0
    # Every winning fragment is unique per pixel
    pix = frags['y'] * 20 + frags['x']
    assert len(np.unique(pix)) == len(pix)
    # The near triangle's centroid pixel must be owned by the near triangle
    cx, cy = 10, 8
    at = (frags['x'] == cx) & (frags['y'] == cy)
    assert at.sum() == 1
    assert frags['face'][at][0] == 1
    assert abs(frags['depth'][at][0] - 5.0) < 1e-9


def test_barycentric_interpolation_at_corner_and_center():
    pts = np.array([[0.0, 0.0], [40.0, 0.0], [0.0, 40.0]])
    z = np.zeros(3)
    faces = np.array([[0, 1, 2]])
    frags = render.rasterize(pts, z, faces, 40, 40)
    colors = np.array([[255.0, 0.0, 0.0], [0.0, 255.0, 0.0], [0.0, 0.0, 255.0]])
    out = render.interpolate(frags, faces, colors)
    # Pixel adjacent to the red corner is dominated by red
    near_red = (frags['x'] == 1) & (frags['y'] == 1)
    assert near_red.sum() == 1
    assert out[near_red][0][0] > 200
    # An interior pixel mixes all three
    interior = (frags['x'] == 10) & (frags['y'] == 10)
    assert interior.sum() == 1
    r, g, b = out[interior][0]
    assert r > 30 and g > 30 and b > 30


def test_fragments_stay_inside_buffer_bounds():
    # Triangle much larger than the buffer: fragments must be clamped
    pts = np.array([[-50.0, -50.0], [90.0, -20.0], [10.0, 90.0]])
    z = np.zeros(3)
    faces = np.array([[0, 1, 2]])
    frags = render.rasterize(pts, z, faces, 30, 30)
    assert len(frags['x']) > 0
    assert frags['x'].min() >= 0 and frags['x'].max() <= 29
    assert frags['y'].min() >= 0 and frags['y'].max() <= 29


def test_degenerate_and_offscreen_triangles_are_dropped():
    pts = np.array([[5.0, 5.0], [5.0, 5.0], [5.0, 5.0],       # zero area
                    [100.0, 100.0], [120.0, 100.0], [110.0, 120.0]])  # off
    z = np.zeros(6)
    faces = np.array([[0, 1, 2], [3, 4, 5]])
    frags = render.rasterize(pts, z, faces, 30, 30)
    assert len(frags['x']) == 0


def test_depth_map_records_minimum():
    uv = np.array([[2.0, 2.0], [18.0, 2.0], [10.0, 18.0],
                   [6.0, 4.0], [16.0, 6.0], [8.0, 16.0]])
    depths = np.array([10.0, 10.0, 10.0, 5.0, 5.0, 5.0])
    faces = np.array([[0, 1, 2], [3, 4, 5]])
    dm = render.build_depth_map(uv, depths, faces, 20)
    assert abs(dm[8, 10] - 5.0) < 1e-9      # overlap: near depth wins
    assert abs(dm[3, 5] - 10.0) < 1e-9      # far-only region
    assert np.isinf(dm[0, 0])               # uncovered region
