import pygame
import sys
import os

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog, InventoryWindow, MapWindow
from dungeon import DungeonMaster
from mapmemory import MapMemory
from render import RenderManager
from crt import CRT
from tilemaps import DUNGEON_ORDER

class GameManager:
    def __init__(self):
        # Initialize Pygame and set up the display
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Dig Adventure')
        self.clock = pygame.time.Clock()
        
        self.setup_controllers() # Controller Setup
        self.load_assets() # Pre-load dirt asset to avoid loading it 60 times per second
        self.dungeon = DungeonMaster(self.scaled_dirt_tiles) # Initialize the DungeonMaster with the pre-scaled dirt tiles from load_assets()
        self.all_sprites = pygame.sprite.Group() # Create a group to hold all sprites
        self.audio = AudioManager() # Initialize the audio manager
        self.game_active = True
        self.game_result = None
        self.score = 0
        self.high_score = self.load_high_score()
        self.level_order = list(DUNGEON_ORDER)
        self.current_level_index = 0
        self.transition_label = ""
        self.transition_end_time = 0
        self.pending_level_load = False
        
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # Initialize Windows
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)
        self.map_memory = None

        # CRT Effect
        self.crt = CRT(self.screen)

        # Render Manager
        self.render = None

        self.load_level()

    def reset_game(self):
        """
        Restart the game by replacing the current GameManager instance
        with a brand new one.

        This is safer than trying to manually reset every subsystem,
        because it reuses the same startup path the game already uses
        when it first launches.

        We will implement a more elegant reset in the future,
        but this is a good quick solution for now to speed up testing.
        """
        new_game_manager = GameManager()
        new_game_manager.run()
        sys.exit()

        # note, it does not stay in fullscreen.

    @property
    def current_level_number(self) -> int:
        return self.current_level_index + 1

    @property
    def is_transitioning(self) -> bool:
        return pygame.time.get_ticks() < self.transition_end_time

    def get_high_score_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), GameSettings.HIGH_SCORE_FILE)

    def load_high_score(self) -> int:
        """Load the saved high score from disk if it exists."""
        high_score_path = self.get_high_score_path()
        if not os.path.exists(high_score_path):
            return 0

        try:
            with open(high_score_path, 'r', encoding='utf-8') as score_file:
                return int(score_file.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def save_high_score(self) -> None:
        """Persist the best score reached so far to disk."""
        self.high_score = max(self.high_score, self.score)

        try:
            with open(self.get_high_score_path(), 'w', encoding='utf-8') as score_file:
                score_file.write(str(self.high_score))
        except OSError:
            pass

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
        self.player.inventory.pop('KEY', None)
        self.player.discovered_items = set(progress['discovered_items'])

    def load_level(self, player_progress: dict[str, object] | None = None) -> None:
        """Build the currently selected dungeon level and spawn fresh entities."""
        self.all_sprites.empty()

        dungeon_name = self.level_order[self.current_level_index]
        self.dungeon.load_dungeon(dungeon_name)
        self.dungeon.setup_tile_map()
        self.spawn_door()
        self.spawn_monster()
        self.spawn_player()
        self.restore_player_progress(player_progress)

        self.map_memory = MapMemory(self)
        self.render = RenderManager(self)

    def start_level_transition(self) -> None:
        """Pause on a title card before loading the next dungeon."""
        self.transition_label = f"LEVEL {self.current_level_number}"
        self.transition_end_time = pygame.time.get_ticks() + GameSettings.LEVEL_TRANSITION_MS
        self.pending_level_load = True
        self.audio.stop_music()

    def update_level_transition(self) -> None:
        """Load the pending dungeon once the transition card has finished."""
        if not self.pending_level_load:
            return

        if pygame.time.get_ticks() < self.transition_end_time:
            return

        player_progress = self.capture_player_progress()
        self.load_level(player_progress)
        self.audio.play_random_bgm()
        self.pending_level_load = False
        self.transition_label = ""
        self.transition_end_time = 0

    def finish_game(self, result: str) -> None:
        """End the current run and persist the high score."""
        self.game_active = False
        self.game_result = result
        self.audio.stop_music()
        self.save_high_score()

    def handle_door_unlock(self) -> None:
        """Advance to the next dungeon, or finish the run on the last door."""
        if self.current_level_index >= len(self.level_order) - 1:
            self.log_message("CONGRATULATIONS! YOU CLEARED THE FINAL DUNGEON!")
            self.finish_game("win")
            return

        next_level_number = self.current_level_number + 1
        self.log_message(f"YOU UNLOCK THE DOOR. DESCENDING TO LEVEL {next_level_number}...")
        self.current_level_index += 1
        self.start_level_transition()

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self):
        """Initializes connected gamepads or joysticks."""
        pygame.joystick.init()
        # Create a list of all connected controllers
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
    # ENTITY SPAWNING --> SpawnManager Class? (probably not a priority)
    # -------------------------

    def spawn_player(self):
        col, row = self.dungeon.player_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.player = Player(self, (x, y), self.all_sprites)

    def spawn_monster(self):
        self.monsters = []
        for col, row in self.dungeon.monster_grid_positions:
            x, y = self.grid_to_screen(col, row)
            monster = Monster(self, (x, y), self.all_sprites)
            self.monsters.append(monster)

    def spawn_door(self):
        col, row = self.dungeon.door_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.door = Door(self, (x, y), self.all_sprites)

    # -------------------------
    # COORDINATE + MAP HELPERS --> Future MapUtils Class?
    # -------------------------

    def grid_to_screen(self, col, row):
        return (
            UISettings.ACTION_WINDOW_X + col * GridSettings.TILE_SIZE,
            UISettings.ACTION_WINDOW_Y + row * GridSettings.TILE_SIZE,
        )

    def screen_to_grid(self, x, y):
        return (
            int((x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE),
            int((y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE),
        )

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
                self.log_message("THE INVISIBILITY CLOAK FADES.")

        for monster in self.monsters:
            monster.resolve_turn()

        self.check_player_caught_by_monster()

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
    # UI / GAME FEEDBACK --> Leave in GameManager for now
    # -------------------------
    
    def log_message(self, text):
        """The central hub for all game objects to send text to the UI."""
        self.message_log.add_message(text)

    # -------------------------
    # Score
    # -------------------------

    def add_score(self, item_name: str, amount: int = 1) -> None:
        value = ItemSettings.TREASURE_SCORE_VALUES.get(item_name, 0)
        self.score += value * amount

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def run(self):
        """
        Run the game loop.
        """
        # Main game loop
        while True:
            self.update_level_transition()

            # Event Handling
            for event in pygame.event.get():
                # Handle quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Keyboard Inputs for fullscreen toggle and game restart
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    # Restart only after game over / escape
                    if not self.game_active and event.key == pygame.K_RETURN:
                        self.reset_game()
                # Gamepad Inputs for fullscreen toggle and game restart
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()
                    # Restart only after game over / escape
                    if not self.game_active and event.button == 7:
                        self.reset_game()

            self.message_log.update() # Update message log to handle typing effect and message timing
            if self.game_active:
                if not self.is_transitioning and not self.is_busy: # Only allow player input if we're not in the middle of an animation or message
                    self.all_sprites.update()

                if not self.is_transitioning:
                    # Always run the animation math (so sprites can finish their slide)
                    for sprite in self.all_sprites:
                        if hasattr(sprite, 'animate'):
                            sprite.animate()

                    # Catch collisions immediately when a monster finishes moving onto the player.
                    self.check_player_caught_by_monster()

            # Drawing
            self.screen.fill('black')
            self.render.draw_grid_background() # Draw the grid background
            self.all_sprites.draw(self.screen) # Draw the sprites to the screen
            
            if not DebugSettings.NO_FOG: # Toggle Fog of War for testing
                self.render.draw_fog_of_war()
            self.render.draw_ui_frames() # Draw the UI frames and outlines
            self.message_log.draw(self.screen)
            self.inventory_window.draw(self.screen)
            self.map_window.draw(self.screen)
            self.render.draw_level_transition()
            self.render.draw_end_game_screens()
            if not self.is_transitioning:
                self.crt.draw() # CRT Effect on top of everything else

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()