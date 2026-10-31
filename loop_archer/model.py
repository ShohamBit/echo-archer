"""Combat simulation. Rendering and input handling live in app.py.

Positions and speeds use Unreal world units; rendering scales a 1680-unit square.
update accepts seconds. Pass a seeded Random
for reproducible balance experiments and tests.
"""
from dataclasses import dataclass, field
import math
import random
from pygame import Vector2 as Vec
from .progression import Progress
from .boss import Warden, Tempest
from .enemy_ai import update_enemy

WIDTH, HEIGHT = 1680, 1680
PLAYER_RADIUS = 60
ARROW_RADIUS = 35
PICKUP_RADIUS = 135
PORTAL_MARGIN = 65
PORTAL_SHIFT = 1400


@dataclass
class Enemy:
    id: int
    pos: Vec
    kind: str = "chaser"
    hp: float = 1
    speed: float = 190
    radius: float = 75
    shot_timer: float = 2
    slow: float = 0
    flash: float = 0
    warden: Warden | None = None
    phase: str = "hunt"
    attack_clock: float = 1.0
    heading: Vec = field(default_factory=lambda: Vec(0, 1))

    def __post_init__(self):
        if self.kind == "boss" and self.warden is None:
            self.warden = Warden()
        elif self.kind == "tempest" and self.warden is None:
            self.warden = Tempest()


@dataclass
class Arrow:
    pos: Vec
    velocity: Vec
    damage: float
    full: bool = False
    state: str = "flying"
    age: float = 0
    bounces: int = 0
    hit: set[int] = field(default_factory=set)
    return_hit: set[int] = field(default_factory=set)
    return_distance: float = 0
    launch_speed: float = 0
    decay_ticks: int = 0
    portal_cooldown: float = 0
    portal_wraps: int = 0

    def __post_init__(self):
        if not self.launch_speed:
            self.launch_speed = self.velocity.length() + 250


@dataclass
class Bullet:
    pos: Vec
    velocity: Vec


@dataclass
class Particle:
    pos: Vec
    velocity: Vec
    life: float
    color: tuple[int, int, int]


def segment_hits(start: Vec, end: Vec, center: Vec, radius: float) -> bool:
    """Swept circle test prevents fast arrows tunnelling between frames."""
    delta = end - start
    t = max(0, min(1, (center - start).dot(delta) / delta.length_squared())) if delta else 0
    return (start + delta * t).distance_squared_to(center) <= radius * radius


