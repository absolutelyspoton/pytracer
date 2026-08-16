# Author: Dominic Williams
# Date created: 10 Aug 2022
# v3 (Aug 2026): array-oriented pipeline on numpy - batched transforms,
# fragment rasterisation with a z-buffer, deferred batch shading, per-frame
# shadow mapping. Same five render modes and key bindings as v2.
#
# Simple Wireframe Viewing System using pygame for 2D graphical drawing system

import numpy as np
import pygame
import sys

import camera as camera_module
import light
import loader
import matrix
import mesh as mesh_module
import render
import shadow
import viewer_state
import viewport

INPUT_DATA_SOURCE = 'file'  # 'db' or 'file'
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 800

# Filled-mode quality: while the view changes, the fragment pipeline renders
# at SSAA_INTERACTIVE x pane resolution (0.5 = half res, smooth-upscaled);
# once the view has been still for STILL_FRAMES_FOR_HQ frames, one
# SSAA_STILL supersampled anti-aliased frame is rendered (~0.3s) and cached
# until the view changes again.
SSAA_INTERACTIVE = 0.5
SSAA_STILL = 2
STILL_FRAMES_FOR_HQ = 15

# Color constants
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 100, 100)
COLOR_BLUE = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_MAGENTA = (255, 0, 255)

FLOOR_BASE_COLOR = (152, 152, 158)

the_mesh = None  # loaded in __main__


