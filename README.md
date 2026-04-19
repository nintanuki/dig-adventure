# dig-adventure

## Statement of Intent: Graphical Dungeon Crawler

### Vision
This project is an evolution of my original text-based adventure. The goal is to move from a command-line interface to a 2D graphical grid while preserving the "turn-based" tension of the original mechanics.

### Core Mechanics to Port
* **The 1:1 Action Economy:** Every player action (move, dig, use item) triggers a corresponding action from the Monster.
* **Reactive Monster AI:** The monster will continue to use Manhattan distance logic to decide between wandering, idling, or chasing the player.
* **Dynamic Visibility:** Replacing text descriptions with a visual "Circle of Light." The radius will be tied to the inventory items (Candle vs. Torch vs. Lantern).
* **Hidden Objectives:** The key and exit mechanics remain central. Players must physically "Dig" on grid tiles to reveal items, simulating the `find_random_item` logic from the text version.

### Visual Interface Goals
* **Central Grid:** A graphical viewport showing the player, discovered tiles, and the monster (if within light range).
* **Hybrid HUD:** A dedicated sidebar for the Map and Inventory, with a text-based event log at the bottom to maintain the "story" feel of the original game.