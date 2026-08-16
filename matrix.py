# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Matrix Maths Module

import math

VECTOR_SIZE = 4 # 4x4 Matrices

# Return zero matrix
# [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
def ZeroMatrix():
    return [[0 for i in range(VECTOR_SIZE)] for j in range(VECTOR_SIZE)]  

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
    return (x, y, z)

# Matrix maths to rotate through x,y,z axis
def RotateMatrix(x_theta,y_theta,z_theta):
    """Compose XYZ rotation matrix directly without intermediate multiplications.

    Directly computes (Rx * Ry) * Rz by calculating the 9 coefficients,
    avoiding 2 full matrix multiplications (128 operations -> ~18 operations).

    Verified formulas from symbolic expansion of rotation matrix products.
    """
    x_rad = math.radians(x_theta)
    y_rad = math.radians(y_theta)
    z_rad = math.radians(z_theta)

    # Pre-compute sin/cos once
    cx, sx = math.cos(x_rad), math.sin(x_rad)
    cy, sy = math.cos(y_rad), math.sin(y_rad)
    cz, sz = math.cos(z_rad), math.sin(z_rad)

    # Build rotation matrix by direct coefficient calculation
    m = [[0 for _ in range(4)] for _ in range(4)]

    # Row 0
    m[0][0] = cy * cz
    m[0][1] = cy * sz
    m[0][2] = -sy
    m[0][3] = 0

    # Row 1
    m[1][0] = sx * sy * cz - cx * sz
    m[1][1] = cx * cz + sx * sy * sz
    m[1][2] = sx * cy
    m[1][3] = 0

    # Row 2
    m[2][0] = cx * sy * cz + sx * sz
    m[2][1] = cx * sy * sz - sx * cz
    m[2][2] = cx * cy
    m[2][3] = 0

    # Row 3 (translation/homogeneous)
    m[3][0] = 0
    m[3][1] = 0
    m[3][2] = 0
    m[3][3] = 1

    return m

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
    denom = VectorMagnitude(v)

    if abs(denom) < 1e-9:
        return (v[0], v[1], v[2])
    else:
        t = 1.0 / denom
        return (v[0]*t, v[1]*t, v[2]*t)

def DotProduct(v1,v2):
    return ( (v1[0]*v2[0]) + (v1[1]*v2[1]) + (v1[2]*v2[2]) )

def CalcSurfaceNormal(v1,v2,v3):
    # Calculate collinear vectors
    a_x, a_y, a_z = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
    b_x, b_y, b_z = v3[0]-v2[0], v3[1]-v2[1], v3[2]-v2[2]

    # Calculate the normal and return it
    x = a_y * b_z - a_z * b_y
    y = a_z * b_x - a_x * b_z
    z = a_x * b_y - a_y * b_x

    return (x, y, z)

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
