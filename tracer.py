# Author: Dominic Williams
# Date created: August 16, 2026 (v3)
#
# Tracer: batched ray tracer over the view-space scene.
#
# Rays are the fragment pipeline's shape taken to its conclusion: flat
# arrays of origins and directions, intersected against the whole mesh with
# Moller-Trumbore, shaded in bulk with the same reflection model as the
# raster modes. Primary rays realise the true pinhole/view-plane model;
# shadow rays give exact shadows (no map, no bias); an iterative bounce
# loop adds mirror reflections.
#
# Acceleration: a two-level cluster structure. Triangles are partitioned by
# median split into small clusters with AABBs; for each cluster (a short
# Python loop) all active rays slab-test the box and only the survivors run
# Moller-Trumbore against the cluster's triangles. Rays are processed in
# chunks to bound memory.

import numpy as np

import light as light_module

CLUSTER_LEAF_SIZE = 32
RAY_CHUNK = 65536
EPS = 1e-9
OFFSET = 1e-3  # surface offset for secondary rays (scene units)


class Scene:
    """Triangles prepared for intersection, with cluster acceleration."""

    def __init__(self, vertices, faces, vertex_normals, face_is_floor):
        self.vertices = np.asarray(vertices, dtype=np.float64)
        self.faces = np.asarray(faces, dtype=np.int64)
        self.vertex_normals = np.asarray(vertex_normals, dtype=np.float64)
        self.face_is_floor = np.asarray(face_is_floor, dtype=bool)

        tri = self.vertices[self.faces]          # (M, 3, 3)
        self.v0 = tri[:, 0]
        self.edge1 = tri[:, 1] - tri[:, 0]
        self.edge2 = tri[:, 2] - tri[:, 0]

        # Cluster build: recursive median split on centroids
        centroids = tri.mean(axis=1)
        clusters = []

        def split(idx):
            if len(idx) <= CLUSTER_LEAF_SIZE:
                clusters.append(idx)
                return
            c = centroids[idx]
            axis = int(np.argmax(c.max(axis=0) - c.min(axis=0)))
            med = np.median(c[:, axis])
            left = idx[c[:, axis] <= med]
            right = idx[c[:, axis] > med]
            if len(left) == 0 or len(right) == 0:
                clusters.append(idx)
                return
            split(left)
            split(right)

        split(np.arange(len(self.faces)))
        self.clusters = clusters
        self.cluster_lo = np.array([tri[c].min(axis=(0, 1)) for c in clusters])
        self.cluster_hi = np.array([tri[c].max(axis=(0, 1)) for c in clusters])


