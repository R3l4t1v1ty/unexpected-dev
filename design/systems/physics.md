# physics/

A light port of Godot's 2D math and collision, in plain Python, for adventure mode (and maybe minigames). It depends on nothing, so it can be built at any time, in parallel with M1.

## Why plain .py
See [architecture.md](../architecture.md) §10:
- No rollback overhead.
- Unit tests run with plain `python3`.
- Shift+R reload.

It's loaded with `renpy.add_python_directory("code/physics/")` and imported as `uxphys_*` modules. The files stay flat in `physics/` because a subfolder would get its own Claude lock.

## Modules
| Module | Contents |
|---|---|
| `uxphys_math.py` | `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`, following Godot 4.4's method names and semantics (snake_case) |
| `uxphys_collide.py` | Shapes (rect/AABB, circle), overlap tests, swept-AABB movement, `Body.move_and_slide()` returning collision info (normal, collider), `CollisionGrid` (terrain cells, cell-hashed static solids, dynamic bodies, layers and masks), `Area` with enter/exit callbacks for any body, `raycast` |
| `uxphys_path.py` | A* on the collision grid with a walkability cache per body size, string pulling (path smoothing) |
| `physics_loader.rpy` | Init -600: adds the directory, imports the modules, registers them for reload |
| `test_*.py` | Unit tests (excluded from builds) |

## Reuse from the adventure prototype
The prototype (`ActionAdventureMode/game/code/engine/math/*.rpy`, `adventure/adventure_map.rpy`, `adventure_path.rpy`) has:
- faithful Godot 4.4 math ports
- a sound `CollisionGrid`: terrain mask, cell-hashed solids, swept AABB X-then-Y so nothing tunnels
- A* plus string pulling

What it lacked:
- collision normals and slide info
- shapes other than boxes
- Area-style enter/exit (only the player detected contact)
- grid raycasts
- a bounds check on the A* start cell

A locked physics/ session can't read the prototype. To port from it, copy the files in as `ref_*.txt` from a root session, or do the port from a root session.

## Budget
200 bodies on a 100×100 grid: under 2 ms per tick in Ren'Py's Python.
