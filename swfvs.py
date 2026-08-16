# Author: Dominic Williams
# Date created: 10 Aug 2022
#
# Simple Wireframe Viewing System using pygame for 2D graphical drawing system

import pygame
import time
import loader
import matrix
import sys
import surface
import vertex as v
import viewer_state
import viewport
import light
import raster

INPUT_DATA_SOURCE = 'file'  # 'db' or 'file'
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 800

# Gouraud/Phong rasterise per pixel in pure Python, so they render into a
# reduced-resolution buffer scaled up to the pane. 2 = half resolution
# (4x fewer pixels); set to 1 for full resolution at ~4x the frame time.
RENDER_SCALE = 2

# Solid mode anti-aliasing: supersample the pane by this factor and smooth-
# downscale (pygame polygon fills are C-speed, so 2x2 oversampling is cheap).
# Set to 1 to disable.
SOLID_SSAA = 2

# Gouraud/Phong still-image anti-aliasing: while the view is changing they
# render at 1/RENDER_SCALE resolution for interactivity; once the view has
# been still for STILL_FRAMES_FOR_HQ frames, one supersampled frame is
# rendered at SSAA_STILL x pane resolution (slow - seconds for Phong) and
# cached until the view changes again.
SSAA_STILL = 2
STILL_FRAMES_FOR_HQ = 15

# Interactive Phong evaluates lighting every Nth pixel (held between) for
# speed; anti-aliased stills always use per-pixel lighting (step 1).
PHONG_INTERACTIVE_STEP = 2

# Color constants
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 100, 100)
COLOR_BLUE = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_MAGENTA = (255, 0, 255)

vertices = v.vertices()
surfaces = surface.surface()


def validate_surfaces(surfaces, vertex_count):
    """Validate that all surface vertex references are within range."""
    for face in surfaces.surface_list:
        for vertex_idx in face.vertex_list:
            if vertex_idx < 1 or vertex_idx > vertex_count:
                raise ValueError(
                    f"Face {face.index} references vertex {vertex_idx}, "
                    f"but only {vertex_count} vertices loaded"
                )


