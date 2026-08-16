# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Simple Wireframe Viewing System using pygame for 2Dgraphical drawing system

import pygame
import time
import loader 
import matrix 
import sys
import math
import surface
import vertex as v

INPUT_DATA_SOURCE = 'file' # 'db' or 'file'
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 800

vertices = v.vertices()
surfaces = surface.surface()
svmap = []

def CalcVectorNormals():

    # Calc vertex normals from surface normals
    print('calculating vertex normals from surface normals ...')
    for v in vertices.vertex_list:
        totalvec_x = 0
        totalvec_y = 0
        totalvec_z = 0
        sc = 0
        for s in surfaces.surface_list:
            if v.index in s.vertex_list:
                totalvec_x = totalvec_x + s.normal[0]
                totalvec_y = totalvec_y + s.normal[1]
                totalvec_z = totalvec_z + s.normal[2]
                sc += 1
        if sc > 0:
            v.normal = matrix.NormaliseVector([totalvec_x/sc, totalvec_y/sc, totalvec_z/sc])
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

def Toggle(flag):
    if flag:
        return False
    elif not flag:
        return True
    else:
        return True

def start():

    x_scalar = 100
    y_scalar = 100
    z_scalar = 100

    x_rotation = 0.0
    y_rotation = 0.0
    z_rotation = 0.0

    x_translation = SCREEN_WIDTH/2
    y_translation = SCREEN_HEIGHT/2
    z_translation = 0

    scale_shift = 1.1
    rotation_shift = 1.0
    translation_shift = 15.0

    black = 0, 0, 0
    white = 255,255,255
    red = 255,100,100
    blue = 0,0,255
    green = 0,255,0
    magenta = 255,0,255

    x_rotate = False
    y_rotate = False
    z_rotate = False

    pygame.init()

    size = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode(size)
    screen.fill(white)

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    fps_update_timer = 0
    fps_text = font.render('FPS: 0.0', True, black)

    drawnormals = False
    normals_calculated = False
    drawfaces = True
    drawaxes = True
    backface_cull = False

    while 1:

        if x_rotate:
            x_rotation -=math.radians(25)

        if y_rotate:
            y_rotation += math.radians(25)

        if z_rotate:
            z_rotation +=math.radians(25)

        screen.fill(white)

        for event in pygame.event.get():

            if event.type == pygame.QUIT: 

                sys.exit()
                        
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_q:

                    sys.exit()

                if event.key == pygame.K_c:

                    x_scalar = 100
                    y_scalar = 100
                    z_scalar = 100

                    x_rotation = 180.0
                    y_rotation = 180.0
                    z_rotation = 0.0

                    x_translation = SCREEN_WIDTH/2
                    y_translation = SCREEN_HEIGHT/2
                    z_translation = 0

                if event.key == pygame.K_MINUS:

                    x_scalar = x_scalar / scale_shift
                    y_scalar = y_scalar / scale_shift
                    z_scalar = z_scalar / scale_shift

                if event.key == pygame.K_EQUALS:

                    x_scalar = x_scalar * scale_shift
                    y_scalar = y_scalar * scale_shift
                    z_scalar = z_scalar * scale_shift
                    
                if event.key == pygame.K_a:

                    drawaxes = Toggle(drawaxes)

                if event.key == pygame.K_x:

                    x_rotate = Toggle(x_rotate)

                if event.key == pygame.K_y:

                    y_rotate = Toggle(y_rotate)

                if event.key == pygame.K_z:

                    z_rotate = Toggle(z_rotate)
                    
                if event.key == pygame.K_UP:

                    y_translation -= translation_shift
                
                if event.key == pygame.K_DOWN:

                    y_translation += translation_shift

                if event.key == pygame.K_LEFT:

                    x_translation -= translation_shift

                if event.key == pygame.K_RIGHT:

                    x_translation += translation_shift

                if event.key == pygame.K_n or event.key == pygame.K_v:

                    if drawnormals:
                        drawnormals = False
                        print('vertex normals off ...')
                    else:
                        drawnormals = True
                        print('vertex normals on ...')
                        if not normals_calculated:
                            CalcVectorNormals()
                            normals_calculated = True

                if event.key == pygame.K_f:

                    if drawfaces:
                        drawfaces = False
                        print('draw faces off ...')
                    else:
                        drawfaces = True
                        print('draw faces on ...')

                if event.key == pygame.K_b:

                    if backface_cull:
                        backface_cull = False
                        print('backface culling off ...')
                    else:
                        backface_cull = True
                        print('backface culling on ...')

                screen.fill(white)

        # Calc linear transforms for scaling, rotation and TODO: translation
        MS = matrix.ScaleMatrix(x_scalar,y_scalar,z_scalar)
        MR = matrix.RotateMatrix(x_rotation,y_rotation,z_rotation)
        MT = matrix.TranslateMatrix(x_translation,y_translation,z_translation)
        # Combine all three matrices into one
        M = matrix.MatrixMult(matrix.MatrixMult(MS,MR),MT)

        MO = matrix.OrthographicMatrix()
        MP = matrix.PerspectiveMatrix()

        # Perform linear transforms on all vertices in one go to calc view coords from world coords
        for vertex in vertices.vertex_list:
            vertex.calc_view_coordinates(M)
            vertex.calc_screen_coordinates(MP)

        if drawfaces:

            for face in surfaces.surface_list:

                # Get index to each vertex in the surface ( 3 in this case as polgon is a triangle )
                vertex_index_1 = face.vertex_list[0] - 1
                vertex_index_2 = face.vertex_list[1] - 1
                vertex_index_3 = face.vertex_list[2] - 1

                # Surface normals are pre-computed at load time and cached in face.normal
                # (no per-frame recalculation needed)

                # Backface culling (optional, can be toggled with 'b' key)
                # Note: Simple face-normal-based culling works for convex meshes but may miss
                # surfaces on complex geometry like the teapot handle/spout
                if backface_cull:
                    normal_view = matrix.MatrixVector(MR, face.normal)
                    if normal_view[2] < 0:
                        continue

                # view plane transformation (basic TODO: add wiew point and proper perspective view plane transform )
                # i.e. convert 3 dimensional coordinate onto 2 dimensional view plane ( impl parralel and perspective )
                p = [(vertices.vertex_list[vertex_index_1].x_screen,
                    vertices.vertex_list[vertex_index_1].y_screen),
                    (vertices.vertex_list[vertex_index_2].x_screen,
                    vertices.vertex_list[vertex_index_2].y_screen),
                    (vertices.vertex_list[vertex_index_3].x_screen,
                    vertices.vertex_list[vertex_index_3].y_screen)]
                pygame.draw.polygon(screen,black,p,1)

        if drawnormals:

            for vertex in vertices.vertex_list:

                x1 = vertex.x_screen
                y1 = vertex.y_screen
                x2 = vertex.x_screen - vertex.normal[0] * 10
                y2 = vertex.y_screen - vertex.normal[1] * 10

                pygame.draw.line(screen,red,[x1,y1],[x2,y2],1)

        if drawaxes:

            pygame.draw.line(screen,green,[0+x_translation,0+y_translation],[200+x_translation,0+y_translation],3) # type: ignore
            pygame.draw.line(screen,blue,[0+x_translation,0+y_translation],[0+x_translation,200+y_translation],3) # type: ignore
            pygame.draw.line(screen,magenta,[0+x_translation,0+y_translation],[175+x_translation,175+y_translation],3) # type: ignore

        fps_update_timer += 1
        if fps_update_timer >= 10:
            current_fps = clock.get_fps()
            fps_text = font.render(f'FPS: {current_fps:.1f}', True, black)
            fps_update_timer = 0

        screen.blit(fps_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)
        screen.fill(white)

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


