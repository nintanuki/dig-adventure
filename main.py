import pygame
import sys
import json

import debug
from settings import *
from sprites import Player

class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption('Dig Adventure')
        self.clock = pygame.time.Clock()

        # Create a group to hold all sprites
        self.all_sprites = pygame.sprite.Group()
        
        # Instantiate player and add to the group
        # (Starting at 0,0 for now)
        self.player = Player((0,0), self.all_sprites)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.all_sprites.update() # Update all sprites (calls their update method, if they have one)
            
            # Drawing
            self.screen.fill('black')
            self.all_sprites.draw(self.screen) # Draw all sprites to the screen
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()