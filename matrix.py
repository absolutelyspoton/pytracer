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
    x = m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2] + m[3][0]
    y = m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2] + m[3][1]
    z = m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2] + m[3][2]
    return ([x,y,z])

# Matrix maths to rotate through x,y,z axis
def RotateMatrix(x_theta,y_theta,z_theta):

    x_rad = math.radians(x_theta)
    y_rad = math.radians(y_theta)
    z_rad = math.radians(z_theta)

    # Rotation through z-axis
    arr_z = IdentityMatrix()
    arr_z[0][0] = math.cos(z_rad)  # type: ignore
    arr_z[1][0] = math.sin(z_rad) * -1 # type: ignore
    arr_z[0][1] = math.sin(z_rad) # type: ignore
    arr_z[1][1] = math.cos(z_rad) # type: ignore

    # Rotation through y-axis
    arr_y = IdentityMatrix()
    arr_y[0][0] = math.cos(y_rad) # type: ignore
    arr_y[2][0] = math.sin(y_rad) # type: ignore
    arr_y[0][2] = math.sin(y_rad) * -1 # type: ignore
    arr_y[2][2] = math.cos(y_rad) # type: ignore

    # Rotation through x-axis
    arr_x = IdentityMatrix()
    arr_x[1][1] = math.cos(x_rad) # type: ignore
    arr_x[2][1] = math.sin(x_rad) * -1 # type: ignore
    arr_x[1][2] = math.sin(x_rad) # type: ignore
    arr_x[2][2] = math.cos(x_rad) # type: ignore

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
    m[3][3] = 1
    return(m)

def PerspectiveMatrix():
    m = IdentityMatrix()
    m[2][3] = 0.1  # type: ignore
    m[3][3] = 0
    return(m)

def OrthographicMatrix():
    m = IdentityMatrix()
    m[2][2] = 0
    return(m)

def VectorMagnitude(v) ->float:
    return math.sqrt((v[0]*v[0])+(v[1]*v[1])+(v[2]*v[2]))
    
def NormaliseVector(v):
    r = [0,0,0]
    denom = VectorMagnitude(v)

    if denom == 0.0:
        r[0] = v[0]
        r[1] = v[1]
        r[2] = v[2]
    else:
        t = 1.0 / denom
        r[0] = v[0]*t
        r[1] = v[1]*t
        r[2] = v[2]*t
    return r

def DotProduct(v1,v2):
    return ( (v1[0]*v2[0]) + (v1[1]*v2[1]) + (v1[2]*v2[2]) )

def CalcSurfaceNormal(v1,v2,v3):
        
    # First calculate colinnear vectors
    a = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
    b = [v3[0]-v2[0],v3[1]-v2[1],v3[2]-v2[2]]

    # Calculate the normal and return it
    x = a[1] * b[2] - a[2] * b[1]
    y = a[2] * b[0] - a[0] * b[2]
    z = a[0] * b[1] - a[1] * b[0]

    return [x,y,z]

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

    PrintMatrix(OrthographicMatrix())

    PrintMatrix(PerspectiveMatrix())

    v1 = [0,0,0]
    v2 = [1,2,3]
    v3 = [4,5,6]
    v4 = [0.343,0.423,0.122]
    v5 = [-0.123,-0.987,-0.876]

    print(NormaliseVector(v1))
    print(NormaliseVector(v2))
    print(NormaliseVector(v3))

    print(DotProduct(v1,v2))
    print(DotProduct(v3,v4))
    print(DotProduct(v5,v2))

    print(CalcSurfaceNormal(v1,v2,v3))
