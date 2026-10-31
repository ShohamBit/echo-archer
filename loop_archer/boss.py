"""Warden armor/charge and Tempest spiral/blink encounters.

Uses geometry only; no window, sound, save or input dependencies.
"""
from dataclasses import dataclass, field
from pygame import Vector2 as Vec


@dataclass
class Warden:
    phase: str = "fan_windup"
    timer: float = 1.1
    heading: Vec = field(default_factory=lambda: Vec(0, 1))
    target: Vec | None = None
    core_budget: float = 12
    cycles: int = 0
    enraged: bool = False

    NAME = "THE WARDEN"
    MAX_HEALTH = 48
    CORE_BUDGET = 12
    DURATIONS = {"fan_windup": 1.1, "fan_recovery": .6, "dash_windup": 1.1,
                 "dash": .5, "exposed": 1.65}

    @property
    def exposed(self):
        return self.phase == "exposed" and self.core_budget > 0

    @property
    def hint(self):
        return {"fan_windup": "Volley incoming — move between the lanes",
                "fan_recovery": "Prepare to sidestep the charge",
                "dash_windup": "Charge locked — leave the marked lane",
                "dash": "Get behind the Warden",
                "exposed": "Hit the glowing rear core" if self.exposed else "Core sealed — prepare for the next attack"}[self.phase]

    def core_position(self, position, radius):
        return position - self.heading * radius * .72

    def rear_hit(self, velocity):
        return self.exposed and bool(velocity) and velocity.normalize().dot(self.heading) > .2

    def core_damage(self, arrow_damage):
        """Reward a precise hit; a maxed volley cannot skip the whole encounter."""
        if not self.exposed:
            return 0
        amount = min(self.core_budget, arrow_damage * 3)
        self.core_budget -= amount
        return amount

    def _enter(self, phase, position, player):
        self.phase, self.timer = phase, self.DURATIONS[phase]
        if phase in ("fan_windup", "dash_windup"):
            self.target = Vec(player)
            delta = self.target - position
            self.heading = delta.normalize() if delta else Vec(0, 1)
        elif phase == "exposed":
            self.core_budget = self.CORE_BUDGET
            self.cycles += 1

    def update(self, dt, position, player, bounds, radius):
        if self.target is None:
            self.target = Vec(player)
            delta = self.target - position
            self.heading = delta.normalize() if delta else Vec(0, 1)
        shots = []
        if self.phase == "dash":
            position += self.heading * (2300 if self.enraged else 2000) * dt
            position.x = max(radius, min(bounds[0] - radius, position.x))
            position.y = max(radius, min(bounds[1] - radius, position.y))
        self.timer -= dt * (1.3 if self.enraged and self.phase != "dash" else 1)
        if self.timer > 0:
            return shots
        if self.phase == "fan_windup":
            for angle in (range(-48, 49, 12) if self.enraged else (-24, -12, 0, 12, 24)):
                direction = self.heading.rotate(angle)
                shots.append((position + direction * (radius + 22), direction * (680 if self.enraged else 550)))
            self._enter("fan_recovery", position, player)
        elif self.phase == "fan_recovery":
            self._enter("dash_windup", position, player)
        elif self.phase == "dash_windup":
            self._enter("dash", position, player)
        elif self.phase == "dash":
            self._enter("exposed", position, player)
        else:
            if self.enraged:
                for angle in range(0, 360, 30):
                    direction = Vec(1, 0).rotate(angle + self.cycles * 13)
                    shots.append((position + direction * (radius + 22), direction * 380))
            self._enter("fan_windup", position, player)
        return shots


@dataclass
class Tempest:
    """A mobile spiral caster: escape the spiral, then punish the marked blink."""
    phase: str = "spiral"
    timer: float = 3.2
    heading: Vec = field(default_factory=lambda: Vec(0, 1))
    target: Vec | None = None
    core_budget: float = 8
    cycles: int = 0
    enraged: bool = False
    shot_clock: float = 0
    angle: float = 0

    NAME = "THE TEMPEST"
    MAX_HEALTH = 32
    CORE_BUDGET = 8

    @property
    def exposed(self):
        return self.phase == "exposed" and self.core_budget > 0

    @property
    def hint(self):
        return {"spiral": "Weave through the rotating spiral",
                "blink": "Blink incoming — leave the violet mark",
                "exposed": "Strike the open eye" if self.exposed else "Eye sealed — keep moving"}[self.phase]

    def core_position(self, position, radius):
        return Vec(position)

    def rear_hit(self, velocity):
        return self.exposed

    def core_damage(self, damage):
        amount = min(self.core_budget, damage * 3) if self.exposed else 0
        self.core_budget -= amount
        return amount

    def update(self, dt, position, player, bounds, radius):
        shots = []
        self.timer -= dt
        if self.phase == "spiral":
            self.angle += dt * (145 if self.enraged else 105)
            self.shot_clock -= dt
            if self.shot_clock <= 0:
                self.shot_clock += .15 if self.enraged else .21
                for offset in (0, 120, 240):
                    direction = Vec(1, 0).rotate(self.angle + offset)
                    shots.append((position + direction * (radius + 25), direction * 440))
        if self.timer > 0:
            return shots
        if self.phase == "spiral":
            self.phase, self.timer = "blink", 1.0
            self.target = Vec(max(radius, min(bounds[0] - radius, player.x)),
                              max(radius, min(bounds[1] - radius, player.y)))
        elif self.phase == "blink":
            position.update(self.target)
            self.phase, self.timer = "exposed", 1.8 if self.enraged else 2.2
            self.core_budget = self.CORE_BUDGET
            for angle in range(0, 360, 45):
                direction = Vec(1, 0).rotate(angle + self.cycles * 17)
                shots.append((position + direction * (radius + 25), direction * 330))
        else:
            self.phase, self.timer = "spiral", 3.2
            self.cycles += 1
        return shots
