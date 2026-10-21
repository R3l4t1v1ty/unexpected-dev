# Milestones

Systems only; story comes after. Each milestone lists folders in the order to start them. Detailed tasks are in each folder's `TASKS.md`.

## M1: Foundation
Goal: a new game starts, saves and loads with the new state model; ui and dev tooling exist; the RPG is designed.

| Folder | Work |
|---|---|
| core | Everything: stores, definitions, registry, `gs`, flags, clocks, signals, `Req`, migrations, `StateAction`, `label_for` / `asset`, `label start` |
| ui | Clean up the moved standard screens, variants, game-menu tab registry, HUD container |
| dev | Test menu, debug overlay (first version), content validator (first version) |
| physics | All of it can happen in parallel; it depends on nothing |
| rpg | **Design session with you** (the RPG shapes conditions, items and adventure mode) |
| — | **Decide the Android size strategy** (see open-questions.md) |

## M2: World mode
Goal: the sandbox loop works end to end with test content, for both twins.

| Folder | Work |
|---|---|
| fx | Music manager, transforms with live reduced motion, loading screens, shader |
| world | Graph, interactables, world view and loop, map and fast travel, twin swap |
| characters | Characters, encyclopedia, factions and reputation, relationship skeleton |
| rpg | Stubs only: `rpg.give/has`, `ReqItem`, `ReqStat` |
| events | **Design session with you**, then events, triggers, event book, replay |
| ui | Say screen skins, components, toasts, preferences, swap button |
| dev | Integration demo pack (a small test world built only from the public API) |

## M3: RPG
Goal: the full RPG from the M1 design: stats and modifiers, items, gear, currencies, inventory and character panels, shops, progression, stat checks, combat API.

## M4: Adventure mode
Goal: adventure maps playable from the world, with the map maker.

| Folder | Work |
|---|---|
| adventure | Map format, runtime, input and touch controls, entities, rooms and doors, minimap, map maker port, combat (uses the rpg combat API) |

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
      │      ├─ rpg (stubs in M2, full in M3) ─┐
      │      └─ minigames                      ├─ adventure
      └─ dev (grows with every system)         ┘
```

Things that can run at the same time: physics with anything; fx with characters; minigames with anything after ui; computer and progress after events.
