from __future__ import annotations

import json
from pathlib import Path

from loop_archer.config import SAVE_PATH
from loop_archer.models import GameState, new_game_state


def save_game(state: GameState, path: str | Path = SAVE_PATH) -> None:
    save_path = Path(path)
    payload = {
        "total_shards": state.total_shards,
        "owned_upgrades": sorted(state.owned_upgrades),
        "best_time": state.best_time,
        "current_loop": state.current_loop,
    }
    save_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_game(path: str | Path = SAVE_PATH) -> GameState:
    save_path = Path(path)
    if not save_path.exists():
        return new_game_state()

    payload = json.loads(save_path.read_text(encoding="utf-8"))
    return new_game_state(
        total_shards=int(payload.get("total_shards", 0)),
        owned_upgrades=set(payload.get("owned_upgrades", [])),
        current_loop=max(1, int(payload.get("current_loop", 1))),
        best_time=float(payload.get("best_time", 0.0)),
    )
