import pygame
import colorsys
import math
from settings import UISettings, FontSettings, WindowSettings, ColorSettings

class MessageLog:
    def __init__(self, game):
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

    def _is_word_char(self, char: str) -> bool:
        return char.isalnum() or char == "_"

    def _has_word_boundaries(self, text: str, index: int, length: int) -> bool:
        """Require non-word boundaries around highlights to avoid partial matches."""
        before_ok = index == 0 or not self._is_word_char(text[index - 1])
        after_index = index + length
        after_ok = after_index >= len(text) or not self._is_word_char(text[after_index])
        return before_ok and after_ok

    def _find_match_at(self, text: str, upper_text: str, index: int) -> tuple[str, str] | None:
        # Highlight controller labels only when they appear as line-leading prompts
        # like "A - DIG..." so regular words are unaffected.
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
        draw_x = x
        for segment_text, segment_color in self._split_colored_segments(text, default_color):
            text_surface = self.font.render(segment_text, False, segment_color)
            surface.blit(text_surface, (draw_x, y))
            draw_x += text_surface.get_width()

    def add_message(self, text, type_speed=None):
        """
        Adds a new message to the log and removes old ones if full.
        Use a typewriter effect for the most recent message, while keeping previous messages static.
        """
        # If there is an active message finishing up, move it to history first
        if self.full_text:
            self.messages.append(self.full_text)
            if len(self.messages) > WindowSettings.MAX_MESSAGES:
                self.messages.pop(0)

        # Set up the new message to be typed
        self.full_text = text
        self.active_message = ""
        self.char_index = 0
        self.current_type_speed = type_speed if type_speed is not None else self.type_speed
        self.is_typing = True

    def draw(self, surface):
        """Renders the current messages inside the log window."""
        # Calculate starting vertical position inside the Log Box
        start_x = UISettings.LOG_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.LOG_Y + WindowSettings.TEXT_PADDING

        # Draw History (Static white text)
        for index, message in enumerate(self.messages):
            y_pos = start_y + (index * WindowSettings.LINE_HEIGHT)
            self._draw_colored_line(surface, message, start_x, y_pos, FontSettings.DEFAULT_COLOR)

        # Draw Active Message (Typewriter effect in Yellow)
        if self.full_text:
            # Position it right after the last historical message
            y_pos = start_y + (len(self.messages) * WindowSettings.LINE_HEIGHT)
            self._draw_colored_line(surface, self.active_message, start_x, y_pos, FontSettings.LAST_MESSAGE_COLOR)

    def update(self):
        """Increments the character count."""
        if self.is_typing:
            self.char_index += self.current_type_speed
            # Ensure we don't go out of bounds of the string
            self.active_message = self.full_text[:int(self.char_index)]
            
            if self.char_index >= len(self.full_text):
                self.is_typing = False

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def _rainbow_color(self) -> tuple[int, int, int]:
        hue = (pygame.time.get_ticks() * 0.0002) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
        return int(red * 255), int(green * 255), int(blue * 255)

    def _cloak_glow_color(self) -> tuple[int, int, int]:
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1.0) / 2.0
        min_color = pygame.Color(ColorSettings.CLOAK_GLOW_MIN)
        max_color = pygame.Color(ColorSettings.CLOAK_GLOW_MAX)
        return (
            int(min_color.r + (max_color.r - min_color.r) * pulse),
            int(min_color.g + (max_color.g - min_color.g) * pulse),
            int(min_color.b + (max_color.b - min_color.b) * pulse),
        )

    def _get_item_label_color(self, item: str) -> tuple[int, int, int] | str:
        if item == 'RUBY':
            return ColorSettings.TREASURE_RUBY
        if item == 'SAPPHIRE':
            return ColorSettings.TREASURE_SAPPHIRE
        if item == 'EMERALD':
            return ColorSettings.TREASURE_EMERALD
        if item == 'DIAMOND':
            return ColorSettings.TREASURE_DIAMOND
        if item == 'INVISIBILITY CLOAK':
            return self._cloak_glow_color()
        if item == 'MAGIC MAP':
            return self._rainbow_color()
        if item == 'KEY':
            return ColorSettings.BORDER_KEY_ACTIVE
        if item == 'GOLD COINS':
            return ColorSettings.TEXT_GOLD
        if item == 'MONSTER REPELLENT':
            return ColorSettings.REPELLED_TINT
        return FontSettings.DEFAULT_COLOR

    def draw(self, surface):
        """Renders the player's inventory items in the sidebar."""
        # Starting coordinates based on Sidebar settings
        start_x = UISettings.SIDEBAR_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.SIDEBAR_Y + WindowSettings.TEXT_PADDING
        
        # Header
        header_surf = self.font.render("INVENTORY", False, ColorSettings.TEXT_TITLE)
        surface.blit(header_surf, (start_x, start_y))

        visual_row = 0
        tight_line_height = WindowSettings.LINE_HEIGHT - 1

        # Loop through the player's inventory dictionary
        # Use a counter for visual row indexing, as we might skip some items
        for item, count in self.game.player.inventory.items():
            # LOGIC: Only show if they have it OR if they've found it before
            has_it = count > 0
            discovered = item in self.game.player.discovered_items

            if has_it or discovered:
                item_color = self._get_item_label_color(item)

                # 1. Render the Label (Syntax-highlight item names)
                label_text = f"{item}: "
                label_surf = self.font.render(label_text, False, item_color)
                
                # 2. Render the Number (Red if 0, otherwise default white)
                num_color = ColorSettings.TEXT_ERROR if count <= 0 else FontSettings.DEFAULT_COLOR
                num_surf = self.font.render(str(count), False, num_color)

                # 3. Calculate Positions
                y_pos = start_y + 25 + (visual_row * tight_line_height)
                
                # Blit Label
                surface.blit(label_surf, (start_x, y_pos))
                # Blit Number immediately after the label
                surface.blit(num_surf, (start_x + label_surf.get_width(), y_pos))
                
                visual_row += 1