def intersect(scene, origins, dirs, any_hit=False):
    """Batched nearest-hit (or any-hit) intersection.

    origins, dirs: (R, 3). Returns dict with 't' (inf = miss), 'face'
    (-1 = miss), 'u', 'v' (barycentric). For any_hit, 't' is any blocking
    hit's distance (early exit per cluster).
    """
    R = len(dirs)
    best_t = np.full(R, np.inf)
    best_face = np.full(R, -1, dtype=np.int64)
    best_u = np.zeros(R)
    best_v = np.zeros(R)

    for start in range(0, R, RAY_CHUNK):
        sl = slice(start, min(start + RAY_CHUNK, R))
        o = origins[sl]
        d = dirs[sl]
        n_rays = len(d)
        with np.errstate(divide='ignore'):
            inv_d = 1.0 / np.where(np.abs(d) < EPS, EPS, d)

        c_t = best_t[sl]
        c_face = best_face[sl]
        c_u = best_u[sl]
        c_v = best_v[sl]

        for ci in range(len(scene.clusters)):
            lo, hi = scene.cluster_lo[ci], scene.cluster_hi[ci]
            t0 = (lo - o) * inv_d
            t1 = (hi - o) * inv_d
            t_near = np.minimum(t0, t1).max(axis=1)
            t_far = np.maximum(t0, t1).min(axis=1)
            mask = (t_far >= t_near) & (t_far > EPS) & (t_near < c_t)
            cand = np.nonzero(mask)[0]
            if len(cand) == 0:
                continue

            fidx = scene.clusters[ci]
            e1 = scene.edge1[fidx]               # (F, 3)
            e2 = scene.edge2[fidx]
            v0 = scene.v0[fidx]
            dc = d[cand]                          # (C, 3)
            oc = o[cand]

            # Moller-Trumbore, two-sided, broadcast (C, F)
            pvec = np.cross(dc[:, None, :], e2[None, :, :])
            det = np.einsum('fk,cfk->cf', e1, pvec)
            with np.errstate(divide='ignore', invalid='ignore'):
                inv_det = np.where(np.abs(det) > EPS, 1.0 / det, 0.0)
            tvec = oc[:, None, :] - v0[None, :, :]
            u = np.einsum('cfk,cfk->cf', tvec, pvec) * inv_det
            qvec = np.cross(tvec, e1[None, :, :])
            v = np.einsum('cfk,cfk->cf', dc[:, None, :], qvec) * inv_det
            t = np.einsum('fk,cfk->cf', e2, qvec) * inv_det

            valid = ((np.abs(det) > EPS) & (u >= 0.0) & (v >= 0.0)
                     & (u + v <= 1.0) & (t > OFFSET))
            t = np.where(valid, t, np.inf)
            fi = np.argmin(t, axis=1)
            rows = np.arange(len(cand))
            tc = t[rows, fi]
            better = tc < c_t[cand]
            upd = cand[better]
            c_t[upd] = tc[better]
            c_face[upd] = fidx[fi[better]]
            c_u[upd] = u[rows, fi][better]
            c_v[upd] = v[rows, fi][better]

            if any_hit and (c_face >= 0).all():
                break

        best_t[sl] = c_t
        best_face[sl] = c_face
        best_u[sl] = c_u
        best_v[sl] = c_v

    return {'t': best_t, 'face': best_face, 'u': best_u, 'v': best_v}


def _hit_normals(scene, hit, dirs):
    """Interpolated unit normals at hit points, flipped toward the ray."""
    f = scene.faces[hit['face']]
    n0 = scene.vertex_normals[f[:, 0]]
    n1 = scene.vertex_normals[f[:, 1]]
    n2 = scene.vertex_normals[f[:, 2]]
    u = hit['u'][:, None]
    v = hit['v'][:, None]
    n = (1.0 - u - v) * n0 + u * n1 + v * n2
    lens = np.linalg.norm(n, axis=1, keepdims=True)
    lens[lens < EPS] = 1.0
    n = n / lens
    # Two-sided shading: face the incoming ray
    flip = np.einsum('ij,ij->i', n, dirs) > 0.0
    n[flip] = -n[flip]
    return n


