# Author: Dominic Williams
# Date created: August 16, 2026
#
# Raster: pure-Python scanline triangle rasteriser with attribute
# interpolation, for the shading modes pygame.draw.polygon cannot do
# (per-pixel colour). Pixels are written with Surface.set_at, which ignores
# pygame's clip rect, so callers pass explicit bounds (the viewport pane)
# and the rasteriser clamps to them itself.
#
# The span loops step attributes incrementally (DDA) rather than
# re-interpolating per pixel, and fill_phong inlines the whole reflection
# model - per-pixel Python cost is the frame budget here, so the inner
# loops trade a little repetition for speed.

import light as light_module


def _sorted_by_y(pts, attrs):
    """Return the three (point, attr) pairs sorted top-to-bottom by y."""
    order = sorted(range(3), key=lambda i: pts[i][1])
    return [(pts[i], attrs[i]) for i in order]


def _edge_x_and_attrs(y, p_top, a_top, p_bot, a_bot):
    """Interpolate x and attributes along the edge p_top->p_bot at scanline y."""
    dy = p_bot[1] - p_top[1]
    t = (y - p_top[1]) / dy if dy > 1e-9 else 0.0
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    x = p_top[0] + (p_bot[0] - p_top[0]) * t
    attrs = tuple(a + (b - a) * t for a, b in zip(a_top, a_bot))
    return x, attrs


def fill_triangle(surface, pts, attrs, shade_fn, bounds):
    """Scanline-fill a triangle, interpolating attribute tuples.

    Generic path: shade_fn maps one interpolated attribute tuple to an
    (r, g, b) colour. The specialised fills below are the fast paths.
    """
    (p0, a0), (p1, a1), (p2, a2) = _sorted_by_y(pts, attrs)
    bx_min, by_min, bx_max, by_max = bounds

    y_start = max(int(p0[1] + 0.5), by_min)
    y_end = min(int(p2[1] + 0.5), by_max)
    mid_y = p1[1]
    set_at = surface.set_at

    for y in range(y_start, y_end + 1):
        xl, al = _edge_x_and_attrs(y, p0, a0, p2, a2)
        if y < mid_y:
            xr, ar = _edge_x_and_attrs(y, p0, a0, p1, a1)
        else:
            xr, ar = _edge_x_and_attrs(y, p1, a1, p2, a2)

        if xl > xr:
            xl, xr = xr, xl
            al, ar = ar, al

        x_start = max(int(xl + 0.5), bx_min)
        x_end = min(int(xr + 0.5), bx_max)
        if x_end < x_start:
            continue

        span = xr - xl
        if span > 1e-9:
            inv_span = 1.0 / span
            for x in range(x_start, x_end + 1):
                t = (x - xl) * inv_span
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                a = tuple(u + (v - u) * t for u, v in zip(al, ar))
                set_at((x, y), shade_fn(a))
        else:
            set_at((x_start, y), shade_fn(al))


def fill_gouraud(surface, pts, colors, bounds):
    """Gouraud fill: interpolate per-vertex (r, g, b) colours.

    Hot path: colours step incrementally across each span (three additions
    per pixel), with a cheap clamp because pixel-centre rounding can step
    just past the span's end values.
    """
    (p0, a0), (p1, a1), (p2, a2) = _sorted_by_y(pts, colors)
    bx_min, by_min, bx_max, by_max = bounds

    y_start = max(int(p0[1] + 0.5), by_min)
    y_end = min(int(p2[1] + 0.5), by_max)
    mid_y = p1[1]
    set_at = surface.set_at

    for y in range(y_start, y_end + 1):
        xl, al = _edge_x_and_attrs(y, p0, a0, p2, a2)
        if y < mid_y:
            xr, ar = _edge_x_and_attrs(y, p0, a0, p1, a1)
        else:
            xr, ar = _edge_x_and_attrs(y, p1, a1, p2, a2)

        if xl > xr:
            xl, xr = xr, xl
            al, ar = ar, al

        x_start = max(int(xl + 0.5), bx_min)
        x_end = min(int(xr + 0.5), bx_max)
        if x_end < x_start:
            continue

        r, g, b = al
        span = xr - xl
        if span >= 1.0:
            inv_span = 1.0 / span
            dr = (ar[0] - r) * inv_span
            dg = (ar[1] - g) * inv_span
            db = (ar[2] - b) * inv_span
            off = x_start - xl
            if off > 0.0:
                r += dr * off
                g += dg * off
                b += db * off
            for x in range(x_start, x_end + 1):
                ri = int(r)
                gi = int(g)
                bi = int(b)
                if ri < 0:
                    ri = 0
                elif ri > 255:
                    ri = 255
                if gi < 0:
                    gi = 0
                elif gi > 255:
                    gi = 255
                if bi < 0:
                    bi = 0
                elif bi > 255:
                    bi = 255
                set_at((x, y), (ri, gi, bi))
                r += dr
                g += dg
                b += db
        else:
            set_at((x_start, y), (int(r), int(g), int(b)))


