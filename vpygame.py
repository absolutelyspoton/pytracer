import sys
import pygame
import csv
import math

def start(vertices,faces):

    pygame.init()

    size = width, height = 1024, 800
    center_x = width / 2
    center_y = height / 4
    center_z = 500
    scalar_x = 1
    scalar_y = 1
    scalar_z = 1

    shift = 5
    rotation_shift = math.radians(2)
   
    black = 0, 0, 0
    white = 255,255,255

    x_rotation = 0
    y_rotation = 0
    z_rotation = 0

    z_depth = 4

    screen = pygame.display.set_mode(size)
    screen.fill(white)

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
                        
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_c:
                    center_x = width / 2
                    center_y = height / 4
                    center_z = 500
                    scalar_x = 1
                    scalar_y = 1
                    scalar_z = 1
                    x_rotation, y_rotation, z_rotation = 0,0,0
                    screen.fill(white)


                if event.key == pygame.K_MINUS:
                    scalar_x -= shift
                    scalar_y -= shift
                    screen.fill(white)

                if event.key == pygame.K_EQUALS:
                    scalar_x += shift
                    scalar_y += shift
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

                if event.key == pygame.K_e:
                    z_depth -= 1
                    screen.fill(white)  

                if event.key == pygame.K_r:
                    z_depth += 1
                    screen.fill(white)  

                if event.key == pygame.K_UP:
                    center_y += 30
                    screen.fill(white)  
                
                if event.key == pygame.K_DOWN:
                    center_y -= 30
                    screen.fill(white)  

                if event.key == pygame.K_LEFT:
                    center_x -= 30
                    screen.fill(white)  
                
                if event.key == pygame.K_RIGHT:
                    center_x += 30
                    screen.fill(white)  

        # for v in vertices:
        #     x,y,z = float(v[0]),float(v[1]),float(v[2])
        #     l = (center_x+x*scalar,center_y+y*scalar)
        #     pygame.draw.line(screen,black,l,l,1)

        for f in faces:
            v1,v2,v3 = int(f[0]),int(f[1]),int(f[2])

            x1v = float(vertices[v1-1][0]) * scalar_x + center_x
            x2v = float(vertices[v2-1][0]) * scalar_x + center_x
            x3v = float(vertices[v3-1][0]) * scalar_x + center_x
            y1v = float(vertices[v1-1][1]) * scalar_y + center_y
            y2v = float(vertices[v2-1][1]) * scalar_y + center_y
            y3v = float(vertices[v3-1][1]) * scalar_y + center_y
            z1v = float(vertices[v1-1][2]) * scalar_z + center_z
            z2v = float(vertices[v2-1][2]) * scalar_z + center_z
            z3v = float(vertices[v3-1][2]) * scalar_z + center_z

            # ratation through x-axis
            y1v = y1v * math.cos(x_rotation) - z1v * math.sin(x_rotation)
            z1v = y1v * math.sin(x_rotation) + z1v * math.cos(x_rotation)
            y2v = y2v * math.cos(x_rotation) - z2v * math.sin(x_rotation)
            z2v = y2v * math.sin(x_rotation) + z3v * math.cos(x_rotation)
            y3v = y3v * math.cos(x_rotation) - z3v * math.sin(x_rotation)
            z3v = y3v * math.sin(x_rotation) + z3v * math.cos(x_rotation)            

            # ratation through y-axis
            x1v = x1v * math.cos(y_rotation) + z1v * math.sin(y_rotation)
            z1v = z1v * math.cos(y_rotation) - x1v * math.sin(y_rotation)
            x2v = x2v * math.cos(y_rotation) + z2v * math.sin(y_rotation)
            z2v = z2v * math.cos(y_rotation) - x2v * math.sin(y_rotation)
            x3v = x3v * math.cos(y_rotation) + z3v * math.sin(y_rotation)
            z3v = z3v * math.cos(y_rotation) - x3v * math.sin(y_rotation)

            # ratation through z-axis
            x1v = x1v * math.cos(z_rotation) - y1v * math.sin(z_rotation)
            y1v = x1v * math.sin(z_rotation) + y1v * math.cos(z_rotation)
            x2v = x2v * math.cos(z_rotation) - y2v * math.sin(z_rotation)
            y2v = x2v * math.sin(z_rotation) + y2v * math.cos(z_rotation)
            x3v = x3v * math.cos(z_rotation) - y3v * math.sin(z_rotation)
            y3v = x3v * math.sin(z_rotation) + y3v * math.cos(z_rotation)

            # view plane transformation
            if z1v != 0:
                x1s = x1v / (z1v/z_depth)
                y1s = y1v / (z1v/z_depth)
            else:
                x1s = x1v
                y1s = y1v
                
            if z2v != 0:
                x2s = x2v / (z2v/z_depth)
                y2s = y2v / (z2v/z_depth)
            else:
                x2s = x2v
                y2s = x2v

            if z3v != 0:
                x3s = x3v / (z3v/z_depth)
                y3s = y3v / (z3v/z_depth)
            else:
                x3s = x3v
                y3s = y3v

            p = [(x1v,y1v),(x2v,y2v),(x3v,y3v)]
            #p = [(x1s,y1s),(x2s,y2s),(x3s,y3s)]

            pygame.draw.polygon(screen,black,p,1)


        pygame.display.flip()

def load_data(fn):
    data = []
    with open(fn) as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=',')
        for row in csv_reader:
            data.append(row)
    return(data[1:])

if __name__ == '__main__':
    vertices = load_data('utah_teapot_vertices.csv')
    faces = load_data('utah_teapot_faces.csv')
    start(vertices,faces)

else :
    print(__name__)