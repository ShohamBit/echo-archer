# Campaign pacing and crowd spacing

The player enjoys the higher difficulty and finds Tempest harder than the Warden.
This slice keeps their attack timings, health and per-opening damage budgets,
and places Tempest at the campaign finale.

| Wave | Encounter | Purpose |
| --- | --- | --- |
| 1 | The Hunt | Hunters in pairs; practice lunge warnings and recall routes |
| 2 | Armored Flank | Introduce flanking guards and rush recovery |
| 3 | Crossfire | Introduce casters, then mix all three enemy roles |
| 4 | The Warden | Test committed attacks and rear-core positioning |
| 5 | Aftershock | A smaller, slower encounter after the midboss |
| 6 | Hunters' Gauntlet | Faster mixed packs and escape-lane decisions |
| 7 | Eye of the Storm | Denser mixed pressure before the finale |
| 8 | The Tempest | Spiral fire, marked blink and open-eye punishment |

Enemies arrive in small groups with gaps between them. Wave names, short tactical
objectives and queued reinforcements are visible. More Company adds one enemy per
equipped rank to ordinary waves; boss encounters stay solo. Existing nugget odds
are retained.

After the last enemy and pending reinforcement are cleared, a two-second regroup
period freezes the clock and passive income. Enemy bullets are cleared. Movement,
charge, recall and pickup remain available, and flying arrows cannot hurt the
player during regroup. The next wave is announced before it begins. Boss entrance
scenes still freeze the simulation separately. Survival retains continuous
spawning; Endless keeps its generated waves and gets regroup breaks.

Enemy spacing borrows the earlier Echo Archer prototype's separation idea. It uses
a local spatial grid and bounded soft pushes. Bosses never participate; enemies
in a windup or lunge retain their committed positions and direction. Spacing is
not an extra damage or health upgrade.

Boss Practice now ends after an actual kill of the selected boss and offers a
retry. It cannot continue into campaign waves or bank practice rewards. Campaign
victory requires killing Tempest at wave eight; the Warden alone cannot grant it.

A new full-size practice kill test also found that Tempest's outer blades could
deflect arrows before they reached the exposed eye. During exposure only, arrows
now pass through the outer ring until their swept path reaches the eye. A closed
eye still deflects shots; its eight-damage opening budget remains unchanged.

## Player acceptance

Play from both a reduced and a full loadout. Check whether:

- Each enemy role is introduced clearly before the mixed fights.
- Spawn gaps create decisions without feeling like unnecessary waiting.
- Regroup gives enough time to collect arrows and prepare.
- Crowds read better without weakening committed lunges.
- Wave five feels like a recovery beat and waves six/seven build pressure.
- Warden then Tempest feels like the right difficulty order.
- Both practice victories end cleanly, without changing saved points or records.

102 automated tests cover existing combat plus wave order, spawn gaps, rank effects,
regroup behavior, final-boss checks, full-size eye hits, spacing and both practice
kill/retry paths. Staged review frames are generated with
`analysis/capture_campaign.py` using temporary progress. The 180-frame dummy-SDL
boss/crowd benchmark measured 9.05ms mean render time, 13.70ms p95; simulation
averaged 0.38ms. Native display latency and game balance remain playtest checks.

## Entrance correction

Normal runs have a one-second player gate arrival; bosses have a 3.2-second reveal
at a safe landing position. Enter skips either entrance. The clock, simulation and
combat input stay frozen; Escape/focus loss pauses the animation as well.
Combat warnings and the aiming cursor appear after arrival rather than during it.

A regression reproduced death before the boss entrance: the simulation spawned
and collided with the boss before the app could pause it. App-controlled runs now
yield from simulation immediately on boss spawn, then start the reveal before any
boss AI, projectile or contact update. Landing selection avoids overlapping the
player. Other checks cover normal entry timing, skip/pause and stale menu clicks.
Review frames come from `analysis/capture_entrances.py` using temporary progress.
