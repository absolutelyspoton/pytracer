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


def make_torus(major=2.2, minor=1.0, seg_u=48, seg_v=24):
    """Parametric torus: ring of radius `major` in the xz-plane, tube of
    radius `minor`. seg_u segments around the ring, seg_v around the tube.
    Wound so face normals point outward from the tube surface."""
    us = np.arange(seg_u) * (2.0 * np.pi / seg_u)
    vs = np.arange(seg_v) * (2.0 * np.pi / seg_v)
    gu, gv = np.meshgrid(us, vs, indexing='ij')

    ring = major + minor * np.cos(gv)
    verts = np.column_stack([(ring * np.cos(gu)).ravel(),
                             (minor * np.sin(gv)).ravel(),
                             (ring * np.sin(gu)).ravel()])

    faces = []
    for i in range(seg_u):
        i2 = (i + 1) % seg_u
        for j in range(seg_v):
            j2 = (j + 1) % seg_v
            a = i * seg_v + j
            b = i2 * seg_v + j
            c = i2 * seg_v + j2
            d = i * seg_v + j2
            faces.append((a, c, b))
            faces.append((a, d, c))
    return Mesh(verts, faces)


def merge_meshes(meshes):
    """Concatenate meshes into one (face indices offset per part)."""
    verts = []
    faces = []
    offset = 0
    for m in meshes:
        verts.append(m.vertices)
        faces.append(m.faces + offset)
        offset += len(m.vertices)
    return Mesh(np.vstack(verts), np.vstack(faces))


def make_uv_sphere(center, radius, seg_u=24, seg_v=14):
    """Lat-long sphere with true pole vertices."""
    cx, cy, cz = center
    verts = [(cx, cy + radius, cz)]           # north pole
    for i in range(1, seg_v):
        theta = np.pi * i / seg_v
        for j in range(seg_u):
            phi = 2.0 * np.pi * j / seg_u
            verts.append((cx + radius * np.sin(theta) * np.cos(phi),
                          cy + radius * np.cos(theta),
                          cz + radius * np.sin(theta) * np.sin(phi)))
    verts.append((cx, cy - radius, cz))       # south pole
    south = len(verts) - 1

    def ring(i, j):
        return 1 + (i - 1) * seg_u + (j % seg_u)

    faces = []
    for j in range(seg_u):                    # pole caps
        faces.append((0, ring(1, j + 1), ring(1, j)))
        faces.append((south, ring(seg_v - 1, j), ring(seg_v - 1, j + 1)))
    for i in range(1, seg_v - 1):             # bands
        for j in range(seg_u):
            a, b = ring(i, j), ring(i, j + 1)
            c, d = ring(i + 1, j), ring(i + 1, j + 1)
            faces.append((a, b, d))
            faces.append((a, d, c))
    return Mesh(verts, faces)


def make_tube(p0, p1, r0, r1, segs=20):
    """Capped tube/frustum from p0 (radius r0) to p1 (radius r1)."""
    p0 = np.asarray(p0, dtype=np.float64)
    p1 = np.asarray(p1, dtype=np.float64)
    axis = p1 - p0
    axis = axis / np.linalg.norm(axis)
    # Orthonormal frame around the axis
    ref = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else \
        np.array([1.0, 0.0, 0.0])
    u = np.cross(axis, ref)
    u /= np.linalg.norm(u)
    w = np.cross(axis, u)

    verts = [tuple(p0), tuple(p1)]            # cap centres: 0, 1
    for j in range(segs):
        phi = 2.0 * np.pi * j / segs
        rim = np.cos(phi) * u + np.sin(phi) * w
        verts.append(tuple(p0 + r0 * rim))
    for j in range(segs):
        phi = 2.0 * np.pi * j / segs
        rim = np.cos(phi) * u + np.sin(phi) * w
        verts.append(tuple(p1 + r1 * rim))

    faces = []
    for j in range(segs):
        j2 = (j + 1) % segs
        a, b = 2 + j, 2 + j2                  # p0 rim
        c, d = 2 + segs + j, 2 + segs + j2    # p1 rim
        faces.append((0, b, a))               # p0 cap
        faces.append((1, c, d))               # p1 cap
        faces.append((a, b, d))               # side
        faces.append((a, d, c))
    m = Mesh(verts, faces)
    # Winding fix: flip faces whose normal points toward the tube axis
    tri = m.vertices[m.faces]
    cent = tri.mean(axis=1)
    mid = (p0 + p1) / 2.0
    to_axis = cent - mid
    inward = np.einsum('ij,ij->i', m.face_normals, to_axis) < 0
    fixed = m.faces.copy()
    fixed[inward] = fixed[inward][:, [0, 2, 1]]
    return Mesh(m.vertices, fixed)


