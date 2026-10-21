# physics/

## Purpose
A light port of Godot's 2D math and collision in plain Python, used by adventure mode (and possibly minigames): vectors, rects, transforms, collision grid, bodies, areas, raycasts, pathfinding.

## Rules
- Plain `.py` modules named `uxphys_*.py`, flat in this folder (no subfolders: each would get its own Claude lock). The only `.rpy` file is `physics_loader.rpy`.
- No Ren'Py imports in `uxphys_*` modules. They must run under plain `python3` for tests. Write Python 3.12-compatible code (the Ren'Py SDK bundles 3.12; the system Python is newer).
- Import as `import uxphys_math` etc. Never through a package path like `code.physics…` (that would make Ren'Py treat `game/code/` as a package named `code`, shadowing Python's `code` module and duplicating classes).
- Follow Godot 4.4 naming and semantics (snake_case methods) so ports from Godot code read naturally.
- Tests: `test_*.py` in this folder, run with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest` from this folder. They're excluded from builds.
- No per-call allocations in hot paths you can avoid; physics runs every tick.

@TASKS.md
