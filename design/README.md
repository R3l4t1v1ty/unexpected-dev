# Unexpected: design

The plan for rebuilding Unexpected from the ground up. This folder is for people and for Claude sessions started at the project root; it never ships (`build.classify('design/', None)` in `game/code/options.rpy`).

Scope right now: **game systems only.** Story content comes later.

## Files

| File | What's in it |
|---|---|
| [vision.md](vision.md) | What the game is, the two modes, every system and whether it's kept, changed or new |
| [architecture.md](architecture.md) | Rules every system follows: saving, ids, conditions, signals, twins and time, the world loop, screens, init order, testing, platforms |
| [milestones.md](milestones.md) | Build order (M1–M5), dependencies, what can run in parallel |
| [open-questions.md](open-questions.md) | Decisions that wait on you |
| [old-versions.md](old-versions.md) | Where the old projects are, what to reuse, mistakes not to repeat |
| [systems/](systems/) | One design doc per code folder |

## How design/, CLAUDE.md and TASKS.md fit together

```
design/                      full design, for you and root sessions (never shipped)
game/code/CLAUDE.md          shared rules + the public API of every folder
                             (every Claude session in game/code loads it)
game/code/<folder>/CLAUDE.md that folder's purpose and rules, imports TASKS.md
game/code/<folder>/TASKS.md  that folder's context and task checklist
```

A Claude session started inside a code folder, e.g. `game/code/world/`, can only see that folder and the CLAUDE.md files above it. It cannot read `design/` or the other folders. That's why:
- each `TASKS.md` repeats the parts of the design its folder needs, and
- anything one folder uses from another is listed in `game/code/CLAUDE.md`.

When you change the design here, also update the affected `TASKS.md` files and, for rules or APIs, `game/code/CLAUDE.md`.

## Day-to-day workflow

1. Pick the next unchecked task in a folder's `TASKS.md` (see [milestones.md](milestones.md) for order).
2. Start `claude` inside that folder and ask it to do the task. Tasks marked **(needs user)** start with a conversation with you.
3. When the session changes a public API, it prints the lines to add to `game/code/CLAUDE.md`. Apply them from a session started in `game/code/` (not locked) or by hand.
4. Lint and play from the project root (locked sessions can't run Ren'Py):
   - `~/renpy-8.5.3-sdk/renpy.sh . lint`
   - `~/renpy-8.5.3-sdk/renpy.sh .`
   - phone layout: `RENPY_VARIANT="small phone touch android mobile" ~/renpy-8.5.3-sdk/renpy.sh .`
5. Commit from the project root.

New folder under `game/code/`? Run `python3 .claude/sync-folders.py` from `game/code/`. It adds the folder's lock, a starter CLAUDE.md and a starter TASKS.md.
