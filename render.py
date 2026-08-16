# Author: Dominic Williams
# Date created: August 16, 2026 (v3)
#
# Render: batched fragment rasteriser with a z-buffer.
#
# The v2 renderer looped triangles in Python and wrote pixels one at a time;
# per-triangle numpy is slower still for teapot-sized triangles (measured
# 0.9x). The array-oriented shape that wins is fragment batching: ONE set of
# flat arrays holds every candidate pixel of every triangle, barycentric
# weights and depths are computed for all of them in a handful of numpy
# operations, and a z-buffer resolve keeps the nearest fragment per pixel.
# Painter's sorting is gone; occlusion is exact per pixel. The same batch
# machinery pointed down the light's axis builds the shadow map.

import numpy as np


def _empty_frags():
    return {k: np.empty(0, dtype=(np.int64 if k in ('x', 'y', 'face') else np.float64))
            for k in ('x', 'y', 'face', 'w0', 'w1', 'w2', 'depth')}


def _fragments(screen_pts, z_view, faces, width, height):
    """Generate all inside-triangle fragments (pre z-resolve): the flat
    candidate stream shared by the frame rasteriser and the depth map."""
    empty = _empty_frags()
    if len(faces) == 0:
        return empty

    tri = screen_pts[faces]  # (M, 3, 2)
    x0, y0 = tri[:, 0, 0], tri[:, 0, 1]
    x1, y1 = tri[:, 1, 0], tri[:, 1, 1]
    x2, y2 = tri[:, 2, 0], tri[:, 2, 1]

    # Barycentric denominators; degenerate (zero-area) triangles drop out
    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    ok = np.abs(denom) > 1e-12

    # Per-face integer bounding boxes clamped to the buffer
    xmin = np.clip(np.floor(tri[:, :, 0].min(axis=1)), 0, width - 1).astype(np.int64)
    xmax = np.clip(np.ceil(tri[:, :, 0].max(axis=1)), 0, width - 1).astype(np.int64)
    ymin = np.clip(np.floor(tri[:, :, 1].min(axis=1)), 0, height - 1).astype(np.int64)
    ymax = np.clip(np.ceil(tri[:, :, 1].max(axis=1)), 0, height - 1).astype(np.int64)
    bw = xmax - xmin + 1
    bh = ymax - ymin + 1

    # Faces whose bbox is fully outside collapse to degenerate spans when
    # clamped; drop those and degenerates
    ok &= (tri[:, :, 0].max(axis=1) >= 0) & (tri[:, :, 0].min(axis=1) <= width - 1)
    ok &= (tri[:, :, 1].max(axis=1) >= 0) & (tri[:, :, 1].min(axis=1) <= height - 1)
    keep = np.nonzero(ok)[0]
    if len(keep) == 0:
        return empty

    bw, bh = bw[keep], bh[keep]
    xmin, ymin = xmin[keep], ymin[keep]
    counts = bw * bh

    # One flat fragment array for every candidate pixel of every face
    offsets = np.concatenate(([0], np.cumsum(counts)[:-1]))
    total = int(counts.sum())
    frag_k = np.repeat(np.arange(len(keep)), counts)       # index into keep
    local = np.arange(total) - offsets[frag_k]
    fx = xmin[frag_k] + local % bw[frag_k]
    fy = ymin[frag_k] + local // bw[frag_k]

    # Barycentric weights for ALL fragments at once (sample pixel centres)
    f = keep[frag_k]                                       # original face row
    px = fx.astype(np.float64) + 0.5
    py = fy.astype(np.float64) + 0.5
    d = denom[f]
    w0 = ((y1[f] - y2[f]) * (px - x2[f]) + (x2[f] - x1[f]) * (py - y2[f])) / d
    w1 = ((y2[f] - y0[f]) * (px - x2[f]) + (x0[f] - x2[f]) * (py - y2[f])) / d
    w2 = 1.0 - w0 - w1

    inside = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
    if not inside.any():
        return empty
    f = f[inside]
    fx, fy = fx[inside], fy[inside]
    w0, w1, w2 = w0[inside], w1[inside], w2[inside]

    zf = z_view[faces[f]]
    depth = w0 * zf[:, 0] + w1 * zf[:, 1] + w2 * zf[:, 2]
    return {'x': fx, 'y': fy, 'face': f,
            'w0': w0, 'w1': w1, 'w2': w2, 'depth': depth}


def rasterize(screen_pts, z_view, faces, width, height):
    """Rasterise triangles into surviving (visible) fragments.

    screen_pts: (N, 2) float, buffer pixel coordinates per vertex
    z_view:     (N,) float, view-space depth per vertex (smaller = nearer)
    faces:      (M, 3) int, vertex indices (pre-filtered: caller drops
                clipped / back-facing faces)
    width, height: buffer dimensions

    Returns a dict of per-winning-fragment arrays (one entry per pixel that
    ends up covered): 'x', 'y' (int), 'face' (index into `faces`),
    'w0'/'w1'/'w2' (barycentric weights), 'depth'. Empty arrays if nothing
    is visible.
    """
    frags = _fragments(screen_pts, z_view, faces, width, height)
    if len(frags['x']) == 0:
        return frags

    # Z-buffer resolve: sort fragments by (pixel, depth), keep the first
    # (nearest) per pixel
    pix = frags['y'] * width + frags['x']
    order = np.lexsort((frags['depth'], pix))
    pix_sorted = pix[order]
    first = np.empty(len(order), dtype=bool)
    first[0] = True
    first[1:] = pix_sorted[1:] != pix_sorted[:-1]
    win = order[first]
    return {k: v[win] for k, v in frags.items()}


def interpolate(frags, faces, vertex_attrs):
    """Barycentric-interpolate per-vertex attributes at winning fragments.

    vertex_attrs: (N, C) array; returns (F, C).
    """
    corner = vertex_attrs[faces[frags['face']]]            # (F, 3, C)
    return (frags['w0'][:, None] * corner[:, 0]
            + frags['w1'][:, None] * corner[:, 1]
            + frags['w2'][:, None] * corner[:, 2])


def build_depth_map(uv_pts, depths, faces, size):
    """Minimum-depth map (the shadow map): same fragment machinery, but the
    resolve is a direct scatter-min over the raw fragment stream (no winner
    sort needed). Returns (size, size) float64 indexed [iy][ix] to match
    shadow.ShadowMap."""
    frags = _fragments(uv_pts, depths, faces, size, size)
    depth_map = np.full(size * size, np.inf)
    if len(frags['x']):
        np.minimum.at(depth_map, frags['y'] * size + frags['x'],
                      frags['depth'])
    return depth_map.reshape(size, size)


if __name__ == '__main__':
    # Two overlapping triangles: the nearer one must win the shared pixels
    pts = np.array([[2.0, 2.0], [18.0, 2.0], [10.0, 18.0],     # far triangle
                    [6.0, 4.0], [16.0, 6.0], [8.0, 16.0]])     # near triangle
    z = np.array([10.0, 10.0, 10.0, 5.0, 5.0, 5.0])
    faces = np.array([[0, 1, 2], [3, 4, 5]])
    frags = rasterize(pts, z, faces, 20, 20)
    print(f'{len(frags["x"])} visible fragments')
    grid = np.full((20, 20), '.', dtype='<U1')
    grid[frags['y'], frags['x']] = np.where(frags['face'] == 1, 'N', 'f')
    print('\n'.join(''.join(row) for row in grid))
    print('near triangle owns the overlap (N inside f):',
          (frags['face'] == 1).sum(), 'near pixels')
