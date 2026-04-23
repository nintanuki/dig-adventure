from settings import UISettings

class MapMemory:
    """Track and expose the player's remembered minimap terrain and entities."""

    def __init__(self, game) -> None:
        """Initialize per-level map memory state.

        Args:
            game: Active game manager providing world and player state.
        """
        self.game = game
        self.dungeon = self.game.dungeon

        self.seen_tiles = {}
        self.last_seen_monster_pos = set()
        self.last_seen_door_pos = None

        if self.player_has_any_map():
            self.reveal_full_terrain_memory()

    def player_has_magic_map(self):
        """Return whether the player owns the magic map.

        Returns:
            bool: True when magic map inventory count is positive.
        """
        return self.game.player.inventory.get("MAGIC MAP", 0) > 0

    def player_has_regular_map(self):
        """Return whether the player owns the regular map.

        Returns:
            bool: True when regular map inventory count is positive.
        """
        return self.game.player.inventory.get("MAP", 0) > 0

    def player_has_any_map(self):
        """Return whether either map variant is owned.

        Returns:
            bool: True when regular or magic map is present.
        """
        return self.player_has_regular_map() or self.player_has_magic_map()

    def player_has_active_light_source(self):
        """Return whether the player currently emits light.

        Returns:
            bool: True when light radius is greater than zero.
        """
        return self.game.player.light_radius > 0

    def should_update_map_memory(self):
        """Return whether map memory should update this turn.

        Returns:
            bool: True when light is active or magic map is owned.
        """
        return self.player_has_active_light_source() or self.player_has_magic_map()

    def should_draw_player_on_minimap(self):
        """Return whether the player marker should render on the minimap.

        Returns:
            bool: True when marker visibility conditions are met.
        """
        return self.player_has_active_light_source() or self.player_has_magic_map()
    
    def player_can_see_grid_pos(self, target_grid_pos):
        """Check if terrain at a grid coordinate should be revealed.

        Args:
            target_grid_pos: Target (col, row) grid coordinate.

        Returns:
            bool: True when the tile is visible under current reveal rules.
        """
        # Owning either map reveals terrain without line-of-sight checks.
        if self.player_has_any_map():
            return True

        if not self.player_has_active_light_source():
            return False

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
        if not self.should_update_map_memory():
            return

        self._remember_visible_tiles()
        self._remember_visible_entities()

    def reveal_full_terrain_memory(self):
        """Reveal full terrain memory immediately when a map is obtained."""
        for row in range(UISettings.ROWS):
            for col in range(UISettings.COLS):
                grid_pos = (col, row)
                cell_type = self.game.dungeon.get_map_cell(col, row)

                if cell_type == "x":
                    self.seen_tiles[grid_pos] = "#"
                else:
                    tile_state = self.game.dungeon.tile_data.get(grid_pos)
                    if tile_state and tile_state["is_dug"]:
                        self.seen_tiles[grid_pos] = "o"
                    else:
                        self.seen_tiles[grid_pos] = " "

        door_grid_pos = self.game.screen_to_grid(self.game.door.position.x, self.game.door.position.y)
        self.last_seen_door_pos = door_grid_pos

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
        """Persist door and monster positions according to map type."""
        # Persist door once it has been observed.
        door_grid_pos = self.game.screen_to_grid(self.game.door.position.x, self.game.door.position.y)
        if self.player_can_see_grid_pos(door_grid_pos):
            self.last_seen_door_pos = door_grid_pos

        visible_monster_positions = self.get_visible_monster_positions()

        # Magic map tracks monsters in real time, including zero-visible states.
        if self.player_has_magic_map():
            self.last_seen_monster_pos = visible_monster_positions
        elif visible_monster_positions:
            self.last_seen_monster_pos = visible_monster_positions

    def get_visible_monster_positions(self):
        """Return currently visible monster coordinates.

        Returns:
            set[tuple[int, int]]: Visible monster grid positions.
        """
        visible_positions = set()

        for monster in self.game.monsters:
            monster_grid_pos = self.game.screen_to_grid(
                monster.position.x,
                monster.position.y
            )

            if self.player_has_magic_map() or self._can_see_entity_grid_pos(monster_grid_pos):
                visible_positions.add(monster_grid_pos)

        return visible_positions

    def _can_see_entity_grid_pos(self, target_grid_pos):
        """Check if an entity grid position is visible with light and LOS rules.

        Args:
            target_grid_pos: Target (col, row) entity coordinate.

        Returns:
            bool: True when the entity position is visible.
        """
        if not self.player_has_active_light_source():
            return False

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