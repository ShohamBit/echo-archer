"""Read-only staged review frames for the encounter expansion."""
import os
from pathlib import Path
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from loop_archer.app import App
from loop_archer.model import Enemy
from loop_archer.progression import BY_KEY, Progress


with tempfile.TemporaryDirectory() as directory:
    app = App(Path(directory) / "unused.json", headless=True, seed=7)
    app.save_allowed = False
    app.progress = Progress(levels={key: value.max_level for key, value in BY_KEY.items()})
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    app.action("loadout")
    app.progress.equip("damage", 2)
    app.progress.equip("multishot", 0)
    app.render()
    pygame.image.save(app.canvas, str(output / "expansion-loadout.png"))
    app.practice_boss = "tempest"
    app.start(practice=True)
    app.intro_remaining = 1.4
    app.animation = 1.8
    app.run.invulnerable = 0
    app.render()
    pygame.image.save(app.canvas, str(output / "expansion-tempest-entry.png"))
    app.intro_remaining = 0
    app.run.enemies[0].warden.phase = "blink"
    app.run.enemies[0].warden.target = pygame.Vector2(1120, 1000)
    app.render()
    pygame.image.save(app.canvas, str(output / "expansion-tempest-blink.png"))
    app.start()
    app.entry_remaining = 0
    app.run.invulnerable = 0
    app.run.wave, app.run.time_left, app.run.max_time = 5, 25, 25
    app.run.player = pygame.Vector2(840, 1050)
    for i, (kind, pos) in enumerate((("chaser", (420, 600)), ("tank", (1100, 600)),
                                    ("shooter", (800, 340)), ("nugget", (1350, 1100)),
                                    ("chaser", (500, 1200)))):
        enemy = Enemy(i + 1, pygame.Vector2(pos), kind=kind, radius=100 if kind == "tank" else 75)
        enemy.heading = (app.run.player - enemy.pos).normalize()
        if kind == "chaser":
            enemy.phase = "windup"
        app.run.enemies.append(enemy)
    app.run.multikill_feedback = "MULTI-KILL x3   +3 POINTS"
    app.run.multikill_feedback_time = 2
    app.run.multikill_bonus = 5
    app.run.best_multikill = 3
    app.render()
    pygame.image.save(app.canvas, str(output / "expansion-creatures.png"))
    pygame.quit()
