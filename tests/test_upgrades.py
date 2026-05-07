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


def test_expanded_archer_upgrades_stack_into_late_damage_and_speed():
    state = new_game_state(
        total_shards=38,
        owned_upgrades={"sharper_arrows_1", "sharper_arrows_2", "quick_draw_1"},
    )

    damage_result = apply_upgrade(state, "sharper_arrows_3")
    speed_result = apply_upgrade(state, "quick_draw_2")
    arrow_result = apply_upgrade(state, "swift_arrows")

    assert damage_result.purchased is True
    assert speed_result.purchased is True
    assert arrow_result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.damage == 17
    assert state.player_stats.fire_rate == 1.44
    assert state.player_stats.arrow_speed == 864.0
    assert state.player_stats.arrow_range == 598.0


def test_piercing_shot_requires_first_damage_upgrade_and_adds_pierce():
    locked_state = new_game_state(total_shards=18)

    locked_result = apply_upgrade(locked_state, "piercing_shot")

    assert locked_result.purchased is False
    assert locked_result.reason == "Prerequisite locked"
    assert locked_state.player_stats.pierce == 0

    state = new_game_state(
        total_shards=18,
        owned_upgrades={"sharper_arrows_1"},
    )

    result = apply_upgrade(state, "piercing_shot")

    assert result.purchased is True
    assert state.player_stats.pierce == 1


def test_expanded_survivor_upgrades_improve_survival_stats():
    state = new_game_state(
        total_shards=38,
        owned_upgrades={"vital_echo"},
    )

    hp_result = apply_upgrade(state, "vital_echo_2")
    speed_result = apply_upgrade(state, "light_feet")
    dash_result = apply_upgrade(state, "shorter_dash_cooldown")

    assert hp_result.purchased is True
    assert speed_result.purchased is True
    assert dash_result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.max_hp == 150
    assert state.player_stats.speed == 297.0
    assert state.player_stats.dash_cooldown == 1.875


def test_expanded_echo_upgrades_reduce_decay_extend_pickup_and_boost_shards():
    state = new_game_state(
        total_shards=40,
        owned_upgrades={"stable_echo"},
    )

    decay_result = apply_upgrade(state, "stable_echo_2")
    magnet_result = apply_upgrade(state, "echo_magnet")
    shard_result = apply_upgrade(state, "memory_of_battle")

    assert decay_result.purchased is True
    assert magnet_result.purchased is True
    assert shard_result.purchased is True
    assert state.total_shards == 0
    assert state.player_stats.echo_decay_multiplier == 0.64
    assert state.player_stats.pickup_radius == 63.0
    assert state.player_stats.shard_gain_multiplier == 1.25
