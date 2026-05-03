"""Save-slot persistence for player progress between dungeon levels.

A save records the player's name, the next dungeon they will descend into,
their inventory and discovery state, and the score they had at the moment
the save was written. Saves are auto-written exactly once per cleared
dungeon: after treasure conversion finishes but before the shop opens. They
are never written on death, on quit, or on the final dungeon clear, so a
completed run leaves the save pointing at the shop before the final
dungeon.

Files live as JSON under saves/slot_NN.json (1-indexed). A save schema
version is included on every file so future schema changes can be detected.
"""

import json
import os

from settings import AssetPaths, GameSettings


class SaveManager:
    """Read, write, and enumerate per-slot JSON saves for the game.

    The manager is bound to the active GameManager only so callers do not
    have to pass paths around. It keeps no mutable state of its own.
    """

    # The whitelist for player names is everything the pixel font in
    # assets/font/Pixeled.ttf displays cleanly. Letters and digits are allowed in
    # any order, plus a literal space so multi-word names are possible.
    ALLOWED_NAME_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")

    def __init__(self, game) -> None:
        """Bind the manager to the active game instance.

        Args:
            game: Active GameManager instance.
        """
        self.game = game

    # -------------------------
    # PATHS
    # -------------------------

    def get_saves_dir(self) -> str:
        """Return the absolute path to the saves directory.

        Returns:
            Filesystem path for the saves directory.
        """
        # Anchor on the project root (AssetPaths.BASE_DIR) rather than this
        # file's directory; otherwise saves would land in systems/saves/
        # after this module moved into the systems/ package.
        return os.path.join(AssetPaths.BASE_DIR, GameSettings.SAVES_DIR)

    def get_slot_path(self, slot_id: int) -> str:
        """Return the absolute path for one slot's save file.

        Args:
            slot_id: 1-indexed slot number.

        Returns:
            Filesystem path for the slot's JSON file.
        """
        # Zero-pad to two digits so directory listings sort naturally even
        # if MAX_SAVE_SLOTS ever grows past 9.
        filename = f"slot_{slot_id:02d}.json"
        return os.path.join(self.get_saves_dir(), filename)

    def ensure_saves_dir(self) -> None:
        """Create the saves directory on disk if it does not yet exist.

        Called lazily before every write rather than at construction time so
        a read-only environment can still call list_slots without side
        effects.
        """
        os.makedirs(self.get_saves_dir(), exist_ok=True)

    # -------------------------
    # NAME SANITIZATION
    # -------------------------

    def sanitize_name(self, raw_name: str) -> str:
        """Normalize a typed name to the allowed character set and length.

        Uppercases every letter, drops anything not in ALLOWED_NAME_CHARS,
        collapses leading/trailing whitespace, and truncates to
        MAX_PLAYER_NAME_LENGTH.

        Args:
            raw_name: Raw name typed by the player.

        Returns:
            Sanitized, uppercased, trimmed name (may be empty).
        """
        upper = (raw_name or "").upper()
        filtered = "".join(ch for ch in upper if ch in self.ALLOWED_NAME_CHARS)
        # Trim outer whitespace but keep interior spaces so multi-word names
        # like "PLAYER 1" survive.
        trimmed = filtered.strip()
        return trimmed[: GameSettings.MAX_PLAYER_NAME_LENGTH]

    # -------------------------
    # SLOT VALIDITY
    # -------------------------

    def is_valid_slot(self, slot_id: int) -> bool:
        """Return whether the slot id is in the allowed 1..MAX_SAVE_SLOTS range.

        Args:
            slot_id: Candidate slot number.

        Returns:
            True when slot_id is a valid slot identifier.
        """
        return isinstance(slot_id, int) and 1 <= slot_id <= GameSettings.MAX_SAVE_SLOTS

    def is_slot_occupied(self, slot_id: int) -> bool:
        """Return whether a save file exists for the given slot.

        Args:
            slot_id: 1-indexed slot number.

        Returns:
            True when the slot's save file exists on disk.
        """
        if not self.is_valid_slot(slot_id):
            return False
        return os.path.exists(self.get_slot_path(slot_id))

    # -------------------------
    # LIST / LOAD / SAVE / DELETE
    # -------------------------

    def list_slots(self) -> list[dict]:
        """Return a summary entry for every slot in 1..MAX_SAVE_SLOTS.

        Each entry is a dict with keys:
            slot_id (int): 1-indexed slot number.
            occupied (bool): True when the slot has a parseable save.
            name (str | None): Player name, or None when empty/corrupt.
            level (int | None): Level the save resumes into.
            score (int | None): Saved score.
            gold (int | None): Saved gold coin count.
            corrupt (bool): True when a file exists but failed to parse.

        Returns:
            List of slot summary dicts, ordered by slot_id ascending.
        """
        summaries: list[dict] = []
        for slot_id in range(1, GameSettings.MAX_SAVE_SLOTS + 1):
            summary = {
                "slot_id": slot_id,
                "occupied": False,
                "name": None,
                "level": None,
                "score": None,
                "gold": None,
                "corrupt": False,
            }
            path = self.get_slot_path(slot_id)
            if not os.path.exists(path):
                summaries.append(summary)
                continue

            data = self.load_slot(slot_id)
            if data is None:
                # File exists but did not parse cleanly. Surface a corrupt
                # flag so the UI can show "EMPTY (corrupt)" rather than
                # crashing or silently hiding the file.
                summary["corrupt"] = True
                summaries.append(summary)
                continue

            inventory = data.get("inventory") or {}
            summary.update(
                occupied=True,
                name=data.get("player_name", ""),
                # `level` is the 1-indexed dungeon number the save resumes
                # into. A brand-new slot with no progress reads 1 here, so
                # the slot select row says "LV  1" rather than "LV  0".
                level=data.get("next_level"),
                score=data.get("score", 0),
                gold=int(inventory.get("GOLD COINS", 0)),
            )
            summaries.append(summary)
        return summaries

    def load_slot(self, slot_id: int) -> dict | None:
        """Load and return one slot's parsed JSON save.

        Args:
            slot_id: 1-indexed slot number.

        Returns:
            Save dict, or None when the slot is empty, missing, or
            unreadable.
        """
        if not self.is_valid_slot(slot_id):
            return None

        path = self.get_slot_path(slot_id)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as save_file:
                data = json.load(save_file)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None

        # Coerce discovered_items back to a set; JSON has no native set type
        # so it lands as a list. Callers expect a set so the player can use
        # `in` cheaply.
        if isinstance(data, dict) and isinstance(data.get("discovered_items"), list):
            data["discovered_items"] = set(data["discovered_items"])

        return data if isinstance(data, dict) else None

    def save_slot(
        self,
        slot_id: int,
        player_name: str,
        next_level: int,
        inventory: dict[str, int],
        discovered_items: set[str],
        score: int,
    ) -> bool:
        """Write one slot's save file.

        Args:
            slot_id: 1-indexed slot number to write into.
            player_name: Sanitized display name for the save.
            next_level: 1-indexed dungeon level the save resumes into.
                A brand-new save uses the first level number (1); after
                clearing a level, callers pass the level number the
                player is heading into next (e.g. 2 after beating 1).
            inventory: Dict of item name -> count. Caller is responsible
                for excluding level-scoped items.
            discovered_items: Set of item names the player has seen.
            score: Score accumulated so far this run.

        Returns:
            True on a successful write, False on any I/O or serialization
            failure.
        """
        if not self.is_valid_slot(slot_id):
            return False

        payload = {
            "save_version": GameSettings.SAVE_VERSION,
            "slot_id": slot_id,
            "player_name": player_name,
            "next_level": next_level,
            # Defensive copies so caller mutations after the call cannot
            # later corrupt the on-disk file via shared references.
            "inventory": dict(inventory),
            "discovered_items": sorted(discovered_items),
            "score": score,
        }

        try:
            self.ensure_saves_dir()
            with open(self.get_slot_path(slot_id), "w", encoding="utf-8") as save_file:
                json.dump(payload, save_file, indent=2)
        except OSError:
            return False
        return True

    def delete_slot(self, slot_id: int) -> bool:
        """Remove the save file for one slot, if present.

        Args:
            slot_id: 1-indexed slot number to delete.

        Returns:
            True when the slot is now empty (deleted or already absent).
            False on I/O errors.
        """
        if not self.is_valid_slot(slot_id):
            return False

        path = self.get_slot_path(slot_id)
        if not os.path.exists(path):
            return True

        try:
            os.remove(path)
        except OSError:
            return False
        return True
