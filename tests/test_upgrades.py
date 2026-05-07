from loop_archer.models import GameMode, new_game_state
from loop_archer.upgrades import apply_upgrade


def test_upgrade_purchase_subtracts_shards_and_increases_damage():
    state = new_game_state(total_shards=10)

    result = apply_upgrade(state, "sharper_arrows_1")

    assert result.purchased is True
    assert state.total_shards == 5
    assert "sharper_arrows_1" in state.owned_upgrades
    assert state.player_stats.damage == 12
    assert state.mode is GameMode.PLAYING


def test_upgrade_cannot_be_bought_without_enough_shards():
    state = new_game_state(total_shards=4)

    result = apply_upgrade(state, "sharper_arrows_1")

    assert result.purchased is False
    assert result.reason == "Not enough shards"
    assert state.total_shards == 4
    assert state.player_stats.damage == 10
    assert state.owned_upgrades == set()
