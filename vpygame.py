import sys
import pygame
import loader 
import matrix 


def start(vertices,faces):

    pygame.init()

    size = width, height = 1024, 800

    center_x = width / 2
    center_y = height / 2
    center_z = 0
    center_shift = 10

    scalar_x = -100
    scalar_y = -100
    scalar_z = -100
    scale_shift = 1.1

    x_rotation = 0
    y_rotation = 0
    z_rotation = 0
    rotation_shift = 10
   
    black = 0, 0, 0
    white = 255,255,255

    screen = pygame.display.set_mode(size)
    screen.fill(white)

    I = matrix.IdentityMatrix()

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
                        
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_c:
                    center_x = width / 2
                    center_y = height / 4
                    center_z = 100
                    x_rotation = 0
                    y_rotation = 0
                    z_rotation = 0
                    screen.fill(white)


                if event.key == pygame.K_MINUS:
                    scalar_x = scalar_x / scale_shift
                    scalar_y = scalar_y / scale_shift
                    scalar_z = scalar_z / scale_shift

                    screen.fill(white)

                if event.key == pygame.K_EQUALS:

                    scalar_x = scalar_x * scale_shift
                    scalar_y = scalar_y * scale_shift
                    scalar_z = scalar_z * scale_shift
                    
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
        
        # todo : translate
        I = matrix.MatrixMult(matrix.RotateMatrix(x_rotation,y_rotation,z_rotation), matrix.ScaleMatrix(scalar_x,scalar_y,scalar_z))
        
        print(center_x,center_y,center_z)
        matrix.PrintMatrix(I)

        for face in surfaces.surface_list:
            
            vertex_index_1 = int(face[0])
            vertex_index_2 = int(face[1])
            vertex_index_3 = int(face[2])

            x1w = float(vertices.vertex_list[vertex_index_1-1].x) 
            y1w = float(vertices.vertex_list[vertex_index_1-1].y)  
            z1w = float(vertices.vertex_list[vertex_index_1-1].z) 

            x2w = float(vertices.vertex_list[vertex_index_2-1].x) 
            y2w = float(vertices.vertex_list[vertex_index_2-1].y) 
            z2w = float(vertices.vertex_list[vertex_index_2-1].z) 

            x3w = float(vertices.vertex_list[vertex_index_3-1].x) 
            y3w = float(vertices.vertex_list[vertex_index_3-1].y) 
            z3w = float(vertices.vertex_list[vertex_index_3-1].z)   

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
    vertices = loader.load_vertices()
    surfaces = loader.load_surfaces()
    start(vertices,surfaces)
else :
    print(__name__)