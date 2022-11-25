# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Simple Wireframe Viewing System

import pygame
import loader 
import matrix 
import sys
import math

def start(vertices,faces):

    pygame.init()

    size = width, height = 1024, 800

    center_x = width / 2
    center_y = height / 2
    center_z = 0
    center_shift = 10

    x_scalar = -100
    y_scalar = -100
    z_scalar = -100
    scale_shift = 1.1

    x_rotation = 0.0
    y_rotation = 0.0
    z_rotation = 0.0
    rotation_shift = 1.0

    x_translation = 0.0
    y_translation = 0.0
    z_translation = 0.0
    translation_shift = 1.0

    black = 0, 0, 0
    white = 255,255,255

    screen = pygame.display.set_mode(size)
    screen.fill(white)

    rotation = False

    while 1:

        if rotation:
            y_rotation += math.radians(25)
            x_rotation +=math.radians(25)
            z_rotation +=math.radians(25)
            screen.fill(white)

        for event in pygame.event.get():

            if event.type == pygame.QUIT: 
                sys.exit()
                        
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_c:
                    center_x = width / 2
                    center_y = height / 2
                    center_z = 100
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
                    z_rotation -= rotation_shift
                    
                if event.key == pygame.K_x:
                    z_rotation += rotation_shift
                    
                if event.key == pygame.K_a:
                    y_rotation -= rotation_shift
                    
                if event.key == pygame.K_s:
                    y_rotation += rotation_shift
                    
                if event.key == pygame.K_q:
                    x_rotation -= rotation_shift

                if event.key == pygame.K_w:
                    x_rotation += rotation_shift

                if event.key == pygame.K_UP:
                    center_y -= center_shift
                
                if event.key == pygame.K_DOWN:
                    center_y += center_shift

                if event.key == pygame.K_LEFT:
                    center_x -= center_shift

                if event.key == pygame.K_RIGHT:
                    center_x += center_shift

                if event.key == pygame.K_SPACE:
                    if rotation:
                        rotation = False
                    else:
                        rotation = True

                screen.fill(white)
                    
        # Calc linear transforms for scaling, rotation and TODO: translation
        MS = matrix.ScaleMatrix(x_scalar,y_scalar,z_scalar)
        MR = matrix.RotateMatrix(x_rotation,y_rotation,z_rotation)        
        MT = matrix.TranslateMatrix(x_translation,y_translation,z_translation)
        # Combine all three matrices into one
        M = matrix.MatrixMult(matrix.MatrixMult(MS,MR),MT)

        face_count = 0
        for face in surfaces.surface_list:
            face_count +=1
            # TODO: wrap in method of surface class
            
            # Get index to each vertex in the surface ( 3 in this case as polgon is a triangle )
            vertex_index_1 = face.vertex_list[0] -1
            vertex_index_2 = face.vertex_list[1] -1
            vertex_index_3 = face.vertex_list[2] -1

            # # Using the index to the vertex calc the x,y,z view coordinate, from world coord
            vertices.vertex_list[vertex_index_1].calc_transform(M)
            vertices.vertex_list[vertex_index_2].calc_transform(M)
            vertices.vertex_list[vertex_index_3].calc_transform(M)

            x1v = vertices.vertex_list[vertex_index_1].tx
            y1v = vertices.vertex_list[vertex_index_1].ty
            z1v = vertices.vertex_list[vertex_index_1].tz

            x2v = vertices.vertex_list[vertex_index_2].tx
            y2v = vertices.vertex_list[vertex_index_2].ty
            z2v = vertices.vertex_list[vertex_index_2].tz

            x3v = vertices.vertex_list[vertex_index_3].tx
            y3v = vertices.vertex_list[vertex_index_3].ty
            z3v = vertices.vertex_list[vertex_index_3].tz

            x1w = vertices.vertex_list[vertex_index_1].wx
            y1w = vertices.vertex_list[vertex_index_1].wy
            z1w = vertices.vertex_list[vertex_index_1].wz

            x2w = vertices.vertex_list[vertex_index_2].wx
            y2w = vertices.vertex_list[vertex_index_2].wy
            z2w = vertices.vertex_list[vertex_index_2].wz

            x3w = vertices.vertex_list[vertex_index_3].wx
            y3w = vertices.vertex_list[vertex_index_3].wy
            z3w = vertices.vertex_list[vertex_index_3].wz

            v1v = [x1v,y1v,z1v]
            v2v = [x2v,y2v,z2v]
            v3v = [x3v,y3v,z3v]

            v1w = [x1w,y1w,z1w]
            v2w = [x2w,y2w,z2w]
            v3w = [x3w,y3w,z3w]

            # Calculate surface normals 
            # Using two collinear vertices, calculate normal between the two vectors
            # Needed for deciding whether to cull the rendering of the surface

            normal = matrix.CalcSurfaceNormal(v1v,v2v,v3v)
            success = (abs(normal[0]) + abs(normal[1]) + abs(normal[2]) > 0.00000001)
            
            if not success:
                print ('face:',face_count)
                print ('w1',v1w)
                print ('w2',v2w)
                print ('w3',v3w)
                print ('v1',v1v)
                print ('v2',v2v)
                print ('v3',v3v)
                print ('normal',face.normal,success)

            face.normal = matrix.NormaliseVector(normal)

            # view plane transformation (basic TODO: add wiew point and proper perspective view plane transform )
            # i.e. convert 3 dimensional coordinate onto 2 dimensional view plane ( impl parralel and perspective )
            p = [(x1v+center_x,y1v+center_y),(x2v+center_x,y2v+center_y),(x3v+center_x,y3v+center_y)]

            pygame.draw.polygon(screen,black,p,1)

        for vertex in vertices.vertex_list:
            matrix.CalcVertexNormal(vertex)

        pygame.display.flip()

if __name__ == '__main__':
    print("loading vertices from database ...")
    vertices = loader.load_vertices_db()

    print("loading surfaces from database ...")
    surfaces = loader.load_surfaces_db()

    print('rendering ...')
    start(vertices,surfaces)


