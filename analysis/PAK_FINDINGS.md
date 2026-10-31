# Supplied LOOP ARCHER package: static gameplay evidence

**Superseded for behavior:** the follow-up [decoded Blueprint report](blueprints/RECOVERED_LOGIC.md)
now resolves charging, recall, damage, edge portals and spawning through actual
Kismet instructions. This first-pass document retains the earlier default-only
observations and their original limitations.

Source: `LOOP ARCHER/GMTK2025/Content/Paks/GMTK2025-WindowsNoEditor.pak`.
SHA-256: `6c12fa5dda779e148deac5c99048e90ff2053ae3d5c7b9c064700b4da4ef0441`.

These observations come from the custom read-only `inspect_pak.py` parser,
not a REA decompiler. REA's directory inspection separately identified the
Unreal package layout in parent Evidence
`ev_d9e9bdae701b4abadfe7cced7419f315a911e8b9783047fb253ed446716a8425`.

Run `python analysis/inspect_pak.py` from the workspace root to reproduce.
The script requires only Python's standard library and never changes the
supplied game. It verifies stored member SHA-1 hashes and decoded lengths.
It is specific to this observed unencrypted Unreal pak v11 layout, its zlib
compression and cooked tagged property encoding, rather than a general
Unreal decompiler.

## Observed package contents

The directory index contains 1342 file members. Relevant cooked assets include
Player, Arrow, WaveManager, four enemy classes, 19 upgrade node types,
SkillTreeMap, GameplayMap and EndGame. `pak_inventory.json` retains names and
compact-entry offsets. `gameplay_strings.json` retains strings and decoded
member SHA-256 identities for 396 project config/asset files.

`GMTK2025/Config/DefaultInput.ini` maps WASD to movement, left mouse to Shoot,
and both right mouse and Space to Recall. GameTutorial includes "to Recall"
and "SPACE". Blueprint names expose charging, recall, auto-fire and timer
systems, but names alone do not establish the execution path.

## Observed class defaults

`gameplay_defaults.json` retains property names, types, default values and
body offsets. These are cooked class defaults; Blueprint initialization can
overwrite them, so they are not automatically effective runtime values.

| Class | Observed defaults |
| --- | --- |
| Player | ShootingSpeed 1.25; MovementSpeed 500; AutoFIreTime 4; TimeLeft 30; DefaultTime 10; BowChargeLevel 1 |
| Arrow | Speed 1500; ArrowDamage 1; ArrowDamageRecall 1; CanDamage true |
| Enemy | Health 2; DefaultHealth 2; PointsAddition 1; TimeAddition 0.5; DefaultSpeed 190 |
| EnemyMoreHealth | Health/DefaultHealth 4; points 2; time addition 0.7; speed 150; scale 1.35 |
| EnemyNugget | Health/DefaultHealth 5; points 10; speed 70; scale 0.9 |
| EnemyShooter | Health 5 but DefaultHealth 6; points 5; time addition 0.6; speed 125; ShootingSpeed 2.25 |
| WaveManager | EnemySpawnTime 3.5; one initial EnemyToSpawn reference |
| NodeBase | Description "+1 damage"; MaxLevel 8 |

## Observed skill-tree configuration

`skill_tree_defaults.json` retains placed actor overrides from SkillTreeMap,
including exact prices, descriptions, ranks and outgoing discovery references.
Only Damage is explicitly enabled by default. Missing description/rank overrides
inherit NodeBase defaults; Movement therefore has eight ranks.

| Node | Description / effect label | Prices by rank |
| --- | --- | --- |
| Damage | +1 damage (inherited) | 2, 25, 40, 55, 60 |
| ChargeSpeed | +0.15 Charge Speed | 5, 10, 20, 40, 50 |
| ArrowSpeed | +250 Arrow Speed | 10, 15, 25, 40, 50 |
| FullCharge | +1 Damage when fully charged | 15, 25, 35 |
| MultiShot | +1 Arrow | 20, 50 |
| SelfDamage | Arrows can't damage you | 25 |
| MoreTimer | +3 Time | 5, 15, 20, 25, 40 |
| MoreTimeAddition | +0.3 Time Addition | 10, 15, 20, 25, 40 |
| MoreEnemies | +1 More Enemy | 10, 25, 35, 40, 55 |
| NuggetChance | +2.5 Nugget Chance | 15, 25, 40 |
| Sale | -5 All Upgrade Costs | 20, 35 |
| MovementSpeed | +25 Walk Speed | 5, 10, 20, 25, 40, 75, 90, 100 |
| Shield | +1 Shield | 15, 30 |
| SlowEnemies | +30 Slow To Enemy On Hit | 10, 15, 25 |
| MoreRecall | +1 Recall Damage | 5, 15, 25, 30, 50 |
| MorePoints | +1 Point From Kills | 10, 25 |
| PointsRecall | +1 Point for recall kills | 10, 15, 25 |
| PassivePoints | +1 Point Every 3 Seconds | 15, 25, 40 |
| BounceDamage | +1 Damage After Bounce | 15, 25, 50, 75 |

Outgoing `NodesToTriggerOnDiscover` references resolve to these placed actors:

- Damage -> ChargeSpeed, MoreTimer, MovementSpeed, MoreRecall
- ChargeSpeed -> ArrowSpeed
- ArrowSpeed -> MultiShot, FullCharge
- MultiShot -> SelfDamage
- MoreTimer -> MoreTimeAddition, MoreEnemies
- MoreEnemies -> NuggetChance
- NuggetChance -> Sale
- MovementSpeed -> Shield, SlowEnemies
- MoreRecall -> PointsRecall, MorePoints
- PointsRecall -> PassivePoints, BounceDamage

These are observed configuration links. Whether discovery requires one purchase,
full rank, hover, or another trigger requires control-flow/runtime evidence.

## Remaining unknowns

The work does not decompile Blueprint bytecode, recover the original Unreal
project or establish complete gameplay parity. Exact wave ramp, runtime timer
initialization (30 versus 10), charge scaling, recall collision and self-damage
rules require focused execution or Blueprint control-flow decoding. The immunity
upgrade's label supports the intended existence of arrow self-damage, but does
not prove precisely which arrow states hurt the player. Timings are engine units
until corroborated in execution. No original artwork, sounds or executable code
are exported for reuse in the Python reconstruction.
