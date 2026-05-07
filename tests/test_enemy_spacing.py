from loop_archer.input import InputState
from loop_archer.models import Enemy, Vec2, new_game_state
from loop_archer.systems import update_world


def test_chasers_push_apart_when_clustered():
    state = new_game_state()
    state.next_spawn_time = 999
    state.player.position = Vec2(180, 0)
    state.enemies.append(Enemy(id=1, position=Vec2(-40, 0)))
    state.enemies.append(Enemy(id=2, position=Vec2(-35, 0)))
    before_distance = state.enemies[0].position.distance_to(state.enemies[1].position)

    update_world(state, InputState(), 0.05)

    after_distance = state.enemies[0].position.distance_to(state.enemies[1].position)
    assert after_distance > before_distance
