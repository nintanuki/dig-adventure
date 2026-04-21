# Dig Adventure

A turn-based dungeon crawler where every move matters.

You explore a dark, grid-based dungeon in search of a hidden key while avoiding a relentless monster. The environment is completely dark at the start — your only way to see is by using limited light sources. Every action you take advances the world, including the monster.

Survival depends on careful movement, resource management, and reading the situation before it’s too late.

---

# Core Gameplay

## Turn-Based Movement

* The game runs on a **1:1 action system**
* Every player action triggers a monster action:

  * Move
  * Dig
  * Use item

There is no idle time — every decision has consequences.

---

## Objective

* Find the **hidden key**
* Locate the **exit door**
* Escape the dungeon

Failing to avoid the monster results in immediate game over.

---

## Visibility & Light

* The game begins in **complete darkness**
* You must use light sources to see:

  * Match
  * Torch
  * Lantern

Each light source:

* Has a **limited duration**
* Provides a **different visibility radius**
* Gradually fades over time

When your light runs out, you are back in darkness.

---

## Digging System

* Most tiles must be **dug** to reveal what’s underneath
* Digging can uncover:

  * The key
  * Useful items
  * Treasure
  * Nothing at all

Each tile can only be dug once.

---

## Inventory & Items

### Utility Items

* **Match / Torch / Lantern** — provide temporary light
* **Monster Repellent** — keeps the monster away for a few turns
* **Key Detector** — gives proximity hints to the key
* **Map** — helps track explored areas

### Treasure

* Gold and gems can be found while digging
  (Currently limited use, intended for future systems)

---

## The Monster

* Moves **after every player action**
* Uses **distance-based logic** to track you
* Can wander, idle, or chase depending on proximity
* If it reaches your tile, you lose

The monster becomes more dangerous the closer it is — sometimes without you even seeing it.

---

## Map & Memory

* The minimap tracks:

  * Explored areas
  * Dug tiles
  * Previously seen locations
* Visibility is limited to your current light radius

Exploration is gradual and information is incomplete.

---

# Controls

## Keyboard

* Movement:

  * `W / A / S / D` or Arrow Keys

* Actions:

  * `Space` — Dig
  * `T` — Use light source
  * `E` — Use key detector
  * `R` — Use monster repellent

---

## Controller (if connected)

* D-Pad — Movement
* Buttons:

  * `A` — Dig
  * `B` — Use light
  * `X` — Key detector
  * `Y` — Repellent

---

# Strategy Tips

* Light is your most valuable resource — don’t waste it
* Digging blindly can be dangerous, but necessary
* Use the key detector to avoid wandering aimlessly
* Pay attention to movement patterns — the monster is predictable, until it isn’t
* Plan multiple moves ahead whenever possible

---

# Current State

The game is fully playable with:

* Turn-based movement
* Procedural dungeon selection
* Fog of war and light system
* Inventory and item usage
* Monster AI
* UI (log, inventory, minimap)

Ongoing work focuses on:

* Refactoring and code cleanup
* Bug fixes and balance
* Expanding gameplay systems

---

# Summary

Dig Adventure is about tension, uncertainty, and decision-making under pressure.

You are never safe.
You are never fully informed.
And every move could be your last.
