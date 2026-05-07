from __future__ import annotations

from dataclasses import dataclass

from loop_archer.models import GameState, UpgradeDefinition, build_player_stats


UPGRADE_DEFINITIONS: dict[str, UpgradeDefinition] = {
    "sharper_arrows_1": UpgradeDefinition(
        id="sharper_arrows_1",
        name="Sharper Arrows I",
        branch="Archer",
        cost=5,
        description="+20% arrow damage",
        damage_multiplier=1.2,
    ),
    "sharper_arrows_2": UpgradeDefinition(
        id="sharper_arrows_2",
        name="Sharper Arrows II",
        branch="Archer",
        cost=10,
        description="+20% arrow damage",
        prerequisites=("sharper_arrows_1",),
        damage_multiplier=1.2,
    ),
    "sharper_arrows_3": UpgradeDefinition(
        id="sharper_arrows_3",
        name="Sharper Arrows III",
        branch="Archer",
        cost=18,
        description="+20% arrow damage",
        prerequisites=("sharper_arrows_2",),
        damage_multiplier=1.2,
    ),
    "quick_draw_1": UpgradeDefinition(
        id="quick_draw_1",
        name="Quick Draw I",
        branch="Archer",
        cost=8,
        description="+20% fire rate",
        fire_rate_multiplier=1.2,
    ),
    "quick_draw_2": UpgradeDefinition(
        id="quick_draw_2",
        name="Quick Draw II",
        branch="Archer",
        cost=12,
        description="+20% fire rate",
        prerequisites=("quick_draw_1",),
        fire_rate_multiplier=1.2,
    ),
    "piercing_shot": UpgradeDefinition(
        id="piercing_shot",
        name="Piercing Shot",
        branch="Archer",
        cost=18,
        description="Arrows hit 1 extra enemy",
        prerequisites=("sharper_arrows_1",),
        pierce_bonus=1,
    ),
    "swift_arrows": UpgradeDefinition(
        id="swift_arrows",
        name="Swift Arrows",
        branch="Archer",
        cost=8,
        description="+20% speed, +15% range",
        arrow_speed_multiplier=1.2,
        arrow_range_multiplier=1.15,
    ),
    "vital_echo": UpgradeDefinition(
        id="vital_echo",
        name="Vital Echo",
        branch="Survivor",
        cost=8,
        description="+25 max HP",
        max_hp_bonus=25,
    ),
    "vital_echo_2": UpgradeDefinition(
        id="vital_echo_2",
        name="Vital Echo II",
        branch="Survivor",
        cost=16,
        description="+25 max HP",
        prerequisites=("vital_echo",),
        max_hp_bonus=25,
    ),
    "light_feet": UpgradeDefinition(
        id="light_feet",
        name="Light Feet",
        branch="Survivor",
        cost=10,
        description="+10% movement speed",
        speed_multiplier=1.1,
    ),
    "shorter_dash_cooldown": UpgradeDefinition(
        id="shorter_dash_cooldown",
        name="Shorter Dash",
        branch="Survivor",
        cost=12,
        description="-25% dash cooldown",
        dash_cooldown_multiplier=0.75,
    ),
    "stable_echo": UpgradeDefinition(
        id="stable_echo",
        name="Stable Echo",
        branch="Echo",
        cost=8,
        description="-20% Echo Decay",
        echo_decay_multiplier=0.8,
    ),
    "stable_echo_2": UpgradeDefinition(
        id="stable_echo_2",
        name="Stable Echo II",
        branch="Echo",
        cost=16,
        description="-20% Echo Decay",
        prerequisites=("stable_echo",),
        echo_decay_multiplier=0.8,
    ),
    "echo_magnet": UpgradeDefinition(
        id="echo_magnet",
        name="Echo Magnet",
        branch="Echo",
        cost=10,
        description="+50% pickup radius",
        pickup_radius_multiplier=1.5,
    ),
    "memory_of_battle": UpgradeDefinition(
        id="memory_of_battle",
        name="Memory of Battle",
        branch="Echo",
        cost=14,
        description="+25% pickup shard value",
        shard_gain_multiplier=1.25,
    ),
}


@dataclass(frozen=True)
class PurchaseResult:
    purchased: bool
    reason: str = ""


def apply_upgrade(state: GameState, upgrade_id: str) -> PurchaseResult:
    definition = UPGRADE_DEFINITIONS.get(upgrade_id)
    if definition is None:
        return PurchaseResult(False, "Unknown upgrade")
    if upgrade_id in state.owned_upgrades:
        return PurchaseResult(False, "Already owned")
    missing = [item for item in definition.prerequisites if item not in state.owned_upgrades]
    if missing:
        return PurchaseResult(False, "Prerequisite locked")
    if state.total_shards < definition.cost:
        return PurchaseResult(False, "Not enough shards")

    state.total_shards -= definition.cost
    state.owned_upgrades.add(upgrade_id)
    state.player_stats = build_player_stats(state.owned_upgrades)
    state.player.hp = min(state.player.hp, state.player_stats.max_hp)
    return PurchaseResult(True)
