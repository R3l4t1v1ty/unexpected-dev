# adventure/

## Purpose
Adventure mode: a top-down, RPG Maker–like mode entered from the world (painted rooms, free movement, NPCs, doors, combat), plus its map maker (`editor_*.rpy`, developer-only).

## Rules
- Namespace `adv`; screens and labels `adventure_*` / `adv_*`. Editor files are named `editor_*.rpy` (excluded from builds by options.rpy). Nothing outside editor files may reference editor names.
- Saves hold only plain state (world, room, position, facing, permanent progress) in `core.state("adv")`. Never store the displayable, maps, art or entities in `gs`. Rebuild the runtime from plain state on load.
- Per-frame classes derive from `python_object`, not the store's `object`. Don't create `Transform`s, `Solid`s or `Text`s every frame; cache them.
- The displayable must stop redrawing when nothing moves and while paused.
- Every image ≤ 2048 px per side (chunk room layers).
- Maps live in `game/maps/`, never `game/images/`.
- Physics comes from `uxphys_*` modules; combat rules from rpg/'s combat API.
- Input must work with touch: no hover-only or keyboard-only actions.

@TASKS.md
