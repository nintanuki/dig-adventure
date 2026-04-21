import pygame
from mapmemory import MapMemory
from settings import UISettings, FontSettings, WindowSettings

class MessageLog:
    def __init__(self, game):
        self.game = game
        self.messages = list(WindowSettings.WELCOME_MESSAGE) 
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

        # Typewriter state
        self.pending_message = None # Holds the message until sprites finish moving
        self.full_text = ""
        self.active_message = ""
        self.char_index = 0
        self.type_speed = WindowSettings.TYPING_SPEED
        self.is_typing = False

    def add_message(self, text):
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
        self.is_typing = True

    def draw(self, surface):
        """Renders the current messages inside the log window."""
        # Calculate starting vertical position inside the Log Box
        start_x = UISettings.LOG_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.LOG_Y + WindowSettings.TEXT_PADDING

        # Draw History (Static white text)
        for index, message in enumerate(self.messages):
            text_surface = self.font.render(message, False, FontSettings.DEFAULT_COLOR)
            surface.blit(text_surface, (start_x, start_y + (index * WindowSettings.LINE_HEIGHT)))

        # Draw Active Message (Typewriter effect in Yellow)
        if self.full_text:
            # Position it right after the last historical message
            y_pos = start_y + (len(self.messages) * WindowSettings.LINE_HEIGHT)
            text_surface = self.font.render(self.active_message, False, FontSettings.LAST_MESSAGE_COLOR)
            surface.blit(text_surface, (start_x, y_pos))

    def update(self):
        """Increments the character count."""
        if self.is_typing:
            self.char_index += self.type_speed
            # Ensure we don't go out of bounds of the string
            self.active_message = self.full_text[:int(self.char_index)]
            
            if self.char_index >= len(self.full_text):
                self.is_typing = False

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def draw(self, surface):
        """Renders the player's inventory items in the sidebar."""
        # Starting coordinates based on Sidebar settings
        start_x = UISettings.SIDEBAR_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.SIDEBAR_Y + WindowSettings.TEXT_PADDING
        
        # Header
        header_surf = self.font.render("INVENTORY", False, 'yellow')
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
                # 1. Render the Label (Always White)
                label_text = f"{item}: "
                label_surf = self.font.render(label_text, False, FontSettings.DEFAULT_COLOR)
                
                # 2. Render the Number (Red if 0, otherwise White)
                num_color = 'red' if count <= 0 else FontSettings.DEFAULT_COLOR
                num_surf = self.font.render(str(count), False, num_color)

                # 3. Calculate Positions
                y_pos = start_y + 25 + (visual_row * tight_line_height)
                
                # Blit Label
                surface.blit(label_surf, (start_x, y_pos))
                # Blit Number immediately after the label
                surface.blit(num_surf, (start_x + label_surf.get_width(), y_pos))
                
                visual_row += 1

# windows.py

# windows.py
class MapWindow:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def draw(self, surface):
        # 1. Calculation for centering
        padding = 10
        available_w = UISettings.SIDEBAR_WIDTH - (padding * 2)
        mini_tile_size = available_w // UISettings.COLS
        
        start_x = UISettings.SIDEBAR_X + padding
        start_y = UISettings.MAP_Y + padding

        # Draw Header Got rid of this as it was taking up too much space and the map is pretty self-explanatory
        # header_surf = self.font.render("MINIMAP", False, 'yellow')
        # surface.blit(header_surf, (start_x, UISettings.MAP_Y + padding))

        # 2. Iterate through the grid ONCE
        for r in range(UISettings.ROWS):
            for c in range(UISettings.COLS):
                grid_pos = (c, r)

                if grid_pos in self.game.map_memory.seen_tiles:
                    rect = (
                        start_x + (c * mini_tile_size),
                        start_y + (r * mini_tile_size),
                        mini_tile_size - 1,
                        mini_tile_size - 1
                    )

                    remembered = self.game.map_memory.seen_tiles[grid_pos]

                    if remembered == "#":
                        color = (120, 120, 120)   # wall
                    elif remembered == "o":
                        color = (139, 90, 43)     # dug spot
                    else:
                        color = (50, 50, 50)      # explored dirt/floor

                    pygame.draw.rect(surface, color, rect)

        # draw remembered door
        if self.game.map_memory.last_seen_door_pos:
            d_col, d_row = self.game.map_memory.last_seen_door_pos
            pygame.draw.rect(surface, 'yellow',
                (start_x + (d_col * mini_tile_size),
                start_y + (d_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # draw remembered monster positions
        for m_col, m_row in self.game.map_memory.last_seen_monster_pos:
            pygame.draw.rect(surface, 'red',
                (start_x + (m_col * mini_tile_size),
                start_y + (m_row * mini_tile_size),
                mini_tile_size - 1, mini_tile_size - 1)
            )

        # Draw Player (Ask main.py for the grid conversion)
        p_col, p_row = self.game.screen_to_grid(self.game.player.position.x, self.game.player.position.y)
        pygame.draw.rect(surface, 'blue', 
                         (start_x + (p_col * mini_tile_size), 
                          start_y + (p_row * mini_tile_size), 
                          mini_tile_size - 1, mini_tile_size - 1))