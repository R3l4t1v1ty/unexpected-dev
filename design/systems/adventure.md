# adventure/

Adventure mode: a top-down, RPG Maker–like mode entered from the world, and its map maker. Reference: the ActionAdventureMode prototype (see [old-versions.md](../old-versions.md)).

## Decisions
From the RPG design with the user (2026-10-23):
- **What it is:** the RPG's playground: interactable objects, NPCs, enemies, items and loot (crafting materials come from here), real-time combat. It can start events (an area or object starts one).
- **Art:** almost everything is pre-rendered sprites. Only VFX are drawn in code (shapes, particles, shaders).
- **Hand-made maps**, no shuffled layouts. Ten entrances on the world graph: Beach, Underground, Prison, Destruction Fields, Frostlands, Ruins of Silver Cities, Satyr Forest, Spec Ops, Magical Forest, Shroomie Caves.
- **Replayable:** enemies and loot come back on every visit, except certain bosses and hidden loot, which are one-time per twin.
- **A run costs 1 time slot.** Victory or leaving keeps what was found. Defeat sends the twin back to the entrance and loses the run's loot, so loot is held in the run until it ends.

From the M1 plan:
- **Maps are whole-room painted images** (layers) with a painted collision mask, like the prototype. Not tilesets. Layers are cut into chunks of ≤ 2048 px for Android (texture limit 4096).
- **The map maker is a port of the prototype's editor**, improved: rooms browser, collision-mask painting with undo, object placement with property panels, playtest. It lives in `adventure/editor_*.rpy` (it needs the entity registry and renderer internals) and is excluded from builds.
- **Physics** comes from physics/ (`uxphys_*`).
- **Saves hold only plain state**: world, room, position, facing, per-twin permanent progress (opened chests, defeated enemies…). The runtime is rebuilt from that on load. The prototype pickled its whole displayable, maps and art; don't.

## Map format v1 (to finalise in adventure task 1)
```
game/maps/<world_id>/world.json            {"version": 1, "rooms": {"<room_id>": {"pos": [x, y]}}, "start": ...}
game/maps/<world_id>/<room_id>/map.json    {"version": 1, "size": [w, h], "cell": 8,
                                            "layers": [{"name": "ground", "z": "ground",
                                                        "chunks": [[cx, cy, "ground_0_0.webp"], ...]}, ...],
                                            "objects": [{"type": "npc", "id": "...", "x": 0, "y": 0,
                                                         "props": {...}}, ...]}
game/maps/<world_id>/<room_id>/collision.png   one pixel per cell; colours = terrain types
game/maps/<world_id>/<room_id>/<layer>_<cx>_<cy>.webp
```
- Maps live in `game/maps/`, not `game/images/`: Ren'Py names images in `game/images/` automatically by basename, and the first file wins silently.
- Rooms sit side by side in one world coordinate space; touching edges are open (slide, fade or cut transition). Interiors are reached through door objects.

## Runtime
- One creator-defined displayable with a fixed 60 Hz tick (accumulator in `render`), interpolation between ticks for smooth motion on high-refresh screens, and **no redraws while nothing moves or while paused** (the prototype redrew every frame even during dialogue, which drains phone batteries).
- Camera like Camera2D (smoothing, limits, zoom, pixel snap); draw order by (layer, y); view culling.
- Per-frame objects derive from `python_object` (store objects log every change for rollback). Cache tinted and effect displayables instead of creating `Transform`s every frame.
- Entities: `@adv.entity_type("npc")` registry with editor property definitions. Types: npc, interact, door, exit, enemy, prop, marker, area trigger.
- Areas (enter/exit) from physics drive triggers for any body, not only the player.
- Talking to an NPC or interacting calls a Ren'Py label (`core.label_for("adv", id, verb)`) and resumes afterwards. Loop shape: `call screen adventure_view` returns actions like `("talk", npc_id)`; the label calls content; back to the screen.

## Input
Named actions like Godot's input map. PC: WASD/arrows, interact key, ability keys, click-to-move with A*. **Touch from the start**: tap-to-move and tap-to-interact, a virtual stick, on-screen action and ability buttons, no hover-based aiming.

## Combat
- **Real time.** Each twin has their own fixed kit, and the story adds abilities and empowers existing ones; for example, Nemu's claw swipe later gains bonus fire spell damage.
- **Who does what:** rpg/ holds ability data and the damage math. adventure/ implements how each ability moves and hits, reusing the prototype's hits, knockback, stun, slow, stacking effects and projectiles.
- **Stats:** str gives health and physical damage; dex gives attack speed, move speed and crit; int gives mana and spell damage.
- **Not in the first version:** companions, charming enemies.
- **Touch:** ability buttons, and aiming that works without a mouse (e.g. auto-target the nearest enemy, or tap a target).

## Signals for other folders
Factions' quests need adventure goals: boss defeated, place reached, thing found. Adventure emits signals for these.

## Open questions
- How adventure play raises power (rpg task 10).
- Touch aiming details.