class Run:
    def __init__(self, progress: Progress, rng: random.Random | None = None, endless: bool = False, original: bool = False):
        self.rng = rng or random.Random()
        self.levels = progress.equipped_levels()
        self.endless = endless
        self.original = original
        self.player = Vec(WIDTH / 2, HEIGHT / 2)
        self.aim = Vec(1, 0)
        self.max_time = 10 + self.level("time") * 3
        self.time_left = float(self.max_time)
        self.elapsed = 0.0
        self.charge = 0.0
        self.charging = False
        self.shields = self.level("shield")
        self.invulnerable = 1.0
        self.enemies: list[Enemy] = []
        self.arrows: list[Arrow] = []
        self.bullets: list[Bullet] = []
        self.particles: list[Particle] = []
        self.kills = 0
        self.points = 0
        self.wave = 0
        self.wave_delay = 0.7
        self.spawn_queue: list[str] = []
        self.spawn_timer = 0.0
        self.next_id = 0
        self.over = False
        self.victory = False
        self.boss_defeated = False
        self.reason = ""
        self.banner = "DRAW. RELEASE. RECALL."
        self.banner_time = 2.0
        self.shake = 0.0
        self.passive_clock = 0.0
        self.events: list[str] = []
        self.spawn_stage = -1
        self.original_spawn_clock = .75
        self.original_spawn_count = 0
        self.original_spawn_interval = self.rng.uniform(1.45, 1.5)
        self.original_shooter_threshold = self.rng.randint(9, 10) + self.level("more_enemies")
        self.combo = 0
        self.combo_timer = 0.0
        self.skillshot_bonus = 0
        self.skillshot_counts = {"Portal": 0, "Ricochet": 0, "Recall": 0}
        self.feedback = ""
        self.feedback_time = 0.0
        self.last_bow_state = "ready"
        self.multikill_count = 0
        self.last_kill_time = -100.0
        self.multikill_bonus = 0
        self.best_multikill = 0
        self.multikill_feedback = ""
        self.multikill_feedback_time = 0.0

    def level(self, key: str) -> int:
        return self.levels.get(key, 0)

    @property
    def charge_duration(self) -> float:
        return max(.1, 1.25 - 0.15 * self.level("charge"))

    @property
    def can_shoot(self) -> bool:
        return not self.over and not self.arrows

    @property
    def bow_state(self) -> str:
        if self.charging:
            return "charging"
        if not self.arrows:
            return "ready"
        if any(a.state == "returning" for a in self.arrows):
            return "returning"
        if any(a.state == "stuck" for a in self.arrows):
            return "recallable"
        return "flying"

    @property
    def bow_hint(self) -> str:
        return {"ready": "Ready — hold left mouse", "charging": f"Drawing {self.charge_level}/4 — release to shoot",
                "flying": "Arrow in flight", "recallable": "Hold Space / right mouse to recall",
                "returning": "Returning — keep holding"}[self.bow_state]

    @property
    def charge_level(self) -> int:
        return min(4, 1 + int((self.charge + 1e-8) / (self.charge_duration / 4)))

    def begin_charge(self) -> None:
        if self.can_shoot:
            self.charging = True

    def release(self) -> None:
        if self.over or not self.charging or self.arrows:
            return
        level = self.charge_level
        full = level >= 4
        damage = 1 + self.level("damage") + (self.level("full_charge") if full else 0)
        count = 1 + self.level("multishot")
        speed = (1000, 1500, 2000, 2750)[level - 1] + 250 * self.level("speed")
        for i in range(count):
            direction = self.aim.rotate((i - (count - 1) / 2) * 20)
            self.arrows.append(Arrow(self.player + direction * 155, direction * speed, damage, full))
        self.events.append("shoot")
        self.charge = 0
        self.charging = False

    def recall(self) -> None:
        if self.over:
            return
        found = False
        for arrow in self.arrows:
            if arrow.state == "stuck":
                arrow.state = "returning"
                arrow.return_hit.clear()
                arrow.return_distance = arrow.pos.distance_to(self.player)
                delta = self.player - arrow.pos
                arrow.velocity = Vec()
                arrow.age = 0
                found = True
        if found:
            self.events.append("recall")
            self.banner, self.banner_time = "RECALL", 0.6

    def stop_recall(self) -> None:
        for arrow in self.arrows:
            if arrow.state == "returning":
                arrow.state = "stuck"
                arrow.velocity = Vec()
                arrow.return_hit.clear()

    def burst(self, pos: Vec, color=(255, 92, 101), count=10):
        for _ in range(count):
            self.particles.append(Particle(Vec(pos), Vec(self.rng.uniform(-180, 180),
                                                       self.rng.uniform(-180, 180)),
                                           self.rng.uniform(0.2, 0.6), color))

    def finish(self, reason: str, victory: bool = False):
        if self.over:
            return
        self.over, self.victory, self.reason = True, victory, reason
        self.events.append("win" if victory else "death")
        self.burst(self.player, (226, 244, 243), 35)

    def hurt(self, reason: str):
        if self.invulnerable > 0 or self.over:
            return
        self.shake = 10
        if self.shields:
            self.shields -= 1
            self.invulnerable = 1.5
            self.events.append("shield")
            self.burst(self.player, (122, 220, 222), 20)
        else:
            self.finish(reason)

    def spawn(self, kind: str):
        side = self.rng.randrange(4)
        pos = (Vec(20, self.rng.uniform(30, HEIGHT - 30)) if side == 0 else
               Vec(WIDTH - 20, self.rng.uniform(30, HEIGHT - 30)) if side == 1 else
               Vec(self.rng.uniform(30, WIDTH - 30), 20) if side == 2 else
               Vec(self.rng.uniform(30, WIDTH - 30), HEIGHT - 20))
        if self.original:
            angle = self.rng.uniform(0, math.tau)
            pos = Vec(WIDTH / 2, HEIGHT / 2) + Vec(math.cos(angle), math.sin(angle)) * 850
        hp = 2 + (self.wave - 1) // 3
        radius, speed = 75, 190 if self.original else 190 + (self.wave - 1) * 5
        if self.original:
            hp = 2
        if kind == "tank":
            hp = 4 + (self.wave - 1) // 3
            radius, speed = 100, 150
            if self.original:
                hp = 4
        elif kind == "shooter":
            hp, radius, speed = (5 if self.original else 5 + (self.wave - 1) // 3), 75, 125
        elif kind == "nugget":
            hp, radius, speed = 5, 65, 70
        elif kind in ("boss", "tempest"):
            hp, radius, speed = (Warden.MAX_HEALTH if kind == "boss" else Tempest.MAX_HEALTH), 140, 0
            pos = Vec(WIDTH / 2, HEIGHT * .30)
            self.max_time = max(30, self.max_time)
            self.time_left = self.max_time
            self.bullets.clear()
            self.feedback, self.feedback_time = "Boss encounter — clock restored", 2.5
        self.next_id += 1
        self.enemies.append(Enemy(self.next_id, pos, kind, hp, speed, radius))

    def start_wave(self):
        self.wave += 1
        if self.wave == 8 and not self.endless:
            # Let the finale teach its own pattern without unrelated shooters
            # obscuring the telegraphs and rear-core opportunity.
            self.spawn_queue = ["boss"]
        elif self.wave == 4 and not self.endless:
            self.spawn_queue = ["tempest"]
        else:
            self.spawn_queue = ["shooter" if self.wave >= 3 and i % 5 == 4 else
                                "tank" if self.wave >= 2 and i % 4 == 3 else "chaser"
                                for i in range(4 + self.wave * 2 + self.level("more_enemies"))]
            for i, kind in enumerate(self.spawn_queue):
                if kind == "chaser" and self.rng.random() < .025 * self.level("nugget"):
                    self.spawn_queue[i] = "nugget"
        self.banner = "THE LOOP / FINAL WAVE" if self.wave == 8 and not self.endless else f"WAVE {self.wave:02}"
        self.banner_time = 1.8
        self.spawn_timer = 0

    def update(self, dt: float, movement=(0, 0), aim=None):
        if dt <= 0 or self.over:
            return
        # Bounded substeps keep wall and collision behavior stable during frame stalls.
        remaining = min(dt, 0.25)
        while remaining > 1e-8 and not self.over:
            step = min(remaining, 1 / 120)
            self._step(step, movement, aim)
            remaining -= step

    def _step(self, dt, movement, aim):
        self.elapsed += dt
        self.time_left -= dt
        self.invulnerable = max(0, self.invulnerable - dt)
        self.shake = max(0, self.shake - dt * 32)
        self.banner_time = max(0, self.banner_time - dt)
        self.feedback_time = max(0, self.feedback_time - dt)
        self.multikill_feedback_time = max(0, self.multikill_feedback_time - dt)
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer == 0:
            self.combo = 0
        if self.time_left <= 0:
            self.time_left = 0
            self.finish("Time ran out")
            return
        direction = Vec(movement)
        if direction.length_squared() > 1:
            direction = direction.normalize()
        movement_speed = 500 + 25 * self.level("movement")
        if any(a.state == "returning" for a in self.arrows):
            movement_speed /= 5
        elif self.charging:
            movement_speed *= 1 - .5 * min(1, self.charge / self.charge_duration)
        self.player += direction * movement_speed * dt
        self.player.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, self.player.x))
        self.player.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, self.player.y))
        if aim is not None and Vec(aim).distance_squared_to(self.player) > 1:
            self.aim = (Vec(aim) - self.player).normalize()
        if self.charging:
            old_tier = self.charge_level
            self.charge += dt
            if old_tier < 4 and self.charge_level == 4:
                self.events.append("charged")
            if self.charge >= 4:
                self.release()
        self.passive_clock += dt
        if self.passive_clock >= 3:
            self.passive_clock -= 3
            self.points += self.level("passive")
        if self.original:
            self._original_spawning(dt)
        elif not self.enemies and not self.spawn_queue:
            self.wave_delay -= dt
            if self.wave_delay <= 0:
                if self.wave >= 8 and not self.endless:
                    if self.boss_defeated:
                        self.points += 30
                        self.finish("Final encounter cleared", True)
                        return
                    # Even an unusual empty final-wave state cannot bypass the boss.
                    self.spawn("boss")
                else:
                    self.start_wave()
        if self.spawn_queue:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn(self.spawn_queue.pop(0))
                self.spawn_timer = 0.25
                self.wave_delay = 1.3
        for enemy in self.enemies:
            enemy.flash = max(0, enemy.flash - dt)
            if enemy.warden:
                enemy.warden.enraged = enemy.hp <= enemy.warden.MAX_HEALTH / 2
                for position, velocity in enemy.warden.update(dt, enemy.pos, self.player, (WIDTH, HEIGHT), enemy.radius):
                    self.bullets.append(Bullet(position, velocity))
            else:
                for velocity in update_enemy(enemy, self.player, dt):
                    self.bullets.append(Bullet(Vec(enemy.pos) + velocity.normalize() * (enemy.radius + 22), velocity))
            if enemy.pos.distance_to(self.player) < enemy.radius + PLAYER_RADIUS:
                self.hurt("An enemy caught you")
        for bullet in self.bullets[:]:
            old = Vec(bullet.pos)
            bullet.pos += bullet.velocity * dt
            if segment_hits(old, bullet.pos, self.player, PLAYER_RADIUS + 15):
                self.bullets.remove(bullet)
                self.hurt("Hit by an enemy projectile")
            elif not (-20 < bullet.pos.x < WIDTH + 20 and -20 < bullet.pos.y < HEIGHT + 20):
                self.bullets.remove(bullet)
        self._arrows(dt)
        state = self.bow_state
        if state != self.last_bow_state and state in ("ready", "recallable"):
            self.events.append("ready" if state == "ready" else "recallable")
        self.last_bow_state = state
        for particle in self.particles[:]:
            particle.pos += particle.velocity * dt
            particle.velocity *= max(0, 1 - dt * 4)
            particle.life -= dt
            if particle.life <= 0:
                self.particles.remove(particle)

    def _arrows(self, dt):
        for arrow in self.arrows[:]:
            arrow.age += dt
            arrow.portal_cooldown = max(0, arrow.portal_cooldown - dt)
            if arrow.state == "stuck":
                if arrow.pos.distance_to(self.player) <= PICKUP_RADIUS:
                    self.arrows.remove(arrow)
                    self.events.append("pickup")
                continue
            old = Vec(arrow.pos)
            returning = arrow.state == "returning"
            if returning:
                # Blueprint VInterpTo uses a timeline value as DeltaTime. Preserve
                # its 60 Hz feel while making the Python integration frame independent.
                curve = arrow.age / .35 * .1 if arrow.age < .35 else min(1, .1 + (arrow.age - .35) / .65 * .9)
                fraction = 1 - (1 - .15 * curve) ** (dt * 60)
                delta = self.player - arrow.pos
                arrow.velocity = delta * fraction / dt
                arrow.pos += delta * fraction
            else:
                # DecreaseSpeed runs every 0.1 seconds, lowering the speed cap by250.
                ticks = int((arrow.age + 1e-8) / .1)
                arrow.decay_ticks = ticks
                speed_cap = max(0, arrow.launch_speed - ticks * 250)
                if arrow.velocity.length() > speed_cap:
                    arrow.velocity.scale_to_length(speed_cap) if speed_cap else arrow.velocity.update(0, 0)
                if speed_cap <= 300:
                    arrow.state = "stuck"
                    arrow.hit.clear()
                    continue
                arrow.pos += arrow.velocity * dt
            if not returning:
                if arrow.portal_cooldown == 0 and (arrow.pos.x < PORTAL_MARGIN or arrow.pos.x > WIDTH - PORTAL_MARGIN):
                    arrow.pos.x += PORTAL_SHIFT if arrow.pos.x < PORTAL_MARGIN else -PORTAL_SHIFT
                    arrow.portal_cooldown = .25
                    arrow.portal_wraps += 1
                    arrow.hit.clear()
                    old = Vec(arrow.pos)  # A teleport is not a sweep through every enemy.
                    self.events.append("recall")
                if arrow.pos.y < 4 or arrow.pos.y > HEIGHT - 4:
                    arrow.pos.y = max(4, min(HEIGHT - 4, arrow.pos.y))
                    arrow.velocity.y *= -1
                    arrow.bounces += 1
                    arrow.hit.clear()
            hit_set = arrow.return_hit if returning else arrow.hit
            travel = arrow.pos - old
            # Resolve a nonpiercing shot against the closest crossed target first.
            candidates = sorted(self.enemies, key=lambda enemy: (enemy.pos - old).dot(travel))
            for enemy in candidates:
                if enemy.id in hit_set or not segment_hits(old, arrow.pos, enemy.pos, enemy.radius + ARROW_RADIUS):
                    continue
                hit_set.add(enemy.id)
                damage = (1 + self.level("recall")) if returning else arrow.damage + (self.level("bounce") if arrow.bounces else 0)
                if enemy.warden:
                    core = enemy.warden.core_position(enemy.pos, enemy.radius)
                    if not enemy.warden.rear_hit(arrow.velocity) or not segment_hits(old, arrow.pos, core, 55 + ARROW_RADIUS):
                        self.feedback, self.feedback_time = ("Armor — wait for the open eye" if enemy.kind == "tempest" else "Armor — aim for the exposed rear core"), 1.1
                        self.events.append("armor")
                        if not returning:
                            normal = old - enemy.pos
                            if normal:
                                arrow.velocity = arrow.velocity.reflect(normal.normalize())
                        continue
                    damage = enemy.warden.core_damage(damage)
                    self.time_left = min(self.max_time, self.time_left + 3)
                    self.feedback, self.feedback_time = f"CORE HIT  +{round(damage)} damage", 1.3
                    self.events.append("core")
                enemy.hp -= damage
                enemy.slow = 30 * self.level("slow")
                enemy.flash = 0.12
                self.burst(enemy.pos, count=4)
                self.events.append("hit")
                if enemy.hp <= 0:
                    self.enemies.remove(enemy)
                    if enemy.kind == "boss":
                        self.boss_defeated = True
                    self.kills += 1
                    base_points = {"tank": 2, "shooter": 5, "nugget": 10, "boss": 20, "tempest": 20}.get(enemy.kind, 1)
                    self.points += base_points + self.level("reward") + (self.level("recall_reward") if returning else 0)
                    self._reward_skillshot(arrow, returning)
                    self._reward_multikill()
                    time_gain = {"tank": .7, "shooter": .6}.get(enemy.kind, .5)
                    self.time_left = min(self.max_time, self.time_left + time_gain + 0.3 * self.level("time_kill"))
                    self.burst(enemy.pos)
                    self.shake = 3
                    self.events.append("kill")
            if returning and segment_hits(old, arrow.pos, self.player, PICKUP_RADIUS):
                self.arrows.remove(arrow)
                self.events.append("pickup")
            elif not returning and arrow.age > .1 and not self.level("safe") and segment_hits(old, arrow.pos, self.player, PLAYER_RADIUS + ARROW_RADIUS):
                self.hurt("Your flying arrow hit you")

    def _reward_multikill(self):
        # Kills within 0.4 seconds form one burst, independent of frame rate.
        self.multikill_count = self.multikill_count + 1 if self.elapsed - self.last_kill_time <= .4 else 1
        self.last_kill_time = self.elapsed
        self.best_multikill = max(self.best_multikill, self.multikill_count)
        if self.multikill_count < 2:
            return
        bonus = min(5, self.multikill_count)
        self.points += bonus
        self.multikill_bonus += bonus
        self.multikill_feedback = f"MULTI-KILL x{self.multikill_count}   +{bonus} POINTS"
        self.multikill_feedback_time = 2
        self.events.append("skillshot")

    def _reward_skillshot(self, arrow, returning):
        tags = (["Portal"] if arrow.portal_wraps else []) + (["Ricochet"] if arrow.bounces else []) + (["Recall"] if returning else [])
        if not tags:
            self.combo, self.combo_timer = 0, 0
            return
        self.combo = self.combo + 1 if self.combo_timer > 0 else 1
        self.combo_timer = 3.0
        bonus = len(tags) + min(2, (self.combo - 1) // 2)
        self.points += bonus
        self.skillshot_bonus += bonus
        for tag in tags:
            self.skillshot_counts[tag] += 1
        self.feedback = f"{' + '.join(tags)}  /  chain {self.combo}  /  +{bonus} points"
        self.feedback_time = 1.8
        self.events.append("skillshot")

    def _original_spawning(self, dt):
        """WaveManager count-based pools; live enemies need not be cleared."""
        # Survival continues regardless of how many enemies have spawned.
        rank = self.level("more_enemies")
        stage = 2 if self.original_spawn_count >= self.original_shooter_threshold else 1 if self.original_spawn_count >= 3 + rank else 0
        if self.spawn_stage < 0:
            self.spawn_stage, self.wave = 0, 1
        elif stage != self.spawn_stage:
            self.spawn_stage, self.wave = stage, stage + 1
            self.original_spawn_interval = self.rng.uniform(2, 2.25) if stage == 1 else self.rng.uniform(3.5, 4)
            self.original_spawn_clock = max(.15, self.original_spawn_interval - rank * .5)
        self.original_spawn_clock -= dt
        if self.original_spawn_clock <= 0:
            if self.rng.random() < .05 + .02 * self.level("nugget"):
                self.spawn("nugget")
            else:
                self.spawn(("chaser", "tank", "shooter")[stage])
                self.original_spawn_count += 1
            # Avoid the shipped timer becoming non-positive at high upgrade ranks.
            self.original_spawn_clock = max(.15, self.original_spawn_interval - rank * .5)


def bank_run(progress: Progress, run: Run) -> None:
    """Called exactly once by the app when a run ends."""
    progress.points += run.points
    progress.loops += 1
    progress.best_wave = max(progress.best_wave, run.wave)
    progress.best_kills = max(progress.best_kills, run.kills)
