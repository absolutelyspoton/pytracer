# Author: Dominic Williams
# Date created: August 16, 2026
#
# Camera: view transform and perspective projection parameters.
#
# The camera sits on the world -z axis at `distance` from the origin, looking
# toward +z. Its view matrix translates the world by +distance in z, which
# places the camera at the view-space origin: any point with z_view > near is
# in front of the camera.

import math
import matrix

class Camera:

    def __init__(self, distance=6.5, fov_degrees=60.0, near=0.5, min_distance=1.0):
        self.default_distance = distance
        self.distance = distance
        self.fov_degrees = fov_degrees
        self.near = near
        self.min_distance = min_distance

        # Focal distance of the view plane. The pane-mapping factor below
        # cancels it out, so its value only sets the scale of the intermediate
        # view-plane coordinates.
        self.focal_distance = 1.0

        # Pixels per unit on the view plane, chosen so the vertical FOV spans
        # the viewport pane exactly: half the pane height corresponds to a
        # projected offset of focal_distance * tan(fov/2).
        self.pixels_per_unit = None  # set by attach_viewport()

    def attach_viewport(self, viewport):
        """Derive the pane-mapping constants from a viewport."""
        half_fov_rad = math.radians(self.fov_degrees) / 2.0
        self.pixels_per_unit = ((viewport.height / 2.0) /
                                (self.focal_distance * math.tan(half_fov_rad)))

    def view_matrix(self):
        return matrix.TranslateMatrix(0.0, 0.0, self.distance)

    def projection_matrix(self):
        return matrix.PerspectiveMatrix(self.focal_distance)

    def dolly(self, factor):
        """Move the camera toward (factor < 1) or away from (factor > 1) the origin."""
        self.distance = max(self.min_distance, self.distance * factor)

    def reset(self):
        self.distance = self.default_distance

    def __repr__(self):
        return (f"Camera(distance={self.distance:.2f}, fov={self.fov_degrees}°, "
                f"near={self.near})")


if __name__ == '__main__':
    import viewport

    cam = Camera()
    cam.attach_viewport(viewport.DEFAULT_VIEWPORT)
    print(cam)
    print('view matrix:')
    matrix.PrintMatrix(cam.view_matrix())
    print('projection matrix:')
    matrix.PrintMatrix(cam.projection_matrix())
    print(f'pixels per view-plane unit: {cam.pixels_per_unit:.2f}')

    cam.dolly(0.5)
    cam.dolly(0.01)  # should clamp at min_distance
    print(cam)
