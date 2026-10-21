# adventure/ tasks

Milestone: **M4** (needs physics, core, ui; combat needs rpg's combat API).

## Context
Decisions:
- Maps are **whole-room painted images** (layers) plus a painted collision mask, not tilesets. Layers are cut into chunks of ≤ 2048 px (Android's texture limit is 4096).
- The **map maker is a port** of the old prototype's editor, improved.
- Saves hold only plain state; the runtime is rebuilt on load.

The old prototype (ActionAdventureMode) is outside this folder. Ask the user to copy files in as `ref_*.txt` when porting. What it had:
- One `renpy.Displayable` (`AdventureMode`) with a fixed 60 Hz tick accumulator in `render()`, capped frame gaps, a Camera2D-like camera (smoothing, limits, zoom via `Render.zoom`, pixel snap), and sorting by (z, y) with view culling.
- Godot-style input actions (`is_pressed`, `is_just_pressed`, `get_vector`). Free movement: accel 1500, speed 120 px/s, friction 2000; terrain speed factors. Click-to-move via A*, click-an-object to walk there and interact.
- Animation: 8 directions, any states, mirror fallbacks, RPG Maker MV 3×4 sheets.
- Entities via `@adventure_type` with `editor_properties`: interact (calls a label), npc (faces you, calls a label), enemy (label on touch, optional health, no AI), dummy, door, exit, solid, prop, marker.
- World layout: rooms placed side by side in one coordinate space with seamless open edges (slide/fade/cut), doors for interiors, per-twin `permanent` progress, an Isaac-style minimap.
- Calling a label from inside the mode and resuming: `renpy.call(label, from_current=True)`, then re-run the `run()` statement.
- Editor (~2000 lines): worlds/rooms browser, mask painting (brush, rect, fill, 100-step undo), object placement with property panels, prop collision and hit-box drawing, add neighbour rooms, playtest at the mouse position, `.bak` copies on save; F9 opens it.
- Combat: hits with knockback, stun, slow, ignite; stacking and detonation; skillshot and homing projectiles; two LoL-style kits.

What it did wrong (fix here):
- It pickled the whole displayable, maps and art into saves.
- It redrew every frame even while paused, with no interpolation (judder on high-refresh screens).
- It made new `Transform`s and `Solid`s every frame, sorted everything every frame, and rebuilt HUD text every 0.05 s.
- Only the player detected contact (no exit events).
- It had no touch controls for abilities, interact or minimap.
- Editor screens scanned the disk on every evaluation.
- Whole-room images could exceed Android's texture limit.
- An unreachable test room and missing prop images failed silently.

Map format v1 (finalise in task 1):
```
game/maps/<world_id>/world.json            {"version": 1, "rooms": {"<room_id>": {"pos": [x, y]}}, "start": ...}
game/maps/<world_id>/<room_id>/map.json    {"version": 1, "size": [w, h], "cell": 8,
                                            "layers": [{"name", "z", "chunks": [[cx, cy, file], ...]}],
                                            "objects": [{"type", "id", "x", "y", "props": {...}}]}
game/maps/<world_id>/<room_id>/collision.png   one pixel per cell; colours = terrain types
game/maps/<world_id>/<room_id>/<layer>_<cx>_<cy>.webp
```
Rules for map files:
- Maps never go in `game/images/` (Ren'Py auto-names images there by basename, first file wins).
- JSON-loaded data must be converted to plain .rpy containers before going into `gs`.
- Use `renpy.loadable`/`renpy.open_file` to read, and clear Ren'Py's loadable cache after the editor writes.

## Uses
- physics: `uxphys_math`, `uxphys_collide` (`CollisionGrid`, `Body`, `Area`, `raycast`), `uxphys_path` (`astar`, `smooth_path`).
- core: `register_state`/`state`, `me()`, `label_for`, `asset`, signals, `StateAction`.
- ui: components, `uix.notify`, touch variants.
- rpg: combat API, `rpg.give` (pickups).
- world: how adventure is entered from a world object (`call adventure(world_id, entry_id)` from a content label) and where the player returns.

## Tasks
- [ ] 1. **Map format v1.** Finalise the format, write a loader with version checks and clear errors, chunked layers, collision mask → `CollisionGrid`. Done when: a hand-made test map with 2 rooms loads.
- [ ] 2. **Runtime and view.** Runtime in a constant store; displayable with fixed tick, interpolation, idle sleep (no redraw when nothing moves or while paused); camera; draw order and culling. Done when: a test character walks around a test room smoothly, and CPU is near idle when standing still.
- [ ] 3. **Loop, sync, rebuild.** `label adventure(world_id, entry_id)`; `call screen adventure_view` returning action tuples; plain state in `core.state("adv")` synced with `renpy.retain_after_load()`; rebuild on load. Done when: saving in a room and loading puts the player back in the same room and position.
- [ ] 4. **Input and touch.** Named actions; keyboard, click/tap-to-move with A*; virtual stick and on-screen buttons under `touch`. Done when: playable on PC and under phone emulation.
- [ ] 5. **Entities.** `@adv.entity_type` registry with editor property specs; npc, interact, door, exit, enemy, prop, marker, area trigger; physics Areas for triggers; labels via `core.label_for("adv", id, verb)` called and resumed. Done when: test room has a talking NPC, a door and an area trigger.
- [ ] 6. **Rooms and minimap.** Seamless room edges with transitions, doors, per-twin permanent progress, minimap. Done when: walk across 3 rooms and through a door; progress persists per twin.
- [ ] 7. **Map maker.** Port the prototype editor into `editor_*.rpy`: rooms browser, mask painting with undo, object placement with property panels, chunk export, playtest; no disk scans inside screens; writes into `game/maps/`. Done when: a new room made in the editor plays in the runtime.
- [ ] 8. **Combat.** After rpg's combat API: abilities, hits, effects, enemies with basic AI, touch ability buttons. Done when: a test fight works on PC and touch.
- [ ] 9. **Publish.** Print the adventure section for game/code/CLAUDE.md (entering, labels, entity registry, map format).

## API to publish
`call adventure(world_id, entry_id)` (and what `_return` holds), `adv.entity_type`, adventure content label naming, the map format v1, signals `adventure_entered`, `adventure_left`.
