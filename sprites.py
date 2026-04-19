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

    def get_input_direction(self):
        """
        Handle player input for movement,
        including both keyboard and controller input.

        Returns:
            horizontal_step (int): The number of steps to move horizontally.
            vertical_step (int): The number of steps to move vertically.
        """
        keys = pygame.key.get_pressed()
        horizontal_step = 0 # 0 means no movement, but we are also initializing here
        vertical_step = 0

        # current_time = pygame.time.get_ticks()
        # # Only allow movement if enough time has passed since the last move
        # if current_time - self.last_move_time < self.move_cooldown:
        #     return

        # Movement is based on grid snapping, so the player moves in increments of the tile size.

        # Keyboard check
        if keys[pygame.K_UP] or keys[pygame.K_w]:    vertical_step = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: vertical_step = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]: horizontal_step = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: horizontal_step = 1

        # Controller D-Pad check
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            dpad_direction = joystick.get_hat(0)
            # Only override if the d-pad is actually being touched
            if dpad_direction[0] != 0: horizontal_step = dpad_direction[0]
            if dpad_direction[1] != 0: vertical_step = -dpad_direction[1]

        return horizontal_step, vertical_step

    def process_movement_input(self):
        """Checks the timer and input before deciding to move."""
        current_time = pygame.time.get_ticks()
        
        # 1. Check if enough time has passed (The Cooldown)
        if current_time - self.time_of_last_move >= self.move_cooldown_milliseconds:
            
            # 2. Get the direction the player wants to go
            horizontal_step, vertical_step = self.get_input_direction()
            
            # 3. If there is input, execute the movement and reset the timer
            if horizontal_step != 0 or vertical_step != 0:
                self.apply_grid_snap_movement(horizontal_step, vertical_step)
                self.time_of_last_move = current_time

    def move(self, horizontal_step=0, vertical_step=0):
        """
        The actual math that moves the player exactly one tile.
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
        self.process_movement_input()