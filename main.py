import pygame
import sys
import random
import json

from settings import *
from audio import AudioManager
from sprites import Player
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
        self.spawn_player() # Spawn the player at a safe location

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
        # 1. The Action Window Frame
        # We draw it 2 pixels wider than the window so it doesn't overlap tiles
        action_frame_rect = pygame.Rect(
            UISettings.ACTION_WINDOW_X - 2, 
            UISettings.ACTION_WINDOW_Y - 2, 
            UISettings.ACTION_WINDOW_WIDTH + 4, 
            UISettings.ACTION_WINDOW_HEIGHT + 4
        )
        pygame.draw.rect(self.screen, 'white', action_frame_rect, 2, border_radius=5)

        # 2. Sidebar Outline (Blue)
        sidebar_rect = pygame.Rect(
            ScreenSettings.WIDTH - UISettings.SIDEBAR_WIDTH, 0, 
            UISettings.SIDEBAR_WIDTH, ScreenSettings.HEIGHT
        )
        pygame.draw.rect(self.screen, 'blue', sidebar_rect, 2)

        # 3. Bottom Log Outline (Red)
        log_rect = pygame.Rect(
            0, ScreenSettings.HEIGHT - UISettings.BOTTOM_LOG_HEIGHT, 
            ScreenSettings.WIDTH, UISettings.BOTTOM_LOG_HEIGHT
        )
        pygame.draw.rect(self.screen, 'red', log_rect, 2)

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
            
            self.all_sprites.update() # Update all sprites (calls their update method, if they have one)
            
            # Drawing
            self.screen.fill('black')
            self.draw_grid_background() # Draw the grid background
            self.draw_ui_frames() # Draw the UI frames and outlines

            # Temporary UI Outlines for visualization (debugging purposes)
            # Sidebar
            # pygame.draw.rect(self.screen, 'blue', (ScreenSettings.WIDTH - UISettings.SIDEBAR_WIDTH, 0, UISettings.SIDEBAR_WIDTH, ScreenSettings.HEIGHT), 2)
            # Bottom Log
            # pygame.draw.rect(self.screen, 'red', (0, ScreenSettings.HEIGHT - UISettings.BOTTOM_LOG_HEIGHT, ScreenSettings.WIDTH, UISettings.BOTTOM_LOG_HEIGHT), 2)

            self.all_sprites.draw(self.screen) # Draw all sprites to the screen

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()