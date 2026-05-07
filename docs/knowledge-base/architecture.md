# Architecture

The project uses a small data-driven architecture. Gameplay rules live outside
pygame rendering code so they can be tested without opening a window.

## Package Shape

- `src/loop_archer/models.py`: dataclasses and enums for saveable/runtime state.
- `src/loop_archer/systems.py`: gameplay rules and world update functions.
- `src/loop_archer/input.py`: input data passed into the simulation.
- `src/loop_archer/upgrades.py`: upgrade definitions and purchase logic.
- `src/loop_archer/persistence.py`: JSON save/load.
- `src/loop_archer/layout.py`: screen-size layout helpers.
- `src/loop_archer/main.py`: pygame app, input polling, rendering, screen-specific layouts, and buttons.
- `src/loop_archer/config.py`: tuning constants.

## Data Flow

1. `GameApp.run()` polls pygame input.
2. Pygame input is converted into `InputState`.
3. `update_world(state, input_state, dt)` advances gameplay only when `state.mode` is `PLAYING`.
4. Rendering reads the current `GameState` and draws it.
5. Death and upgrade screens mutate state through explicit helpers such as `begin_next_loop()` and `apply_upgrade()`.
6. `save_game()` persists permanent progress when the player dies or buys/restarts from the upgrade screen.

## State Ownership

`GameState` is the source of truth. Pygame surfaces, buttons, polygons, and draw
positions are view-only. Do not put gameplay rules directly into draw methods.

Reusable UI placement logic can live beside the screen that uses it when it is
specific to that screen. For example, `upgrade_screen_layout()` is in `main.py`
because it arranges upgrade cards and restart UI for that overlay, while generic
HUD geometry remains in `layout.py`.

## Coordinate System

World coordinates are centered at `(0, 0)`. The renderer converts world
coordinates to screen coordinates using the current screen center.

The arena radius is stored on `GameState.arena_radius`, which is synchronized
from the current screen size by `GameApp._sync_arena_radius()`.

## State Modes

- `PLAYING`: simulation advances.
- `DEAD_SUMMARY`: run has ended and summary UI is shown.
- `UPGRADE`: skill-tree UI is shown.
- `VICTORY_LATER`: reserved for future boss/final-wave work.
- `PAUSED`: reserved but not wired into gameplay yet.