def fill_depth(depth, pts, depths, size):
    """Scanline-rasterise a triangle into a 2D depth buffer, keeping the
    minimum depth per cell. Used to build the shadow map: the light 'sees'
    the nearest surface along each texel."""
    (p0, d0), (p1, d1), (p2, d2) = _sorted_by_y(pts, [(depths[0],),
                                                      (depths[1],),
                                                      (depths[2],)])
    last = size - 1
    y_start = max(int(p0[1] + 0.5), 0)
    y_end = min(int(p2[1] + 0.5), last)
    mid_y = p1[1]

    for y in range(y_start, y_end + 1):
        xl, al = _edge_x_and_attrs(y, p0, d0, p2, d2)
        if y < mid_y:
            xr, ar = _edge_x_and_attrs(y, p0, d0, p1, d1)
        else:
            xr, ar = _edge_x_and_attrs(y, p1, d1, p2, d2)

        if xl > xr:
            xl, xr = xr, xl
            al, ar = ar, al

        x_start = max(int(xl + 0.5), 0)
        x_end = min(int(xr + 0.5), last)
        if x_end < x_start:
            continue

        row = depth[y]
        d = al[0]
        span = xr - xl
        if span >= 1.0:
            dd = (ar[0] - d) / span
            off = x_start - xl
            if off > 0.0:
                d += dd * off
            for x in range(x_start, x_end + 1):
                if d < row[x]:
                    row[x] = d
                d += dd
        else:
            if d < row[x_start]:
                row[x_start] = d


