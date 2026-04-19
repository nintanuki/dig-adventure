import pygame
import random
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

        self.inventory = {
        'Gold': 0, 'Ruby': 0, 'Diamond': 0, 'Emerald': 0,
        'Torch': 2, 'Lantern': 0, 'Monster Repellent': 0,
        'Key': 0, 'Shovel': 1, 'Map': 1
        }

        self.game = game # Reference to the game manager for accessing shared resources like the audio manager

    def get_input(self):
        """
        Handle player input for movement,
        including both keyboard and controller input.

        Returns:
            horizontal_step (int): The number of steps to move horizontally. -1, 0, or 1
            vertical_step (int): The number of steps to move vertically. -1, 0, or 1
            action_type (str): 'move', 'dig', 'map', 'torch', 'repellent', or None
        """
        keys = pygame.key.get_pressed()
        horizontal_step = 0 # 0 means no movement, but we are also initializing here
        vertical_step = 0
        action_type = None

        # Movement is based on grid snapping, so the player moves in increments of the tile size.
        # Keyboard check
        if keys[pygame.K_UP] or keys[pygame.K_w]:    vertical_step = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: vertical_step = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]: horizontal_step = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: horizontal_step = 1

        if horizontal_step != 0 or vertical_step != 0:
            action_type = 'move'

        # Action Keys (Mnemonic)
        elif keys[pygame.K_d]: action_type = 'dig'
        elif keys[pygame.K_m]: action_type = 'map'
        elif keys[pygame.K_t]: action_type = 'torch'
        elif keys[pygame.K_r]: action_type = 'repellent'

        # Controller check
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            
            # D-Pad (Movement)
            dpad_direction = joystick.get_hat(0)
            # Only override if the d-pad is actually being touched
            if dpad_direction[0] != 0 or dpad_direction[1] != 0:
                horizontal_step = dpad_direction[0]
                vertical_step = -dpad_direction[1]
                action_type = 'move'

            # Buttons (Actions)
            # 0:A (Dig), 1:B (Torch), 2:X (Map), 3:Y (Repellent)
            if action_type is None:
                if joystick.get_button(0): action_type = 'dig'
                elif joystick.get_button(1): action_type = 'torch'
                elif joystick.get_button(2): action_type = 'map'
                elif joystick.get_button(3): action_type = 'repellent'

        return horizontal_step, vertical_step, action_type

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
            
            # Log messages for movement
            if vertical_step == -1: self.game.log_message("You move one pace North.")
            elif vertical_step == 1: self.game.log_message("You move one pace South.")
            elif horizontal_step == -1: self.game.log_message("You move one pace West.")
            elif horizontal_step == 1: self.game.log_message("You move one pace East.")

            self.game.audio.play_move_sound() # Play the movement sound effect
            self.game.advance_turn()
        else:
            # ...if the move is invalid (e.g., out of bounds), don't update the position and instead
            self.game.log_message("You can't go that way!")
            self.game.audio.play_boundary_sound() # play a sound effect to indicate the collision

    def process_movement(self):
        """Checks the timer and input before deciding to move."""
        current_time = pygame.time.get_ticks()
        
        # Check if enough time has passed (The Cooldown)
        if current_time - self.time_of_last_move >= self.move_cooldown:
            # Get the direction the player wants to go
            horizontal_step, vertical_step, action = self.get_input()
            # If there is input, execute the movement and reset the timer
            if action == 'move':
                self.apply_grid_snap_movement(horizontal_step, vertical_step)
                self.time_of_last_move = current_time

            elif action == 'dig':
                self.dig()
                # advance turn is handled in the dig function because
                # we need to check if the player already dug there
                # self.game.advance_turn()
                self.time_of_last_move = current_time

            elif action == 'map':
                self.game.log_message("You check your map...")
                self.game.advance_turn()
                self.time_of_last_move = current_time

            elif action == 'torch':
                self.game.log_message("You light a torch!")
                self.game.advance_turn()
                self.time_of_last_move = current_time

            elif action == 'repellent':
                self.game.log_message("You used a monster repellent!")
                self.game.advance_turn()
                self.time_of_last_move = current_time

    def dig(self):
        """Perform a dig action on the current tile."""
        # Convert pixel position back to grid coordinates
        grid_x = int((self.position.x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE)
        grid_y = int((self.position.y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE)
        grid_pos = (grid_x, grid_y)

        tile = self.game.tile_data.get(grid_pos)

        if tile:
            if tile['is_dug']:
                self.game.log_message("You've already dug here.")
            else:
                tile['is_dug'] = True
                
                # Ask the game manager what is here (it checks Key first, then SPAWN_CHANCE)
                found_item = self.game.get_item_at_tile(grid_pos)

                # Then check to see if it's worth something
                if found_item:
                    self.game.log_message(f"You found a {found_item}!")
                    # Update inventory
                    if found_item in self.inventory:
                        self.inventory[found_item] += 1

                    # # Add to score when that part is ready
                    # if found_item in ItemSettings.TREASURE_VALUES:
                    #     self.score += ItemSettings.TREASURE_VALUES[found_item]
                else:
                    # if None is returned from game.get_item_at_tile
                    self.game.log_message("Nothing but dirt here.")
                
                self.game.advance_turn() # Digging costs a turn

    def update(self):
        """Update the player's state. This method is called every frame."""
        self.process_movement()

class Monster(pygame.sprite.Sprite):
    def __init__(self, game, position, groups):
        super().__init__(groups)
        self.game = game
        
        # Load and scale the monster image
        surface = pygame.image.load(AssetPaths.MONSTER).convert_alpha()
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

    def take_turn(self):
        """Logic for the monster's turn."""
        # 1. 25% chance to do nothing (Idling)
        if random.random() < 0.25:
            return

        # 2. Pick a random direction (-1, 0, or 1)
        horizontal_step = random.choice([-1, 0, 1])
        vertical_step = random.choice([-1, 0, 1])
        
        # Prevent diagonal movement by picking only one axis if both are chosen
        if horizontal_step != 0 and vertical_step != 0:
            if random.random() < 0.5: horizontal_step = 0
            else: vertical_step = 0

        if horizontal_step != 0 or vertical_step != 0:
            self.apply_movement(horizontal_step, vertical_step)

    def apply_movement(self, horizontal_step, vertical_step):
        """Calculate and apply movement with boundary checks."""
        target_x = self.position.x + (horizontal_step * GridSettings.TILE_SIZE)
        target_y = self.position.y + (vertical_step * GridSettings.TILE_SIZE)

        # Boundary Math (Same as Player)
        min_x = UISettings.ACTION_WINDOW_X + GridSettings.TILE_SIZE
        max_x = UISettings.ACTION_WINDOW_X + UISettings.ACTION_WINDOW_WIDTH - (GridSettings.TILE_SIZE * 2)
        min_y = UISettings.ACTION_WINDOW_Y + GridSettings.TILE_SIZE
        max_y = UISettings.ACTION_WINDOW_Y + UISettings.ACTION_WINDOW_HEIGHT - (GridSettings.TILE_SIZE * 2)

        if min_x <= target_x <= max_x and min_y <= target_y <= max_y:
            self.position.x = target_x
            self.position.y = target_y
            self.rect.topleft = self.position

    def update(self):
        """
        I don't think we need this since the monster doesn't take controller input
        and this is not an action game, but I'm leaving it here just in case
        """
        pass

class Door(pygame.sprite.Sprite):
    def __init__(self, game, position, groups):
        super().__init__(groups)
        self.game = game
        
        # Load and scale both versions of the door
        closed_surf = pygame.image.load(AssetPaths.CLOSED_DOOR).convert_alpha()
        open_surf = pygame.image.load(AssetPaths.OPEN_DOOR).convert_alpha()
        
        self.closed_image = pygame.transform.scale(closed_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        self.open_image = pygame.transform.scale(open_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        
        self.image = self.closed_image
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

    def open_door(self):
        self.image = self.open_image

    def update(self):
        pass