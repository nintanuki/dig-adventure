import random
from settings import UISettings, ItemSettings
from tilemaps import DUNGEONS # Rename this dictionary to Dungeon_Maps or Blueprints or something

class DungeonMaster:
    def __init__(self, scaled_dirt_tiles: list) -> None:
        """
        Own the dungeon layout and mutable per-tile dungeon state.

        This class is responsible for selecting a dungeon, normalizing its layout,
        building runtime tile data, and answering questions about what exists in
        the dungeon.

        Args:
            scaled_dirt_tiles (list): Pre-scaled dirt tile surfaces used when
                building tile_data for diggable tiles.
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

    def load_random_dungeon(self) -> None:
        """
        Select a dungeon blueprint and normalize it into a usable grid.

        This converts the raw dungeon definition into a consistent internal
        format so the rest of the game can treat diggable terrain uniformly.
        It also validates the dungeon dimensions early so malformed maps fail
        fast during setup.

        Raises:
            ValueError: If the selected dungeon does not match the expected
                row or column count.
        """
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

    def setup_tile_map(self) -> None:
        """
        Build mutable per-tile state on top of the static dungeon layout.

        The dungeon grid stores the fixed structure of the map, while tile_data
        stores gameplay state that can change over time, such as whether a tile
        has been dug, what item is hidden there, and which dirt surface it uses.
        Only diggable tiles are included in tile_data.
        """
        self.tile_data = {}

        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                if self.is_diggable(col, row):
                    self.tile_data[(col, row)] = {
                        "is_dug": False,
                        "item": None,
                        "dirt_surface": random.choice(self.scaled_dirt_tiles),
                    }

        # Pre-place special items from map markers
        self.key_grid_pos = self.find_single_marker("K")
        self.tile_data[self.key_grid_pos]["item"] = "KEY"

        detector_grid_pos = self.find_single_marker("T")
        self.tile_data[detector_grid_pos]["item"] = "KEY DETECTOR"

        self.map_grid_pos = self.find_single_marker("C")
        self.tile_data[self.map_grid_pos]["item"] = "MAP"

    def get_item_at_tile(self, grid_pos: tuple[int, int]) -> tuple[str | None, int]:
        """
        Determine what item is revealed when a tile is dug.

        Pre-placed map items take priority. If no fixed item is stored at the
        tile, a random reward is rolled using the configured spawn chances and
        quantities.

        Args:
            grid_pos (tuple[int, int]): The tile position being dug.

        Returns:
            tuple[str | None, int]: A pair of (item_name, amount). Returns
                (None, 0) when no item is found.
        """
        # Check if a specific item (like the Key) was pre-placed
        if self.tile_data[grid_pos]["item"]:
            return self.tile_data[grid_pos]["item"], 1
        
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
    # MAP RULES / LOOKUPS
    # -------------------------

    def get_map_cell(self, col: int, row: int) -> str:
        """
        Return the raw dungeon symbol stored at a grid position.

        Out-of-bounds positions are treated as walls so movement and collision
        code can safely query the map without doing separate boundary checks.

        Args:
            col (int): Grid column.
            row (int): Grid row.

        Returns:
            str: The raw map symbol at that location. Returns "x" for walls and
                out-of-bounds positions.
        """
        if 0 <= row < len(self.current_grid) and 0 <= col < len(self.current_grid[row]):
            return self.current_grid[row][col]
        return "x"  # treat out of bounds as wall

    def is_walkable(self, col: int, row: int) -> bool:
        """
        Check whether an entity can occupy a grid position.

        Args:
            col (int): Grid column.
            row (int): Grid row.

        Returns:
            bool: True if the tile is not a wall. False for walls and
                out-of-bounds positions.
        """
        return self.get_map_cell(col, row) != "x"

    def is_diggable(self, col: int, row: int) -> bool:
        """
        Check whether the player can dig or search a grid position.

        Marker tiles are included so special items can still be discovered even
        when a tile originally contained something other than plain terrain.

        Args:
            col (int): Grid column.
            row (int): Grid row.

        Returns:
            bool: True if the tile should have mutable dig/search state. False
                for walls and out-of-bounds positions.
        """
        return self.get_map_cell(col, row) in {" ", "P", "M", "D", "K", "T", "C"}

    # Future refactor: consider replacing find_single_marker / find_multiple_markers
    # with a more unified marker lookup API.

    def find_single_marker(self, marker: str) -> tuple[int, int]:
        """
        Find the position of a unique marker in the current dungeon.

        Args:
            marker (str): The map symbol to search for.

        Returns:
            tuple[int, int]: The marker's grid position as (col, row).

        Raises:
            ValueError: If the marker does not exist in the current dungeon.
        """
        for row_index, row in enumerate(self.current_grid):
            for col_index, cell in enumerate(row):
                if cell == marker:
                    return (col_index, row_index)
        raise ValueError(f"Marker {marker!r} not found in dungeon {self.dungeon_name}")

    def find_multiple_markers(self, marker: str) -> list[tuple[int, int]]:
        """
        Find all positions of a repeated marker in the current dungeon.

        Args:
            marker (str): The map symbol to search for.

        Returns:
            list[tuple[int, int]]: A list of grid positions as (col, row).

        Raises:
            ValueError: If the marker does not appear anywhere in the dungeon.
        """
        positions: list[tuple[int, int]] = [] # Initialize an empty list to store found positions

        for row_index, row in enumerate(self.current_grid):
            for col_index, cell in enumerate(row):
                if cell == marker:
                    positions.append((col_index, row_index))

        if not positions:
            raise ValueError(f"Marker {marker!r} not found in dungeon {self.dungeon_name}")
        
        return positions
