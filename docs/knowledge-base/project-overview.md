# Project Overview

Echo Archer is a Python + pygame-ce top-down archery survivor prototype. The
core idea is a death-loop arena game: the player fights enemies, earns shards,
dies, buys permanent upgrades, and restarts stronger.

The project is inspired by the gamejam concept, but Echo Archer should remain
its own game. Do not copy the original name, assets, music, exact UI, or exact
presentation.

## Current Playable State

- The game starts fullscreen and can toggle fullscreen/windowed with `F11`.
- The player is a warm circle in the center of a circular arena.
- Enemy types currently include red triangle chasers and fast diamond chasers.
- The player moves with WASD or arrow keys, aims with the mouse, shoots with left mouse, and dashes with Space.
- HP drains over time through Echo Decay, so HP is also the run timer pressure.
- Enemies also damage the player on contact.
- Death opens a run summary, then a branch-column skill-tree screen.
- Permanent upgrades currently improve damage, fire rate, pierce, arrow speed/range, max HP, movement, dash cooldown, pickup radius, shard gain, and Echo Decay.
- Save data stores permanent shards, owned upgrades, best time, and loop count.

## Naming

Use `Echo Archer` as the game name in UI and docs.

The old folder/package names still use `loop_archer` because the MVP was created
before the name settled. Renaming package/module paths can happen later as its
own isolated refactor.

## Near-Term Direction

Good next feature candidates:

- Add projectile wrapping as an upgrade, not as a default rule.
- Add settings, including an optional numeric HP display.
- Add one more enemy type so the new upgrade power has more interesting targets.
