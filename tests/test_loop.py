import pytest

from loop_archer import config
from loop_archer.input import InputState
from loop_archer.models import DeathReason, Enemy, GameMode, Vec2, new_game_state
from loop_archer.systems import begin_next_loop, current_echo_decay_rate, update_world


def advance_world(state, seconds):
    steps = int(seconds / 0.05)
    for _ in range(steps):
        update_world(state, InputState(), 0.05)


def test_death_banks_run_shards_and_enters_upgrade_state():
    state = new_game_state()
    state.run_shards = 7
    state.player.hp = 1
    state.player.invincibility_timer = 0
    state.enemies.append(
        Enemy(id=1, position=state.player.position, damage=25, reward=1)
    )

    update_world(state, InputState(), 0.016)

    assert state.mode is GameMode.DEAD_SUMMARY
    assert state.total_shards == 7
    assert state.run_shards == 0
    assert state.last_run_summary.shards_gained == 7
    assert state.last_run_summary.death_reason is DeathReason.OVERWHELMED


def test_begin_next_loop_resets_run_but_keeps_permanent_progress():
    state = new_game_state(total_shards=5, owned_upgrades={"sharper_arrows_1"})
    state.mode = GameMode.DEAD_SUMMARY
    state.enemies.append(Enemy(id=1, position=Vec2(100, 0)))
    state.run_timer = 12

    begin_next_loop(state)

    assert state.mode is GameMode.PLAYING
    assert state.current_loop == 2
    assert state.total_shards == 5
    assert state.owned_upgrades == {"sharper_arrows_1"}
    assert state.player_stats.damage == 12
    assert state.enemies == []
    assert state.run_timer == 0


def test_echo_decay_waits_for_grace_period():
    state = new_game_state()
    state.next_spawn_time = 999

    advance_world(state, config.ECHO_DECAY_GRACE_SECONDS / 2)

    assert state.player.hp == state.player_stats.max_hp
    assert state.mode is GameMode.PLAYING


def test_echo_decay_drips_hp_after_grace_period():
    state = new_game_state()
    state.next_spawn_time = 999

    advance_world(state, config.ECHO_DECAY_GRACE_SECONDS + 1.0)

    assert state.player.hp == pytest.approx(
        state.player_stats.max_hp - config.BASE_ECHO_DECAY_PER_SECOND
    )
    assert state.mode is GameMode.PLAYING


def test_echo_decay_can_end_the_loop_with_echo_faded_reason():
    state = new_game_state()
    state.player.hp = config.BASE_ECHO_DECAY_PER_SECOND * 0.5
    state.run_timer = config.ECHO_DECAY_GRACE_SECONDS

    advance_world(state, 1.0)

    assert state.mode is GameMode.DEAD_SUMMARY
    assert state.last_run_summary.death_reason is DeathReason.ECHO_FADED


def test_echo_decay_rate_uses_player_stat_multiplier():
    state = new_game_state(owned_upgrades={"stable_echo"})

    assert current_echo_decay_rate(
        config.ECHO_DECAY_GRACE_SECONDS + 1.0,
        state.player_stats,
    ) == pytest.approx(config.BASE_ECHO_DECAY_PER_SECOND * 0.8)
