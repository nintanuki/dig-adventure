# PROJECT TODO — DIG ADVENTURE

---

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
- [X] Break up `GameManager` (too many responsibilities)
- [X] Separate concerns:
  - Game state
  - Rendering
  - Input handling
  - Turn system
- [X] Create clearer systems for:
  - Turn resolution
  - Map memory / fog
  - UI updates

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
- [ ] Entire map not revealed on win/loss
- [ ] Play found gold/treasure sound AFTER dig sound (they currently overlap)

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

## Progression
- [ ] Add scoring system for treasure
- [ ] Make treasure meaningful (shop, upgrades, etc.)
- [ ] Consider:
  - Rest stop between levels
  - Multi-level progression loop

---

# CORE GAMEPLAY IMPROVEMENTS

## Player Experience
- [ ] Improve pacing (movement vs text timing)
- [ ] Sync:
  - Movement animation → THEN text → THEN next turn

## Monster Interaction
- [ ] Add stealth or avoidance mechanic
- [ ] Add temporary banish or defensive option

## Map / UI
- [X] Show on minimap:
  - Door
  - Dug tiles
  - Last known monster position

---

# EXISTING SYSTEMS TO COMPLETE

## Turn System
- [ ] Ensure monster moves ONLY after player action completes (animation-aware)
- [X] Press start to play again
- [X] Score system
- [ ] Leaderboard

## Feedback Systems
- [ ] Add visual/audio cues for nearby monster:
  - Howl text
  - Screen shake
  - Audio intensity

---

# CONTENT & STRUCTURE

## Maps
- [ ] Improve map variety (less repetitive starts)
- [ ] Adjust unfair layouts
- [ ] Add more handcrafted maps
- [ ] (Optional) Controlled randomization

## Rules
- [ ] Define win/loss reveal behavior and post-game summary rules

---

# IDEAS (POST-CORE ONLY)

## Mechanics
- [ ] Monster attracted to light (stronger light = more danger) instead of just manhattan distance
  This keeps the player safe in darkness unless very close / colliding.
  Increasing light radius should increase monster aggro distance.
- [ ] Dynamic monster variety (random sprites)
- [ ] Random obstacles

## Systems
- [ ] Dynamic music (Jaws-style proximity system)

## Visual / UX
- [ ] Text highlighting (e.g. colored item names)

---

# FEATURES TO ADD (AFTER STABILIZATION)

## Gameplay
- [ ] Add monster variety
- [ ] Add more obstacles (traps?)

## Player Tools
- [ ] Define utility tools that are not combat focused (e.g., scouting aid)

---

# NEXT ACTIONABLE TASKS

- [ ] Prevent player movement into occupied monster tiles
- [ ] Sequence dig -> treasure audio so sounds do not overlap
- [ ] Reveal full map memory on win/loss end state

---

# NOTES

- Current foundation is solid (grid, movement, fog, digging all working)
- Biggest risk now is code complexity, not features
- Focus = stability → clarity → polish → expansion
- Light source should not just be a radius; it should be blocked by walls (no seeing through walls)
- Marker lookup cleanup note resolved: duplicate marker lookup helpers are no longer present.

- Make metal detector more sensitive, add more levels + a real sound
- add shop or something you can do with gems + gold
- show gold at end of game
- Made spawns random again, but now must ensure entities do not spawn on top
  of each other or too close.
- Create a special area in the UI for unique key items (symbols?) instead of tracking quantity in inventory sidebar