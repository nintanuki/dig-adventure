"""Dungeon progression and spawn configuration.

Keeps difficulty buckets, level routing, and monster count rules outside tilemaps.py.
"""

from tilemaps import DUNGEONS


class DungeonConfig:
    """Own difficulty routing and per-dungeon spawn configuration."""

    DIFFICULTY_TUTORIAL = "TUTORIAL"
    DIFFICULTY_VERY_EASY = "VERY_EASY"
    DIFFICULTY_EASY = "EASY"
    DIFFICULTY_MEDIUM = "MEDIUM"
    DIFFICULTY_HARD = "HARD"
    DIFFICULTY_VERY_HARD = "VERY_HARD"

    def __init__(
        self,
        dungeons: dict,
        dungeon_difficulty: dict[str, str],
        dungeon_monster_counts: dict[str, int],
        level_difficulty_by_number: dict[int, str],
    ) -> None:
        self.dungeons = dungeons
        self.dungeon_difficulty = dungeon_difficulty
        self.dungeon_monster_counts = dungeon_monster_counts
        self.level_difficulty_by_number = level_difficulty_by_number

        self.validate_config_tables()
        self.dungeons_by_difficulty = self.build_dungeons_by_difficulty()
        self.level_dungeon_order = self.build_level_dungeon_order()

    @property
    def allowed_difficulties(self) -> set[str]:
        return {
            self.DIFFICULTY_TUTORIAL,
            self.DIFFICULTY_VERY_EASY,
            self.DIFFICULTY_EASY,
            self.DIFFICULTY_MEDIUM,
            self.DIFFICULTY_HARD,
            self.DIFFICULTY_VERY_HARD,
        }

    def validate_config_tables(self) -> None:
        """Validate metadata tables stay in sync with defined dungeons."""
        defined = set(self.dungeons.keys())

        difficulty_names = set(self.dungeon_difficulty.keys())
        monster_names = set(self.dungeon_monster_counts.keys())

        if difficulty_names != defined:
            raise ValueError(
                "DUNGEON_DIFFICULTY keys must match DUNGEONS exactly. "
                f"Missing: {sorted(defined - difficulty_names)}. "
                f"Extra: {sorted(difficulty_names - defined)}."
            )

        if monster_names != defined:
            raise ValueError(
                "DUNGEON_MONSTER_COUNTS keys must match DUNGEONS exactly. "
                f"Missing: {sorted(defined - monster_names)}. "
                f"Extra: {sorted(monster_names - defined)}."
            )

        for dungeon_name, difficulty in self.dungeon_difficulty.items():
            if difficulty not in self.allowed_difficulties:
                raise ValueError(
                    f"{dungeon_name} has invalid difficulty '{difficulty}'. "
                    f"Allowed values: {sorted(self.allowed_difficulties)}"
                )

        for dungeon_name, count in self.dungeon_monster_counts.items():
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"{dungeon_name} monster count must be a non-negative int.")

    def build_dungeons_by_difficulty(self) -> dict[str, list[str]]:
        """Group dungeons by difficulty preserving DUNGEONS definition order."""
        grouped = {
            self.DIFFICULTY_TUTORIAL: [],
            self.DIFFICULTY_VERY_EASY: [],
            self.DIFFICULTY_EASY: [],
            self.DIFFICULTY_MEDIUM: [],
            self.DIFFICULTY_HARD: [],
            self.DIFFICULTY_VERY_HARD: [],
        }

        for dungeon_name in self.dungeons:
            grouped[self.dungeon_difficulty[dungeon_name]].append(dungeon_name)

        return grouped

    def build_level_dungeon_order(
        self,
        level_difficulty_by_number: dict[int, str] | None = None,
    ) -> list[str]:
        """Build level->dungeon order from difficulty routing rules.

        Each dungeon is used at most once per playthrough.
        """
        difficulty_by_level = level_difficulty_by_number or self.level_difficulty_by_number
        level_numbers = sorted(difficulty_by_level.keys())
        if not level_numbers:
            return []

        start_level = level_numbers[0]
        expected = list(range(start_level, start_level + len(level_numbers)))
        if level_numbers != expected:
            raise ValueError(
                "LEVEL_DIFFICULTY_BY_NUMBER must use contiguous level numbers. "
                f"Found: {level_numbers}"
            )

        # Validate that each difficulty has enough unique maps for assigned levels.
        required_per_difficulty: dict[str, int] = {}
        for level_number in level_numbers:
            difficulty = difficulty_by_level[level_number]
            required_per_difficulty[difficulty] = required_per_difficulty.get(difficulty, 0) + 1

        for difficulty, required_count in required_per_difficulty.items():
            available_count = len(self.dungeons_by_difficulty.get(difficulty, []))
            if required_count > available_count:
                raise ValueError(
                    f"Difficulty '{difficulty}' needs {required_count} unique maps for this schedule, "
                    f"but only {available_count} are configured."
                )

        usage_counts: dict[str, int] = {}
        level_order = []

        for level_number in level_numbers:
            difficulty = difficulty_by_level[level_number]
            pool = self.dungeons_by_difficulty.get(difficulty)
            if not pool:
                raise ValueError(
                    f"No dungeons assigned to difficulty '{difficulty}' "
                    f"for level {level_number}."
                )

            index = usage_counts.get(difficulty, 0)
            dungeon_name = pool[index]
            usage_counts[difficulty] = index + 1
            level_order.append(dungeon_name)

        return level_order

    def get_monster_count_for_dungeon(self, dungeon_name: str) -> int:
        """Return configured monster count for one dungeon name."""
        if dungeon_name not in self.dungeon_monster_counts:
            raise KeyError(f"No monster count configured for dungeon: {dungeon_name}")
        return self.dungeon_monster_counts[dungeon_name]


