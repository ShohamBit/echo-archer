"""Read-only, repeatable CPU rendering benchmark; no frame-rate limiter."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
from time import perf_counter

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pygame
from loop_archer.app import App
from loop_archer.model import Enemy
from loop_archer.progression import BY_KEY, Progress

def measure(frames=60, boss=False):
    with tempfile.TemporaryDirectory() as directory:
        app = App(Path(directory) / "unused.json", headless=True, seed=25)
        app.save_allowed = False
        app.progress = Progress(levels={k: u.max_level for k, u in BY_KEY.items()})
        app.start()
        app.entry_remaining = 0
        app.run.invulnerable = 1000
        app.run.time_left = 1000
        app.run.enemies = [Enemy(i, pygame.Vector2(150 + (i % 6) * 250, 180 + (i // 6) * 260)) for i in range(24)]
        app.run.next_id = 24
        if boss:
            app.run.spawn("boss")
            app.run.wave = 8
        app.run.begin_charge()
        app.run.charge = app.run.charge_duration
        app.run.release()
        for _ in range(5):
            app.render()
        rendering, effects, simulation = [], [], []
        for _ in range(frames):
            start = perf_counter()
            app.render()
            rendering.append((perf_counter() - start) * 1000)
            start = perf_counter()
            app.presentation.apply(app.canvas)
            effects.append((perf_counter() - start) * 1000)
            start = perf_counter()
            app.run.update(1 / 60, aim=(1200, 500))
            simulation.append((perf_counter() - start) * 1000)
        pygame.quit()
    summary = lambda xs: {"mean_ms": round(statistics.mean(xs), 2), "p95_ms": round(sorted(xs)[int(len(xs) * .95) - 1], 2)}
    return {"frames": frames, "boss_stress": boss, "render": summary(rendering), "full_frame_effects": summary(effects), "simulation": summary(simulation)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--boss", action="store_true")
    args = parser.parse_args()
    result = measure(180 if args.boss else 60, boss=args.boss)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
