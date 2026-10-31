# Loop Archer design research and interview

Date: 2026-10-31. Status: direction revised by user after the presentation trial.
The original research remains context; fidelity is no longer the product goal.

## Latest accepted direction

The user reported lag, rejected the pixelated appearance, reported premature
"Loop breached" victory, and explicitly asked to make an independent game.
This supersedes the earlier faithful-visual milestone. Keep the existing progress
and combat identity, use a smooth modern presentation, fix objective completion,
and then develop richer encounters and progression. See ADR-0001.

Measured causes: the previous full-screen effects consumed88.6ms/frame on average;
the inherited fifteen-spawn finish fired rapidly with maxed spawn upgrades.
The revised benchmark is recorded in `artifacts/performance-after.json`; detailed
original mechanics remain evidence, rather than binding product requirements.

## Confirmed project context

- The user wants to extend the supplied Loop Archer in Python.
- The first recreation differed materially from the original; exact control-flow
  recovery subsequently corrected arrow inventory, portals, recall and scale.
- The user still finds the visual presentation different and prefers the original
  spatial skill tree over the recreation's grid.
- The user has maxed the Python recreation, not the original. The current save
  confirms all 19 upgrade types at their caps after 26 recorded attempts, with
  1,540 unspent points. The save has no playtime measurement; elapsed time and
  whether the player considers that pace too fast remain unknown.
- Preserve progress while discussing or changing the presentation.
- Work uses an 80%-used threshold for either reported account usage window as a
  best-effort stopping rule in this chat. Avoid additional subagents for now.

## Primary sources and bounded findings

### 1. The original Loop Archer creator

The creator describes permanent skill-tree upgrades between deaths and says a
planned final boss was unfinished. They also identify Nodebuster as an influence
in the comments. This supports examining the progression experience as well as
combat, without establishing that any particular extension will be enjoyable.

