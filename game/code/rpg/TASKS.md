# rpg/ tasks

Milestones: design in **M1**, stubs in **M2**, the rest in **M3** (combat API before adventure combat in M4).

## Context
A full rebuild and the most important system: it affects conditions, items, adventure mode and relationships. It must cover:
- adventure-mode combat
- stat checks in world mode and events
- items, gear and shops
- progression (XP, levels, talents)

Each twin has their own RPG character.

Ideas from the old versions (not decisions):
- Stats int/dex/str/cha with derived values (mana = int×2, HP = str×2, crit from dex).
- 6 gear slots per twin, 20-slot inventory, 4 currencies.
- Drag-and-drop equip with tooltips, and a shop with tabs.
- Reputation tiers per faction (characters/ owns reputation).
- The adventure prototype had real-time, LoL-style ability kits (Brand, Syndra) with hits, knockback, stun, slow, ignite, stacking and detonation, and homing or skillshot projectiles.
- What went wrong before: almost nothing was wired (no story code changed XP or reputation), and combat classes had inverted hit/crit checks and missing returns.

The design session (task 1) must answer:
1. The stat list, and what each stat does in world, events and combat.
2. Stat checks: thresholds or rolls, visible odds, retries, time cost.
3. Items: categories, stacking, gear slots, tiers or rarity, crafting.
4. Currencies and shops: which currencies, where, stock rules.
5. Progression: XP sources, levels, talents or skill trees, respec.
6. Combat model for adventure mode, damage, effects, enemies.
7. Ties to relationships.
8. Anything shared between twins.

## Uses
- core: `Definition`, registry, `register_state`/`state`, `me()`, `Req…`, signals, `StateAction`, `asset`.
- ui: `uix.register_hud_panel`, `uix.register_menu_tab`, tap-to-place helper, components, `uix.notify`.

## Tasks
- [ ] 1. **(needs user, M1) Design session.** Answer the 8 questions with the user and replace this Context with the agreed design (stats, formulas, item model, slots, currencies, shop rules, progression, combat model). Then refine tasks 3–9.
- [ ] 2. **(M2) Stubs.** Minimal item definitions, `rpg.give(item, n=1)`, `rpg.take(item, n=1)`, `rpg.has(item, n=1)`, `ReqItem(item, n=1)`, `rpg.stat(name)` and `ReqStat(stat, min)` with placeholder stats; signal `item_changed`. Done when: `rpg_test.rpy` covers them and save/load keeps the inventory.
- [ ] 3. **Stats and modifiers.** Base stats, modifiers from gear, effects and talents, derived stats; one function computes final values. Done when: tests cover stacking modifiers.
- [ ] 4. **Items, gear, currencies.** Full item definitions, gear slots, equip/unequip rules, currencies (`rpg.money`, `rpg.add_money`). Done when: tests.
- [ ] 5. **Panels.** `rpg_inventory_panel` and `rpg_character_panel` as HUD panels: drag between them on PC, tap-to-place on touch, tooltips; changes through `core.StateAction`. Done when: equip by drag and by tap both survive save/load.
- [ ] 6. **Shops.** Shop definitions with stock rules, buy/sell, `call rpg_shop(shop_id)`, phone layout. Done when: test shop works.
- [ ] 7. **Progression.** XP, levels, talents per the design; signal `level_up`. Done when: tests.
- [ ] 8. **Stat checks.** `rpg.check(stat, difficulty)` with the agreed rules and an optional screen showing the check; signal `stat_checked`. Done when: test label uses it in a menu choice.
- [ ] 9. **Combat API.** Plain-data combat rules for adventure mode: damage, effects, abilities, per the design. Done when: unit-style tests of a few exchanges.
- [ ] 10. **Publish.** Print the rpg section for game/code/CLAUDE.md after each of tasks 2–9 that changes the API.

## API to publish
See the rpg section of game/code/CLAUDE.md (planned names); update after the design.