def make_luxo(scale=1.0):
    """An articulated desk lamp balanced on a ball - homage to the classic
    animation. Ball, round base, two angled arms with joint spheres, and a
    conical shade aimed down-forward."""
    parts = []
    # The ball (rests on y=0)
    parts.append(make_uv_sphere((0.0, 1.5, 0.0), 1.5, seg_u=28, seg_v=18))
    # Lamp base: a squat disc sitting on top of the ball
    parts.append(make_tube((0.0, 2.95, 0.0), (0.0, 3.3, 0.0),
                           0.95, 0.75, segs=24))
    # Joints
    parts.append(make_uv_sphere((0.0, 3.35, 0.0), 0.17, seg_u=12, seg_v=8))
    elbow = (-0.75, 4.75, 0.0)
    parts.append(make_uv_sphere(elbow, 0.16, seg_u=12, seg_v=8))
    head_joint = (0.65, 5.55, 0.0)
    parts.append(make_uv_sphere(head_joint, 0.16, seg_u=12, seg_v=8))
    # Arms: lower leans back, upper leans forward
    parts.append(make_tube((0.0, 3.35, 0.0), elbow, 0.09, 0.09, segs=14))
    parts.append(make_tube(elbow, head_joint, 0.09, 0.09, segs=14))
    # Shade: cone opening down-forward from the head joint
    axis = np.array([0.75, -0.85, 0.0])
    axis /= np.linalg.norm(axis)
    neck = np.asarray(head_joint) + axis * 0.12
    mouth = np.asarray(head_joint) + axis * 1.05
    parts.append(make_tube(neck, mouth, 0.16, 0.62, segs=24))

    merged = merge_meshes(parts)
    if scale != 1.0:
        merged = Mesh(merged.vertices * scale, merged.faces)
    return merged


def make_cobra_mk1(scale=1.0):
    """Angular wedge spacecraft in the spirit of Elite's Cobra Mk I:
    pointed nose, wide flat wing plan, raised cockpit ridge fore, matching
    keel below, flat hexagonal tail panel.

    Every face gets its own vertices so vertex normals equal face normals -
    the hull shades as flat facets (an angular ship must not be smoothed).
    Winding is fixed automatically: the hull is star-shaped around the
    origin, so any face whose normal points inward is flipped.
    """
    s = scale
    v = np.array([
        [0.0, 0.0, -3.4],    # 0 nose
        [-3.4, 0.0, 2.2],    # 1 wingtip left
        [3.4, 0.0, 2.2],     # 2 wingtip right
        [-1.2, 0.8, 2.2],    # 3 tail top left
        [1.2, 0.8, 2.2],     # 4 tail top right
        [-1.2, -0.8, 2.2],   # 5 tail bottom left
        [1.2, -0.8, 2.2],    # 6 tail bottom right
        [0.0, 0.9, -0.6],    # 7 cockpit ridge peak
        [0.0, -0.9, -0.2],   # 8 keel peak
        [0.0, 0.0, 2.2],     # 9 tail centre (fan point)
    ]) * s

    hull = [
        # Upper hull: nose -> ridge -> tail top edge, out to the wingtips
        (0, 1, 7), (1, 3, 7), (7, 3, 4), (7, 4, 2), (0, 7, 2),
        # Lower hull, mirrored through the keel
        (0, 8, 1), (1, 8, 5), (8, 6, 5), (8, 2, 6), (0, 2, 8),
        # Tail panel: hexagon fanned from the centre
        (9, 1, 5), (9, 5, 6), (9, 6, 2), (9, 2, 4), (9, 4, 3), (9, 3, 1),
    ]

    # Fix winding so every face normal points away from the interior
    tris = []
    for (a, b, c) in hull:
        p0, p1, p2 = v[a], v[b], v[c]
        n = np.cross(p1 - p0, p2 - p1)
        centroid = (p0 + p1 + p2) / 3.0
        if np.dot(n, centroid) < 0:
            p1, p2 = p2, p1
        tris.append((p0, p1, p2))

    # Per-face vertices: no sharing, so shading stays flat-faceted
    verts = np.array([p for tri in tris for p in tri])
    faces = np.arange(len(verts)).reshape(-1, 3)
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
