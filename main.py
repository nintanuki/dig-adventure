import pygame
import sys

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door, NPC
from windows import MessageLog, InventoryWindow, MapWindow
from dungeon import DungeonMaster
from dungeon_config import DUNGEON_CONFIG, LEVEL_DUNGEON_ORDER, get_monster_count_for_dungeon
from mapmemory import MapMemory
from render import RenderManager
from crt import CRT
from managers import ScoreLeaderboardManager, BetweenLevelManager
from tutorial import TutorialManager, default_duration_for as tutorial_default_duration

class GameManager:
    """Coordinate game state, flow, rendering phases, and input orchestration."""

    def __init__(self, start_fullscreen: bool = False):
        """Initialize runtime systems, persistent state, and the first dungeon level.

        Args:
            start_fullscreen (bool): Whether to launch directly in fullscreen mode.
        """
        # Initialize Pygame and set up the display
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Dungeon Digger')
        if start_fullscreen:
            pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()
        
        # -------- Core subsystem initialization --------
        self.setup_controllers()
        self.load_assets()
        self.dungeon = DungeonMaster(self.scaled_dirt_tiles)
        self.all_sprites = pygame.sprite.Group()
        self.audio = AudioManager()
        self.score_manager = ScoreLeaderboardManager(self)
        self.between_level_manager = BetweenLevelManager(self)
        self.game_active = False
        self.game_result = None
        self.score = 0
        self.high_score = self.score_manager.load_high_score()
        self.leaderboard = self.score_manager.load_leaderboard()
        self.level_order = list(LEVEL_DUNGEON_ORDER)
        self.level_numbers = sorted(DUNGEON_CONFIG.level_difficulty_by_number.keys())
        self.current_level_index = 0
        self.pending_level_index = 0
        self.transition_label = ""
        self.transition_end_time = 0
        self.pending_level_load = False
        self.message_success_border_until = 0
        self.r2_trigger_is_pressed = False

        # Tutorial system. Constructed lazily in start_gameplay_from_title when
        # the player chooses PLAY. Stays None for SKIP TUTORIAL runs.
        self.tutorial: TutorialManager | None = None

        self.ui_state = 'title'
        self.title_menu_index = 0
        self.npcs: list = []

        # State for game over flow and leaderboard entry.
        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.pending_leaderboard_score = 0
        self.initials_entry = "AAA"
        self.initials_index = 0
        self.between_level_manager.initialize_state()

        # -------- Tutorial --------
        self.tutorial_dismiss_input_locked = False
        
        # Pre-create the fog surface to avoid doing it every frame during rendering.
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # -------- UI windows --------
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)
        self.map_memory = None

        # -------- Post-processing --------
        self.crt = CRT(self.screen)

        # -------- Rendering facade --------
        self.render = None

        # Load the first level after all systems are initialized, so that level setup can rely on any subsystem being ready.
        self.load_level()
        self.audio.stop_music()

        # TODO: Continue splitting run() into process_events(), update_state(), and render_frame().

    def reset_game(self):
        """
        Restart the game by replacing the current GameManager instance
        with a brand new one.

        This is safer than trying to manually reset every subsystem,
        because it reuses the same startup path the game already uses
        when it first launches.
        """
        current_surface = pygame.display.get_surface()
        was_fullscreen = bool(current_surface and (current_surface.get_flags() & pygame.FULLSCREEN))

        new_game_manager = GameManager(start_fullscreen=was_fullscreen)
        new_game_manager.run()
        sys.exit()

    def close_game(self) -> None:
        """Close the game process cleanly."""
        pygame.quit()
        sys.exit()

    def quit_combo_pressed(self) -> bool:
        """Return True if START + SELECT + L1 + R1 are held on any controller."""
        required_buttons = InputSettings.JOY_BUTTON_QUIT_COMBO
        for joystick in self.connected_joysticks:
            if all(joystick.get_button(button) for button in required_buttons):
                return True
        return False

    @property
    def current_level_number(self) -> int:
        """Return the configured level number for the current level index.

        Returns:
            int: Current configured level number.
        """
        if not self.level_numbers:
            return self.current_level_index
        return self.level_numbers[self.current_level_index]

    @property
    def is_transitioning(self) -> bool:
        """Report whether a level transition card is currently active.

        Returns:
            bool: True while transition timing is in progress.
        """
        return pygame.time.get_ticks() < self.transition_end_time


    def start_gameplay_from_title(self, skip_tutorial: bool = False) -> None:
        """Leave title screen and begin active gameplay.

        Args:
            skip_tutorial: When True, advance past level 0 (The Arena) to level 1.
        """
        self.audio.play_menu_select_sound()
        if skip_tutorial and len(self.level_order) > 1:
            self.current_level_index = 1
            self.pending_level_index = 1
            player_progress = self.capture_player_progress()
            self.load_level(player_progress)
        # Activate the tutorial system only when the player chose PLAY. It
        # then runs for the entire session and is level-agnostic.
        if not skip_tutorial:
            self.tutorial = TutorialManager(self)
        else:
            self.tutorial = None
        self.ui_state = 'playing'
        self.game_active = True
        self.audio.play_random_bgm()

    def handle_title_menu_move(self, direction: int) -> None:
        """Move the title screen cursor up (-1) or down (+1)."""
        options_count = 2  # PLAY, SKIP TUTORIAL
        new_index = (self.title_menu_index + direction) % options_count
        if new_index != self.title_menu_index:
            self.title_menu_index = new_index
            self.audio.play_menu_move_sound()

    def handle_start_press(self) -> None:
        """Handle Start/Enter based on top-level UI state."""
        if self.ui_state == 'title':
            skip = self.title_menu_index == 1
            self.start_gameplay_from_title(skip_tutorial=skip)
            return

        if self.ui_state == 'game_over' and self.score_manager.can_continue_from_game_over():
            self.score_manager.continue_from_game_over()
            return

        if self.ui_state == 'enter_initials':
            self.score_manager.submit_initials_entry()
            return

        if self.ui_state == 'leaderboard':
            self.reset_game()

    def capture_player_progress(self) -> dict[str, object] | None:
        """Snapshot persistent player state before rebuilding the level."""
        if not hasattr(self, 'player'):
            return None

        return {
            'inventory': self.player.inventory.copy(),
            'discovered_items': set(self.player.discovered_items),
        }

    def restore_player_progress(self, progress: dict[str, object] | None) -> None:
        """Restore inventory and discovery state after spawning a fresh player."""
        if not progress:
            return

        self.player.inventory = progress['inventory'].copy()
        self.player.discovered_items = set(progress['discovered_items'])

    def load_level(self, player_progress: dict[str, object] | None = None) -> None:
        """Build the currently selected dungeon level and spawn fresh entities."""
        self.all_sprites.empty()

        dungeon_name = self.level_order[self.current_level_index]
        monster_count = get_monster_count_for_dungeon(dungeon_name)
        self.dungeon.load_dungeon(dungeon_name)
        self.dungeon.setup_tile_map(monster_count=monster_count)
        self.spawn_door()
        self.spawn_monster()
        self.spawn_npcs()
        self.spawn_player()
        self.restore_player_progress(player_progress)

        self.map_memory = MapMemory(self)
        self.render = RenderManager(self)

    def finish_game(self, result: str) -> None:
        """End the current run and persist the high score."""
        self.game_active = False
        self.game_result = result
        self.ui_state = 'game_over'
        if self.map_memory is not None:
            self.map_memory.reveal_full_terrain_memory()
        self.pending_leaderboard_score = self.score
        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.audio.stop_music()
        self.score_manager.save_high_score()

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self):
        """Initializes connected gamepads or joysticks."""
        pygame.joystick.init()
        # Cache all currently connected controllers.
        self.connected_joysticks = [pygame.joystick.Joystick(index) for index in range(pygame.joystick.get_count())]

    def load_assets(self):
        """Handle all image loading and scaling in one place."""
        self.scaled_dirt_tiles = []

        for dirt_path in AssetPaths.DIRT_TILES:
            dirt_surf = pygame.image.load(dirt_path).convert_alpha()
            scaled_dirt = pygame.transform.scale(
                dirt_surf,
                (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
            )
            self.scaled_dirt_tiles.append(scaled_dirt)
        
        dug_surf = pygame.image.load(AssetPaths.DUG_TILE).convert_alpha()
        self.scaled_dug_tile = pygame.transform.scale(dug_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        wall_surf = pygame.image.load(AssetPaths.WALL_TILE).convert_alpha()
        self.scaled_wall_tile = pygame.transform.scale(wall_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

    # -------------------------
    # ENTITY SPAWNING
    # -------------------------

    def spawn_player(self):
        """Spawn the player sprite at the precomputed dungeon spawn tile."""
        col, row = self.dungeon.player_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.player = Player(self, (x, y), self.all_sprites)

    def spawn_monster(self):
        """Spawn all monster sprites at the precomputed dungeon spawn tiles."""
        self.monsters = []
        for col, row in self.dungeon.monster_grid_positions:
            x, y = self.grid_to_screen(col, row)
            monster = Monster(self, (x, y), self.all_sprites)
            self.monsters.append(monster)

    def spawn_door(self):
        """Spawn the level door sprite at the precomputed dungeon door tile."""
        col, row = self.dungeon.door_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.door = Door(self, (x, y), self.all_sprites)

    def spawn_npcs(self):
        """Spawn NPC sprites at the precomputed dungeon NPC positions."""
        self.npcs = []
        for col, row in self.dungeon.npc_grid_positions:
            x, y = self.grid_to_screen(col, row)
            npc = NPC(self, (x, y), self.all_sprites)
            self.npcs.append(npc)

    def _trigger_npc_interaction(self, npc) -> None:
        """Give the player a random item from an NPC then remove it."""
        self.log_message("IT'S DANGEROUS TO GO ALONE! TAKE THIS!")

        found_item, amount = self.dungeon.roll_random_loot()
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
                self.score_manager.add_score(found_item, amount)

            if amount > 1:
                self.log_message(f"YOU FOUND {amount} {display_name}!")
            elif found_item == "MONSTER REPELLENT":
                self.log_message("YOU FOUND A CAN OF MONSTER REPELLENT!")
            else:
                article = 'AN' if found_item[0] in 'AEIOU' else 'A'
                self.log_message(f"YOU FOUND {article} {found_item}!")

            if found_item == "GOLD COINS" or found_item in ["RUBY", "SAPPHIRE", "EMERALD", "DIAMOND"]:
                self.audio.play_coin_sound()

            if found_item == "MAGIC MAP" and self.player.inventory.get("MAP", 0) > 0:
                self.player.inventory["MAP"] -= 1
                if self.player.inventory["MAP"] <= 0:
                    self.player.inventory.pop("MAP", None)

            self.player.inventory[found_item] = self.player.inventory.get(found_item, 0) + amount
            self.player.discovered_items.add(found_item)
            self.notify_tutorial('item_picked_up', item=found_item)

            # Pick up a light source from an NPC -> auto-select if none active.
            if found_item in ('LANTERN', 'TORCH', 'MATCH'):
                self.player.refresh_light_selection()

            if found_item in ["MAP", "MAGIC MAP"]:
                self.map_memory.reveal_full_terrain_memory()

        npc.fade_pending = True
        self.npcs.remove(npc)

    # TODO: Refactor spawning helpers into a dedicated SpawnManager when setup logic grows further.

    # -------------------------
    # COORDINATE + MAP HELPERS
    # -------------------------

    def grid_to_screen(self, col, row):
        """Convert grid coordinates to top-left screen pixel coordinates.

        Args:
            col: Grid column.
            row: Grid row.

        Returns:
            tuple[int, int]: Screen-space pixel coordinates.
        """
        return (
            UISettings.ACTION_WINDOW_X + col * GridSettings.TILE_SIZE,
            UISettings.ACTION_WINDOW_Y + row * GridSettings.TILE_SIZE,
        )

    def screen_to_grid(self, x, y):
        """Convert screen pixel coordinates to grid coordinates.

        Args:
            x: Screen-space x position.
            y: Screen-space y position.

        Returns:
            tuple[int, int]: Grid column and row indices.
        """
        return (
            int((x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE),
            int((y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE),
        )

    # TODO: Refactor coordinate conversion helpers into a small utility class/module shared by gameplay systems.

    # -------------------------
    # TURN / GAME STATE --> TurnManager Class (maybe not is_busy())
    # -------------------------

    def advance_turn(self):
        """
        Resolve one world step after the player commits to an action.

        This is where time passes in the dungeon: temporary effects tick down,
        monsters respond, and loss conditions are checked. Keeping that logic
        together helps the game stay consistently turn-based.
        """

        if not self.game_active:
            return

        self.map_memory.remember_visible_map_info()

        # Handle Light Shrinking
        if self.player.light_turns_left > 0:
            self.player.light_turns_left -= 1
            
            if self.player.light_turns_left > 0:
                # Calculate how much radius we have per turn of life
                # We use the starting radius of the current light source
                unit_radius = self.player.active_light_max_radius / self.player.active_light_max_duration
                self.player.light_radius = unit_radius * self.player.light_turns_left
            else:
                # It hit zero
                self.player.light_radius = LightSettings.DEFAULT_RADIUS
                self.log_message("YOUR LIGHT FLICKERS OUT...")

        # Handle Repellent Duration
        if self.player.repellent_turns > 0:
            self.player.repellent_turns -= 1
            if self.player.repellent_turns == 0:
                self.log_message("THE SCENT OF THE REPELLENT FADES AWAY...")

        # Handle Invisibility Cloak Duration
        if self.player.invisibility_turns > 0:
            self.player.invisibility_turns -= 1
            if self.player.invisibility_turns == 0:
                self.log_message("THE INVISIBILITY WEARS OFF.")
                if self.player.invisibility_from_cloak:
                    self.player.invisibility_cooldown_turns = (
                        ItemSettings.INVISIBILITY_CLOAK_COOLDOWN + GameSettings.STATUS_EFFECT_TURN_BUFFER
                    )
                    self.player.invisibility_from_cloak = False

        # Handle Invisibility Cloak Cooldown
        if self.player.invisibility_cooldown_turns > 0:
            self.player.invisibility_cooldown_turns -= 1

        # Check NPC adjacency: trigger interaction when player moves to a tile adjacent to an NPC.
        if self.player.is_moving:
            dest_col, dest_row = self.screen_to_grid(
                self.player.target_pos.x, self.player.target_pos.y)
            for npc in list(self.npcs):
                npc_col, npc_row = self.screen_to_grid(npc.position.x, npc.position.y)
                if abs(dest_col - npc_col) + abs(dest_row - npc_row) == 1:
                    self._trigger_npc_interaction(npc)

        for monster in self.monsters:
            monster.resolve_turn()

        # Remove any NPC that a monster has landed on.
        for monster in self.monsters:
            dest = monster.target_pos if monster.is_moving else monster.position
            m_col, m_row = self.screen_to_grid(dest.x, dest.y)
            for npc in list(self.npcs):
                npc_col, npc_row = self.screen_to_grid(npc.position.x, npc.position.y)
                if m_col == npc_col and m_row == npc_row:
                    npc.kill()
                    self.npcs.remove(npc)

        self.check_player_caught_by_monster()

        # Let the tutorial decide whether to surface its next card now that
        # the world has settled for this turn.
        if self.tutorial is not None:
            self.tutorial.on_turn_end()

    def check_player_caught_by_monster(self) -> bool:
        """Return True and end the game if any monster occupies the player's tile."""
        if not self.game_active:
            return False

        if self.player.is_invisible():
            return False

        for monster in self.monsters:
            if self.player.position == monster.position:
                self.log_message("YOU WERE CAUGHT BY THE MONSTER!")
                self.audio.play_scream_sound()
                self.finish_game("loss")
                return True

        return False

    @property
    def is_busy(self):
        """Centralized check to see if the game is currently animating."""
        return (self.player.is_moving or 
                any(monster.is_moving for monster in self.monsters) or
                self.message_log.is_typing)

    # -------------------------
    # -------------------------
    # UI / GAME FEEDBACK
    # -------------------------
    # -------------------------
    
    def log_message(self, text, type_speed=None):
        """The central hub for all game objects to send text to the UI."""
        self.message_log.add_message(text, type_speed=type_speed)

    def notify_tutorial(self, event: str, **kwargs) -> None:
        """Forward a game-side event to the tutorial system if it exists.

        No-op when the tutorial isn't active (SKIP TUTORIAL run, or already
        torn down). Game-side call sites can call this unconditionally.
        """
        if self.tutorial is not None:
            self.tutorial.notify(event, **kwargs)

    @property
    def is_tutorial_blocking(self) -> bool:
        """True while a tutorial card is on screen and gameplay must freeze."""
        return self.tutorial is not None and self.tutorial.is_blocking

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def run(self):
        """
        Run the game loop.
        """
        # TODO: Split run() into process_events(), update_state(), and render_frame() for maintainability.
        # Main game loop
        while True:
            if self.quit_combo_pressed():
                self.close_game()

            if self.ui_state == 'playing':
                self.between_level_manager.update_level_transition()
                self.between_level_manager.update_door_unlock_sequence()
                self.between_level_manager.update_treasure_conversion()

            self.score_manager.update_game_over_flow()

            # -------- Event handling --------
            for event in pygame.event.get():
                # Exit request.
                if event.type == pygame.QUIT:
                    self.close_game()

                # Keyboard input routes.
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()

                    # Tutorial dismissal short-circuits all other keyboard
                    # handlers while a card is up. SPACE is the advertised
                    # dismiss key; ENTER is also accepted.
                    if self.is_tutorial_blocking:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                            if self.tutorial.try_dismiss():
                                self.tutorial_dismiss_input_locked = True
                        continue

                    if self.ui_state == 'title':
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.handle_title_menu_move(-1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.handle_title_menu_move(1)

                    if self.in_shop_phase:
                        self.between_level_manager.handle_shop_event(event)

                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.handle_start_press()

                    self.score_manager.handle_initials_event(event)

                # Controller button input routes.
                if event.type == pygame.JOYBUTTONDOWN:
                    if self.quit_combo_pressed():
                        self.close_game()

                    if event.button == InputSettings.JOY_BUTTON_BACK:
                        pygame.display.toggle_fullscreen()

                    # Tutorial dismissal short-circuits all gameplay button
                    # handlers while a card is up.
                    if self.is_tutorial_blocking:
                        if event.button == InputSettings.JOY_BUTTON_A:
                            if self.tutorial.try_dismiss():
                                self.tutorial_dismiss_input_locked = True
                        continue

                    if self.in_shop_phase:
                        self.between_level_manager.handle_shop_event(event)

                    if event.button in (InputSettings.JOY_BUTTON_START, InputSettings.JOY_BUTTON_A):
                        self.handle_start_press()

                    # Cycle the player's active light source while in gameplay.
                    if (
                        self.ui_state == 'playing'
                        and self.game_active
                        and not self.is_transitioning
                        and not self.in_treasure_conversion
                        and not self.in_shop_phase
                    ):
                        if event.button == InputSettings.JOY_BUTTON_L1:
                            self.player.cycle_selected_light_source(-1)
                        elif event.button == InputSettings.JOY_BUTTON_R1:
                            self.player.cycle_selected_light_source(1)

                    self.score_manager.handle_initials_event(event)

                if event.type == pygame.JOYHATMOTION and self.ui_state == 'title':
                    _, hat_y = event.value
                    if hat_y == 1:
                        self.handle_title_menu_move(-1)
                    elif hat_y == -1:
                        self.handle_title_menu_move(1)

                if event.type == pygame.JOYHATMOTION and self.in_shop_phase:
                    self.between_level_manager.handle_shop_event(event)

                if event.type == pygame.JOYHATMOTION:
                    self.score_manager.handle_initials_event(event)

                # Controller R2 trigger mute toggle (edge-triggered). L2 is
                # reserved for the invisibility cloak. Mute state is surfaced
                # via the persistent green MUTE indicator drawn by
                # RenderManager, not via the in-game message log.
                if event.type == pygame.JOYAXISMOTION and event.axis == InputSettings.JOY_AXIS_R2:
                    trigger_pressed = event.value > InputSettings.JOY_TRIGGER_THRESHOLD
                    if trigger_pressed and not self.r2_trigger_is_pressed:
                        self.audio.toggle_mute(
                            resume_music=self.game_active and not self.is_transitioning
                        )
                    self.r2_trigger_is_pressed = trigger_pressed

            # -------- Per-frame update --------
            self.message_log.update()
            # Let the tutorial drain its burst queue when nothing is on screen
            # (handles the boot sequence and back-to-back chains).
            if self.tutorial is not None:
                self.tutorial.update()
            if self.ui_state == 'playing' and self.game_active:
                if (
                    not self.is_transitioning
                    and not self.is_busy
                    and not self.in_treasure_conversion
                    and not self.in_shop_phase
                    and not self.is_tutorial_blocking
                ):
                    self.all_sprites.update()

                if (
                    not self.is_transitioning
                    and not self.in_treasure_conversion
                    and not self.in_shop_phase
                    and not self.is_tutorial_blocking
                ):
                    # Always advance movement animation to complete in-flight motion.
                    # TODO: Replace hasattr('animate') with a protocol/base class for animatable sprites.
                    for sprite in self.all_sprites:
                        if hasattr(sprite, 'animate'):
                            sprite.animate()

                    # Resolve collisions immediately after movement completes.
                    self.check_player_caught_by_monster()

            # -------- Rendering --------
            self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

            if self.ui_state in {'playing', 'game_over'}:
                self.render.draw_grid_background()
                self.all_sprites.draw(self.screen)

                if self.ui_state == 'playing' and not DebugSettings.NO_FOG:
                    self.render.draw_fog_of_war()
                self.render.draw_ui_frames()
                self.message_log.draw(self.screen)
                self.inventory_window.draw(self.screen)
                self.map_window.draw(self.screen)
                self.render.draw_level_transition()
                self.render.draw_treasure_conversion()
                self.render.draw_shop_menu()
                if self.tutorial is not None:
                    self.tutorial.draw(self.screen)

            if self.ui_state == 'title':
                self.render.draw_title_screen()
            elif self.ui_state == 'game_over':
                self.render.draw_end_game_screens()
            elif self.ui_state == 'enter_initials':
                self.render.draw_initials_entry_screen()
            elif self.ui_state == 'leaderboard':
                self.render.draw_leaderboard_screen()

            # Apply CRT pass after world/UI rendering.
            self.crt.draw()

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()