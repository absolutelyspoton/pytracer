# Author: Dominic Williams
# Date created: 10 Aug 2022
# v3 (Aug 2026): rewritten on numpy - same conventions, batch operations.
#
# Matrix Maths Module
#
# Conventions (unchanged from v1/v2): matrices are row-major 4x4; vectors
# are ROW vectors multiplied on the left (v @ M), so translation lives in
# row 3 (m[3][0..2]), not the last column. New matrix code must follow this
# or transforms compose incorrectly.

import math
import numpy as np

VECTOR_SIZE = 4  # 4x4 matrices


def ZeroMatrix():
    return np.zeros((4, 4))


def IdentityMatrix():
    return np.identity(4)


def MatrixMult(m1, m2):
    return np.asarray(m1) @ np.asarray(m2)


def MatrixVector(m, v):
    """Single row-vector transform (affine part). Kept for tests and
    call sites that work one point at a time; batch code uses
    transform_points."""
    m = np.asarray(m)
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return (x * m[0, 0] + y * m[1, 0] + z * m[2, 0] + m[3, 0],
            x * m[0, 1] + y * m[1, 1] + z * m[2, 1] + m[3, 1],
            x * m[0, 2] + y * m[1, 2] + z * m[2, 2] + m[3, 2])


def MatrixVectorH(m, v):
    """Homogeneous single-vector transform: also returns w (column 3),
    needed for the perspective divide."""
    m = np.asarray(m)
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return (x * m[0, 0] + y * m[1, 0] + z * m[2, 0] + m[3, 0],
            x * m[0, 1] + y * m[1, 1] + z * m[2, 1] + m[3, 1],
            x * m[0, 2] + y * m[1, 2] + z * m[2, 2] + m[3, 2],
            x * m[0, 3] + y * m[1, 3] + z * m[2, 3] + m[3, 3])


def transform_points(points, m):
    """Batch row-vector transform: (N, 3) points -> (N, 3), one matmul."""
    p = np.asarray(points)
    return p @ m[:3, :3] + m[3, :3]


def transform_directions(directions, m):
    """Batch direction transform (rotation only - no translation row)."""
    return np.asarray(directions) @ np.asarray(m)[:3, :3]


def RotateMatrix(x_theta, y_theta, z_theta):
    x = math.radians(x_theta)
    y = math.radians(y_theta)
    z = math.radians(z_theta)

    arr_z = np.identity(4)
    arr_z[0, 0] = math.cos(z)
    arr_z[1, 0] = -math.sin(z)
    arr_z[0, 1] = math.sin(z)
    arr_z[1, 1] = math.cos(z)

    arr_y = np.identity(4)
    arr_y[0, 0] = math.cos(y)
    arr_y[2, 0] = math.sin(y)
    arr_y[0, 2] = -math.sin(y)
    arr_y[2, 2] = math.cos(y)

    arr_x = np.identity(4)
    arr_x[1, 1] = math.cos(x)
    arr_x[2, 1] = -math.sin(x)
    arr_x[1, 2] = math.sin(x)
    arr_x[2, 2] = math.cos(x)

    return arr_x @ arr_y @ arr_z


def ScaleMatrix(x, y, z):
    m = np.identity(4)
    m[0, 0] = x
    m[1, 1] = y
    m[2, 2] = z
    return m


def TranslateMatrix(x, y, z):
    m = np.identity(4)
    m[3, 0] = x
    m[3, 1] = y
    m[3, 2] = z
    return m


def PerspectiveMatrix(focal_distance=10.0):
    """Perspective projection for row vectors: w = z / focal_distance, so
    after the homogeneous divide x' = x * focal_distance / z."""
    m = np.identity(4)
    m[2, 3] = 1.0 / focal_distance
    m[3, 3] = 0.0
    return m


def OrthographicMatrix():
    m = np.identity(4)
    m[2, 2] = 0.0
    return m


def VectorMagnitude(v) -> float:
    return float(np.linalg.norm(np.asarray(v, dtype=np.float64)))


def NormaliseVector(v):
    a = np.asarray(v, dtype=np.float64)
    denom = np.linalg.norm(a)
    if denom < 1e-9:
        return (float(a[0]), float(a[1]), float(a[2]))
    a = a / denom
    return (float(a[0]), float(a[1]), float(a[2]))


def DotProduct(v1, v2):
    return float(np.dot(np.asarray(v1, dtype=np.float64),
                        np.asarray(v2, dtype=np.float64)))


def CalcSurfaceNormal(v1, v2, v3):
    a = np.asarray(v2, dtype=np.float64) - np.asarray(v1, dtype=np.float64)
    b = np.asarray(v3, dtype=np.float64) - np.asarray(v2, dtype=np.float64)
    n = np.cross(a, b)
    return (float(n[0]), float(n[1]), float(n[2]))


def PrintMatrix(m):
    for row in np.asarray(m):
        print(list(row))


if __name__ == '__main__':

    I = IdentityMatrix()
    PrintMatrix(I)

    Z = ZeroMatrix()
    PrintMatrix(Z)

    PrintMatrix(MatrixMult(I, Z))

    print(MatrixVector(Z, [1, 2, 3]))

    PrintMatrix(RotateMatrix(45, 30, 150))

    PrintMatrix(ScaleMatrix(3, 6, 9))

    PrintMatrix(TranslateMatrix(0.5, 0.5, 0.5))

    PrintMatrix(OrthographicMatrix())

    PrintMatrix(PerspectiveMatrix())

    print(NormaliseVector([1, 2, 3]))
    print(DotProduct([4, 5, 6], [0.343, 0.423, 0.122]))
    print(CalcSurfaceNormal([0, 0, 0], [1, 2, 3], [4, 5, 6]))

    pts = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    print(transform_points(pts, TranslateMatrix(10, 20, 30)))
