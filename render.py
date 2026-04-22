import pygame
import random
from settings import *

class RenderManager:
    def __init__(self, game) -> None:
        self.game = game
        self.screen = game.screen
        self.dungeon = game.dungeon
        self.fog_surface = game.fog_surface

        self.scaled_wall_tile = game.scaled_wall_tile
        self.scaled_dug_tile = game.scaled_dug_tile
        self.scaled_dirt_tiles = game.scaled_dirt_tiles

    def draw_grid_background(self):
        """
        Loops through the screen and draws the dirt tiles with grey outlines.
        Draws the dirt tiles only within the Action Window boundaries.
        """
        # Loop through columns and rows based on our calculated grid size
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                x, y = self.game.grid_to_screen(col, row)
                cell_type = self.dungeon.get_map_cell(col, row)

                if cell_type == "x":
                    self.screen.blit(self.scaled_wall_tile, (x, y))
                else:
                    tile_state = self.dungeon.tile_data.get((col, row))
                    if tile_state and tile_state["is_dug"]:
                        self.screen.blit(self.scaled_dug_tile, (x, y))
                    elif tile_state:
                        self.screen.blit(tile_state["dirt_surface"], (x, y))
                    else:
                        # fallback for any non-wall tile that wasn't added to tile_data
                        self.screen.blit(random.choice(self.scaled_dirt_tiles), (x, y))

                if DebugSettings.GRID: # Toggle grey outlines for debugging
                    tile_outline = pygame.Rect(x, y, GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
                    pygame.draw.rect(self.screen, (60, 60, 60), tile_outline, 1)

    def draw_ui_frames(self):
        """Draw borders around all UI sections."""
        
        # We define the frames as a list of tuples so we can easily loop through them and draw them with the same style.
        frames = [
            (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y,
            UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT),

            (UISettings.SIDEBAR_X, UISettings.SIDEBAR_Y,
            UISettings.SIDEBAR_WIDTH, UISettings.SIDEBAR_HEIGHT),

            (UISettings.LOG_X, UISettings.LOG_Y,
            UISettings.LOG_WIDTH, UISettings.LOG_HEIGHT),

            (UISettings.MAP_X, UISettings.MAP_Y,
            UISettings.MAP_WIDTH, UISettings.MAP_HEIGHT),
        ]

        # We loop through each frame definition and draw a rounded rectangle with the specified border color, thickness, and radius.
        for x, y, width, height in frames:
            rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(
                self.screen,
                UISettings.BORDER_COLOR,
                rect,
                2,
                UISettings.BORDER_RADIUS
            )

        score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        score_surf = score_font.render(f"SCORE: {self.game.score}", False, 'white')

        score_x = UISettings.SCORE_X
        score_y = UISettings.SCORE_Y

        self.screen.blit(score_surf, (score_x, score_y))

    def draw_fog_of_war(self):
        """
        Build a soft-edged light reveal over a fully dark dungeon.

        The fog is rendered as a separate surface so visibility can be controlled
        independently from tile rendering and sprite drawing.
        """
        self.fog_surface.fill((0, 0, 0, 255)) # Start with a fully opaque black surface

        # We are going to create a circular gradient mask that will "punch through" the fog of war to create our light radius effect.
        # This will create a more natural looking light effect with smooth edges
        if self.game.player.light_radius > 0:
            radius_px = int(self.game.player.light_radius * GridSettings.TILE_SIZE)
            
            # Create the mask surface (Twice the radius)
            # This must be SRCALPHA and we start it COMPLETELY transparent
            light_mask = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
            light_mask.fill((0, 0, 0, 0)) 
            
            # Draw a WHITE gradient from the center outwards
            # Center = White (Alpha 255)
            # Edge = Transparent (Alpha 0)
            for i in range(radius_px, 0, -1):
                # Inner circles are more opaque (brighter)
                alpha = int(255 * (1 - (i / radius_px)))
                pygame.draw.circle(light_mask, (255, 255, 255, alpha), (radius_px, radius_px), i)
            
            # Center it on the player
            player_center = (
                self.game.player.rect.centerx - UISettings.ACTION_WINDOW_X,
                self.game.player.rect.centery - UISettings.ACTION_WINDOW_Y
            )
            mask_rect = light_mask.get_rect(center=player_center)
            
            # THE MAGIC BLEND MODE: BLEND_RGBA_SUB
            # We are SUBTRACTING our white gradient from the black fog.
            # (Black 255 Alpha) - (White 255 Alpha) = (Black 0 Alpha) -> Transparent!
            # Since the area outside the circle is 0 alpha, nothing gets subtracted, 
            # so the fog stays black and square-free.
            self.fog_surface.blit(light_mask, mask_rect, special_flags=pygame.BLEND_RGBA_SUB)

        # Blit the fog to the screen
        self.screen.blit(self.fog_surface, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

    def draw_end_game_screens(self):
        # Draw Game Over Overlay
        if not self.game.game_active:
            # Dim the screen
            overlay = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0,0))

            # Setup font for large text
            big_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
            
            # Use explicit game outcome so door-tile deaths do not render as a win.
            if self.game.game_result == "win":
                end_text = "ESCAPE"
                end_color = 'green'
            else:
                end_text = "GAME OVER"
                end_color = 'red'
            
            # Render and Center
            text_surf = big_font.render(end_text, False, end_color)
            text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH/2, ScreenSettings.HEIGHT/2))
            self.screen.blit(text_surf, text_rect)