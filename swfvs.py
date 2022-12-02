# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Simple Wireframe Viewing System using pygame for 2Dgraphical drawing system

import pygame
import loader 
import matrix 
import sys
import math
import surface
import vertex

INPUT_DATA_SOURCE = 'file' # 'db' or 'file'
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 800

vertices = vertex.vertices()
surfaces = surface.surface()
svmap = []

def CalcVectorNormals():

    # Calc vertex normals from surface normals
    print('calculating vertex normals from surface normals ...')
    for v in vertices.vertex_list:
        totalvec_x = 0
        totalvec_y = 0
        totalvec_z = 0
        totalvec = [totalvec_x,totalvec_y,totalvec_z]
        sc = 1
        for s in surfaces.surface_list:
            if v.index in s.vertex_list:
                totalvec_x = totalvec_x + s.normal[0]
                totalvec_y = totalvec_y + s.normal[1]
                totalvec_z = totalvec_z + s.normal[2]
                totalvec = [totalvec_x,totalvec_y,totalvec_z]
                sc+=1
        v.normal = matrix.NormaliseVector(totalvec)
    print('... done')

def CalcTransforms(x_scalar,y_scalar,z_scalar,x_rotation,y_rotation,z_rotation,x_translation,y_translation,z_translation):
   
    # Calc linear transforms for scaling, rotation and TODO: translation
    MS = matrix.ScaleMatrix(x_scalar,y_scalar,z_scalar)
    MR = matrix.RotateMatrix(x_rotation,y_rotation,z_rotation)        
    MT = matrix.TranslateMatrix(x_translation,y_translation,z_translation)
    # Combine all three matrices into one
    M = matrix.MatrixMult(matrix.MatrixMult(MS,MR),MT)
    MO = matrix.OrthographicMatrix()
    MP = matrix.PerspectiveMatrix()

    # Perform linear transforms on all vertices in one go to calc view coords from world coords
    for v in vertices.vertex_list:
        v.calc_view_coordinates(M)
        v.calc_screen_coordinates(MP)

def start():

    x_scalar = 100
    y_scalar = 100
    z_scalar = 100

    x_rotation = 180.0
    y_rotation = 180.0
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

    pygame.init()

    size = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode(size)
    screen.fill(white)

    rotation = False
    drawnormals = False
    normals_calculated = False
    drawfaces = True

    while 1:

        CalcTransforms(x_scalar,y_scalar,z_scalar,x_rotation,y_rotation,z_rotation,x_translation,y_translation,z_translation)

        if rotation:
            x_rotation +=math.radians(25)
            y_rotation += math.radians(25)
            z_rotation +=math.radians(25)
            screen.fill(white)

        for event in pygame.event.get():

            if event.type == pygame.QUIT: 

                sys.exit()
                        
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_c:

                    x_rotation = 0
                    y_rotation = 0
                    z_rotation = 0

                if event.key == pygame.K_MINUS:

                    x_scalar = x_scalar / scale_shift
                    y_scalar = y_scalar / scale_shift
                    z_scalar = z_scalar / scale_shift

                if event.key == pygame.K_EQUALS:

                    x_scalar = x_scalar * scale_shift
                    y_scalar = y_scalar * scale_shift
                    z_scalar = z_scalar * scale_shift
                    
                if event.key == pygame.K_z:

                    z_rotation += rotation_shift
                    
                if event.key == pygame.K_x:

                    z_rotation -= rotation_shift
                    
                if event.key == pygame.K_a:

                    y_rotation -= rotation_shift
                    
                if event.key == pygame.K_s:

                    y_rotation += rotation_shift
                    
                if event.key == pygame.K_q:

                    x_rotation -= rotation_shift

                if event.key == pygame.K_w:

                    x_rotation += rotation_shift

                if event.key == pygame.K_UP:

                    y_translation -= translation_shift
                
                if event.key == pygame.K_DOWN:

                    y_translation += translation_shift

                if event.key == pygame.K_LEFT:

                    x_translation -= translation_shift

                if event.key == pygame.K_RIGHT:

                    x_translation += translation_shift

                if event.key == pygame.K_n:

                    if drawnormals:
                        drawnormals = False
                        print('draw normals off ...')
                    else:
                        drawnormals = True
                        print('draw normals on ...')
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


                if event.key == pygame.K_SPACE:

                    if rotation:
                        rotation = False
                        print('rotation off ...')
                    else:
                        rotation = True
                        print('rotation on ...')
                
                screen.fill(white)

        if drawfaces:

            for face in surfaces.surface_list:
                
                # Get index to each vertex in the surface ( 3 in this case as polgon is a triangle )
                vertex_index_1 = face.vertex_list[0] - 1
                vertex_index_2 = face.vertex_list[1] - 1
                vertex_index_3 = face.vertex_list[2] - 1

                # Calculate surface normals 
                # Using two collinear vertices, calculate normal between the two vectors
                # Needed for deciding whether to cull the rendering of the surface
                normal = matrix.CalcSurfaceNormal(
                        [vertices.vertex_list[vertex_index_1].x_world,
                        vertices.vertex_list[vertex_index_1].y_world,
                        vertices.vertex_list[vertex_index_1].z_world],
                        [vertices.vertex_list[vertex_index_2].x_world,
                        vertices.vertex_list[vertex_index_2].y_world,
                        vertices.vertex_list[vertex_index_2].z_world],
                        [vertices.vertex_list[vertex_index_3].x_world,
                        vertices.vertex_list[vertex_index_3].y_world,
                        vertices.vertex_list[vertex_index_3].z_world])
                
                # TODO: iterate around the vertices of the surface until success (page 382)
                success = (abs(normal[0]) + abs(normal[1]) + abs(normal[2]) > 0.0001)
                face.normal = matrix.NormaliseVector(normal)

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

        pygame.display.flip()

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

    print('starting render mode ...')
    start()


