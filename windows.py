import pygame
import colorsys
import math
from settings import UISettings, FontSettings, WindowSettings, ColorSettings

class MessageLog:
    """Render and animate the scrolling in-game message log."""

    def __init__(self, game):
        """Initialize message history, highlighting rules, and typewriter state.

        Args:
            game: Active game manager providing state and settings access.
        """
        self.game = game
        self.messages = list(WindowSettings.WELCOME_MESSAGE) 
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

        self.highlight_terms = self._build_highlight_terms()

        # Typewriter state
        self.full_text = ""
        self.active_message = ""
        self.char_index = 0
        self.type_speed = WindowSettings.TYPING_SPEED
        self.current_type_speed = self.type_speed
        self.is_typing = False

    def _build_highlight_terms(self) -> list[tuple[str, str]]:
        """Build ordered highlight terms for message-window text coloring."""
        self.control_label_colors = {
            "X": ColorSettings.MESSAGE_CONTROL_X,
            "Y": ColorSettings.MESSAGE_CONTROL_Y,
            "B": ColorSettings.MESSAGE_CONTROL_B,
            "A": ColorSettings.MESSAGE_CONTROL_A,
        }

        term_colors = {
            "YOU WERE CAUGHT BY THE MONSTER": ColorSettings.TEXT_LOSS,
            "KEY": ColorSettings.BORDER_KEY_ACTIVE,
            "REPELLENT": ColorSettings.REPELLED_TINT,
            "RUBY": ColorSettings.TREASURE_RUBY,
            "EMERALD": ColorSettings.TREASURE_EMERALD,
            "SAPPHIRE": ColorSettings.TREASURE_SAPPHIRE,
            "GOLD COINS": ColorSettings.TEXT_GOLD,
            "GOLD": ColorSettings.TEXT_GOLD,
            "DOORS": ColorSettings.MESSAGE_DOOR,
            "DOOR": ColorSettings.MESSAGE_DOOR,
        }

        for term, color in FontSettings.WORD_COLORS.items():
            if term in {"MONSTER", "MONSTER REPELLENT", "X", "Y", "B", "A"}:
                continue
            term_colors.setdefault(term, color)

        return sorted(term_colors.items(), key=lambda item: len(item[0]), reverse=True)

    def _default_color_for_message(self, text: str, fallback_color: str) -> str:
        """Return default line color, with custom overrides for warning lines."""
        warning_messages = {
            "YOU HEAR A MONSTER NEARBY!",
            "YOU'VE BEEN SPOTTED BY A MONSTER!",
        }
        if text.upper() in warning_messages:
            return ColorSettings.TEXT_LOSS
        return fallback_color

    def _is_word_char(self, char: str) -> bool:
        """Return whether a character should count as part of a word.

        Args:
            char (str): Character to classify.

        Returns:
            bool: True for alphanumeric characters and underscores.
        """
        return char.isalnum() or char == "_"

    def _has_word_boundaries(self, text: str, index: int, length: int) -> bool:
        """Require non-word boundaries around highlights to avoid partial matches."""
        before_ok = index == 0 or not self._is_word_char(text[index - 1])
        after_index = index + length
        after_ok = after_index >= len(text) or not self._is_word_char(text[after_index])
        return before_ok and after_ok

    def _find_match_at(self, text: str, upper_text: str, index: int) -> tuple[str, str] | None:
        """Find a highlight token that starts at a text index.

        Args:
            text (str): Original mixed-case text.
            upper_text (str): Uppercased version of the same text.
            index (int): Candidate start index.

        Returns:
            tuple[str, str] | None: Matched term and color, or None.
        """
        # Highlight controller labels only in prompt-leading form (for example "A - DIG...").
        if index == 0 and len(text) >= 4 and text[1:4] == " - " and text[0].upper() in self.control_label_colors:
            label = text[0]
            return label, self.control_label_colors[label.upper()]

        for term, color in self.highlight_terms:
            if upper_text.startswith(term, index) and self._has_word_boundaries(text, index, len(term)):
                return term, color
        return None

    def _split_colored_segments(self, text: str, default_color: str) -> list[tuple[str, str]]:
        """Split text into render segments with per-term colors."""
        if not text:
            return []

        segments: list[tuple[str, str]] = []
        upper_text = text.upper()
        index = 0

        while index < len(text):
            match = self._find_match_at(text, upper_text, index)
            if match:
                term, color = match
                segments.append((text[index:index + len(term)], color))
                index += len(term)
                continue

            start = index
            index += 1
            while index < len(text):
                if self._find_match_at(text, upper_text, index):
                    break
                index += 1
            segments.append((text[start:index], default_color))

        return segments

    def _draw_colored_line(self, surface, text: str, x: int, y: int, default_color: str) -> None:
        """Draw one line of text with inline segment coloring.

        Args:
            surface: Target surface for drawing.
            text (str): Text line to render.
            x (int): Start x pixel position.
            y (int): Baseline y pixel position.
            default_color (str): Color used for non-highlighted text.
        """
        effective_default_color = self._default_color_for_message(text, default_color)
        draw_x = x
        for segment_text, segment_color in self._split_colored_segments(text, effective_default_color):
            text_surface = self.font.render(segment_text, False, segment_color)
            surface.blit(text_surface, (draw_x, y))
            draw_x += text_surface.get_width()

    def add_message(self, text, type_speed=None):
        """
        Queue a new active message and start its typewriter animation.

        Args:
            text (str): Message text to display.
            type_speed (float | None): Optional characters-per-frame override.
        """
        # Persist the previous active message before starting a new one.
        if self.full_text:
            self.messages.append(self.full_text)
            if len(self.messages) > WindowSettings.MAX_MESSAGES:
                self.messages.pop(0)

        # Initialize typewriter state for the incoming message.
        self.full_text = text
        self.active_message = ""
        self.char_index = 0
        self.current_type_speed = type_speed if type_speed is not None else self.type_speed
        self.is_typing = True

        # TODO: Refactor message formatting/highlighting rules into a dedicated text presentation utility.

    def draw(self, surface):
        """Render current message history and active typewriter text.

        Args:
            surface: Target surface for the message window.
        """
        # Compute text anchor inside message window.
        start_x = UISettings.LOG_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.LOG_Y + WindowSettings.TEXT_PADDING

        # Draw historical lines.
        for index, message in enumerate(self.messages):
            y_pos = start_y + (index * WindowSettings.LINE_HEIGHT)
            self._draw_colored_line(surface, message, start_x, y_pos, FontSettings.DEFAULT_COLOR)

        # Draw active typewriter line.
        if self.full_text:
            # Place active line directly below message history.
            y_pos = start_y + (len(self.messages) * WindowSettings.LINE_HEIGHT)
            self._draw_colored_line(surface, self.active_message, start_x, y_pos, FontSettings.LAST_MESSAGE_COLOR)

    def update(self):
        """Increments the character count."""
        if self.is_typing:
            self.char_index += self.current_type_speed
            # Clamp slicing by using integer cursor and full-text bounds.
            self.active_message = self.full_text[:int(self.char_index)]
            
            if self.char_index >= len(self.full_text):
                self.is_typing = False

