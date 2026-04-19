import pygame
# from audio import AudioManager
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, game, position, groups):
        """
        Initialize the player sprite.

        Args:
            game (GameManager): The game manager instance.
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
        self.move_cooldown = PlayerSettings.MOVEMENT_COOLDOWN
        self.time_of_last_move = 0

        self.game = game # Reference to the game manager for accessing shared resources like the audio manager

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

    def apply_grid_snap_movement(self, horizontal_step=0, vertical_step=0):
        """
        The actual math that moves the player exactly one tile.
        Move the player by a certain number of steps
        in the horizontal and vertical directions,
        based on the tile size defined in settings.

        Args:
            horizontal_step (int, optional): _description_. Defaults to 0.
            vertical_step (int, optional): _description_. Defaults to 0.
        """
        
        # 1. Calculate where the player WANTS to go based on the steps and tile size
        # We store this in temporary variables before updating' the player's actual position,
        # so we can check if it's a valid move first.
        target_destination_x = self.position.x + horizontal_step * GridSettings.TILE_SIZE
        target_destination_y = self.position.y + vertical_step * GridSettings.TILE_SIZE

        # 2. Calculate the inner 'dirt' boundaries (excluding the walls)
        # The leftmost dirt tile starts after the anchor + 1 wall tile
        min_safe_x = UISettings.ACTION_WINDOW_X + GridSettings.TILE_SIZE
        # The rightmost dirt tile is the window width minus 2 tiles (the walls on both sides)
        max_safe_x = UISettings.ACTION_WINDOW_X + UISettings.ACTION_WINDOW_WIDTH - (GridSettings.TILE_SIZE * 2)

        min_safe_y = UISettings.ACTION_WINDOW_Y + GridSettings.TILE_SIZE
        max_safe_y = UISettings.ACTION_WINDOW_Y + UISettings.ACTION_WINDOW_HEIGHT - (GridSettings.TILE_SIZE * 2)

        # 3. Check if that target destination is inside the game world boundaries
        if min_safe_x <= target_destination_x <= max_safe_x and \
            min_safe_y <= target_destination_y <= max_safe_y:
            # If it is valid, update the player's position to the new coordinates
            self.position.x = target_destination_x
            self.position.y = target_destination_y
            # Update the rect's position to match the new position OR...
            self.rect.topleft = self.position
            self.game.log_message("You moved!")
            self.game.audio.play_move_sound() # Play the movement sound effect
        else:
            # ...if the move is invalid (e.g., out of bounds), don't update the position and instead
            # play a sound effect to indicate the collision
            self.game.audio.play_boundary_sound()

    def process_movement_input(self):
        """Checks the timer and input before deciding to move."""
        current_time = pygame.time.get_ticks()
        
        # 1. Check if enough time has passed (The Cooldown)
        if current_time - self.time_of_last_move >= self.move_cooldown:
            
            # 2. Get the direction the player wants to go
            horizontal_step, vertical_step = self.get_input_direction()
            
            # 3. If there is input, execute the movement and reset the timer
            if horizontal_step != 0 or vertical_step != 0:
                self.apply_grid_snap_movement(horizontal_step, vertical_step)
                self.time_of_last_move = current_time

    def update(self):
        """Update the player's state. This method is called every frame."""
        self.process_movement_input()