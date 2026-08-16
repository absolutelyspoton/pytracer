# Author: Dominic Williams
# Date created: August 16, 2026
#
# Viewport: Defines a rectangular viewing region within the screen

class Viewport:
    """
    Defines a rectangular viewport within the screen.

    The viewport is the target rectangle for the camera projection and the
    pixel-level clipping region for geometry drawing (via pygame set_clip).
    """

    def __init__(self, x, y, width, height, screen_width=1024, screen_height=800):
        """
        Initialize viewport.

        Args:
            x: Left edge of viewport (screen pixels)
            y: Top edge of viewport (screen pixels)
            width: Viewport width in pixels
            height: Viewport height in pixels
            screen_width: Total screen width
            screen_height: Total screen height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Derived bounds
        self.x_min = x
        self.y_min = y
        self.x_max = x + width
        self.y_max = y + height

        # Pane center: the projection maps the camera axis to this point
        self.center_x = x + width / 2.0
        self.center_y = y + height / 2.0

    def is_on_screen(self, x_screen, y_screen):
        """
        Check if a point is within the viewport bounds.

        Args:
            x_screen, y_screen: Screen coordinates

        Returns:
            True if point is within viewport
        """
        return (self.x_min <= x_screen <= self.x_max and
                self.y_min <= y_screen <= self.y_max)

    def clip_to_viewport(self, x_screen, y_screen):
        """
        Clamp coordinates to viewport bounds.

        Args:
            x_screen, y_screen: Screen coordinates

        Returns:
            (x_clipped, y_clipped): Coordinates clamped to viewport
        """
        x_clipped = max(self.x_min, min(self.x_max, x_screen))
        y_clipped = max(self.y_min, min(self.y_max, y_screen))
        return (x_clipped, y_clipped)

    def draw_frame(self, screen, color=(0, 0, 0), thickness=2):
        """
        Draw the viewport frame on screen.

        Args:
            screen: pygame screen object
            color: RGB color tuple
            thickness: Frame thickness in pixels
        """
        import pygame
        # Draw rectangle outline
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, color, rect, thickness)

    def __repr__(self):
        return f"Viewport(x={self.x}, y={self.y}, size={self.width}x{self.height})"


# Default viewport: 800×600 centered in 1024×800 screen
DEFAULT_VIEWPORT = Viewport(
    x=(1024 - 800) // 2,      # 112 (center horizontally)
    y=(800 - 600) // 2,       # 100 (center vertically)
    width=800,
    height=600,
    screen_width=1024,
    screen_height=800
)
