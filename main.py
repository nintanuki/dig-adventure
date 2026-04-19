import pygame
import sys
import random
import json

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog
import debug

class GameManager:
    def __init__(self):
        # Initialize Pygame and set up the display
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Dig Adventure')
        self.clock = pygame.time.Clock()
        
        self.setup_controllers() # Controller Setup
        self.load_assets() # Pre-load dirt asset to avoid loading it 60 times per second
        self.all_sprites = pygame.sprite.Group() # Create a group to hold all sprites
        self.audio = AudioManager() # Initialize the audio manager
        self.game_active = True
        self.spawn_door()
        self.spawn_player() # Spawn the player at a safe location
        self.spawn_monster()
        self.message_log = MessageLog(self)

    def setup_controllers(self):
        """Initializes connected gamepads or joysticks."""
        pygame.joystick.init()
        # Create a list of all connected controllers
        self.connected_joysticks = [pygame.joystick.Joystick(index) for index in range(pygame.joystick.get_count())]

    def load_assets(self):
        """Handle all image loading and scaling in one place."""
        dirt = pygame.image.load(AssetPaths.DIRT_TILE).convert_alpha()
        self.scaled_dirt_tile = pygame.transform.scale(dirt, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)) #
        
        wall = pygame.image.load(AssetPaths.WALL_TILE).convert_alpha()
        self.scaled_wall_tile = pygame.transform.scale(wall, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

    def spawn_player(self):
        """Calculates a safe spawn point and initializes the player sprite."""
        
        # Spawn the player at a random location within the Action Window, avoiding the walls
        # Calculate random grid coordinates (avoiding the walls by starting at 1 and ending at COLS-1 and ROWS-1)
        random_grid_column = random.randint(1, UISettings.COLS - 2)
        random_grid_row = random.randint(1, UISettings.ROWS - 2)

        # 2. Convert those grid coordinates into the actual screen anchor points
        # We take the Action Window's start point and add the tile offset
        player_screen_start_x = UISettings.ACTION_WINDOW_X + (random_grid_column * GridSettings.TILE_SIZE)
        player_screen_start_y = UISettings.ACTION_WINDOW_Y + (random_grid_row * GridSettings.TILE_SIZE)

        # 3. Create the player at that specific pixel location
        # Note: We initialize the sprite group here as well
        self.player = Player(self, (player_screen_start_x, player_screen_start_y), self.all_sprites)

    def spawn_monster(self):
        """Spawns a monster at a random valid location."""
        col = random.randint(1, UISettings.COLS - 2)
        row = random.randint(1, UISettings.ROWS - 2)
        
        x = UISettings.ACTION_WINDOW_X + (col * GridSettings.TILE_SIZE)
        y = UISettings.ACTION_WINDOW_Y + (row * GridSettings.TILE_SIZE)
        
        self.monster = Monster(self, (x, y), self.all_sprites)

    def spawn_door(self):
        """Spawns the door at a random location."""
        col = random.randint(1, UISettings.COLS - 2)
        row = random.randint(1, UISettings.ROWS - 2)
        # Simple check to ensure it's not on the player start
        if col == 1 and row == 1: col = 5 
        
        x = UISettings.ACTION_WINDOW_X + (col * GridSettings.TILE_SIZE)
        y = UISettings.ACTION_WINDOW_Y + (row * GridSettings.TILE_SIZE)
        
        # We save a reference to the door specifically so we can check it later
        self.door = Door(self, (x, y), self.all_sprites)

    def advance_turn(self):
        """Called whenever the player performs an action."""

        if not self.game_active:
            return

        self.monster.take_turn()

        # Check for Monster Collision (Loss)
        if self.player.position == self.monster.position:
            self.log_message("You were caught by the monster!")
            self.game_active = False

        # Check for Door Collision (Win)
        # Note: We'll add key requirements later, for now just touching it wins
        if self.player.position == self.door.position:
            self.door.open_door()
            self.log_message("You escaped the dungeon!")
            self.game_active = False

    def draw_grid_background(self):
        """
        Loops through the screen and draws the dirt tiles with grey outlines.
        Draws the dirt tiles only within the Action Window boundaries.
        """
        # Loop through columns and rows based on our calculated grid size
        for col in range(UISettings.COLS):
            for row in range(UISettings.ROWS):
                # Calculate the actual pixel position on the screen for each tile
                tile_window_x = UISettings.ACTION_WINDOW_X + (col * GridSettings.TILE_SIZE)
                tile_window_y = UISettings.ACTION_WINDOW_Y + (row * GridSettings.TILE_SIZE)

                # Check if this tile is on the edge of our grid
                is_wall = (col == 0 or col == UISettings.COLS - 1 or 
                        row == 0 or row == UISettings.ROWS - 1)

                # Draw the wall tile if it's an edge, otherwise draw the dirt tile
                if is_wall:
                    self.screen.blit(self.scaled_wall_tile, (tile_window_x, tile_window_y))
                else:
                    self.screen.blit(self.scaled_dirt_tile, (tile_window_x, tile_window_y))

                # Draw the faint grey grid lines
                tile_outline = pygame.Rect(tile_window_x, tile_window_y, GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
                pygame.draw.rect(self.screen, (60, 60, 60), tile_outline, 1)

    def draw_ui_frames(self):
        """Draws the aesthetic borders around the game and UI sections."""
        # The Action Window Frame
        action_frame_rect = pygame.Rect(
            UISettings.ACTION_WINDOW_X, 
            UISettings.ACTION_WINDOW_Y, 
            UISettings.ACTION_WINDOW_WIDTH, 
            UISettings.ACTION_WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, UISettings.BORDER_COLOR, action_frame_rect, 2, UISettings.BORDER_RADIUS)
        
        # Sidebar Window Frame
        sidebar_frame_rect = pygame.Rect(
            UISettings.SIDEBAR_X,
            UISettings.SIDEBAR_Y,
            UISettings.SIDEBAR_WIDTH,
            UISettings.SIDEBAR_HEIGHT)
        pygame.draw.rect(self.screen, UISettings.BORDER_COLOR, sidebar_frame_rect, 2, UISettings.BORDER_RADIUS)
        
        # Message Window Log Frame
        message_log_frame_rect = pygame.Rect(
            UISettings.LOG_X,
            UISettings.LOG_Y,
            UISettings.LOG_WIDTH,
            UISettings.LOG_HEIGHT)
        pygame.draw.rect(self.screen, UISettings.BORDER_COLOR, message_log_frame_rect, 2, UISettings.BORDER_RADIUS)

        # Map Window Frame
        map_frame_rect = pygame.Rect(
            UISettings.MAP_X,
            UISettings.MAP_Y,
            UISettings.MAP_WIDTH,
            UISettings.MAP_HEIGHT)
        pygame.draw.rect(self.screen, UISettings.BORDER_COLOR, map_frame_rect, 2, UISettings.BORDER_RADIUS)

    def log_message(self, text):
        """The central hub for all game objects to send text to the UI."""
        self.message_log.add_message(text)

    def draw_end_game_screens(self):
        # Draw Game Over Overlay
        if not self.game_active:
            # Dim the screen
            overlay = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0,0))

            # Setup font for large text
            big_font = pygame.font.Font(FontSettings.FONT, FontSettings.ENDGAME_SIZE)
            
            # Logic to decide if we won or lost for the text
            end_text = "VICTORY" if self.player.position == self.door.position else "GAME OVER"
            end_color = 'green' if end_text == "VICTORY" else 'red'
            
            # Render and Center
            text_surf = big_font.render(end_text, False, end_color)
            text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH/2, ScreenSettings.HEIGHT/2))
            self.screen.blit(text_surf, text_rect)

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

                # Handle fullscreen toggle with F11 key
                if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            pygame.display.toggle_fullscreen()

            # Only update sprites if the game is active. 
            # This prevents the player from moving after death.
            if self.game_active:
                self.all_sprites.update() # Update all sprites (calls their update method, if they have one)

            # Drawing
            self.screen.fill('black')
            self.draw_grid_background() # Draw the grid background
            self.all_sprites.draw(self.screen) # Draw the sprites to the screen
            self.draw_ui_frames() # Draw the UI frames and outlines
            self.message_log.draw(self.screen) # Draw text to the message log
            self.draw_end_game_screens()

            

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()