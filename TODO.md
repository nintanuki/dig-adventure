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
- [ ] Break up `GameManager` (too many responsibilities)
- [ ] Separate concerns:
  - Game state
  - Rendering
  - Input handling
  - Turn system
- [ ] Create clearer systems for:
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
- [ ] Monster can spawn on player
- [ ] Monster gets stuck between walls
- [ ] Monster-player collision delay (should trigger instant game over)
- [ ] Map drawing is incorrect / broken
- [ ] Entire map not revealed on win/loss

## Visual / UX Bugs
- [ ] Text is blurry (font/rendering issue)
- [ ] Grammar fix: “a emerald” → “an emerald”
- [ ] Monster visibility issue (color blends with environment)

---

# GAMEPLAY BALANCE

## Difficulty
- [ ] Game is too hard early on
- [ ] Some maps are overly punishing
- [ ] Reduce frustration from “useless” loot
- [ ] Make key detector more sensitive
- [ ] Provide clues when monsters are near?
- [ ] Randomize key, player, door and monster locations. The maps should just be based on walls.

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
- [ ] Show on minimap:
  - Door
  - Dug tiles
  - Last known monster position

---

# EXISTING SYSTEMS TO COMPLETE

## Turn System
- [ ] Ensure monster moves ONLY after player action completes (animation-aware)
- [ ] Press start to play again
- [ ] Score system and leaderboard

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
- [ ] 

---

# IDEAS (POST-CORE ONLY)

## Mechanics
- [ ] Monster attracted to light (stronger light = more danger)
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
- [ ] 

---

# NEXT ACTIONABLE TASKS

- [ ] Improve map system (visibility + minimap accuracy)
- [ ] Fix monster collision + spawning bugs
- [ ] Begin GameManager refactor

---

# NOTES

- Current foundation is solid (grid, movement, fog, digging all working)
- Biggest risk now is code complexity, not features
- Focus = stability → clarity → polish → expansion