def start():
    """Main render loop using encapsulated ViewerState."""

    # Initialize pygame
    pygame.init()
    size = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode(size)
    screen.fill(COLOR_WHITE)

    # Initialize state and input handler
    state = viewer_state.ViewerState(SCREEN_WIDTH, SCREEN_HEIGHT)
    input_handler = viewer_state.InputHandler(state)

    # Initialize viewport (800×600 centered in main window) and point the
    # camera's projection at it
    vp = viewport.DEFAULT_VIEWPORT
    state.camera.attach_viewport(vp)

    # Center the model about the world origin (the teapot data sits on y=0),
    # so it rotates about its middle and frames symmetrically in the pane
    xs = [vtx.x_world for vtx in vertices.vertex_list]
    ys = [vtx.y_world for vtx in vertices.vertex_list]
    zs = [vtx.z_world for vtx in vertices.vertex_list]
    MC = matrix.TranslateMatrix(-(min(xs) + max(xs)) / 2.0,
                                -(min(ys) + max(ys)) / 2.0,
                                -(min(zs) + max(zs)) / 2.0)

    # Offscreen buffer for the per-pixel shading modes (see RENDER_SCALE)
    raster_buffer = pygame.Surface((vp.width // RENDER_SCALE,
                                    vp.height // RENDER_SCALE))

    # Oversized buffer for solid-mode supersampled anti-aliasing (SOLID_SSAA)
    solid_buffer = pygame.Surface((vp.width * SOLID_SSAA,
                                   vp.height * SOLID_SSAA))

    # Oversized buffer + cache for Gouraud/Phong anti-aliased stills
    hq_buffer = pygame.Surface((vp.width * SSAA_STILL,
                                vp.height * SSAA_STILL))
    hq_sig = None      # view signature the cached still was rendered for
    hq_image = None    # cached pane-sized anti-aliased still
    still_frames = 0   # consecutive frames with an unchanged view

    # Rendering resources
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    help_font = pygame.font.Font(None, 28)
    fps_update_timer = 0
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
        'b - Toggle backface culling (wireframe)',
        'h - Toggle this help',
        'q - Quit'
    ]

    while True:
        # Update continuous rotations
        state.update_continuous_rotations()
        screen.fill(COLOR_WHITE)

        # Handle input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()

                input_handler.handle_keydown(event.key)

        # Compute transformations: model (scale·rotate·translate) composed
        # with the camera's view matrix, so view space has the camera at the
        # origin looking toward +z.
        MS = matrix.ScaleMatrix(*state.scale)
        MR = matrix.RotateMatrix(*state.rotation)
        MT = matrix.TranslateMatrix(*state.translation)
        MV = matrix.MatrixMult(MC, MS)
        MV = matrix.MatrixMult(MV, MR)
        MV = matrix.MatrixMult(MV, MT)
        MV = matrix.MatrixMult(MV, state.camera.view_matrix())
        P = state.camera.projection_matrix()

        # Transform vertices: world -> view -> perspective divide -> pane
        for vertex in vertices.vertex_list:
            vertex.calc_view_coordinates(MV)
            vertex.calc_screen_coordinates(P, state.camera, vp)

        # View-space normals, needed for facing tests in hidden-line and solid
        # modes and for the optional wireframe backface cull. Rotation
        # preserves unit length, so these stay normalised.
        transformed_normals = None
        if state.draw_faces and (state.render_mode != 'wireframe' or state.backface_cull):
            transformed_normals = [matrix.MatrixVector(MR, face.normal)
                                   for face in surfaces.surface_list]

        # Clip all geometry drawing to the viewport pane. Pygame clips at the
        # pixel level, so faces straddling the pane edge are partially drawn
        # (no gaps) and nothing renders outside the pane.
        screen.set_clip(pygame.Rect(vp.x, vp.y, vp.width, vp.height))

        # Draw faces
        if state.draw_faces:
            vlist = vertices.vertex_list

            # Depth range for depth cueing: near edges draw black, far edges
            # fade toward light grey
            z_lo = None
            z_hi = None
            for vtx in vlist:
                if vtx.clipped:
                    continue
                z = vtx.z_view
                if z_lo is None or z < z_lo:
                    z_lo = z
                if z_hi is None or z > z_hi:
                    z_hi = z
            z_span = (z_hi - z_lo) if (z_lo is not None and z_hi > z_lo) else 1.0

            if z_lo is None:
                pass  # everything clipped, nothing to draw

            elif state.render_mode == 'wireframe':
                for face_idx, face in enumerate(surfaces.surface_list):
                    va = vlist[face.vertex_list[0] - 1]
                    vb = vlist[face.vertex_list[1] - 1]
                    vc = vlist[face.vertex_list[2] - 1]
                    if va.clipped or vb.clipped or vc.clipped:
                        continue

                    # Backface culling (optional): back-facing when the normal
                    # points away from the camera at the view-space origin
                    if state.backface_cull:
                        n = transformed_normals[face_idx]
                        if (n[0] * va.x_view + n[1] * va.y_view + n[2] * va.z_view) > 0:
                            continue

                    depth = (va.z_view + vb.z_view + vc.z_view) / 3.0
                    cue = int(190 * (depth - z_lo) / z_span)
                    pygame.draw.aalines(screen, (cue, cue, cue), True,
                                        ((va.x_screen, va.y_screen),
                                         (vb.x_screen, vb.y_screen),
                                         (vc.x_screen, vc.y_screen)))

            else:
                # Painter's algorithm for all filled modes: collect
                # front-facing faces, then draw far-to-near so nearer faces
                # paint over further ones.
                mode = state.render_mode

                # Gouraud/Phong: track whether the view changed; a cached
                # anti-aliased still short-circuits the whole frame build
                if mode in ('gouraud', 'phong'):
                    view_sig = (tuple(state.rotation), tuple(state.translation),
                                tuple(state.scale), state.camera.distance, mode)
                    if view_sig != hq_sig:
                        hq_sig = view_sig
                        hq_image = None
                        still_frames = 0
                    else:
                        still_frames += 1
                use_cached_still = (mode in ('gouraud', 'phong')
                                    and hq_image is not None)

                # Smooth shading needs per-vertex view-space normals; Gouraud
                # additionally lights every vertex once, up front
                if mode in ('gouraud', 'phong') and not use_cached_still:
                    view_normals = [matrix.MatrixVector(MR, vtx.normal)
                                    for vtx in vlist]
                if mode == 'gouraud' and not use_cached_still:
                    vertex_colors = [light.phong_shade(
                                         view_normals[i],
                                         (vtx.x_view, vtx.y_view, vtx.z_view),
                                         state.light)
                                     for i, vtx in enumerate(vlist)]

                render_list = []
                for face_idx, face in ([] if use_cached_still
                                       else enumerate(surfaces.surface_list)):
                    i1 = face.vertex_list[0] - 1
                    i2 = face.vertex_list[1] - 1
                    i3 = face.vertex_list[2] - 1
                    va, vb, vc = vlist[i1], vlist[i2], vlist[i3]
                    if va.clipped or vb.clipped or vc.clipped:
                        continue

                    n = transformed_normals[face_idx]
                    cx = (va.x_view + vb.x_view + vc.x_view) / 3.0
                    cy = (va.y_view + vb.y_view + vc.y_view) / 3.0
                    cz = (va.z_view + vb.z_view + vc.z_view) / 3.0
                    facing = -(n[0] * cx + n[1] * cy + n[2] * cz)
                    if facing <= 0:
                        continue

                    pts = ((va.x_screen, va.y_screen),
                           (vb.x_screen, vb.y_screen),
                           (vc.x_screen, vc.y_screen))
                    if mode == 'hidden-line':
                        shade = int(190 * (cz - z_lo) / z_span)  # edge depth cue
                        payload = (shade, shade, shade)
                    elif mode == 'solid':
                        # Flat shading: one lighting evaluation per face
                        payload = light.phong_shade(n, (cx, cy, cz), state.light)
                    elif mode == 'gouraud':
                        payload = (vertex_colors[i1], vertex_colors[i2],
                                   vertex_colors[i3])
                    else:  # phong
                        payload = ((view_normals[i1], view_normals[i2],
                                    view_normals[i3]),
                                   ((va.x_view, va.y_view, va.z_view),
                                    (vb.x_view, vb.y_view, vb.z_view),
                                    (vc.x_view, vc.y_view, vc.z_view)))
                    render_list.append((cz, payload, pts))

                render_list.sort(key=lambda t: -t[0])  # far first

                if mode == 'hidden-line':
                    # Fill with background to erase edges behind, then outline
                    # with the depth-cued colour (antialiased)
                    for depth, colr, pts in render_list:
                        pygame.draw.polygon(screen, COLOR_WHITE, pts, 0)
                        pygame.draw.aalines(screen, colr, True, pts)
                elif mode == 'solid':
                    if SOLID_SSAA > 1:
                        # Supersample: fill at SSAA x pane resolution, then
                        # smooth-downscale into the pane for anti-aliasing
                        buf = solid_buffer
                        buf.fill(COLOR_WHITE)
                        ss = SOLID_SSAA
                        for depth, colr, pts in render_list:
                            bpts = tuple(((p[0] - vp.x) * ss, (p[1] - vp.y) * ss)
                                         for p in pts)
                            pygame.draw.polygon(buf, colr, bpts, 0)
                        screen.blit(pygame.transform.smoothscale(
                            buf, (vp.width, vp.height)), (vp.x, vp.y))
                    else:
                        for depth, colr, pts in render_list:
                            pygame.draw.polygon(screen, colr, pts, 0)
                else:
                    # Gouraud/Phong rasterise per pixel in pure Python. While
                    # the view is changing they use the reduced-resolution
                    # buffer for interactivity; once still, one supersampled
                    # anti-aliased frame is rendered and cached (see the
                    # SSAA_STILL / STILL_FRAMES_FOR_HQ constants).
                    if use_cached_still:
                        screen.blit(hq_image, (vp.x, vp.y))
                    else:
                        if still_frames >= STILL_FRAMES_FOR_HQ:
                            buf = hq_buffer
                            pt_scale = float(SSAA_STILL)
                            print(f'rendering anti-aliased {mode} still ...')
                        else:
                            buf = raster_buffer
                            pt_scale = 1.0 / RENDER_SCALE

                        # The rasteriser writes pixels directly (set_at
                        # ignores the clip rect), so it gets bounds explicitly
                        buf.fill(COLOR_WHITE)
                        bounds = (0, 0, buf.get_width() - 1, buf.get_height() - 1)

                        if mode == 'gouraud':
                            for depth, colors, pts in render_list:
                                bpts = tuple(((p[0] - vp.x) * pt_scale,
                                              (p[1] - vp.y) * pt_scale)
                                             for p in pts)
                                raster.fill_gouraud(buf, bpts, colors, bounds)
                        else:  # phong
                            phong_step = (1 if buf is hq_buffer
                                          else PHONG_INTERACTIVE_STEP)
                            for depth, (normals, view_pts), pts in render_list:
                                bpts = tuple(((p[0] - vp.x) * pt_scale,
                                              (p[1] - vp.y) * pt_scale)
                                             for p in pts)
                                raster.fill_phong(buf, bpts, normals, view_pts,
                                                  state.light, bounds,
                                                  step=phong_step)

                        scaled = pygame.transform.smoothscale(
                            buf, (vp.width, vp.height))
                        if buf is hq_buffer:
                            hq_image = scaled
                            print('... done')
                        screen.blit(scaled, (vp.x, vp.y))

        # Draw vertex normals (clip rect trims any that cross the pane edge)
        if state.draw_normals:
            for vertex in vertices.vertex_list:
                if not vertex.normal or vertex.clipped:
                    continue
                x1, y1 = vertex.x_screen, vertex.y_screen
                x2 = x1 - vertex.normal[0] * 10
                y2 = y1 - vertex.normal[1] * 10
                pygame.draw.line(screen, COLOR_RED, [x1, y1], [x2, y2], 1)

        # Draw axis legend (fixed in viewport top-left corner)
        if state.draw_axes:
            # Draw at fixed position in viewport (top-left + offset)
            tx = vp.x + 20
            ty = vp.y + 20
            axis_len = 80
            pygame.draw.line(screen, COLOR_GREEN, [tx, ty], [tx + axis_len, ty], 2)
            pygame.draw.line(screen, COLOR_BLUE, [tx, ty], [tx, ty + axis_len], 2)
            pygame.draw.line(screen, COLOR_MAGENTA, [tx, ty], [tx + 60, ty + 60], 2)

        # Geometry drawing done - remove clip so frame and HUD draw normally
        screen.set_clip(None)

        # Draw viewport frame
        vp.draw_frame(screen, color=COLOR_BLACK, thickness=2)

        # Draw FPS counter and geometry stats
        fps_update_timer += 1
        if fps_update_timer >= 10:
            current_fps = clock.get_fps()

            # Visibility is only needed for these stats, so compute it here
            # (every 10th frame) rather than per-vertex in the hot transform loop.
            in_pane = [vp.x_min <= vtx.x_screen <= vp.x_max and
                       vp.y_min <= vtx.y_screen <= vp.y_max
                       for vtx in vertices.vertex_list]

            displayed_vertices = sum(in_pane) if state.draw_faces else 0
            displayed_faces = 0
            displayed_edges = 0

            if state.draw_faces:
                for face_idx, face in enumerate(surfaces.surface_list):
                    va = vertices.vertex_list[face.vertex_list[0] - 1]
                    if state.backface_cull and state.render_mode == 'wireframe':
                        n = transformed_normals[face_idx]
                        if (n[0] * va.x_view + n[1] * va.y_view + n[2] * va.z_view) > 0:
                            continue

                    # A face is displayed if any vertex is in the pane
                    # (edge-straddling faces are partially drawn by the clip rect)
                    if (in_pane[face.vertex_list[0] - 1] or
                        in_pane[face.vertex_list[1] - 1] or
                        in_pane[face.vertex_list[2] - 1]):
                        displayed_faces += 1
                        displayed_edges += 3  # Each triangle has 3 edges

            displayed_normals = 0
            if state.draw_normals:
                displayed_normals = sum(1 for i, vtx in enumerate(vertices.vertex_list)
                                        if in_pane[i] and vtx.normal)
            if state.draw_faces:
                displayed_normals += displayed_faces  # Add face normals

            status_line = (
                f'{current_fps:.0f} FPS  '
                f'Vertices:{displayed_vertices}  Edges:{displayed_edges}  Faces:{displayed_faces}  Normals:{displayed_normals}'
            )
            clipped_count = sum(1 for vtx in vertices.vertex_list if vtx.clipped)
            if clipped_count:
                status_line += f'  Clipped:{clipped_count}'
            status_line += f'  [{state.render_mode}]'

            fps_text = font.render(status_line, True, COLOR_BLACK)
            fps_update_timer = 0

        screen.blit(fps_text, (10, 10))

        # Draw help overlay
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

        print("loading vertices from database ...")
        vertices = loader.load_vertices_api()
        print('... done')

        print("loading surfaces from database ...")
        surfaces = loader.load_surfaces_api()
        print('... done')

    elif INPUT_DATA_SOURCE == 'file':

        print("loading vertices from file ...")
        vertices = loader.load_vertices_file()
        print('... done')

        print("loading surfaces from file ...")
        surfaces = loader.load_surfaces_file()
        print('... done')

    print('validating surfaces ...')
    validate_surfaces(surfaces, vertices.vertex_count())
    print('... done')

    print('computing surface normals ...')
    loader.compute_surface_normals(surfaces, vertices)
    loader.compute_vertex_normals(surfaces, vertices)
    print('... done')

    print('starting render mode ...')
    start()
