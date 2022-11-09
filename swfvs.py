# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Simple Wireframe Viewing System

import pygame
import loader 
import matrix 
import sys
from devtools import debug

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

    x_rotation = 0
    y_rotation = 0
    z_rotation = 0
    rotation_shift = 1
   
    black = 0, 0, 0
    white = 255,255,255

    screen = pygame.display.set_mode(size)
    screen.fill(white)

    rotation = False

    while 1:

        if rotation:
            y_rotation +=1
            x_rotation +=1
            z_rotation +=1
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
                    screen.fill(white)

                if event.key == pygame.K_MINUS:
                    x_scalar = x_scalar / scale_shift
                    y_scalar = y_scalar / scale_shift
                    z_scalar = z_scalar / scale_shift

                    screen.fill(white)

                if event.key == pygame.K_EQUALS:

                    x_scalar = x_scalar * scale_shift
                    y_scalar = y_scalar * scale_shift
                    z_scalar = z_scalar * scale_shift
                    
                    screen.fill(white)

                if event.key == pygame.K_z:
                    z_rotation -= rotation_shift
                    screen.fill(white)

                if event.key == pygame.K_x:
                    z_rotation += rotation_shift
                    screen.fill(white)

                if event.key == pygame.K_a:
                    y_rotation -= rotation_shift
                    screen.fill(white)

                if event.key == pygame.K_s:
                    y_rotation += rotation_shift
                    screen.fill(white)    

                if event.key == pygame.K_q:
                    x_rotation -= rotation_shift
                    screen.fill(white)

                if event.key == pygame.K_w:
                    x_rotation += rotation_shift
                    screen.fill(white)

                if event.key == pygame.K_UP:
                    center_y -= center_shift
                    screen.fill(white)  
                
                if event.key == pygame.K_DOWN:
                    center_y += center_shift
                    screen.fill(white)  

                if event.key == pygame.K_LEFT:
                    center_x -= center_shift
                    screen.fill(white)  

                if event.key == pygame.K_RIGHT:
                    center_x += center_shift
                    screen.fill(white)  

                if event.key == pygame.K_SPACE:
                    if rotation:
                        rotation = False
                    else:
                        rotation = True

                    
        # todo : add the translate
        I = matrix.MatrixMult(matrix.RotateMatrix(x_rotation,y_rotation,z_rotation), matrix.ScaleMatrix(x_scalar,y_scalar,z_scalar))
        
        for surface in surfaces.surface_list:
            
            # Get index to each vertex in the surface ( 3 in this case as polgon is a triangle )
            vertex_index_1 = int(surface.vertex_list[0])
            vertex_index_2 = int(surface.vertex_list[1])
            vertex_index_3 = int(surface.vertex_list[2])

            # Using the index to the vertex extract the x,y,z world coordinate 
            # one
            x1w = float(vertices.vertex_list[vertex_index_1-1].x) 
            y1w = float(vertices.vertex_list[vertex_index_1-1].y)  
            z1w = float(vertices.vertex_list[vertex_index_1-1].z) 
            v1w = [x1w,y1w,z1w]

            # two
            x2w = float(vertices.vertex_list[vertex_index_2-1].x) 
            y2w = float(vertices.vertex_list[vertex_index_2-1].y) 
            z2w = float(vertices.vertex_list[vertex_index_2-1].z) 
            v2w = [x2w,y2w,z2w]

            # three
            x3w = float(vertices.vertex_list[vertex_index_3-1].x) 
            y3w = float(vertices.vertex_list[vertex_index_3-1].y) 
            z3w = float(vertices.vertex_list[vertex_index_3-1].z)
            v3w = [x3w,y3w,z3w]

            # Calculate surface normals ( call method of surface class )
            # Using two collinear vertices, calculate normal between the two vectors
            # Needed for deciding whether to cull the rendering of the surface
            surface.calcNormal(v1w,v2w,v3w)

            t = matrix.MatrixVector(I,[x1w,y1w,z1w])
            x1w = t[0] 
            y1w = t[1] 
            z1w = t[2] 

            t = matrix.MatrixVector(I,[x2w,y2w,z2w])
            x2w = t[0] 
            y2w = t[1] 
            z2w = t[2] 

            t = matrix.MatrixVector(I,[x3w,y3w,z3w])
            x3w = t[0] 
            y3w = t[1]
            z3w = t[2] 

            # view plane transformation
            p = [(x1w+center_x,y1w+center_y),(x2w+center_x,y2w+center_y),(x3w+center_x,y3w+center_y)]

            pygame.draw.polygon(screen,black,p,1)

        pygame.display.flip()

if __name__ == '__main__':
    print("loading vertices from database ...")
    vertices = loader.load_vertices_db()
    print("loading surfaces from database ...")
    surfaces = loader.load_surfaces_db()
    print('rendering ...')
    start(vertices,surfaces)


