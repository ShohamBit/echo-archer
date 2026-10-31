"""Read-only staged entrance review frames for player and both bosses."""
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


with tempfile.TemporaryDirectory() as directory:
    app = App(Path(directory) / "unused.json", headless=True, seed=8)
    app.save_allowed = False
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    app.start()
    app.entry_remaining = .45
    app.render()
    pygame.image.save(app.canvas, str(output / "entrance-player.png"))
    for kind in ("boss", "tempest"):
        app.practice_boss = kind
        app.start(practice=True)
        for label, remaining in (("opening", 2.8), ("landed", .6)):
            app.intro_remaining = remaining
            app.render()
            pygame.image.save(app.canvas, str(output / f"entrance-{kind}-{label}.png"))
    pygame.quit()
