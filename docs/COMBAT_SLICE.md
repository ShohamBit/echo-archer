# First combat slice playtest

Historical first-slice checklist. The Warden is now harder and the expansion
adds a second boss, entrances, music, multi-kills, loadouts and new enemy roles.
Use `ENCOUNTER_EXPANSION.md` for the current playtest and validation results.

Launch `Play Loop Archer.cmd`. Normal Campaign includes the new finale; choose
**Boss Practice** to enter it immediately with your current upgrades. Practice
does not bank points or write the save. The current slice keeps movement, charge
timing and the one-volley recall cycle unchanged.

1. Shoot, wait for the arrow to stop, hold recall and collect it. Check that the
   nearby state badge and sounds explain when shooting and recalling are possible.
2. During the Warden's fan windup, move out of the marked rays. During its charge
   windup, leave the marked lane. Its attack direction locks before the attack.
3. After the charge, reach the glowing rear core. Try a direct rear shot, portal
   setup or returning arrow. Armor should block frontal hits; the exposed core
   should reward a deliberate setup. Even maxed damage requires several openings.
4. In normal combat, get portal, ricochet and recall kills. Check the point bonus,
   three-second chain and results counts. Decide whether bonuses are noticeable
   without making ordinary kills feel pointless.
5. Return to the menu and quit practice. Confirm the saved currency and records
   remain unchanged when reopening the game.

Acceptance is pending the player's feedback: are bow states clear, are both boss
attacks readable, is the rear core practical to hit, and is the encounter enjoyable
with a fully upgraded profile? Automated checks do not establish game feel.

Development validation: 69 tests pass, including maxed-volley damage limits and
practice save preservation. The dummy-SDL boss/crowd benchmark measured 8.14ms
mean render time, 10.36ms p95 over 180 frames; native frame pacing remains a manual
check. Review frames are in `artifacts/warden-dash_windup.png` and
`artifacts/warden-exposed.png`, generated with a temporary practice profile.
