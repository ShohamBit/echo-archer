from loop_archer import config
from loop_archer.input import InputState
from loop_archer.models import EnemyKind, Vec2, new_game_state
from loop_archer.systems import create_enemy, update_world


def test_fast_enemy_uses_fast_enemy_stats():
    enemy = create_enemy(1, EnemyKind.FAST, Vec2(10, 20))

    assert enemy.kind is EnemyKind.FAST
    assert enemy.position == Vec2(10, 20)
    assert enemy.hp == config.FAST_CHASER_HP
    assert enemy.speed == config.FAST_CHASER_SPEED
    assert enemy.damage == config.FAST_CHASER_DAMAGE
    assert enemy.reward == config.FAST_CHASER_REWARD
    assert enemy.radius == config.FAST_CHASER_RADIUS


def test_later_waves_mix_fast_enemies_with_chasers():
    state = new_game_state()
    state.run_timer = 20.0
    state.next_spawn_time = 20.0

    update_world(state, InputState(), 0.05)

    kinds = {enemy.kind for enemy in state.enemies}
    assert EnemyKind.CHASER in kinds
    assert EnemyKind.FAST in kinds