class MapWindow:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def draw(self, surface):
        if self.game.is_in_shop_phase:
            label_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
            label_surf = label_font.render("ITEM SHOP", False, ColorSettings.TEXT_TITLE)
            label_rect = label_surf.get_rect(center=(
                UISettings.MAP_X + (UISettings.MAP_WIDTH // 2),
                UISettings.MAP_Y + (UISettings.MAP_HEIGHT // 2),
            ))
            surface.blit(label_surf, label_rect)
            return

        # Fit the minimap into the map window and center it.
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

        # 2. Iterate through the grid ONCE
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

                    remembered = self.game.map_memory.seen_tiles[grid_pos]

                    if remembered == "#":
                        color = ColorSettings.MINIMAP_WALL   # wall
                    elif remembered == "o":
                        color = ColorSettings.MINIMAP_DUG     # dug spot
                    else:
                        color = ColorSettings.MINIMAP_FLOOR      # explored dirt/floor

                    pygame.draw.rect(surface, color, rect)

                    if remembered == "o":
                        # Draw a small X so dug tiles are easy to distinguish.
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

        # draw remembered door
        if self.game.map_memory.last_seen_door_pos is not None:
            d_col, d_row = self.game.map_memory.last_seen_door_pos
            pygame.draw.rect(surface, ColorSettings.MINIMAP_DOOR,
                (start_x + (d_col * mini_tile_size),
                start_y + (d_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # draw remembered monster positions
        for m_col, m_row in self.game.map_memory.last_seen_monster_pos:
            pygame.draw.rect(surface, ColorSettings.MINIMAP_MONSTER,
                (start_x + (m_col * mini_tile_size),
                start_y + (m_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # Draw player while lit, or always with the magic map radar.
        if self.game.map_memory.should_draw_player_on_minimap():
            p_col, p_row = self.game.screen_to_grid(self.game.player.position.x, self.game.player.position.y)
            pygame.draw.rect(surface, ColorSettings.MINIMAP_PLAYER, 
                             (start_x + (p_col * mini_tile_size), 
                              start_y + (p_row * mini_tile_size), 
                              mini_tile_size - 1, mini_tile_size - 1))