# factions/

## Purpose
Factions, reputation (per twin) and quests. Factions open shops, discounts, recipes and services as reputation grows; quests are how reputation is earned.

## Rules
- Namespace `fac`; screens `fac_*`.
- Classes at init -300, faction and quest data and screens at 0, wiring (signal connections, price modifier, tab/panel registration) at 100.
- Faction and quest definitions are frozen definitions; reputation, opened factions and quest progress are per-twin plain data in `gs`.
- factions uses rpg (items, recipes, money, `rpg.stat("cha")`, `rpg.register_price_modifier`) and characters (`ReqKnown`); rpg and characters never reference factions.
- Quest progress reacts to signals (`item_changed`, `item_crafted`, adventure signals); never poll from screens.

@TASKS.md