class InventoryWindow:
    """Render the player's inventory list and item-state highlighting."""

    def __init__(self, game):
        """Initialize inventory window rendering dependencies.

        Args:
            game: Active game manager instance.
        """
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def _rainbow_color(self) -> tuple[int, int, int]:
        """Return a dynamic rainbow color for special inventory items.

        Returns:
            tuple[int, int, int]: RGB color tuple.
        """
        hue = (pygame.time.get_ticks() * 0.0002) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
        return int(red * 255), int(green * 255), int(blue * 255)

    def _cloak_glow_color(self) -> tuple[int, int, int]:
        """Return a pulsing glow color for the invisibility cloak label.

        Returns:
            tuple[int, int, int]: RGB color tuple.
        """
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1.0) / 2.0
        min_color = pygame.Color(ColorSettings.CLOAK_GLOW_MIN)
        max_color = pygame.Color(ColorSettings.CLOAK_GLOW_MAX)
        return (
            int(min_color.r + (max_color.r - min_color.r) * pulse),
            int(min_color.g + (max_color.g - min_color.g) * pulse),
            int(min_color.b + (max_color.b - min_color.b) * pulse),
        )

    def _get_item_label_color(self, item: str) -> tuple[int, int, int] | str:
        """Select a display color for an inventory item label.

        Args:
            item (str): Inventory item name.

        Returns:
            tuple[int, int, int] | str: Pygame-compatible color.
        """
        return FontSettings.DEFAULT_COLOR

    def draw(self, surface):
        """Render the player's discovered inventory and counts.

        Args:
            surface: Target surface for the inventory window.
        """
        # Base sidebar text anchors.
        start_x = UISettings.SIDEBAR_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.SIDEBAR_Y + WindowSettings.TEXT_PADDING

        # Inventory header.
        header_surf = self.font.render("INVENTORY", False, ColorSettings.TEXT_TITLE)
        surface.blit(header_surf, (start_x, start_y))

        visual_row = 0
        # TODO: Move inventory spacing literals (-1, +25) to WindowSettings constants.
        tight_line_height = WindowSettings.LINE_HEIGHT - 1

        # Reserve a small gutter on every row for the active-light marker so
        # labels stay aligned whether or not the marker is drawn.
        marker_gutter_surf = self.font.render("> ", False, ColorSettings.TEXT_SELECTOR)
        marker_gutter_width = marker_gutter_surf.get_width()
        active_light_source = self.game.player.selected_light_source

        # Iterate inventory rows while tracking only visible entries.
        for item, count in self.game.player.inventory.items():
            # Render item if owned now or previously discovered.
            has_it = count > 0
            discovered = item in self.game.player.discovered_items

            if has_it or discovered:
                item_color = self._get_item_label_color(item)

                # Render label using item-specific color.
                label_text = f"{item}: "
                label_surf = self.font.render(label_text, False, item_color)

                # Render quantity; zero-count values use error color.
                num_color = ColorSettings.TEXT_ERROR if count <= 0 else FontSettings.DEFAULT_COLOR
                num_surf = self.font.render(str(count), False, num_color)

                # Compute row y-position.
                y_pos = start_y + 25 + (visual_row * tight_line_height)

                # Mark the row whose item is the active B-button light source.
                if item == active_light_source:
                    surface.blit(marker_gutter_surf, (start_x, y_pos))

                # Draw label and quantity in one row, shifted past the gutter.
                label_x = start_x + marker_gutter_width
                surface.blit(label_surf, (label_x, y_pos))
                surface.blit(num_surf, (label_x + label_surf.get_width(), y_pos))

                visual_row += 1