DUNGEON_DIFFICULTY = {
    'The Arena': DungeonConfig.DIFFICULTY_TUTORIAL,
    'The Corners': DungeonConfig.DIFFICULTY_VERY_EASY,
    'The Lanes': DungeonConfig.DIFFICULTY_EASY,
    'The Clover': DungeonConfig.DIFFICULTY_EASY,
    'The Pillars': DungeonConfig.DIFFICULTY_VERY_EASY,
    'The H': DungeonConfig.DIFFICULTY_EASY,
    'The Gallery': DungeonConfig.DIFFICULTY_MEDIUM,
    'The Cross': DungeonConfig.DIFFICULTY_MEDIUM,
    'The Ring': DungeonConfig.DIFFICULTY_MEDIUM,
    'The Divided': DungeonConfig.DIFFICULTY_MEDIUM,
    'The Plus': DungeonConfig.DIFFICULTY_MEDIUM,
    'The Offset Hall': DungeonConfig.DIFFICULTY_HARD,
    'The Double Loop': DungeonConfig.DIFFICULTY_HARD,
    'The Pocket': DungeonConfig.DIFFICULTY_HARD,
    'The Zig-Zag': DungeonConfig.DIFFICULTY_HARD,
    'The Serpent': DungeonConfig.DIFFICULTY_VERY_HARD,
}

DUNGEON_MONSTER_COUNTS = {
    'The Arena': 1,
    'The Corners': 1,
    'The Lanes': 1,
    'The Clover': 1,
    'The Pillars': 2,
    'The H': 2,
    'The Gallery': 3,
    'The Cross': 3,
    'The Ring': 2,
    'The Divided': 4,
    'The Plus': 3,
    'The Offset Hall': 3,
    'The Double Loop': 4,
    'The Pocket': 4,
    'The Zig-Zag': 4,
    'The Serpent': 2,
}

LEVEL_DIFFICULTY_BY_NUMBER = {
    0: DungeonConfig.DIFFICULTY_TUTORIAL,
    1: DungeonConfig.DIFFICULTY_VERY_EASY,
    2: DungeonConfig.DIFFICULTY_VERY_EASY,
    3: DungeonConfig.DIFFICULTY_EASY,
    4: DungeonConfig.DIFFICULTY_EASY,
    5: DungeonConfig.DIFFICULTY_MEDIUM,
    6: DungeonConfig.DIFFICULTY_MEDIUM,
    7: DungeonConfig.DIFFICULTY_MEDIUM,
    8: DungeonConfig.DIFFICULTY_HARD,
    9: DungeonConfig.DIFFICULTY_HARD,
    10: DungeonConfig.DIFFICULTY_VERY_HARD,
}

DUNGEON_CONFIG = DungeonConfig(
    dungeons=DUNGEONS,
    dungeon_difficulty=DUNGEON_DIFFICULTY,
    dungeon_monster_counts=DUNGEON_MONSTER_COUNTS,
    level_difficulty_by_number=LEVEL_DIFFICULTY_BY_NUMBER,
)

DUNGEONS_BY_DIFFICULTY = DUNGEON_CONFIG.dungeons_by_difficulty
LEVEL_DUNGEON_ORDER = DUNGEON_CONFIG.level_dungeon_order


def get_monster_count_for_dungeon(dungeon_name: str) -> int:
    """Compatibility helper for existing imports."""
    return DUNGEON_CONFIG.get_monster_count_for_dungeon(dungeon_name)
