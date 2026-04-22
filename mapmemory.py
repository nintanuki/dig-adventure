from settings import UISettings

class MapMemory:
    def __init__(self, game) -> None:
        self.game = game
        self.dungeon = self.game.dungeon

        self.seen_tiles = {}
        self.last_seen_monster_pos = set()
        self.last_seen_door_pos = None
    
    def player_can_see_grid_pos(self, target_grid_pos):
        """Check if a grid coordinate should be revealed on the minimap."""
        # If the player has the map, the whole minimap is revealed.
        if self.game.player.inventory.get("MAP", 0) > 0:
            return True

        player_grid_pos = self.game.screen_to_grid(
            self.game.player.position.x,
            self.game.player.position.y
        )

        reveal_radius = int(self.game.player.light_radius)

        if reveal_radius < 0:
            return False

        distance = self.dungeon.manhattan_distance(player_grid_pos, target_grid_pos)
        if distance > reveal_radius:
            return False

        return self.dungeon.has_line_of_sight(player_grid_pos, target_grid_pos)

    def remember_visible_map_info(self):
        """Persist anything currently visible to the minimap memory."""
        self._remember_visible_tiles()
        self._remember_visible_entities()

    def _remember_visible_tiles(self):
        """Persist visible terrain state (walls, dug tiles, and floor)."""
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

    def _remember_visible_entities(self):
        """Persist visible door and monster positions."""
        # remember door once seen
        door_grid_pos = self.game.screen_to_grid(self.game.door.position.x, self.game.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        visible_monster_positions = self.get_visible_monster_positions()

        if visible_monster_positions:
            self.last_seen_monster_pos = visible_monster_positions

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