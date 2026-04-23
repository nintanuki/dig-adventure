import pygame
import random
import colorsys
from settings import *

class RenderManager:
    """Draw gameplay, overlays, and menu/state-specific UI screens."""

    def __init__(self, game) -> None:
        """Capture render dependencies from the active game manager.

        Args:
            game: Active game manager containing sprites, state, and surfaces.
        """
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
        """Return the minimap border color based on map ownership state.

        Returns:
            tuple[int, int, int]: RGB color used for map window border.
        """
        if self.game.map_memory.player_has_magic_map():
            return self._rainbow_color()
        if self.game.map_memory.player_has_regular_map():
            return ColorSettings.BORDER_MAP_ACTIVE
        return ColorSettings.BORDER_DEFAULT

    def _get_inventory_border_color(self) -> tuple[int, int, int]:
        """Return the inventory border color based on key ownership.

        Returns:
            tuple[int, int, int]: RGB color for inventory window border.
        """
        if self.game.player.inventory.get("KEY", 0) > 0:
            return ColorSettings.BORDER_KEY_ACTIVE
        return ColorSettings.BORDER_DEFAULT

    def _get_message_border_color(self) -> tuple[int, int, int]:
        """Return the message-log border color from current game outcome/state.

        Returns:
            tuple[int, int, int]: RGB color for message window border.
        """
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
        # TODO: Refactor tile/fog composition into dedicated rendering passes if rendering complexity grows.
        # Draw map tiles in row-major order.
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
                        # Fallback draw path for non-wall tiles missing runtime state.
                        self.screen.blit(random.choice(self.scaled_dirt_tiles), (x, y))

                if DebugSettings.GRID:
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
        # Start from a fully opaque darkness layer.
        self.fog_surface.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 255))

        # Subtract a radial alpha mask from the fog layer to reveal lit tiles.
        if self.game.player.light_radius > 0:
            radius_px = int(self.game.player.light_radius * GridSettings.TILE_SIZE)
            
            # Allocate a transparent mask surface with diameter-based bounds.
            light_mask = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
            light_mask.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 0)) 
            
            # Draw concentric circles: center strongest, edge weakest.
            for i in range(radius_px, 0, -1):
                # Linear alpha falloff from center to edge.
                alpha = int(255 * (1 - (i / radius_px)))
                pygame.draw.circle(light_mask, color_with_alpha(ColorSettings.LIGHT_MASK, alpha), (radius_px, radius_px), i)
            
            # Align reveal mask to the player's center in action-window space.
            player_center = (
                self.game.player.rect.centerx - UISettings.ACTION_WINDOW_X,
                self.game.player.rect.centery - UISettings.ACTION_WINDOW_Y
            )
            mask_rect = light_mask.get_rect(center=player_center)
            
            # Use subtractive blending to carve visible space out of the fog layer.
            self.fog_surface.blit(light_mask, mask_rect, special_flags=pygame.BLEND_RGBA_SUB)

        # Composite fog over gameplay scene.
        self.screen.blit(self.fog_surface, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

    def draw_end_game_screens(self):
        """Draw game-over overlay and continue prompt for finished runs."""
        # Draw Game Over Overlay
        if self.game.ui_state == 'game_over':
            # TODO: Move end-screen overlay alpha (180) and prompt Y offset (+42) to UI/Game settings.
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

            if self.game.game_result == 'loss' and self.game.game_over_prompt_start_time > 0:
                elapsed_since_prompt = pygame.time.get_ticks() - self.game.game_over_prompt_start_time
                prompt_alpha = max(0, min(255, int((elapsed_since_prompt / GameSettings.GAME_OVER_PROMPT_FADE_MS) * 255)))
                if prompt_alpha > 0:
                    prompt_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
                    prompt_color = color_with_alpha(ColorSettings.TEXT_PROMPT, prompt_alpha)
                    prompt_surf = prompt_font.render("PRESS START TO CONTINUE", False, prompt_color)
                    prompt_rect = prompt_surf.get_rect(center=(ScreenSettings.WIDTH / 2, (ScreenSettings.HEIGHT / 2) + 42))
                    self.screen.blit(prompt_surf, prompt_rect)
            elif self.game.game_result != 'loss':
                prompt_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
                prompt_surf = prompt_font.render("PRESS START TO CONTINUE", False, ColorSettings.TEXT_PROMPT)
                prompt_rect = prompt_surf.get_rect(center=(ScreenSettings.WIDTH / 2, (ScreenSettings.HEIGHT / 2) + 42))
                self.screen.blit(prompt_surf, prompt_rect)

    def draw_title_screen(self):
        """Draw a minimal title card while waiting for Start."""
        self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

        title_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
        prompt_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        title_surf = title_font.render("DUNGEON DIGGER", False, ColorSettings.TEXT_DEFAULT)
        title_rect = title_surf.get_rect(center=(ScreenSettings.WIDTH / 2, (ScreenSettings.HEIGHT / 2) - 20))
        self.screen.blit(title_surf, title_rect)

        prompt_surf = prompt_font.render("PRESS START TO PLAY", False, ColorSettings.TEXT_PROMPT)
        prompt_rect = prompt_surf.get_rect(center=(ScreenSettings.WIDTH / 2, (ScreenSettings.HEIGHT / 2) + 28))
        self.screen.blit(prompt_surf, prompt_rect)

    def draw_initials_entry_screen(self):
        """Draw initials input for top-ten leaderboard placement."""
        self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

        # TODO: Replace layout magic numbers in this screen (160, 240, 310, 360, 430) with UI constants.

        title_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
        body_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        prompt_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        title_surf = title_font.render("GAME OVER", False, ColorSettings.TEXT_LOSS)
        title_rect = title_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 160))
        self.screen.blit(title_surf, title_rect)

        invite_surf = body_font.render("TOP TEN! ENTER YOUR INITIALS", False, ColorSettings.TEXT_DEFAULT)
        invite_rect = invite_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 240))
        self.screen.blit(invite_surf, invite_rect)

        padded_initials = self.game.initials_entry.ljust(3, '_')
        initials_surf = title_font.render(padded_initials, False, ColorSettings.TEXT_PROMPT)
        initials_rect = initials_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 310))
        self.screen.blit(initials_surf, initials_rect)

        score_surf = body_font.render(f"SCORE: {self.game.pending_leaderboard_score}", False, ColorSettings.TEXT_GOLD)
        score_rect = score_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 360))
        self.screen.blit(score_surf, score_rect)

        help_surf = prompt_font.render("TYPE 3 LETTERS. PRESS START TO CONFIRM.", False, ColorSettings.TEXT_DEFAULT)
        help_rect = help_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 430))
        self.screen.blit(help_surf, help_rect)

    def draw_leaderboard_screen(self):
        """Draw the persisted top-ten scoreboard."""
        self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

        # TODO: Replace leaderboard layout literals (80, 140, 34, -145, +60, 260, -60) with UI constants.

        title_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
        row_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        prompt_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        title_surf = title_font.render("LEADERBOARD", False, ColorSettings.TEXT_DEFAULT)
        title_rect = title_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 80))
        self.screen.blit(title_surf, title_rect)

        if self.game.leaderboard:
            start_y = 140
            row_height = 34
            for rank, (initials, score) in enumerate(self.game.leaderboard, start=1):
                rank_text = f"{rank:>2}. {initials}"
                score_text = f"{score}"

                rank_surf = row_font.render(rank_text, False, ColorSettings.TEXT_DEFAULT)
                score_surf = row_font.render(score_text, False, ColorSettings.TEXT_GOLD)

                y = start_y + ((rank - 1) * row_height)
                self.screen.blit(rank_surf, (ScreenSettings.WIDTH // 2 - 145, y))
                self.screen.blit(score_surf, (ScreenSettings.WIDTH // 2 + 60, y))
        else:
            empty_surf = row_font.render("NO SCORES YET", False, ColorSettings.TEXT_DEFAULT)
            empty_rect = empty_surf.get_rect(center=(ScreenSettings.WIDTH / 2, 260))
            self.screen.blit(empty_surf, empty_rect)

        prompt_surf = prompt_font.render("PRESS START TO PLAY AGAIN", False, ColorSettings.TEXT_PROMPT)
        prompt_rect = prompt_surf.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT - 60))
        self.screen.blit(prompt_surf, prompt_rect)

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

        # TODO: Move conversion UI layout/alpha literals (200, 20, 22, 16, 5, -18) to UI settings.

        # Dim gameplay area while conversion UI is active.
        overlay = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, 200))
        self.screen.blit(overlay, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

        # Configure conversion UI fonts.
        font_items = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        font_large = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        font_prompt = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        # Base text layout anchors.
        start_x = UISettings.ACTION_WINDOW_X + 20
        start_y = UISettings.ACTION_WINDOW_Y + 20
        line_height = 22

        # Mutable vertical cursor for stacked rows.
        y_pos = start_y

        # Render conversion title.
        title_surf = font_large.render("TREASURE EXCHANGED FOR COINS", False, ColorSettings.TEXT_TITLE)
        self.screen.blit(title_surf, (start_x, y_pos))
        y_pos += line_height + 16

        # Render revealed treasure rows and accumulate displayed total.
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

            # Build row prefix with quantity.
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

        # Reveal total after item rows complete.
        if total_is_ready:
            y_pos += 5
            total_surf = font_large.render(f"= {total_gold} GOLD COINS!", False, ColorSettings.TEXT_TITLE)
            self.screen.blit(total_surf, (start_x, y_pos))

        # Fade in continue prompt after reveal delay.
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

        # TODO: Move shop UI layout/alpha literals (210, 20, 22, 16, 6, +12, -18) to UI settings.

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
