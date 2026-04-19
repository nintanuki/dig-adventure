import pygame
import sys
import json

import debug
from settings import *
from sprites import Player

class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Dig Adventure')
        self.clock = pygame.time.Clock()

        # Controller Setup
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

        # Pre-load dirt asset to avoid loading it 60 times per second
        dirt_tile = pygame.image.load(AssetPaths.DIRT_TILE).convert_alpha()
        self.scaled_dirt_tile = pygame.transform.scale(dirt_tile, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        # Create a group to hold all sprites
        self.all_sprites = pygame.sprite.Group()
        
        # Instantiate player and add to the group
        # (Starting at 0,0 for now)
        self.player = Player((0,0), self.all_sprites)

    def draw_grid_background(self):
        """Loops through the screen and draws the dirt tiles with grey outlines."""
        for x_pixels in range(0, ScreenSettings.WIDTH, GridSettings.TILE_SIZE):
            for y_pixels in range(0, ScreenSettings.HEIGHT, GridSettings.TILE_SIZE):
                # Draw the dirt tile
                self.screen.blit(self.scaled_dirt_tile, (x_pixels, y_pixels))
                
                # Draw the faint grey grid lines
                tile_outline = pygame.Rect(x_pixels, y_pixels, GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
                pygame.draw.rect(self.screen, (60, 60, 60), tile_outline, 1)

    def run(self):
        """
        Run the game loop.
        """
        # Main game loop
        while True:
            # Event Handling
            for event in pygame.event.get():
                # Handle quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Handle fullscreen toggle with F11 key
                if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            pygame.display.toggle_fullscreen()
            
            self.all_sprites.update() # Update all sprites (calls their update method, if they have one)
            
            # Drawing
            self.screen.fill('black')
            self.draw_grid_background() # Draw the grid background
            self.all_sprites.draw(self.screen) # Draw all sprites to the screen

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()