"""Authored encounter order and spawn rhythm; boss mechanics live in boss.py."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Encounter:
    title: str
    goal: str
    enemies: tuple[str, ...]
    cadence: float = .30
    pack_size: int = 3
    pack_pause: float = 1.0

    @property
    def boss(self):
        return self.enemies[0] if self.enemies[0] in ("boss", "tempest") else None


CAMPAIGN = (
    Encounter("THE HUNT", "Sidestep hunter lunges. Recall through the pack.",
              ("chaser",) * 6, .35, 2, 1.0),
    Encounter("ARMORED FLANK", "Let guards commit, then punish their recovery.",
              ("chaser", "chaser", "tank", "chaser", "chaser", "tank", "chaser", "tank"), .35, 3, 1.1),
    Encounter("CROSSFIRE", "Casters lock their aim. Move after the warning.",
              ("shooter", "chaser", "chaser", "shooter", "chaser", "tank", "shooter", "chaser", "chaser", "shooter")),
    Encounter("THE WARDEN", "Dodge the charge. Hit the exposed rear core.", ("boss",)),
    Encounter("AFTERSHOCK", "Regain your rhythm before the final climb.",
              ("chaser", "chaser", "tank", "chaser", "chaser", "shooter", "chaser", "chaser"), .35, 2, 1.15),
    Encounter("HUNTERS' GAUNTLET", "Keep an escape lane between rushes and volleys.",
              ("chaser", "tank", "chaser", "shooter") * 3, .25, 3, .9),
    Encounter("EYE OF THE STORM", "Read the windups. Set up multi-kills through the crowd.",
              ("shooter", "chaser", "tank", "chaser", "shooter", "tank", "chaser") * 2, .25, 3, .8),
    Encounter("THE TEMPEST", "Escape the spiral. Leave the blink mark, then strike the eye.", ("tempest",)),
)
FINAL_BOSS = CAMPAIGN[-1].boss


def boss_wave(kind):
    return next(i for i, encounter in enumerate(CAMPAIGN, 1) if encounter.boss == kind)
