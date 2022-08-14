# Author: Dominic Williams
# Date created: 14 Aug 2022
# 
# Unit tests for matrix maths module

import matrix

def test_ZeroMatrix():
    arr = matrix.ZeroMatrix()
    for i in range(matrix.VECTOR_SIZE):
        for j in range(matrix.VECTOR_SIZE):
            assert arr[i][j] == 0

def test_IdentityMatrix():
    arr = matrix.IdentityMatrix()
    for i in range(matrix.VECTOR_SIZE):
        for j in range(matrix.VECTOR_SIZE):
            if i == j:
                assert arr[i][j] == 1
            else:
                assert arr[i][j] == 0

def test_MatrixMult_II():
    m1 = matrix.IdentityMatrix()
    m2 = matrix.IdentityMatrix()
    m3 = matrix.MatrixMult(m1,m2)
    for i in range(matrix.VECTOR_SIZE):
        for j in range(matrix.VECTOR_SIZE):
            assert m1[i][j] == m2[i][j] == m3[i][j]
            if i == j:
                assert m1[i][j] == m2[i][j] == m3[i][j] == 1
            else:
                assert m1[i][j] == m2[i][j] == m3[i][j] == 0
            
def test_MatrixMult_ZZ():
    m1 = matrix.ZeroMatrix()
    m2 = matrix.ZeroMatrix()
    m3 = matrix.MatrixMult(m1,m2)
    for i in range(matrix.VECTOR_SIZE):
        for j in range(matrix.VECTOR_SIZE):
            assert m1[i][j] == m2[i][j] == m3[i][j]
            assert m1[i][j] == m2[i][j] == m3[i][j] == 0
            
