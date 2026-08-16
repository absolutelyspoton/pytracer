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
        '+/- - Zoom in/out',
        'x/y/z - Spin on X/Y/Z axis',
        'a - Toggle axis legend',
        'n/v - Toggle vertex normals',
        'f - Toggle wireframe faces',
        'b - Toggle backface culling',
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

        # Compute transformations
        MS = matrix.ScaleMatrix(*state.scale)
        MR = matrix.RotateMatrix(*state.rotation)
        MT = matrix.TranslateMatrix(*state.translation)
        M = matrix.MatrixMult(matrix.MatrixMult(MS, MR), MT)

        MP = matrix.PerspectiveMatrix()

        # Transform vertices
        for vertex in vertices.vertex_list:
            vertex.calc_view_coordinates(M)
            vertex.calc_screen_coordinates(MP)

        # Draw faces
        if state.draw_faces:
            for face in surfaces.surface_list:
                v1_idx = face.vertex_list[0] - 1
                v2_idx = face.vertex_list[1] - 1
                v3_idx = face.vertex_list[2] - 1

                # Backface culling (optional)
                if state.backface_cull:
                    normal_view = matrix.MatrixVector(MR, face.normal)
                    if normal_view[2] < 0:
                        continue

                # Draw triangle
                p = [
                    (vertices.vertex_list[v1_idx].x_screen, vertices.vertex_list[v1_idx].y_screen),
                    (vertices.vertex_list[v2_idx].x_screen, vertices.vertex_list[v2_idx].y_screen),
                    (vertices.vertex_list[v3_idx].x_screen, vertices.vertex_list[v3_idx].y_screen)
                ]
                pygame.draw.polygon(screen, COLOR_BLACK, p, 1)

        # Draw vertex normals
        if state.draw_normals:
            for vertex in vertices.vertex_list:
                x1, y1 = vertex.x_screen, vertex.y_screen
                x2 = x1 - vertex.normal[0] * 10
                y2 = y1 - vertex.normal[1] * 10
                pygame.draw.line(screen, COLOR_RED, [x1, y1], [x2, y2], 1)

        # Draw axis legend
        if state.draw_axes:
            tx, ty = state.translation[0], state.translation[1]
            pygame.draw.line(screen, COLOR_GREEN, [tx, ty], [tx + 200, ty], 3)
            pygame.draw.line(screen, COLOR_BLUE, [tx, ty], [tx, ty + 200], 3)
            pygame.draw.line(screen, COLOR_MAGENTA, [tx, ty], [tx + 175, ty + 175], 3)

        # Draw FPS counter and geometry stats
        fps_update_timer += 1
        if fps_update_timer >= 10:
            current_fps = clock.get_fps()

            # Count displayed geometry
            displayed_vertices = vertices.vertex_count() if state.draw_faces else 0
            displayed_faces = 0
            displayed_edges = 0

            if state.draw_faces:
                for face in surfaces.surface_list:
                    # Apply backface culling logic
                    if state.backface_cull:
                        normal_view = matrix.MatrixVector(MR, face.normal)
                        if normal_view[2] < 0:
                            continue
                    displayed_faces += 1
                    displayed_edges += 3  # Each triangle has 3 edges

            displayed_normals = 0
            if state.draw_normals:
                displayed_normals = vertices.vertex_count()  # Only vertex normals are drawn
            if state.draw_faces:
                displayed_normals += displayed_faces  # Add face normals

            status_line = (
                f'{current_fps:.0f} FPS  '
                f'Vertices:{displayed_vertices}  Edges:{displayed_edges}  Faces:{displayed_faces}  Normals:{displayed_normals}'
            )

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
        clock.tick(60)


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
