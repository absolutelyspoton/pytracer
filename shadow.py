# Author: Dominic Williams
# Date created: August 16, 2026
# v3: batched on numpy - the map is built with the same fragment rasteriser
# as the frame, and shadow tests run for whole point arrays at once, which
# makes per-frame self-shadowing affordable.
#
# Shadow: orthographic shadow map for the directional light. Everything
# works in view space (camera at the origin), matching light.py. The light
# travels along d = -to_light.

import numpy as np

import matrix
import render

SHADOW_MAP_SIZE = 256
BIAS_FRACTION = 0.04  # of the scene's depth range along the light (acne guard)


def light_basis(lt):
    """Orthonormal basis for light space: w along the light's travel
    direction, u/v spanning the plane perpendicular to it."""
    w = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    ux, uy = w[1], -w[0]
    mag = (ux * ux + uy * uy) ** 0.5
    if mag < 1e-6:
        u = (1.0, 0.0, 0.0)
    else:
        u = (ux / mag, uy / mag, 0.0)
    v = (w[1] * u[2] - w[2] * u[1],
         w[2] * u[0] - w[0] * u[2],
         w[0] * u[1] - w[1] * u[0])
    return u, v, w


class ShadowMap:
    """Orthographic depth map of the scene as seen from the light."""

    def __init__(self, basis, u_min, v_min, scale_u, scale_v, bias, depth, size):
        self.basis = basis          # (3, 3): rows u, v, w
        self.u_min = u_min
        self.v_min = v_min
        self.scale_u = scale_u
        self.scale_v = scale_v
        self.bias = bias
        self.depth = depth          # (size, size) float, indexed [iy][ix]
        self.size = size

    def is_shadowed_batch(self, points):
        """(N, 3) view-space points -> (N,) bool occlusion mask."""
        p = np.asarray(points, dtype=np.float64).reshape(-1, 3)
        lp = p @ self.basis.T       # columns: u, v, w
        ix = np.clip(((lp[:, 0] - self.u_min) * self.scale_u).astype(np.int64),
                     0, self.size - 1)
        iy = np.clip(((lp[:, 1] - self.v_min) * self.scale_v).astype(np.int64),
                     0, self.size - 1)
        return lp[:, 2] > self.depth[iy, ix] + self.bias

    def is_shadowed(self, p_view):
        """Single-point convenience wrapper."""
        return bool(self.is_shadowed_batch([p_view])[0])


def build_shadow_map(view_points, faces, lt, size=SHADOW_MAP_SIZE):
    """Rasterise the scene into a depth map as seen from the light.

    view_points: (N, 3) view-space vertex positions (array or list)
    faces: (M, 3) 0-based vertex index triples (array or list)
    """
    pts = np.asarray(view_points, dtype=np.float64).reshape(-1, 3)
    face_arr = np.asarray(faces, dtype=np.int64).reshape(-1, 3)

    u, v, w = light_basis(lt)
    basis = np.array([u, v, w])
    lp = pts @ basis.T              # (N, 3): u, v, w coordinates

    u_lo, v_lo, w_lo = lp.min(axis=0)
    u_hi, v_hi, w_hi = lp.max(axis=0)

    margin_u = (u_hi - u_lo) * 0.01 + 1e-9
    margin_v = (v_hi - v_lo) * 0.01 + 1e-9
    u_min = u_lo - margin_u
    v_min = v_lo - margin_v
    scale_u = (size - 1) / (u_hi - u_lo + 2 * margin_u)
    scale_v = (size - 1) / (v_hi - v_lo + 2 * margin_v)
    bias = (w_hi - w_lo) * BIAS_FRACTION + 1e-9

    uv = np.empty((len(lp), 2))
    uv[:, 0] = (lp[:, 0] - u_min) * scale_u
    uv[:, 1] = (lp[:, 1] - v_min) * scale_v
    depth = render.build_depth_map(uv, lp[:, 2], face_arr, size)

    return ShadowMap(basis, u_min, v_min, scale_u, scale_v, bias, depth, size)


def project_to_floor(p_view, lt, floor_y):
    """Project a view-space point along the light direction onto the plane
    y = floor_y. Kept for tests/reference; v3 renders the floor as scene
    geometry and shadows it with the map instead."""
    dx, dy, dz = -lt.to_light[0], -lt.to_light[1], -lt.to_light[2]
    if dy <= 1e-9:
        return None
    t = (floor_y - p_view[1]) / dy
    if t < 0.0:
        return None
    return (p_view[0] + t * dx, floor_y, p_view[2] + t * dz)


if __name__ == '__main__':
    import light as light_module

    lt = light_module.Light()
    u, v, w = light_basis(lt)
    print('u.v =', matrix.DotProduct(u, v))
    print('|w| =', matrix.VectorMagnitude(w))

    tri = [(-1.0, 0.0, 4.0), (1.0, 0.0, 4.0), (0.0, 0.0, 6.0)]
    sm = build_shadow_map(tri, [(0, 1, 2)], lt)
    d = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    centroid = (0.0, 0.0, 14.0 / 3.0)
    behind = (centroid[0] + d[0], centroid[1] + d[1], centroid[2] + d[2])
    print('behind triangle shadowed:', sm.is_shadowed(behind))
    beside = (centroid[0] + 5.0 + d[0], centroid[1] + d[1], centroid[2] + d[2])
    print('beside triangle shadowed:', sm.is_shadowed(beside))
    print('floor projection:', project_to_floor((0.0, 0.0, 5.0), lt, 3.0))
