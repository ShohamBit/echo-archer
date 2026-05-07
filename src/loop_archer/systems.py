from __future__ import annotations

from math import pi

from loop_archer import config
from loop_archer.input import InputState
from loop_archer.models import (
    Arrow,
    DeathReason,
    Enemy,
    EnemyKind,
    GameMode,
    GameState,
    Pickup,
    Player,
    RunSummary,
    Vec2,
    build_player_stats,
    clamp_to_arena,
)


def create_enemy(entity_id: int, kind: EnemyKind, position: Vec2) -> Enemy:
    if kind is EnemyKind.FAST:
        return Enemy(
            id=entity_id,
            position=position,
            kind=kind,
            hp=config.FAST_CHASER_HP,
            speed=config.FAST_CHASER_SPEED,
            damage=config.FAST_CHASER_DAMAGE,
            reward=config.FAST_CHASER_REWARD,
            radius=config.FAST_CHASER_RADIUS,
        )

    return Enemy(id=entity_id, position=position, kind=EnemyKind.CHASER)


def begin_next_loop(state: GameState) -> None:
    state.current_loop += 1
    state.mode = GameMode.PLAYING
    state.player_stats = build_player_stats(state.owned_upgrades)
    state.player = Player(hp=state.player_stats.max_hp)
    state.enemies.clear()
    state.arrows.clear()
    state.pickups.clear()
    state.run_timer = 0.0
    state.next_spawn_time = 0.5
    state.spawn_count = 0
    state.run_shards = 0
    state.kills = 0
    state.pending_death_reason = None


