"""Small rendering helpers shared by gameplay, UI, and overlay modules.

settings.py is intentionally kept declarative (constants only); anything that
needs pygame at import time lives here instead.
"""

import pygame


def color_with_alpha(color_name: str, alpha: int) -> pygame.Color:
    """Return a pygame.Color with an explicit alpha channel.

    Args:
        color_name: Any pygame-compatible color name or value.
        alpha: Alpha channel value in the 0-255 range.

    Returns:
        A pygame.Color with the requested transparency.
    """
    color = pygame.Color(color_name)
    color.a = alpha
    return color
