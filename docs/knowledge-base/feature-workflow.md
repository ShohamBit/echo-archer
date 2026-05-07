# Feature Workflow

Use this checklist when adding new features later.

## 1. Start Clean

Check git status:

```powershell
git status --short
```

If there are uncommitted changes, decide whether they belong to the current
feature. Do not mix unrelated work.

## 2. Write Down the Feature Shape

Before editing, answer:

- What player-facing behavior changes?
- Which system owns the rule?
- Which renderer/UI piece displays it?
- Does it need persistence?
- What tests prove it works?

## 3. Keep Simulation and Rendering Separate

Put gameplay rules in `systems.py`, `models.py`, `upgrades.py`, or another
simulation-focused module.

Put drawing and pygame event handling in `main.py`.

If a screen-size calculation is needed, prefer `layout.py`.

## 4. Test First When Behavior Changes

Add or update tests before implementation when changing:

- combat
- movement
- death/loop rules
- upgrades
- saves
- enemy behavior
- layout helper behavior

Pure visual drawing changes can be verified with a pygame smoke check.

## 5. Verify

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run a pygame smoke check for UI/rendering changes.

## 6. Commit Every Feature

Commit each complete feature before starting the next one:

```powershell
git add <changed-files>
git commit -m "feat: short feature description"
```

Use focused commit messages, for example:

- `feat: add dash ability`
- `feat: add stable echo upgrade`
- `feat: add projectile wrapping upgrade`
- `fix: prevent enemies spawning inside player`

## 7. Update This Knowledge Base

When a feature changes architecture, gameplay, UI, testing, or workflow, update
the matching Markdown file in this folder in the same commit.
