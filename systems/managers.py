import os
import pygame

from settings import GameSettings, ItemSettings, UISettings, InputSettings


class ScoreLeaderboardManager:
    """Handle score accumulation plus high-score and leaderboard persistence."""

    def __init__(self, game) -> None:
        """Store shared game reference for score and UI state updates.

        Args:
            game: Active game manager instance.
        """
        self.game = game

    # -------------------------
    # PERSISTENCE
    # -------------------------

    def get_leaderboard_path(self) -> str:
        """Return the absolute path to the leaderboard data file.

        Returns:
            Filesystem path for the leaderboard file.
        """
        return os.path.join(os.path.dirname(__file__), GameSettings.LEADERBOARD_FILE)

    def load_high_score(self) -> int:
        """Return the current high score by reading the top leaderboard entry.

        The high score is no longer stored in its own file. The leaderboard's
        top entry is the single source of truth, so this method derives the
        value from there. Returns zero when no leaderboard entries exist.

        Returns:
            High score value, or zero if no leaderboard entries exist.
        """
        entries = self.load_leaderboard()
        if not entries:
            return 0
        return entries[0][1]

    def save_high_score(self) -> None:
        """Refresh the in-memory high score from leaderboard state.

        Kept as a no-write operation rather than removed so existing call
        sites still work and the public surface of ScoreLeaderboardManager
        stays stable. Persistence happens through save_leaderboard whenever
        a new entry qualifies; this method simply re-syncs the cached
        value the HUD reads each frame.
        """
        self.game.high_score = max(self.game.high_score, self.game.score)

    def load_leaderboard(self) -> list[tuple[str, int]]:
        """Load top scores from disk in descending order.

        Returns:
            list[tuple[str, int]]: Sorted leaderboard entries.
        """
        leaderboard_path = self.get_leaderboard_path()
        if not os.path.exists(leaderboard_path):
            return []

        entries: list[tuple[str, int]] = []
        try:
            with open(leaderboard_path, "r", encoding="utf-8") as board_file:
                for raw_line in board_file:
                    line = raw_line.strip()
                    if not line or "," not in line:
                        continue

                    initials, score_text = line.split(",", 1)
                    try:
                        score = int(score_text.strip())
                    except ValueError:
                        continue

                    if score < 0:
                        continue

                    entries.append((self.sanitize_initials(initials), score))
        except OSError:
            return []

        entries.sort(key=lambda entry: entry[1], reverse=True)
        return entries[: GameSettings.LEADERBOARD_LIMIT]

    def save_leaderboard(self) -> None:
        """Persist leaderboard entries to disk."""
        try:
            with open(self.get_leaderboard_path(), "w", encoding="utf-8") as board_file:
                for initials, score in self.game.leaderboard:
                    board_file.write(f"{initials},{score}\n")
        except OSError:
            pass

    # -------------------------
    # SCORING
    # -------------------------

    def add_score(self, item_name: str, amount: int = 1) -> None:
        """Increase score from one treasure pickup.

        Args:
            item_name: Treasure item key.
            amount: Quantity collected.
        """
        value = ItemSettings.TREASURE_SCORE_VALUES.get(item_name, 0)
        self.game.score += value * amount

    def sanitize_initials(self, initials: str) -> str:
        """Normalize initials to exactly three uppercase alphabetic characters.

        Args:
            initials: Raw initials input.

        Returns:
            Sanitized three-character initials string.
        """
        letters = "".join(char for char in initials.upper() if char.isalpha())
        return (letters[:3]).ljust(3, "A")

    def is_top_ten_score(self, score: int) -> bool:
        """Return True when score qualifies for leaderboard entry.

        Args:
            score: Candidate score.

        Returns:
            True when score should be entered.
        """
        if score <= 0:
            return False

        if len(self.game.leaderboard) < GameSettings.LEADERBOARD_LIMIT:
            return True

        return score >= self.game.leaderboard[-1][1]

    def add_leaderboard_entry(self, initials: str, score: int) -> None:
        """Insert and persist one top-score entry.

        Args:
            initials: Player initials.
            score: Final score for this run.
        """
        clean_initials = self.sanitize_initials(initials)
        existing_index = next(
            (index for index, (name, _) in enumerate(self.game.leaderboard) if name == clean_initials),
            None,
        )

        if existing_index is not None:
            if score <= self.game.leaderboard[existing_index][1]:
                return
            self.game.leaderboard[existing_index] = (clean_initials, score)
        else:
            self.game.leaderboard.append((clean_initials, score))

        self.game.leaderboard.sort(key=lambda entry: entry[1], reverse=True)
        self.game.leaderboard = self.game.leaderboard[: GameSettings.LEADERBOARD_LIMIT]
        self.game.high_score = max(self.game.high_score, self.game.leaderboard[0][1] if self.game.leaderboard else 0)
        self.save_leaderboard()

    # -------------------------
    # GAME-OVER FLOW
    # -------------------------

    def update_game_over_flow(self) -> None:
        """Reveal continue prompt after game-over text is fully typed."""
        if self.game.ui_state != "game_over" or self.game.game_result != "loss":
            return

        if self.game.message_log.is_typing:
            return

        now = pygame.time.get_ticks()
        if self.game.game_over_message_complete_time == 0:
            self.game.game_over_message_complete_time = now
            self.game.game_over_prompt_start_time = now + GameSettings.GAME_OVER_CONTINUE_DELAY_MS

    def can_continue_from_game_over(self) -> bool:
        """Return whether the continue action is currently allowed.

        Returns:
            True when continue action should be accepted.
        """
        if self.game.ui_state != "game_over":
            return False

        if self.game.game_result != "loss":
            return True

        return (
            self.game.game_over_prompt_start_time > 0
            and pygame.time.get_ticks() >= self.game.game_over_prompt_start_time
        )

    def continue_from_game_over(self) -> None:
        """Route from the game-over screen based on the run outcome.

        On a loss, the run is over and we drop the player back to a fresh
        title screen via reset_game(). The leaderboard is reserved for
        completed runs only, so deaths neither prompt for initials nor
        write a leaderboard entry. On a win, we proceed into the existing
        initials-entry or leaderboard flow.
        """
        if self.game.game_result == "loss":
            self.game.reset_game()
            return

        if self.is_top_ten_score(self.game.pending_leaderboard_score):
            self.game.ui_state = "enter_initials"
            self.game.initials_entry = "AAA"
            self.game.initials_index = 0
            return

        self.game.ui_state = "leaderboard"

    # -------------------------
    # INITIALS ENTRY
    # -------------------------

    def submit_initials_entry(self) -> None:
        """Commit initials and transition to leaderboard screen."""
        self.add_leaderboard_entry(self.game.initials_entry, self.game.pending_leaderboard_score)
        self.game.ui_state = "leaderboard"

    def handle_initials_event(self, event: pygame.event.Event) -> None:
        """Handle keyboard/controller input while entering initials.

        Args:
            event: Input event to process.
        """
        if self.game.ui_state != "enter_initials":
            return

        if event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value

            if hat_x == -1:
                self.game.initials_index = max(0, self.game.initials_index - 1)
            elif hat_x == 1:
                self.game.initials_index = min(2, self.game.initials_index + 1)

            if hat_y == 1:
                chars = list(self.game.initials_entry)
                current = chars[self.game.initials_index]
                chars[self.game.initials_index] = "A" if current == "Z" else chr(ord(current) + 1)
                self.game.initials_entry = "".join(chars)
            elif hat_y == -1:
                chars = list(self.game.initials_entry)
                current = chars[self.game.initials_index]
                chars[self.game.initials_index] = "Z" if current == "A" else chr(ord(current) - 1)
                self.game.initials_entry = "".join(chars)
            return

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == InputSettings.JOY_BUTTON_A:
                self.submit_initials_entry()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.game.initials_index = max(0, self.game.initials_index - 1)
                return
            if event.key == pygame.K_RIGHT:
                self.game.initials_index = min(2, self.game.initials_index + 1)
                return
            if event.key == pygame.K_UP:
                chars = list(self.game.initials_entry)
                current = chars[self.game.initials_index]
                chars[self.game.initials_index] = "A" if current == "Z" else chr(ord(current) + 1)
                self.game.initials_entry = "".join(chars)
                return
            if event.key == pygame.K_DOWN:
                chars = list(self.game.initials_entry)
                current = chars[self.game.initials_index]
                chars[self.game.initials_index] = "Z" if current == "A" else chr(ord(current) - 1)
                self.game.initials_entry = "".join(chars)



