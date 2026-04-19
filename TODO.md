# Development Roadmap: From Text to Graphics

## Issues to Fix:
- [ ] Player can "pass through" the monster
- [ ] Monster can spawn on top of player

## Ideas
- [ ] Animate movement (just move the image for now, no frames) and when the "animation" is complete, trigger a type writer effect for the message. THEN allow the player to take their next turn, not just using at timer?
- [ ] Randomly load in different monster sprites
- [ ] Add random obstacles
- [ ] Add text highlighting (e.g. Emerald is green)

## Phase 1: The Foundation (Baby Steps)
- [X] **Window Initialization:** Set up a basic window using a library like Pygame or Arcade.
- [X] **The Grid:** Render a static 8x8 grid of squares based on the `settings.py` dimensions.
- [X] **Player Sprite:** Place a simple sprite (or colored square) on the grid that moves with arrow keys.
- [/] **Controller Support:** Figure out controller early. D-Pad movement and a dig button at least to start.
- [X] **Boundary Checks:** Ensure the player cannot move outside the grid (porting logic from `main.py`).

## Phase 2: Visibility & "Fog of War"
- [ ] **Darkness Layer:** Cover the grid in black.
- [ ] **Light Radius:** Implement a basic "mask" around the player sprite.
- [ ] **Torch Logic:** Add a button to "Light Torch" that expands the mask radius for $X$ turns.

## Phase 3: The Monster & Turn Sync
- [ ] **Monster Sprite:** Add the monster to the grid (hidden by darkness).
- [ ] **Turn Trigger:** Create a function that signals the Monster to move only *after* the player's movement animation ends.
- [ ] **Visual Cues:** Display "Howl" text or screen shakes when the monster is within 2 steps.

## Phase 4: Digging & Items
- [ ] **Dig Interaction:** Add a keybind to dig. Change tile color/sprite once searched.
- [ ] **UI Sidebar:** Create a basic text overlay to show counts for Torches, Repellent, and Keys.
- [ ] **Victory/Loss Screens:** Replace the `typewriter` "Game Over" with a graphical splash screen.

## Phase 5: Effects?
- [ ] **Sprite Animation:** Find free placeholder assets for both the player and the monster that have at least 8 frames, 4 for each cardinal direction and 2 per direction for walking. Digging and other animations can be figured out later.