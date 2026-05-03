"""Standalone dungeon map viewer for quick layout inspection.

This tool is intentionally separate from game runtime code.
Run from the project root with `python -m tools.map_viewer` so the
core/ package is importable; running the file directly will fail
because the script directory becomes tools/ instead of the repo root.
"""

import sys

import pygame

from core.dungeon_config import DUNGEON_DIFFICULTY, DUNGEON_MONSTER_COUNTS
from core.tilemaps import DUNGEONS


WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 760
BACKGROUND = (15, 20, 25)
PANEL_BG = (27, 33, 41)
WALL_COLOR = (120, 140, 160)
FLOOR_COLOR = (211, 183, 138)
GRID_LINE = (42, 50, 61)
TEXT_COLOR = (238, 240, 242)
MUTED_TEXT = (170, 180, 190)
ACCENT = (88, 170, 255)
DUNGEON_NAMES = list(DUNGEONS.keys())


def clamp_index(index: int, size: int) -> int:
    """Wrap index in [0, size)."""
    if size <= 0:
        return 0
    return index % size


def draw_map(
    surface: pygame.Surface,
    grid: list,
    top_left: tuple[int, int],
    area_size: tuple[int, int],
) -> None:
    """Render one dungeon grid to fit inside area_size."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        return

    area_w, area_h = area_size
    tile_size = min(area_w // cols, area_h // rows)

    map_w = tile_size * cols
    map_h = tile_size * rows

    start_x = top_left[0] + (area_w - map_w) // 2
    start_y = top_left[1] + (area_h - map_h) // 2

    for row in range(rows):
        for col in range(cols):
            cell = grid[row][col]
            color = WALL_COLOR if cell == "x" else FLOOR_COLOR
            rect = pygame.Rect(
                start_x + col * tile_size,
                start_y + row * tile_size,
                tile_size,
                tile_size,
            )
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, GRID_LINE, rect, 1)

    border_rect = pygame.Rect(start_x - 2, start_y - 2, map_w + 4, map_h + 4)
    pygame.draw.rect(surface, ACCENT, border_rect, 2)


def render(screen: pygame.Surface, title_font: pygame.font.Font, body_font: pygame.font.Font, index: int) -> None:
    """Render the full viewer UI for the current dungeon index."""
    dungeon_name = DUNGEON_NAMES[index]
    dungeon = DUNGEONS[dungeon_name]
    difficulty = DUNGEON_DIFFICULTY[dungeon_name]
    monster_count = DUNGEON_MONSTER_COUNTS[dungeon_name]

    screen.fill(BACKGROUND)

    panel_rect = pygame.Rect(40, 40, WINDOW_WIDTH - 80, WINDOW_HEIGHT - 80)
    pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=12)

    title = title_font.render(dungeon_name, True, TEXT_COLOR)
    screen.blit(title, (66, 58))

    subtitle = body_font.render(
        f"{index + 1}/{len(DUNGEON_NAMES)}  |  {dungeon['desc']}",
        True,
        MUTED_TEXT,
    )
    screen.blit(subtitle, (66, 104))

    meta = body_font.render(
        f"Difficulty: {difficulty}  |  Monsters: {monster_count}",
        True,
        MUTED_TEXT,
    )
    screen.blit(meta, (66, 132))

    instructions = body_font.render(
        "Left/Right or A/D: change map    Home/End: first/last    Esc: quit",
        True,
        MUTED_TEXT,
    )
    screen.blit(instructions, (66, WINDOW_HEIGHT - 76))

    draw_map(
        surface=screen,
        grid=dungeon["grid"],
        top_left=(66, 174),
        area_size=(WINDOW_WIDTH - 132, WINDOW_HEIGHT - 284),
    )

    pygame.display.flip()


def main() -> None:
    """Launch interactive dungeon viewer."""
    pygame.init()
    pygame.display.set_caption("Dungeon Digger Map Viewer")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("consolas", 38, bold=True)
    body_font = pygame.font.SysFont("consolas", 24)

    if not DUNGEON_NAMES:
        raise ValueError("No dungeons found in DUNGEONS.")

    index = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    index = clamp_index(index + 1, len(DUNGEON_NAMES))
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    index = clamp_index(index - 1, len(DUNGEON_NAMES))
                elif event.key == pygame.K_HOME:
                    index = 0
                elif event.key == pygame.K_END:
                    index = len(DUNGEON_NAMES) - 1
            elif event.type == pygame.MOUSEWHEEL:
                index = clamp_index(index + (-event.y), len(DUNGEON_NAMES))

        render(screen, title_font, body_font, index)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
