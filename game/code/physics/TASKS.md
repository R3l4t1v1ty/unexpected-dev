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
- [ ] 1. **Loader.** `physics_loader.rpy` at init -600: `renpy.add_python_directory("code/physics/")`, import the modules, add them to `config.reload_modules`. Done when: lint passes and the console can create `uxphys_math.Vector2(1, 2)`.
- [ ] 2. **Math.** `uxphys_math.py`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D` with Godot 4.4 methods (length, normalized, dot, cross, angle, rotated, lerp, move_toward, clamp, snapped, intersects, encloses, merge, grow, has_point, intersects_segment, xform…). Done when: `test_uxphys_math.py` passes.
- [ ] 3. **Collision.** `uxphys_collide.py`: rect and circle shapes, overlap tests, `CollisionGrid` (terrain cells with speed factor, static solids hashed by cell with owners so they can be removed, dynamic bodies, layers and masks), swept movement, `Body.move_and_slide()` returning collisions with normal and collider. Done when: tests cover tunnelling at high speed, sliding along walls, layer masks.
- [ ] 4. **Areas.** `Area` with enter/exit callbacks for any body, evaluated once per tick. Done when: tests cover enter, stay, exit and removal while inside.
- [ ] 5. **Raycast.** Grid DDA plus shapes; returns hit point, normal, collider. Done when: tests.
- [ ] 6. **Pathfinding.** `uxphys_path.py`: A* on the grid with a walkability cache per body size, bounds-checked start and goal, string pulling. Done when: tests on a maze, including a start outside the grid.
- [ ] 7. **Benchmark.** `test_bench.py` (named `test_*` so builds exclude it; runs with `python3 test_bench.py`): 200 bodies on a 100×100 grid. Done when: under 2 ms per tick on the dev machine (report the number).
- [ ] 8. **Publish.** Print the physics section for game/code/CLAUDE.md.

## API to publish
`uxphys_math`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`. `uxphys_collide`: `CollisionGrid`, `Body`, `Area`, `raycast`. `uxphys_path`: `astar`, `smooth_path`.