class MapWindow:
    """Render the minimap terrain memory and entity markers."""

    def __init__(self, game):
        """Initialize minimap rendering dependencies.

        Args:
            game: Active game manager instance.
        """
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def draw(self, surface):
        """Render the minimap (or shop label) into the map UI window.

        Args:
            surface: Target surface for map window rendering.
        """
        if self.game.in_shop_phase:
            label_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
            label_surf = label_font.render("ITEM SHOP", False, ColorSettings.TEXT_TITLE)
            label_rect = label_surf.get_rect(center=(
                UISettings.MAP_X + (UISettings.MAP_WIDTH // 2),
                UISettings.MAP_Y + (UISettings.MAP_HEIGHT // 2),
            ))
            surface.blit(label_surf, label_rect)
            return

        # Fit the minimap into available map-window space.
        padding = UISettings.MINIMAP_PADDING
        available_w = UISettings.MAP_WIDTH - (padding * 2)
        available_h = UISettings.MAP_HEIGHT - (padding * 2)
        mini_tile_size = min(
            available_w // UISettings.COLS,
            available_h // UISettings.ROWS,
        )

        map_pixel_w = mini_tile_size * UISettings.COLS
        map_pixel_h = mini_tile_size * UISettings.ROWS

        start_x = UISettings.MAP_X + (UISettings.MAP_WIDTH - map_pixel_w) // 2
        start_y = UISettings.MAP_Y + (UISettings.MAP_HEIGHT - map_pixel_h) // 2

        # Draw remembered terrain cells.
        for r in range(UISettings.ROWS):
            for c in range(UISettings.COLS):
                grid_pos = (c, r)

                if grid_pos in self.game.map_memory.seen_tiles:
                    rect = pygame.Rect(
                        start_x + (c * mini_tile_size),
                        start_y + (r * mini_tile_size),
                        mini_tile_size - 1,
                        mini_tile_size - 1
                    )

                    # TODO: Replace minimap cell inset literal (-1) and line inset literal (1) with UI constants.

                    remembered = self.game.map_memory.seen_tiles[grid_pos]

                    if remembered == "#":
                        color = ColorSettings.MINIMAP_WALL   # wall
                    elif remembered == "o":
                        color = ColorSettings.MINIMAP_DUG     # dug spot
                    else:
                        color = ColorSettings.MINIMAP_FLOOR      # explored dirt/floor

                    pygame.draw.rect(surface, color, rect)

                    if remembered == "o":
                        # Mark dug tiles with a small X for readability.
                        inset = 1
                        pygame.draw.line(
                            surface,
                            ColorSettings.BLACK,
                            (rect.left + inset, rect.top + inset),
                            (rect.right - inset, rect.bottom - inset),
                            1,
                        )
                        pygame.draw.line(
                            surface,
                            ColorSettings.BLACK,
                            (rect.left + inset, rect.bottom - inset),
                            (rect.right - inset, rect.top + inset),
                            1,
                        )

        # Draw last known door position.
        if self.game.map_memory.last_seen_door_pos is not None:
            d_col, d_row = self.game.map_memory.last_seen_door_pos
            pygame.draw.rect(surface, ColorSettings.MINIMAP_DOOR,
                (start_x + (d_col * mini_tile_size),
                start_y + (d_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # Draw remembered monster positions.
        for m_col, m_row in self.game.map_memory.last_seen_monster_pos:
            pygame.draw.rect(surface, ColorSettings.MINIMAP_MONSTER,
                (start_x + (m_col * mini_tile_size),
                start_y + (m_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # Draw player marker while lit, or always with magic map.
        if self.game.map_memory.should_draw_player_on_minimap():
            p_col, p_row = self.game.screen_to_grid(self.game.player.position.x, self.game.player.position.y)
            pygame.draw.rect(surface, ColorSettings.MINIMAP_PLAYER, 
                             (start_x + (p_col * mini_tile_size), 
                              start_y + (p_row * mini_tile_size), 
                              mini_tile_size - 1, mini_tile_size - 1))