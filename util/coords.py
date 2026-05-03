"""Stateless conversion between grid coordinates and screen pixels.

Lives outside GameManager so any subsystem (minimap_memory, sprites, render,
windows) can do the conversion without going through the game manager
just to call two-line math.
"""

from settings import GridSettings, UISettings


def grid_to_screen(col: int, row: int) -> tuple[int, int]:
    """Return the action-window pixel coordinate for a grid cell's top-left corner.

    Args:
        col: Grid column.
        row: Grid row.

    Returns:
        (x, y) in screen-space pixels.
    """
    return (
        UISettings.ACTION_WINDOW_X + col * GridSettings.TILE_SIZE,
        UISettings.ACTION_WINDOW_Y + row * GridSettings.TILE_SIZE,
    )


def screen_to_grid(x: float, y: float) -> tuple[int, int]:
    """Return the (col, row) of the grid cell covering the given screen pixel.

    Args:
        x: Screen-space x position in pixels.
        y: Screen-space y position in pixels.

    Returns:
        (col, row) grid indices.
    """
    return (
        int((x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE),
        int((y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE),
    )
