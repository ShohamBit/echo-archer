"""Distinct ordinary enemy decisions, with committed and readable attacks."""
from pygame import Vector2 as Vec


def separate_enemies(enemies, dt, bounds=(1680, 1680)):
    """Soft local spacing; committed attacks and bosses keep their positions.

    A spatial grid avoids checking every pair across the entire arena.
    """
    bodies = [enemy for enemy in enemies if not enemy.warden]
    grid, offsets = {}, {enemy.id: Vec() for enemy in bodies}
    cell_size = max((enemy.radius * 2 for enemy in bodies), default=200)
    for enemy in bodies:
        cell = (int(enemy.pos.x // cell_size), int(enemy.pos.y // cell_size))
        grid.setdefault(cell, []).append(enemy)
    for enemy in bodies:
        cell = (int(enemy.pos.x // cell_size), int(enemy.pos.y // cell_size))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in grid.get((cell[0] + dx, cell[1] + dy), ()):
                    if other.id <= enemy.id:
                        continue
                    delta = enemy.pos - other.pos
                    desired = (enemy.radius + other.radius) * .9
                    distance = delta.length()
                    if distance >= desired:
                        continue
                    direction = delta / distance if distance else Vec(1, 0).rotate((enemy.id * 73 + other.id * 31) % 360)
                    push = direction * ((desired - distance) / desired) * 160
                    offsets[enemy.id] += push
                    offsets[other.id] -= push
    for enemy in bodies:
        if enemy.phase not in ("hunt", "recover"):
            continue
        push = offsets[enemy.id]
        if push.length_squared() > 180 ** 2:
            push.scale_to_length(180)
        enemy.pos += push * dt
        enemy.pos.x = max(enemy.radius, min(bounds[0] - enemy.radius, enemy.pos.x))
        enemy.pos.y = max(enemy.radius, min(bounds[1] - enemy.radius, enemy.pos.y))


def update_enemy(enemy, player, dt):
    """Move in-place and return projectile velocities; no rendering dependencies."""
    delta = player - enemy.pos
    distance = delta.length()
    toward = delta.normalize() if distance else Vec(1, 0)
    enemy.heading = toward if enemy.phase == "hunt" else enemy.heading
    enemy.attack_clock -= dt
    speed = max(20, enemy.speed - enemy.slow)
    shots = []
    if enemy.kind == "chaser":
        if enemy.phase == "hunt":
            enemy.pos += toward * speed * dt
            if distance < 540 and enemy.attack_clock <= 0:
                enemy.phase, enemy.attack_clock = "windup", .65
                enemy.heading = toward
        elif enemy.phase == "windup" and enemy.attack_clock <= 0:
            enemy.phase, enemy.attack_clock = "lunge", .3
        elif enemy.phase == "lunge":
            enemy.pos += enemy.heading * 1000 * dt
            if enemy.attack_clock <= 0:
                enemy.phase, enemy.attack_clock = "recover", .7
        elif enemy.phase == "recover" and enemy.attack_clock <= 0:
            enemy.phase, enemy.attack_clock = "hunt", 1.4
    elif enemy.kind == "tank":
        # Walk across the player's approach, then commit to a short shield rush.
        if enemy.phase == "hunt":
            enemy.pos += (toward * .6 + toward.rotate(90) * (.8 if enemy.id % 2 else -.8)) * speed * dt
            if distance < 600 and enemy.attack_clock <= 0:
                enemy.phase, enemy.attack_clock = "windup", .9
                enemy.heading = toward
        elif enemy.phase == "windup" and enemy.attack_clock <= 0:
            enemy.phase, enemy.attack_clock = "lunge", .45
        elif enemy.phase == "lunge":
            enemy.pos += enemy.heading * 680 * dt
            if enemy.attack_clock <= 0:
                enemy.phase, enemy.attack_clock = "recover", 1.1
        elif enemy.phase == "recover" and enemy.attack_clock <= 0:
            enemy.phase, enemy.attack_clock = "hunt", 1.8
    elif enemy.kind == "shooter":
        if enemy.phase == "hunt":
            approach = 1 if distance > 650 else -1 if distance < 450 else 0
            enemy.pos += (toward * approach + toward.rotate(90) * (.7 if enemy.id % 2 else -.7)) * speed * dt
            if enemy.attack_clock <= 0:
                enemy.phase, enemy.attack_clock = "windup", .7
                enemy.heading = toward
        elif enemy.attack_clock <= 0:
            shots = [enemy.heading.rotate(angle) * 510 for angle in (-12, 0, 12)]
            enemy.phase, enemy.attack_clock = "hunt", 2.0
    else:
        # Gold scarabs flee instead of joining the chase.
        enemy.pos -= toward * speed * dt
    enemy.pos.x = max(enemy.radius, min(1680 - enemy.radius, enemy.pos.x))
    enemy.pos.y = max(enemy.radius, min(1680 - enemy.radius, enemy.pos.y))
    return shots
