"""Read-only review frames for the Warden and bow-state presentation."""
import os
from pathlib import Path
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pygame
from pygame import Vector2 as Vec
from loop_archer.app import App
from loop_archer.model import Arrow
from loop_archer.progression import Progress

if __name__ == "__main__":
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        app = App(Path(directory) / "unused.json", headless=True, seed=4)
        app.save_allowed = False
        app.progress = Progress(levels={"damage": 2, "time": 2, "shield": 1})
        app.start(practice=True)
        app.run.invulnerable = 0
        boss = app.run.enemies[0]
        for phase in ("dash_windup", "exposed"):
            boss.pos = Vec(840, 900 if phase == "exposed" else 450)
            boss.warden.phase = phase
            boss.warden.timer = 1.0 if phase == "dash_windup" else 2.6
            boss.warden.heading = Vec(0, 1)
            boss.warden.target = Vec(840, 1200)
            app.run.player = Vec(1100, 1180) if phase == "dash_windup" else Vec(620, 600)
            app.run.aim = (boss.pos - app.run.player).normalize()
            app.run.arrows = [Arrow(Vec(840, 650), Vec(0, 900), 3, bounces=1, portal_wraps=1)] if phase == "exposed" else []
            app.mouse = (640, 420)
            app.render()
            pygame.image.save(app.canvas, str(output / f"warden-{phase}.png"))
        pygame.quit()
    print("Rendered review frames using a temporary profile; player save untouched.")
