import pytest

from loop_archer import config
from loop_archer.input import InputState
from loop_archer.models import Vec2, new_game_state
from loop_archer.systems import update_world


def test_dash_moves_in_current_movement_direction():
    state = new_game_state()
    state.next_spawn_time = 999

    update_world(state, InputState(move=Vec2(1, 0), dash=True), 0)

    assert state.player.position.x == pytest.approx(config.DASH_DISTANCE)
    assert state.player.position.y == pytest.approx(0)
    assert state.player.dash_cooldown_timer == pytest.approx(config.DASH_COOLDOWN)


def test_dash_falls_back_to_aim_direction_when_not_moving():
    state = new_game_state()
    state.next_spawn_time = 999

    update_world(state, InputState(aim_world=Vec2(0, -100), dash=True), 0)

    assert state.player.position.x == pytest.approx(0)
    assert state.player.position.y == pytest.approx(-config.DASH_DISTANCE)


def test_dash_cannot_be_reused_until_cooldown_finishes():
    state = new_game_state()
    state.next_spawn_time = 999

    update_world(state, InputState(move=Vec2(1, 0), dash=True), 0)
    first_position = state.player.position
    update_world(state, InputState(move=Vec2(1, 0), dash=True), 0)

    assert state.player.position == first_position


def test_dash_stays_inside_arena_boundary():
    state = new_game_state()
    state.next_spawn_time = 999
    state.player.position = Vec2(state.arena_radius - config.PLAYER_RADIUS - 10, 0)

    update_world(state, InputState(move=Vec2(1, 0), dash=True), 0)

    assert state.player.position.length() <= state.arena_radius - config.PLAYER_RADIUS
