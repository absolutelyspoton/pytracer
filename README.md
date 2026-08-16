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
|s             |Cycle render mode: wireframe / hidden-line / solid / gouraud / phong / raytrace |
|d             |Toggle shadows (floor shadow; self-shadowing in stills) |
|p             |Cycle ray-traced floor pattern: checker / stripes / rings / mandelbrot / plain |
|m             |Cycle ray-traced model material: silver / glass / wood / marble |
|o             |Object menu (1-9 selects; objects/ CSVs or MongoDB collections) |
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
|1.2           |Shadows (planar projected on ground plane; shadow-mapped self-shadowing) |
|1.5           |v3: numpy array pipeline - z-buffer rasteriser, live self-shadowing      |
|2.0           |Ray tracing - primary/shadow/reflection rays, mirror materials           |
|2.1           |Refraction & glass (Snell, Fresnel/Schlick, total internal reflection)   |
|1.3 (todo)    |Multiple light source                                                    |

