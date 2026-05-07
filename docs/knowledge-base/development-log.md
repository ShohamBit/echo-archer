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

## feat: add core upgrade choices

Expanded permanent progression:

- added `Sharper Arrows II`, `Vital Echo`, `Stable Echo`, and `Quick Draw I`
- extended player stats for max HP, fire rate, and Echo Decay multiplier
- updated the upgrade screen from one card to multiple clickable cards
- added tests for upgrade effects, prerequisite locking, and Echo Decay scaling

## feat: add dash ability

Added a core movement verb:

- `Space` dashes in movement direction, or aim direction when standing still
- dash clamps to arena bounds
- dash has a 2.5 second cooldown
- HUD shows dash cooldown beside the health bar
- added tests for dash movement, cooldown, aim fallback, and arena clamping

## feat: add fast diamond enemy

Added the second enemy type:

- introduced `EnemyKind`
- added fast enemy stats through `create_enemy()`
- mixed fast enemies into later waves
- rendered fast enemies as magenta diamonds
- added tests for fast enemy stats and wave mixing