def render_still(vertices, faces, vertex_normals, face_is_floor,
                 cam, vp, lt, shadows_on=True, bounces=2, report=None):
    """Trace the scene to a (pane_width, pane_height, 3) uint8 image.

    All geometry in view space (camera at the origin looking +z).
    """
    scene = Scene(vertices, faces, vertex_normals, face_is_floor)
    W, H = vp.width, vp.height
    ppu = cam.pixels_per_unit

    # Primary rays through the view plane (pinhole at the origin)
    px, py = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5,
                         indexing='ij')
    dirs = np.stack([(px.ravel() - W / 2.0) / ppu,
                     (py.ravel() - H / 2.0) / ppu,
                     np.ones(W * H)], axis=1)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    origins = np.zeros_like(dirs)

    R = W * H
    accum = np.zeros((R, 3))
    throughput = np.ones(R)
    active = np.arange(R)

    L = np.asarray(lt.to_light)
    silver = np.asarray(light_module.MATERIAL_BASE_COLOR, dtype=np.float64)
    checker_light = np.asarray(light_module.CHECKER_LIGHT, dtype=np.float64)
    checker_dark = np.asarray(light_module.CHECKER_DARK, dtype=np.float64)
    tile = light_module.CHECKER_TILE
    # Sky gradient for rays that miss: pale at the horizon, blue overhead
    sky_horizon = np.array([245.0, 247.0, 252.0])
    sky_top = np.array([120.0, 160.0, 220.0])
    stats = []

    def sky_color(directions):
        up = np.clip(-directions[:, 1], 0.0, 1.0)  # view-space y grows down
        return sky_horizon + up[:, None] * (sky_top - sky_horizon)

    for bounce in range(bounces + 1):
        if len(active) == 0:
            break
        hit = intersect(scene, origins, dirs)
        stats.append(f'bounce {bounce}: {len(active)} rays, '
                     f'{int((hit["face"] >= 0).sum())} hits')

        missed = hit['face'] < 0
        accum[active[missed]] += (throughput[active[missed], None]
                                  * sky_color(dirs[missed]))

        h = ~missed
        if not h.any():
            break
        hidx = active[h]
        t = hit['t'][h, None]
        p = origins[h] + dirs[h] * t
        sub_hit = {k: hit[k][h] for k in ('face', 'u', 'v')}
        n = _hit_normals(scene, sub_hit, dirs[h])

        shadowed = None
        if shadows_on:
            s_orig = p + n * OFFSET
            s_dirs = np.broadcast_to(L, s_orig.shape).copy()
            s_hit = intersect(scene, s_orig, s_dirs, any_hit=True)
            shadowed = s_hit['face'] >= 0

        # Per-hit material colour: silver model, checkerboard floor
        is_floor = scene.face_is_floor[sub_hit['face']]
        base_colors = np.broadcast_to(silver, (len(p), 3)).copy()
        if is_floor.any():
            fp = p[is_floor]
            parity = (np.floor(fp[:, 0] / tile).astype(np.int64)
                      + np.floor(fp[:, 2] / tile).astype(np.int64)) % 2
            base_colors[is_floor] = np.where(parity[:, None] == 0,
                                             checker_light, checker_dark)

        local = light_module.phong_shade_batch(
            n, p, lt, shadowed=shadowed,
            view_dirs=-dirs[h], base_colors=base_colors).astype(np.float64)

        refl = np.where(is_floor, light_module.FLOOR_REFLECTIVITY,
                        light_module.MODEL_REFLECTIVITY)
        if bounce == bounces:
            refl = np.zeros_like(refl)  # final bounce keeps all its light

        accum[hidx] += throughput[hidx, None] * (1.0 - refl[:, None]) * local
        throughput[hidx] *= refl

        # Continue only rays that still carry meaningful energy
        alive = throughput[hidx] > 0.02
        active = hidx[alive]
        d_in = dirs[h][alive]
        n_a = n[alive]
        d_dot_n = np.einsum('ij,ij->i', d_in, n_a)[:, None]
        dirs = d_in - 2.0 * d_dot_n * n_a
        origins = p[alive] + n_a * OFFSET

    if report:
        report('; '.join(stats))
    return accum.reshape(W, H, 3).clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    import light as lm

    # Tiny scene: one triangle floating above a big floor square
    verts = np.array([
        [-1.0, -1.0, 5.0], [1.0, -1.0, 5.0], [0.0, -2.0, 5.5],   # occluder
        [-8.0, 2.0, 1.0], [8.0, 2.0, 1.0],
        [8.0, 2.0, 14.0], [-8.0, 2.0, 14.0],                     # floor
    ])
    faces = np.array([[0, 1, 2], [3, 4, 5], [3, 5, 6]])
    vnorms = np.array([[0, 0, -1.0]] * 3 + [[0, -1.0, 0]] * 4)
    is_floor = np.array([False, True, True])

    scene = Scene(verts, faces, vnorms, is_floor)
    o = np.array([[0.0, 0.0, 0.0]])
    d = np.array([[0.0, -0.25, 1.0]])
    d = d / np.linalg.norm(d)
    hit = intersect(scene, o, d)
    print('ray at occluder: face', hit['face'][0], 't', round(hit['t'][0], 3))

    d2 = np.array([[0.0, 0.35, 1.0]])
    d2 = d2 / np.linalg.norm(d2)
    hit2 = intersect(scene, o, d2)
    print('ray at floor: face', hit2['face'][0])
