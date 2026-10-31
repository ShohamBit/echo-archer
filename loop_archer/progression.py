"""Permanent upgrades and versioned, atomic JSON saves. No rendering code."""
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class Upgrade:
    key: str
    name: str
    description: str
    prices: tuple[int, ...]
    column: int
    row: int
    parent: str | None = None

    @property
    def max_level(self) -> int:
        return len(self.prices)


# The placement is a compact UI arrangement. Effects, prices and prerequisites
# come from the packaged SkillTreeMap actors; see analysis/PAK_FINDINGS.md.
UPGRADES = (
    Upgrade("damage", "Sharper arrows", "+1 arrow damage per rank.", (2, 25, 40, 55, 60), 0, 0),
    Upgrade("charge", "Quick draw", "Reduce draw time by 0.15 seconds per rank.", (5, 10, 20, 40, 50), 1, 0, "damage"),
    Upgrade("speed", "Swift arrows", "+250 arrow speed per rank.", (10, 15, 25, 40, 50), 2, 0, "charge"),
    Upgrade("multishot", "Split shot", "+1 arrow in every volley.", (20, 50), 3, 0, "speed"),
    Upgrade("time", "Borrowed time", "+3 seconds at the start of every loop.", (5, 15, 20, 25, 40), 0, 1, "damage"),
    Upgrade("time_kill", "Keep it going", "+0.3 seconds restored per kill.", (10, 15, 20, 25, 40), 1, 1, "time"),
    Upgrade("shield", "Second chance", "+1 shield. A shield absorbs a fatal hit.", (15, 30), 2, 1, "movement"),
    Upgrade("safe", "Friendly fire", "Your flying arrows can no longer hurt you. Recall is always safe.", (25,), 3, 1, "multishot"),
    Upgrade("reward", "Bounty", "+1 point earned from each enemy.", (10, 25), 0, 2, "recall"),
    Upgrade("recall", "Recall force", "+1 returning-arrow damage per rank.", (5, 15, 25, 30, 50), 1, 2, "damage"),
    Upgrade("recall_reward", "Return on investment", "+1 point from a recall kill per rank.", (10, 15, 25), 2, 2, "recall"),
    Upgrade("bounce", "Bank shot", "+1 damage after an arrow hits a wall.", (15, 25, 50, 75), 3, 2, "recall_reward"),
    Upgrade("movement", "Fleet footed", "+25 movement speed per rank.", (5, 10, 20, 25, 40, 75, 90, 100), 0, 3, "damage"),
    Upgrade("full_charge", "Perfect draw", "+1 damage on a fully charged shot.", (15, 25, 35), 1, 3, "speed"),
    Upgrade("slow", "Pin down", "Hits slow enemies by 30 speed per rank.", (10, 15, 25), 2, 3, "movement"),
    Upgrade("passive", "Compound interest", "+1 point every three seconds per rank.", (15, 25, 40), 3, 3, "recall_reward"),
    Upgrade("more_enemies", "More company", "Per rank: +1 enemy per wave in Campaign/Endless; faster spawning in Survival.", (10, 25, 35, 40, 55), 0, 4, "time"),
    Upgrade("nugget", "Golden opportunity", "Gold chance per rank: +2.5% in Campaign/Endless; +2% in Survival (base 5%).", (15, 25, 40), 1, 4, "more_enemies"),
    Upgrade("sale", "Better deals", "All upgrades cost 5 fewer points per rank (minimum 1).", (20, 35), 2, 4, "nugget"),
)
BY_KEY = {u.key: u for u in UPGRADES}


@dataclass
class Progress:
    points: int = 0
    levels: dict[str, int] = field(default_factory=dict)
    loops: int = 0
    best_wave: int = 0
    best_kills: int = 0
    active_levels: dict[str, int] = field(default_factory=dict)

    def equipped_levels(self):
        return {key: min(self.level(key), max(0, self.active_levels.get(key, self.level(key))))
                for key in BY_KEY}

    def equip(self, key, rank):
        if key in BY_KEY:
            self.active_levels[key] = max(0, min(self.level(key), rank))

    def level(self, key: str) -> int:
        return self.levels.get(key, 0)

    def unlocked(self, key: str) -> bool:
        parent = BY_KEY[key].parent
        return parent is None or self.level(parent) > 0

    def cost(self, key: str) -> int:
        prices = BY_KEY[key].prices
        return max(1, prices[min(self.level(key), len(prices) - 1)] - 5 * self.equipped_levels()["sale"])

    def buy(self, key: str) -> bool:
        if key not in BY_KEY or not self.unlocked(key):
            return False
        if self.level(key) >= BY_KEY[key].max_level or self.points < self.cost(key):
            return False
        self.points -= self.cost(key)
        self.levels[key] = self.level(key) + 1
        return True


def save_progress(path: Path, progress: Progress) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "points": progress.points, "levels": progress.levels,
               "loops": progress.loops, "best_wave": progress.best_wave,
               "best_kills": progress.best_kills, "active_levels": progress.active_levels}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_progress(path: Path) -> tuple[Progress, str]:
    if not path.exists():
        return Progress(), ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unsupported save version")
        def integer(key):
            value = data.get(key, 0)
            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid {key}")
            return value
        levels = data.get("levels", {})
        if not isinstance(levels, dict):
            raise ValueError("Invalid upgrade levels")
        clean = {}
        for key, value in levels.items():
            if key in BY_KEY:
                if type(value) is not int or not 0 <= value <= BY_KEY[key].max_level:
                    raise ValueError("Invalid upgrade rank")
                clean[key] = value
        active = data.get("active_levels", {})
        if not isinstance(active, dict):
            raise ValueError("Invalid equipped upgrades")
        equipped = {}
        for key, value in active.items():
            if key in BY_KEY:
                if type(value) is not int or not 0 <= value <= clean.get(key, 0):
                    raise ValueError("Invalid equipped rank")
                equipped[key] = value
        return Progress(integer("points"), clean, integer("loops"),
                        integer("best_wave"), integer("best_kills"), equipped), ""
    except (OSError, ValueError, TypeError):
        # Preserve the original file. The app disables writes until a different save is selected.
        return Progress(), "Save could not be read. Original preserved; saving disabled."
