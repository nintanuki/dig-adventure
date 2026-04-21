import pygame
import sys
import random
import json

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog, InventoryWindow, MapWindow
# from tilemaps import DUNGEONS # is this being used outside of DungeonMaster?
from dungeon import DungeonMaster
from mapmemory import MapMemory
from render import RenderManager
from crt import CRT

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

        self.dungeon.load_random_dungeon()
        self.dungeon.setup_tile_map()
        self.spawn_door()
        self.spawn_monster()
        self.spawn_player() # Spawn the player at a safe location
        
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # Initialize Windows
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)
        self.map_memory = MapMemory(self)

        # CRT Effect
        self.crt = CRT(self.screen)

        # Render Manager
        self.render = RenderManager(self)

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
        col, row = self.dungeon.find_single_marker("P")
        x, y = self.grid_to_screen(col, row)
        self.player = Player(self, (x, y), self.all_sprites)

    def spawn_monster(self):
        self.monsters = []
        for col, row in self.dungeon.find_multiple_markers("M"):
            x, y = self.grid_to_screen(col, row)
            monster = Monster(self, (x, y), self.all_sprites)
            self.monsters.append(monster)

    def spawn_door(self):
        col, row = self.dungeon.find_single_marker("D")
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

        if not self.game_active: return

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

        for monster in self.monsters:
            monster.take_turn()

        # Check for Monster Collision (Loss)
        for monster in self.monsters:
            if self.player.position == monster.position:
                self.log_message("YOU WERE CAUGHT BY THE MONSTER!")
                pygame.mixer.music.stop() # Stop the music immediately on death
                self.audio.play_scream_sound()
                self.game_active = False
                break

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
    # MAIN LOOP
    # -------------------------

    def run(self):
        """
        Run the game loop.
        """
        # Main game loop
        while True:
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

            # Only update sprites if the game is active. 
            # This prevents the player from moving after death.
            if self.game_active:
                # Always update the log (it handles its own typing timer)
                self.message_log.update()
                # Call sprites update functions ONLY if not busy
                if not self.is_busy:
                    self.all_sprites.update()
                # Always run the animation math (so sprites can finish their slide)
                for sprite in self.all_sprites:
                    if hasattr(sprite, 'animate'):
                        sprite.animate()

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
            self.render.draw_end_game_screens()
            self.crt.draw() # CRT Effect on top of everything else

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()