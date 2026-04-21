import random
from settings import UISettings, ItemSettings, MonsterSettings
from tilemaps import DUNGEONS

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
        self.current_grid = []
        self.tile_data = {}

        self.player_grid_pos = None
        self.door_grid_pos = None
        self.monster_grid_positions = []
        self.key_grid_pos = None

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

        # Randomize all important positions
        self.player_grid_pos = self.get_random_walkable_position()
        self.door_grid_pos = self.get_random_walkable_position()

        monster_count = MonsterSettings.COUNT
        self.monster_grid_positions = [
            self.get_random_walkable_position()
            for _ in range(monster_count)
        ]

        self.key_grid_pos = self.place_fixed_item("KEY")
        self.place_fixed_item("KEY DETECTOR")
        self.place_fixed_item("MAP")

    def get_walkable_positions(self) -> list[tuple[int, int]]:
        positions = []

        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                if self.is_walkable(col, row):
                    positions.append((col, row))

        return positions


    def get_random_walkable_position(self) -> tuple[int, int]:
        return random.choice(self.get_walkable_positions())

    def place_fixed_item(self, item_name: str) -> tuple[int, int]:
        """Place a fixed item on a random walkable tile and return its position."""
        grid_pos = self.get_random_walkable_position()
        self.tile_data[grid_pos]["item"] = item_name
        return grid_pos

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
        return self.get_map_cell(col, row) == " "

    def blocks_vision(self, col: int, row: int) -> bool:
        """
        Return True if this tile blocks sight.

        For now, walls are the only vision blockers.
        """
        return self.get_map_cell(col, row) == "x"
    
    def manhattan_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        """
        Return Manhattan distance between two grid positions.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_line_points(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Return all grid points on a line from start to end using Bresenham's algorithm.
        """
        x1, y1 = start
        x2, y2 = end

        points = []

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        x, y = x1, y1
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1

        if dx > dy:
            err = dx / 2.0
            while x != x2:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        points.append((x2, y2))
        return points
    
    def has_line_of_sight(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """
        Return True if sight from start to end is not blocked by walls.

        The start tile and end tile themselves are allowed; only tiles in between
        can block vision.
        """
        line_points = self.get_line_points(start, end)

        for col, row in line_points[1:-1]:
            if self.blocks_vision(col, row):
                return False

        return True