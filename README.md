# Dungeon Digger

Dungeon Digger is a turn-based dungeon crawler where each action you take advances the world.
You dig for treasure, survive monsters, unlock doors, and descend through every level.

## Objective

Clear all dungeon levels in order by finding a key and unlocking the door on each level.

To win a run:
1. Explore the level.
2. Find the key.
3. Reach the door.
4. Use Dig at the door while carrying a key.
5. Repeat until you clear the final dungeon.

## Core Rules

- The game is turn-based: most player actions advance the turn.
- Monsters move/respond after your turn actions.
- If a monster reaches your tile and you are not invisible, you lose (this can happen even in darkness).
- You cannot move through walls.
- Digging can reveal loot, tools, treasure, or nothing.
- Keys, maps, and key detectors are level-scoped and do not carry between levels.
- Treasure is exchanged for gold between levels.
- Gold is used in the shop between levels.

## How Turns Work

The following actions generally consume a turn:
- Moving
- Digging
- Lighting a source (Match, Torch, Lantern)
- Using Key Detector
- Using Monster Repellent
- Using Invisibility Cloak

Some invalid actions do not advance a turn (for example, trying to use an item you do not have).

## Controls (Keyboard)

### Global
- Enter: Start game / continue on end screens
- F11: Toggle fullscreen

### Movement
- W A S D
- Arrow keys

### Actions
- Space: Dig (or attempt to unlock door if standing on it with a key)
- E: Use Key Detector
- T: Use best available light source
- R: Use Monster Repellent
- C: Use Invisibility Cloak

### Shop
- Up/Down or W/S: Move selection
- Enter / Space / Z: Buy selected item (or Continue)
- X or 5: Buy 5 of selected item (where applicable)

### Initials Entry (Leaderboard)
- Type letters A-Z
- Backspace: Delete last letter
- Enter: Submit initials (once 3 letters are entered)

## Controls (Controller)

### Global
- Start (Button 7): Start / continue / confirm end-screen flow
- Back/Select (Button 6): Toggle fullscreen
- L2 trigger axis (platform dependent): Toggle audio mute

### Movement
- D-pad

### Actions
- A (Button 0): Dig
- B (Button 1): Light
- X (Button 2): Key Detector
- Y (Button 3): Monster Repellent
- LB (Button 4): Invisibility Cloak

### Shop
- D-pad Up/Down: Move selection
- A (Button 0): Buy selected item
- X (Button 2): Buy 5 selected item
- Start (Button 7): Continue to next level

## Items and Effects

### Utility and Progression
- Key: Required to unlock the level door.
- Map: Reveals terrain memory on minimap.
- Magic Map: Stronger map behavior, including enhanced minimap utility.
- Key Detector: Gives proximity hints to the key.

### Survival Tools
- Match, Torch, Lantern: Provide temporary light radius for visibility.
- Monster Repellent: Temporarily repels monsters.
- Invisibility Cloak: Temporarily prevents monsters from detecting you.

### Treasure and Currency
- Gold Coins, Ruby, Sapphire, Emerald, Diamond: Treasure used for score and/or conversion.
- Between levels, non-coin treasure is exchanged into gold for shopping.

## Score and Leaderboard

- Treasure increases score.
- High score is persisted.
- Runs that qualify for top leaderboard placement prompt initials entry.
- Leaderboard stores top entries and is shown at the end of a run.

## Game Flow

1. Title Screen
2. Level gameplay
3. Door unlock sequence
4. Treasure conversion
5. Shop
6. Next level transition
7. Final win screen or game-over flow

## Tips for New Players

- Light management is survival: save stronger lights for dangerous areas.
- Use the key detector when you feel lost.
- Repellent and cloak are clutch tools when cornered.
- Prioritize reaching the door safely over greed.
- Buy ahead in the shop when you can afford it.

## Running the Game

From the project directory:

```bash
python main.py
```

If your environment uses a different Python command, use that equivalent.
