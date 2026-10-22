# rpg/ tasks

Milestones: design done in **M1**, stubs in **M2**, the rest in **M3** (combat numbers before adventure combat in **M4**).

## Context
Designed with the user on 2026-10-23.

**Stats.** Four base stats per twin: `str`, `int`, `dex`, `cha`.
- Value = base + gear + temporary effects. Gear counts everywhere, including choices.
- Base stats rise from world-mode training (Gym, Library, Pool…, slower), from adventure mode (how is open: task 10), and from story rewards.
- Combat: str → health and physical damage; dex → attack speed, move speed, crit; int → mana and spell damage.
- cha → reputation gains, shop prices, relationship gains; maybe charming enemies later (not in the first version).

**Stat checks.** Fixed thresholds, no dice. Menu choices carry a requirement; the choice screen (ui/) greys out a choice whose `req` fails and shows `req.describe()`:
```
menu:
    "Lift the beam" (req=ReqStat("str", 12)):
        ...
    "Show her the locket" (req=ReqItem("silver_locket")):
        ...
```
So `ReqStat(...).describe()` must give short player text like "Strength 12", and `ReqItem` "Silver Locket". Any `Req` works the same way.

**Abilities.** Each twin has their own fixed kit; the twins fight differently. The story unlocks new abilities and empowers existing ones (e.g. Nemu's claw swipe later gains bonus fire spell damage). rpg holds ability data (cooldown, mana cost, damage, scaling stat, upgrades) and the damage math; adventure/ implements how each ability moves and hits. Not in the first version: companions, charming enemies.

**Items.**
- Gear slots: head, neck, arm, waist, leg, trinket, plus a weapon slot that always holds the twin's special weapon. The player can't unequip or swap it; the story can upgrade or replace it.
- Kinds known so far: gear, crafting materials, consumables (including each relationship character's reset item), key items (unlock dialogue options), recipes, gifts.
- The rest of the item design is open (rarity or tiers, fixed items or random stats per drop, inventory size, stacking): task 4 starts with the user. Stubs store a count per item id.

**Loot and crafting** (designed to be built together):
- Loot comes from adventure mode (enemies, chests, hidden spots) via loot tables that adventure asks rpg to roll (`renpy.random`).
- Three craft stations, each its own craft with its own recipes: Alchemy Lab, Poison Caverns, Workshop.
- Recipes are learned: found as loot, bought, or earned from factions.
- Crafting always succeeds and costs no time.

**Money, shops, chest, gifts.**
- Currencies: `gold` and `yen`, per twin.
- Four shops on the world graph (Dim Hand Guild Outpost, Twilight Allure, Poison Caverns, Workshop). Stock gated with `Req`s (e.g. factions' `ReqRep`). Prices drop with cha and with modifiers other folders register (`rpg.register_price_modifier(fn)`; factions/ adds discounts).
- Inventory, gear and money are per twin; a shared chest at Home passes items between the twins (a shared state section).
- Gift items raise relationship stats: `call rpg_gift(char_id)` lets the player pick a gift, takes it and calls `chars.add_rel`.
- characters/ offers `chars.register_gain_modifier(fn)`: register one so cha speeds up relationship gains.

**Old versions** (ideas only): 6 gear slots, drag-and-drop equipping with tooltips, a shop with tabs. Their combat code had inverted hit and crit checks and missing returns; test crit both ways. Nothing else carries over.

## Uses
- core: `Definition`, registry, `register_state`/`state`, `me()`, `Req…`, signals, `StateAction`, `asset`.
- ui: `uix.register_hud_panel`, `uix.register_menu_tab`, tap-to-place helper, components, `uix.notify`, the choice screen's `req=` support.
- characters: `chars.add_rel`, `chars.register_gain_modifier` (tasks 3 and 6).

## Tasks
- [x] 1. **Design session.** Done 2026-10-23; the result is the Context above. Still open: item design (task 4) and adventure progression (task 10).
- [ ] 2. **(M2) Stubs.** Minimal item definitions; `rpg.give(item, n=1)`, `rpg.take`, `rpg.has`, `ReqItem(item, n=1)`; base stats per twin with placeholder starting values (data keyed by twin); `rpg.stat(stat)`, `rpg.base(stat)`, `rpg.train(stat, amount)`, `ReqStat(stat, min)` with short `describe()` text; signals `item_changed`, `stat_changed`. Done when: `rpg_test.rpy` covers them, a test menu uses `req=ReqStat(...)` and `req=ReqItem(...)`, and save/load keeps inventory and stats.
- [ ] 3. **Stats and modifiers.** One function computes final stats (base + gear + effects); derived combat stats (health, mana, physical and spell damage, attack speed, move speed, crit); cha factors for prices, reputation and relationship gains; register the relationship gain modifier. Done when: tests cover stacking modifiers.
- [ ] 4. **(needs user) Items, gear, currencies.** Settle the open item questions with the user and write the answers into this Context. Then: full item definitions, slots with the fixed weapon slot (`rpg.set_weapon(weapon)` for the story), equip rules, `gold`/`yen`, `rpg.money`, `rpg.add_money`, `ReqMoney`. Done when: tests.
- [ ] 5. **Panels.** `rpg_inventory_panel` and `rpg_character_panel` as HUD panels: drag between them on PC, tap-to-place on touch, tooltips; changes through `core.StateAction`. Done when: equipping by drag and by tap both survive save/load.
- [ ] 6. **Shared chest and gifts.** `call rpg_chest` (shared section), `call rpg_gift(char_id)`. Done when: an item moves from one twin to the other through the chest, and a gift raises a test relationship.
- [ ] 7. **Shops.** Shop definitions with currency, stock `Req`s, buy/sell, price modifiers; `call rpg_shop(shop_id)`; phone layout. Done when: a test shop works, and a registered test modifier changes prices.
- [ ] 8. **Loot and crafting.** Loot tables and `rpg.roll_loot(table_id)`; recipe definitions, `rpg.learn_recipe(recipe)`, stations, `call rpg_craft(station_id)`; signal `item_crafted`. Done when: tests roll a table and craft an item at a test station.
- [ ] 9. **Abilities.** Ability definitions per twin, `rpg.learn`, `rpg.empower(ability, upgrade)`, `rpg.knows`, `ReqAbility`; signal `ability_learned`. Done when: tests.
- [ ] 10. **(needs user) Progression.** Decide with the user how adventure play raises power (XP and levels, XP per stat, or something else), then build it. Done when: tests.
- [ ] 11. **Combat numbers.** Plain functions on plain data for adventure: derived stats, ability data with upgrades, damage (physical/spell, crit). Done when: unit-style tests of a few exchanges, including crit on and off.
- [ ] 12. **Publish.** Print the rpg section for game/code/CLAUDE.md after each task that changes the API.

## API to publish
See the rpg section of game/code/CLAUDE.md (planned names); update it as tasks finish.
