# Author: Dominic Williams
# Date created: August 16, 2026
#
# Light: single directional light source and the Phong reflection model.
#
# All lighting is evaluated in view space, where the camera sits at the
# origin: the viewer direction from any surface point is -normalize(point).
# The light direction is likewise defined in view space, so it stays fixed
# relative to the viewer while the model rotates under it.

import numpy as np
import matrix

# Material properties (a future material concept can move these onto objects)
MATERIAL_BASE_COLOR = (190, 193, 200)  # silver/grey
AMBIENT_COEFF = 0.25   # ka
DIFFUSE_COEFF = 0.6    # kd - metals reflect more specularly than diffusely
SPECULAR_COEFF = 0.7   # ks
SHININESS = 40         # specular exponent - tight metallic highlight


class Light:
    """Directional light defined in view space."""

    def __init__(self, direction=(0.4, 0.6, 0.7),
                 ambient=1.0, diffuse=1.0, specular=1.0):
        # Default travels right/down/away in view space, i.e. the light sits
        # at the viewer's upper-left, in front of the model. (Screen y grows
        # downward, and +z points away from the camera.)
        # Direction the light travels; lighting math uses the reversed,
        # normalised vector pointing from the surface toward the light.
        d = matrix.NormaliseVector(direction)
        self.to_light = (-d[0], -d[1], -d[2])
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular

    def __repr__(self):
        return (f"Light(to_light={self.to_light}, ambient={self.ambient}, "
                f"diffuse={self.diffuse}, specular={self.specular})")


def phong_intensity(normal, point_view, light):
    """Phong reflection model. Returns (base, spec) where `base` in 0..1
    scales the material colour (ambient + diffuse) and `spec` in 0..1 is the
    white specular term added on top.

    normal must be unit length; point_view is the surface point in view space.
    """
    lx, ly, lz = light.to_light
    nx, ny, nz = normal

    # Diffuse: Lambert term N.L
    n_dot_l = nx * lx + ny * ly + nz * lz

    base = AMBIENT_COEFF * light.ambient
    spec = 0.0
    if n_dot_l > 0.0:
        base += DIFFUSE_COEFF * light.diffuse * n_dot_l

        # Specular: R.V with R = 2(N.L)N - L, V = direction to the viewer
        rx = 2.0 * n_dot_l * nx - lx
        ry = 2.0 * n_dot_l * ny - ly
        rz = 2.0 * n_dot_l * nz - lz
        px, py, pz = point_view
        p_len = (px * px + py * py + pz * pz) ** 0.5
        if p_len > 1e-9:
            # V = -point / |point| (camera at the view-space origin)
            r_dot_v = -(rx * px + ry * py + rz * pz) / p_len
            if r_dot_v > 0.0:
                spec = SPECULAR_COEFF * light.specular * (r_dot_v ** SHININESS)

    return (min(base, 1.0), min(spec, 1.0))


def phong_shade_batch(normals, points, light, shadowed=None):
    """Vectorised Phong reflection model.

    normals:  (N, 3) unit normals, view space
    points:   (N, 3) view-space positions (camera at the origin)
    shadowed: optional (N,) bool - shadowed samples keep ambient only
    Returns (N, 3) uint8 colours.
    """
    n = np.asarray(normals)
    p = np.asarray(points)
    L = np.asarray(light.to_light)

    n_dot_l = n @ L
    lit = n_dot_l > 0.0
    if shadowed is not None:
        lit = lit & ~np.asarray(shadowed)

    base = np.full(len(n), AMBIENT_COEFF * light.ambient)
    base[lit] += DIFFUSE_COEFF * light.diffuse * n_dot_l[lit]

    spec = np.zeros(len(n))
    if lit.any():
        nl = n[lit]
        pl = p[lit]
        refl = 2.0 * n_dot_l[lit, None] * nl - L
        p_len = np.linalg.norm(pl, axis=1)
        p_len[p_len < 1e-9] = 1.0
        r_dot_v = -np.einsum('ij,ij->i', refl, pl) / p_len
        pos = r_dot_v > 0.0
        s = np.zeros(len(nl))
        s[pos] = SPECULAR_COEFF * light.specular * r_dot_v[pos] ** SHININESS
        spec[lit] = s

    np.clip(base, None, 1.0, out=base)
    np.clip(spec, None, 1.0, out=spec)
    colors = (np.outer(base, np.asarray(MATERIAL_BASE_COLOR, dtype=np.float64))
              + 255.0 * spec[:, None])
    return np.clip(colors, 0, 255).astype(np.uint8)


def ambient_shade(light):
    """Material colour under ambient light only - what a fully shadowed
    surface receives."""
    base = min(AMBIENT_COEFF * light.ambient, 1.0)
    return (min(int(MATERIAL_BASE_COLOR[0] * base), 255),
            min(int(MATERIAL_BASE_COLOR[1] * base), 255),
            min(int(MATERIAL_BASE_COLOR[2] * base), 255))


def phong_shade(normal, point_view, light):
    """Full Phong shade of the material: returns an (r, g, b) colour."""
    base, spec = phong_intensity(normal, point_view, light)
    white = 255.0 * spec
    r = MATERIAL_BASE_COLOR[0] * base + white
    g = MATERIAL_BASE_COLOR[1] * base + white
    b = MATERIAL_BASE_COLOR[2] * base + white
    return (min(int(r), 255), min(int(g), 255), min(int(b), 255))


if __name__ == '__main__':
    lt = Light()
    print(lt)

    # Normal facing straight at the light: full diffuse
    print('facing light:', phong_shade(lt.to_light, (0.0, 0.0, 5.0), lt))
    # Normal facing away: ambient only
    away = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    print('facing away: ', phong_shade(away, (0.0, 0.0, 5.0), lt))
    # Mirror-reflection geometry (normal halfway between light and viewer):
    # strong specular
    half = matrix.NormaliseVector((lt.to_light[0], lt.to_light[1], lt.to_light[2] - 1.0))
    print('spec setup:  ', phong_shade(half, (0.0, 0.0, 5.0), lt))
