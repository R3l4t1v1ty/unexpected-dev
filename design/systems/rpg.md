# rpg/

A full rebuild, and the system with the most influence on the rest of the game. **The design happens with the user first (M1).** This page records what's known and what the design must answer.

## Known requirements
The RPG must drive:
- **Adventure-mode combat** (HP, damage, abilities, effects, enemies).
- **Stat checks in world mode and events** (stats or skills unlock choices, locations, relationship progress).
- **Items, gear and shops** (inventory, equipment slots, currencies, buying and selling, maybe crafting).
- **Progression** (XP, levels, talents or skill trees).

Each twin has their own RPG character (stats, gear, inventory).

## From the old versions (ideas, not decisions)
- Stats int/dex/str/cha with derived values (mana from int, HP from str, crit from dex).
- 6 gear slots per twin, 20-slot inventory, 4 currencies.
- Drag-and-drop equip with tooltips (now: a HUD panel per system; tap-to-place on touch).
- Reputation tiers per faction (characters/ owns reputation).
- A shop with tabs; the released game had one hardcoded shop.
- In practice almost nothing was wired: no story code changed XP or reputation, and the combat classes were sketches with bugs. Build only what the design needs.

## What the design session must answer
1. The stat list, and what each stat does in world mode, events and combat.
2. How stat checks work: thresholds or rolls? Visible odds? Retry rules? Time cost?
3. Items: categories, stacking, gear slots, rarity or tiers, crafting or not.
4. Currencies and shops: which currencies, where shops are, stock rules (`Req`-based?).
5. Progression: where XP comes from (events, adventure, activities), levels, talents or skill trees, respec.
6. Combat: real-time ability kits like the adventure prototype (Brand/Syndra-style), or something else; damage model; status effects; enemies.
7. How the RPG ties into relationships (stats gating relationship steps? gifts?).
8. What's shared between twins (nothing? some currencies?).

## Planned API shape (adjust after the design)
`rpg.give/take/has`, `ReqItem`, `rpg.stat`, `rpg.check`, `ReqStat`, `rpg.money`, `rpg.add_money`, shops (`call rpg_shop(id)`), HUD panels `rpg_inventory_panel` and `rpg_character_panel`, a combat API for adventure mode, signals `item_changed`, `level_up`, `stat_checked`.

M2 needs only stubs (`rpg.give/take/has`, `ReqItem`, `ReqStat`) so world and events can be built against them.
