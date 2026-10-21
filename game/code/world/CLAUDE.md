# world/

## Purpose
World mode (the sandbox): spaces, places, locations and their connections as a graph; objects and NPCs placed in locations; the world view screen; the world loop that runs content and does bookkeeping; the map and fast-travel panel; twin swapping.

## Rules
- Namespace `world`; screens and labels `world_*` (except content labels, which come from `core.label_for`).
- Classes at init -300, data and screens at 0, hook/panel registration at 100.
- Location ids are `space.place.location`. Never build ids, label names or image paths by hand; use `core.label_for` and `core.asset`.
- Content labels are `call`ed by `world_loop` and must `return`. world never jumps into content and content never jumps back.
- world doesn't reference events, characters' internals or rpg. Those plug in with `world.register_entry_hook`, `world.register_hidden_provider`, `world.register_marker_provider` and `Req` classes.
- Screens never loop over every location or interactable; precompute per location.

@TASKS.md
