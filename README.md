# Echo Archer MVP

A small Python + pygame-ce top-down archery survivor prototype inspired by the
death-loop progression idea in the plan.

## Run

From this folder:

```powershell
.\.venv\Scripts\python.exe -m loop_archer
```

Or, after the editable install:

```powershell
.\.venv\Scripts\loop-archer.exe
```

## Controls

- WASD or arrow keys: move
- Mouse: aim
- Left mouse button: shoot
- F11: toggle fullscreen
- Esc: quit

## Current POC Rules

- Echo Archer starts fullscreen.
- Your HP is also your loop timer: after the grace period, Echo Decay drains HP every second.
- If enemies finish you, the run ends as `Overwhelmed`.
- If Echo Decay drains the last HP, the run ends as `Echo Faded`.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Knowledge Base

Project notes live in [docs/knowledge-base/index.md](docs/knowledge-base/index.md).
Start there when adding a new feature after time away.
