# Milestones

Systems only; story comes after. Each milestone lists folders in the order to start them. Detailed tasks are in each folder's `TASKS.md`.

## M1: Foundation
Goal: a new game starts, saves and loads with the new state model; ui and dev tooling exist; the RPG is designed.

Done so far: core, physics, the RPG design (with relationships, factions and the world graph, 2026-10-23), the Android size decision.

| Folder | Work |
|---|---|
| core | Everything: stores, definitions, registry, `gs`, flags, clocks, signals, `Req`, migrations, `StateAction`, `label_for` / `asset`, `label start` |
| ui | Clean up the moved standard screens, variants, game-menu tab registry, HUD container |
| dev | Test menu, debug overlay (first version), content validator (first version) |
| physics | All of it can happen in parallel; it depends on nothing |
| rpg | **Design session with you**: done 2026-10-23 (see systems/rpg.md, characters.md, factions.md) |
| — | Android size: decided, Ren'Py's Downloader for Large Games (see architecture.md) |

## M2: World mode
Goal: the sandbox loop works end to end with test content, for both twins.

| Folder | Work |
|---|---|
| fx | Music manager, transforms with live reduced motion, loading screens, shader |
| world | Graph, interactables, world view and loop, map and fast travel, twin swap |
| characters | Characters, encyclopedia, relationships (model, activities) |
| rpg | Stubs only: items, base stats, `ReqItem`, `ReqStat` |
| events | **Design session with you**, then events, triggers, event book, replay |
| ui | Say screen skins, choice screen with `req=`, components, toasts, preferences, swap button |
| dev | Integration demo pack (a small test world built only from the public API) |

## M3: RPG
Goal: the full RPG from the M1 design, then factions.

| Folder | Work |
|---|---|
| rpg | Stats and modifiers, **item design with you**, items, gear, gold and yen, panels, shared chest, gifts, shops, loot and crafting, abilities, **progression design with you**, combat numbers |
| factions | Factions, reputation (per twin), **quest details with you**, quests, perks (shops, discounts, recipes, services), quest log |

## M4: Adventure mode
Goal: adventure maps playable from the world, with the map maker.

| Folder | Work |
|---|---|
| adventure | Map format, runtime, input and touch controls, entities (chests, one-time bosses, event triggers), rooms and doors, minimap, map maker port, combat (uses rpg's combat numbers) |
| factions | Quest goals from adventure signals |

## M5: Extras
| Folder | Work |
|---|---|
| computer | **Design session with you**, app shell, GossipUp |
| minigames | Common protocol, loop puzzle, rune trace with drag |
| progress | **Achievement design with you**, achievements, gallery |

## Dependencies

```
physics ─────────────────────────────┐
core ─┬─ ui ─┬─ fx ── world ─┬─ events ─┬─ progress
      │      │               │          └─ computer
      │      ├─ characters ──┘
      │      ├─ rpg (stubs in M2, full in M3) ─┬─ factions (M3; adventure goals M4)
      │      └─ minigames                      ├─ adventure
      └─ dev (grows with every system)         ┘
```

Things that can run at the same time: physics with anything; fx with characters; minigames with anything after ui; computer and progress after events; factions with adventure once rpg is done.
