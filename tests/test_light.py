# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the Phong reflection model

import matrix
import light


def test_normal_facing_light_gets_full_diffuse():
    lt = light.Light()
    base, spec = light.phong_intensity(lt.to_light, (0.0, 0.0, 5.0), lt)
    assert abs(base - (light.AMBIENT_COEFF + light.DIFFUSE_COEFF)) < 1e-9


def test_normal_facing_away_gets_ambient_only():
    lt = light.Light()
    away = (-lt.to_light[0], -lt.to_light[1], -lt.to_light[2])
    base, spec = light.phong_intensity(away, (0.0, 0.0, 5.0), lt)
    assert abs(base - light.AMBIENT_COEFF) < 1e-9
    assert spec == 0.0


def test_specular_peaks_at_mirror_geometry():
    # Viewer at origin looking at a point on the +z axis; a normal halfway
    # between the light and viewer directions gives the mirror reflection
    lt = light.Light()
    half = matrix.NormaliseVector((lt.to_light[0], lt.to_light[1],
                                   lt.to_light[2] - 1.0))
    _, spec_mirror = light.phong_intensity(half, (0.0, 0.0, 5.0), lt)
    _, spec_offset = light.phong_intensity(lt.to_light, (0.0, 0.0, 5.0), lt)
    assert spec_mirror > 0.3
    assert spec_mirror > spec_offset


def test_shade_stays_in_rgb_range():
    lt = light.Light(ambient=5.0, diffuse=5.0, specular=5.0)  # overdriven
    half = matrix.NormaliseVector((lt.to_light[0], lt.to_light[1],
                                   lt.to_light[2] - 1.0))
    for n in (lt.to_light, half, (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)):
        r, g, b = light.phong_shade(n, (0.0, 0.0, 5.0), lt)
        assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255
