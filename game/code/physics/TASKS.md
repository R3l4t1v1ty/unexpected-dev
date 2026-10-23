# physics/ tasks

Milestone: **M1, in parallel** (depends on nothing). Must be done before adventure/ starts (M4).

## Context
Adventure mode is a top-down, RPG Maker–like mode with free movement (acceleration and friction), click/tap-to-move pathfinding, painted rooms with a collision mask, NPCs, doors, projectiles and area triggers. This folder provides the math and collision for it.

Why plain Python (checked in the Ren'Py 8.5.3 SDK):
- `.py` modules skip Ren'Py's rollback rewriting, so there's no per-object overhead.
- They can be unit-tested outside Ren'Py.
- `config.reload_modules` makes Shift+R reload them.
- `renpy.add_python_directory("code/physics/")` (path relative to `game/`) must run before the imports.

Reference: the old adventure prototype had good ports to learn from, but they're outside this folder. Ask the user to copy them in as `ref_*.txt` if you want them:
- Godot 4.4 `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`
- a `CollisionGrid` with a terrain mask (one cell per pixel of `collision.png`, colours → terrain types with a speed factor and solidity), cell-hashed static solid rects, dynamic movable boxes, and swept AABB moving X then Y so nothing tunnels
- A* with up to 30000 expansions plus string pulling

Its gaps, to fix here:
- no collision normals or slide info
- boxes only
- no enter/exit areas (only the player detected touching, once per contact, no exit)
- no grid raycast (it sampled points instead)
- the A* start cell wasn't bounds-checked

## Uses
Nothing.

## Tasks
- [x] 1. **Loader.** `physics_loader.rpy` at init -600: `renpy.add_python_directory("code/physics/")`, import the modules, add them to `config.reload_modules`. Done when: lint passes and the console can create `uxphys_math.Vector2(1, 2)`. *2026-10-23: the user confirmed lint and the console check pass.*
- [x] 2. **Math.** `uxphys_math.py`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D` with Godot 4.4 methods (length, normalized, dot, cross, angle, rotated, lerp, move_toward, clamp, snapped, intersects, encloses, merge, grow, has_point, intersects_segment, xform…). Done when: `test_uxphys_math.py` passes.
- [x] 3. **Collision.** `uxphys_collide.py`: rect and circle shapes, overlap tests, `CollisionGrid` (terrain cells with speed factor, static solids hashed by cell with owners so they can be removed, dynamic bodies, layers and masks), swept movement, `Body.move_and_slide()` returning collisions with normal and collider. Done when: tests cover tunnelling at high speed, sliding along walls, layer masks.
- [x] 4. **Areas.** `Area` with enter/exit callbacks for any body, evaluated once per tick. Done when: tests cover enter, stay, exit and removal while inside.
- [x] 5. **Raycast.** Grid DDA plus shapes; returns hit point, normal, collider. Done when: tests.
- [x] 6. **Pathfinding.** `uxphys_path.py`: A* on the grid with a walkability cache per body size, bounds-checked start and goal, string pulling. Done when: tests on a maze, including a start outside the grid.
- [x] 7. **Benchmark.** `test_bench.py` (named `test_*` so builds exclude it; runs with `python3 test_bench.py`): 200 bodies on a 100×100 grid. Done when: under 2 ms per tick on the dev machine (report the number). *2026-10-22, Python 3.14 on an i5-13500H under WSL: 1.1 ms mean, 0.8 ms median per tick (200 bodies plus 20 areas). Ren'Py's Python 3.12 may be a little slower; Android several times slower. The p95 and max numbers are WSL timing noise: a fixed workload shows the same spikes.*
- [x] 8. **Publish.** Print the physics section for game/code/CLAUDE.md.

## Decisions
- Ported from the old prototype's math (gmath, Vector2…Transform2D): same reference semantics, protocols, `_Constant` constants. Godot helper names added (`v.floor()`, `rect.get_center()`, `t.get_rotation()`, `clampf`…). `gmath.round` is `roundf` here, so the builtin isn't shadowed. `Transform2D.to_matrix()` became `matrix_values()` (no Ren'Py import): `Matrix(t.matrix_values())`.
- Terrain comes in as bytes, one terrain index per cell (the map editor's mask); `Terrain(layer, speed)` per index. Physics never decodes PNGs: adventure/ does.
- Movement is exact swept time-of-impact (no sampling), and bodies stop `SKIN` (0.001 px) short along the normal, so sliding never catches on cell seams. Overlapping at the start blocks only motion going deeper, so nothing gets stuck.
- `move_and_slide(delta)` follows Godot's floating mode: max 4 slides, `wall_min_slide_angle` 15°, the first slide keeps the full speed, and velocity isn't changed. Terrain speed scales the motion (`use_terrain_speed`).
- Areas update in `grid.step()`. Only objects that moved are rechecked, and a body in buckets with no area isn't rechecked at all.
- Pathfinding: StaticBody and terrain block, moving Bodies don't. Maps per (mask, body box) are cached in `grid.cache` and cleared by `grid.version` bumps. Connected regions make unreachable goals fail instantly; with partial paths, the body walks to the nearest reachable cell. `find_path` uses heuristic weight 1.2 (paths about 3% longer, about 3× faster on a 4K room with 8 px cells); `astar` is exact by default.

## API to publish
`uxphys_math`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`, Godot global helpers. `uxphys_collide`: `CollisionGrid` (with `raycast`, `intersect_point`, `intersect_shape`, `is_free`, `step`), `Terrain`, `RectShape`, `CircleShape`, `StaticBody`, `Body`, `Area`, `Collision`, `RayHit`. `uxphys_path`: `astar`, `smooth_path`, `find_path`, `segment_clear`, `walkable_map`, `regions`.
