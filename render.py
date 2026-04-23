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
            return ColorSettings.BORDER_MAP_ACTIVE
        return ColorSettings.BORDER_DEFAULT

    def _get_inventory_border_color(self) -> tuple[int, int, int]:
        if self.game.player.inventory.get("KEY", 0) > 0:
            return ColorSettings.BORDER_KEY_ACTIVE
        return ColorSettings.BORDER_DEFAULT

    def _get_message_border_color(self) -> tuple[int, int, int]:
        if not self.game.game_active and self.game.game_result == "loss":
            return ColorSettings.BORDER_MESSAGE_FAILURE

        if pygame.time.get_ticks() < self.game.message_success_border_until:
            return ColorSettings.BORDER_MESSAGE_SUCCESS

        return ColorSettings.BORDER_DEFAULT

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
                    pygame.draw.rect(self.screen, ColorSettings.GRID_OUTLINE, tile_outline, 1)

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
            alpha_color = color_with_alpha(border_color, border_alpha)
            pygame.draw.rect(border_surface, alpha_color, border_surface.get_rect(), 2, UISettings.BORDER_RADIUS)
            self.screen.blit(border_surface, action_window_rect.topleft)

        score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        hud_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        score_surf = score_font.render(f"SCORE: {self.game.score}", False, ColorSettings.TEXT_DEFAULT)
        high_score_surf = hud_font.render(f"HIGH SCORE: {self.game.high_score}", False, ColorSettings.TEXT_DEFAULT)
        level_surf = hud_font.render(f"LEVEL {self.game.current_level_number}", False, ColorSettings.TEXT_DEFAULT)
        dungeon_name_surf = hud_font.render(self.game.dungeon.dungeon_name.upper(), False, ColorSettings.TEXT_DEFAULT)

        dungeon_name_rect = dungeon_name_surf.get_rect(center=(UISettings.MAP_X + (UISettings.MAP_WIDTH / 2), UISettings.DUNGEON_NAME_Y))

        self.screen.blit(high_score_surf, (UISettings.SCORE_X, UISettings.SCORE_Y))
        self.screen.blit(score_surf, (UISettings.CURRENT_SCORE_X, UISettings.CURRENT_SCORE_Y))
        self.screen.blit(level_surf, (UISettings.LEVEL_X, UISettings.LEVEL_Y))
        if not self.game.is_in_shop_phase:
            self.screen.blit(dungeon_name_surf, dungeon_name_rect)

    def draw_fog_of_war(self):
        """
        Build a soft-edged light reveal over a fully dark dungeon.

        The fog is rendered as a separate surface so visibility can be controlled
        independently from tile rendering and sprite drawing.
        """
        self.fog_surface.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 255)) # Start with a fully opaque black surface

        # We are going to create a circular gradient mask that will "punch through" the fog of war to create our light radius effect.
        # This will create a more natural looking light effect with smooth edges
        if self.game.player.light_radius > 0:
            radius_px = int(self.game.player.light_radius * GridSettings.TILE_SIZE)
            
            # Create the mask surface (Twice the radius)
            # This must be SRCALPHA and we start it COMPLETELY transparent
            light_mask = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
            light_mask.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 0)) 
            
            # Draw a WHITE gradient from the center outwards
            # Center = White (Alpha 255)
            # Edge = Transparent (Alpha 0)
            for i in range(radius_px, 0, -1):
                # Inner circles are more opaque (brighter)
                alpha = int(255 * (1 - (i / radius_px)))
                pygame.draw.circle(light_mask, color_with_alpha(ColorSettings.LIGHT_MASK, alpha), (radius_px, radius_px), i)
            
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
            overlay.fill(ColorSettings.OVERLAY_BACKGROUND)
            self.screen.blit(overlay, (0,0))

            # Setup font for large text
            big_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
            
            # Use explicit game outcome so door-tile deaths do not render as a win.
            if self.game.game_result == "win":
                end_text = "CONGRATULATIONS"
                end_color = ColorSettings.TEXT_WIN
            else:
                end_text = "GAME OVER"
                end_color = ColorSettings.TEXT_LOSS
            
            # Render and Center
            text_surf = big_font.render(end_text, False, end_color)
            text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH/2, ScreenSettings.HEIGHT/2))
            self.screen.blit(text_surf, text_rect)

    def draw_level_transition(self):
        """Draw a full-screen transition card between dungeon levels."""
        if not self.game.is_transitioning:
            return

        overlay = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT))
        overlay.fill(ColorSettings.OVERLAY_BACKGROUND)
        self.screen.blit(overlay, (0, 0))

        big_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
        text_surf = big_font.render(self.game.transition_label, False, ColorSettings.TEXT_DEFAULT)
        text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT / 2))
        self.screen.blit(text_surf, text_rect)

    def draw_treasure_conversion(self):
        """Draw the treasure to gold conversion display in the action window."""
        if not self.game.is_in_treasure_conversion_phase:
            return

        # Draw semi-transparent overlay over the action window
        overlay = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 200))
        self.screen.blit(overlay, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

        # Setup fonts
        font_items = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        font_large = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        font_prompt = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        # Start position for text display
        start_x = UISettings.ACTION_WINDOW_X + 20
        start_y = UISettings.ACTION_WINDOW_Y + 20
        line_height = 22

        # Current line position
        y_pos = start_y

        # Display title
        title_surf = font_large.render("TREASURE EXCHANGED FOR COINS", False, ColorSettings.TEXT_TITLE)
        self.screen.blit(title_surf, (start_x, y_pos))
        y_pos += line_height + 16

        # Display each treasure item with its conversion value
        total_gold = 0
        elapsed = pygame.time.get_ticks() - self.game.conversion_display_start_time
        reveal_count = max(0, elapsed // self.game.conversion_line_reveal_interval_ms)

        visible_items = list(self.game.treasure_conversion_data.items())[:reveal_count]

        def draw_segments(x: int, y: int, segments: list[tuple[str, str]]) -> None:
            draw_x = x
            for text, color in segments:
                surf = font_items.render(text, False, color)
                self.screen.blit(surf, (draw_x, y))
                draw_x += surf.get_width()

        for item, data in visible_items:
            count = data['count']
            value_each = data['value_each']
            total_value = count * value_each
            total_gold += total_value

            # Format: ITEM: count, value = total
            if count > 1:
                prefix_text = f"+ {count} "
            else:
                prefix_text = "+ 1 "

            if item == 'RUBY':
                item_color = ColorSettings.TREASURE_RUBY
            elif item == 'SAPPHIRE':
                item_color = ColorSettings.TREASURE_SAPPHIRE
            elif item == 'EMERALD':
                item_color = ColorSettings.TREASURE_EMERALD
            elif item == 'DIAMOND':
                item_color = ColorSettings.TREASURE_DIAMOND
            else:
                item_color = ColorSettings.TEXT_DEFAULT

            draw_segments(start_x, y_pos, [
                (prefix_text, ColorSettings.TEXT_DEFAULT),
                (item, item_color),
                (f" ({total_value})", ColorSettings.TEXT_DEFAULT),
            ])
            y_pos += line_height

        all_items_revealed = len(visible_items) == len(self.game.treasure_conversion_data)
        total_ready_at = (len(self.game.treasure_conversion_data) * self.game.conversion_line_reveal_interval_ms) + self.game.conversion_total_reveal_delay_ms
        total_is_ready = all_items_revealed and elapsed >= total_ready_at

        # Display total only after all items have been revealed.
        if total_is_ready:
            y_pos += 5
            total_surf = font_large.render(f"= {total_gold} GOLD COINS!", False, ColorSettings.TEXT_TITLE)
            self.screen.blit(total_surf, (start_x, y_pos))

        # Check if we should show the "PRESS START" prompt
        prompt_ready_at = total_ready_at + self.game.conversion_display_delay_ms
        if elapsed >= prompt_ready_at:
            prompt_alpha = min(255, int(((elapsed - prompt_ready_at) / self.game.conversion_prompt_fade_ms) * 255))
            prompt_color = color_with_alpha(ColorSettings.TEXT_PROMPT, prompt_alpha)
            prompt_surf = font_prompt.render("PRESS START TO CONTINUE", False, prompt_color)
            prompt_rect = prompt_surf.get_rect(
                center=(
                    UISettings.ACTION_WINDOW_X + (UISettings.ACTION_WINDOW_WIDTH // 2),
                    UISettings.ACTION_WINDOW_Y + UISettings.ACTION_WINDOW_HEIGHT - 18,
                )
            )
            self.screen.blit(prompt_surf, prompt_rect)

    def draw_shop_menu(self):
        """Draw the between-level shop inside the action window."""
        if not self.game.is_in_shop_phase:
            return

        overlay = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 210))
        self.screen.blit(overlay, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

        font_small = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        font_large = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        font_prompt = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        start_x = UISettings.ACTION_WINDOW_X + 20
        start_y = UISettings.ACTION_WINDOW_Y + 20
        line_height = 22
        y_pos = start_y

        title_surf = font_large.render("KHAJIIT HAS WARES, IF YOU HAVE COIN", False, ColorSettings.TEXT_TITLE)
        self.screen.blit(title_surf, (start_x, y_pos))
        y_pos += line_height + 16

        gold_total = self.game.player.inventory.get('GOLD COINS', 0)
        gold_surf = font_small.render(f"GOLD COINS: {gold_total}", False, ColorSettings.TEXT_GOLD)
        self.screen.blit(gold_surf, (start_x, y_pos))
        y_pos += line_height + 6

        options = self.game.get_shop_menu_options()
        selected_index = min(self.game.shop_selected_index, max(0, len(options) - 1))

        for index, option in enumerate(options):
            if option == 'CONTINUE':
                line_text = 'CONTINUE TO NEXT LEVEL'
                color = ColorSettings.TEXT_CONTINUE
            else:
                price = ItemSettings.SHOP_PRICES[option]
                stock = self.game.shop_stock.get(option)
                if stock == 0:
                    line_text = f"{option} - OUT OF STOCK"
                    color = ColorSettings.TEXT_ERROR
                else:
                    count_suffix = '' if stock is None else f" x{stock}"
                    line_text = f"{option}{count_suffix} - {price}G"
                    color = ColorSettings.TEXT_DEFAULT

            if index == selected_index:
                selector_surf = font_small.render('> ', False, ColorSettings.TEXT_SELECTOR)
                self.screen.blit(selector_surf, (start_x, y_pos))
                line_surf = font_small.render(line_text, False, color)
                self.screen.blit(line_surf, (start_x + 12, y_pos))
            else:
                line_surf = font_small.render(f"  {line_text}", False, color)
                self.screen.blit(line_surf, (start_x, y_pos))

            y_pos += line_height

        elapsed = pygame.time.get_ticks() - self.game.shop_display_start_time
        if elapsed >= self.game.shop_display_delay_ms:
            prompt_surf = font_prompt.render("PRESS START TO CONTINUE", False, ColorSettings.TEXT_PROMPT)
            prompt_rect = prompt_surf.get_rect(
                center=(
                    UISettings.ACTION_WINDOW_X + (UISettings.ACTION_WINDOW_WIDTH // 2),
                    UISettings.ACTION_WINDOW_Y + UISettings.ACTION_WINDOW_HEIGHT - 18,
                )
            )
            self.screen.blit(prompt_surf, prompt_rect)
