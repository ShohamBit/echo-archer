# Decoded original gameplay logic

This pass reads actual cooked Kismet instructions, unlike the first pass's
strings/default-only inspection. The original installation is unchanged.

## Reproduce and provenance

- Original pak SHA-256: `6c12fa5dda779e148deac5c99048e90ff2053ae3d5c7b9c064700b4da4ef0441`.
- Parser: official [UAssetGUI alpha8 release](https://github.com/atenfyr/UAssetGUI/releases/tag/v1.0.0.0-alpha.8),
  `net472/UAssetGUI.exe`, acquired solely as an analysis tool, not a game dependency.
- The bundled API identifies itself as `UAssetAPI 1.0.0.0 (8035554)`.
- Export command: `UAssetGUI.exe tojson source.uasset destination.json VER_UE4_27`.
  The source assets have stripped engine version fields. 4.27 is the selected
  parsing profile, not a proved recorded engine version. All selected scripts
  decode and the projected logical bytecode sizes match the declared sizes.
- Run `python analysis/blueprints/extract_selected.py`, then inspect the JSON
  and `*.kismet.txt`. The latter includes instruction index and reconstructed
  in-memory `@offset`, and resolves package references to human-readable names.
  It is a readable AST projection, not original Blueprint graph layout.
- `read_kismet.py` checks every projected function's instruction total against
  `ScriptBytecodeSize`, including the 36,946-byte Player event graph, 6,661-byte
  Arrow graph and 3,932-byte WaveManager graph.

No target game code is executed by this decoding. Most statements below are
observations of compiled control flow. Engine collision semantics and screen
projection are separately identified as derived interpretations.

## One-arrow lifecycle (Player)

`CanShoot?` starts true. Shoot press only enters the charge gate if it is true.
Release while `HoldingShoot?` clears that flag, sets `CanShoot?=false`, hides
the held arrow, then invokes `ShootBow`. The `PickedUpArrow` event calls
`StopRecall`, sets `Recalling?=false`, sets `CanShoot?=true`, and shows the held
arrow again. This establishes one volley until pickup, rather than unlimited
new arrows. Multishot spawns two arrows at rank one, three at rank two, but
each pickup invokes the same readiness reset.

Sources: Player instructions 762–827, 1129–1154; event wrapper `PickedUpArrow`
enters the event graph at @31774; `ShootBow` enters @18440.

Charge starts at level 1 and increments every `ShootingSpeed/4`, clamping to
level 4. Baseline `ShootingSpeed=1.25`; upgrades subtract `rank*0.15` directly.
Thus level 4 is reached after 0.9375 seconds at baseline; this is not the prior
continuous ratio/1.25 formula. Auto-fire is scheduled at `AutoFIreTime=4` while
holding and invokes the release behavior. Charge level speed table is
1:1000, 2:1500, 3:2000, 4:2750 world units/s. The spawned `Speed` property is
that table value plus 250 plus arrow-speed rank*250; the initial `Velocity`
uses the table value. Negative forward-vector direction is the asset's bow
orientation convention, not backward firing relative to its cursor.

Arrow damage is `1+DamageNode`, plus the full-charge upgrade only at level>=4.
Full charge does **not** enable piercing: the Arrow hit routine never stops
flight on enemy overlap. The initial remake's partial-shot stop was invented.

Sources: Player instructions 56–98, 762–768, 847–856, 1108–1116;
Arrow instructions 40–55 and 113–119.

## Recall (Player and Arrow)

Recall is held input. `InputActionDelegateBinding_0` maps Recall pressed to
`InpActEvt_Recall..._2` and released to `_3`. Press scans arrows but only calls
`StartRecallingArrow` for arrows with `Stopped?=true`. Release iterates arrows
and calls `StopRecallingArrow`.

`StartRecallingArrow` sets `Recalling?=true`, enables damage and plays a timeline.
Every update computes `VInterpTo(currentArrowLocation, currentPlayerLocation,
RecallAnimValue, 0.15)` and sets the arrow position, so it homes toward the live
player. It does not aim at a position snapshot. Note the original feeds the
curve value into VInterpTo's DeltaTime argument, not real frame delta; matching
its exact feel requires a chosen simulation tick rate or measured equivalent.

The recall curve is cubic with keys `(time,value)=(0,0),(.35,.1),(1,1)`;
the middle arrive tangent is .50490886, leave tangent1.2319362; endpoint tangents0.
The timeline is one second long and its finished callback restarts recall.
Arrow rotation also interpolates toward the player with speed5.

Self-damage explicitly requires `NOT Recalling?`, `CanDamage=true`, a collision
component tagged `Player`, and immunity rank0. Recalled arrows are safe;
the dangerous arrows are still flying/bouncing outward. The prior remake's
returning-arrow self-damage was the opposite rule.

The player's `ArrowPick` sphere radius is100 world units; its damage sphere
radius is50. Arrow capsule radius35. Stopped arrows touching ArrowPick invoke
StartPickup and eventually Player.PickedUpArrow. Effective circular overlap
distance is about135 units if simplifying the original 3D capsule/sphere pair.

Sources: Player instructions 304–367 and386–416; Arrow instructions2–8,
168–186,207–223,238–250; Arrow `CurveFloat_0` and `RecallAnim_Template`;
Player `Sphere_GEN_VARIABLE` and `Sphere1_GEN_VARIABLE`.

## Flight, bounce and portals (Arrow, Portal, GameplayMap)

Flight starts a repeated .1-second timer. Each tick increments SpeedDecrease by
250 and sets InitialSpeed/MaxSpeed to Speed-SpeedDecrease. At <=300, the arrow
sets Stopped, disables damage and resets its enemy hit list. At <=0 it clears
the timer and zeros velocity. This is a speed-dependent travel budget, not
a fixed 1.6-second lifespan. Bounces do not consume/destroy the arrow.

ProjectileMovement has bShouldBounce=true, Bounciness=5, Friction=0, gravity0,
and MaxSpeed clamping. Every bounce sets Bounced=true and resets EnemiesHitList,
allowing another hit on the same enemy after a bounce. BounceDamageNode is
added to outward damage once Bounced is true. Recall uses its separate
1+RecallDamageNode value. An enemy is not repeatedly damaged during a single
unchanged overlap pass.

There are also actual side portals. Portal overlap checks component tag arrow,
NOT Recalling and NOT RecentlyTeleported; then it calls Arrow.TeleportEvent
and teleports location by PositionChange. GameplayMap overrides are
`(0,+1400,0)` and `(0,-1400,0)`. With the top-down camera, world Y corresponds
to horizontal screen travel. Thus side arrows can wrap to the opposite side
without reversing direction, while other physical walls reflect.

Portal actor world Y≈-775/+791, world X=-180, scale(3.75,1.25,3.5).
Portal box component scale(8.5,1,1), with inherited box extent32, implies long
halfextent1020, spanning the vertical arena. This geometry calculation assumes
the standard inherited BoxComponent extent, absent an override. TeleportEvent
sets RecentlyTeleported true, clears hit history and schedules reset after.25s.

Sources: Arrow instructions21–23,123–160,188–193,258–263;
`ProjectileMovement_GEN_VARIABLE`; Portal instructions4–13;
GameplayMap placed Portal2 and Portal_2 data.

## Scale and movement

Player capsule radius60, camera FOV80 and constrained square aspect ratio.
Camera `OrthoWidth=500` is present, but no ProjectionMode override is present;
the inherited perspective mode makes OrthoWidth irrelevant. Camera SpringArm
length1000 implies a visible width of approximately
`2*1000*tan(80deg/2)=1678` world units, before camera animation/height effects.
This is a derived projection estimate, not a pixel-perfect measurement.

Physical walls are around world X=-811/+848 and Y=-854/+850. A screen-size
simulation should convert world speeds/radii by approximately screenSide/1678.
Using speeds500 directly as pixels/second in an880px arena made movement
roughly twice as fast relative to the world. The tiny radius12 had no support.

Baseline movement500 plus25/rank. During charge, a timeline lerps movement
speed from full to half. During recall, movement is divided by5, and a reset
timeline restores normal speed afterward. The CharacterMovement component
declares MaxAcceleration10000, BrakingDecelerationWalking3000, GroundFriction3.

Sources: Player component defaults and instructions648–651,355–356,
1178–1180,1278–1280; GameplayMap wall component transforms.

## Timer and spawning

The Player graph explicitly initializes TimeLeft=DefaultTime; this resolves
the old default ambiguity in favor of10 starting seconds plus3/timer rank.
Countdown ticks subtract.05. TimerAddition clamps to DefaultTime, updates bar,
then waits.3seconds before countdown restarts. Shield hit also calls
TimerAddition(5), beyond the earlier recreation's shield absorption alone.

Original WaveManager is not a clear-every-wave arena schedule. BeginPlay
waits.75s, spawns once, and starts periodic spawning at a sampled interval
1.45–1.5 seconds. Spawn location is radius850 on a random rotating arm.
Default pool is ordinary enemies. At normal-spawn count3+MoreEnemiesRank,
a one-shot gate changes pool to heavy enemies and interval2–2.25 seconds.
At randomly selected threshold9+rank through10+rank, pool becomes shooters,
interval3.5–4. At15+rank another gate switches shooter interval2–3.
The StartSpawning function subtracts MoreEnemiesRank*.5 from interval.

Nugget probability in actual instructions is `5+2*rank` percent, despite the
upgrade text's2.5 label. Nugget spawning exits before normal-count increment.
ReceiveTick separately breaches the loop at raw normal-spawn count>=15,
regardless of live enemies; it invokes Player.Death with end-game flags.
This may truncate the final threshold branch and is preserved as an observed
original-code inconsistency, not silently repaired in this report.

Sources: Player instructions117–119,1183–1206,1236;
WaveManager @1255–1394,@1395–2745,@2772–3453,@3458–3771,@3777–3924.

## Limitations

These are static cooked control-flow observations, not a complete playthrough.
Unreal component integration, collisions, timeline ticks, camera motion and
postprocessing can affect feel. An exact equivalent requires runtime comparison.
The JSON parser profile was selected4.27 rather than read from a recorded
engine version; matched bytecode lengths are a consistency check, not proof
every asset rendering detail was interpreted perfectly. No whole native binary
decompilation or original editor graph reconstruction was attempted.
