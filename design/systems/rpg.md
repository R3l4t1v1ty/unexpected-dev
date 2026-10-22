# rpg/

The RPG layer: stats, abilities, items and gear, inventory, loot tables, crafting, currencies, shops, the shared chest, gifts, and the combat numbers adventure mode uses. Each twin has their own RPG character. Designed with the user on 2026-10-23; the detailed version for building is in `game/code/rpg/TASKS.md`.

## Stats
Four base stats per twin: **str** (strength), **int** (intelligence), **dex** (dexterity), **cha** (charisma).

- A stat's value is base + gear + temporary effects. Gear counts everywhere, including choices in events.
- Base stats rise in both modes: training in world mode (Gym, Library, Pool…; slower), adventure mode (how is still open, see Progression), and story rewards.

| Stat | In combat | Elsewhere |
|---|---|---|
| str | health, physical damage | choices |
| dex | attack speed, move speed, crit | choices |
| int | mana, spell damage | choices |
| cha | maybe charming enemies (later) | reputation gains, shop prices, relationship gains, choices |

## Stat checks
Fixed thresholds, no dice. A menu choice carries its requirement:
```
menu:
    "Lift the beam" (req=ReqStat("str", 12)):
        ...
    "Show her the locket" (req=ReqItem("silver_locket")):
        ...
```
The choice screen (ui/) shows a choice whose `req` fails greyed out, with `req.describe()` ("Strength 12"). To hide a choice instead, use a normal `if`. Any `Req` works, so items, reputation and relationships unlock dialogue options anywhere, not only in adventure mode. (Checked in the SDK: Ren'Py 8.5 passes per-choice arguments to the choice screen as `item.kwargs`.)

## Abilities
- Each twin has a fixed kit of their own; the twins fight differently.
- The story unlocks new abilities and empowers existing ones. Example: Nemu's claw swipe later gains bonus fire spell damage.
- rpg holds the numbers (cooldown, mana cost, damage, scaling stat, upgrades) and the damage math. adventure/ implements how each ability moves and hits.
- Not in the first version: companions, charming enemies. Nemu's old story abilities (charm, confusion, fire, counter) don't carry over.

## Items
- Gear slots: head, neck, arm, waist, leg, trinket, plus a **weapon slot** that always holds the twin's special weapon. The player can't unequip or swap it; the story can upgrade or replace it.
- Item kinds known so far: gear, crafting materials, consumables (including the relationship reset item), key items that unlock dialogue options, recipes, gifts.
- **Open:** the rest of the item design: rarity or tiers, fixed items or random stats per drop, inventory size, stacking. Decided with the user before rpg task 4. The M2 stubs store a count per item id; random stats per drop would need one record per copy in the save.

## Loot and crafting (built together)
- Loot comes from adventure mode: enemies, chests, hidden spots. Loot tables are rpg data; adventure asks rpg to roll them. Most loot comes back on every visit; some hidden loot and certain bosses are one-time (adventure tracks that per twin).
- Three craft stations, each its own craft with its own recipes: **Alchemy Lab** (Henyutamei), **Poison Caverns** (Hell Citadel), **Workshop** (Order HQ).
- Recipes are learned: found as loot, bought, or earned from factions.
- Crafting always succeeds and costs no time.
- Example recipe: a character's relationship reset item = a base item + something specific to that character.

## Money, shops, chest
- Two currencies, **gold** and **yen**, per twin.
- Shops on the world graph: Dim Hand Guild Outpost and Twilight Allure (Henyutamei, Underground), Poison Caverns (Hell Citadel), Workshop (Order HQ). Stock can be gated with `Req`s (reputation, story). Prices drop with cha and with faction discounts (factions/ registers a price modifier with rpg).
- Inventory, gear and money are per twin. A **shared chest at Home** passes items between the twins.

## Gifts
Gift items can be given to relationship NPCs and raise their relationship stats. characters/ owns those stats; rpg calls `chars.add_rel`.

## Progression
- Power comes from base stats (training, adventure), gear (loot, crafting) and abilities (story).
- **Open:** how adventure play raises power: XP and levels, XP per stat (the released game's model), or something else. Decided with the user before rpg task 10.

## API shape (adjust while building)
- Items: `rpg.give(item, n=1)`, `rpg.take(item, n=1)`, `rpg.has(item, n=1)`, `ReqItem(item, n=1)`
- Stats: `rpg.stat(stat, twin=None)` (total), `rpg.base(stat, twin=None)`, `rpg.train(stat, amount)`, `ReqStat(stat, min)`
- Abilities: `rpg.learn(ability)`, `rpg.empower(ability, upgrade)`, `rpg.knows(ability)`, `ReqAbility(ability)`
- Money: `rpg.money(currency)`, `rpg.add_money(currency, n)`, `ReqMoney(currency, n)`
- `call rpg_shop(shop_id)`, `call rpg_craft(station_id)`, `call rpg_chest`, `call rpg_gift(char_id)`, `rpg.learn_recipe(recipe)`, `rpg.roll_loot(table_id)`, `rpg.register_price_modifier(fn)`
- HUD panels `rpg_inventory_panel`, `rpg_character_panel`
- Combat numbers for adventure: derived stats, ability data, the damage function
- Signals: `item_changed(twin, item, count)`, `stat_changed(twin, stat, value)`, `ability_learned(twin, ability)`, `item_crafted(twin, item, count)`

## From the old versions
Kept as ideas: the 6 gear slots, drag-and-drop equipping with tooltips (now HUD panels with tap-to-place on touch), a shop with tabs. Dropped: dice checks, 4 currencies, professions, clubs, talent trees, damage-type profiles. Almost none of the old RPG code was wired to the story; build only what's above.
