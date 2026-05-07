# Gameplay Systems

## Player

The player is represented by `Player` and `PlayerStats` in `models.py`.

Current stats come from `config.py` plus owned permanent upgrades:

- max HP
- movement speed
- damage
- fire rate
- arrow speed
- arrow range
- pierce count
- pickup radius
- shard gain multiplier
- invincibility seconds
- Echo Decay multiplier
- dash distance
- dash cooldown

The player is clamped inside the arena with `clamp_to_arena(position, arena_radius)`.

## Dash

Dash is available by default on `Space`.

Current dash rules:

- dashes in the current movement direction
- falls back to aim direction if the player is not moving
- stays inside the arena boundary
- uses `DASH_DISTANCE = 125.0`
- uses `DASH_COOLDOWN = 2.5`
- briefly flashes the player while dashing

Future dash upgrades can reduce cooldown, increase distance, or add a damage
trail.

## Shooting

`_shoot_if_ready()` creates an `Arrow` when the player is holding shoot and the
shot cooldown is ready.

Current arrow rules:

- travels in a straight line
- has finite range
- damages enemies on circle collision
- disappears on hit unless it has pierce remaining
- uses upgraded arrow speed, range, damage, and pierce values from `PlayerStats`

Projectile wrapping is not implemented yet. It is a good future upgrade hook.

## Enemies

Enemy kinds are represented by `EnemyKind`.

Current enemy types:

- `CHASER`: red triangle, medium speed, medium HP, contact damage.
- `FAST`: magenta diamond, low HP, higher speed, lower contact damage, better shard reward.

Current shared behavior:

- spawns around the arena edge
- moves toward the player
- damages on contact
- uses a separation force so enemies do not stack into one pile
- drops shard pickups on death

Enemy stats should be created through `create_enemy()` so kind-specific tuning
stays centralized. Rendering branches on `enemy.kind` in `main.py`.

## Waves

`_spawn_due_waves()` is timer-based. It increases wave size slowly and spawns
enemies around the arena edge. Fast enemies start mixing into waves after the
early chaser-only phase. Spawn tuning currently lives inside `systems.py` and can
later move into authored wave data.

## Echo Decay

Echo Decay drains HP over time after a grace period. It gives each run a natural
time limit even if enemies do not hit the player.

Current constants:

- `ECHO_DECAY_GRACE_SECONDS = 0.5`
- `BASE_ECHO_DECAY_PER_SECOND = 5`
- `ECHO_DECAY_RAMP_START_SECONDS = 30.0`
- `ECHO_DECAY_RAMP_PER_SECOND = 0.04`

If Echo Decay kills the player, the death reason is `Echo Faded`. If enemies kill
the player, the death reason is `Overwhelmed`.

## Currency

Shard flow:

1. Enemies die and create `Pickup` objects.
2. Pickups move toward the player inside pickup radius.
3. Collected pickups add to `run_shards`.
4. On death, `run_shards` plus survival bonus are added to `total_shards`.

Survival bonus is `int(run_timer // 10)`.

`Memory of Battle` multiplies collected pickup value before it enters
`run_shards`. Survival bonus is currently not multiplied.

## Upgrades

Upgrade definitions live in `upgrades.py`.

Current upgrades:

- `sharper_arrows_1`: `Sharper Arrows I`, costs 5 shards, multiplies damage by 1.2.
- `sharper_arrows_2`: `Sharper Arrows II`, costs 10 shards, requires `Sharper Arrows I`, multiplies damage by 1.2.
- `sharper_arrows_3`: `Sharper Arrows III`, costs 18 shards, requires `Sharper Arrows II`, multiplies damage by 1.2.
- `quick_draw_1`: `Quick Draw I`, costs 8 shards, increases fire rate by 20%.
- `quick_draw_2`: `Quick Draw II`, costs 12 shards, requires `Quick Draw I`, increases fire rate by 20%.
- `piercing_shot`: `Piercing Shot`, costs 18 shards, requires `Sharper Arrows I`, arrows can hit one extra enemy.
- `swift_arrows`: `Swift Arrows`, costs 8 shards, increases arrow speed by 20% and arrow range by 15%.
- `vital_echo`: `Vital Echo`, costs 8 shards, adds 25 max HP.
- `vital_echo_2`: `Vital Echo II`, costs 16 shards, requires `Vital Echo`, adds 25 max HP.
- `light_feet`: `Light Feet`, costs 10 shards, increases movement speed by 10%.
- `shorter_dash_cooldown`: `Shorter Dash`, costs 12 shards, reduces dash cooldown by 25%.
- `stable_echo`: `Stable Echo`, costs 8 shards, reduces Echo Decay by 20%.
- `stable_echo_2`: `Stable Echo II`, costs 16 shards, requires `Stable Echo`, reduces Echo Decay by 20%.
- `echo_magnet`: `Echo Magnet`, costs 10 shards, increases pickup radius by 50%.
- `memory_of_battle`: `Memory of Battle`, costs 14 shards, increases collected pickup shard value by 25%.

`build_player_stats()` reapplies owned upgrades from scratch. Keep this pattern
when adding new permanent stat upgrades.

## Persistence

`save_data.json` is ignored by git and stores:

- total shards
- owned upgrade ids
- best time
- current loop

Runtime-only entities such as enemies, arrows, pickups, current HP, and run timer
are not saved.
