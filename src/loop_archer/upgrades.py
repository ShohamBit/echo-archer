from __future__ import annotations

from dataclasses import dataclass

from loop_archer.models import GameState, UpgradeDefinition, build_player_stats


UPGRADE_DEFINITIONS: dict[str, UpgradeDefinition] = {
    "sharper_arrows_1": UpgradeDefinition(
        id="sharper_arrows_1",
        name="Sharper Arrows I",
        branch="Archer",
        cost=5,
        damage_multiplier=1.2,
    )
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
