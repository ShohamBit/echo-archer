# Development Log

This file summarizes the committed project history so far.

## `eebf08a` - added MVP for echo archer

Created the first Python + pygame-ce MVP:

- project package and virtualenv setup
- movement, aiming, shooting
- chaser enemies
- arrows and collision
- shard drops and pickup collection
- death summary
- one permanent upgrade: `Sharper Arrows I`
- JSON save/load
- automated tests for core systems

## `d43455d` - feat: add fullscreen echo decay loop pressure

Added the first major POC improvement:

- fullscreen startup
- `F11` fullscreen/windowed toggle
- dynamic layout instead of hardcoded `1280x720` positions
- Echo Decay passive HP drain
- death reasons: `Overwhelmed` and `Echo Faded`
- HUD Echo Decay status

## `eb3e72e` - feat: improve enemy readability and spacing

Improved enemy readability and arena use:

- chasers became larger
- chasers render as red triangle-bodied enemies
- added darker enemy core and forward mark
- added enemy separation so chasers do not stack into one pile
- arena radius scales on larger displays

## `cf3f98e` - feat: move health to bottom bar

Changed HUD layout:

- moved HP from top-left to a wide bottom-center bar
- removed numeric HP from the HUD
- kept metrics in the top-left
- added layout test for the health bar placement
