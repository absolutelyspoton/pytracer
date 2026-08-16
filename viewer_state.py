# Author: Dominic Williams
# Date created: 2026
#
# ViewerState: Encapsulates all viewer transformation and display state
# InputHandler: Processes keyboard input and updates state

import pygame
import math
import camera
import light

class ViewerState:
    """Encapsulates all viewer transformation and display state."""

    # Configuration constants
    SCALE_MULTIPLIER = 1.1
    ROTATION_INCREMENT_DEG = 25
    TRANSLATION_INCREMENT = 0.25  # world units (model is ~3.5 units in radius)
    DOLLY_MULTIPLIER = 1.1
    RENDER_MODES = ['wireframe', 'hidden-line', 'solid', 'gouraud', 'phong']

    def __init__(self, screen_width, screen_height):
        # Model transformations (world units; the model loads at its raw size)
        self.scale = [1.0, 1.0, 1.0]
        self.rotation = [180.0, 180.0, 0.0]
        self.translation = [0.0, 0.0, 0.0]

        # Camera (view transform + perspective projection)
        self.camera = camera.Camera()

        # Single directional light (view space, fixed relative to the viewer)
        self.light = light.Light()

        # Display flags
        self.draw_normals = False
        self.draw_faces = True
        self.draw_axes = True
        self.backface_cull = False  # wireframe-only toggle; other modes always cull
        self.render_mode = 'wireframe'  # cycles: wireframe -> hidden-line -> solid
        self.show_help = False

        # Continuous rotation state
        self.rotation_active = [False, False, False]  # x, y, z

    def reset(self):
        """Reset to initial state (equivalent to pressing 'c')."""
        self.scale = [1.0, 1.0, 1.0]
        self.rotation = [180.0, 180.0, 0.0]
        self.translation = [0.0, 0.0, 0.0]
        self.camera.reset()

    def toggle_normals(self):
        """Toggle vertex normals display."""
        self.draw_normals = not self.draw_normals

    def toggle_faces(self):
        """Toggle wireframe faces display."""
        self.draw_faces = not self.draw_faces

    def toggle_axes(self):
        """Toggle axis legend display."""
        self.draw_axes = not self.draw_axes

    def toggle_backface_cull(self):
        """Toggle backface culling."""
        self.backface_cull = not self.backface_cull

    def cycle_render_mode(self):
        """Advance to the next render mode: wireframe -> hidden-line -> solid."""
        i = self.RENDER_MODES.index(self.render_mode)
        self.render_mode = self.RENDER_MODES[(i + 1) % len(self.RENDER_MODES)]

    def toggle_help(self):
        """Toggle help overlay."""
        self.show_help = not self.show_help

    def toggle_rotation(self, axis):
        """Toggle continuous rotation on given axis (0=x, 1=y, 2=z)."""
        self.rotation_active[axis] = not self.rotation_active[axis]

    def update_continuous_rotations(self):
        """Update rotation values based on active rotation flags."""
        if self.rotation_active[0]:
            self.rotation[0] -= math.radians(self.ROTATION_INCREMENT_DEG)
        if self.rotation_active[1]:
            self.rotation[1] += math.radians(self.ROTATION_INCREMENT_DEG)
        if self.rotation_active[2]:
            self.rotation[2] += math.radians(self.ROTATION_INCREMENT_DEG)

    def scale_zoom(self, factor):
        """Scale all axes by factor (factor > 1 = zoom in, < 1 = zoom out)."""
        for i in range(3):
            self.scale[i] *= factor

    def pan(self, dx, dy):
        """Pan by (dx, dy) in screen space."""
        self.translation[0] += dx
        self.translation[1] += dy


class InputHandler:
    """Processes keyboard input and updates viewer state."""

    def __init__(self, state):
        self.state = state

    def handle_keydown(self, key):
        """Process a keyboard event."""
        if key == pygame.K_c:
            self.state.reset()
            print('center ...')

        elif key == pygame.K_MINUS:
            # Dolly the camera away from the object (zoom out)
            self.state.camera.dolly(self.state.DOLLY_MULTIPLIER)

        elif key == pygame.K_EQUALS:
            # Dolly the camera toward the object (zoom in)
            self.state.camera.dolly(1.0 / self.state.DOLLY_MULTIPLIER)

        elif key == pygame.K_x:
            self.state.toggle_rotation(0)

        elif key == pygame.K_y:
            self.state.toggle_rotation(1)

        elif key == pygame.K_z:
            self.state.toggle_rotation(2)

        elif key == pygame.K_UP:
            self.state.pan(0, -self.state.TRANSLATION_INCREMENT)

        elif key == pygame.K_DOWN:
            self.state.pan(0, self.state.TRANSLATION_INCREMENT)

        elif key == pygame.K_LEFT:
            self.state.pan(-self.state.TRANSLATION_INCREMENT, 0)

        elif key == pygame.K_RIGHT:
            self.state.pan(self.state.TRANSLATION_INCREMENT, 0)

        elif key == pygame.K_a:
            self.state.toggle_axes()
            status = 'on' if self.state.draw_axes else 'off'
            print(f'axis legend {status} ...')

        elif key == pygame.K_n or key == pygame.K_v:
            self.state.toggle_normals()
            status = 'on' if self.state.draw_normals else 'off'
            print(f'vertex normals {status} ...')

        elif key == pygame.K_f:
            self.state.toggle_faces()
            status = 'on' if self.state.draw_faces else 'off'
            print(f'draw faces {status} ...')

        elif key == pygame.K_b:
            self.state.toggle_backface_cull()
            status = 'on' if self.state.backface_cull else 'off'
            print(f'backface culling {status} ...')

        elif key == pygame.K_s:
            self.state.cycle_render_mode()
            print(f'render mode: {self.state.render_mode} ...')

        elif key == pygame.K_h:
            self.state.toggle_help()
            status = 'on' if self.state.show_help else 'off'
            print(f'help {status} ...')
