import random
from settings import UISettings, ItemSettings
from tilemaps import DUNGEONS # Rename this dictionary to Dungeon_Maps or Blueprints or something

class DungeonMaster:
    def __init__(self, scaled_dirt_tiles):
        """
        Own the dungeon layout and all mutable per-tile dungeon state.

        GameManager still handles orchestration, rendering, and entities.
        DungeonMaster answers questions about the dungeon itself.
        """
        self.scaled_dirt_tiles = scaled_dirt_tiles

        self.dungeon_name = None
        self.dungeon_desc = None
        self.current_grid = []
        self.tile_data = {}

        self.key_grid_pos = None
        self.map_grid_pos = None

    # -------------------------
    # DUNGEON / MAP BUILDING
    # -------------------------

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

        # Safeguard: Ensure the grid matches expected dimensions
        if len(self.current_grid) != UISettings.ROWS:
            raise ValueError(f"{self.dungeon_name} has wrong row count.")
        for row in self.current_grid:
            if len(row) != UISettings.COLS:
                raise ValueError(f"{self.dungeon_name} has wrong column count.")

    def setup_tile_map(self):
        """
        Create the per-tile runtime state for the selected dungeon.

        The dungeon layout defines the fixed structure, while tile_data stores
        the mutable state that can change during play, such as digging and items.
        """
        self.tile_data = {}

        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                # cell_type = self.get_map_cell(col, row)
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
        # Check if a specific item (like the Key) was pre-placed
        if self.tile_data[grid_pos]['item']:
            return self.tile_data[grid_pos]['item'], 1
        
        # Otherwise, roll for a random item using your SPAWN_RATES
        roll = random.random()
        cumulative_chance = 0

        # Iterate through items and their spawn chances to determine what item, if any, spawns
        for item, chance in ItemSettings.SPAWN_CHANCE.items():
            cumulative_chance += chance
            if roll < cumulative_chance:
                # If this item is selected to spawn, we then check how many should spawn
                min_qty, max_qty = ItemSettings.SPAWN_QUANTITIES.get(item, (1, 1)) # Default to 1 if not specified
                amount = random.randint(min_qty, max_qty) # Random quantity within the defined range for this item
                return item, amount
                
        return None, 0
    
    # -------------------------
    # COORDINATE + MAP HELPERS
    # -------------------------

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
