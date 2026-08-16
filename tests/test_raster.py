# Author: Dominic Williams
# Date created: August 16, 2026
#
# Unit tests for the scanline triangle rasteriser (offscreen, headless)

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

import raster

pygame.init()

BLACK = (0, 0, 0)


def make_surface():
    surf = pygame.Surface((100, 100))
    surf.fill(BLACK)
    return surf


def test_gouraud_corners_match_vertex_colors():
    surf = make_surface()
    raster.fill_gouraud(surf, ((10, 10), (90, 20), (40, 90)),
                        ((255, 0, 0), (0, 255, 0), (0, 0, 255)),
                        (0, 0, 99, 99))
    r = surf.get_at((14, 14))[:3]
    g = surf.get_at((85, 21))[:3]
    b = surf.get_at((41, 85))[:3]
    assert r[0] > 200 and r[1] < 60 and r[2] < 60
    assert g[1] > 200 and g[0] < 60 and g[2] < 60
    assert b[2] > 200 and b[0] < 60 and b[1] < 60


def test_gouraud_interpolates_between_colors():
    # Left edge red, right edge blue: a middle pixel holds a genuine mix
    surf = make_surface()
    raster.fill_gouraud(surf, ((10, 50), (90, 50), (50, 10)),
                        ((255, 0, 0), (0, 0, 255), (128, 0, 128)),
                        (0, 0, 99, 99))
    mid = surf.get_at((50, 45))[:3]
    assert 60 < mid[0] < 200
    assert 60 < mid[2] < 200


def test_raster_respects_bounds():
    # Bounds cover only the left half; no pixel to the right may be written
    surf = make_surface()
    raster.fill_gouraud(surf, ((10, 10), (90, 10), (50, 90)),
                        ((255, 255, 255),) * 3,
                        (0, 0, 49, 99))
    for x in (50, 60, 80):
        for y in (11, 30, 50):
            assert surf.get_at((x, y))[:3] == BLACK
    assert surf.get_at((40, 15))[:3] != BLACK


def test_phong_fill_writes_lit_pixels():
    import light
    surf = make_surface()
    lt = light.Light()
    # Normal pointing back at the camera on the mirror half-vector: bright
    import matrix
    n = matrix.NormaliseVector((lt.to_light[0], lt.to_light[1],
                                lt.to_light[2] - 1.0))
    raster.fill_phong(surf, ((10, 10), (90, 10), (50, 60)),
                      (n, n, n), ((0, 0, 5),) * 3, lt, (0, 0, 99, 99))
    px = surf.get_at((50, 20))[:3]
    assert px != BLACK
    assert px[0] > 200  # specular pushes toward white
