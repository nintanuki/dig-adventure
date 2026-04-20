# Development Roadmap: From Text to Graphics

## Issues to Fix:
- [ ] Player can "pass through" the monster
- [ ] Monster can spawn on top of player
- [ ] Figure out why text is so blurry
- [ ] Fix "you found a emerald -> an emerald"
- [ ] Entire map should be revealed upon escape or gameover
- [ ] Refactor code, game manager has way too many functions!
- [ ] Properly comment everything
- [ ] Monster is green and grass is green... hard to see?
- [ ] Monster appears to get stuck between two walls until it sees the player and then gives chase
- [ ] Map drawing feature is not working properly, fix that when you have time

Gameplay:
- [ ] Add premade maps will walls and obstacles using 2D lists like the Zelda Pygame tutorial (with a randomize option?)
- [ ] Add a second monster
- [ ] Pacing is slow, move player faster? But somehow it's waiting until the text is down which I like

## Ideas
- [ ] Animate movement (just move the image for now, no frames) and when the "animation" is complete, THEN trigger the type writer effect for the message. THEN allow the player to take their next turn, not just using at timer?
- [ ] Randomly load in different monster sprites
- [ ] Add random obstacles
- [ ] Add text highlighting (e.g. Emerald is green)
- [ ] Instead of the monster chasing you when it gets close, make the monster attracted to the light! Stronger light sources are more dangerous
- [ ] Dynamic "Jaws" like music indicating monster distance?

What to do next:
- [ ] add metal detector so player isn't wandering aimlessly
- [ ] no backtracking rule.............?

## Phase 1: The Foundation (Baby Steps)
- [X] **Window Initialization:** Set up a basic window using a library like Pygame or Arcade.
- [X] **The Grid:** Render a static 8x8 grid of squares based on the `settings.py` dimensions.
- [X] **Player Sprite:** Place a simple sprite (or colored square) on the grid that moves with arrow keys.
- [X] **Controller Support:** Figure out controller early. D-Pad movement and a dig button at least to start.
- [X] **Boundary Checks:** Ensure the player cannot move outside the grid (porting logic from `main.py`).

## Phase 2: Visibility & "Fog of War"
- [X] **Darkness Layer:** Cover the grid in black.
- [X] **Light Radius:** Implement a basic "mask" around the player sprite.
- [X] **Torch Logic:** Add a button to "Light Torch" that expands the mask radius for $X$ turns.

## Phase 3: The Monster & Turn Sync
- [X] **Monster Sprite:** Add the monster to the grid (hidden by darkness).
- [?] **Turn Trigger:** Create a function that signals the Monster to move only *after* the player's movement animation ends.
- [ ] **Visual Cues:** Display "Howl" text or screen shakes when the monster is within 2 steps.

## Phase 4: Digging & Items
- [X] **Dig Interaction:** Add a keybind to dig. Change tile color/sprite once searched.
- [X] **UI Sidebar:** Create a basic text overlay to show counts for Torches, Repellent, and Keys.
- [X] **Victory/Loss Screens:** Replace the `typewriter` "Game Over" with a graphical splash screen.

## Phase 5: Effects?
- [ ] **Sprite Animation:** Find free placeholder assets for both the player and the monster that have at least 8 frames, 4 for each cardinal direction and 2 per direction for walking. Digging and other animations can be figured out later.