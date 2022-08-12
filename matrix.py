# Author: Dominic Williams
# Date created: 10 Aug 2022
# 
# Matrix Maths Module



import math

VECTOR_SIZE = 4

def ZeroMatrix():
    arr = [[0 for i in range(VECTOR_SIZE)] for j in range(VECTOR_SIZE) ]
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            arr[i][j] = 0
    return arr  

def IdentityMatrix():
    arr = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            if i == j:
                arr[i][j] = 1
    return arr

def MatrixMult(arr1,arr2):
    arr = ZeroMatrix()
    for i in range(VECTOR_SIZE):
        for j in range(VECTOR_SIZE):
            for e in range(VECTOR_SIZE):
                arr[i][j] = arr[i][j] + arr1[i][e]*arr2[e][j]
    return(arr)

def MatrixVector(arr,vect):
    x = arr[0][0]*vect[0] + arr[0][1]*vect[1] + arr[0][2]*vect[2] + arr[0][3]
    y = arr[1][0]*vect[0] + arr[1][1]*vect[1] + arr[1][2]*vect[2] + arr[1][3]
    z = arr[2][0]*vect[0] + arr[2][1]*vect[1] + arr[2][2]*vect[2] + arr[2][3]
    return ([x,y,z])

def RotateMatrix(x,y,z):

    x_rad = math.radians(x)
    y_rad = math.radians(y)
    z_rad = math.radians(z)

    arr_z = IdentityMatrix()
    arr_z[0][0] = math.cos(z_rad)
    arr_z[1][0] = math.sin(z_rad) * -1
    arr_z[0][1] = math.sin(z_rad)
    arr_z[1][1] = math.cos(z_rad)

    arr_y = IdentityMatrix()
    arr_y[0][0] = math.cos(y_rad)
    arr_y[2][0] = math.sin(y_rad) 
    arr_y[0][2] = math.sin(y_rad) * -1
    arr_y[2][2] = math.cos(y_rad)

    arr_x = IdentityMatrix()
    arr_x[1][1] = math.cos(x_rad)
    arr_x[2][1] = math.sin(x_rad) * -1
    arr_x[1][2] = math.sin(x_rad) 
    arr_x[2][2] = math.cos(x_rad)

    arr = MatrixMult(arr_x,arr_y)
    arr = MatrixMult(arr,arr_z)

    return(arr)

def ScaleMatrix(x,y,z):
    arr = IdentityMatrix()
    arr[0][0] = x
    arr[1][1] = y
    arr[2][2] = z
    return(arr)

def TranslateMatrix(x,y,z):
    arr = IdentityMatrix()
    arr[3][0] = x
    arr[3][1] = y
    arr[3][2] = z
    return(arr)

def PrintMatrix(arr):
    for n in arr:
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