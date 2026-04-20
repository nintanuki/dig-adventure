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
        # Load the player image and armor pieces, then scale them to fit the grid.
        self.image = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.image = pygame.transform.scale(self.image, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        # Set the rect's top-left corner to the given position
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft) # Using Vector2 for easier movement calculations

        # Cooldown Timer (in milliseconds) so the player can't spam movement input
        self.move_cooldown = PlayerSettings.MOVEMENT_COOLDOWN
        self.time_of_last_move = 0

        self.inventory = ItemSettings.INITIAL_INVENTORY.copy()
        self.discovered_items = set(self.inventory.keys())
        
        self.repellent_turns = 0

        self.light_radius = LightSettings.DEFAULT_RADIUS
        self.light_turns_left = 0
        self.active_light_max_radius = 0
        self.active_light_max_duration = 0

        # Animation states for smooth movement
        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED

        self.game = game # Reference to the game manager for accessing shared resources like the audio manager

    def get_input(self):
        """
        Handle player input for movement,
        including both keyboard and controller input.

        Returns:
            horizontal_step (int): The number of steps to move horizontally. -1, 0, or 1
            vertical_step (int): The number of steps to move vertically. -1, 0, or 1
            action_type (str): 'move', 'dig', 'detector', 'light', 'repellent', or None
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
        elif keys[pygame.K_SPACE]: action_type = 'dig'
        elif keys[pygame.K_e]: action_type = 'detector'
        elif keys[pygame.K_t]: action_type = 'light'
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
            # 0:A (Dig), 1:B (Light), 2:X (Detector), 3:Y (Repellent)
            if action_type is None:
                if joystick.get_button(0): action_type = 'dig'
                elif joystick.get_button(1): action_type = 'light'
                elif joystick.get_button(2): action_type = 'detector'
                elif joystick.get_button(3): action_type = 'repellent'

        return horizontal_step, vertical_step, action_type

    def apply_grid_snap_movement(self, horizontal_step=0, vertical_step=0):
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + horizontal_step
        target_row = current_row + vertical_step

        if self.game.is_walkable(target_col, target_row):
            target_x, target_y = self.game.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

            if vertical_step == -1:
                self.game.log_message("YOU MOVED NORTH.")
            elif vertical_step == 1:
                self.game.log_message("YOU MOVED SOUTH.")
            elif horizontal_step == -1:
                self.game.log_message("YOU MOVED WEST.")
            elif horizontal_step == 1:
                self.game.log_message("YOU MOVED EAST.")

            self.game.audio.play_move_sound()
            self.game.advance_turn()
        else:
            self.game.log_message("YOU CAN'T GO THAT WAY!")
            self.game.audio.play_boundary_sound()

    def process_movement_and_actions(self):
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

            elif action == 'light':
                # Setup helper variables to avoid repeating code
                light_source = None
                if self.inventory.get('LANTERN', 0) > 0:
                    light_source = ('LANTERN', LightSettings.LANTERN_RADIUS, LightSettings.LANTERN_DURATION)
                elif self.inventory.get('TORCH', 0) > 0:
                    light_source = ('TORCH', LightSettings.TORCH_RADIUS, LightSettings.TORCH_DURATION)
                elif self.inventory.get('MATCH', 0) > 0:
                    light_source = ('MATCH', LightSettings.MATCH_RADIUS, LightSettings.MATCH_DURATION)

                if light_source:
                    name, radius, duration = light_source
                    self.inventory[name] -= 1
                    
                    # Store the "Max" values for the shrinking math
                    self.active_light_max_radius = radius
                    self.active_light_max_duration = duration
                    self.light_radius = radius
                    self.light_turns_left = duration + 1 # fix off by one error
                    
                    if self.inventory.get("MAP", 0) > 0:
                        self.game.refresh_map_snapshot()
                        self.game.log_message(f"YOU LIGHT A {name.upper()}, YOU CHECK YOUR MAP.")
                    else:
                        self.game.log_message(f"YOU LIGHT A {name.upper()}!")
                    self.game.advance_turn()
                else:
                    self.game.log_message("YOU HAVE NO LIGHT SOURCES!")
                self.time_of_last_move = current_time

            elif action == 'detector':
                if self.inventory.get('KEY DETECTOR', 0) > 0:
                    self.use_key_detector()
                    self.game.advance_turn()
                else:
                    self.game.log_message("YOU DON'T HAVE A KEY DETECTOR!")
                self.time_of_last_move = current_time

            elif action == 'repellent':
                if self.inventory.get('MONSTER REPELLENT', 0) > 0:
                    self.inventory['MONSTER REPELLENT'] -= 1
                    self.repellent_turns = MonsterSettings.REPELLENT_DURATION + 1 # this should really be in ItemSettings
                    self.game.log_message("YOU SPRAY THE REPELLENT.")
                    # self.game.audio.play_repellent_sound() # doesn't exist yet
                    self.game.advance_turn()
                else:
                    self.game.log_message("YOU HAVE NO MONSTER REPELLENT LEFT!")
                self.time_of_last_move = current_time

    def dig(self):
        if self.position == self.game.door.position:
            if self.inventory.get('KEY', 0) > 0:
                self.game.door.open_door()
                self.game.log_message("YOU USE THE KEY AND ESCAPE THE DUNGEON!")
                self.game.game_active = False
            else:
                self.game.log_message("THE DOOR IS LOCKED. YOU NEED A KEY!")
                self.game.audio.play_boundary_sound()
            return

        grid_pos = self.game.screen_to_grid(self.position.x, self.position.y)
        tile = self.game.tile_data.get(grid_pos)

        if not tile:
            self.game.log_message("YOU CAN'T DIG HERE.")
            return

        if tile["is_dug"]:
            self.game.log_message("YOU'VE ALREADY DUG HERE.")
            return

        tile["is_dug"] = True
        found_item, amount = self.game.get_item_at_tile(grid_pos)

        if found_item:
            display_name = found_item
            if amount > 1:
                if found_item == "TORCH":
                    display_name = "TORCHES"
                elif found_item == "MATCH":
                    display_name = "MATCHES"
                elif found_item.endswith("Y"):
                    display_name = found_item[:-1] + "IES"
                elif not found_item.endswith("S"):
                    display_name = found_item + "S"

            if amount > 1:
                self.game.log_message(f"YOU FOUND {amount} {display_name}!")
            else:
                self.game.log_message(f"YOU FOUND A {found_item}!")

            if found_item == "KEY":
                self.game.audio.play_key_sound()

            if found_item:
                # Add it to the inventory (create it if it doesn't exist)
                self.inventory[found_item] = self.inventory.get(found_item, 0) + amount
                # Add it to discovered_items so the window draws it
                self.discovered_items.add(found_item)
        else:
            self.game.log_message("NOTHING BUT DIRT HERE.")
        self.game.audio.play_dig_sound()
        self.game.advance_turn()

    def use_key_detector(self):
        """Calculates distance to key and logs proximity message."""
        # Current player grid position
        p_x = int((self.position.x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE)
        p_y = int((self.position.y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE)
        
        # Key grid position (from main.py)
        k_x, k_y = self.game.key_grid_pos
        
        # Manhattan Distance: |x1 - x2| + |y1 - y2|
        distance = abs(p_x - k_x) + abs(p_y - k_y)

        if distance == 0:
            self.game.log_message("THE KEY DETECTOR IS GOING WILD!")
        elif distance == 1:
            self.game.log_message("THE KEY DETECTOR BEEPS RAPIDLY!")
        elif distance <= 3:
            self.game.log_message("THE KEY DETECTOR GIVES A STEADY PULSE...")
        else:
            # "Dead silent" for anything further than 3 steps
            self.game.log_message("THE KEY DETECTOR IS SILENT.")

    def animate(self):
        """Handles the animation of the player sprite when moving."""
        if self.is_moving:
            # Calculate the direction vector towards the target position
            direction = self.target_pos - self.position
            distance = direction.length()

            if distance < self.anim_speed:
                # If we're close enough to the target, snap to it and stop moving
                self.position = self.target_pos
                self.rect.topleft = self.position # Update the rect's position to match the new position
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = self.position

    def update(self):
        """Update the player's state. This method is called every frame."""
        if not self.is_moving:
            self.process_movement_and_actions()

