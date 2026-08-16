# Author: Dominic Williams
# Date created: August 16, 2026 (v3)
#
# Mesh: array-oriented geometry. Vertices, faces, and normals live in numpy
# arrays so the whole pipeline (transform, projection, rasterisation,
# lighting) operates on entire meshes at once. This is the same batch shape
# the future ray tracer needs.

import numpy as np


class Mesh:
    """Triangle mesh held as flat arrays.

    vertices:       (N, 3) float64, world space
    faces:          (M, 3) int32, 0-based vertex indices
    face_normals:   (M, 3) float64, unit, world space
    vertex_normals: (N, 3) float64, unit, world space (area-weighted average
                    of adjacent face normals)
    """

    def __init__(self, vertices, faces):
        self.vertices = np.asarray(vertices, dtype=np.float64).reshape(-1, 3)
        self.faces = np.asarray(faces, dtype=np.int32).reshape(-1, 3)
        if self.faces.size and self.faces.max() >= len(self.vertices):
            raise ValueError(
                f"face references vertex {self.faces.max()}, "
                f"but only {len(self.vertices)} vertices loaded")
        self.face_normals = None
        self.vertex_normals = None
        self.compute_normals()

    def compute_normals(self):
        """Vectorised face + vertex normals (one pass, no Python loops)."""
        v = self.vertices
        f = self.faces
        a = v[f[:, 1]] - v[f[:, 0]]
        b = v[f[:, 2]] - v[f[:, 1]]
        n = np.cross(a, b)
        lengths = np.linalg.norm(n, axis=1, keepdims=True)
        lengths[lengths < 1e-12] = 1.0
        self.face_normals = n / lengths

        # Vertex normals: scatter-add each face normal onto its 3 vertices
        vn = np.zeros_like(v)
        for k in range(3):
            np.add.at(vn, f[:, k], self.face_normals)
        vlen = np.linalg.norm(vn, axis=1, keepdims=True)
        vlen[vlen < 1e-12] = 1.0
        self.vertex_normals = vn / vlen

    def center_offset(self):
        """Translation that centres the mesh's bounding box on the origin."""
        lo = self.vertices.min(axis=0)
        hi = self.vertices.max(axis=0)
        return -(lo + hi) / 2.0

    def bounding_radius(self):
        """Half the bounding-box diagonal (radius that survives any rotation
        about the centred origin)."""
        lo = self.vertices.min(axis=0)
        hi = self.vertices.max(axis=0)
        return float(np.linalg.norm(hi - lo)) / 2.0

    def vertex_count(self):
        return len(self.vertices)

    def face_count(self):
        return len(self.faces)

    def __repr__(self):
        return f"Mesh({self.vertex_count()} vertices, {self.face_count()} faces)"


def floor_mesh(floor_y, half_size, z_center, z_near=0.7, divisions=8):
    """The ground plane as scene geometry: a grid of triangles in view
    space at y = floor_y (y grows downward; this sits below the model),
    centred at depth z_center. Tessellated because the rasteriser's cost
    scales with triangle bounding boxes - two screen-filling triangles
    would generate millions of candidate fragments, a grid of small cells
    stays proportional to the visible area. The near edge is clamped in
    front of the camera's near plane so the grid is never clipped away.
    Wound so face normals point up (-y)."""
    s = half_size
    z0 = max(z_near, z_center - s)
    z1 = z_center + s
    xs = np.linspace(-s, s, divisions + 1)
    zs = np.linspace(z0, z1, divisions + 1)
    gx, gz = np.meshgrid(xs, zs, indexing='ij')
    verts = np.column_stack([gx.ravel(), np.full(gx.size, floor_y), gz.ravel()])

    faces = []
    n = divisions + 1
    for i in range(divisions):
        for j in range(divisions):
            a = i * n + j
            b = (i + 1) * n + j
            faces.append((a, b, b + 1))
            faces.append((a, b + 1, a + 1))
    return Mesh(verts, faces)


if __name__ == '__main__':
    m = Mesh([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
             [(0, 1, 2), (0, 2, 3)])
    print(m)
    print('face normals:\n', m.face_normals)
    print('vertex normals:\n', m.vertex_normals)
    print('center offset:', m.center_offset())
    print('radius:', m.bounding_radius())

    fl = floor_mesh(4.0, 10.0, 6.5)
    print(fl)
    print('floor normals (expect (0,-1,0)):\n', fl.face_normals)
