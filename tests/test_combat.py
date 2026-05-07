from loop_archer.config import ARROW_RANGE
from loop_archer.models import Arrow, Enemy, GameMode, Pickup, Vec2, new_game_state
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


def test_piercing_arrow_damages_two_enemies_before_disappearing():
    state = new_game_state(owned_upgrades={"sharper_arrows_1", "piercing_shot"})
    state.enemies.extend(
        [
            Enemy(id=1, position=Vec2(30, 0), hp=20),
            Enemy(id=2, position=Vec2(32, 0), hp=20),
        ]
    )
    state.arrows.append(
        Arrow(
            id=3,
            position=Vec2(25, 0),
            direction=Vec2(1, 0),
            damage=10,
            speed=0,
            range_remaining=ARROW_RANGE,
            pierce_remaining=state.player_stats.pierce,
        )
    )

    update_world(state, InputState(), 0.016)

    assert [enemy.hp for enemy in state.enemies] == [10, 10]
    assert state.arrows == []


def test_shooting_uses_upgraded_arrow_range_and_pierce():
    state = new_game_state(
        owned_upgrades={"sharper_arrows_1", "piercing_shot", "swift_arrows"}
    )
    state.player.aim_direction = Vec2(1, 0)

    update_world(state, InputState(aim_world=Vec2(100, 0), shoot=True), 0.0)

    assert len(state.arrows) == 1
    assert state.arrows[0].range_remaining == 598.0
    assert state.arrows[0].pierce_remaining == 1
    assert state.arrows[0].speed == 864.0


def test_memory_of_battle_increases_pickup_shards():
    state = new_game_state(owned_upgrades={"memory_of_battle"})
    state.pickups.append(Pickup(id=1, position=state.player.position, value=4))

    update_world(state, InputState(), 0.016)

    assert state.run_shards == 5
    assert state.pickups == []