class Monster(pygame.sprite.Sprite):
    def __init__(self, game, position, groups):
        super().__init__(groups)
        self.game = game
        
        # Load and scale the monster image
        surface = pygame.image.load(AssetPaths.MONSTER).convert_alpha()
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED
        self.is_chasing = False

    def take_turn(self):
        """Determines the monster's behavior each turn, including chasing the player if they are close enough."""
       
        # Check if the monster is currently repelled
        is_repelled = self.game.player.repellent_turns > 0

        # Calculate the Manhattan distance to the player
        horizontal_difference = self.game.player.position.x - self.position.x
        vertical_difference = self.game.player.position.y - self.position.y
        manhattan_distance = (abs(horizontal_difference) // GridSettings.TILE_SIZE) + (abs(vertical_difference) // GridSettings.TILE_SIZE)

        # If the monster is repelled, it will try to move away from the player instead of towards them.
        if is_repelled:
            self.is_chasing = False
            move_horizontal = 0
            move_vertical = 0

            # The logic is basically the same as chasing, but reversed. =
            # The monster will try to move in the direction that increases the distance between itself and the player.
            if abs(horizontal_difference) >= abs(vertical_difference):
                if horizontal_difference > 0:
                    move_horizontal = -GridSettings.TILE_SIZE
                elif horizontal_difference < 0:
                    move_horizontal = GridSettings.TILE_SIZE
                elif vertical_difference > 0:
                    move_vertical = -GridSettings.TILE_SIZE
                elif vertical_difference < 0:
                    move_vertical = GridSettings.TILE_SIZE
            else: # If the player is more vertical than horizontal, prioritize moving vertically to get away
                if vertical_difference > 0:
                    move_vertical = -GridSettings.TILE_SIZE
                elif vertical_difference < 0:
                    move_vertical = GridSettings.TILE_SIZE
                elif horizontal_difference > 0:
                    move_horizontal = -GridSettings.TILE_SIZE
                elif horizontal_difference < 0:
                    move_horizontal = GridSettings.TILE_SIZE

            # After calculating the movement, we apply it.
            # The apply_movement function will handle boundary checks to make sure the monster doesn't move out of bounds.
            self.apply_movement(move_horizontal, move_vertical)
            return

        # If the monster is not repelled, it will check if the player is within its chase radius.
        if manhattan_distance <= MonsterSettings.CHASE_RADIUS:
            self.is_chasing = True

        # If the monster is chasing, it will try to move towards the player. Otherwise, it will move randomly or idle.
        if self.is_chasing:
            move_horizontal = 0
            move_vertical = 0

            # The monster will prioritize moving in the direction where the player is farther away,
            # to close the distance more efficiently.
            # This is the same logic as the repellent, but instead of moving away from the player, it moves towards them.
            # Can this be moved into a function since it's so similar? But the signs are different...
            if abs(horizontal_difference) >= abs(vertical_difference):
                if horizontal_difference > 0:
                    move_horizontal = GridSettings.TILE_SIZE
                elif horizontal_difference < 0:
                    move_horizontal = -GridSettings.TILE_SIZE
                elif vertical_difference > 0:
                    move_vertical = GridSettings.TILE_SIZE
                elif vertical_difference < 0:
                    move_vertical = -GridSettings.TILE_SIZE
            else:
                if vertical_difference > 0:
                    move_vertical = GridSettings.TILE_SIZE
                elif vertical_difference < 0:
                    move_vertical = -GridSettings.TILE_SIZE
                elif horizontal_difference > 0:
                    move_horizontal = GridSettings.TILE_SIZE
                elif horizontal_difference < 0:
                    move_horizontal = -GridSettings.TILE_SIZE

            # After calculating the movement, we apply it.
            self.apply_movement(move_horizontal, move_vertical)
            return

        # If the monster is not chasing, it has a chance to move randomly or do nothing (idle).
        if random.random() > MonsterSettings.IDLE_CHANCE:
            self.move_randomly()

    def move_randomly(self):
        """Picks a random cardinal direction."""
        direction = random.choice(['up', 'down', 'left', 'right'])
        step_x, step_y = 0, 0
        if direction == 'up': step_y = -GridSettings.TILE_SIZE
        elif direction == 'down': step_y = GridSettings.TILE_SIZE
        elif direction == 'left': step_x = -GridSettings.TILE_SIZE
        elif direction == 'right': step_x = GridSettings.TILE_SIZE
        
        self.apply_movement(step_x, step_y)

    def apply_movement(self, horizontal_amount, vertical_amount):
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + (horizontal_amount // GridSettings.TILE_SIZE)
        target_row = current_row + (vertical_amount // GridSettings.TILE_SIZE)

        if self.game.is_walkable(target_col, target_row):
            target_x, target_y = self.game.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

    def animate(self):
        """The visual sliding logic."""
        if self.is_moving:
            direction = self.target_pos - self.position
            if direction.length() < self.anim_speed:
                self.position = self.target_pos
                self.rect.topleft = self.position
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
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