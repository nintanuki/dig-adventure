import pygame
import sys
import os

from settings import *
from audio import AudioManager
from sprites import Player, Monster, Door
from windows import MessageLog, InventoryWindow, MapWindow
from dungeon import DungeonMaster
from mapmemory import MapMemory
from render import RenderManager
from crt import CRT
from tilemaps import DUNGEON_ORDER

class GameManager:
    def __init__(self, start_fullscreen: bool = False):
        # Initialize Pygame and set up the display
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Dungeon Digger')
        if start_fullscreen:
            pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()
        
        self.setup_controllers() # Controller Setup
        self.load_assets() # Pre-load dirt asset to avoid loading it 60 times per second
        self.dungeon = DungeonMaster(self.scaled_dirt_tiles) # Initialize the DungeonMaster with the pre-scaled dirt tiles from load_assets()
        self.all_sprites = pygame.sprite.Group() # Create a group to hold all sprites
        self.audio = AudioManager() # Initialize the audio manager
        self.game_active = False
        self.game_result = None
        self.score = 0
        self.high_score = self.load_high_score()
        self.leaderboard = self.load_leaderboard()
        self.level_order = list(DUNGEON_ORDER)
        self.current_level_index = 0
        self.pending_level_index = 0
        self.transition_label = ""
        self.transition_end_time = 0
        self.pending_level_load = False
        self.message_success_border_until = 0
        self.l2_trigger_is_pressed = False
        self.ui_state = 'title'

        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.pending_leaderboard_score = 0
        self.initials_entry = ""
        
        # Treasure Conversion Phase
        self.in_treasure_conversion = False
        self.treasure_conversion_data = {}  # Stores treasures found in current level for conversion
        self.conversion_display_start_time = 0
        self.conversion_display_delay_ms = 2000  # Delay before showing "PRESS START TO CONTINUE" after total appears
        self.conversion_line_reveal_interval_ms = 520
        self.conversion_total_reveal_delay_ms = 450
        self.conversion_prompt_fade_ms = 650

        # Door unlock sequence pacing
        self.pending_treasure_conversion = False
        self.treasure_conversion_pending_since = 0
        self.treasure_conversion_post_message_delay_ms = 450

        # Shop Phase
        self.in_shop_phase = False
        self.shop_selected_index = 0
        self.shop_display_start_time = 0
        self.shop_display_delay_ms = 200
        self.shop_stock: dict[str, int | None] = {}
        self.shop_limited_stock_template = {
            'LANTERN': 3,
            'INVISIBILITY CLOAK': 1,
            'MAP': 1,
            'KEY DETECTOR': 1,
        }
        
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # Initialize Windows
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)
        self.map_memory = None

        # CRT Effect
        self.crt = CRT(self.screen)

        # Render Manager
        self.render = None

        self.load_level()
        self.audio.stop_music()

    def reset_game(self):
        """
        Restart the game by replacing the current GameManager instance
        with a brand new one.

        This is safer than trying to manually reset every subsystem,
        because it reuses the same startup path the game already uses
        when it first launches.

        We will implement a more elegant reset in the future,
        but this is a good quick solution for now to speed up testing.
        """
        current_surface = pygame.display.get_surface()
        was_fullscreen = bool(current_surface and (current_surface.get_flags() & pygame.FULLSCREEN))

        new_game_manager = GameManager(start_fullscreen=was_fullscreen)
        new_game_manager.run()
        sys.exit()

        # note, it does not stay in fullscreen.

    @property
    def current_level_number(self) -> int:
        return self.current_level_index + 1

    @property
    def is_transitioning(self) -> bool:
        return pygame.time.get_ticks() < self.transition_end_time

    @property
    def is_in_treasure_conversion_phase(self) -> bool:
        return self.in_treasure_conversion

    @property
    def is_in_shop_phase(self) -> bool:
        return self.in_shop_phase

    def get_high_score_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), GameSettings.HIGH_SCORE_FILE)

    def get_leaderboard_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), GameSettings.LEADERBOARD_FILE)

    def load_high_score(self) -> int:
        """Load the saved high score from disk if it exists."""
        high_score_path = self.get_high_score_path()
        if not os.path.exists(high_score_path):
            return 0

        try:
            with open(high_score_path, 'r', encoding='utf-8') as score_file:
                return int(score_file.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def save_high_score(self) -> None:
        """Persist the best score reached so far to disk."""
        self.high_score = max(self.high_score, self.score)

        try:
            with open(self.get_high_score_path(), 'w', encoding='utf-8') as score_file:
                score_file.write(str(self.high_score))
        except OSError:
            pass

    def _sanitize_initials(self, initials: str) -> str:
        letters = ''.join(char for char in initials.upper() if char.isalpha())
        return (letters[:3]).ljust(3, 'A')

    def load_leaderboard(self) -> list[tuple[str, int]]:
        """Load top scores from disk in descending order."""
        leaderboard_path = self.get_leaderboard_path()
        if not os.path.exists(leaderboard_path):
            return []

        entries: list[tuple[str, int]] = []
        try:
            with open(leaderboard_path, 'r', encoding='utf-8') as board_file:
                for raw_line in board_file:
                    line = raw_line.strip()
                    if not line:
                        continue

                    if ',' not in line:
                        continue

                    initials, score_text = line.split(',', 1)
                    try:
                        score = int(score_text.strip())
                    except ValueError:
                        continue

                    if score < 0:
                        continue

                    entries.append((self._sanitize_initials(initials), score))
        except OSError:
            return []

        entries.sort(key=lambda entry: entry[1], reverse=True)
        return entries[:GameSettings.LEADERBOARD_LIMIT]

    def save_leaderboard(self) -> None:
        """Persist leaderboard entries to disk."""
        try:
            with open(self.get_leaderboard_path(), 'w', encoding='utf-8') as board_file:
                for initials, score in self.leaderboard:
                    board_file.write(f"{initials},{score}\n")
        except OSError:
            pass

    def is_top_ten_score(self, score: int) -> bool:
        """Return True when score qualifies for leaderboard entry."""
        if score <= 0:
            return False

        if len(self.leaderboard) < GameSettings.LEADERBOARD_LIMIT:
            return True

        return score >= self.leaderboard[-1][1]

    def add_leaderboard_entry(self, initials: str, score: int) -> None:
        """Insert and persist one top-score entry."""
        clean_initials = self._sanitize_initials(initials)
        existing_index = next(
            (i for i, (name, _) in enumerate(self.leaderboard) if name == clean_initials),
            None
        )
        if existing_index is not None:
            if score <= self.leaderboard[existing_index][1]:
                return
            self.leaderboard[existing_index] = (clean_initials, score)
        else:
            self.leaderboard.append((clean_initials, score))
        self.leaderboard.sort(key=lambda entry: entry[1], reverse=True)
        self.leaderboard = self.leaderboard[:GameSettings.LEADERBOARD_LIMIT]
        self.high_score = max(self.high_score, self.leaderboard[0][1] if self.leaderboard else 0)
        self.save_leaderboard()

    def start_gameplay_from_title(self) -> None:
        """Leave title screen and begin active gameplay."""
        self.ui_state = 'playing'
        self.game_active = True
        self.audio.play_random_bgm()

    def can_continue_from_game_over(self) -> bool:
        """Return True when the post-loss continue prompt is currently visible."""
        if self.ui_state != 'game_over':
            return False

        if self.game_result != 'loss':
            return True

        return self.game_over_prompt_start_time > 0 and pygame.time.get_ticks() >= self.game_over_prompt_start_time

    def update_game_over_flow(self) -> None:
        """Wait until death text is done, then reveal the continue prompt."""
        if self.ui_state != 'game_over' or self.game_result != 'loss':
            return

        if self.message_log.is_typing:
            return

        now = pygame.time.get_ticks()
        if self.game_over_message_complete_time == 0:
            self.game_over_message_complete_time = now
            self.game_over_prompt_start_time = now + GameSettings.GAME_OVER_CONTINUE_DELAY_MS

    def continue_from_game_over(self) -> None:
        """Advance to initials entry or directly to the leaderboard."""
        if self.is_top_ten_score(self.pending_leaderboard_score):
            self.ui_state = 'enter_initials'
            self.initials_entry = ""
            return

        self.ui_state = 'leaderboard'

    def submit_initials_entry(self) -> None:
        """Commit initials for this run, then show leaderboard."""
        self.add_leaderboard_entry(self.initials_entry, self.pending_leaderboard_score)
        self.ui_state = 'leaderboard'

    def handle_initials_event(self, event: pygame.event.Event) -> None:
        """Handle keyboard/controller input while entering leaderboard initials."""
        if self.ui_state != 'enter_initials':
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.initials_entry = self.initials_entry[:-1]
                return

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self.initials_entry) == 3:
                self.submit_initials_entry()
                return

            if event.unicode and event.unicode.isalpha() and len(self.initials_entry) < 3:
                self.initials_entry += event.unicode.upper()
                return

        if event.type == pygame.JOYBUTTONDOWN and event.button == 7 and len(self.initials_entry) == 3:
            self.submit_initials_entry()

    def handle_start_press(self) -> None:
        """Handle Start/Enter based on top-level UI state."""
        if self.ui_state == 'title':
            self.start_gameplay_from_title()
            return

        if self.ui_state == 'game_over' and self.can_continue_from_game_over():
            self.continue_from_game_over()
            return

        if self.ui_state == 'leaderboard':
            self.reset_game()

    def capture_player_progress(self) -> dict[str, object] | None:
        """Snapshot persistent player state before rebuilding the level."""
        if not hasattr(self, 'player'):
            return None

        return {
            'inventory': self.player.inventory.copy(),
            'discovered_items': set(self.player.discovered_items),
        }

    def restore_player_progress(self, progress: dict[str, object] | None) -> None:
        """Restore inventory and discovery state after spawning a fresh player."""
        if not progress:
            return

        self.player.inventory = progress['inventory'].copy()
        self.player.discovered_items = set(progress['discovered_items'])

    def load_level(self, player_progress: dict[str, object] | None = None) -> None:
        """Build the currently selected dungeon level and spawn fresh entities."""
        self.all_sprites.empty()

        dungeon_name = self.level_order[self.current_level_index]
        self.dungeon.load_dungeon(dungeon_name)
        self.dungeon.setup_tile_map()
        self.spawn_door()
        self.spawn_monster()
        self.spawn_player()
        self.restore_player_progress(player_progress)

        self.map_memory = MapMemory(self)
        self.render = RenderManager(self)

    def start_level_transition(self) -> None:
        """Pause on a title card before loading the next dungeon."""
        self.transition_label = f"LEVEL {self.current_level_number}"
        self.transition_end_time = pygame.time.get_ticks() + GameSettings.LEVEL_TRANSITION_MS
        self.pending_level_load = True
        self.audio.stop_music()

    def update_level_transition(self) -> None:
        """Load the pending dungeon once the transition card has finished."""
        if not self.pending_level_load:
            return

        if pygame.time.get_ticks() < self.transition_end_time:
            return

        player_progress = self.capture_player_progress()
        self.load_level(player_progress)
        self.audio.play_random_bgm()
        self.pending_level_load = False
        self.transition_label = ""
        self.transition_end_time = 0

    def finish_game(self, result: str) -> None:
        """End the current run and persist the high score."""
        self.game_active = False
        self.game_result = result
        self.ui_state = 'game_over'
        self.pending_leaderboard_score = self.score
        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.audio.stop_music()
        self.save_high_score()

    def handle_door_unlock(self) -> None:
        """Advance to the next dungeon, or finish the run on the last door."""
        self.message_success_border_until = pygame.time.get_ticks() + UISettings.DOOR_UNLOCK_BORDER_FLASH_MS

        if self.current_level_index >= len(self.level_order) - 1:
            self.log_message("CONGRATULATIONS! YOU CLEARED THE FINAL DUNGEON!")
            self.finish_game("win")
            return

        next_level_number = self.current_level_number + 1
        self.pending_level_index = self.current_level_index + 1
        self.audio.stop_music()
        self.log_message(
            f"YOU UNLOCK THE DOOR. DESCENDING TO LEVEL {next_level_number}...",
            type_speed=0.12,
        )
        self.pending_treasure_conversion = True
        self.treasure_conversion_pending_since = pygame.time.get_ticks()

    def update_door_unlock_sequence(self) -> None:
        """Delay treasure exchange until after unlock message has finished typing."""
        if not self.pending_treasure_conversion:
            return

        if self.message_log.is_typing:
            return

        elapsed = pygame.time.get_ticks() - self.treasure_conversion_pending_since
        if elapsed < self.treasure_conversion_post_message_delay_ms:
            return

        self.pending_treasure_conversion = False
        self.remove_between_level_items()
        self.start_treasure_conversion()

    def remove_between_level_items(self) -> None:
        """Remove inventory items that should never carry across dungeon boundaries."""
        removed_any = False
        for item_name in ItemSettings.LEVEL_SCOPED_ITEMS:
            if self.player.inventory.get(item_name, 0) > 0:
                removed_any = True
            self.player.inventory.pop(item_name, None)
            self.player.discovered_items.discard(item_name)

        if removed_any:
            self.log_message("KEYS, MAPS, AND DETECTORS DON'T CARRY BETWEEN LEVELS.")

    def start_treasure_conversion(self) -> None:
        """Collect treasures from inventory and prepare for conversion display."""
        # Collect treasure items from inventory (exclude gold coins which should not be converted)
        treasure_items = {}
        for item, value in ItemSettings.TREASURE_SCORE_VALUES.items():
            if item == 'GOLD COINS':  # Skip gold coins - they're the conversion target, not source
                continue
            if item in self.player.inventory and self.player.inventory[item] > 0:
                treasure_items[item] = {
                    'count': self.player.inventory[item],
                    'value_each': value
                }
        
        self.treasure_conversion_data = treasure_items
        self.in_treasure_conversion = True
        self.conversion_display_start_time = pygame.time.get_ticks()
        self.log_message("YOUR TREASURE IS EXCHANGED FOR GOLD COINS.")

    def update_treasure_conversion(self) -> None:
        """Handle input and state updates during treasure conversion phase."""
        if not self.in_treasure_conversion:
            return
        
        # Check if enough time has passed to show the "PRESS START" prompt
        elapsed = pygame.time.get_ticks() - self.conversion_display_start_time
        display_ready = elapsed >= self.conversion_display_delay_ms

        # Check for player input (Start button / Enter key)
        keys = pygame.key.get_pressed()
        button_pressed = keys[pygame.K_RETURN]
        
        # Also check gamepad
        for joystick in self.connected_joysticks:
            if joystick.get_button(7):  # Start button
                button_pressed = True
                break

        if display_ready and button_pressed:
            self.complete_treasure_conversion()

    def complete_treasure_conversion(self) -> None:
        """Convert collected treasures to gold coins and proceed to the shop."""
        # Convert treasures to gold coins
        total_gold = 0
        for item, data in self.treasure_conversion_data.items():
            gold_value = data['value_each'] * data['count']
            total_gold += gold_value
        
        # Add the gold coins to inventory
        if total_gold > 0:
            self.player.inventory['GOLD COINS'] = self.player.inventory.get('GOLD COINS', 0) + total_gold
            self.player.discovered_items.add('GOLD COINS')
        
        # Remove converted treasures from inventory
        for item in self.treasure_conversion_data.keys():
            self.player.inventory.pop(item, None)
        
        # Reset treasure conversion state
        self.in_treasure_conversion = False
        self.treasure_conversion_data = {}

        # Move to shop phase before the next level loads.
        self.start_shop_phase()

    def start_shop_phase(self) -> None:
        """Open the between-level shop with refreshed stock."""
        self.in_shop_phase = True
        self.shop_selected_index = 0
        self.shop_display_start_time = pygame.time.get_ticks()
        self.shop_stock = {}

        for item_name in ItemSettings.SHOP_PRICES:
            if item_name in self.shop_limited_stock_template:
                self.shop_stock[item_name] = self.shop_limited_stock_template[item_name]
            else:
                # None means infinite stock.
                self.shop_stock[item_name] = None

        self.log_message("KHAJIIT HAS WARES, IF YOU HAVE COIN.")

    def get_shop_menu_options(self) -> list[str]:
        """Return shop items plus a continue option."""
        options = []
        for item_name in ItemSettings.SHOP_PRICES:
            options.append(item_name)

        options.append('CONTINUE')
        return options

    def move_shop_selection(self, delta: int) -> None:
        """Move the highlighted shop row up or down."""
        options = self.get_shop_menu_options()
        if not options:
            self.shop_selected_index = 0
            return

        self.shop_selected_index = (self.shop_selected_index + delta) % len(options)

    def _format_purchase_message(self, item_name: str, quantity: int) -> str:
        """Build purchase confirmation text with simple plural rules."""
        if quantity == 1:
            if item_name == 'MONSTER REPELLENT':
                return 'YOU BOUGHT A CAN OF MONSTER REPELLENT.'
            article = 'AN' if item_name[0] in 'AEIOU' else 'A'
            return f'YOU BOUGHT {article} {item_name}.'

        if item_name == 'MATCH':
            plural_name = 'MATCHES'
        elif item_name == 'TORCH':
            plural_name = 'TORCHES'
        elif item_name.endswith('Y'):
            plural_name = item_name[:-1] + 'IES'
        elif item_name.endswith('S'):
            plural_name = item_name
        else:
            plural_name = item_name + 'S'

        return f'YOU BOUGHT {quantity} {plural_name}.'

    def buy_shop_item(self, item_name: str, quantity: int = 1) -> None:
        """Try to buy one shop item and immediately update inventory and gold."""
        if item_name not in ItemSettings.SHOP_PRICES:
            return

        stock = self.shop_stock.get(item_name)
        if stock is not None and stock <= 0:
            self.log_message("THAT ITEM IS OUT OF STOCK.")
            self.audio.play_boundary_sound()
            return

        purchase_quantity = quantity
        if stock is not None:
            purchase_quantity = min(purchase_quantity, stock)

        if purchase_quantity <= 0:
            return

        unit_price = ItemSettings.SHOP_PRICES[item_name]
        total_price = unit_price * purchase_quantity
        current_gold = self.player.inventory.get('GOLD COINS', 0)

        if current_gold < total_price:
            self.log_message("YOU CAN'T AFFORD THAT.")
            self.audio.play_boundary_sound()
            return

        self.player.inventory['GOLD COINS'] = current_gold - total_price
        self.player.inventory[item_name] = self.player.inventory.get(item_name, 0) + purchase_quantity
        self.player.discovered_items.add(item_name)
        self.log_message(self._format_purchase_message(item_name, purchase_quantity))
        self.audio.play_coin_sound()

        if stock is not None:
            self.shop_stock[item_name] = max(0, stock - purchase_quantity)

        # Clamp selection in case the purchased item just sold out and disappeared.
        options = self.get_shop_menu_options()
        if options:
            self.shop_selected_index = min(self.shop_selected_index, len(options) - 1)
        else:
            self.shop_selected_index = 0

    def complete_shop_phase(self) -> None:
        """Close the shop and begin loading the next level."""
        self.in_shop_phase = False
        self.current_level_index = self.pending_level_index
        self.log_message(f"YOU LEAVE THE SHOP. DESCENDING TO LEVEL {self.current_level_number}...")
        self.start_level_transition()

    def handle_shop_event(self, event: pygame.event.Event) -> None:
        """Process keyboard/controller input for the between-level shop."""
        if not self.in_shop_phase:
            return

        elapsed = pygame.time.get_ticks() - self.shop_display_start_time
        if elapsed < self.shop_display_delay_ms:
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

            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x, pygame.K_5):
                selected_option = options[self.shop_selected_index]
                if selected_option == 'CONTINUE':
                    self.complete_shop_phase()
                else:
                    quantity = 5 if event.key in (pygame.K_x, pygame.K_5) else 1
                    self.buy_shop_item(selected_option, quantity=quantity)
                return

        if event.type == pygame.JOYHATMOTION:
            _, hat_y = event.value
            if hat_y == 1:
                self.move_shop_selection(-1)
            elif hat_y == -1:
                self.move_shop_selection(1)
            return

        if event.type == pygame.JOYBUTTONDOWN:
            # Start button can always continue from the shop.
            if event.button == 7:
                self.complete_shop_phase()
                return

            if event.button == 0:  # A button confirms selection.
                selected_option = options[self.shop_selected_index]
                if selected_option == 'CONTINUE':
                    self.complete_shop_phase()
                else:
                    self.buy_shop_item(selected_option)
                return

            if event.button == 2:  # X button buys 5 at once.
                selected_option = options[self.shop_selected_index]
                if selected_option == 'CONTINUE':
                    self.complete_shop_phase()
                else:
                    self.buy_shop_item(selected_option, quantity=5)
                return

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self):
        """Initializes connected gamepads or joysticks."""
        pygame.joystick.init()
        # Create a list of all connected controllers
        self.connected_joysticks = [pygame.joystick.Joystick(index) for index in range(pygame.joystick.get_count())]

    def load_assets(self):
        """Handle all image loading and scaling in one place."""
        self.scaled_dirt_tiles = []

        for dirt_path in AssetPaths.DIRT_TILES:
            dirt_surf = pygame.image.load(dirt_path).convert_alpha()
            scaled_dirt = pygame.transform.scale(
                dirt_surf,
                (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
            )
            self.scaled_dirt_tiles.append(scaled_dirt)
        
        dug_surf = pygame.image.load(AssetPaths.DUG_TILE).convert_alpha()
        self.scaled_dug_tile = pygame.transform.scale(dug_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        wall_surf = pygame.image.load(AssetPaths.WALL_TILE).convert_alpha()
        self.scaled_wall_tile = pygame.transform.scale(wall_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

    # -------------------------
    # ENTITY SPAWNING --> SpawnManager Class? (probably not a priority)
    # -------------------------

    def spawn_player(self):
        col, row = self.dungeon.player_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.player = Player(self, (x, y), self.all_sprites)

    def spawn_monster(self):
        self.monsters = []
        for col, row in self.dungeon.monster_grid_positions:
            x, y = self.grid_to_screen(col, row)
            monster = Monster(self, (x, y), self.all_sprites)
            self.monsters.append(monster)

    def spawn_door(self):
        col, row = self.dungeon.door_grid_pos
        x, y = self.grid_to_screen(col, row)
        self.door = Door(self, (x, y), self.all_sprites)

    # -------------------------
    # COORDINATE + MAP HELPERS --> Future MapUtils Class?
    # -------------------------

    def grid_to_screen(self, col, row):
        return (
            UISettings.ACTION_WINDOW_X + col * GridSettings.TILE_SIZE,
            UISettings.ACTION_WINDOW_Y + row * GridSettings.TILE_SIZE,
        )

    def screen_to_grid(self, x, y):
        return (
            int((x - UISettings.ACTION_WINDOW_X) // GridSettings.TILE_SIZE),
            int((y - UISettings.ACTION_WINDOW_Y) // GridSettings.TILE_SIZE),
        )

    # -------------------------
    # TURN / GAME STATE --> TurnManager Class (maybe not is_busy())
    # -------------------------

    def advance_turn(self):
        """
        Resolve one world step after the player commits to an action.

        This is where time passes in the dungeon: temporary effects tick down,
        monsters respond, and loss conditions are checked. Keeping that logic
        together helps the game stay consistently turn-based.
        """

        if not self.game_active:
            return

        self.map_memory.remember_visible_map_info()

        # Handle Light Shrinking
        if self.player.light_turns_left > 0:
            self.player.light_turns_left -= 1
            
            if self.player.light_turns_left > 0:
                # Calculate how much radius we have per turn of life
                # We use the starting radius of the current light source
                unit_radius = self.player.active_light_max_radius / self.player.active_light_max_duration
                self.player.light_radius = unit_radius * self.player.light_turns_left
            else:
                # It hit zero
                self.player.light_radius = LightSettings.DEFAULT_RADIUS
                self.log_message("YOUR LIGHT FLICKERS OUT...")

        # Handle Repellent Duration
        if self.player.repellent_turns > 0:
            self.player.repellent_turns -= 1
            if self.player.repellent_turns == 0:
                self.log_message("THE SCENT OF THE REPELLENT FADES AWAY...")

        # Handle Invisibility Cloak Duration
        if self.player.invisibility_turns > 0:
            self.player.invisibility_turns -= 1
            if self.player.invisibility_turns == 0:
                self.log_message("THE INVISIBILITY CLOAK FADES.")

        for monster in self.monsters:
            monster.resolve_turn()

        self.check_player_caught_by_monster()

    def check_player_caught_by_monster(self) -> bool:
        """Return True and end the game if any monster occupies the player's tile."""
        if not self.game_active:
            return False

        if self.player.is_invisible():
            return False

        for monster in self.monsters:
            if self.player.position == monster.position:
                self.log_message("YOU WERE CAUGHT BY THE MONSTER!")
                self.audio.play_scream_sound()
                self.finish_game("loss")
                return True

        return False

    @property
    def is_busy(self):
        """Centralized check to see if the game is currently animating."""
        return (self.player.is_moving or 
                any(monster.is_moving for monster in self.monsters) or
                self.message_log.is_typing)

    # -------------------------
    # UI / GAME FEEDBACK --> Leave in GameManager for now
    # -------------------------
    
    def log_message(self, text, type_speed=None):
        """The central hub for all game objects to send text to the UI."""
        self.message_log.add_message(text, type_speed=type_speed)

    # -------------------------
    # Score
    # -------------------------

    def add_score(self, item_name: str, amount: int = 1) -> None:
        value = ItemSettings.TREASURE_SCORE_VALUES.get(item_name, 0)
        self.score += value * amount

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def run(self):
        """
        Run the game loop.
        """
        # Main game loop
        while True:
            if self.ui_state == 'playing':
                self.update_level_transition()
                self.update_door_unlock_sequence()
                self.update_treasure_conversion()

            self.update_game_over_flow()

            # Event Handling
            for event in pygame.event.get():
                # Handle quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Keyboard Inputs for fullscreen toggle and game restart
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()

                    if self.is_in_shop_phase:
                        self.handle_shop_event(event)

                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.handle_start_press()

                    self.handle_initials_event(event)

                # Gamepad button inputs for fullscreen toggle and game restart
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()

                    if self.is_in_shop_phase:
                        self.handle_shop_event(event)

                    if event.button == 7:
                        self.handle_start_press()

                    self.handle_initials_event(event)

                if event.type == pygame.JOYHATMOTION and self.is_in_shop_phase:
                    self.handle_shop_event(event)

                # Gamepad input for L2 trigger mute toggle (edge-triggered)
                if event.type == pygame.JOYAXISMOTION and event.axis in (2, 4):
                    trigger_pressed = event.value > 0.5
                    if trigger_pressed and not self.l2_trigger_is_pressed:
                        is_muted = self.audio.toggle_mute(
                            resume_music=self.game_active and not self.is_transitioning
                        )
                        self.log_message("AUDIO MUTED." if is_muted else "AUDIO UNMUTED.")
                    self.l2_trigger_is_pressed = trigger_pressed

            self.message_log.update() # Update message log to handle typing effect and message timing
            if self.ui_state == 'playing' and self.game_active:
                if not self.is_transitioning and not self.is_busy and not self.is_in_treasure_conversion_phase and not self.is_in_shop_phase: # Only allow player input if we're not in the middle of an animation or message
                    self.all_sprites.update()

                if not self.is_transitioning and not self.is_in_treasure_conversion_phase and not self.is_in_shop_phase:
                    # Always run the animation math (so sprites can finish their slide)
                    for sprite in self.all_sprites:
                        if hasattr(sprite, 'animate'):
                            sprite.animate()

                    # Catch collisions immediately when a monster finishes moving onto the player.
                    self.check_player_caught_by_monster()

            # Drawing
            self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

            if self.ui_state in {'playing', 'game_over'}:
                self.render.draw_grid_background() # Draw the grid background
                self.all_sprites.draw(self.screen) # Draw the sprites to the screen

                if not DebugSettings.NO_FOG: # Toggle Fog of War for testing
                    self.render.draw_fog_of_war()
                self.render.draw_ui_frames() # Draw the UI frames and outlines
                self.message_log.draw(self.screen)
                self.inventory_window.draw(self.screen)
                self.map_window.draw(self.screen)
                self.render.draw_level_transition()
                self.render.draw_treasure_conversion()
                self.render.draw_shop_menu()

            if self.ui_state == 'title':
                self.render.draw_title_screen()
            elif self.ui_state == 'game_over':
                self.render.draw_end_game_screens()
            elif self.ui_state == 'enter_initials':
                self.render.draw_initials_entry_screen()
            elif self.ui_state == 'leaderboard':
                self.render.draw_leaderboard_screen()

            self.crt.draw() # CRT Effect on top of everything else

            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)
 
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()