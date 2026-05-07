from loop_archer.input import InputState
from loop_archer.models import Enemy, GameMode, Vec2, new_game_state
from loop_archer.systems import begin_next_loop, update_world


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