def start():
    """Main render loop using the array-oriented pipeline."""

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.fill(COLOR_WHITE)

    state = viewer_state.ViewerState(SCREEN_WIDTH, SCREEN_HEIGHT)
    input_handler = viewer_state.InputHandler(state)

    vp = viewport.DEFAULT_VIEWPORT
    state.camera.attach_viewport(vp)

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    help_font = pygame.font.Font(None, 28)
    fps_update_timer = 0
    current_fps = 0.0
    fps_text = font.render('FPS: 0.0', True, COLOR_BLACK)

    help_text = [
        'KEYBOARD CONTROLS:',
        'c - Center/reset view',
        'Arrow keys - Pan up/down/left/right',
        '+/- - Dolly camera in/out',
        'x/y/z - Spin on X/Y/Z axis',
        'a - Toggle axis legend',
        'n/v - Toggle vertex normals',
        'f - Toggle faces',
        's - Cycle render: wire/hidden-line/solid/gouraud/phong',
        'd - Toggle shadows',
        'b - Toggle backface culling (wireframe)',
        'h - Toggle this help',
        'q - Quit'
    ]

    # Model constants
    center_offset = the_mesh.center_offset()
    MC = matrix.TranslateMatrix(*center_offset)
    model_radius = the_mesh.bounding_radius()
    floor_y = model_radius * 1.05
    floor_half = model_radius * 4.0

    # Fragment-pipeline buffers per SSAA scale (surfarray layout (W, H, 3))
    buffers = {}
    for k in {SSAA_INTERACTIVE, SSAA_STILL}:
        w, h = int(vp.width * k), int(vp.height * k)
        buffers[k] = (pygame.Surface((w, h)), np.empty((w, h, 3), dtype=np.uint8))

    # Adaptive-quality state for the filled modes
    hq_sig = None       # view signature the cached still was rendered for
    hq_image = None     # cached pane-sized anti-aliased frame
    hq_faces = 0        # face count shown while the cache is displayed
    still_frames = 0
    shadow_cache_sig = None
    shadow_cache_map = None

    while True:
        state.update_continuous_rotations()
        screen.fill(COLOR_WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                input_handler.handle_keydown(event.key)

        # --- Transform stage: whole mesh in a few matmuls -----------------
        MS = matrix.ScaleMatrix(*state.scale)
        MR = matrix.RotateMatrix(*state.rotation)
        MT = matrix.TranslateMatrix(*state.translation)
        MV = MC @ MS @ MR @ MT @ state.camera.view_matrix()

        view_pts = matrix.transform_points(the_mesh.vertices, MV)
        face_normals = matrix.transform_directions(the_mesh.face_normals, MR)
        screen_pts, clipped = state.camera.project(view_pts, vp)

        faces = the_mesh.faces
        centroids = view_pts[faces].mean(axis=1)
        facing = -np.einsum('ij,ij->i', face_normals, centroids)
        face_clipped = clipped[faces].any(axis=1)

        mode = state.render_mode
        displayed_faces = 0

        screen.set_clip(pygame.Rect(vp.x, vp.y, vp.width, vp.height))

        if state.draw_faces and mode == 'wireframe':
            ok = ~face_clipped
            if state.backface_cull:
                ok &= facing > 0
            depths = centroids[:, 2]
            visible_z = view_pts[~clipped, 2]
            if visible_z.size:
                z_lo, z_hi = visible_z.min(), visible_z.max()
                span = max(z_hi - z_lo, 1e-9)
                cues = (190 * (depths - z_lo) / span).astype(np.int64).clip(0, 255)
                tri_screen = screen_pts[faces]
                for i in np.nonzero(ok)[0]:
                    c = int(cues[i])
                    pygame.draw.aalines(screen, (c, c, c), True, tri_screen[i])
                displayed_faces = int(ok.sum())

        elif state.draw_faces and mode == 'hidden-line':
            # Painter's algorithm is still the right tool for line art
            ok = np.nonzero(~face_clipped & (facing > 0))[0]
            order = ok[np.argsort(-centroids[ok, 2])]
            visible_z = view_pts[~clipped, 2]
            if visible_z.size:
                z_lo = visible_z.min()
                span = max(visible_z.max() - z_lo, 1e-9)
                tri_screen = screen_pts[faces]
                for i in order:
                    c = int(190 * (centroids[i, 2] - z_lo) / span)
                    pts = tri_screen[i]
                    pygame.draw.polygon(screen, COLOR_WHITE, pts, 0)
                    pygame.draw.aalines(screen, (c, c, c), True, pts)
                displayed_faces = len(order)

        elif state.draw_faces:
            # --- Fragment pipeline: solid / gouraud / phong ---------------
            # Adaptive quality: fast interactive render while the view moves,
            # one cached supersampled frame once it settles
            view_sig = (tuple(state.rotation), tuple(state.translation),
                        tuple(state.scale), state.camera.distance, mode,
                        state.show_shadows)
            if view_sig != hq_sig:
                hq_sig = view_sig
                hq_image = None
                still_frames = 0
            else:
                still_frames += 1

            if hq_image is not None:
                screen.blit(hq_image, (vp.x, vp.y))
                displayed_faces = hq_faces
            else:
                ssaa = (SSAA_STILL if still_frames >= STILL_FRAMES_FOR_HQ
                        else SSAA_INTERACTIVE)
                buf_surface, frame = buffers[ssaa]
                buf_w, buf_h = frame.shape[0], frame.shape[1]

                # Scene = model + floor geometry (the floor occludes and
                # receives shadows like everything else)
                D = state.camera.distance
                floor = mesh_module.floor_mesh(floor_y, floor_half, D,
                                               z_near=state.camera.near + 0.2)
                n_model = len(view_pts)
                floor_screen, floor_clipped = state.camera.project(
                    floor.vertices, vp)

                scene_view = np.vstack([view_pts, floor.vertices])
                scene_screen = np.vstack([screen_pts, floor_screen])
                scene_clipped = np.concatenate([clipped, floor_clipped])
                scene_faces = np.vstack([faces, floor.faces + n_model])
                scene_fnormals = np.vstack([face_normals, floor.face_normals])
                scene_vnormals = np.vstack([
                    matrix.transform_directions(the_mesh.vertex_normals, MR),
                    floor.vertex_normals])
                scene_centroids = scene_view[scene_faces].mean(axis=1)
                scene_facing = -np.einsum('ij,ij->i', scene_fnormals,
                                          scene_centroids)

                ok = (~scene_clipped[scene_faces].any(axis=1)) & (scene_facing > 0)
                draw_faces_arr = scene_faces[ok]
                displayed_faces = len(draw_faces_arr)

                buf_pts = (scene_screen - (vp.x, vp.y)) * ssaa
                frags = render.rasterize(buf_pts, scene_view[:, 2],
                                         draw_faces_arr, buf_w, buf_h)

                # Shadow map from the model only (the floor receives, the
                # model self-shadows), cached while the pose is unchanged.
                # Interactive frames use a smaller map (soft edges are
                # invisible at half res); stills get the full-size one.
                shadow_map = None
                if state.show_shadows and len(frags['x']):
                    map_size = 256 if ssaa == SSAA_STILL else 128
                    pose_sig = view_sig[:4] + (map_size,)
                    if pose_sig != shadow_cache_sig:
                        shadow_cache_map = shadow.build_shadow_map(
                            view_pts, faces, state.light, size=map_size)
                        shadow_cache_sig = pose_sig
                    shadow_map = shadow_cache_map

                # Material ratio that turns lit silver into lit floor grey
                floor_ratio = (np.asarray(FLOOR_BASE_COLOR, dtype=np.float64)
                               / np.asarray(light.MATERIAL_BASE_COLOR,
                                            dtype=np.float64))

                frame[:] = 255
                if len(frags['x']):
                    frag_face_rows = frags['face']  # index into draw_faces_arr

                    if mode == 'solid':
                        # Flat: light per FACE, shadow per face centroid
                        kept_centroids = scene_centroids[ok]
                        f_shadowed = (shadow_map.is_shadowed_batch(kept_centroids)
                                      if shadow_map is not None else None)
                        face_colors = light.phong_shade_batch(
                            scene_fnormals[ok], kept_centroids, state.light,
                            shadowed=f_shadowed).astype(np.float64)
                        floor_face = np.nonzero(ok)[0] >= len(faces)
                        face_colors[floor_face] *= floor_ratio
                        colors = face_colors[frag_face_rows].clip(0, 255) \
                                                            .astype(np.uint8)

                    elif mode == 'gouraud':
                        # Light and shadow per VERTEX, interpolate colours
                        v_shadowed = (shadow_map.is_shadowed_batch(scene_view)
                                      if shadow_map is not None else None)
                        vcolors = light.phong_shade_batch(
                            scene_vnormals, scene_view, state.light,
                            shadowed=v_shadowed).astype(np.float64)
                        vcolors[n_model:] *= floor_ratio
                        colors = render.interpolate(frags, draw_faces_arr,
                                                    vcolors) \
                                       .clip(0, 255).astype(np.uint8)

                    else:  # phong: everything per FRAGMENT
                        # One fused gather for positions + normals
                        attrs = render.interpolate(
                            frags, draw_faces_arr,
                            np.hstack([scene_view, scene_vnormals]))
                        frag_pos = attrs[:, :3]
                        frag_norm = attrs[:, 3:]
                        lens = np.linalg.norm(frag_norm, axis=1, keepdims=True)
                        lens[lens < 1e-12] = 1.0
                        frag_norm /= lens
                        shadowed = (shadow_map.is_shadowed_batch(frag_pos)
                                    if shadow_map is not None else None)
                        colors = light.phong_shade_batch(
                            frag_norm, frag_pos, state.light,
                            shadowed=shadowed).astype(np.float64)
                        floor_frag = (np.nonzero(ok)[0][frag_face_rows]
                                      >= len(faces))
                        colors[floor_frag] *= floor_ratio
                        colors = colors.clip(0, 255).astype(np.uint8)

                    frame[frags['x'], frags['y']] = colors

                pygame.surfarray.blit_array(buf_surface, frame)
                if ssaa != 1:
                    pane = pygame.transform.smoothscale(
                        buf_surface, (vp.width, vp.height))
                else:
                    pane = buf_surface
                if ssaa == SSAA_STILL:
                    hq_image = pane.copy()
                    hq_faces = displayed_faces
                screen.blit(pane, (vp.x, vp.y))

        # Vertex normal overlay
        if state.draw_normals:
            vnorm = matrix.transform_directions(the_mesh.vertex_normals, MR)
            show = ~clipped
            starts = screen_pts[show]
            ends = starts - vnorm[show][:, :2] * 10.0
            for (x1, y1), (x2, y2) in zip(starts, ends):
                pygame.draw.line(screen, COLOR_RED, (x1, y1), (x2, y2), 1)

        # Axis legend (fixed in viewport top-left corner)
        if state.draw_axes:
            tx, ty = vp.x + 20, vp.y + 20
            pygame.draw.line(screen, COLOR_GREEN, [tx, ty], [tx + 80, ty], 2)
            pygame.draw.line(screen, COLOR_BLUE, [tx, ty], [tx, ty + 80], 2)
            pygame.draw.line(screen, COLOR_MAGENTA, [tx, ty], [tx + 60, ty + 60], 2)

        screen.set_clip(None)
        vp.draw_frame(screen, color=COLOR_BLACK, thickness=2)

        # HUD
        fps_update_timer += 1
        if fps_update_timer >= 10:
            current_fps = clock.get_fps()
            in_pane = (~clipped
                       & (screen_pts[:, 0] >= vp.x_min)
                       & (screen_pts[:, 0] <= vp.x_max)
                       & (screen_pts[:, 1] >= vp.y_min)
                       & (screen_pts[:, 1] <= vp.y_max))
            displayed_vertices = int(in_pane.sum()) if state.draw_faces else 0
            shown_faces = displayed_faces if state.draw_faces else 0
            status_line = (
                f'{current_fps:.0f} FPS  '
                f'Vertices:{displayed_vertices}  Edges:{shown_faces * 3}  '
                f'Faces:{shown_faces}  Normals:{shown_faces}'
            )
            clipped_count = int(clipped.sum())
            if clipped_count:
                status_line += f'  Clipped:{clipped_count}'
            status_line += f'  [{state.render_mode}]'
            fps_text = font.render(status_line, True, COLOR_BLACK)
            fps_update_timer = 0

        screen.blit(fps_text, (10, 10))

        if state.show_help:
            help_y = 60
            for line in help_text:
                help_surface = help_font.render(line, True, COLOR_BLACK)
                screen.blit(help_surface, (10, help_y))
                help_y += 30

        pygame.display.flip()
        clock.tick(0)  # Unlimited FPS (0 means no cap)


if __name__ == '__main__':

    if INPUT_DATA_SOURCE == 'db':
        print("loading mesh from database ...")
        the_mesh = loader.load_mesh_api()
    else:
        print("loading mesh from file ...")
        the_mesh = loader.load_mesh_file()
    print(f'... done: {the_mesh}')

    print('starting render mode ...')
    start()
