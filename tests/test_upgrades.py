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


def test_second_damage_upgrade_requires_first_damage_upgrade():
    state = new_game_state(total_shards=20)

    result = apply_upgrade(state, "sharper_arrows_2")

    assert result.purchased is False
    assert result.reason == "Prerequisite locked"
    assert state.total_shards == 20
    assert "sharper_arrows_2" not in state.owned_upgrades


def test_second_damage_upgrade_stacks_after_first_damage_upgrade():
    state = new_game_state(
        total_shards=20,
        owned_upgrades={"sharper_arrows_1"},
    )

    result = apply_upgrade(state, "sharper_arrows_2")

    assert result.purchased is True
    assert state.total_shards == 10
    assert state.player_stats.damage == 14


def test_vital_echo_increases_max_hp():
    state = new_game_state(total_shards=8)

    result = apply_upgrade(state, "vital_echo")

    assert result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.max_hp == 125


def test_stable_echo_reduces_echo_decay_multiplier():
    state = new_game_state(total_shards=8)

    result = apply_upgrade(state, "stable_echo")

    assert result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.echo_decay_multiplier == 0.8


def test_quick_draw_increases_fire_rate():
    state = new_game_state(total_shards=8)

    result = apply_upgrade(state, "quick_draw_1")

    assert result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.fire_rate == 1.2
