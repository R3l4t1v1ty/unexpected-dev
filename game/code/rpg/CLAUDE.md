# rpg/

## Purpose
The RPG layer: stats and modifiers, items, gear, inventory, currencies, shops, progression (XP, levels, talents), stat checks for world and events, and the combat rules adventure mode uses. Each twin has their own RPG character.

## Rules
- Namespace `rpg`; screens `rpg_*`.
- Classes at init -300, data and screens at 0, panel/tab registration at 100.
- Item, shop and ability definitions are definitions (frozen, never saved); inventories, stats and gear are per-twin plain data in `gs` (via `core.register_state`).
- Combat rules are plain functions on plain data, with no screens or displayables, so adventure/ can call them from its tick.
- Equip and other screen-driven changes use `core.StateAction`.
- Build only what the agreed design needs. The old versions were full of RPG code nothing called.

@TASKS.md
