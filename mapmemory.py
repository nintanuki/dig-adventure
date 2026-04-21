from settings import UISettings

class MapMemory:
    def __init__(self, game) -> None:
        self.game = game
        self.dungeon = self.game.dungeon

        self.seen_tiles = {}
        self.last_map_player_pos = None
        self.last_seen_monster_pos = set()
        self.last_seen_door_pos = None
        self.map_snapshot_lines = []
    
    def player_can_see_grid_pos(self, target_grid_pos):
        """Check if a grid coordinate should be revealed on the minimap."""
        # If the player has the map, the whole minimap is revealed.
        if self.game.player.inventory.get("MAP", 0) > 0:
            return True

        player_grid_pos = self.game.screen_to_grid(
            self.game.player.position.x,
            self.game.player.position.y
        )

        reveal_radius = int(self.game.player.light_radius - 1)

        if reveal_radius < 0:
            return False

        distance = self.dungeon.manhattan_distance(player_grid_pos, target_grid_pos)
        if distance > reveal_radius:
            return False

        return self.dungeon.has_line_of_sight(player_grid_pos, target_grid_pos)

    def remember_visible_map_info(self):
        """Persist anything currently visible to the minimap memory."""
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                grid_pos = (col, row)

                if self.player_can_see_grid_pos(grid_pos):
                    cell_type = self.game.dungeon.get_map_cell(col, row)

                    if cell_type == "x":
                        self.seen_tiles[grid_pos] = "#"
                    else:
                        tile_state = self.game.dungeon.tile_data.get(grid_pos)
                        if tile_state and tile_state["is_dug"]:
                            self.seen_tiles[grid_pos] = "o"
                        else:
                            self.seen_tiles[grid_pos] = " "
                            
        # remember door once seen
        door_grid_pos = self.game.screen_to_grid(self.game.door.position.x, self.game.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        visible_monster_positions = self.get_visible_monster_positions()

        if visible_monster_positions:
            self.last_seen_monster_pos = visible_monster_positions

    def refresh_map_snapshot(self):
        """Update remembered map data using only what the player can currently see."""
        # Remember where the player was when they checked the map
        self.last_map_player_pos = self.game.screen_to_grid(self.game.player.position.x, self.game.player.position.y)

        # Reveal all tiles currently inside light radius
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                grid_pos = (col, row)

                if self.player_can_see_grid_pos(grid_pos):
                    cell_type = self.game.dungeon.get_map_cell(col, row)

                    # Store remembered terrain
                    if cell_type == "x":
                        self.seen_tiles[grid_pos] = "#"
                    else:
                        tile_state = self.game.dungeon.tile_data.get(grid_pos)

                        if tile_state and tile_state["is_dug"]:
                            self.seen_tiles[grid_pos] = "o"
                        else:
                            self.seen_tiles[grid_pos] = " "

        # Remember door location only if currently visible
        door_grid_pos = self.game.screen_to_grid(self.game.door.position.x, self.game.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        visible_monster_positions = self.get_visible_monster_positions()

        if visible_monster_positions:
            self.last_seen_monster_pos = visible_monster_positions

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
                if grid_pos in self.last_seen_monster_pos:
                    char = "M"
                if self.last_map_player_pos == grid_pos:
                    char = "P"

                chars.append(char)

            lines.append("".join(chars))

        self.map_snapshot_lines = lines

    def get_visible_monster_positions(self):
        """Return a set of monster grid positions currently visible to the player."""
        visible_positions = set()

        for monster in self.game.monsters:
            monster_grid_pos = self.game.screen_to_grid(
                monster.position.x,
                monster.position.y
            )

            if self.player_can_see_grid_pos(monster_grid_pos):
                visible_positions.add(monster_grid_pos)

        return visible_positions