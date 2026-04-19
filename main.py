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

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.flip()

if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()