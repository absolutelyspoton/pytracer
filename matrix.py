# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Matrix Maths Module

import math

VECTOR_SIZE = 4 # 4x4 Matrices

# Return zero matrix
# [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
def ZeroMatrix():
    arr = [[0 for i in range(VECTOR_SIZE)] for j in range(VECTOR_SIZE) ]
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            arr[i][j] = 0
    return arr  

# Return identity matrix
# [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
def IdentityMatrix():
    arr = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            if i == j:
                arr[i][j] = 1
    return arr

#M Matrix multiplication of two matrices
def MatrixMult(m1,m2):
    mz = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            for e in range(VECTOR_SIZE):
                mz[i][j] = mz[i][j] + m1[i][e]*m2[e][j]
    return(mz)

def MatrixVector(m,v):
    x = m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2] + m[0][3]
    y = m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2] + m[1][3]
    z = m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2] + m[2][3]
    return ([x,y,z])

# Matrix maths to rotate through x,y,z axis
def RotateMatrix(x_theta,y_theta,z_theta):

    x_rad = math.radians(x_theta)
    y_rad = math.radians(y_theta)
    z_rad = math.radians(z_theta)

    # Rotation through z-axis
    arr_z = IdentityMatrix()
    arr_z[0][0] = math.cos(z_rad)
    arr_z[1][0] = math.sin(z_rad) * -1
    arr_z[0][1] = math.sin(z_rad)
    arr_z[1][1] = math.cos(z_rad)

    # Rotation through y-axis
    arr_y = IdentityMatrix()
    arr_y[0][0] = math.cos(y_rad)
    arr_y[2][0] = math.sin(y_rad) 
    arr_y[0][2] = math.sin(y_rad) * -1
    arr_y[2][2] = math.cos(y_rad)

    # Rotation through x-axis
    arr_x = IdentityMatrix()
    arr_x[1][1] = math.cos(x_rad)
    arr_x[2][1] = math.sin(x_rad) * -1
    arr_x[1][2] = math.sin(x_rad) 
    arr_x[2][2] = math.cos(x_rad)

    m = MatrixMult(arr_x,arr_y)
    m = MatrixMult(m,arr_z)

    return(m)

def ScaleMatrix(x,y,z):
    m = IdentityMatrix()
    m[0][0] = x
    m[1][1] = y
    m[2][2] = z
    return(m)

def TranslateMatrix(x,y,z):
    m = IdentityMatrix()
    m[3][0] = x
    m[3][1] = y
    m[3][2] = z
    return(m)

def PrintMatrix(m):
    for n in m:
        print(n)


if (__name__ == '__main__'):
    
    I = IdentityMatrix()
    PrintMatrix(I)
    
    Z = ZeroMatrix()
    PrintMatrix(Z)
    
    PrintMatrix(MatrixMult(I,Z))

    print(MatrixVector(Z,[1,2,3]))

    PrintMatrix(RotateMatrix(45,30,150))

    PrintMatrix(ScaleMatrix(3,6,9))

    PrintMatrix(TranslateMatrix(0.5,0.5,0.5))
else :
    print(__name__)