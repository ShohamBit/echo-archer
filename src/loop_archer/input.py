from dataclasses import dataclass, field

from loop_archer.models import Vec2


@dataclass
class InputState:
    move: Vec2 = field(default_factory=Vec2)
    aim_world: Vec2 = field(default_factory=lambda: Vec2(1, 0))
    shoot: bool = False
    dash: bool = False
