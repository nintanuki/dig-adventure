"""Tutorial / hint overlay system.

This module owns every piece of the tutorial feature:
- The card catalog (every message id, its text, and which queue it goes into).
- The trigger map (game event -> list of card ids to push).
- The runtime queues (burst = immediate, flow = paced one-per-turn).
- The dismiss / anti-mash logic.
- The action-window overlay rendering.

Anything that needs to change about the tutorial — copy, ordering, when cards
fire, anti-mash delay, visuals — should live in this file. The rest of the
codebase only knows about the small public API on TutorialManager:
    is_blocking, update, on_turn_end, notify, try_dismiss, draw.

The manager is created at the title screen when the player chooses PLAY
(skip_tutorial=False). It then lives for the entire run regardless of which
level the player is on. If the player chose SKIP TUTORIAL, the manager is
never instantiated and notify_tutorial calls are no-ops.
"""

from collections import deque
from dataclasses import dataclass

import pygame

from settings import (
    AudioSettings,
    ColorSettings,
    FontSettings,
    LightSettings,
    MonsterSettings,
    UISettings,
    color_with_alpha,
    ItemSettings,
    GameSettings,
)


# Card lifecycle queues.
QUEUE_BURST = "burst"
QUEUE_FLOW = "flow"
FLOW_CARD_TURN_GAP = 2 # Number of turns between showing flow cards.


@dataclass(frozen=True)
class Card:
    """One tutorial card.

    Attributes:
        id: Unique identifier; tracked in shown_ids so each card fires once.
        text: Body text displayed in large type. Keep short.
        queue: QUEUE_BURST (drains immediately) or QUEUE_FLOW (one per turn).
    """

    id: str
    text: str
    queue: str = QUEUE_BURST


# -------------------------------------------------------------------------
# Card catalog.
#
# Every card the tutorial can ever show is defined here. Card ids are also
# what triggers reference. All copy lives in this dict.
# -------------------------------------------------------------------------
CARDS: dict[str, Card] = {
    # ---- Boot / main flow ----
    "welcome": Card("welcome", "WELCOME TO DUNGEON DIGGER!", QUEUE_BURST),
    "move": Card("move", "USE D-PAD OR ARROW KEYS TO MOVE.", QUEUE_BURST),
    "dig": Card("dig", "PRESS A OR SPACE TO DIG.", QUEUE_FLOW),
    "door": Card("door", "FIND A KEY TO OPEN THE DOOR.", QUEUE_FLOW),
    "key_hint": Card("key_hint", "DIG TO UNCOVER THE BURIED KEY.", QUEUE_FLOW),
    "treasure_hint": Card("treasure_hint", "TREASURE IS HIDDEN IN THE DIRT.", QUEUE_FLOW),
    "dark_warning": Card("dark_warning", "MONSTERS LURK IN THE DARK.", QUEUE_FLOW),
    "good_luck": Card("good_luck", "GOOD LUCK!", QUEUE_FLOW),

    # ---- Item pickups ----
    "pickup_match": Card("pickup_match", "PRESS B TO LIGHT THE MATCH.", QUEUE_BURST),
    "pickup_torch": Card("pickup_torch", "PRESS B TO LIGHT THE TORCH.", QUEUE_BURST),
    "pickup_torch_tip": Card("pickup_torch_tip", "TORCHES PROVIDE MORE LIGHT THAN MATCHES.", QUEUE_BURST),
    "pickup_lantern": Card("pickup_lantern", "PRESS B TO LIGHT THE LANTERN.", QUEUE_BURST),
    "pickup_lantern_tip": Card("pickup_lantern_tip", "LANTERNS PROVIDE MORE LIGHT THAN TORCHES.", QUEUE_BURST),
    "pickup_light_tip": Card("pickup_light_tip", "AND YOUR LIGHT WILL LAST LONGER.", QUEUE_BURST),
    "pickup_repellent": Card("pickup_repellent", "PRESS Y TO REPEL MONSTERS.", QUEUE_BURST),
    "pickup_detector": Card("pickup_detector", "PRESS X TO LOCATE THE KEY.", QUEUE_BURST),
    "pickup_cloak": Card("pickup_cloak", "PRESS L2 TO TURN INVISIBLE.", QUEUE_BURST),
    "pickup_scroll": Card("pickup_scroll", "PRESS L2 TO TURN INVISIBLE.", QUEUE_BURST),
    "pickup_key": Card("pickup_key", "YOU FOUND THE KEY! HEAD TO THE DOOR.", QUEUE_BURST),
    "pickup_map": Card("pickup_map", "MAPS REVEAL TERRAIN YOU'VE EXPLORED.", QUEUE_BURST),
    "pickup_magic_map": Card("pickup_magic_map", "THE MAGIC MAP REVEALS EVERYTHING.", QUEUE_BURST),
    "pickup_gold": Card("pickup_gold", "GOLD COINS BUY SHOP ITEMS.", QUEUE_BURST),
    "pickup_gold_tip": Card("pickup_gold_tip", "THEY ALSO ADD TO YOUR SCORE", QUEUE_BURST),
    "pickup_gem": Card("pickup_gem", "GEMS ARE EXCHANGED FOR GOLD.", QUEUE_BURST),
    "pickup_gem_tip": Card("pickup_gem_tip", "THEY ALSO ADD TO YOUR SCORE", QUEUE_BURST),

    # ---- Action effects (use cards). The {N} token is replaced at fire time. ----
    "use_light": Card("use_light", "YOUR LIGHT WILL FADE MORE EVERY TURN.", QUEUE_BURST),
    "use_light_tip2": Card("use_light_tip2", "MORE LIGHT WILL ATTRACT MORE MONSTERS.", QUEUE_BURST),
    "pickup_light_cycle": Card("pickup_light_cycle", "PRESS L1 OR R1 TO CYCLE LIGHT SOURCES.", QUEUE_BURST),
    "use_repellent": Card("use_repellent", "MONSTERS WILL FLEE FOR {N} TURNS.", QUEUE_BURST),
    "use_cloak": Card("use_cloak", "YOU ARE INVISIBLE FOR {N} TURNS.", QUEUE_BURST),
    "use_scroll": Card("use_scroll", "YOU ARE INVISIBLE FOR {N} TURNS.", QUEUE_BURST),
    "use_detector": Card("use_detector", "FOLLOW THE ALARM TO THE KEY.", QUEUE_BURST),

    # ---- Monster events ----
    "monster_spotted": Card(
        "monster_spotted",
        "A MONSTER IS CHASING YOU! YOUR LIGHT GIVES YOU AWAY.",
        QUEUE_BURST,
    ),
    "monster_lost_sight": Card(
        "monster_lost_sight",
        "THE MONSTER LOST YOUR TRAIL.",
        QUEUE_BURST,
    ),
}