def end_run(state: GameState) -> None:
    if state.mode is not GameMode.PLAYING:
        return

    survival_bonus = int(state.run_timer // 10)
    gained = state.run_shards + survival_bonus
    state.total_shards += gained
    state.best_time = max(state.best_time, state.run_timer)
    state.last_run_summary = RunSummary(
        time_survived=state.run_timer,
        enemies_defeated=state.kills,
        shards_gained=gained,
        death_reason=state.pending_death_reason or DeathReason.OVERWHELMED,
    )
    state.run_shards = 0
    state.mode = GameMode.DEAD_SUMMARY
    state.enemies.clear()
    state.arrows.clear()
    state.pickups.clear()


def update_world(state: GameState, input_state: InputState, dt: float) -> None:
    if state.mode is not GameMode.PLAYING:
        return

    dt = min(max(dt, 0.0), 0.05)
    previous_time = state.run_timer
    state.run_timer += dt
    _update_player(state, input_state, dt)
    _apply_echo_decay(state, previous_time, state.run_timer)
    if state.player.hp <= 0:
        end_run(state)
        return

    _shoot_if_ready(state, input_state)
    _spawn_due_waves(state)
    _update_enemies(state, dt)
    _update_arrows(state, dt)
    _resolve_arrow_hits(state)
    _collect_pickups(state, dt)

    if state.player.hp <= 0:
        end_run(state)


def current_echo_decay_rate(run_timer: float, player_stats=None) -> float:
    if run_timer < config.ECHO_DECAY_GRACE_SECONDS:
        return 0.0
    ramp_time = max(0.0, run_timer - config.ECHO_DECAY_RAMP_START_SECONDS)
    base_rate = config.BASE_ECHO_DECAY_PER_SECOND + (
        ramp_time * config.ECHO_DECAY_RAMP_PER_SECOND
    )
    if player_stats is None:
        return base_rate
    return base_rate * player_stats.echo_decay_multiplier


def _apply_echo_decay(state: GameState, previous_time: float, current_time: float) -> None:
    decay_start = config.ECHO_DECAY_GRACE_SECONDS
    if current_time <= decay_start:
        return

    active_seconds = current_time - max(previous_time, decay_start)
    if active_seconds <= 0:
        return

    state.player.hp -= (
        current_echo_decay_rate(current_time, state.player_stats) * active_seconds
    )
    if state.player.hp <= 0 and state.pending_death_reason is None:
        state.pending_death_reason = DeathReason.ECHO_FADED


def _update_player(state: GameState, input_state: InputState, dt: float) -> None:
    player = state.player
    player.shot_cooldown = max(0.0, player.shot_cooldown - dt)
    player.dash_cooldown_timer = max(0.0, player.dash_cooldown_timer - dt)
    player.dash_flash_timer = max(0.0, player.dash_flash_timer - dt)
    player.invincibility_timer = max(0.0, player.invincibility_timer - dt)
    player.hit_flash_timer = max(0.0, player.hit_flash_timer - dt)

    aim = (input_state.aim_world - player.position).normalized()
    if aim.length() > 0:
        player.aim_direction = aim

    _dash_if_ready(state, input_state)

    move = input_state.move.normalized()
    player.position = clamp_to_arena(
        player.position + move * state.player_stats.speed * dt,
        state.arena_radius,
    )


def _dash_if_ready(state: GameState, input_state: InputState) -> None:
    if not input_state.dash or state.player.dash_cooldown_timer > 0:
        return

    direction = input_state.move.normalized()
    if direction.length() <= 0:
        direction = state.player.aim_direction.normalized()
    if direction.length() <= 0:
        direction = Vec2(1, 0)

    state.player.position = clamp_to_arena(
        state.player.position + direction * state.player_stats.dash_distance,
        state.arena_radius,
    )
    state.player.dash_cooldown_timer = state.player_stats.dash_cooldown
    state.player.dash_flash_timer = 0.12


def _shoot_if_ready(state: GameState, input_state: InputState) -> None:
    if not input_state.shoot or state.player.shot_cooldown > 0:
        return

    direction = state.player.aim_direction.normalized()
    if direction.length() <= 0:
        direction = Vec2(1, 0)
    spawn_position = state.player.position + direction * (state.player.radius + 8)
    state.arrows.append(
        Arrow(
            id=state.next_id(),
            position=spawn_position,
            direction=direction,
            damage=state.player_stats.damage,
            speed=state.player_stats.arrow_speed,
            range_remaining=state.player_stats.arrow_range,
            pierce_remaining=state.player_stats.pierce,
        )
    )
    state.player.shot_cooldown = 1.0 / state.player_stats.fire_rate


def _spawn_due_waves(state: GameState) -> None:
    while state.run_timer >= state.next_spawn_time:
        wave_size = min(8, 3 + int(state.run_timer // 18))
        for index in range(wave_size):
            angle = (
                state.spawn_count * 1.37
                + index * (2 * pi / wave_size)
                + state.current_loop * 0.41
            )
            position = Vec2.from_angle(angle) * (state.arena_radius - 8)
            kind = _enemy_kind_for_spawn(state.run_timer, index)
            enemy = create_enemy(state.next_id(), kind, position)
            if kind is EnemyKind.CHASER:
                enemy.speed = config.CHASER_SPEED + min(35, state.run_timer * 0.35)
            state.enemies.append(enemy)
        state.spawn_count += 1
        period = max(1.2, 4.2 - min(state.run_timer, 90) / 35)
        state.next_spawn_time += period


def _enemy_kind_for_spawn(run_timer: float, spawn_index: int) -> EnemyKind:
    if run_timer >= 18.0 and spawn_index % 4 == 0:
        return EnemyKind.FAST
    return EnemyKind.CHASER


def _update_enemies(state: GameState, dt: float) -> None:
    player = state.player
    separation_offsets = _enemy_separation_offsets(state.enemies)
    survivors: list[Enemy] = []
    for enemy in state.enemies:
        enemy.hit_flash_timer = max(0.0, enemy.hit_flash_timer - dt)
        direction = (player.position - enemy.position).normalized()
        separation = separation_offsets.get(enemy.id, Vec2())
        enemy.position = enemy.position + (
            direction * enemy.speed + separation * config.ENEMY_SEPARATION_STRENGTH
        ) * dt

        if enemy.position.distance_to(player.position) <= enemy.radius + player.radius:
            if player.invincibility_timer <= 0:
                player.hp -= enemy.damage
                if player.hp <= 0:
                    state.pending_death_reason = DeathReason.OVERWHELMED
                player.invincibility_timer = state.player_stats.invincibility_seconds
                player.hit_flash_timer = 0.12
        survivors.append(enemy)
    state.enemies = survivors


def _enemy_separation_offsets(enemies: list[Enemy]) -> dict[int, Vec2]:
    offsets = {enemy.id: Vec2() for enemy in enemies}
    for index, enemy in enumerate(enemies):
        for other in enemies[index + 1 :]:
            delta = enemy.position - other.position
            distance = delta.length()
            desired = enemy.radius + other.radius
            if distance >= desired:
                continue

            direction = delta.normalized()
            if direction.length() <= 0:
                direction = Vec2(1, 0)
            strength = (desired - distance) / desired
            push = direction * strength
            offsets[enemy.id] = offsets[enemy.id] + push
            offsets[other.id] = offsets[other.id] - push
    return offsets


def _update_arrows(state: GameState, dt: float) -> None:
    remaining: list[Arrow] = []
    for arrow in state.arrows:
        distance = arrow.speed * dt
        arrow.position = arrow.position + arrow.direction * distance
        arrow.range_remaining -= distance
        if arrow.range_remaining > 0 and arrow.position.length() <= state.arena_radius + 80:
            remaining.append(arrow)
    state.arrows = remaining


def _resolve_arrow_hits(state: GameState) -> None:
    arrows_left: list[Arrow] = []
    dead_enemy_ids: set[int] = set()

    for arrow in state.arrows:
        consumed = False
        for enemy in state.enemies:
            if enemy.id in dead_enemy_ids:
                continue
            if arrow.position.distance_to(enemy.position) > arrow.radius + enemy.radius:
                continue

            enemy.hp -= arrow.damage
            enemy.hit_flash_timer = 0.08
            if enemy.hp <= 0:
                dead_enemy_ids.add(enemy.id)
                state.pickups.append(
                    Pickup(id=state.next_id(), position=enemy.position, value=enemy.reward)
                )
                state.kills += 1

            if arrow.pierce_remaining > 0:
                arrow.pierce_remaining -= 1
            else:
                consumed = True
                break

        if not consumed:
            arrows_left.append(arrow)

    if dead_enemy_ids:
        state.enemies = [
            enemy for enemy in state.enemies if enemy.id not in dead_enemy_ids
        ]
    state.arrows = arrows_left


def _collect_pickups(state: GameState, dt: float) -> None:
    kept: list[Pickup] = []
    for pickup in state.pickups:
        to_player = state.player.position - pickup.position
        distance = to_player.length()
        if distance <= state.player.radius + pickup.radius:
            state.run_shards += max(
                1,
                round(pickup.value * state.player_stats.shard_gain_multiplier),
            )
            continue

        if distance <= state.player_stats.pickup_radius and distance > 0:
            pickup.position = (
                pickup.position
                + to_player.normalized() * config.PICKUP_MAGNET_SPEED * dt
            )
        kept.append(pickup)
    state.pickups = kept
