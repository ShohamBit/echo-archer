# Game improvement backlog

Status: prioritized proposals; the first combat slice is implemented for playtesting.
Based on the current build, the player's feedback and the earlier primary-source
research in `docs/research/game-design-direction.md`.

The design pillars are readable single-volley combat, clever use of portals and
recall, an enjoyable permanent skill tree, smooth presentation and an endgame
worth playing after every upgrade is bought. Preserve existing profiles.

## P0 — Make the current experience dependable

- [ ] **B01 — Measure real gameplay frame pacing.** Add an optional FPS/frame-time
  overlay and benchmark combat and the full skill tree, including heavy waves.
  Target a16.7ms frame budget at the default resolution; measure update, render
  and display separately. The current CPU-only benchmark does not prove native
  display responsiveness. Done when hitching can be reproduced and attributed.
- [ ] **B02 — Make bow state unmistakable.** Show Ready, Flying, Recallable and
  Returning with a compact indicator near the archer and distinct audio cues.
  Display charge tiers clearly. Done when a new player understands why another
  shot or recall is unavailable without reading a paragraph.
- [ ] **B03 — Explain each attempt's outcome.** Show the exact death cause, wave,
  kills, points and best comparison; distinguish time expiry, enemy hit and own
  flying-arrow hit. Keep results fast to dismiss. Done when losses feel explainable
  and victory only follows the actual cleared finale.
- [ ] **B04 — Audit every upgrade's description against every mode.** The current
  More Company description still refers to Original Loop despite the new modes;
  nugget chances also differ between mode implementations. Fix mismatches before
  adding nodes. Done when displayed effects accurately predict gameplay.

## P1 — Give the combat a distinctive reason to replay

- [ ] **B05 — Replace the basic boss with a designed encounter.** Start with two
  clearly telegraphed attacks and one vulnerability window. Prototype a weak point
  reached through a portal or return-arrow setup; avoid relying on more health.
  Test with both modest and maxed upgrades. Done when the player can explain the
  boss's pattern and choose a deliberate response.
- [ ] **B06 — Reward skillful shot routes.** Track portal, ricochet and recall kills
  and introduce a small skillshot/combo reward with readable feedback. Prototype
  rewards before committing to an economy multiplier. Done when a planned route
  feels better than repeatedly firing at the nearest enemy.
- [ ] **B07 — Add enemies with different decisions, not just different health.**
  Prototype a frontal guard that encourages flank/recall hits, and a charger that
  commits to a marked lane. Introduce them separately before mixing them. Done
  when each role changes positioning while remaining readable in a crowd.
- [ ] **B08 — Handcraft the eight-wave pacing.** Alternate introduction, practice,
  mixed pressure and recovery beats; show enemies remaining and the final-wave
  objective. Done when difficulty has a clear shape rather than simply adding
  more bodies, and a late loss can be traced to a learnable mistake.
- [ ] **B09 — Test whether the shot cycle has unnecessary downtime.** Compare the
  existing wait/hold recall with a buffered recall request or modest early-recall
  option in the sandbox. Preserve the meaningful risk of deploying one volley.
  Done when the preferred version feels responsive without becoming unlimited fire.

## P2 — Make progression and the tree rewarding

- [ ] **B10 — Add milestone upgrades that visibly change play.** Candidate unlocks:
  portal-linked shots, a wider return path or a clearly visible ricochet bonus.
  Keep all upgrades eventually obtainable. Prototype one effect at a time and
  ensure each has a clear explanation and testable benefit.
- [ ] **B11 — Finish tree usability.** Add fit-to-tree, focus-on-affordable nodes,
  readable completion markers, purchase feedback and before/after effect values.
  Keep the spatial branches rather than reverting to a grid. Test at small window
  sizes and high zoom. Done when the next useful purchase is easy to find.
- [ ] **B12 — Balance from playtest evidence.** Record attempt duration, death cause,
  wave reached and purchase order locally in an opt-in test profile. Compare fresh,
  mid-tree and fully upgraded starts before changing prices or extending ranks.
  Do not assume that maxing the tree after26 attempts was too fast: playtime and
  the player's judgement of that pace are still unknown.
