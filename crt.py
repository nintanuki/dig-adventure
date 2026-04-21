import pygame
import random
from settings import *

class CRT:
    """Creates a CRT monitor effect"""
    def __init__(self, screen):
        """
        Initializes the CRT effect by loading a TV overlay image,
        scaling it to fit the screen,
        and storing a reference to the screen for drawing.
        """
        self.screen = screen
        self.base_tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.base_tv = pygame.transform.scale(self.base_tv, ScreenSettings.RESOLUTION)

    def create_crt_lines(self, surf):
        """Draws horizontal scan lines across the surface to enhance the CRT effect."""
        line_height = ScreenSettings.CRT_SCANLINE_HEIGHT
        for y in range(0, ScreenSettings.HEIGHT, line_height):
            pygame.draw.line(surf, 'black', (0, y), (ScreenSettings.WIDTH, y), 1)

    def draw(self):
        """Draws the CRT effect by copying the base TV image, applying a random alpha for flickering,
        adding scan lines, and blitting it on top of the current screen."""
        # COPY each frame (prevents stacking)
        tv = self.base_tv.copy()

        tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines(tv)

        self.screen.blit(tv, (0, 0))