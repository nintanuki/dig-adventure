# PRIORITY ORDER (STRICT)
1. Refactor / Clean Code  
2. Documentation  
3. Bug Fixes  
4. Game Balance  
5. New Features  

Do NOT add new features until steps 1–4 are complete.

---

# CORE REFACTORING

## Architecture
- [ ] Break up `GameManager` (too many responsibilities)
- [ ] Separate concerns:
  - Game state
  - Turn system
  - Item Shop

## Code Quality
- [ ] Properly comment all systems
- [ ] Standardize naming conventions
- [ ] Remove dead / experimental code
- [ ] Centralize repeated logic (movement, messaging, etc.)

---

# BUGS / ISSUES

## Gameplay Bugs
- [ ] Player can pass through monster
- [X] Monster can spawn on player
- [ ] Monster gets stuck between walls
- [X] Monster-player collision delay (should trigger instant game over)
- [ ] Map drawing is incorrect / broken
- [X] Entire map not revealed on win/loss
- [ ] Play found gold/treasure sound AFTER dig sound (they currently overlap)
- [ ] Check that we don't need high_score.txt now that we have leaderboard.txt
- [ ] Enemy line of sight doesn't seem to work diagonally

## Visual / UX Bugs
- [ ] Text is blurry (font/rendering issue)
- [X] Grammar fix: “a emerald” → “an emerald”
- [ ] Monster visibility issue (color blends with environment)

---

# GAMEPLAY BALANCE

## Difficulty
- [ ] Game is too hard early on
- [ ] Some maps are overly punishing
- [ ] Reduce frustration from “useless” loot
- [ ] Make key detector more sensitive
- [ ] Provide clues when monsters are near?
- [X] Randomize key, player, door and monster locations. The maps should just be based on walls.
- [X] When the monster starts chasing the player, without repellent it is basically impossible to escape.
  Added monster idle chance during chase (currently controlled by `MonsterSettings.IDLE_CHANCE`).

---

# CORE GAMEPLAY IMPROVEMENTS

## Monster Interaction
- [ ] Add temporary banish or other defensive option

---

# EXISTING SYSTEMS TO COMPLETE

## Feedback Systems
- [ ] Create dedicated sound effect for lighting a lantern
- [ ] Add sound effects to actions that are missing them.

---

# CONTENT & STRUCTURE

## Maps
- [ ] Adjust unfair layouts
- [ ] Add more handcrafted maps

---

# IDEAS (POST-CORE ONLY)

## Mechanics
- [ ] Dynamic monster variety (random sprites)
- [ ] Random obstacles (traps)

## Systems
- [ ] Dynamic music? (Jaws-style proximity system)

# NEXT ACTIONABLE TASKS

- [ ] Prevent player movement into occupied monster tiles
- [ ] Sequence dig -> treasure audio so sounds do not overlap

---

# NOTES

- Current foundation is solid (grid, movement, fog, digging all working)
- Biggest risk now is code complexity, not features
- Focus = stability → clarity → polish → expansion
- Light source should not just be a radius; it should be blocked by walls (no seeing through walls)
- Made spawns random again, but now must ensure entities do not spawn on top of each other or too close.
- Create a special area in the UI for unique key items (symbols?) instead of tracking quantity in inventory sidebar

---

# PROGRESS NOTES (VERIFIED)

These notes capture confirmed progress without changing checkbox status unless a task is fully complete.

## Documentation and Clarity
- Added comprehensive class/function docstrings across gameplay modules.
- Added a player-facing game manual in README.
- Added TODO annotations for magic-number migration and settings organization.

## Architecture and Refactor Readiness
- `GameManager` responsibilities are now explicitly documented and segmented with TODOs for future extraction.
- Run-loop refactor targets are identified (event processing, state updates, frame rendering).
- Shop/input handling has documented extraction points for dedicated handlers.

## Known Completed Fixes (Already Checked)
- Monster-player collision delay fix remains validated as completed.
- Spawn overlap prevention remains validated as completed.
- Grammar fix for article usage remains validated as completed.

## Current Focus Guidance
- Continue reducing complexity in `GameManager` before adding new mechanics.
- Prioritize unresolved gameplay bugs before balance/features.

# Notes & Ideas
- Make shopkeeper and NPCs drop hints.
- Add save game feature. Player enters their name to create a new file, and it autosaves after every dungeon cleared ( decide if this is before or after the shop, probably after, before next nevel loads, so player keeps their purchases but might get a different dungeon on reload and have better luck)
- Allow player to toggle light source, so B doesn't always automatically light lantern > torch > match
- ^ Maybe have an indicator or highlight on the item in the inventory window with the toggle, and group light sources
- Figure out how the tutorial will work
- With the addition of the "tutorial" dungeon and easier levels loaded at start, more dirt tiles = more treasure meaning the player can buy the $10,000 invisibility cloak by level 2! Make it more expensive? The game is also more boring now that it starts with less "challenging" maps, just lots of digging in open space with low threat of monsters.
- remove allowing A to start the game, must press start
- replace pokemon and minecraft sounds

# Tutorial Plan
- since the message window gets busy easily and the player sometimes ignores or misses those messages, the tutorial text should pop up on the action window, in large text with a "press A to continue" prompt. Decide what the messages will be, in what order and what will prompt them.