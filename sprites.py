import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.image.load(AssetPaths.GRAPHICS_DIR + AssetPaths.PLAYER).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

    def update(self):
        pass