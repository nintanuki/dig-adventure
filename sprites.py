import pygame
import random
import os
from typing import Literal
from settings import *

PlayerAction = Literal['move', 'dig', 'detector', 'light', 'repellent', 'cloak']
PlayerIntent = tuple[int, int, PlayerAction | None]

# Ordered priority for auto-selecting a default light source (best-first).
LIGHT_SOURCE_PRIORITY: tuple[str, ...] = ('LANTERN', 'TORCH', 'MATCH')
# Ordered cycle for L1/R1 toggling through owned light sources.
LIGHT_SOURCE_CYCLE_ORDER: tuple[str, ...] = ('MATCH', 'TORCH', 'LANTERN')

LIGHT_SOURCE_STATS = {
    'MATCH': (LightSettings.MATCH_RADIUS, LightSettings.MATCH_DURATION),
    'TORCH': (LightSettings.TORCH_RADIUS, LightSettings.TORCH_DURATION),
    'LANTERN': (LightSettings.LANTERN_RADIUS, LightSettings.LANTERN_DURATION),
}

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
        cloak_player_path = AssetPaths.PLAYER_CLOAK if os.path.exists(AssetPaths.PLAYER_CLOAK) else AssetPaths.PLAYER
        cloak_player_surf = pygame.image.load(cloak_player_path).convert_alpha()
        self.normal_base_image = pygame.transform.scale(player_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        self.cloak_base_image = pygame.transform.scale(cloak_player_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        self.base_image = self.normal_base_image
        self.image = self.base_image.copy()

        # -------- Position and movement state --------
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        initial_inventory = (
            ItemSettings.TEST_INITIAL_INVENTORY
            if DebugSettings.USE_TEST_INITIAL_INVENTORY
            else ItemSettings.NORMAL_INITIAL_INVENTORY
        )
        self.inventory = initial_inventory.copy()
        self.discovered_items = set(self.inventory.keys())
        
        self.repellent_turns = 0
        self.invisibility_turns = 0
        self.invisibility_cooldown_turns = 0
        self.invisibility_from_cloak = False
        self.flash_frame = 0

        self.light_radius = LightSettings.DEFAULT_RADIUS
        self.light_turns_left = 0
        self.active_light_max_radius = 0
        self.active_light_max_duration = 0

        # Light source the B button will activate. None until the player picks
        # one up; auto-selects the best owned source on inventory changes, and
        # can be cycled manually with L1/R1.
        self.selected_light_source: str | None = None
        self.refresh_light_selection()

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

    def _owned_light_sources(self, order: tuple[str, ...]) -> list[str]:
        """Return the subset of light sources the player currently has, in the given order."""
        return [name for name in order if self.inventory.get(name, 0) > 0]

    def refresh_light_selection(self) -> None:
        """Ensure selected_light_source points to an owned source.

        Called after any inventory change that could affect light sources.
        - If the player owns no light sources, selection becomes None.
        - If the current selection is depleted (or unset), pick the best
          owned source per LIGHT_SOURCE_PRIORITY (LANTERN > TORCH > MATCH).
        - Otherwise leave the manual selection alone.
        """
        owned = self._owned_light_sources(LIGHT_SOURCE_PRIORITY)
        if not owned:
            self.selected_light_source = None
        elif self.selected_light_source not in owned:
            self.selected_light_source = owned[0]

    def cycle_selected_light_source(self, direction: int) -> None:
        """Cycle the B-button light selection through owned sources.

        Args:
            direction (int): +1 for next (R1), -1 for previous (L1).
        """
        owned = self._owned_light_sources(LIGHT_SOURCE_CYCLE_ORDER)
        if not owned:
            return
        if self.selected_light_source not in owned:
            self.selected_light_source = owned[0]
            return
        if len(owned) == 1:
            return
        current_index = owned.index(self.selected_light_source)
        new_index = (current_index + direction) % len(owned)
        self.selected_light_source = owned[new_index]

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

        # Ignore held tutorial-dismiss inputs until released so the same
        # A/SPACE press doesn't become an immediate dig.
        if self.game.tutorial_dismiss_input_locked:
            keyboard_still_held = (
                keys[pygame.K_SPACE]
                or keys[pygame.K_RETURN]
                or keys[pygame.K_KP_ENTER]
            )

            controller_still_held = (
                pygame.joystick.get_count() > 0
                and pygame.joystick.Joystick(0).get_button(InputSettings.JOY_BUTTON_A)
            )

            if keyboard_still_held or controller_still_held:
                return 0, 0, None

            self.game.tutorial_dismiss_input_locked = False

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
                if joystick.get_button(InputSettings.JOY_BUTTON_A):
                    action = 'dig'
                elif joystick.get_button(InputSettings.JOY_BUTTON_B):
                    action = 'light'
                elif joystick.get_button(InputSettings.JOY_BUTTON_X):
                    action = 'detector'
                elif joystick.get_button(InputSettings.JOY_BUTTON_Y):
                    action = 'repellent'
                elif joystick.get_axis(InputSettings.JOY_AXIS_L2) > InputSettings.JOY_TRIGGER_THRESHOLD:
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
            self.game.notify_tutorial('moved')
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
            # Use the player's currently selected light source. Defensive
            # refresh in case the selection went stale (e.g. depleted between
            # presses).
            self.refresh_light_selection()
            name = self.selected_light_source

            if name and self.inventory.get(name, 0) > 0:
                radius, duration = LIGHT_SOURCE_STATS[name]
                self.inventory[name] -= 1

                # Preserve source max values for per-turn radius decay.
                self.active_light_max_radius = radius
                self.active_light_max_duration = duration
                self.light_radius = radius
                # Add one turn buffer so effects include the activation turn.
                self.light_turns_left = duration + GameSettings.STATUS_EFFECT_TURN_BUFFER

                if self.inventory.get("MAGIC MAP", 0) > 0:
                    self.game.map_memory.remember_visible_map_info()
                self.game.log_message(f"YOU LIGHT A {name.upper()}!")
                if name == 'MATCH':
                    self.game.audio.play_match_light_sound()
                else:
                    self.game.audio.play_light_sound()

                # Move selection to the next-best owned source if this one ran out.
                self.refresh_light_selection()
                self.game.notify_tutorial(
                    'item_used', kind='light', name=name, duration=int(duration)
                )
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO LIGHT SOURCES!")

        elif action == 'detector':
            if self.inventory.get('KEY DETECTOR', 0) > 0:
                self.activate_key_detector()
                self.game.notify_tutorial('item_used', kind='detector')
                self.game.advance_turn()
            else:
                self.game.log_message("YOU DON'T HAVE A KEY DETECTOR!")

        elif action == 'repellent':
            if self.inventory.get('MONSTER REPELLENT', 0) > 0:
                self.inventory['MONSTER REPELLENT'] -= 1
                self.repellent_turns = MonsterSettings.REPELLENT_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.game.log_message("YOU SPRAY THE REPELLENT.")
                self.game.audio.play_repellent_sound(self.inventory['MONSTER REPELLENT'])
                self.game.notify_tutorial(
                    'item_used', kind='repellent', duration=MonsterSettings.REPELLENT_DURATION
                )
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO MONSTER REPELLENT LEFT!")

        elif action == 'cloak':
            has_scroll = self.inventory.get('INVISIBILITY SCROLL', 0) > 0
            has_cloak = self.inventory.get('INVISIBILITY CLOAK', 0) > 0

            if not has_scroll and not has_cloak:
                self.game.log_message("YOU DON'T HAVE AN INVISIBILITY SCROLL!")
            elif self.invisibility_turns > 0:
                self.game.log_message("YOU ARE ALREADY INVISIBLE!")
            elif has_cloak and self.invisibility_cooldown_turns > 0:
                self.game.log_message("THE INVISIBILITY CLOAK NEEDS TIME TO RECHARGE.")
            elif has_cloak:
                self.invisibility_turns = ItemSettings.INVISIBILITY_CLOAK_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.invisibility_from_cloak = True
                self.game.log_message("YOU WRAP YOURSELF IN THE INVISIBILITY CLOAK.")
                self.game.audio.play_vanish_sound()
                self.game.notify_tutorial(
                    'item_used', kind='cloak', duration=ItemSettings.INVISIBILITY_CLOAK_DURATION
                )
                self.game.advance_turn()
            else:
                self.inventory['INVISIBILITY SCROLL'] -= 1
                if self.inventory['INVISIBILITY SCROLL'] <= 0:
                    self.inventory.pop('INVISIBILITY SCROLL', None)

                self.invisibility_turns = ItemSettings.INVISIBILITY_CLOAK_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.invisibility_from_cloak = False
                self.game.log_message("YOU READ THE INVISIBILITY SCROLL.")
                self.game.notify_tutorial(
                    'item_used', kind='scroll', duration=ItemSettings.INVISIBILITY_CLOAK_DURATION
                )
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
                self.game.between_level_manager.handle_door_unlock()
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
        self.game.notify_tutorial('dug')
        self.game.map_memory.remember_visible_map_info()
        found_item, amount = self.dungeon.get_item_at_tile(tile_grid_pos)

        # Suppress scroll drops if the player already owns the cloak upgrade.
        if found_item == 'INVISIBILITY SCROLL' and self.inventory.get('INVISIBILITY CLOAK', 0) > 0:
            found_item = None
            amount = 0

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
                self.game.score_manager.add_score(found_item, amount)

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
            self.game.notify_tutorial('item_picked_up', item=found_item)

            # Pick up a new light source -> auto-select if none was active.
            if found_item in LIGHT_SOURCE_PRIORITY:
                self.refresh_light_selection()

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

        if distance == ItemSettings.DETECTOR_DISTANCE_FOUND:
            self.game.log_message("THE KEY DETECTOR IS GOING WILD!")
            self.game.audio.play_found_detector_sound()
        elif distance == ItemSettings.DETECTOR_DISTANCE_HOT:
            self.game.log_message("THE KEY DETECTOR BEEPS RAPIDLY!")
            self.game.audio.play_hot_detector_sound()
        elif distance <= ItemSettings.DETECTOR_DISTANCE_STEADY:
            self.game.log_message("THE KEY DETECTOR GIVES A STEADY PULSE...")
            self.game.audio.play_warm_detector_sound()
        elif distance <= ItemSettings.DETECTOR_DISTANCE_SLOW:
            self.game.log_message("THE KEY DETECTOR BEEPS SLOWLY...")
        elif distance <= ItemSettings.DETECTOR_DISTANCE_FAINT:
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
        # Generate a symmetric 0..1 pulse over one flash cycle.
        half_cycle = PlayerSettings.FLASH_HALF_CYCLE
        distance_from_center = abs(self.flash_frame - half_cycle)
        return 1.0 - (distance_from_center / half_cycle)

    def get_action_window_border_style(self) -> tuple[str, int]:
        """Return (RGB color, alpha) for the animated action-window border."""
        if self.is_invisible():
            border_alpha = 95 if self.flash_frame < PlayerSettings.FLASH_HALF_CYCLE else 255
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
            self.flash_frame = (self.flash_frame + 1) % PlayerSettings.FLASH_CYCLE_FRAMES
        else:
            self.flash_frame = 0

        self.base_image = self.cloak_base_image if (is_invisible or is_repelled) else self.normal_base_image
        self.image = self.base_image.copy()

        if is_repelled:
            pulse_ratio = self._get_pulse_ratio()
            # TODO: Move repellent tint alpha range literals (70, 40) into UI/animation constants.
            tint_alpha = 70 + int(40 * pulse_ratio)
            tint_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint_surface.fill(color_with_alpha(ColorSettings.REPELLED_TINT, tint_alpha))
            self.image.blit(tint_surface, (0, 0))

        if is_invisible:
            alpha = 95 if self.flash_frame < PlayerSettings.FLASH_HALF_CYCLE else 255
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

        # Load and scale a random monster variant for this instance.
        monster_candidates: list[str] = []
        if os.path.isdir(AssetPaths.MONSTER_VARIANTS_DIR):
            for name in os.listdir(AssetPaths.MONSTER_VARIANTS_DIR):
                candidate_path = os.path.join(AssetPaths.MONSTER_VARIANTS_DIR, name)
                if os.path.isfile(candidate_path) and name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    monster_candidates.append(candidate_path)

        monster_sprite_path = random.choice(monster_candidates) if monster_candidates else AssetPaths.MONSTER
        surface = pygame.image.load(monster_sprite_path).convert_alpha()
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

    def _is_visible_in_player_light(self, manhattan_distance: int) -> bool:
        """Return whether the monster is currently visible in the player's light."""
        return self.game.player.light_radius > 0 and manhattan_distance <= int(self.game.player.light_radius)

    def _log_chase_warning(self, manhattan_distance: int) -> None:
        """Log the chase warning text variant based on player-visible monster state."""
        if self._is_visible_in_player_light(manhattan_distance):
            self.game.log_message("YOU'VE BEEN SPOTTED BY A MONSTER!")
        else:
            self.game.log_message("YOU HEAR A MONSTER NEARBY!")

    def _stop_chasing(self) -> None:
        """Drop chase state and resume normal music; fire tutorial hook on transition."""
        if self.is_chasing:
            self.game.notify_tutorial('monster_lost_sight')
        self.is_chasing = False
        self.game.audio.play_normal_music()

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
            self._stop_chasing()
            if random.random() > MonsterSettings.IDLE_CHANCE:
                self.move_randomly_one_tile()
            return

        # If the monster is repelled, it will try to move away from the player instead of towards them.
        if is_repelled:
            self._stop_chasing()
            chase_step_x, chase_step_y = self._choose_primary_chase_step(delta_pixels_x, delta_pixels_y)
            step_x = -chase_step_x
            step_y = -chase_step_y

            # After calculating the movement, we apply it.
            # The apply_movement function will handle boundary checks to make sure the monster doesn't move out of bounds.
            self.try_start_move(step_x, step_y)
            return

        # Chasing rules:
        # - if the player has no light, monsters never chase regardless of distance
        # - otherwise use the current chase radius + line of sight rules
        if not player_has_light:
            self._stop_chasing()

        elif is_adjacent or (manhattan_distance <= int(self.game.player.light_radius) and self.has_clear_line_of_sight_to_player()):
            if not self.is_chasing:
                self.is_chasing = True
                self.game.audio.play_monster_chase_sound()
                self.game.audio.play_chase_music()
                self._log_chase_warning(manhattan_distance)
                self.game.notify_tutorial('monster_spotted')
        else:
            self._stop_chasing()

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

class NPC(pygame.sprite.Sprite):
    """A stationary NPC that gives the player a random item when approached."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """Initialize NPC sprite visuals and fade-out state.

        Args:
            game: Active game manager instance.
            position (tuple[int, int]): Starting screen position.
            groups: Sprite groups this NPC belongs to.
        """
        super().__init__(groups)
        self.game = game

        npc_candidates: list[str] = []
        if os.path.isdir(AssetPaths.NPC_VARIANTS_DIR):
            for name in os.listdir(AssetPaths.NPC_VARIANTS_DIR):
                candidate_path = os.path.join(AssetPaths.NPC_VARIANTS_DIR, name)
                if os.path.isfile(candidate_path) and name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    npc_candidates.append(candidate_path)

        npc_sprite_path = random.choice(npc_candidates) if npc_candidates else AssetPaths.PLAYER
        surface = pygame.image.load(npc_sprite_path).convert_alpha()
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        self.rect = self.image.get_rect(topleft=position)
        self.position = pygame.math.Vector2(position)

        # Fade state: stays solid until message finishes, then fades out.
        self.fade_pending = False
        self.fading = False
        self.fade_alpha = 255

    def animate(self) -> None:
        """Advance fade-out animation once any pending message has finished typing."""
        if self.fade_pending and not self.game.message_log.is_typing:
            self.fade_pending = False
            self.fading = True

        if self.fading:
            self.fade_alpha = max(0, self.fade_alpha - NPCSettings.FADE_SPEED)
            self.image.set_alpha(self.fade_alpha)
            if self.fade_alpha <= 0:
                self.kill()

    def update(self) -> None:
        """No-op update hook kept for sprite-group compatibility."""
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
