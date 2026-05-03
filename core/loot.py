"""One-stop pickup resolution shared by digging and NPC encounters.

Both Player.dig_current_tile and GameManager NPC interactions used to
duplicate ~30 lines of pluralization, scoring, inventory mutation, sound
effects, tutorial hooks, and map-reveal side effects. This module owns
that common path so both callers stay tiny.
"""

from settings import ItemSettings, LightSettings


def pluralize(name: str, amount: int) -> str:
    """Return a display-friendly label for a stack of one item.

    Args:
        name: Singular item name (e.g. "TORCH", "RUBY").
        amount: Stack size. Values <=1 return the singular form.

    Returns:
        Plural form for amount>1, singular otherwise.
    """
    if amount <= 1:
        return name
    if name == "TORCH":
        return "TORCHES"
    if name == "MATCH":
        return "MATCHES"
    if name.endswith("Y"):
        return name[:-1] + "IES"
    if name.endswith("S"):
        return name
    return name + "S"


def message_for_pickup(name: str, amount: int) -> str:
    """Return the 'YOU FOUND ...' line for one pickup."""
    if amount > 1:
        return f"YOU FOUND {amount} {pluralize(name, amount)}!"
    if name == "MONSTER REPELLENT":
        return "YOU FOUND A CAN OF MONSTER REPELLENT!"
    article = "AN" if name[0] in "AEIOU" else "A"
    return f"YOU FOUND {article} {name}!"


def resolve_pickup(game, name: str | None, amount: int) -> None:
    """Apply one item pickup end-to-end.

    Handles the score bump, the message-log line, the per-item sound
    effect, the magic-map-replaces-map quirk, the inventory increment
    + discovery set, the tutorial hook, the light-source auto-select,
    and the map full-reveal side effect. A no-op when name is falsy.

    Callers that need to suppress a pickup conditionally (e.g. digging
    an INVISIBILITY SCROLL while already holding the cloak) should null
    out name before calling.

    Args:
        game: Active GameManager — provides player, audio, log, score,
            and tutorial channels.
        name: Item name picked up, or None to skip.
        amount: Stack size.
    """
    if not name:
        return

    player = game.player

    if name in ItemSettings.TREASURE_SCORE_VALUES:
        game.score_manager.add_score(name, amount)

    game.log_message(message_for_pickup(name, amount))

    if name == "KEY":
        game.audio.play('key')
    elif name == "GOLD COINS" or name in ("RUBY", "SAPPHIRE", "EMERALD", "DIAMOND"):
        # All treasure types share the coin SFX.
        game.audio.play('coin')

    # Magic map subsumes any regular map already in the inventory.
    if name == "MAGIC MAP" and player.inventory.get("MAP", 0) > 0:
        player.inventory["MAP"] -= 1
        if player.inventory["MAP"] <= 0:
            player.inventory.pop("MAP", None)

    player.inventory[name] = player.inventory.get(name, 0) + amount
    player.discovered_items.add(name)
    game.notify_tutorial('item_picked_up', item=name)

    if name in LightSettings.SOURCE_PRIORITY:
        # Picking up a fresh light source auto-selects it if none was active.
        player.refresh_light_selection()
    if name in ("MAP", "MAGIC MAP"):
        game.map_memory.reveal_full_terrain_memory()
