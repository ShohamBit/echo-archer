"""Stage campaign pacing review frames without reading or writing real progress."""
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


with tempfile.TemporaryDirectory() as directory:
    app = App(Path(directory) / "unused.json", headless=True, seed=8)
    app.save_allowed = False
    app.start()
    app.entry_remaining = 0
    app.run.wave = 2
    app.run.start_wave()
    app.run.player = pygame.Vector2(840, 1100)
    app.run.invulnerable = 0
    app.run.time_left = 9
    for i, (kind, position) in enumerate((("shooter", (450, 420)), ("chaser", (800, 550)),
                                         ("tank", (1200, 700)), ("shooter", (1200, 350)))):
        enemy = Enemy(i + 1, pygame.Vector2(position), kind=kind, radius=100 if kind == "tank" else 75)
        enemy.heading = (app.run.player - enemy.pos).normalize()
        app.run.enemies.append(enemy)
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    app.render()
    pygame.image.save(app.canvas, str(output / "campaign-crossfire.png"))
    app.run.enemies.clear()
    app.run.spawn_queue.clear()
    app.run.intermission = 1.6
    app.render()
    pygame.image.save(app.canvas, str(output / "campaign-regroup.png"))
    app.practice_boss = "tempest"
    app.start(practice=True)
    app.intro_remaining = 0
    app.run.finish("Boss practice cleared", True)
    app.bank()
    app.scene = "result"
    app.render()
    pygame.image.save(app.canvas, str(output / "campaign-practice-cleared.png"))
    pygame.quit()
