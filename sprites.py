import pygame
import random
from typing import Literal
from settings import *

PlayerAction = Literal['move', 'dig', 'detector', 'light', 'repellent', 'cloak']
PlayerIntent = tuple[int, int, PlayerAction | None]

class Player(pygame.sprite.Sprite):
    """Represent the player entity, inventory state, and turn actions."""

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
        # -------- Sprite visuals --------
        player_surf = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.base_image = pygame.transform.scale(player_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        self.image = self.base_image.copy()

        # -------- Position and movement state --------
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        self.inventory = ItemSettings.INITIAL_INVENTORY.copy()
        self.discovered_items = set(self.inventory.keys())
        
        self.repellent_turns = 0
        self.invisibility_turns = 0
        self.flash_frame = 0

        self.light_radius = LightSettings.DEFAULT_RADIUS
        self.light_turns_left = 0
        self.active_light_max_radius = 0
        self.active_light_max_duration = 0

        # -------- Animation state --------
        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED

        # -------- Shared system references --------
        self.game = game
        self.dungeon = self.game.dungeon

    def _normalize_cardinal_step(self, delta_x_tiles: int, delta_y_tiles: int) -> tuple[int, int]:
        """Allow movement on only one axis so diagonal steps are impossible."""
        if delta_x_tiles != 0 and delta_y_tiles != 0:
            # Keep vertical priority to match keyboard input ordering.
            delta_x_tiles = 0
        return delta_x_tiles, delta_y_tiles

    def read_input_intent(self) -> PlayerIntent:
        """
        Read player input and translate it into movement or action intent.

        Checks both keyboard and controller input and returns a single action
        for the current frame.

        Returns:
            PlayerIntent: A tuple of (delta_x_tiles, delta_y_tiles, action).
            Movement deltas are -1, 0, or 1.
            action is one of 'move', 'dig', 'detector', 'light',
            'repellent', or None.
        """
        keys = pygame.key.get_pressed()
        delta_x_tiles = 0
        delta_y_tiles = 0
        action: PlayerAction | None = None

        # -------- Keyboard movement input --------
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            delta_y_tiles = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            delta_y_tiles = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            delta_x_tiles = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            delta_x_tiles = 1

        if delta_x_tiles != 0 or delta_y_tiles != 0:
            action = 'move'

        # -------- Keyboard action input --------
        elif keys[pygame.K_SPACE]:
            action = 'dig'
        elif keys[pygame.K_e]:
            action = 'detector'
        elif keys[pygame.K_t]:
            action = 'light'
        elif keys[pygame.K_r]:
            action = 'repellent'
        elif keys[pygame.K_c]:
            action = 'cloak'

        # -------- Controller movement/action input --------
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            
            # D-pad movement
            dpad_direction = joystick.get_hat(0)
            # Override keyboard movement only when the D-pad is active.
            if dpad_direction[0] != 0 or dpad_direction[1] != 0:
                delta_x_tiles = dpad_direction[0]
                delta_y_tiles = -dpad_direction[1]
                delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
                action = 'move'

            # Controller actions
            if action is None:
                if joystick.get_button(0):
                    action = 'dig'
                elif joystick.get_button(1):
                    action = 'light'
                elif joystick.get_button(2):
                    action = 'detector'
                elif joystick.get_button(3):
                    action = 'repellent'
                elif joystick.get_button(4):
                    action = 'cloak'

        delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
        return delta_x_tiles, delta_y_tiles, action

    def try_move_by_grid_step(self, delta_x_tiles: int = 0, delta_y_tiles: int = 0) -> None:
        """
        Attempt to move the player by one tile.

        If the target tile is walkable, this starts movement animation,
        logs the direction, plays the movement sound, and advances the turn.
        If the target tile is blocked, it logs a boundary message instead.

        Args:
            delta_x_tiles (int): Horizontal tile step, usually -1, 0, or 1.
            delta_y_tiles (int): Vertical tile step, usually -1, 0, or 1.
        """
        delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + delta_x_tiles
        target_row = current_row + delta_y_tiles

        if self.dungeon.is_walkable(target_col, target_row):
            target_x, target_y = self.game.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

            if delta_y_tiles == -1:
                self.game.log_message("YOU MOVED NORTH.")
            elif delta_y_tiles == 1:
                self.game.log_message("YOU MOVED SOUTH.")
            elif delta_x_tiles == -1:
                self.game.log_message("YOU MOVED WEST.")
            elif delta_x_tiles == 1:
                self.game.log_message("YOU MOVED EAST.")

            self.game.audio.play_move_sound()
            self.game.advance_turn()
        else:
            self.game.log_message("YOU CAN'T GO THAT WAY!")
            self.game.audio.play_boundary_sound()

    def process_turn_action(self) -> None:
        """
        Process one player input action when the player is allowed to act.

        This method gates actions behind the current cooldown/timer logic,
        then dispatches movement, digging, detector use, light use, or repellent use.
        """

        # Get the direction the player wants to go
        delta_x_tiles, delta_y_tiles, action = self.read_input_intent()
        # If there is input, execute the movement and reset the timer
        if action == 'move':
            self.try_move_by_grid_step(int(delta_x_tiles), int(delta_y_tiles))

        elif action == 'dig':
            self.dig_current_tile()
            # Turn advancement is handled inside dig_current_tile().

        elif action == 'light':
            # Select the best available light source by priority.
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
                
                # Preserve source max values for per-turn radius decay.
                self.active_light_max_radius = radius
                self.active_light_max_duration = duration
                self.light_radius = radius
                # TODO: Move turn-buffer literal (+1) into a named gameplay constant.
                self.light_turns_left = duration + 1 # fix off by one error
                
                if self.inventory.get("MAGIC MAP", 0) > 0:
                    self.game.map_memory.remember_visible_map_info()
                self.game.log_message(f"YOU LIGHT A {name.upper()}!")
                if name == 'MATCH':
                    self.game.audio.play_match_light_sound()
                else:
                    self.game.audio.play_light_sound()
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO LIGHT SOURCES!")

        elif action == 'detector':
            if self.inventory.get('KEY DETECTOR', 0) > 0:
                self.activate_key_detector()
                self.game.advance_turn()
            else:
                self.game.log_message("YOU DON'T HAVE A KEY DETECTOR!")

        elif action == 'repellent':
            if self.inventory.get('MONSTER REPELLENT', 0) > 0:
                self.inventory['MONSTER REPELLENT'] -= 1
                # TODO: Move repellent turn-buffer literal (+1) into a named gameplay constant.
                self.repellent_turns = MonsterSettings.REPELLENT_DURATION + 1
                self.game.log_message("YOU SPRAY THE REPELLENT.")
                self.game.audio.play_repellent_sound(self.inventory['MONSTER REPELLENT'])
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO MONSTER REPELLENT LEFT!")

        elif action == 'cloak':
            if self.inventory.get('INVISIBILITY CLOAK', 0) <= 0:
                self.game.log_message("YOU DON'T HAVE AN INVISIBILITY CLOAK!")
            else:
                self.inventory['INVISIBILITY CLOAK'] -= 1
                if self.inventory['INVISIBILITY CLOAK'] <= 0:
                    self.inventory.pop('INVISIBILITY CLOAK', None)

                # TODO: Move invisibility turn-buffer literal (+1) into a named gameplay constant.
                self.invisibility_turns = ItemSettings.INVISIBILITY_CLOAK_DURATION + 1
                self.game.log_message("YOU WRAP YOURSELF IN THE INVISIBILITY CLOAK.")
                self.game.audio.play_vanish_sound()
                self.game.advance_turn()

    def dig_current_tile(self) -> None:
        """
        Resolve the player's dig action at the current tile.

        If the player is standing on the door, digging becomes an unlock attempt.
        Otherwise, this reveals the tile, resolves any discovered item,
        updates remembered map state, and advances the turn.
        """
        if self.position == self.game.door.position:
            if self.inventory.get('KEY', 0) > 0:
                self.game.door.open_door()
                self.game.handle_door_unlock()
            else:
                self.game.log_message("THE DOOR IS LOCKED. YOU NEED A KEY!")
                self.game.audio.play_boundary_sound()
            return

        tile_grid_pos = self.game.screen_to_grid(self.position.x, self.position.y)
        tile_state = self.dungeon.tile_data.get(tile_grid_pos)

        # Guard against invalid tile state to avoid runtime failure.
        if not tile_state:
            self.game.log_message("YOU CAN'T DIG HERE.")
            return

        if tile_state["is_dug"]:
            self.game.log_message("YOU'VE ALREADY DUG HERE.")
            return

        tile_state["is_dug"] = True
        self.game.audio.play_dig_sound()
        self.game.map_memory.remember_visible_map_info()
        found_item, amount = self.dungeon.get_item_at_tile(tile_grid_pos)

        # Build a display-friendly item label for quantity messages.
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

            if found_item in ItemSettings.TREASURE_SCORE_VALUES:
                self.game.add_score(found_item, amount)

            if amount > 1:
                self.game.log_message(f"YOU FOUND {amount} {display_name}!")
            elif found_item == "MONSTER REPELLENT":
                self.game.log_message("YOU FOUND A CAN OF MONSTER REPELLENT!")
            else:
                article = 'AN' if found_item[0] in 'AEIOU' else 'A'
                self.game.log_message(f"YOU FOUND {article} {found_item}!")

            if found_item == "KEY":
                self.game.audio.play_key_sound()

            if found_item == "GOLD COINS" or found_item in ["RUBY", "SAPPHIRE", "EMERALD", "DIAMOND"]:
                # Reuse coin SFX for all treasure pickups.
                self.game.audio.play_coin_sound()

            if found_item == "MAGIC MAP" and self.inventory.get("MAP", 0) > 0:
                self.inventory["MAP"] -= 1
                if self.inventory["MAP"] <= 0:
                    self.inventory.pop("MAP", None)

            # Increment inventory stack for discovered item.
            self.inventory[found_item] = self.inventory.get(found_item, 0) + amount
            # Track discovery so UI can display known items.
            self.discovered_items.add(found_item)

            if found_item in ["MAP", "MAGIC MAP"]:
                self.game.map_memory.reveal_full_terrain_memory()
        else:
            self.game.log_message("NOTHING BUT DIRT HERE.")
        self.game.advance_turn()

        # TODO: Refactor item pluralization/inventory mutation into a dedicated loot-resolution helper.

    def activate_key_detector(self) -> None:
        """
        Check the player's distance from the hidden key and log a hint.

        The detector uses Manhattan distance in grid space and gives stronger
        feedback as the player gets closer.
        """
        player_grid_pos = self.game.screen_to_grid(self.position.x, self.position.y)
        key_grid_pos = self.dungeon.key_grid_pos
        distance = self.dungeon.manhattan_distance(player_grid_pos, key_grid_pos)

        # TODO: Move detector distance thresholds (1, 3, 5, 7) into settings constants.

        if distance == 0:
            self.game.log_message("THE KEY DETECTOR IS GOING WILD!")
            self.game.audio.play_found_detector_sound()
        elif distance == 1:
            self.game.log_message("THE KEY DETECTOR BEEPS RAPIDLY!")
            self.game.audio.play_hot_detector_sound()
        elif distance <= 3:
            self.game.log_message("THE KEY DETECTOR GIVES A STEADY PULSE...")
            self.game.audio.play_warm_detector_sound()
        elif distance <= 5:
            self.game.log_message("THE KEY DETECTOR BEEPS SLOWLY...")
        elif distance <= 7:
            self.game.log_message("A FAINT BEEP COMES FROM THE DETECTOR.")
        else:
            # Dead silent only when very far away.
            self.game.log_message("THE KEY DETECTOR IS SILENT.")

    def is_invisible(self) -> bool:
        """Return True while invisibility cloak effect is active."""
        return self.invisibility_turns > 0

    def is_repelled(self) -> bool:
        """Return True while monster repellent effect is active."""
        return self.repellent_turns > 0

    def _get_pulse_ratio(self) -> float:
        """Return a 0..1 triangle wave used by status-effect pulses."""
        # TODO: Replace pulse-shape literal (15) with a named animation constant.
        # Generate a symmetric 0..1 pulse over one flash cycle.
        distance_from_center = abs(self.flash_frame - 15)
        return 1.0 - (distance_from_center / 15)

    def get_action_window_border_style(self) -> tuple[str, int]:
        """Return (RGB color, alpha) for the animated action-window border."""
        if self.is_invisible():
            # TODO: Move border alpha thresholds (95, 255, 15) into UI/animation constants.
            border_alpha = 95 if self.flash_frame < 15 else 255
            border_color = ColorSettings.BORDER_REPELLED if self.is_repelled() else ColorSettings.BORDER_DEFAULT
            return border_color, border_alpha

        if self.is_repelled():
            pulse_ratio = self._get_pulse_ratio()
            # TODO: Move repellent pulse alpha range literals (80, 80) into UI/animation constants.
            border_alpha = 80 + int(80 * pulse_ratio)
            return ColorSettings.BORDER_REPELLED, border_alpha

        return ColorSettings.BORDER_DEFAULT, 255

    def update_invisibility_visual(self) -> None:
        """Apply visual effects for invisibility and repellent states."""
        is_invisible = self.is_invisible()
        is_repelled = self.is_repelled()

        if is_invisible or is_repelled:
            # TODO: Move flash animation cycle length literal (30) into animation constants.
            self.flash_frame = (self.flash_frame + 1) % 30
        else:
            self.flash_frame = 0

        self.image = self.base_image.copy()

        if is_repelled:
            pulse_ratio = self._get_pulse_ratio()
            # TODO: Move repellent tint alpha range literals (70, 40) into UI/animation constants.
            tint_alpha = 70 + int(40 * pulse_ratio)
            tint_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint_surface.fill(color_with_alpha(ColorSettings.REPELLED_TINT, tint_alpha))
            self.image.blit(tint_surface, (0, 0))

        if is_invisible:
            # TODO: Move invisibility alpha thresholds (95, 255, 15) into UI/animation constants.
            alpha = 95 if self.flash_frame < 15 else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def animate(self) -> None:
        """
        Advance the player's movement animation toward the current target position.

        This keeps the game visually smooth while gameplay still resolves in grid steps.
        """
        if self.is_moving:
            # Move along the normalized direction vector toward target.
            direction = self.target_pos - self.position
            distance = direction.length()

            if distance < self.anim_speed:
                # Snap to destination when remaining distance is below one step.
                self.position = self.target_pos
                self.rect.topleft = (int(self.position.x), int(self.position.y))
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = (int(self.position.x), int(self.position.y))

        self.update_invisibility_visual()

    def update(self) -> None:
        """
        Update the player's per-frame behavior.

        The player only processes new input when not already moving.
        """
        if not self.is_moving:
            self.process_turn_action()

class Monster(pygame.sprite.Sprite):
    """Represent monster behavior, movement, and chase decision logic."""

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

    def _choose_primary_chase_step(self, delta_pixels_x: float, delta_pixels_y: float) -> tuple[int, int]:
        """Return a one-tile movement vector toward the player.

        Args:
            delta_pixels_x (float): Horizontal delta from monster to player.
            delta_pixels_y (float): Vertical delta from monster to player.

        Returns:
            tuple[int, int]: Pixel step aligned to one cardinal direction.
        """
        step_x = 0
        step_y = 0

        if abs(delta_pixels_x) >= abs(delta_pixels_y):
            if delta_pixels_x > 0:
                step_x = GridSettings.TILE_SIZE
            elif delta_pixels_x < 0:
                step_x = -GridSettings.TILE_SIZE
            elif delta_pixels_y > 0:
                step_y = GridSettings.TILE_SIZE
            elif delta_pixels_y < 0:
                step_y = -GridSettings.TILE_SIZE
        else:
            if delta_pixels_y > 0:
                step_y = GridSettings.TILE_SIZE
            elif delta_pixels_y < 0:
                step_y = -GridSettings.TILE_SIZE
            elif delta_pixels_x > 0:
                step_x = GridSettings.TILE_SIZE
            elif delta_pixels_x < 0:
                step_x = -GridSettings.TILE_SIZE

        return step_x, step_y

    def resolve_turn(self) -> None:
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
        player_is_invisible = self.game.player.is_invisible()

        # Calculate the Manhattan distance to the player
        delta_pixels_x = self.game.player.position.x - self.position.x
        delta_pixels_y = self.game.player.position.y - self.position.y
        manhattan_distance = (abs(delta_pixels_x) // GridSettings.TILE_SIZE) + (abs(delta_pixels_y) // GridSettings.TILE_SIZE)

        # Helper variables for readability
        player_has_light = self.game.player.light_radius > 0
        is_adjacent = manhattan_distance <= 1

        if player_is_invisible:
            self.is_chasing = False
            if random.random() > MonsterSettings.IDLE_CHANCE:
                self.move_randomly_one_tile()
            return

        # If the monster is repelled, it will try to move away from the player instead of towards them.
        if is_repelled:
            self.is_chasing = False
            chase_step_x, chase_step_y = self._choose_primary_chase_step(delta_pixels_x, delta_pixels_y)
            step_x = -chase_step_x
            step_y = -chase_step_y

            # After calculating the movement, we apply it.
            # The apply_movement function will handle boundary checks to make sure the monster doesn't move out of bounds.
            self.try_start_move(step_x, step_y)
            return

        # Chasing rules:
        # - if the player has no light, the monster should only chase when adjacent
        # - otherwise use the current chase radius + line of sight rules
        if is_adjacent:
            if not self.is_chasing:
                self.is_chasing = True
                self.game.audio.play_monster_chase_sound()

        elif not player_has_light:
            self.is_chasing = False

        elif manhattan_distance <= int(self.game.player.light_radius) and self.has_clear_line_of_sight_to_player():
            if not self.is_chasing:
                self.is_chasing = True
                self.game.audio.play_monster_chase_sound()
        else:
            self.is_chasing = False

        # If the monster is chasing, it still has a 20% chance to hesitate.
        if self.is_chasing:
            if random.random() < MonsterSettings.IDLE_CHANCE:
                return

            step_x, step_y = self._choose_primary_chase_step(delta_pixels_x, delta_pixels_y)

            # After calculating the movement, we apply it.
            self.try_start_move(step_x, step_y)
            return

        # If the monster is not chasing, it has a chance to move randomly or do nothing (idle).
        if random.random() > MonsterSettings.IDLE_CHANCE:
            self.move_randomly_one_tile()

    def move_randomly_one_tile(self) -> None:
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
        
        self.try_start_move(step_x, step_y)

    def try_start_move(self, delta_pixels_x: int, delta_pixels_y: int) -> None:
        """
        Attempt to move the monster by a pixel offset.

        Converts the movement into grid space, checks if the target tile
        is walkable, and starts movement animation if valid.

        Args:
            delta_pixels_x (int): Pixel movement in the x direction.
            delta_pixels_y (int): Pixel movement in the y direction.
        """
        current_col, current_row = self.game.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + (delta_pixels_x // GridSettings.TILE_SIZE)
        target_row = current_row + (delta_pixels_y // GridSettings.TILE_SIZE)

        if self.dungeon.is_walkable(target_col, target_row):
            target_x, target_y = self.game.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

    def has_clear_line_of_sight_to_player(self) -> bool:
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

    def update(self) -> None:
        """
        Placeholder for per-frame behavior.

        Monster actions are currently turn-based, so this method is unused.
        """
        pass

class Door(pygame.sprite.Sprite):
    """Represent the level door sprite and open/closed visual states."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """Initialize the door sprite with open and closed states."""
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
        """Switch the visible sprite to the open-door texture."""
        self.image = self.open_image

    def update(self) -> None:
        """No-op per-frame update hook required by the sprite group API."""
        pass