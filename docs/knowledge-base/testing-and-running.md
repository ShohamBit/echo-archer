# Testing and Running

## Environment

Use the local virtual environment created in the project root.

Install dependencies if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

## Run the Game

```powershell
.\.venv\Scripts\python.exe -m loop_archer
```

or:

```powershell
.\.venv\Scripts\loop-archer.exe
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Current coverage focuses on:

- arrow/enemy combat
- shard pickups
- death banking and loop reset
- Echo Decay behavior and death reason
- upgrade purchase validation and stat application
- persistence
- enemy separation
- layout helpers for arena and HP bar

## Pygame Smoke Checks

Use dummy SDL drivers when verifying rendering without opening a window:

```powershell
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
.\.venv\Scripts\python.exe -c "from loop_archer.main import GameApp; import pygame; app = GameApp(); app._draw(); pygame.quit(); print('pygame smoke ok')"
```

For UI features that affect fullscreen toggling:

```powershell
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
.\.venv\Scripts\python.exe -c "from loop_archer.main import GameApp; import pygame; app = GameApp(); app._draw(); app._toggle_fullscreen(); app._draw(); pygame.quit(); print('pygame fullscreen smoke ok')"
```

## Verification Rule

Before every feature commit, run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

For rendering or UI changes, also run an appropriate pygame smoke check.