class IntermissionFlow:
    """Drive the between-level sequence: transition card, treasure exchange, then shop."""

    def __init__(self, game) -> None:
        """Store shared game reference.

        Args:
            game: Active game manager instance.
        """
        self.game = game

    def initialize_state(self) -> None:
        """Initialize between-level flow state fields on the game manager."""
        self.game.in_treasure_conversion = False
        self.game.treasure_conversion_data = {}
        self.game.conversion_display_start_time = 0
        self.game.conversion_display_delay_ms = GameSettings.TREASURE_CONVERSION_DISPLAY_DELAY_MS
        self.game.conversion_line_reveal_interval_ms = GameSettings.TREASURE_CONVERSION_LINE_REVEAL_INTERVAL_MS
        self.game.conversion_total_reveal_delay_ms = GameSettings.TREASURE_CONVERSION_TOTAL_REVEAL_DELAY_MS
        self.game.conversion_prompt_fade_ms = GameSettings.TREASURE_CONVERSION_PROMPT_FADE_MS

        self.game.pending_treasure_conversion = False
        self.game.treasure_conversion_pending_since = 0
        self.game.treasure_conversion_post_message_delay_ms = GameSettings.TREASURE_CONVERSION_POST_MESSAGE_DELAY_MS

        self.game.in_shop_phase = False
        self.game.shop_selected_index = 0
        self.game.shop_display_start_time = 0
        self.game.shop_display_delay_ms = GameSettings.SHOP_DISPLAY_DELAY_MS
        self.game.shop_stock = {}
        self.game.shop_limited_stock_template = dict(ItemSettings.SHOP_LIMITED_STOCK_TEMPLATE)

    # -------------------------
    # LEVEL TRANSITION
    # -------------------------

    def start_level_transition(self) -> None:
        """Pause on a title card before loading the next dungeon."""
        self.game.transition_label = f"LEVEL {self.game.current_level_number}"
        self.game.transition_end_time = pygame.time.get_ticks() + GameSettings.LEVEL_TRANSITION_MS
        self.game.pending_level_load = True
        self.game.audio.stop_music()

    def update_level_transition(self) -> None:
        """Load the pending level once transition timing has elapsed."""
        if not self.game.pending_level_load:
            return

        if pygame.time.get_ticks() < self.game.transition_end_time:
            return

        player_progress = self.game.level_loader.capture_player_progress()
        self.game.level_loader.load_level(player_progress)
        self.game.audio.play_random_bgm()
        self.game.pending_level_load = False
        self.game.transition_label = ""
        self.game.transition_end_time = 0

    def handle_door_unlock(self) -> None:
        """Advance to next level or finish run when final door unlocks."""
        self.game.message_success_border_until = (
            pygame.time.get_ticks() + UISettings.DOOR_UNLOCK_BORDER_FLASH_MS
        )

        if self.game.current_level_index >= len(self.game.level_order) - 1:
            self.game.log_message("CONGRATULATIONS! YOU CLEARED THE FINAL DUNGEON!")
            self.game.finish_game("win")
            return

        self.game.pending_level_index = self.game.current_level_index + 1
        self.game.audio.stop_music()
        self.game.log_message(
            "YOU UNLOCK THE DOOR AND ESCAPE THIS FLOOR",
            type_speed=GameSettings.DOOR_UNLOCK_MESSAGE_TYPE_SPEED,
        )
        self.game.pending_treasure_conversion = True
        self.game.treasure_conversion_pending_since = pygame.time.get_ticks()

    def update_door_unlock_sequence(self) -> None:
        """Delay treasure conversion until unlock message typing completes."""
        if not self.game.pending_treasure_conversion:
            return

        if self.game.message_log.is_typing:
            return

        elapsed = pygame.time.get_ticks() - self.game.treasure_conversion_pending_since
        if elapsed < self.game.treasure_conversion_post_message_delay_ms:
            return

        self.game.pending_treasure_conversion = False
        self.remove_between_level_items()
        self.start_treasure_conversion()

    def remove_between_level_items(self) -> None:
        """Remove inventory items that cannot persist across levels."""
        removed_any = False
        for item_name in ItemSettings.LEVEL_SCOPED_ITEMS:
            if self.game.player.inventory.get(item_name, 0) > 0:
                removed_any = True
            self.game.player.inventory.pop(item_name, None)
            self.game.player.discovered_items.discard(item_name)

        if removed_any:
            self.game.log_message("KEYS, MAPS, AND DETECTORS DON'T CARRY BETWEEN LEVELS.")

    # -------------------------
    # TREASURE CONVERSION
    # -------------------------

    def start_treasure_conversion(self) -> None:
        """Build treasure-conversion rows from current inventory."""
        treasure_items = {}
        for item, value in ItemSettings.TREASURE_SCORE_VALUES.items():
            if item == "GOLD COINS":
                continue
            if item in self.game.player.inventory and self.game.player.inventory[item] > 0:
                treasure_items[item] = {
                    "count": self.game.player.inventory[item],
                    "value_each": value,
                }

        self.game.treasure_conversion_data = treasure_items
        self.game.in_treasure_conversion = True
        self.game.conversion_display_start_time = pygame.time.get_ticks()
        self.game.log_message("YOUR TREASURE IS EXCHANGED FOR GOLD COINS.")

    def update_treasure_conversion(self) -> None:
        """Handle treasure conversion input and completion gate."""
        if not self.game.in_treasure_conversion:
            return

        elapsed = pygame.time.get_ticks() - self.game.conversion_display_start_time
        display_ready = elapsed >= self.game.conversion_display_delay_ms

        keys = pygame.key.get_pressed()
        button_pressed = keys[pygame.K_RETURN]

        for joystick in self.game.connected_joysticks:
            if joystick.get_button(InputSettings.JOY_BUTTON_START):
                button_pressed = True
                break

        if display_ready and button_pressed:
            self.complete_treasure_conversion()

    def complete_treasure_conversion(self) -> None:
        """Convert treasure values into gold and open the shop."""
        total_gold = 0
        for _, data in self.game.treasure_conversion_data.items():
            gold_value = data["value_each"] * data["count"]
            total_gold += gold_value

        if total_gold > 0:
            self.game.player.inventory["GOLD COINS"] = self.game.player.inventory.get("GOLD COINS", 0) + total_gold
            self.game.player.discovered_items.add("GOLD COINS")

        for item in self.game.treasure_conversion_data.keys():
            self.game.player.inventory.pop(item, None)

        self.game.in_treasure_conversion = False
        self.game.treasure_conversion_data = {}

        # Save *before* the shop opens. The player's run state at this
        # moment — gold included, level-scoped items already stripped — is
        # what they should resume into on the next load. The next dungeon
        # has not been picked yet, so a death-then-reload flow can re-roll
        # monster and loot placement.
        self.write_auto_save()

        self.start_shop_phase()

    def write_auto_save(self) -> None:
        """Persist the player's mid-run state to their bound save slot.

        Called from complete_treasure_conversion, the only auto-save point.
        No-op when no slot is bound (defensive — under normal play either
        NEW GAME or LOAD GAME assigns a slot before any auto-save can
        fire). The save records the next level the player is heading into
        (1-indexed), the post-conversion inventory (which already excludes
        level-scoped items), the player's discovered-items set, and the
        running score. On success a "GAME SAVED." message is logged so the
        player gets visible confirmation between conversion and shop.
        """
        if self.game.active_save_slot is None:
            return

        next_level = self.game.level_numbers[self.game.pending_level_index]
        wrote = self.game.save_manager.save_slot(
            slot_id=self.game.active_save_slot,
            player_name=self.game.player_name,
            next_level=next_level,
            inventory=self.game.player.inventory,
            discovered_items=self.game.player.discovered_items,
            score=self.game.score,
        )
        if wrote:
            self.game.log_message("GAME SAVED.")

    # -------------------------
    # SHOP
    # -------------------------

    def start_shop_phase(self) -> None:
        """Open shop phase and initialize stock data."""
        self.game.in_shop_phase = True
        self.game.shop_selected_index = 0
        self.game.shop_display_start_time = pygame.time.get_ticks()
        self.game.shop_stock = {}

        for item_name in ItemSettings.SHOP_PRICES:
            if item_name in self.game.shop_limited_stock_template:
                self.game.shop_stock[item_name] = self.game.shop_limited_stock_template[item_name]
            else:
                self.game.shop_stock[item_name] = None

        if self.game.player.inventory.get("INVISIBILITY CLOAK", 0) > 0:
            self.game.shop_stock["INVISIBILITY CLOAK"] = 0

        self.game.log_message('"KHAJIIT HAS WARES, IF YOU HAVE COIN."')

    def get_shop_menu_options(self) -> list[str]:
        """Return ordered shop menu rows.

        Returns:
            Purchasable item rows plus continue row.
        """
        return [*ItemSettings.SHOP_PRICES.keys(), "CONTINUE"]

    def move_shop_selection(self, delta: int) -> None:
        """Move currently highlighted shop row.

        Args:
            delta: Signed row step.
        """
        options = self.get_shop_menu_options()
        if not options:
            self.game.shop_selected_index = 0
            return

        self.game.shop_selected_index = (self.game.shop_selected_index + delta) % len(options)

    def format_purchase_message(self, item_name: str, quantity: int) -> str:
        """Create purchase message text with pluralization.

        Args:
            item_name: Purchased item name.
            quantity: Purchased quantity.

        Returns:
            UI-ready purchase message.
        """
        if quantity == 1:
            if item_name == "MONSTER REPELLENT":
                return "YOU BOUGHT A CAN OF MONSTER REPELLENT."
            article = "AN" if item_name[0] in "AEIOU" else "A"
            return f"YOU BOUGHT {article} {item_name}."

        if item_name == "MATCH":
            plural_name = "MATCHES"
        elif item_name == "TORCH":
            plural_name = "TORCHES"
        elif item_name.endswith("Y"):
            plural_name = item_name[:-1] + "IES"
        elif item_name.endswith("S"):
            plural_name = item_name
        else:
            plural_name = item_name + "S"

        return f"YOU BOUGHT {quantity} {plural_name}."

    def buy_shop_item(self, item_name: str, quantity: int = 1) -> None:
        """Attempt to purchase one shop item.

        Args:
            item_name: Item row selected.
            quantity: Desired quantity.
        """
        if item_name not in ItemSettings.SHOP_PRICES:
            return

        stock = self.game.shop_stock.get(item_name)
        if stock is not None and stock <= 0:
            self.game.log_message("THAT ITEM IS OUT OF STOCK.")
            self.game.audio.play('boundary')
            return

        purchase_quantity = quantity
        if stock is not None:
            purchase_quantity = min(purchase_quantity, stock)

        if purchase_quantity <= 0:
            return

        unit_price = ItemSettings.SHOP_PRICES[item_name]
        total_price = unit_price * purchase_quantity
        current_gold = self.game.player.inventory.get("GOLD COINS", 0)

        if current_gold < total_price:
            self.game.log_message("YOU CAN'T AFFORD THAT.")
            self.game.audio.play('boundary')
            return

        self.game.player.inventory["GOLD COINS"] = current_gold - total_price
        self.game.player.inventory[item_name] = self.game.player.inventory.get(item_name, 0) + purchase_quantity
        self.game.player.discovered_items.add(item_name)
        self.game.log_message(self.format_purchase_message(item_name, purchase_quantity))
        self.game.audio.play('coin')

        if item_name == "INVISIBILITY CLOAK":
            self.game.player.inventory.pop("INVISIBILITY SCROLL", None)

        if stock is not None:
            self.game.shop_stock[item_name] = max(0, stock - purchase_quantity)

        options = self.get_shop_menu_options()
        if options:
            self.game.shop_selected_index = min(self.game.shop_selected_index, len(options) - 1)
        else:
            self.game.shop_selected_index = 0

    def complete_shop_phase(self) -> None:
        """Close shop and begin transition to the next level."""
        self.game.in_shop_phase = False
        self.game.current_level_index = self.game.pending_level_index
        self.game.log_message(f"YOU LEAVE THE SHOP. DESCENDING TO LEVEL {self.game.current_level_number}...")
        self.start_level_transition()

    def handle_shop_event(self, event: pygame.event.Event) -> None:
        """Process keyboard and controller events for shop UI.

        Args:
            event: Input event to process.
        """
        if not self.game.in_shop_phase:
            return

        elapsed = pygame.time.get_ticks() - self.game.shop_display_start_time
        if elapsed < self.game.shop_display_delay_ms:
            return

        options = self.get_shop_menu_options()
        if not options:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.move_shop_selection(-1)
                return

            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.move_shop_selection(1)
                return

            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                selected_option = options[self.game.shop_selected_index]
                if selected_option == "CONTINUE":
                    self.complete_shop_phase()
                else:
                    self.buy_shop_item(selected_option)
                return

        if event.type == pygame.JOYHATMOTION:
            _, hat_y = event.value
            if hat_y == 1:
                self.move_shop_selection(-1)
            elif hat_y == -1:
                self.move_shop_selection(1)
            return

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == InputSettings.JOY_BUTTON_A:
                selected_option = options[self.game.shop_selected_index]
                if selected_option == "CONTINUE":
                    self.complete_shop_phase()
                else:
                    self.buy_shop_item(selected_option)
                return
