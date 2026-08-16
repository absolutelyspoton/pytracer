# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for refraction / glass materials

import math

import numpy as np

import camera
import light
import tracer
import viewport


def glass_panel_scene():
    """A glass panel in front of the floor, viewed straight on."""
    verts = np.array([
        [-2.0, -2.0, 4.0], [2.0, -2.0, 4.0],
        [2.0, 2.0, 4.0], [-2.0, 2.0, 4.0],        # glass panel (facing -z)
        [-30.0, 2.5, 0.5], [30.0, 2.5, 0.5],
        [30.0, 2.5, 30.0], [-30.0, 2.5, 30.0]])   # floor
    faces = np.array([[0, 2, 1], [0, 3, 2],
                      [4, 5, 6], [4, 6, 7]])
    vnorms = np.array([[0.0, 0.0, -1.0]] * 4 + [[0.0, -1.0, 0.0]] * 4)
    materials = np.array([tracer.MAT_GLASS, tracer.MAT_GLASS,
                          tracer.MAT_FLOOR, tracer.MAT_FLOOR])
    return verts, faces, vnorms, materials


def trace_scene(materials_override=None):
    verts, faces, vnorms, materials = glass_panel_scene()
    if materials_override is not None:
        materials = materials_override
    vp = viewport.Viewport(x=0, y=0, width=60, height=44)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    return tracer.render_still(verts, faces, vnorms, materials, cam, vp,
                               light.Light(), shadows_on=True, bounces=2)


def test_snell_straight_through_is_unbent():
    # Normal incidence: refracted direction equals the incoming direction
    d = np.array([0.0, 0.0, 1.0])
    n = np.array([0.0, 0.0, -1.0])
    eta = 1.0 / light.GLASS_IOR
    cos_i = -d @ n
    sin2_t = eta ** 2 * (1 - cos_i ** 2)
    cos_t = math.sqrt(1 - sin2_t)
    t = eta * d + (eta * cos_i - cos_t) * n
    assert np.allclose(t / np.linalg.norm(t), d)


def test_snell_bends_toward_normal_entering_glass():
    # 45 degrees into glass: sin(theta_t) = sin(45)/1.5 -> ~28.13 degrees
    theta_i = math.radians(45.0)
    d = np.array([math.sin(theta_i), 0.0, math.cos(theta_i)])
    n = np.array([0.0, 0.0, -1.0])
    eta = 1.0 / light.GLASS_IOR
    cos_i = -d @ n
    sin2_t = eta ** 2 * (1 - cos_i ** 2)
    cos_t = math.sqrt(1 - sin2_t)
    t = eta * d + (eta * cos_i - cos_t) * n
    t /= np.linalg.norm(t)
    theta_t = math.degrees(math.asin(t[0]))
    assert abs(theta_t - math.degrees(math.asin(math.sin(theta_i)
                                                / light.GLASS_IOR))) < 1e-9


def test_total_internal_reflection_beyond_critical_angle():
    # Glass -> air critical angle is asin(1/1.5) ~ 41.8 degrees
    theta_i = math.radians(50.0)
    eta = light.GLASS_IOR  # exiting
    sin2_t = eta ** 2 * (1 - math.cos(theta_i) ** 2)
    assert sin2_t > 1.0
    # Just below the critical angle transmits
    theta_i = math.radians(40.0)
    sin2_t = eta ** 2 * (1 - math.cos(theta_i) ** 2)
    assert sin2_t < 1.0


def test_schlick_normal_incidence_matches_r0():
    r0 = ((1.0 - light.GLASS_IOR) / (1.0 + light.GLASS_IOR)) ** 2
    fres = r0 + (1.0 - r0) * (1.0 - 1.0) ** 5  # cos = 1
    assert abs(fres - r0) < 1e-12
    assert abs(r0 - 0.04) < 0.001


def test_glass_panel_shows_floor_through_it():
    img_glass = trace_scene()
    # Same scene with the panel silver instead
    verts, faces, vnorms, materials = glass_panel_scene()
    silver_mats = materials.copy()
    silver_mats[:2] = tracer.MAT_SILVER
    img_silver = trace_scene(materials_override=silver_mats)

    # Centre pixels look through/at the panel. Through glass the floor's
    # two checker shades survive (dimmed and tinted); the silver panel
    # instead mirrors, giving a very different picture.
    centre_glass = img_glass[20:40, 15:30]
    centre_silver = img_silver[20:40, 15:30]
    assert not np.array_equal(centre_glass, centre_silver)
    # Glass keeps strong contrast from the checker seen through it
    lum = centre_glass[..., 0].astype(int)
    assert lum.max() - lum.min() > 40


def test_glass_shadow_is_partial_not_full():
    verts, faces, vnorms, materials = glass_panel_scene()
    vp = viewport.Viewport(x=0, y=0, width=60, height=44)
    cam = camera.Camera(distance=6.5)
    cam.attach_viewport(vp)
    lt = light.Light()
    img = tracer.render_still(verts, faces, vnorms, materials, cam, vp,
                              lt, shadows_on=True, bounces=2)
    img_off = tracer.render_still(verts, faces, vnorms, materials, cam, vp,
                                  lt, shadows_on=False, bounces=2)
    # Shadows darken somewhere, but glass transmits: nothing on the floor
    # loses ALL its direct light purely from the glass panel
    diff = img_off[..., 0].astype(int) - img[..., 0].astype(int)
    assert diff.max() > 5          # a shadow exists
    # The glass shadow keeps > GLASS_SHADOW_TRANSMISSION of diffuse: the
    # darkening is bounded well below a full shadow's
    full_shadow_drop = (light.DIFFUSE_COEFF
                        * light.CHECKER_LIGHT[0])  # upper bound scale
    assert diff.max() < full_shadow_drop * (1 - 0.3)
