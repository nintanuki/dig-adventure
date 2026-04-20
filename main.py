import pygame
import sys
import random
import json

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog, InventoryWindow, MapWindow
from tilemaps import DUNGEONS
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
        self.all_sprites = pygame.sprite.Group() # Create a group to hold all sprites
        self.audio = AudioManager() # Initialize the audio manager
        self.game_active = True

        self.load_random_dungeon()
        self.setup_tile_map()
        self.spawn_door()
        self.spawn_monster()
        self.spawn_player() # Spawn the player at a safe location
        
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # Initialize Windows
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)

        # Variables to track what the player has seen for map drawing
        self.seen_tiles = {}
        self.last_map_player_pos = None
        self.last_seen_monster_pos = set()
        self.last_seen_door_pos = None
        self.map_snapshot_lines = []

        # CRT Effect
        self.crt = CRT(self.screen)

    def load_random_dungeon(self):
        """Pick one dungeon and cache all map info for this run."""
        self.dungeon_name, dungeon_data = random.choice(list(DUNGEONS.items()))
        self.dungeon_desc = dungeon_data["desc"]

        # Normalize map symbols so '.' also counts as walkable dirt
        self.current_grid = []
        for row in dungeon_data["grid"]:
            normalized_row = []
            for cell in row:
                normalized_row.append(" " if cell == "." else cell)
            self.current_grid.append(normalized_row)

        # Optional safety check
        if len(self.current_grid) != UISettings.ROWS:
            raise ValueError(f"{self.dungeon_name} has wrong row count.")
        for row in self.current_grid:
            if len(row) != UISettings.COLS:
                raise ValueError(f"{self.dungeon_name} has wrong column count.")

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

    def get_map_cell(self, col, row):
        if 0 <= row < len(self.current_grid) and 0 <= col < len(self.current_grid[row]):
            return self.current_grid[row][col]
        return "x"  # treat out of bounds as wall

    def is_walkable(self, col, row):
        """Tiles entities can stand on."""
        return self.get_map_cell(col, row) != "x"

    def is_diggable(self, col, row):
        """Tiles the player can dig/search."""
        return self.get_map_cell(col, row) in {" ", "P", "M", "D", "K", "T", "C"}

    def find_single_marker(self, marker):
        for row_idx, row in enumerate(self.current_grid):
            for col_idx, cell in enumerate(row):
                if cell == marker:
                    return (col_idx, row_idx)
        raise ValueError(f"Marker {marker!r} not found in dungeon {self.dungeon_name}")

    def find_multiple_markers(self, marker):
        positions = []
        for row_idx, row in enumerate(self.current_grid):
            for col_idx, cell in enumerate(row):
                if cell == marker:
                    positions.append((col_idx, row_idx))
        if not positions:
            raise ValueError(f"Marker {marker!r} not found in dungeon {self.dungeon_name}")
        return positions

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

    def spawn_player(self):
        col, row = self.find_single_marker("P")
        x, y = self.grid_to_screen(col, row)
        self.player = Player(self, (x, y), self.all_sprites)

    def spawn_monster(self):
        self.monsters = []
        for col, row in self.find_multiple_markers("M"):
            x, y = self.grid_to_screen(col, row)
            monster = Monster(self, (x, y), self.all_sprites)
            self.monsters.append(monster)

    def spawn_door(self):
        col, row = self.find_single_marker("D")
        x, y = self.grid_to_screen(col, row)
        self.door = Door(self, (x, y), self.all_sprites)

    def advance_turn(self):
        """Called whenever the player performs an action."""

        if not self.game_active: return

        self.remember_visible_map_info()

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
                self.audio.play_scream_sound()
                self.game_active = False
                break
            
    def draw_grid_background(self):
        """
        Loops through the screen and draws the dirt tiles with grey outlines.
        Draws the dirt tiles only within the Action Window boundaries.
        """
        # Loop through columns and rows based on our calculated grid size
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                x, y = self.grid_to_screen(col, row)
                cell_type = self.get_map_cell(col, row)

                if cell_type == "x":
                    self.screen.blit(self.scaled_wall_tile, (x, y))
                else:
                    tile_state = self.tile_data.get((col, row))
                    if tile_state and tile_state["is_dug"]:
                        self.screen.blit(self.scaled_dug_tile, (x, y))
                    elif tile_state:
                        self.screen.blit(tile_state["dirt_surface"], (x, y))
                    else:
                        # fallback for any non-wall tile that wasn't added to tile_data
                        self.screen.blit(random.choice(self.scaled_dirt_tiles), (x, y))

                if DebugSettings.GRID: # Toggle grey outlines for debugging
                    tile_outline = pygame.Rect(x, y, GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
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
        self.fog_surface.fill((0, 0, 0, 255)) # Start with a fully opaque black surface

        # We are going to create a circular gradient mask that will "punch through" the fog of war to create our light radius effect.
        # This will create a more natural looking light effect with smooth edges
        if self.player.light_radius > 0:
            radius_px = int(self.player.light_radius * GridSettings.TILE_SIZE)
            
            # Create the mask surface (Twice the radius)
            # This must be SRCALPHA and we start it COMPLETELY transparent
            light_mask = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
            light_mask.fill((0, 0, 0, 0)) 
            
            # Draw a WHITE gradient from the center outwards
            # Center = White (Alpha 255)
            # Edge = Transparent (Alpha 0)
            for i in range(radius_px, 0, -1):
                # Inner circles are more opaque (brighter)
                alpha = int(255 * (1 - (i / radius_px)))
                pygame.draw.circle(light_mask, (255, 255, 255, alpha), (radius_px, radius_px), i)
            
            # Center it on the player
            player_center = (
                self.player.rect.centerx - UISettings.ACTION_WINDOW_X,
                self.player.rect.centery - UISettings.ACTION_WINDOW_Y
            )
            mask_rect = light_mask.get_rect(center=player_center)
            
            # THE MAGIC BLEND MODE: BLEND_RGBA_SUB
            # We are SUBTRACTING our white gradient from the black fog.
            # (Black 255 Alpha) - (White 255 Alpha) = (Black 0 Alpha) -> Transparent!
            # Since the area outside the circle is 0 alpha, nothing gets subtracted, 
            # so the fog stays black and square-free.
            self.fog_surface.blit(light_mask, mask_rect, special_flags=pygame.BLEND_RGBA_SUB)

        # Blit the fog to the screen
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
            end_text = "ESCAPE" if self.player.position == self.door.position else "GAME OVER"
            end_color = 'green' if end_text == "ESCAPE" else 'red'
            
            # Render and Center
            text_surf = big_font.render(end_text, False, end_color)
            text_rect = text_surf.get_rect(center=(ScreenSettings.WIDTH/2, ScreenSettings.HEIGHT/2))
            self.screen.blit(text_surf, text_rect)

    def setup_tile_map(self):
        """Build per-tile state from the selected dungeon grid."""
        self.tile_data = {}

        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                cell_type = self.get_map_cell(col, row)

                if self.is_diggable(col, row):
                    self.tile_data[(col, row)] = {
                        "is_dug": False,
                        "item": None,
                        "dirt_surface": random.choice(self.scaled_dirt_tiles),
                    }

        # Pre-place special items from map markers
        self.key_grid_pos = self.find_single_marker("K")
        self.tile_data[self.key_grid_pos]["item"] = "KEY"

        detector_pos = self.find_single_marker("T")
        self.tile_data[detector_pos]["item"] = "KEY DETECTOR"

        self.map_grid_pos = self.find_single_marker("C")
        self.tile_data[self.map_grid_pos]["item"] = "MAP"

    def get_item_at_tile(self, grid_pos):
        """Logic to decide what item is found when digging."""
        # 1. Check if a specific item (like the Key) was pre-placed
        if self.tile_data[grid_pos]['item']:
            return self.tile_data[grid_pos]['item'], 1
        
        # 2. Otherwise, roll for a random item using your SPAWN_RATES
        roll = random.random()
        cumulative_chance = 0
        for item, chance in ItemSettings.SPAWN_CHANCE.items():
            cumulative_chance += chance
            if roll < cumulative_chance:
                # If this item is selected to spawn, we then check how many should spawn
                min_qty, max_qty = ItemSettings.SPAWN_QUANTITIES.get(item, (1, 1)) # Default to 1 if not specified
                amount = random.randint(min_qty, max_qty) # Random quantity within the defined range for this item
                return item, amount
                
        return None, 0

    def player_can_see_grid_pos(self, target_grid_pos):
        """Check if a grid coordinate should be revealed on the minimap."""
        p_col, p_row = self.screen_to_grid(self.player.position.x, self.player.position.y)
        t_col, t_row = target_grid_pos

        dx = abs(p_col - t_col)
        dy = abs(p_row - t_row)

        distance = dx + dy
        reveal_radius = int(self.player.light_radius - 1)

        return distance <= reveal_radius

    def remember_visible_map_info(self):
        """Persist anything currently visible to the minimap memory."""
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                grid_pos = (col, row)

                if self.player_can_see_grid_pos(grid_pos):
                    cell_type = self.get_map_cell(col, row)

                    if cell_type == "x":
                        self.seen_tiles[grid_pos] = "#"
                    else:
                        tile_state = self.tile_data.get(grid_pos)
                        if tile_state and tile_state["is_dug"]:
                            self.seen_tiles[grid_pos] = "o"
                        else:
                            self.seen_tiles[grid_pos] = " "
                            
        # remember door once seen
        door_grid_pos = self.screen_to_grid(self.door.position.x, self.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        # remember monster positions when seen
        for monster in self.monsters:
            monster_grid_pos = self.screen_to_grid(monster.position.x, monster.position.y)
            if self.player_can_see_grid_pos(monster_grid_pos):
                self.last_seen_monster_pos.add(monster_grid_pos)

    def refresh_map_snapshot(self):
        """Update remembered map data using only what the player can currently see."""
        # Remember where the player was when they checked the map
        self.last_map_player_pos = self.screen_to_grid(self.player.position.x, self.player.position.y)

        # Reveal all tiles currently inside light radius
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                grid_pos = (col, row)

                if self.player_can_see_grid_pos(grid_pos):
                    cell_type = self.get_map_cell(col, row)

                    # Store remembered terrain
                    if cell_type == "x":
                        self.seen_tiles[grid_pos] = "#"
                    else:
                        tile_state = self.tile_data.get(grid_pos)

                        if tile_state and tile_state["is_dug"]:
                            self.seen_tiles[grid_pos] = "o"
                        else:
                            self.seen_tiles[grid_pos] = " "

        # Remember door location only if currently visible
        door_grid_pos = self.screen_to_grid(self.door.position.x, self.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        # Remember monster location only if currently visible
        for monster in self.monsters:
            monster_grid_pos = self.screen_to_grid(monster.position.x, monster.position.y)
            if self.player_can_see_grid_pos(monster_grid_pos):
                self.last_seen_monster_pos.add(monster_grid_pos)

        # Build the frozen text snapshot for the UI
        self.build_map_snapshot_lines()

    def build_map_snapshot_lines(self):
        """Build the text rows that the map window will render."""
        lines = []

        for row in range(UISettings.ROWS):
            chars = []

            for col in range(UISettings.COLS):
                grid_pos = (col, row)
                char = " "

                if grid_pos in self.seen_tiles:
                    char = self.seen_tiles[grid_pos]

                # Overlay remembered special markers
                if self.last_seen_door_pos == grid_pos:
                    char = "D"
                if self.last_seen_monster_pos == grid_pos:
                    char = "M"
                if self.last_map_player_pos == grid_pos:
                    char = "P"

                chars.append(char)

            lines.append("".join(chars))

        self.map_snapshot_lines = lines

    def update_map_data(self):
        """Scan the grid and update what the player has discovered."""
        for r in range(UISettings.ROWS):
            for c in range(UISettings.COLS):
                if self.player_can_see_grid_pos((c, r)):
                    # Add to discovered tiles
                    self.seen_tiles[(c, r)] = self.current_grid[r][c]
                    
                    # If monster is here, update its last known location
                    m_col, m_row = self.screen_to_grid(self.monster.position.x, self.monster.position.y)
                    if c == m_col and r == m_row:
                        # We use a set so we can clear/update the red dot
                        self.last_seen_monster_pos = {(m_col, m_row)}

    @property
    def is_busy(self):
        """Centralized check to see if the game is currently animating."""
        return (self.player.is_moving or 
                any(monster.is_moving for monster in self.monsters) or
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
            
            if not DebugSettings.NO_FOG: # Toggle Fog of War for testing
                self.draw_fog_of_war()
            self.draw_ui_frames() # Draw the UI frames and outlines
            self.message_log.draw(self.screen)
            self.inventory_window.draw(self.screen)
            self.map_window.draw(self.screen)
            self.draw_end_game_screens()
            self.crt.draw() # CRT Effect on top of everything else

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()