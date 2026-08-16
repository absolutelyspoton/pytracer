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

# Face materials
MAT_SILVER = 0
MAT_FLOOR = 1
MAT_GLASS = 2

MAX_DEPTH = 6      # ray-tree depth (glass needs enter+exit+internal bounces)
MIN_THROUGHPUT = 0.02


class Scene:
    """Triangles prepared for intersection, with cluster acceleration."""

    def __init__(self, vertices, faces, vertex_normals, face_material):
        self.vertices = np.asarray(vertices, dtype=np.float64)
        self.faces = np.asarray(faces, dtype=np.int64)
        self.vertex_normals = np.asarray(vertex_normals, dtype=np.float64)
        fm = np.asarray(face_material)
        if fm.dtype == bool:  # legacy: True = floor, False = silver model
            fm = np.where(fm, MAT_FLOOR, MAT_SILVER)
        self.face_material = fm.astype(np.int64)

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


def intersect(scene, origins, dirs, any_hit=False, progress=None):
    """Batched nearest-hit (or any-hit) intersection.

    origins, dirs: (R, 3). Returns dict with 't' (inf = miss), 'face'
    (-1 = miss), 'u', 'v' (barycentric). For any_hit, 't' is any blocking
    hit's distance (early exit per cluster). `progress`, if given, is
    called with the fraction of rays processed after each chunk.
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
        if progress is not None:
            progress(min(1.0, sl.stop / R))

    return {'t': best_t, 'face': best_face, 'u': best_u, 'v': best_v}


def _hit_normals(scene, hit, dirs):
    """Interpolated unit normals at hit points, flipped toward the ray.

    Also returns `entering`: True where the ray meets the surface from the
    outside (the unflipped outward normal opposes the ray) - refraction
    needs the crossing direction to pick n1/n2.
    """
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
    entering = ~flip
    n[flip] = -n[flip]
    return n, entering


def _floor_colors(points, floor_pattern):
    """Procedural floor colours for view-space points on the floor plane."""
    checker_light = np.asarray(light_module.CHECKER_LIGHT, dtype=np.float64)
    checker_dark = np.asarray(light_module.CHECKER_DARK, dtype=np.float64)
    tile = light_module.CHECKER_TILE
    if floor_pattern == 'plain':
        return np.broadcast_to(checker_light, (len(points), 3)).copy()
    if floor_pattern == 'stripes':
        k = np.floor((points[:, 0] + points[:, 2]) / tile)
    elif floor_pattern == 'rings':
        k = np.floor(np.sqrt(points[:, 0] ** 2 + points[:, 2] ** 2) / tile)
    else:  # checker
        k = np.floor(points[:, 0] / tile) + np.floor(points[:, 2] / tile)
    parity = k.astype(np.int64) % 2
    return np.where(parity[:, None] == 0, checker_light, checker_dark)


def trace_rays(ctx, origins, dirs, lt, shadows_on=True, bounces=2,
               floor_pattern='checker', progress=None, stats=None):
    """Trace a batch of rays to completion. Returns (R, 3) float colours.

    Ray-stream model: the working set is flat arrays of (origin, dir,
    pixel index, RGB throughput). Opaque hits add their shaded colour and
    continue as one mirror ray; GLASS hits branch into a Fresnel-weighted
    reflected ray AND a Snell-refracted transmitted ray (total internal
    reflection sends everything to the reflection). Branches from the same
    pixel coexist in the stream, so accumulation uses np.add.at.

    `bounces` caps opaque mirror bounces (matching the silver-only
    behaviour); glass branches continue to MAX_DEPTH. `progress` maps 0..1
    over this batch's work.
    """
    scene = ctx['scene']
    R = len(dirs)
    accum = np.zeros((R, 3))
    pixel = np.arange(R)
    T = np.ones((R, 3))

    L = np.asarray(lt.to_light)
    silver = np.asarray(light_module.MATERIAL_BASE_COLOR, dtype=np.float64)
    glass_tint = np.asarray(light_module.GLASS_TINT, dtype=np.float64)
    ior = light_module.GLASS_IOR
    r0 = ((1.0 - ior) / (1.0 + ior)) ** 2  # Schlick base reflectance
    # Sky gradient for rays that miss: pale at the horizon, blue overhead
    sky_horizon = np.array([245.0, 247.0, 252.0])
    sky_top = np.array([120.0, 160.0, 220.0])

    def sky_color(directions):
        up = np.clip(-directions[:, 1], 0.0, 1.0)  # view-space y grows down
        return sky_horizon + up[:, None] * (sky_top - sky_horizon)

    # Progress windows per depth (later depths trace far fewer rays)
    stage_w = np.array([1.0, 0.5, 0.25, 0.12, 0.06, 0.03,
                        0.015][:MAX_DEPTH + 1])
    stage_edges = np.concatenate([[0.0], np.cumsum(stage_w) / stage_w.sum()])

    def stage_progress(depth, lo_frac, hi_frac):
        if progress is None:
            return None
        s0, s1 = stage_edges[depth], stage_edges[depth + 1]
        lo = s0 + (s1 - s0) * lo_frac
        hi = s0 + (s1 - s0) * hi_frac
        return lambda f: progress(lo + f * (hi - lo))

    for depth in range(MAX_DEPTH + 1):
        if len(dirs) == 0:
            break
        hit = intersect(scene, origins, dirs,
                        progress=stage_progress(depth, 0.0, 0.6))
        if stats is not None and depth < len(stats):
            stats[depth]['rays'] += len(dirs)
            stats[depth]['hits'] += int((hit['face'] >= 0).sum())

        missed = hit['face'] < 0
        if missed.any():
            np.add.at(accum, pixel[missed], T[missed] * sky_color(dirs[missed]))

        h = np.nonzero(~missed)[0]
        if len(h) == 0:
            break
        pix_h = pixel[h]
        T_h = T[h]
        d_h = dirs[h]
        p = origins[h] + d_h * hit['t'][h, None]
        sub_hit = {k: hit[k][h] for k in ('face', 'u', 'v')}
        n, entering = _hit_normals(scene, sub_hit, d_h)
        mat = scene.face_material[sub_hit['face']]

        # Light factor: 0 behind opaque geometry, partial behind glass
        lf = None
        if shadows_on:
            s_orig = p + n * OFFSET
            s_dirs = np.broadcast_to(L, s_orig.shape).copy()
            o_hit = intersect(ctx['opaque_scene'], s_orig, s_dirs,
                              any_hit=True,
                              progress=stage_progress(depth, 0.6, 0.85))
            lf = np.where(o_hit['face'] >= 0, 0.0, 1.0)
            if ctx['glass_scene'] is not None:
                g_hit = intersect(ctx['glass_scene'], s_orig, s_dirs,
                                  any_hit=True,
                                  progress=stage_progress(depth, 0.85, 1.0))
                lf = np.where((g_hit['face'] >= 0) & (lf > 0.0),
                              light_module.GLASS_SHADOW_TRANSMISSION, lf)

        next_o = []
        next_d = []
        next_p = []
        next_T = []

        # --- Opaque hits: shade + one mirror continuation ----------------
        om = np.nonzero(mat != MAT_GLASS)[0]
        if len(om):
            is_floor = mat[om] == MAT_FLOOR
            base_colors = np.broadcast_to(silver, (len(om), 3)).copy()
            if is_floor.any():
                base_colors[is_floor] = _floor_colors(p[om][is_floor],
                                                      floor_pattern)
            local = light_module.phong_shade_batch(
                n[om], p[om], lt, view_dirs=-d_h[om],
                base_colors=base_colors,
                light_factor=None if lf is None else lf[om]
            ).astype(np.float64)

            refl = np.where(is_floor, light_module.FLOOR_REFLECTIVITY,
                            light_module.MODEL_REFLECTIVITY)
            if depth >= bounces:
                refl = np.zeros_like(refl)  # cap keeps all remaining light

            np.add.at(accum, pix_h[om],
                      T_h[om] * (1.0 - refl[:, None]) * local)

            T_refl = T_h[om] * refl[:, None]
            alive = T_refl.max(axis=1) > MIN_THROUGHPUT
            if alive.any():
                oa = om[alive]
                d_in = d_h[oa]
                n_a = n[oa]
                ddn = np.einsum('ij,ij->i', d_in, n_a)[:, None]
                next_o.append(p[oa] + n_a * OFFSET)
                next_d.append(d_in - 2.0 * ddn * n_a)
                next_p.append(pix_h[oa])
                next_T.append(T_refl[alive])

        # --- Glass hits: Fresnel reflection + Snell refraction -----------
        gm = np.nonzero(mat == MAT_GLASS)[0]
        if len(gm) and depth < MAX_DEPTH:
            d_g = d_h[gm]
            n_g = n[gm]                     # faces the incident side
            p_g = p[gm]
            cos_i = -np.einsum('ij,ij->i', d_g, n_g)
            eta = np.where(entering[gm], 1.0 / ior, ior)
            sin2_t = eta ** 2 * (1.0 - cos_i ** 2)
            tir = sin2_t > 1.0
            cos_t = np.sqrt(np.clip(1.0 - sin2_t, 0.0, None))

            # Schlick with the angle on the optically thinner side
            cos_x = np.where(entering[gm], cos_i, cos_t)
            fres = r0 + (1.0 - r0) * (1.0 - cos_x) ** 5
            fres = np.where(tir, 1.0, fres)

            # Specular highlight only (light passes through glass)
            local = light_module.phong_shade_batch(
                n_g, p_g, lt, view_dirs=-d_g,
                base_colors=np.zeros((len(gm), 3)),
                light_factor=None if lf is None else lf[gm],
                diffuse_scale=0.0).astype(np.float64)
            np.add.at(accum, pix_h[gm], T_h[gm] * local)

            # Reflected branch (Fresnel share)
            T_refl = T_h[gm] * fres[:, None]
            alive = T_refl.max(axis=1) > MIN_THROUGHPUT
            if alive.any():
                ga = gm[alive]
                d_in = d_h[ga]
                n_a = n[ga]
                ddn = np.einsum('ij,ij->i', d_in, n_a)[:, None]
                next_o.append(p[ga] + n_a * OFFSET)
                next_d.append(d_in - 2.0 * ddn * n_a)
                next_p.append(pix_h[ga])
                next_T.append(T_refl[alive])

            # Refracted branch (transmitted share, tinted per interface)
            T_refr = T_h[gm] * (1.0 - fres)[:, None] * glass_tint
            ok = (~tir) & (T_refr.max(axis=1) > MIN_THROUGHPUT)
            if ok.any():
                t_dir = (eta[ok, None] * d_g[ok]
                         + (eta[ok] * cos_i[ok] - cos_t[ok])[:, None]
                         * n_g[ok])
                t_dir /= np.linalg.norm(t_dir, axis=1, keepdims=True)
                next_o.append(p_g[ok] - n_g[ok] * OFFSET)  # cross the surface
                next_d.append(t_dir)
                next_p.append(pix_h[gm[ok]])
                next_T.append(T_refr[ok])
        elif len(gm):
            # Depth cap reached inside glass: approximate the residual with
            # the sky (rare, low-energy paths)
            np.add.at(accum, pix_h[gm], T_h[gm] * sky_color(d_h[gm]))

        if not next_d:
            break
        origins = np.vstack(next_o)
        dirs = np.vstack(next_d)
        pixel = np.concatenate(next_p)
        T = np.vstack(next_T)

    if progress is not None:
        progress(1.0)
    return accum


BAND_ROWS = 40  # rows traced per band (progressive display granularity)


def render_still(vertices, faces, vertex_normals, face_material,
                 cam, vp, lt, shadows_on=True, bounces=2, report=None,
                 floor_pattern='checker', progress=None, on_band=None):
    """Trace the scene to a (pane_width, pane_height, 3) uint8 image.

    All geometry in view space (camera at the origin looking +z).
    face_material: (M,) int (MAT_SILVER/MAT_FLOOR/MAT_GLASS), or a legacy
    bool array (True = floor). floor_pattern: 'checker' | 'stripes' |
    'rings' | 'plain'.

    The image is traced in horizontal bands of BAND_ROWS so callers can
    show it painting in: `on_band(y0, y1, band_img)` receives each finished
    (W, y1-y0, 3) uint8 slice. `progress` receives an overall 0..1
    fraction as the trace advances.
    """
    scene = Scene(vertices, faces, vertex_normals, face_material)

    # Shadow test sub-scenes: opaque geometry gives full shadow, glass
    # gives partial (light_factor) - see trace_rays
    fm = scene.face_material
    glass_mask = fm == MAT_GLASS
    if glass_mask.any():
        opaque_scene = Scene(scene.vertices, scene.faces[~glass_mask],
                             scene.vertex_normals, fm[~glass_mask])
        glass_scene = Scene(scene.vertices, scene.faces[glass_mask],
                            scene.vertex_normals, fm[glass_mask])
    else:
        opaque_scene = scene
        glass_scene = None
    ctx = {'scene': scene, 'opaque_scene': opaque_scene,
           'glass_scene': glass_scene}

    W, H = vp.width, vp.height
    ppu = cam.pixels_per_unit
    img = np.zeros((W, H, 3), dtype=np.uint8)

    n_bands = (H + BAND_ROWS - 1) // BAND_ROWS
    stats = [{'rays': 0, 'hits': 0} for _ in range(MAX_DEPTH + 1)]

    for b in range(n_bands):
        y0 = b * BAND_ROWS
        y1 = min(y0 + BAND_ROWS, H)

        # Primary rays for this band of rows (pinhole at the origin)
        px, py = np.meshgrid(np.arange(W) + 0.5, np.arange(y0, y1) + 0.5,
                             indexing='ij')
        dirs = np.stack([(px.ravel() - W / 2.0) / ppu,
                         (py.ravel() - H / 2.0) / ppu,
                         np.ones(px.size)], axis=1)
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        origins = np.zeros_like(dirs)

        band_progress = None
        if progress is not None:
            band_progress = (lambda base: lambda f:
                             progress((base + f) / n_bands))(b)

        colors = trace_rays(ctx, origins, dirs, lt, shadows_on=shadows_on,
                            bounces=bounces, floor_pattern=floor_pattern,
                            progress=band_progress, stats=stats)
        band = colors.reshape(W, y1 - y0, 3).clip(0, 255).astype(np.uint8)
        img[:, y0:y1] = band
        if on_band is not None:
            on_band(y0, y1, band)

    if progress is not None:
        progress(1.0)
    if report:
        report('; '.join(f"bounce {i}: {s['rays']} rays, {s['hits']} hits"
                         for i, s in enumerate(stats) if s['rays']))
    return img


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
