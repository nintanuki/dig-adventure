import pygame
import sys
import random
import json

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog, InventoryWindow
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
        self.setup_tile_map()
        self.spawn_door()
        self.spawn_player() # Spawn the player at a safe location
        self.spawn_monster()
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT))

        # Initialize Windows
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)

    def setup_controllers(self):
        """Initializes connected gamepads or joysticks."""
        pygame.joystick.init()
        # Create a list of all connected controllers
        self.connected_joysticks = [pygame.joystick.Joystick(index) for index in range(pygame.joystick.get_count())]

    def load_assets(self):
        """Handle all image loading and scaling in one place."""
        dirt_surf = pygame.image.load(AssetPaths.DIRT_TILE).convert_alpha()
        self.scaled_dirt_tile = pygame.transform.scale(dirt_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        
        dug_surf = pygame.image.load(AssetPaths.DUG_TILE).convert_alpha()
        self.scaled_dug_tile = pygame.transform.scale(dug_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        wall_surf = pygame.image.load(AssetPaths.WALL_TILE).convert_alpha()
        self.scaled_wall_tile = pygame.transform.scale(wall_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

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

        if not self.game_active: return

        # Count down effects
        if self.player.light_turns_left > 0:
            self.player.light_turns_left -= 1
            if self.player.light_turns_left == 0:
                self.player.light_radius = LightSettings.DEFAULT_RADIUS
                self.log_message("Your light flickers out...")

        if self.player.repellent_turns > 0:
            self.player.repellent_turns -= 1

        self.monster.take_turn()

        # Check for Monster Collision (Loss)
        if self.player.position == self.monster.position:
            self.log_message("You were caught by the monster!")
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
                    # Check if this specific tile has been dug
                    grid_pos = (col, row)
                    if self.tile_data.get(grid_pos, {}).get('is_dug'):
                        self.screen.blit(self.scaled_dug_tile, (tile_window_x, tile_window_y))
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

    def draw_fog_of_war(self):
        self.fog_surface.fill((0, 0, 0)) # Reset to pure black
        
        # Calculate player position relative to the action window
        p_x = self.player.position.x - UISettings.ACTION_WINDOW_X + (GridSettings.TILE_SIZE // 2)
        p_y = self.player.position.y - UISettings.ACTION_WINDOW_Y + (GridSettings.TILE_SIZE // 2)
        
        # Draw a "white" circle on the black surface (Alpha mask)
        # The radius is in pixels: (radius * tile_size)
        radius_px = self.player.light_radius * GridSettings.TILE_SIZE
        pygame.draw.circle(self.fog_surface, (255, 255, 255), (p_x, p_y), radius_px)
        
        # Use BLEND_RGBA_MULT to treat the fog_surface as a mask
        self.fog_surface.set_colorkey((255, 255, 255)) 
        self.screen.blit(self.fog_surface, (UISettings.ACTION_WINDOW_X, UISettings.ACTION_WINDOW_Y))

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

    def setup_tile_map(self):
        """Creates a dictionary to track the state and contents of every tile."""
        self.tile_data = {}
        
        # Initialize all tiles as undug and empty
        for col in range(1, UISettings.COLS - 1):
            for row in range(1, UISettings.ROWS - 1):
                self.tile_data[(col, row)] = {
                    'is_dug': False,
                    'item': None
                }
                
        # Randomly place the "Key" at a specific location
        # We turn the "dictionary keys" (the coordinates) into a list and pick one
        random_coords = list(self.tile_data.keys())
        key_pos = random.choice(random_coords)
        self.tile_data[key_pos]['item'] = 'Key'

    def get_item_at_tile(self, grid_pos):
        """Logic to decide what item is found when digging."""
        # 1. Check if a specific item (like the Key) was pre-placed
        if self.tile_data[grid_pos]['item']:
            return self.tile_data[grid_pos]['item']
        
        # 2. Otherwise, roll for a random item using your SPAWN_RATES
        roll = random.random()
        cumulative_chance = 0
        for item, chance in ItemSettings.SPAWN_CHANCE.items():
            cumulative_chance += chance
            if roll < cumulative_chance:
                return item
                
        return None

    @property
    def is_busy(self):
        """Centralized check to see if the game is currently animating."""
        return (self.player.is_moving or 
                self.monster.is_moving or 
                self.message_log.is_typing)

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

                # Handle fullscreen toggle with F11 key and select button
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()

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
            self.draw_grid_background() # Draw the grid background
            self.all_sprites.draw(self.screen) # Draw the sprites to the screen
            # self.draw_fog_of_war()
            self.draw_ui_frames() # Draw the UI frames and outlines
            self.message_log.draw(self.screen)
            self.inventory_window.draw(self.screen)
            self.draw_end_game_screens()

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()