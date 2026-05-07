from loop_archer.config import ARROW_RANGE
from loop_archer.models import Arrow, Enemy, GameMode, Vec2, new_game_state
from loop_archer.systems import update_world
from loop_archer.input import InputState


def test_arrow_hit_reduces_enemy_hp_and_removes_arrow():
    state = new_game_state()
    enemy = Enemy(id=1, position=Vec2(30, 0), hp=20)
    arrow = Arrow(
        id=2,
        position=Vec2(20, 0),
        direction=Vec2(1, 0),
        damage=10,
        speed=0,
        range_remaining=ARROW_RANGE,
    )
    state.enemies.append(enemy)
    state.arrows.append(arrow)

    update_world(state, InputState(), 0.016)

    assert state.enemies[0].hp == 10
    assert state.arrows == []


def test_enemy_death_grants_shard_pickup():
    state = new_game_state()
    enemy = Enemy(id=1, position=Vec2(30, 0), hp=10, reward=3)
    arrow = Arrow(
        id=2,
        position=Vec2(20, 0),
        direction=Vec2(1, 0),
        damage=10,
        speed=0,
        range_remaining=ARROW_RANGE,
    )
    state.enemies.append(enemy)
    state.arrows.append(arrow)

    update_world(state, InputState(), 0.016)

    assert state.enemies == []
    assert state.pickups[0].value == 3
    assert state.kills == 1
    assert state.mode is GameMode.PLAYING
