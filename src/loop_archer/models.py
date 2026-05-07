from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import cos, hypot, sin

from loop_archer import config


class GameMode(Enum):
    PLAYING = "playing"
    DEAD_SUMMARY = "dead_summary"
    UPGRADE = "upgrade"
    VICTORY_LATER = "victory_later"
    PAUSED = "paused"


class DeathReason(Enum):
    OVERWHELMED = "Overwhelmed"
    ECHO_FADED = "Echo Faded"


class EnemyKind(Enum):
    CHASER = "chaser"
    FAST = "fast"


@dataclass(frozen=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def length(self) -> float:
        return hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        magnitude = self.length()
        if magnitude <= 0.00001:
            return Vec2(0, 0)
        return Vec2(self.x / magnitude, self.y / magnitude)

    def distance_to(self, other: Vec2) -> float:
        return (self - other).length()

    @staticmethod
    def from_angle(angle_radians: float) -> Vec2:
        return Vec2(cos(angle_radians), sin(angle_radians))


@dataclass
class PlayerStats:
    max_hp: int = config.PLAYER_MAX_HP
    speed: float = config.PLAYER_SPEED
    damage: int = config.BASE_DAMAGE
    fire_rate: float = config.BASE_FIRE_RATE
    arrow_speed: float = config.BASE_ARROW_SPEED
    arrow_range: float = config.ARROW_RANGE
    pierce: int = 0
    pickup_radius: float = config.INITIAL_PICKUP_RADIUS
    shard_gain_multiplier: float = 1.0
    invincibility_seconds: float = config.PLAYER_INVINCIBILITY
    echo_decay_multiplier: float = 1.0
    dash_distance: float = config.DASH_DISTANCE
    dash_cooldown: float = config.DASH_COOLDOWN


@dataclass
class Player:
    position: Vec2 = field(default_factory=Vec2)
    hp: float = config.PLAYER_MAX_HP
    radius: float = config.PLAYER_RADIUS
    aim_direction: Vec2 = field(default_factory=lambda: Vec2(1, 0))
    shot_cooldown: float = 0.0
    dash_cooldown_timer: float = 0.0
    dash_flash_timer: float = 0.0
    invincibility_timer: float = 0.0
    hit_flash_timer: float = 0.0


@dataclass
class Arrow:
    id: int
    position: Vec2
    direction: Vec2
    damage: int
    speed: float
    range_remaining: float
    radius: float = config.ARROW_RADIUS
    pierce_remaining: int = 0


@dataclass
class Enemy:
    id: int
    position: Vec2
    kind: EnemyKind = EnemyKind.CHASER
    hp: int = config.CHASER_HP
    speed: float = config.CHASER_SPEED
    damage: int = config.CHASER_DAMAGE
    reward: int = config.CHASER_REWARD
    radius: float = config.ENEMY_RADIUS
    hit_flash_timer: float = 0.0


@dataclass
class Pickup:
    id: int
    position: Vec2
    value: int
    radius: float = config.PICKUP_RADIUS


@dataclass
class RunSummary:
    time_survived: float = 0.0
    enemies_defeated: int = 0
    shards_gained: int = 0
    death_reason: DeathReason | None = None


@dataclass
class UpgradeDefinition:
    id: str
    name: str
    branch: str
    cost: int
    description: str
    prerequisites: tuple[str, ...] = ()
    damage_multiplier: float = 1.0
    max_hp_bonus: int = 0
    fire_rate_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    arrow_speed_multiplier: float = 1.0
    arrow_range_multiplier: float = 1.0
    pickup_radius_multiplier: float = 1.0
    shard_gain_multiplier: float = 1.0
    echo_decay_multiplier: float = 1.0
    dash_cooldown_multiplier: float = 1.0
    pierce_bonus: int = 0


@dataclass
class GameState:
    current_loop: int = 1
    mode: GameMode = GameMode.PLAYING
    arena_radius: float = config.ARENA_RADIUS
    player_stats: PlayerStats = field(default_factory=PlayerStats)
    player: Player = field(default_factory=Player)
    enemies: list[Enemy] = field(default_factory=list)
    arrows: list[Arrow] = field(default_factory=list)
    pickups: list[Pickup] = field(default_factory=list)
    run_timer: float = 0.0
    next_spawn_time: float = 0.5
    spawn_count: int = 0
    total_shards: int = 0
    run_shards: int = 0
    owned_upgrades: set[str] = field(default_factory=set)
    best_time: float = 0.0
    kills: int = 0
    last_run_summary: RunSummary = field(default_factory=RunSummary)
    pending_death_reason: DeathReason | None = None
    next_entity_id: int = 1

    def next_id(self) -> int:
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        return entity_id


def clamp_to_arena(position: Vec2, arena_radius: float = config.ARENA_RADIUS) -> Vec2:
    distance = position.length()
    max_distance = arena_radius - config.PLAYER_RADIUS
    if distance <= max_distance:
        return position
    return position.normalized() * max_distance


def build_player_stats(owned_upgrades: set[str] | None = None) -> PlayerStats:
    from loop_archer.upgrades import UPGRADE_DEFINITIONS

    stats = PlayerStats()
    damage_multiplier = 1.0
    fire_rate_multiplier = 1.0
    speed_multiplier = 1.0
    arrow_speed_multiplier = 1.0
    arrow_range_multiplier = 1.0
    pickup_radius_multiplier = 1.0
    shard_gain_multiplier = 1.0
    echo_decay_multiplier = 1.0
    dash_cooldown_multiplier = 1.0
    max_hp_bonus = 0
    pierce_bonus = 0

    for upgrade_id in sorted(owned_upgrades or set()):
        definition = UPGRADE_DEFINITIONS.get(upgrade_id)
        if definition is None:
            continue
        damage_multiplier *= definition.damage_multiplier
        fire_rate_multiplier *= definition.fire_rate_multiplier
        speed_multiplier *= definition.speed_multiplier
        arrow_speed_multiplier *= definition.arrow_speed_multiplier
        arrow_range_multiplier *= definition.arrow_range_multiplier
        pickup_radius_multiplier *= definition.pickup_radius_multiplier
        shard_gain_multiplier *= definition.shard_gain_multiplier
        echo_decay_multiplier *= definition.echo_decay_multiplier
        dash_cooldown_multiplier *= definition.dash_cooldown_multiplier
        max_hp_bonus += definition.max_hp_bonus
        pierce_bonus += definition.pierce_bonus

    stats.damage = round(stats.damage * damage_multiplier)
    stats.fire_rate = round(stats.fire_rate * fire_rate_multiplier, 3)
    stats.speed = round(stats.speed * speed_multiplier, 3)
    stats.arrow_speed = round(stats.arrow_speed * arrow_speed_multiplier, 3)
    stats.arrow_range = round(stats.arrow_range * arrow_range_multiplier, 3)
    stats.pickup_radius = round(stats.pickup_radius * pickup_radius_multiplier, 3)
    stats.shard_gain_multiplier = round(
        stats.shard_gain_multiplier * shard_gain_multiplier,
        3,
    )
    stats.echo_decay_multiplier = round(
        stats.echo_decay_multiplier * echo_decay_multiplier,
        3,
    )
    stats.dash_cooldown = round(stats.dash_cooldown * dash_cooldown_multiplier, 3)
    stats.max_hp += max_hp_bonus
    stats.pierce += pierce_bonus
    return stats


def new_game_state(
    total_shards: int = 0,
    owned_upgrades: set[str] | None = None,
    current_loop: int = 1,
    best_time: float = 0.0,
) -> GameState:
    upgrades = set(owned_upgrades or set())
    stats = build_player_stats(upgrades)
    return GameState(
        current_loop=current_loop,
        player_stats=stats,
        player=Player(hp=stats.max_hp),
        total_shards=total_shards,
        owned_upgrades=upgrades,
        best_time=best_time,
    )
