# Author: Dominic Williams
# Date created: August 16, 2026
#
# Shadow: planar projected shadows and an orthographic shadow map for the
# directional light.
#
# Everything works in view space (camera at the origin), matching light.py.
# The light travels along d = -to_light, which points downward toward the
# floor plane (a plane of constant y; view-space y grows downward).

import matrix

SHADOW_MAP_SIZE = 256
BIAS_FRACTION = 0.04  # of the scene's depth range along the light (acne guard)


def project_to_floor(p_view, lt, floor_y):
    """Project a view-space point along the light direction onto the plane
    y = floor_y. Returns the view-space landing point, or None if the light
    never reaches the plane from this point."""
    dx, dy, dz = -lt.to_light[0], -lt.to_light[1], -lt.to_light[2]
    if dy <= 1e-9:
        return None
    t = (floor_y - p_view[1]) / dy
    if t < 0.0:
        return None
    return (p_view[0] + t * dx, floor_y, p_view[2] + t * dz)


def light_basis(lt):
    """Orthonormal basis for light space: w along the light's travel
    direction, u/v spanning the plane perpendicular to it."""
    w = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    # u = normalize(cross(w, z-axis)); fall back if w is near the z-axis
    ux, uy, uz = w[1], -w[0], 0.0
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
    """Orthographic depth map of the model as seen from the light."""

    def __init__(self, u, v, w, u_min, v_min, scale_u, scale_v, bias, depth, size):
        self.u = u
        self.v = v
        self.w = w
        self.u_min = u_min
        self.v_min = v_min
        self.scale_u = scale_u
        self.scale_v = scale_v
        self.bias = bias
        self.depth = depth
        self.size = size

    def is_shadowed(self, p_view):
        """True if the view-space point is occluded from the light."""
        px, py, pz = p_view
        u, v, w = self.u, self.v, self.w
        lu = px * u[0] + py * u[1] + pz * u[2]
        lv = px * v[0] + py * v[1] + pz * v[2]
        lw = px * w[0] + py * w[1] + pz * w[2]
        ix = int((lu - self.u_min) * self.scale_u)
        iy = int((lv - self.v_min) * self.scale_v)
        last = self.size - 1
        if ix < 0:
            ix = 0
        elif ix > last:
            ix = last
        if iy < 0:
            iy = 0
        elif iy > last:
            iy = last
        return lw > self.depth[iy][ix] + self.bias


def build_shadow_map(view_points, faces, lt, size=SHADOW_MAP_SIZE):
    """Rasterise the model into a depth map as seen from the light.

    view_points: list of (x, y, z) view-space vertex positions
    faces: iterable of (i1, i2, i3) 0-based vertex index triples
    """
    import raster

    u, v, w = light_basis(lt)

    # Transform every vertex into light coordinates
    light_pts = []
    for (px, py, pz) in view_points:
        light_pts.append((px * u[0] + py * u[1] + pz * u[2],
                          px * v[0] + py * v[1] + pz * v[2],
                          px * w[0] + py * w[1] + pz * w[2]))

    u_lo = min(p[0] for p in light_pts)
    u_hi = max(p[0] for p in light_pts)
    v_lo = min(p[1] for p in light_pts)
    v_hi = max(p[1] for p in light_pts)
    w_lo = min(p[2] for p in light_pts)
    w_hi = max(p[2] for p in light_pts)

    # Small margin so boundary samples index inside the map
    margin_u = (u_hi - u_lo) * 0.01 + 1e-9
    margin_v = (v_hi - v_lo) * 0.01 + 1e-9
    u_min = u_lo - margin_u
    v_min = v_lo - margin_v
    scale_u = (size - 1) / (u_hi - u_lo + 2 * margin_u)
    scale_v = (size - 1) / (v_hi - v_lo + 2 * margin_v)
    bias = (w_hi - w_lo) * BIAS_FRACTION + 1e-9

    inf = float('inf')
    depth = [[inf] * size for _ in range(size)]

    for (i1, i2, i3) in faces:
        pts = []
        ds = []
        for i in (i1, i2, i3):
            lu, lv, lw = light_pts[i]
            pts.append(((lu - u_min) * scale_u, (lv - v_min) * scale_v))
            ds.append(lw)
        raster.fill_depth(depth, pts, ds, size)

    return ShadowMap(u, v, w, u_min, v_min, scale_u, scale_v, bias, depth, size)


if __name__ == '__main__':
    import light as light_module

    lt = light_module.Light()
    u, v, w = light_basis(lt)
    print('basis u:', u)
    print('basis v:', v)
    print('basis w:', w)
    print('u.v =', matrix.DotProduct(u, v))
    print('u.w =', matrix.DotProduct(u, w))
    print('|v| =', matrix.VectorMagnitude(v))

    # A single triangle above a test point: the point below it (along the
    # light) is shadowed, a point off to the side is lit
    tri = [(-1.0, 0.0, 4.0), (1.0, 0.0, 4.0), (0.0, 0.0, 6.0)]
    sm = build_shadow_map(tri, [(0, 1, 2)], lt)
    dx, dy, dz = -lt.to_light[0], -lt.to_light[1], -lt.to_light[2]
    centroid = (0.0, 0.0, 14.0 / 3.0)
    behind = (centroid[0] + dx, centroid[1] + dy, centroid[2] + dz)
    print('behind triangle shadowed:', sm.is_shadowed(behind))
    beside = (centroid[0] + 5.0 + dx, centroid[1] + dy, centroid[2] + dz)
    print('beside triangle shadowed:', sm.is_shadowed(beside))
    print('floor projection:', project_to_floor((0.0, 0.0, 5.0), lt, 3.0))
