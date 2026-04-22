import pygame
import random
import colorsys
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

    def _rainbow_color(self) -> tuple[int, int, int]:
        """Return a slow-cycling rainbow RGB color."""
        hue = (pygame.time.get_ticks() * 0.00008) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
        return int(red * 255), int(green * 255), int(blue * 255)

    def _get_map_border_color(self) -> tuple[int, int, int]:
        if self.game.map_memory.player_has_magic_map():
            return self._rainbow_color()
        if self.game.map_memory.player_has_regular_map():
            return (240, 215, 80)
        return (255, 255, 255)

    def _get_inventory_border_color(self) -> tuple[int, int, int]:
        if self.game.player.inventory.get("KEY", 0) > 0:
            return (255, 215, 0)
        return (255, 255, 255)

    def _get_message_border_color(self) -> tuple[int, int, int]:
        if not self.game.game_active and self.game.game_result == "loss":
            return (220, 65, 65)

        if pygame.time.get_ticks() < self.game.message_success_border_until:
            return (90, 210, 110)

        return (255, 255, 255)

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
        action_window_rect = pygame.Rect(
            UISettings.ACTION_WINDOW_X,
            UISettings.ACTION_WINDOW_Y,
            UISettings.ACTION_WINDOW_WIDTH,
            UISettings.ACTION_WINDOW_HEIGHT
        )
        sidebar_rect = pygame.Rect(
            UISettings.SIDEBAR_X,
            UISettings.SIDEBAR_Y,
            UISettings.SIDEBAR_WIDTH,
            UISettings.SIDEBAR_HEIGHT,
        )
        log_rect = pygame.Rect(
            UISettings.LOG_X,
            UISettings.LOG_Y,
            UISettings.LOG_WIDTH,
            UISettings.LOG_HEIGHT,
        )
        map_rect = pygame.Rect(
            UISettings.MAP_X,
            UISettings.MAP_Y,
            UISettings.MAP_WIDTH,
            UISettings.MAP_HEIGHT,
        )

        pygame.draw.rect(
            self.screen,
            self._get_inventory_border_color(),
            sidebar_rect,
            2,
            UISettings.BORDER_RADIUS,
        )
        pygame.draw.rect(
            self.screen,
            self._get_message_border_color(),
            log_rect,
            2,
            UISettings.BORDER_RADIUS,
        )
        pygame.draw.rect(
            self.screen,
            self._get_map_border_color(),
            map_rect,
            2,
            UISettings.BORDER_RADIUS,
        )

        border_color, border_alpha = self.game.player.get_action_window_border_style()
        if border_alpha >= 255:
            pygame.draw.rect(
                self.screen,
                border_color,
                action_window_rect,
                2,
                UISettings.BORDER_RADIUS
            )
        else:
            border_surface = pygame.Surface(
                (action_window_rect.width, action_window_rect.height),
                pygame.SRCALPHA
            )
            pygame.draw.rect(
                border_surface,
                (*border_color, border_alpha),
                border_surface.get_rect(),
                2,
                UISettings.BORDER_RADIUS
            )
            self.screen.blit(border_surface, action_window_rect.topleft)

        score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        hud_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        score_surf = score_font.render(f"SCORE: {self.game.score}", False, 'white')
        high_score_surf = hud_font.render(f"HIGH SCORE: {self.game.high_score}", False, 'white')
        level_surf = hud_font.render(f"LEVEL {self.game.current_level_number}", False, 'white')
        dungeon_name_surf = hud_font.render(self.game.dungeon.dungeon_name.upper(), False, 'white')

        dungeon_name_rect = dungeon_name_surf.get_rect(center=(UISettings.MAP_X + (UISettings.MAP_WIDTH / 2), UISettings.DUNGEON_NAME_Y))

        self.screen.blit(high_score_surf, (UISettings.SCORE_X, UISettings.SCORE_Y))
        self.screen.blit(score_surf, (UISettings.CURRENT_SCORE_X, UISettings.CURRENT_SCORE_Y))
        self.screen.blit(level_surf, (UISettings.LEVEL_X, UISettings.LEVEL_Y))
        self.screen.blit(dungeon_name_surf, dungeon_name_rect)

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
                end_text = "CONGRATULATIONS"
                end_color = 'green'
            else:
                end_text = "GAME OVER"
                end_color = 'red'
            
            # Render and Center
            text_surf = big_font.render(end_text, False, end_color)
            text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH/2, ScreenSettings.HEIGHT/2))
            self.screen.blit(text_surf, text_rect)

    def draw_level_transition(self):
        """Draw a full-screen transition card between dungeon levels."""
        if not self.game.is_transitioning:
            return

        overlay = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT))
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        big_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
        text_surf = big_font.render(self.game.transition_label, False, 'white')
        text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT / 2))
        self.screen.blit(text_surf, text_rect)

    def draw_treasure_conversion(self):
        """Draw the treasure to gold conversion display in the action window."""
        if not self.game.is_in_treasure_conversion_phase:
            return

        # Draw semi-transparent overlay over the action window
        overlay = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

        # Setup fonts
        font_small = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)
        font_large = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)

        # Start position for text display
        start_x = UISettings.ACTION_WINDOW_X + 20
        start_y = UISettings.ACTION_WINDOW_Y + 20
        line_height = 18

        # Current line position
        y_pos = start_y

        # Display title
        title_surf = font_large.render("TREASURE EXCHANGED FOR COINS", False, 'yellow')
        self.screen.blit(title_surf, (start_x, y_pos))
        y_pos += line_height + 10

        # Display each treasure item with its conversion value
        total_gold = 0
        for item, data in self.game.treasure_conversion_data.items():
            count = data['count']
            value_each = data['value_each']
            total_value = count * value_each
            total_gold += total_value

            # Format: ITEM: count, value = total
            if count > 1:
                item_display = f"+ {count} {item}"
            else:
                item_display = f"+ 1 {item}"

            item_text = f"{item_display} ({total_value})"
            item_surf = font_small.render(item_text, False, 'white')
            self.screen.blit(item_surf, (start_x, y_pos))
            y_pos += line_height

        # Display total
        y_pos += 5
        total_surf = font_large.render(f"= {total_gold} GOLD COINS!", False, 'yellow')
        self.screen.blit(total_surf, (start_x, y_pos))

        # Check if we should show the "PRESS START" prompt
        elapsed = pygame.time.get_ticks() - self.game.conversion_display_start_time
        if elapsed >= self.game.conversion_display_delay_ms:
            y_pos += line_height + 10
            prompt_surf = font_small.render("PRESS START TO CONTINUE", False, 'cyan')
            self.screen.blit(prompt_surf, (start_x, y_pos))