def fill_phong(surface, pts, normals, view_pts, lt, bounds, step=1,
               shadow=None):
    """Phong fill: interpolate normals + view positions, light per pixel.

    The reflection model is inlined (no per-pixel function calls). With
    step > 1 lighting is evaluated every `step` pixels and held between
    evaluations - used for the fast interactive render; anti-aliased stills
    use step=1. `shadow` is an optional shadow.ShadowMap: shadowed pixels
    keep ambient light only (self-shadowing in stills).
    """
    attrs = [normals[i] + view_pts[i] for i in range(3)]
    (p0, a0), (p1, a1), (p2, a2) = _sorted_by_y(pts, attrs)
    bx_min, by_min, bx_max, by_max = bounds

    y_start = max(int(p0[1] + 0.5), by_min)
    y_end = min(int(p2[1] + 0.5), by_max)
    mid_y = p1[1]
    set_at = surface.set_at

    # Hoist light/material constants out of the pixel loop
    lx, ly, lz = lt.to_light
    ka = light_module.AMBIENT_COEFF * lt.ambient
    kd = light_module.DIFFUSE_COEFF * lt.diffuse
    ks = light_module.SPECULAR_COEFF * lt.specular
    shininess = light_module.SHININESS
    mr, mg, mb = light_module.MATERIAL_BASE_COLOR

    # Hoist shadow-map fields (consulted once per lighting evaluation)
    if shadow is not None:
        s_u, s_v, s_w = shadow.u, shadow.v, shadow.w
        s_umin, s_vmin = shadow.u_min, shadow.v_min
        s_su, s_sv = shadow.scale_u, shadow.scale_v
        s_bias, s_depth, s_last = shadow.bias, shadow.depth, shadow.size - 1

    for y in range(y_start, y_end + 1):
        xl, al = _edge_x_and_attrs(y, p0, a0, p2, a2)
        if y < mid_y:
            xr, ar = _edge_x_and_attrs(y, p0, a0, p1, a1)
        else:
            xr, ar = _edge_x_and_attrs(y, p1, a1, p2, a2)

        if xl > xr:
            xl, xr = xr, xl
            al, ar = ar, al

        x_start = max(int(xl + 0.5), bx_min)
        x_end = min(int(xr + 0.5), bx_max)
        if x_end < x_start:
            continue

        nx, ny, nz, px, py, pz = al
        span = xr - xl
        if span >= 1.0:
            inv_span = 1.0 / span
            dnx = (ar[0] - nx) * inv_span
            dny = (ar[1] - ny) * inv_span
            dnz = (ar[2] - nz) * inv_span
            dpx = (ar[3] - px) * inv_span
            dpy = (ar[4] - py) * inv_span
            dpz = (ar[5] - pz) * inv_span
            off = x_start - xl
            if off > 0.0:
                nx += dnx * off
                ny += dny * off
                nz += dnz * off
                px += dpx * off
                py += dpy * off
                pz += dpz * off
        else:
            dnx = dny = dnz = dpx = dpy = dpz = 0.0

        color = None
        since_eval = step  # force an evaluation on the first pixel
        for x in range(x_start, x_end + 1):
            if since_eval >= step:
                since_eval = 0
                # Normalise the interpolated normal
                n_len = (nx * nx + ny * ny + nz * nz) ** 0.5
                if n_len > 1e-9:
                    inv_n = 1.0 / n_len
                    ux = nx * inv_n
                    uy = ny * inv_n
                    uz = nz * inv_n
                else:
                    ux = uy = uz = 0.0

                # Phong reflection model, inlined
                n_dot_l = ux * lx + uy * ly + uz * lz
                base = ka
                spec = 0.0
                lit = n_dot_l > 0.0
                if lit and shadow is not None:
                    # Shadow-map test: light-space transform + depth compare
                    lu = px * s_u[0] + py * s_u[1] + pz * s_u[2]
                    lv = px * s_v[0] + py * s_v[1] + pz * s_v[2]
                    lw = px * s_w[0] + py * s_w[1] + pz * s_w[2]
                    ix = int((lu - s_umin) * s_su)
                    iy = int((lv - s_vmin) * s_sv)
                    if ix < 0:
                        ix = 0
                    elif ix > s_last:
                        ix = s_last
                    if iy < 0:
                        iy = 0
                    elif iy > s_last:
                        iy = s_last
                    if lw > s_depth[iy][ix] + s_bias:
                        lit = False
                if lit:
                    base += kd * n_dot_l
                    rx = 2.0 * n_dot_l * ux - lx
                    ry = 2.0 * n_dot_l * uy - ly
                    rz = 2.0 * n_dot_l * uz - lz
                    p_len = (px * px + py * py + pz * pz) ** 0.5
                    if p_len > 1e-9:
                        r_dot_v = -(rx * px + ry * py + rz * pz) / p_len
                        if r_dot_v > 0.0:
                            spec = ks * (r_dot_v ** shininess)

                white = 255.0 * spec
                ri = int(mr * base + white)
                gi = int(mg * base + white)
                bi = int(mb * base + white)
                if ri > 255:
                    ri = 255
                if gi > 255:
                    gi = 255
                if bi > 255:
                    bi = 255
                color = (ri, gi, bi)

            set_at((x, y), color)
            since_eval += 1
            nx += dnx
            ny += dny
            nz += dnz
            px += dpx
            py += dpy
            pz += dpz


if __name__ == '__main__':
    import os
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    import pygame
    import matrix
    pygame.init()

    surf = pygame.Surface((100, 100))
    surf.fill((0, 0, 0))
    bounds = (0, 0, 99, 99)

    # Gouraud: red / green / blue corners
    fill_gouraud(surf, ((10, 10), (90, 20), (40, 90)),
                 ((255, 0, 0), (0, 255, 0), (0, 0, 255)), bounds)
    print('corner near red   :', surf.get_at((14, 14))[:3])
    print('corner near green :', surf.get_at((85, 21))[:3])
    print('corner near blue  :', surf.get_at((41, 85))[:3])
    print('centre-ish        :', surf.get_at((45, 40))[:3])

    # Phong: mirror-reflection normal gives a bright specular fill
    lt = light_module.Light()
    n = matrix.NormaliseVector((lt.to_light[0], lt.to_light[1],
                                lt.to_light[2] - 1.0))
    fill_phong(surf, ((10, 10), (90, 10), (50, 60)),
               (n, n, n), ((0, 0, 5), (0, 0, 5), (0, 0, 5)), lt, bounds)
    print('phong sample      :', surf.get_at((50, 30))[:3])