Source: [PolyCube's original game page](https://polycube2.itch.io/looparcher).

### 2. Nodebuster's developer-authored store description

Nodebuster describes a short incremental experience about gathering resources,
exploring an upgrade tree and growing extremely powerful. This is a reference for
progression and anticipation, not evidence that copying its balance or layout
will work here. Store-page claims are product descriptions, not controlled studies.

Source: [Nodebuster, Goblobin](https://store.steampowered.com/app/3107330/Nodebuster/).

### 3. Titan Souls, explained by its developer

Mark Foster describes firing and retrieving a single arrow as the foundation of
Titan Souls, with bosses distinguished by different moves and weaknesses.
This offers a directly relevant design reference: additional depth can come from
enemy behavior and positioning while retaining one-arrow combat. Its punishing
difficulty and absence of overt prompts are not recommendations for Loop Archer.

Source: [Mark Foster / Acidnerve on Titan Souls](https://blog.playstation.com/archive/2014/07/03/one-arrow-one-life-lots-bosses-can-survive-titan-souls-ps4vita/).

### 4. Game-feel research lead

Jan Willem Nijman's own website lists his talk The Art of Screenshake. The video
could not be fetched in this session, so no detailed technique or numeric tuning
is attributed to it here. It is a follow-up source, not reviewed evidence.

Source: [Jan Willem Nijman's selected talks](https://www.jwaaaap.com/).

## Design hypotheses to test, not settled decisions

| Hypothesis | Concrete experiment | Evidence that would change our mind |
| --- | --- | --- |
| The tree should feel like discovery, rather than a list of purchases | Prototype a movable connected map with purchased, available and undiscovered states; compare with the grid at identical costs | The player prefers seeing all upgrades immediately or finds navigation tedious |
| Major upgrades should change a visible behavior | Preview a milestone upgrade through a brief before/after demonstration | Previews interrupt the loop or make discovery less satisfying |
| Restore recognizable visual feedback before adding content | Compare identical combat with matched bow deformation, pixel scale, glow and sound timing | The player identifies pacing or progression as the larger remaining problem |
| A maxed player needs a reason beyond more ranks | Try a boss whose weakness rewards portal placement or return-arrow positioning | The player wants relaxed power growth rather than mechanical mastery |

These are design inferences from the references and user feedback. Sources do
not prove the best upgrade cadence, session length, effect strength or endgame.

## Accepted decisions: round one

1. First milestone: restore the original visual feel and skill-tree experience
   before adding mechanics. The user answered yes.
2. Fully upgraded refers to the Python recreation. Corrects the earlier ambiguity.
3. Every permanent upgrade should eventually be obtainable. Branches provide
   discovery and purchase-order choices, not permanent mutually exclusive builds.
4. After the faithful foundation, add a proper finale and optional mastery
   challenges rather than relying on endlessly increasing ranks.

These settle direction, not implementation approval for the complete design.
Do not reset or rebalance the existing save merely because it is fully upgraded.

## Accepted decisions: round two

The user answered yes to all four recommendations:

5. Use a short visual/combat/shop comparison as the acceptance checkpoint before
   expanding content; automated tests alone do not establish matching feel.
6. Preserve existing prices, balance and progress during the presentation pass.
7. Match the original pixel/glow/animation direction with independent options to
   reduce shake, flashes and blur.
8. The later boss should test portal, ricochet and recall positioning rather than
   primarily scaling health and damage.

This closes the first milestone's design frontier. Pacing changes and the detailed
boss/challenge design are deferred, not silently selected.

## Presentation comparison build

- `Compare Presentation.cmd` starts a temporary, read-only profile so purchases
  and branch discovery can be tried without changing the player's maxed save.
- Tree positions are mapped from actual placed SkillTreeMap root-component
  coordinates. NodeBase Kismet confirms child spawn/cable creation and hover/hold
  effects; UpgradePlayer confirms movement input for traversing the map.
- Two original TrueType font payloads are copied from their `.ufont` members;
  `assets/PROVENANCE.json` retains source paths and hashes.
- Icons are newly drawn pixel silhouettes; bloom, color separation, bow deformation
  and purchase animation are approximations, not recovered Unreal rendering.
- The short comparison checklist is in `docs/PRESENTATION_CHECKPOINT.md`.
- A headless preview initially banked three points and one attempt. The exact
  pre-preview values were restored. Headless CLI and comparison mode now disable
  saving; a regression test exercises banking through the actual CLI path.

## Interview decision tree

Round one (answered):

1. Direction: faithful foundation with selective extensions, or broader redesign?
2. Clarify which version was maxed before inferring progression needs.
3. Skill-tree role: eventually acquire everything, or mutually exclusive builds?
4. Endgame motivation: a crafted finale and optional challenges, or indefinite
   progression as the central experience?

Round two frontier:

5. Acceptance: compare a short original/recreation sequence covering charge,
   release, portal wrap, ricochet, recall and a shop purchase before expanding scope.
6. Milestone scope: preserve prices and balance for the visual/shop restoration,
   or rebalance progression simultaneously?
7. Presentation options: faithful default effects with independent reductions for
   shake, flashes and blur, or a fixed visual treatment?
8. Future finale: prefer a boss testing portal/ricochet/recall positioning over a
   large health pool and repeated ordinary attacks?

Local shop evidence now confirms the original has hover/hold animations, rank
updates and discovery links; the NodeBase graph tests CurrentLevel>=1. Recover
exact navigation/reveal behavior from the remaining graph before presenting it
as fact. The player's preference for the original does not authorize inventing
a replacement interface.

Later frontier after these answers: fidelity acceptance checkpoint, exact shop
input/navigation, total progression length and cadence, scope of the first boss
and mastery challenges, and final user confirmation of shared understanding.

The later independent-game direction is recorded in
`docs/adr/0001-independent-game-direction.md`. The first combat slice now implements
backlog B02, B05 and B06: bow-state clarity, a Warden encounter with a rear-core
opening, and flat skillshot rewards. Player acceptance remains pending; see
`docs/COMBAT_SLICE.md`. Earlier interview frontiers above are historical context.