# -------------------------------------------------------------------------
# Trigger maps.
#
# notify(event, **kwargs) looks up the event here to figure out which
# card(s) to push. Any kwarg the card text needs is supplied at push time.
# -------------------------------------------------------------------------

# Item name (as stored in the player's inventory) -> pickup card id.
PICKUP_CARDS: dict[str, tuple[str, ...]] = {
    "MATCH": ("pickup_match",),
    "TORCH": ("pickup_torch", "pickup_torch_tip", "pickup_light_tip"),
    "LANTERN": ("pickup_lantern", "pickup_lantern_tip", "pickup_light_tip"),
    "MONSTER REPELLENT": ("pickup_repellent",),
    "KEY DETECTOR": ("pickup_detector",),
    "INVISIBILITY CLOAK": ("pickup_cloak",),
    "INVISIBILITY SCROLL": ("pickup_scroll",),
    "KEY": ("pickup_key",),
    "MAP": ("pickup_map",),
    "MAGIC MAP": ("pickup_magic_map",),
    "GOLD COINS": ("pickup_gold", "pickup_gold_tip"),
    "RUBY": ("pickup_gem", "pickup_gem_tip"),
    "SAPPHIRE": ("pickup_gem", "pickup_gem_tip"),
    "EMERALD": ("pickup_gem", "pickup_gem_tip"),
    "DIAMOND": ("pickup_gem", "pickup_gem_tip"),
}

# Item-use kind (set by Player.process_turn_action) -> use card id.
USE_CARDS: dict[str, tuple[str, ...]] = {
    "light": ("use_light", "use_light_tip2"),
    "repellent": ("use_repellent",),
    "cloak": ("use_cloak",),
    "scroll": ("use_scroll",),
    "detector": ("use_detector",),
}


# -------------------------------------------------------------------------
# Tunables (move to settings.py later if you want them centralized).
# -------------------------------------------------------------------------
DISMISS_DELAY_MS = 500
WORLD_DARKEN_ALPHA = 170          # 0=invisible overlay, 255=fully opaque.
PANEL_ALPHA = 220
PANEL_BORDER_RADIUS = 8
PANEL_PADDING_X = 24
PANEL_PADDING_Y = 18
TEXT_LINE_GAP = 10
PROMPT_TEXT = "PRESS A OR SPACE TO CONTINUE"
PROMPT_GAP = 14                    # Vertical gap between body text and prompt.
BODY_FONT_SIZE = 14
PROMPT_FONT_SIZE = FontSettings.MESSAGE_SIZE


