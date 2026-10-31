# Encounter expansion

This responds to the player's request for harder bosses, fullscreen, boss music
and entrances, multi-kill rewards, a second boss, adjustable upgrades, and more
interesting ordinary enemies. Movement, bow timing and recall controls are retained.

## Playtest

1. Launch normally: fullscreen is the default. Toggle F11, resize the window and
   check that mouse aim stays aligned. `--windowed` is available at launch.
2. Open Upgrade Loadout. Check equipped / owned ranks, Disable All, individual
   plus/minus controls and Equip All Owned. Start an attempt and compare shields,
   shot count, damage and movement. Reopen the game to check the loadout persists.
   No purchase is removed. Disabling Better Deals also removes its shop discount.
3. Select Boss: Warden beside Boss Practice, then enter practice. Watch the
   3.2-second entrance, or press Enter to skip. The clock and combat stay frozen.
   Check the original drum/synth track; pause and resume, then toggle M mute.
4. Test the Warden with both full and reduced upgrades. It requires four openings
   at minimum; the rear-core opening lasts 1.65 seconds. At half health, the fan
   grows from five to nine shots and attacks accelerate. A radial burst ends each
   enraged exposure. Decide whether the threats remain readable and fair.
5. Switch the practice selector to Tempest. Weave between its three rotating
   streams. Leave the violet blink marker, dodge the outward burst, then hit the
   exposed eye. Blink destination locks before teleporting. The eye is vulnerable
   from any direction, with an eight-damage budget per opening and 32 total health.
6. Play Campaign: Tempest is wave four, Warden is wave eight. The midboss must not
   grant campaign victory. Both restore at least 30 seconds on entry. Practice
   never banks combat points or records.
7. In ordinary combat, compare lunging mantis hunters, flanking/rushing armored
   scarabs and strafing horned casters. Watch their windups and punish recovery.
   Gold scarabs flee. Check all three modes and crowded fights.
8. Line up multiple enemies with a piercing or returning volley. Kills within
   0.4 seconds earn +2 on the second, +3 third, +4 fourth and +5 thereafter, on top
   of normal and skillshot points. Confirm HUD feedback and results best burst.

## Validation and limits

83 automated tests cover previous mechanics plus loadout limits/roundtrips,
legacy saves, actual multi-kill scoring, boss scheduling and damage windows,
committed attack aiming, entrance/input freezes, practice save protection and
music pause/resume/stop. No new runtime dependencies were added. Soundtrack
`assets/boss_assault.wav` is original generated PCM; its reproducible composition
is in `analysis/compose_boss_music.py`, with no third-party samples.

The 180-frame dummy-SDL boss/crowd benchmark measured 9.16ms mean rendering,
11.27ms p95 and 0.25ms mean simulation before the final documentation pass.
This does not measure native fullscreen display latency or establish balance.
Native fullscreen/audio feel and boss difficulty still need player acceptance.
Staged review frames in `artifacts/expansion-*.png` use temporary profiles.
