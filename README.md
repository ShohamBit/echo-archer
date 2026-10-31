# Loop Archer / Python

A Pygame action game growing from the supplied **LOOP ARCHER** game by
[PolyCube and tEMMiE](https://polycube2.itch.io/looparcher). The current direction
is an independent game with smooth vector visuals, keeping the satisfying
single-volley/recall combat and permanent branching upgrades.
The supplied Unreal installation stays untouched in `LOOP ARCHER/`.
That installation is local only and is not included in this repository.

This is the current game on the `loop-archer-current` branch. The earlier
[Echo Archer MVP remains on main](https://github.com/ShohamBit/echo-archer/tree/main),
preserving its original code, tests and development knowledge base.

The combat foundation includes:
one deployed arrow/volley until pickup, left/right portal wrapping, top/bottom
ricochets, four charge levels, stepped arrow deceleration, and safe homing recall
while holding Space or right mouse. Combat now uses a centered square arena,
larger silhouettes and the original world-to-screen speed scale.

This is newly written Python, not recovered original source or a complete
behavior-identical port. The original executable and `.pak` are not required
to play the Python game. Art is drawn with Pygame and sound cues are synthesized.
The renderer now uses smooth regular fonts, antialiased geometry and a teal/slate
arena. Pixel fonts, pixelation, chromatic splitting and the expensive full-frame
glow pass are no longer used. Recovered fonts remain local historical analysis
assets and are excluded from this repository.

## Play

On this machine, double-click **Play Loop Archer.cmd**. A local `.venv` with
Pygame 2.6.1 has already been prepared.
The game now starts in fullscreen. F11 switches to a resizable window;
`main.py --windowed` starts windowed directly.

For the visual/shop review, use **Compare Presentation.cmd**. It uses temporary
progress and disables saving, preserving the normal maxed profile. Follow
[the short comparison checklist](docs/PRESENTATION_CHECKPOINT.md).

For another machine (Python 3.10 or later; verified on Python 3.13):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Pygame is the only third-party runtime dependency. It handles the window,
keyboard/mouse, drawing and audio with a conventional Python game loop.
The remainder uses the standard library. Tree coordinates and the generated boss
soundtrack live in `assets/`; the original game package and network access are
not needed at runtime. Windows uses Segoe UI when available; other systems use
Pygame's bundled default font.

The repository excludes local saves, the virtual environment, generated review
artifacts, the original installation, extracted binary/JSON dumps, recovered fonts
and third-party inspection tools. Analysis reports and our own scripts are retained
as development history. Scripts inspecting the original package require a separately
supplied local copy; ordinary play and tests do not.

| Input | Action |
| --- | --- |
| WASD or arrow keys | Move |
| Hold left mouse, then release | Draw and shoot one volley; all arrows pierce |
| Hold right mouse or Space | Recall stopped arrows safely toward your live position |
| Escape | Pause/resume; back to menu outside combat |
| Enter during an arrival | Skip the player or boss entrance |
| M | Toggle sound |
| F11 | Toggle fullscreen |
| F5 / F6 / F7 | Toggle shake / flashes / arrow trails |
| Space in menus | Start next run; results go to upgrades |

The shop is now a spatial tree, using the original node placements. Use WASD to
move through it, wheel to zoom, middle/right drag to pan and Home to recenter.
Hover for rank/effect/cost; hold left mouse for a half-second to buy one rank.
Branches appear after the first rank of their parent. The map uses smooth rounded
nodes with a stable details card beside it.

Kill enemies to earn points and restore a little time. Avoid enemies, projectiles,
and your flying arrows. Returning arrows are safe. Wait for a shot to slow down,
then hold recall to retrieve it; releasing recall stops retrieval. You can also
walk over a stopped arrow to collect it. Shoot again after pickup.
After death, spend banked points on permanent upgrades, then start again.
The first damage upgrade costs two points. Your first runs are intentionally short.

The menu defaults to **Campaign**: clear eight waves and defeat the final boss.
Victory requires a defeated boss and an empty final encounter. A count of spawned
enemies cannot trigger victory. **Endless** continues through escalating waves;
**Survival** uses continuous spawning and has no automatic victory condition.
Progress is shared across modes. Shields protect against hits, not the timer.

## New combat features

The archer now has a nearby bow-state badge, four charge dots and audio cues for
full charge, recall availability and pickup. Movement and shot timing are unchanged.

The wave-four boss, **the Warden**, alternates a telegraphed five-shot fan and a
marked charging lane. After charging, its rear core opens briefly. Hit that core
from behind, using positioning, portals or recall. Armor blocks other hits.
The core takes triple arrow damage, limited to 12 damage per opening against
48 total health, requiring at least four openings. Its faster charge and shorter
1.65-second opening demand deliberate positioning. At half health, it enrages:
a faster nine-shot fan, quicker transitions and a radial burst after recovery.
Boss entry restores at least 30 seconds; successful core hits restore 3 seconds.

**The Tempest** is the Campaign wave-eight finale. Its three rotating bullet streams
give way to a marked teleport, an outward burst and a brief vulnerable eye.
It has 32 health with an eight-damage cap per opening. At half health it fires
more frequently and its opening shortens. Defeating it clears the campaign.

Both bosses enter through an animated gate with a title sequence. Combat and the
clock freeze during the entrance; Enter skips it. An original 150 BPM synth/drum
track plays during the encounters, pauses with the game and follows M mute.
Normal runs also begin with a short, skippable player arrival. Entry animations
pause with the game, and shooting/recall controls resume after arrival. Bosses
land away from the player and cannot move, shoot or deal contact damage before
their entrance begins.

Regular enemies now have animated mantis, scarab and horned-caster silhouettes.
Hunters telegraph a committed lunge; plated guards flank and rush; casters strafe,
hold their aim visibly, then fire a three-shot fan. Gold scarabs flee. These
behaviors apply in all three modes.

Portal, ricochet and recall kills now earn small, flat skillshot bonuses. Each
route type adds one point; consecutive skillshot kills within three seconds add
another point every two chain steps, capped at two extra points. Ordinary kills
break the chain. Total bonus is at most five points per kill. Results show the
bonus and route counts.

Kills no more than 0.4 seconds apart also form a multi-kill burst. The second kill
adds two points, the third three, the fourth four, and subsequent kills five each.
This bonus stacks with skillshots. The HUD and results show bonuses and best burst.

Select the **Boss: Warden / Tempest** button beside **Boss Practice** to choose
an encounter, then enter practice with your equipped upgrades. Practice does not
bank points or write your save. CLI: `main.py --boss-practice --boss tempest`.
See [the expansion playtest checklist](docs/ENCOUNTER_EXPANSION.md).

The campaign now introduces hunters, guards and casters across three authored
encounters before the Warden, then rebuilds pressure toward Tempest. Packs arrive
with deliberate gaps. A two-second regroup freezes the clock after a wave clears,
allowing arrow retrieval and preparation. Soft crowd spacing keeps ordinary
enemies readable while preserving committed attacks. Boss Practice ends cleanly
on the selected boss's defeat. See [the campaign playtest](docs/CAMPAIGN_PLAYTEST.md).

## Upgrade loadouts

Select **Upgrade Loadout** on the main menu. Each row shows equipped / owned
ranks; use minus/plus to select any rank from zero to what you own. **Disable All**
and **Equip All Owned** offer quick resets. Purchased ranks, points and records
are retained. Combat changes apply to the next attempt. Better Deals uses its
equipped rank for shop discounts immediately; owned parent ranks still unlock
the tree. Loadouts save in the existing version-one profile using an optional
`active_levels` field; older profiles equip all owned upgrades by default.

## Saves

Currency, upgrades and records save to `saves/progress.json` after purchases and
run endings. Closing the game banks the active run once. Pause freezes the timer;
losing window focus pauses automatically. A malformed or unsupported save is
preserved and disables saving for that session, with a visible warning.
Choose another save path to start a separate profile:

```powershell
.\.venv\Scripts\python.exe main.py --save saves\another-profile.json
```

An abrupt process termination during combat does not preserve unbanked points.

## Extend it

| File | Responsibility |
| --- | --- |
| `loop_archer/model.py` | Combat, enemies, arrows, recall, timer, wave generation and boss |
| `loop_archer/boss.py` | Warden attack phases, locked telegraphs and rear-core vulnerability |
| `loop_archer/campaign.py` | Eight authored encounters, goals and pack rhythm |
| `loop_archer/enemy_ai.py` | Hunter lunges, guard flanking/rushes, caster strafing and gold fleeing |
| `loop_archer/creatures.py` | Animated vector enemy silhouettes and attack telegraphs |
| `analysis/compose_boss_music.py` | Reproducible original boss soundtrack composition; standard library only |
| `loop_archer/progression.py` | All 19 upgrades, exact recovered prices/rank caps/prerequisites, save format |
| `loop_archer/app.py` | Menu, combat, upgrade tree, pause/results, input and window scaling |
| `loop_archer/audio.py` | Original synthesized sound cues |
| `loop_archer/shop.py` | Original map layout, camera, discovery, hover and hold-to-buy |
| `loop_archer/presentation.py` | Lightweight shake, flash and local trail preferences |
| `analysis/benchmark_presentation.py` | Read-only rendering/simulation performance benchmark |
| `tests/` | Combat, progression, save integrity and application regression tests |
| `analysis/PAK_FINDINGS.md` | First-pass inventory and recovered defaults |
| `analysis/blueprints/RECOVERED_LOGIC.md` | Decoded original behavior, instruction references and remaining limits |
| `analysis/inspect_pak.py` | Reproducible standard-library inspector for the supplied pak |

To add an upgrade, add an `Upgrade` record in `progression.py`, assign a position
in `assets/tree_positions.json` and implement its effect through `Run.level(key)` in `model.py`.
Prices determine the maximum rank. A parent is unlocked after one purchased rank
in this recreation. To add enemies, extend `Run.spawn`, the enemy update behavior,
and the corresponding drawing in `App.draw_arena`. `Run.start_wave` owns the
campaign progression. The model can be run without opening a window.

## Evidence and reconstruction choices

Static inspection recovered all 1,342 pak member names and decoded strings/default
properties from 396 project files. Recovered facts include the original controls,
19 skill types, price arrays, rank caps, discovery links and enemy/arrow defaults.
The Python implementation uses those prices, caps and links, with fresh labels
and a compact tree layout. REA evidence IDs and source hashes are in the findings.

The original was briefly observed running: white diamond archer and bow,
checkerboard square arena, red diamond enemies, draining time bar, points,
skill screen and Space to enter a run. This was a bounded observation, not a
full playthrough or frame-by-frame comparison.

The follow-up pass decoded Player, Arrow, WaveManager, Portal and GameplayMap
with UAssetGUI/UAssetAPI, retaining readable Kismet projections and checked script
sizes. It corrected several inaccurate first-pass guesses. The base draw duration
is 1.25 seconds, charge rises every quarter-duration, and charge upgrades subtract
0.15 seconds per rank. Full charge adds damage, rather than enabling piercing.
Moving shots lose 250 speed every 0.1 seconds; only stopped arrows can be recalled.
Recall follows the live player and cannot hurt them. Flying arrows can.

The camera has a square aspect ratio, perspective FOV80 and arm length1000,
giving an approximately1680-unit playfield. Movement is500 world units/second,
slowing toward250 during charging and100 during recall. Horizontal portals shift
arrows by1400 units; vertical walls reflect them. Original spawning starts after
0.75 seconds, changes pools by spawn count and ends at15 normal spawns. That last
rule was deliberately removed from this game: it caused premature victory with
maxed spawn upgrades. See [the direction decision](docs/adr/0001-independent-game-direction.md).

Remaining approximations include native collision/perspective details, animation,
the recall curve's exact cubic tangents, and frame-dependent Unreal interpolation.
Python uses a frame-independent approximation of recall at60Hz. High upgrade
ranks clamp spawn intervals to0.15 seconds to avoid invalid native timer values.
Unlocking children after the first purchase and the one-point discount floor
remain recreation choices. The added campaign and endless modes use their own
wave schedule. Original music, sprites and postprocessing remain unreproduced.
Original game credits remain with its creators.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q loop_archer main.py tests analysis\inspect_pak.py
.\.venv\Scripts\python.exe main.py --headless --scene play --seed 9 --frames 100 --screenshot artifacts\play.png
```

Headless mode uses SDL dummy video/audio drivers and never writes progress. `--scene menu`, `--scene tree`,
`--frames`, `--seed` and `--screenshot` support repeatable rendering checks.
Manual feel/balance checks remain useful: shoot, recall while dodging, die, buy
damage, restart, pause, resize, and quit/reopen to confirm persistence.

## Rendering performance

The repeatable local 60-frame CPU benchmark dropped from 101.63ms mean render time
(113.87ms p95) to 11.44ms mean (13.8ms p95) after removing the full-frame pixel/glow
pipeline. Simulation was under 1ms per step in both runs. These measurements use
SDL dummy video, so they measure CPU work, not an assurance of identical display
latency or FPS on every machine. The game targets 60FPS.

```powershell
.\.venv\Scripts\python.exe analysis/benchmark_presentation.py --output artifacts\performance.json
```
