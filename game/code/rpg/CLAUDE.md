# rpg/

## Purpose
The RPG layer: stats, abilities, items, gear, inventory, loot tables, crafting, currencies, shops, the shared chest, gifts, and the combat numbers adventure mode uses. Each twin has their own RPG character.

## Rules
- Namespace `rpg`; screens `rpg_*`.
- Classes at init -300, data and screens at 0, panel/tab registration at 100.
- Item, recipe, loot-table, shop and ability definitions are definitions (frozen, never saved); inventories, stats, gear, money and known recipes/abilities are per-twin plain data in `gs` (via `core.register_state`). The shared chest is a shared section.
- Combat numbers are plain functions on plain data, with no screens or displayables, so adventure/ can call them from its tick.
- Equip and other screen-driven changes use `core.StateAction`.
- Other folders change prices and gains through registries (`rpg.register_price_modifier`); rpg doesn't reach into factions/.
- Build only what the agreed design needs. The old versions were full of RPG code nothing called.

@TASKS.md
