import pygame
from settings import UISettings, FontSettings, WindowSettings

class MessageLog:
    def __init__(self, game):
        self.game = game
        self.messages = WindowSettings.WELCOME_MESSAGE
        
        # Load font from settings
        # If you don't have the .ttf file yet, use None for default system font
        self.font = pygame.font.SysFont(FontSettings.FONT, FontSettings.SIZE) 
        self.text_color = pygame.Color('white')

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
            text_surface = self.font.render(message, True, self.text_color)
            surface.blit(text_surface, (start_x, start_y + (index * WindowSettings.LINE_HEIGHT)))