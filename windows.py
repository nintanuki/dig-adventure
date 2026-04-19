import pygame
from settings import UISettings, FontSettings, WindowSettings

class MessageLog:
    def __init__(self, game):
        self.game = game
        self.messages = WindowSettings.WELCOME_MESSAGE
        
        # Load font from settings
        # If you don't have the .ttf file yet, use None for default system font
        self.font = pygame.font.SysFont(FontSettings.FONT, FontSettings.MESSAGE_SIZE) 

    def add_message(self, text):
        """Adds a new message to the log and removes old ones if full."""
        self.messages.append(text)
        if len(self.messages) > WindowSettings.MAX_MESSAGES:
            self.messages.pop(0) # Remove the oldest message

    def draw(self, surface):
        """Renders the current messages inside the log window."""
        # Calculate starting vertical position inside the Log Box
        start_x = UISettings.LOG_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.LOG_Y + WindowSettings.TEXT_PADDING

        for index, message in enumerate(self.messages):
            # Check if this is the most recent message (the last index)
            is_last = (index == len(self.messages) - 1)

            display_text = f">>> {message}" if is_last else message
            text_color = FontSettings.LAST_MESSAGE_COLOR if is_last else FontSettings.DEFAULT_COLOR

            text_surface = self.font.render(display_text, True, text_color)
            surface.blit(text_surface, (start_x, start_y + (index * WindowSettings.LINE_HEIGHT)))

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont(FontSettings.FONT, FontSettings.MESSAGE_SIZE)

    def draw(self, surface):
        """Renders the player's inventory items in the sidebar."""
        # Starting coordinates based on Sidebar settings
        start_x = UISettings.SIDEBAR_X + WindowSettings.TEXT_PADDING
        start_y = UISettings.SIDEBAR_Y + WindowSettings.TEXT_PADDING
        
        # Header
        header_surf = self.font.render("INVENTORY", True, 'yellow')
        surface.blit(header_surf, (start_x, start_y))

        # Loop through the player's inventory dictionary
        for index, (item, count) in enumerate(self.game.player.inventory.items()):
            item_text = f"{item}: {count}"
            # Offset y-position for each line using LINE_HEIGHT
            text_surf = self.font.render(item_text, True, FontSettings.DEFAULT_COLOR)
            surface.blit(text_surf, (start_x, start_y + 40 + (index * WindowSettings.LINE_HEIGHT)))