- [ ] **B13 — Provide an endgame after the tree is complete.** Add a small set of
  mastery goals: portal-only boss finish, recall-kill chain, limited-shield clear,
  or a timed challenge. Reward records, medals or cosmetics instead of mandatory
  endless stat inflation. Existing maxed profiles must be able to participate.

## P3 — Polish and expand only after the core works

- [ ] **B14 — Give archery a coherent sound identity.** Replace generic synthesized
  tones with a matching draw, release, impact, portal, recall and pickup set.
  Separate music/effects volume. Keep sound useful even with visual effects reduced.
- [ ] **B15 — Improve arena identity without obscuring threats.** Add a restrained
  environment, recognizable portal mouths and distinct enemy silhouettes; consider
  a second arena with a mechanical difference after the first is balanced.
  Avoid reintroducing expensive full-frame filters.
- [ ] **B16 — Make settings and profiles approachable.** Visible pause-menu controls
  for volume, shake, flashes and trails; optional recall hold/toggle binding; separate
  test profiles and clear sandbox labels. Never reset progression without a direct
  user request.

## Recommended first development slice

1. B02: bow/recall state clarity.
2. B05: a boss with one genuinely interesting vulnerability.
3. B06: a small skillshot reward that connects portals, bounces and recall.

Keep B01 and B04 as checks throughout. This slice addresses responsiveness and
identity while creating something a fully upgraded player can meaningfully test.
Do not implement all proposals at once; compare each change against the current
build and retain it only if the player finds it better.

## Lightweight playtest checklist

- Can the player tell when a shot, recall and pickup are available?
- Is a death understandable, and can the player name a better next action?
- Does a portal or recall setup offer a useful choice beyond direct firing?
- Are enemy attacks readable at the busiest point of the attempt?
- Is a purchase visibly useful, and is the next branch easy to find?
- Does the boss remain interesting with a fully upgraded profile?
- Does frame pacing remain steady through combat, the tree and transitions?

## First slice implementation status

B02, B05 and B06 are implemented; their player acceptance checks remain open.
Bow states and charge cues, the Warden's fan/charge/rear-core cycle, and flat
skillshot rewards are available. Boss Practice uses current upgrades without
banking rewards or writing the profile. Movement and shot timing are unchanged.

B04 is partially addressed: More Company and Nugget descriptions now explain
mode differences. The remaining description audit is still open. B08 now shows
enemies remaining and a finale objective; wave pacing remains open.

Validation: 69 automated tests pass. A 180-frame boss/crowd CPU benchmark measured
8.14ms mean rendering and 10.36ms p95. Native display/frame-pacing acceptance
under B01 remains open. No dependencies or save-format changes were introduced.
Use `docs/COMBAT_SLICE.md` for the next playtest.

## Encounter expansion status

Following the player's positive boss feedback and request for greater difficulty:
the Warden now has faster attacks, shorter openings and an enraged phase. A
distinct Tempest midboss appears at wave four; both have entrance scenes and an
original boss music loop. Multi-kill bonuses complement B06's route rewards.

B07 is implemented for playtesting through lunging hunters, flanking/rushing
guards and strafing casters, with animated creature silhouettes toward B15.
Fullscreen default and saved, reversible equipped ranks address part of B16.
B14 still needs a full cue identity and independent volume controls. These
implementations await player acceptance; the remaining backlog remains open.
Current checklist and validation: `docs/ENCOUNTER_EXPANSION.md`.

## Campaign slice status

B08 is implemented for playtesting: eight named encounters introduce enemy roles,
pace reinforcements in packs, and offer timed regroup breaks. Following the
player's feedback, Warden is the midboss and Tempest the finale; their attack
tuning is retained. Soft enemy separation adapts an idea found in the older Echo
Archer prototype. Both Boss Practice victories now finish instead of advancing
into unrelated waves. See `docs/CAMPAIGN_PLAYTEST.md` for acceptance checks.
