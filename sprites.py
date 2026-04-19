import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, position, groups):
        """
        Initialize the player sprite.

        Args:
            position (tuple): The initial position of the player.
            groups (list): A list of sprite groups this sprite belongs to.
        """
        super().__init__(groups)
        surface = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        # Scale the image according to the tile size defined in settings, so it fits the grid.
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        # Set the rect's top-left corner to the given position
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft) # Using Vector2 for easier movement calculations

        # Cooldown Timer (in milliseconds) so the player can't spam movement input
        self.move_cooldown = 2000
        self.last_move_time = 0

    def controls(self):
        """Handle player input for movement."""
        keys = pygame.key.get_pressed()

        current_time = pygame.time.get_ticks()
        # Only allow movement if enough time has passed since the last move
        if current_time - self.last_move_time < self.move_cooldown:
            return

        # Movement is based on grid snapping, so the player moves in increments of the tile size.
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.move(vertical_step=-1)
            self.last_move_time = current_time
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.move(vertical_step=1)
            self.last_move_time = current_time
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move(horizontal_step=-1)
            self.last_move_time = current_time
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move(horizontal_step=1)
            self.last_move_time = current_time

    def move(self, horizontal_step=0, vertical_step=0):
        """
        Move the player by a certain number of steps
        in the horizontal and vertical directions,
        based on the tile size defined in settings.

        Args:
            horizontal_step (int, optional): _description_. Defaults to 0.
            vertical_step (int, optional): _description_. Defaults to 0.
        """
        # Update the player's position based on the steps and tile size
        self.position.x += horizontal_step * GridSettings.TILE_SIZE
        self.position.y += vertical_step * GridSettings.TILE_SIZE

        # Update the rect's position to match the new position
        self.rect.topleft = self.position

    def update(self):
        """Update the player's state. This method is called every frame."""
        self.controls()