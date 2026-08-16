# pytracer
Attempt to build a ray tracing app abstracting various graphics libraries

Graphics Packages Integrated
- pygame

GUI Commands

|Key           |Description                                    |
|--------------|-----------------------------------------------|
|C             |Centre drawing / Reset (camera + transforms)   |
|Arrow Keys    |Shift Up/Down/Left/Right                       |
|+|-           |Dolly camera in/out                            |
|x|y|z         |Spin object through X-Axis, Y-Axis, Z-Axis     |
|a             |Display X/Y/Z Axis Legend                      |
|n|v           |Toggle display of vertex normals               |
|f             |Toggle display of surfaces (polygons)          |
|s             |Cycle render mode: wireframe / hidden-line / solid / gouraud / phong |
|b             |Toggle backface culling (wireframe mode)       |
|h             |Toggle help overlay                            |
|q             |Quit                                           |

Feature History

|Rev           |Description                                                              |
|--------------|------------------------------------------------------------------------ |
|0.11          |Basic Wireframe Drawing - Zoom, Translate, Rotate                        |
|0.2           |Object Classes                                                           |
|0.3           |Normals for surfaces and vertices                                        |
|0.4           |Test cases, and test harness (pytest)                                    |
|0.5           |3d to 2d View Transforms - Perspective & parallel projection             |
|0.6           |Loader supports files, MongoDB direct, and API to Mongo                  |
|0.7           |View plane & perspective camera (dolly, near-plane clipping, viewport)   |
|0.8           |Backface culling & hidden-surface removal (painter's algorithm)          |
|0.9           |Single light source (Phong reflection model: ambient/diffuse/specular)  |
|1.0           |Phong Shading (per-pixel normal interpolation, scanline rasteriser)      |
|1.1           |Gauraud Shading (per-vertex lighting, colour interpolation)              |
|1.2 (todo)    |Shadows                                                                  |
|1.3 (todo)    |Multiple light source                                                    |

