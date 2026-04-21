import pygame
import random
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """
        Initialize the player sprite and its gameplay state.

        This sets up the player's visual sprite, movement state, inventory,
        temporary status effects, and animation data.

        Args:
            game: The active GameManager instance that coordinates the game.
            position (tuple[int, int]): The player's starting screen position.
            groups: Sprite groups this player should be added to.
        """
        super().__init__(groups)
        # Load the player image and armor pieces, then scale them to fit the grid.
        self.image = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.image = pygame.transform.scale(self.image, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        # Set the rect's top-left corner to the given position
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft) # Using Vector2 for easier movement calculations

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
        self.dungeon = self.game.dungeon # Reference to the dungeon for checking tile states during movement and actions

    def get_input(self) -> tuple[int, int, str | None]:
        """
        Read player input and translate it into movement or action intent.

        Checks both keyboard and controller input and returns a single action
        for the current frame.

        Returns:
            tuple[int, int, str | None]: A tuple of
                (horizontal_step, vertical_step, action_type).
                Movement steps are -1, 0, or 1.
                action_type is one of 'move', 'dig', 'detector', 'light',
                'repellent', or None.
        """
        keys = pygame.key.get_pressed()
        horizontal_step = 0 # 0 means no movement, but we are also initializing here
        vertical_step = 0
        action_type: str | None = None

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

    def apply_grid_snap_movement(self, horizontal_step: int = 0, vertical_step: int = 0) -> None:
        """
        Attempt to move the player by one tile.

        If the target tile is walkable, this starts movement animation,
        logs the direction, plays the movement sound, and advances the turn.
        If the target tile is blocked, it logs a boundary message instead.

        Args:
            horizontal_step (int): Horizontal tile step, usually -1, 0, or 1.
            vertical_step (int): Vertical tile step, usually -1, 0, or 1.
        """
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + horizontal_step
        target_row = current_row + vertical_step

        if self.dungeon.is_walkable(target_col, target_row):
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

    def process_movement_and_actions(self) -> None:
        """
        Process one player input action when the player is allowed to act.

        This method gates actions behind the current cooldown/timer logic,
        then dispatches movement, digging, detector use, light use, or repellent use.
        """

        # Get the direction the player wants to go
        horizontal_step, vertical_step, action_type = self.get_input()
        # If there is input, execute the movement and reset the timer
        if action_type == 'move':
            self.apply_grid_snap_movement(int(horizontal_step), int(vertical_step))

        elif action_type == 'dig':
            self.dig()
            # advance turn is handled in the dig function because
            # we need to check if the player already dug there
            # self.game.advance_turn()

        elif action_type == 'light':
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

        elif action_type == 'detector':
            if self.inventory.get('KEY DETECTOR', 0) > 0:
                self.use_key_detector()
                self.game.advance_turn()
            else:
                self.game.log_message("YOU DON'T HAVE A KEY DETECTOR!")

        elif action_type == 'repellent':
            if self.inventory.get('MONSTER REPELLENT', 0) > 0:
                self.inventory['MONSTER REPELLENT'] -= 1
                self.repellent_turns = MonsterSettings.REPELLENT_DURATION + 1 # this should really be in ItemSettings
                self.game.log_message("YOU SPRAY THE REPELLENT.")
                self.game.audio.play_repellent_sound()
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO MONSTER REPELLENT LEFT!")

    def dig(self) -> None:
        """
        Resolve the player's dig action at the current tile.

        If the player is standing on the door, digging becomes an unlock attempt.
        Otherwise, this reveals the tile, resolves any discovered item,
        updates remembered map state, and advances the turn.
        """
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
        tile = self.dungeon.tile_data.get(grid_pos)

        # This should never happen since the player can only be on valid tiles,
        # but we are adding this just in case to prevent crashes.
        if not tile:
            self.game.log_message("YOU CAN'T DIG HERE.")
            return

        if tile["is_dug"]:
            self.game.log_message("YOU'VE ALREADY DUG HERE.")
            return

        tile["is_dug"] = True
        self.game.remember_visible_map_info()
        found_item, amount = self.dungeon.get_item_at_tile(grid_pos)

        # Pluralization logic, which is a bit hacky but it works for now.
        # WE may want to use a helper function later.
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

            if found_item in ["TORCH", "LANTERN", "MATCH"]:
                pass # add a sound for lighting something

            # This can all be collapsed into one treasure/reward sound rule if we are keeping the same sounds for both
            if found_item == "GOLD COINS":
                self.game.audio.play_coin_sound()
            if found_item in ["RUBY", "SAPPHIRE", "EMERALD", "DIAMOND"]:
                self.game.audio.play_coin_sound() # using coin sound for treasures for now
                # change this to something different later

            if found_item:
                # Add it to the inventory (create it if it doesn't exist)
                self.inventory[found_item] = self.inventory.get(found_item, 0) + amount
                # Add it to discovered_items so the window draws it
                self.discovered_items.add(found_item)
        else:
            self.game.log_message("NOTHING BUT DIRT HERE.")
        self.game.audio.play_dig_sound()
        self.game.advance_turn()

    def use_key_detector(self) -> None:
        """
        Check the player's distance from the hidden key and log a hint.

        The detector uses Manhattan distance in grid space and gives stronger
        feedback as the player gets closer.
        """
        # Current player grid position
        player_column = int((self.position.x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE)
        player_row = int((self.position.y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE)
        
        # Key grid position (from main.py)
        key_column, key_row = self.dungeon.key_grid_pos
        
        # Manhattan Distance: |x1 - x2| + |y1 - y2|
        distance = abs(player_column - key_column) + abs(player_row - key_row)

        if distance == 0:
            self.game.log_message("THE KEY DETECTOR IS GOING WILD!")
        elif distance == 1:
            self.game.log_message("THE KEY DETECTOR BEEPS RAPIDLY!")
        elif distance <= 3:
            self.game.log_message("THE KEY DETECTOR GIVES A STEADY PULSE...")
        else:
            # "Dead silent" for anything further than 3 steps
            self.game.log_message("THE KEY DETECTOR IS SILENT.")

    def animate(self) -> None:
        """
        Advance the player's movement animation toward the current target position.

        This keeps the game visually smooth while gameplay still resolves in grid steps.
        """
        if self.is_moving:
            # Calculate the direction vector towards the target position
            direction = self.target_pos - self.position
            distance = direction.length()

            if distance < self.anim_speed:
                # If we're close enough to the target, snap to it and stop moving
                self.position = self.target_pos
                self.rect.topleft = (int(self.position.x), int(self.position.y)) # Update the rect's position to match the new position
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = (int(self.position.x), int(self.position.y))

    def update(self) -> None:
        """
        Update the player's per-frame behavior.

        The player only processes new input when not already moving.
        """
        if not self.is_moving:
            self.process_movement_and_actions()

class Monster(pygame.sprite.Sprite):
    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """
        Initialize the monster sprite and its movement state.

        Sets up the monster's visual representation, position tracking,
        and animation state used for turn-based movement.

        Args:
            game: The active GameManager instance.
            position (tuple[int, int]): Starting screen position.
            groups: Sprite groups this monster belongs to.
        """
        super().__init__(groups)
        self.game = game
        self.dungeon = self.game.dungeon
        
        # Load and scale the monster image
        surface = pygame.image.load(AssetPaths.MONSTER).convert_alpha()
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED
        self.is_chasing = False

    def take_turn(self) -> None:
        """
        Determine the monster's behavior for a single turn.

        The monster can:
        - move away from the player if repelled
        - chase the player if within range and line of sight
        - move randomly or idle otherwise

        Behavior priority:
            1. Repelled → move away
            2. In range + visible → chase
            3. Otherwise → random movement or idle
        """
       
        # Check if the monster is currently repelled
        is_repelled = self.game.player.repellent_turns > 0

        # Calculate the Manhattan distance to the player
        delta_x = self.game.player.position.x - self.position.x
        delta_y = self.game.player.position.y - self.position.y
        manhattan_distance = (abs(delta_x) // GridSettings.TILE_SIZE) + (abs(delta_y) // GridSettings.TILE_SIZE)

        # If the monster is repelled, it will try to move away from the player instead of towards them.
        if is_repelled:
            self.is_chasing = False
            step_x = 0
            step_y = 0

            # The logic is basically the same as chasing, but reversed. =
            # The monster will try to move in the direction that increases the distance between itself and the player.
            if abs(delta_x) >= abs(delta_y):
                if delta_x > 0:
                    step_x = -GridSettings.TILE_SIZE
                elif delta_x < 0:
                    step_x = GridSettings.TILE_SIZE
                elif delta_y > 0:
                    step_y = -GridSettings.TILE_SIZE
                elif delta_y < 0:
                    step_y = GridSettings.TILE_SIZE
            else: # If the player is more vertical than horizontal, prioritize moving vertically to get away
                if delta_y > 0:
                    step_y = -GridSettings.TILE_SIZE
                elif delta_y < 0:
                    step_y = GridSettings.TILE_SIZE
                elif delta_x > 0:
                    step_x = -GridSettings.TILE_SIZE
                elif delta_x < 0:
                    step_x = GridSettings.TILE_SIZE

            # After calculating the movement, we apply it.
            # The apply_movement function will handle boundary checks to make sure the monster doesn't move out of bounds.
            self.apply_movement(step_x, step_y)
            return

        # If the monster is not repelled, it will check if the player is within its chase radius.
        # The monster also needs line of sight to the player to start chasing (can't see through walls).
        if manhattan_distance <= MonsterSettings.CHASE_RADIUS and self.has_line_of_sight():
            # Only play the sound if we weren't already chasing
            if not self.is_chasing:
                self.is_chasing = True
                self.game.audio.play_monster_chase_sound()
        else:
            # Optional: Reset chasing status if they lose the player
            self.is_chasing = False

        # If the monster is chasing, it will try to move towards the player. Otherwise, it will move randomly or idle.
        if self.is_chasing:
            step_x = 0
            step_y = 0

            # The monster will prioritize moving in the direction where the player is farther away,
            # to close the distance more efficiently.
            # This is the same logic as the repellent, but instead of moving away from the player, it moves towards them.
            # Can this be moved into a function since it's so similar? But the signs are different...
            if abs(delta_x) >= abs(delta_y):
                if delta_x > 0:
                    step_x = GridSettings.TILE_SIZE
                elif delta_x < 0:
                    step_x = -GridSettings.TILE_SIZE
                elif delta_y > 0:
                    step_y = GridSettings.TILE_SIZE
                elif delta_y < 0:
                    step_y = -GridSettings.TILE_SIZE
            else:
                if delta_y > 0:
                    step_y = GridSettings.TILE_SIZE
                elif delta_y < 0:
                    step_y = -GridSettings.TILE_SIZE
                elif delta_x > 0:
                    step_x = GridSettings.TILE_SIZE
                elif delta_x < 0:
                    step_x = -GridSettings.TILE_SIZE

            # After calculating the movement, we apply it.
            self.apply_movement(step_x, step_y)
            return

        # If the monster is not chasing, it has a chance to move randomly or do nothing (idle).
        if random.random() > MonsterSettings.IDLE_CHANCE:
            self.move_randomly()

    def move_randomly(self) -> None:
        """
        Move the monster in a random cardinal direction.

        Used when the monster is not actively chasing the player.
        """
        direction = random.choice(['up', 'down', 'left', 'right'])
        step_x, step_y = 0, 0
        if direction == 'up': step_y = -GridSettings.TILE_SIZE
        elif direction == 'down': step_y = GridSettings.TILE_SIZE
        elif direction == 'left': step_x = -GridSettings.TILE_SIZE
        elif direction == 'right': step_x = GridSettings.TILE_SIZE
        
        self.apply_movement(step_x, step_y)

    def apply_movement(self, horizontal_amount: int, vertical_amount: int) -> None:
        """
        Attempt to move the monster by a pixel offset.

        Converts the movement into grid space, checks if the target tile
        is walkable, and starts movement animation if valid.

        Args:
            horizontal_amount (int): Pixel movement in the x direction.
            vertical_amount (int): Pixel movement in the y direction.
        """
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + (horizontal_amount // GridSettings.TILE_SIZE)
        target_row = current_row + (vertical_amount // GridSettings.TILE_SIZE)

        if self.dungeon.is_walkable(target_col, target_row):
            target_x, target_y = self.game.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

    def has_line_of_sight(self) -> bool:
        """
        Check if the monster has a clear path to the player.

        Only straight-line (row or column) visibility is considered.
        Walls block line of sight.

        Returns:
            bool: True if no walls block the view, False otherwise.
        """
        m_col, m_row = self.game.screen_to_grid(self.position.x, self.position.y)
        p_col, p_row = self.game.screen_to_grid(self.game.player.position.x, self.game.player.position.y)

        # Check if they are in the same column
        if m_col == p_col:
            start, end = min(m_row, p_row), max(m_row, p_row)
            for row in range(start + 1, end):
                if not self.dungeon.is_walkable(m_col, row):
                    return False
            return True

        # Check if they are in the same row
        if m_row == p_row:
            start, end = min(m_col, p_col), max(m_col, p_col)
            for col in range(start + 1, end):
                if not self.dungeon.is_walkable(col, m_row):
                    return False
            return True
        return False

    def animate(self) -> None:
        """
        Advance the monster's movement animation toward its target position.
        """
        if self.is_moving:
            direction = self.target_pos - self.position
            if direction.length() < self.anim_speed:
                self.position = self.target_pos
                self.rect.topleft = (int(self.position.x), int(self.position.y))
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = (int(self.position.x), int(self.position.y))

    def update(self):
        """
        Placeholder for per-frame behavior.

        Monster actions are currently turn-based, so this method is unused.
        """
        pass

class Door(pygame.sprite.Sprite):
    def __init__(self, game, position: tuple[int, int], groups) -> None:
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

    def open_door(self) -> None:
        self.image = self.open_image

    def update(self) -> None:
        pass