"""Build (and rebuild) one dungeon level: terrain spawn, entity spawn, progress carry-over.

Pulled out of GameManager so 'how a level gets constructed' lives in one
place. GameManager keeps only the call sites — load on boot, on
start_gameplay_from_title, and after a successful door unlock.
"""

from util import coords
from core.dungeon_config import get_monster_count_for_dungeon
from ui.minimap_memory import MinimapMemory
from ui.render import RenderManager
from core.sprites import Door, Monster, NPC, Player


class LevelLoader:
    """Construct a fresh level world on top of an existing GameManager.

    Holds no state of its own; mutates GameManager attributes
    (dungeon, all_sprites, player, monsters, door, npcs, map_memory, render).
    """

    def __init__(self, game) -> None:
        """Bind to the active game manager.

        Args:
            game: The GameManager whose world this loader will populate.
        """
        self.game = game

    def load_level(self, player_progress: dict[str, object] | None = None) -> None:
        """Build the currently selected dungeon and spawn fresh entities.

        Args:
            player_progress: Optional snapshot from capture_player_progress to
                re-apply once the new player has been spawned. None means
                start fresh (e.g. on boot).
        """
        game = self.game
        game.all_sprites.empty()

        dungeon_name = game.level_order[game.current_level_index]
        monster_count = get_monster_count_for_dungeon(dungeon_name)
        game.dungeon.load_dungeon(dungeon_name)
        game.dungeon.setup_tile_map(monster_count=monster_count)

        # Door spawns first so other entities can avoid landing on it.
        self.spawn_door()
        self.spawn_monsters()
        self.spawn_npcs()
        self.spawn_player()
        self.restore_player_progress(player_progress)

        # Memory + renderer reference the freshly-spawned entities.
        game.map_memory = MinimapMemory(game)
        game.render = RenderManager(game)

    def spawn_player(self) -> None:
        """Spawn the player sprite at the dungeon's chosen player tile."""
        game = self.game
        col, row = game.dungeon.player_grid_pos
        x, y = coords.grid_to_screen(col, row)
        game.player = Player(game, (x, y), game.all_sprites)

    def spawn_monsters(self) -> None:
        """Spawn one monster sprite at each precomputed monster tile."""
        game = self.game
        game.monsters = []
        for col, row in game.dungeon.monster_grid_positions:
            x, y = coords.grid_to_screen(col, row)
            game.monsters.append(Monster(game, (x, y), game.all_sprites))

    def spawn_door(self) -> None:
        """Spawn the level door at the dungeon's chosen door tile."""
        game = self.game
        col, row = game.dungeon.door_grid_pos
        x, y = coords.grid_to_screen(col, row)
        game.door = Door(game, (x, y), game.all_sprites)

    def spawn_npcs(self) -> None:
        """Spawn one NPC sprite per dungeon NPC tile (zero or more)."""
        game = self.game
        game.npcs = []
        for col, row in game.dungeon.npc_grid_positions:
            x, y = coords.grid_to_screen(col, row)
            game.npcs.append(NPC(game, (x, y), game.all_sprites))

    def capture_player_progress(self) -> dict[str, object] | None:
        """Snapshot inventory and discovery before the player sprite is replaced.

        Returns:
            A dict with copies of the player's inventory and discovered
            items, or None if no player exists yet (first boot).
        """
        game = self.game
        if not hasattr(game, 'player'):
            return None
        return {
            'inventory': game.player.inventory.copy(),
            'discovered_items': set(game.player.discovered_items),
        }

    def restore_player_progress(self, progress: dict[str, object] | None) -> None:
        """Re-apply a snapshot to the freshly-spawned player.

        Args:
            progress: Output of capture_player_progress, or None to skip.
        """
        if not progress:
            return
        player = self.game.player
        player.inventory = progress['inventory'].copy()
        player.discovered_items = set(progress['discovered_items'])
