# Testing Checklist

Run this after major changes to ensure nothing broke:

* Start game successfully
* Move in all 4 directions
* Bump into wall
* Dig empty tile
* Dig item tile
* Use light
* Use detector
* Use repellent
* Let monster take a few turns
* Die to monster
* Win by opening door with key
* Confirm log, inventory, minimap still render

# Refactoring Rules
* Update CHANGELOG.md for every code change (timestamp, file, line numbers, before/after, why) including which AI model made the change. Read it first before making changes so you know the current state.
* All code must be PEP-8 compliant.
* All classes and functions must have a docstring.
* All docstrings must have a summary, Args (if applicable) and Returns (if applicable)
* Do not change function names (unless their role is now completely different)
* Keep functions organized and grouped by role. The update and run functions in classes should be the last function, and do as little as possible. Only call other functions if possible.
* Do not change variable names if not necessary.
* Function names and variable names must be descriptive.
* Do not remove comments unless they are no longer relevant.
* Comments must explain why, not just what.
* When making a change, do not leave a comment that a change was made, unless it was to fix a bug that wasn't obvious and to explain why something was done in an unconventional way.