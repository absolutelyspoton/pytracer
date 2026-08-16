# Author: Dominic Williams
# Date created: 10 Aug 2022
#
# Simple Wireframe Viewing System using pygame for 2D graphical drawing system

import pygame
import time
import loader
import matrix
import sys
import math
import surface
import vertex as v
import viewer_state
import viewport

INPUT_DATA_SOURCE = 'file'  # 'db' or 'file'
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 800

# Color constants
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 100, 100)
COLOR_BLUE = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_MAGENTA = (255, 0, 255)

vertices = v.vertices()
surfaces = surface.surface()


def CalcVectorNormals():
    """Calculate vertex normals from surface normals."""
    print('calculating vertex normals from surface normals ...')
    for vertex in vertices.vertex_list:
        totalvec_x = 0
        totalvec_y = 0
        totalvec_z = 0
        sc = 0
        for s in surfaces.surface_list:
            if vertex.index in s.vertex_list:
                totalvec_x = totalvec_x + s.normal[0]
                totalvec_y = totalvec_y + s.normal[1]
                totalvec_z = totalvec_z + s.normal[2]
                sc += 1
        if sc > 0:
            vertex.normal = matrix.NormaliseVector([totalvec_x/sc, totalvec_y/sc, totalvec_z/sc])
    print('... done')


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
        's - Cycle render mode (wireframe/hidden-line/solid)',
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

                # Special handling for normals toggle (needs CalcVectorNormals call)
                if event.key == pygame.K_n or event.key == pygame.K_v:
                    state.toggle_normals()
                    status = 'on' if state.draw_normals else 'off'
                    print(f'vertex normals {status} ...')
                    if state.draw_normals and not state.normals_calculated:
                        CalcVectorNormals()
                        state.normals_calculated = True
                else:
                    # All other input to handler
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
                    pygame.draw.polygon(screen, (cue, cue, cue),
                                        ((va.x_screen, va.y_screen),
                                         (vb.x_screen, vb.y_screen),
                                         (vc.x_screen, vc.y_screen)), 1)

            else:
                # Painter's algorithm for hidden-line and solid modes: collect
                # front-facing faces, then draw far-to-near so nearer faces
                # paint over further ones.
                solid = state.render_mode == 'solid'
                render_list = []
                for face_idx, face in enumerate(surfaces.surface_list):
                    va = vlist[face.vertex_list[0] - 1]
                    vb = vlist[face.vertex_list[1] - 1]
                    vc = vlist[face.vertex_list[2] - 1]
                    if va.clipped or vb.clipped or vc.clipped:
                        continue

                    n = transformed_normals[face_idx]
                    cx = (va.x_view + vb.x_view + vc.x_view) / 3.0
                    cy = (va.y_view + vb.y_view + vc.y_view) / 3.0
                    cz = (va.z_view + vb.z_view + vc.z_view) / 3.0
                    facing = -(n[0] * cx + n[1] * cy + n[2] * cz)
                    if facing <= 0:
                        continue

                    if solid:
                        # Facing ratio 0..1: a "headlight" at the camera, until
                        # a real light source lands (roadmap rev 0.9)
                        facing /= math.sqrt(cx * cx + cy * cy + cz * cz)
                        shade = int(40 + 180 * min(facing, 1.0))
                    else:
                        shade = int(190 * (cz - z_lo) / z_span)  # edge depth cue
                    render_list.append((cz, shade,
                                        (va.x_screen, va.y_screen),
                                        (vb.x_screen, vb.y_screen),
                                        (vc.x_screen, vc.y_screen)))

                render_list.sort(key=lambda t: -t[0])  # far first
                if solid:
                    for depth, shade, p1, p2, p3 in render_list:
                        pygame.draw.polygon(screen, (shade, shade, shade), (p1, p2, p3), 0)
                else:
                    # Hidden-line: fill with background to erase edges behind,
                    # then outline with the depth-cued colour
                    for depth, shade, p1, p2, p3 in render_list:
                        pts = (p1, p2, p3)
                        pygame.draw.polygon(screen, COLOR_WHITE, pts, 0)
                        pygame.draw.polygon(screen, (shade, shade, shade), pts, 1)

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
    print('... done')

    print('starting render mode ...')
    start()