class TutorialManager:
    """Holds tutorial state and renders the action-window card overlay."""

    def __init__(self, game) -> None:
        """Initialize state and queue the boot sequence (welcome -> move).

        Args:
            game: The active GameManager (used for is_transitioning, screen
                rect, and surface access during draw).
        """
        self.game = game

        self.shown_ids: set[str] = set()
        self.burst_queue: deque[tuple[Card, dict]] = deque()
        self.flow_queue: deque[tuple[Card, dict]] = deque()

        self.current_card: Card | None = None
        self.current_text: str = ""
        self.message_shown_at_ms: int = 0

        # Pre-build the body and prompt fonts once.
        self._body_font = pygame.font.Font(FontSettings.FONT, BODY_FONT_SIZE)
        self._prompt_font = pygame.font.Font(FontSettings.FONT, PROMPT_FONT_SIZE)

        # Boot sequence: welcome, then move, then the rest of the main flow
        # paced one per turn.
        self._push_card_id("welcome")
        self._push_card_id("move")
        for card_id in ("dig", "door", "key_hint", "treasure_hint", "dark_warning", "good_luck"):
            self._push_card_id(card_id)

        self.flow_turns_until_next_card = FLOW_CARD_TURN_GAP

    # ---------------- Public API ---------------- #

    @property
    def is_blocking(self) -> bool:
        """True while a tutorial card is on screen.

        The game freezes (no input, no monster turns, no animations finishing)
        for as long as this is True.
        """
        return self.current_card is not None

    def update(self) -> None:
        """Per-frame work. Drain the burst queue when nothing is on screen."""
        if self.current_card is not None:
            return
        if self.game.is_transitioning:
            return
        # Burst queue drains immediately (used for boot sequence + interrupts +
        # back-to-back chains).
        if self.burst_queue:
            self._show_next_from(self.burst_queue)

    def on_turn_end(self) -> None:
        """Called from advance_turn after world state has settled.

        Drains an interrupt first if one was queued during the just-ended turn,
        otherwise drains one paced flow card.
        """
        # Interrupts (burst) always take precedence over the regular flow
        if self.current_card is not None:
            return
        # Context-sensitive cards interrupt immediately.
        if self.burst_queue:
            self._show_next_from(self.burst_queue)
            return
        # If no interrupts, show the next flow card if it's time.
        if not self.flow_queue:
            return
        # Check the turn gap timer; only show the next card if it's elapsed
        if self.flow_turns_until_next_card > 0:
            self.flow_turns_until_next_card -= 1
            return

        self._show_next_from(self.flow_queue)
        self.flow_turns_until_next_card = FLOW_CARD_TURN_GAP

    def try_dismiss(self) -> bool:
        """Attempt to dismiss the current card.

        Returns:
            True if the card was actually dismissed; False if there is no
            card up or the anti-mash window has not elapsed.
        """
        if self.current_card is None:
            return False
        elapsed = pygame.time.get_ticks() - self.message_shown_at_ms
        if elapsed < DISMISS_DELAY_MS:
            return False
        self.current_card = None
        self.current_text = ""
        return True

    def notify(self, event: str, **kwargs) -> None:
        """Hook for game-side events.

        Args:
            event: Event name. Currently used:
                'item_picked_up'    kwargs: item (str)
                'item_used'         kwargs: kind (str), name (str | None),
                                            duration (int | None)
                'monster_spotted'
                'monster_lost_sight'
                'moved' / 'dug' (currently unused; reserved for future hooks)
        """
        if event == "item_picked_up":
            item = kwargs.get("item")

            # Context-sensitive interrupts for picking up any
            light_sources = {"MATCH", "TORCH", "LANTERN"}
            # If the player picks up a light source and has already discovered another one
            # show the light cycle card.
            if item in light_sources:
                already_discovered_light_sources = (
                    self.game.player.discovered_items.intersection(light_sources) - {item}
                )
                if already_discovered_light_sources:
                    self._push_card_id("pickup_light_cycle")

            for card_id in PICKUP_CARDS.get(item, ()):
                self._push_card_id(card_id)
            return

        if event == "item_used":
            kind = kwargs.get("kind")
            duration = kwargs.get("duration")
            card_ids = USE_CARDS.get(kind, ())
            for card_id in card_ids:
                fmt = {"N": duration} if duration is not None else {}
                self._push_card_id(card_id, fmt=fmt)
            return

        if event == "monster_spotted":
            self._push_card_id("monster_spotted")
            return

        if event == "monster_lost_sight":
            self._push_card_id("monster_lost_sight")
            return

        # 'moved' / 'dug' are reserved hooks — no-op for now but preserved so
        # game-side call sites don't need to change later if we add behavior.

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the world-darken overlay and the card panel over the action window."""
        if self.current_card is None:
            return

        action_rect = pygame.Rect(
            UISettings.ACTION_WINDOW_X,
            UISettings.ACTION_WINDOW_Y,
            UISettings.ACTION_WINDOW_WIDTH,
            UISettings.ACTION_WINDOW_HEIGHT,
        )

        # Step 1: darken the world inside the action window.
        darken = pygame.Surface(action_rect.size, pygame.SRCALPHA)
        darken.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, WORLD_DARKEN_ALPHA))
        screen.blit(darken, action_rect.topleft)

        # Step 2: render the body text (wrap to fit the panel width).
        max_text_width = action_rect.width - (PANEL_PADDING_X * 2) - 16
        body_lines = self._wrap_text(self.current_text, self._body_font, max_text_width)
        body_surfs = [
            self._body_font.render(line, False, ColorSettings.TEXT_DEFAULT) for line in body_lines
        ]
        prompt_surf = self._prompt_font.render(PROMPT_TEXT, False, ColorSettings.TEXT_PROMPT)

        body_height = sum(s.get_height() for s in body_surfs) + TEXT_LINE_GAP * max(0, len(body_surfs) - 1)
        panel_inner_height = body_height + PROMPT_GAP + prompt_surf.get_height()
        panel_height = panel_inner_height + (PANEL_PADDING_Y * 2)
        panel_width = action_rect.width - 64

        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = action_rect.center

        # Step 3: draw the card panel (opaque-ish so text reads cleanly).
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill(color_with_alpha(ColorSettings.OVERLAY_BACKGROUND, PANEL_ALPHA))
        pygame.draw.rect(
            panel_surface,
            ColorSettings.BORDER_DEFAULT,
            panel_surface.get_rect(),
            2,
            PANEL_BORDER_RADIUS,
        )
        screen.blit(panel_surface, panel_rect.topleft)

        # Step 4: blit body text centered vertically inside the panel.
        cursor_y = panel_rect.top + PANEL_PADDING_Y
        for surf in body_surfs:
            line_rect = surf.get_rect(center=(panel_rect.centerx, cursor_y + surf.get_height() // 2))
            screen.blit(surf, line_rect)
            cursor_y += surf.get_height() + TEXT_LINE_GAP

        # Step 5: blit the prompt below the body.
        prompt_y = panel_rect.bottom - PANEL_PADDING_Y - prompt_surf.get_height()
        prompt_rect = prompt_surf.get_rect(center=(panel_rect.centerx, prompt_y + prompt_surf.get_height() // 2))
        screen.blit(prompt_surf, prompt_rect)

    # ---------------- Internal helpers ---------------- #

    def _push_card_id(self, card_id: str, *, fmt: dict | None = None) -> None:
        """Queue a card by id, skipping if already shown."""
        if card_id in self.shown_ids:
            return
        card = CARDS.get(card_id)
        if card is None:
            return
        # Avoid double-queuing the same id within a single session.
        for queued_card, _ in (*self.burst_queue, *self.flow_queue):
            if queued_card.id == card_id:
                return
        target = self.burst_queue if card.queue == QUEUE_BURST else self.flow_queue
        target.append((card, fmt or {}))

    def _show_next_from(self, queue: deque[tuple[Card, dict]]) -> None:
        """Pop one card from the given queue and start displaying it."""
        if not queue:
            return
        card, fmt = queue.popleft()
        # Skip if it became shown via another path (defensive).
        if card.id in self.shown_ids:
            self._show_next_from(queue)
            return
        text = card.text
        if fmt:
            try:
                text = text.format(**fmt)
            except (KeyError, IndexError):
                # Bad format args shouldn't crash the game; fall back to raw text.
                text = card.text
        self.current_card = card
        self.current_text = text
        self.shown_ids.add(card.id)
        self.message_shown_at_ms = pygame.time.get_ticks()

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """Greedy word-wrap so cards fit inside the panel width."""
        words = text.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines


# -------------------------------------------------------------------------
# Convenience: derive default durations for the use_* cards if the call site
# doesn't pass one explicitly. Importable so the action handlers can stay
# compact.
# -------------------------------------------------------------------------
def default_duration_for(kind: str, name: str | None = None) -> int | None:
    """Return the duration (in turns) the matching use_* card should show.

    Falls back to None when there is no obvious duration.
    """
    if kind == "light":
        if name == "MATCH":
            return int(LightSettings.MATCH_DURATION)
        if name == "TORCH":
            return int(LightSettings.TORCH_DURATION)
        if name == "LANTERN":
            return int(LightSettings.LANTERN_DURATION)
    if kind == "repellent":
        return MonsterSettings.REPELLENT_DURATION
    if kind == "cloak" or kind == "scroll":
        return ItemSettings.INVISIBILITY_CLOAK_DURATION
    return None
