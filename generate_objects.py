#!/usr/bin/env python3
# Author: Dominic Williams
# Date created: August 16, 2026
#
# Generate procedural object CSVs into objects/, matching the Utah teapot
# file conventions: {name}_vertices.csv / {name}_faces.csv (header row,
# 1-based face indices) plus {name}_*_mdb.csv variants with a leading id
# column for MongoDB import.
#
# Add new shapes to GENERATORS; setup_mongodb.py imports every pair found
# in objects/ into {name}_vertices / {name}_surfaces collections.

import mesh

GENERATORS = {
    'torus': lambda: mesh.make_torus(major=2.2, minor=1.0,
                                     seg_u=48, seg_v=24),
    'cobra_mk1': lambda: mesh.make_cobra_mk1(),
    'luxo_lamp': lambda: mesh.make_luxo(),
}


def write_object(name, m):
    vfn = f'./objects/{name}_vertices.csv'
    ffn = f'./objects/{name}_faces.csv'

    with open(vfn, 'w') as f:
        f.write('x,y,z\n')
        for x, y, z in m.vertices:
            f.write(f'{x:.6f},{y:.6f},{z:.6f}\n')
    with open(ffn, 'w') as f:
        f.write('x,y,z\n')
        for a, b, c in m.faces + 1:  # CSVs hold 1-based indices
            f.write(f'{a},{b},{c}\n')

    # MongoDB variants carry a leading id column
    with open(f'./objects/{name}_vertices_mdb.csv', 'w') as f:
        f.write('id,x,y,z\n')
        for i, (x, y, z) in enumerate(m.vertices, start=1):
            f.write(f'{i},{x:.6f},{y:.6f},{z:.6f}\n')
    with open(f'./objects/{name}_faces_mdb.csv', 'w') as f:
        f.write('id,x,y,z\n')
        for i, (a, b, c) in enumerate(m.faces + 1, start=1):
            f.write(f'{i},{a},{b},{c}\n')

    print(f'{name}: {m.vertex_count()} vertices, {m.face_count()} faces -> '
          f'{vfn}, {ffn} (+ _mdb variants)')


if __name__ == '__main__':
    for name, gen in GENERATORS.items():
        write_object(name, gen())
