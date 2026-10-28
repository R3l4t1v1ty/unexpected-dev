# Milestones

Systems only; story comes after. Each milestone lists folders in the order to start them. Detailed tasks are in each folder's `TASKS.md`.

## M1: Foundation (done 2026-10-24)
Goal: a new game starts, saves and loads with the new state model; ui and dev tooling exist; the RPG is designed.

| Folder | Work |
|---|---|
| core | Everything: stores, definitions, registry, `gs`, flags, clocks, signals, `Req`, migrations, `StateAction`, `label_for` / `asset`, `label start`. Added for dev: validator registry, kind/section lookups, `snapshot`/`migrate` (tasks 13–15) |
| ui | Everything except task 12 (clean-up, waits on art). The M2 ui work (say skins, choice screen with `req=`, components, toasts, preferences) was done early |
| dev | Test menu, debug overlay, content validator, fixture saves, profiler helpers |
| physics | All of it |
| rpg | Design session: relationships, factions and the world graph too (2026-10-23) |
| — | Android size: Ren'Py's Downloader for Large Games (see architecture.md) |

## M2: World mode
Goal: the sandbox loop works end to end with test content, for both twins.

Four rounds. Folders in the same round run in parallel; a round can start once the tasks it needs from the round before are done.

**Round 1: start now** (each needs only core and ui)

| Folder | Tasks |
|---|---|
| fx | 1–7: sound, music manager, transforms with live reduced motion, transitions, mirage shader, fake loading (placeholder tips until you write them) |
| world | 1–3: graph definitions and validator, NPCs and objects, per-twin location and visited |
| characters | 1, 2, 4: speakers, introductions, relationship model |
| rpg | 2: stubs (items, base stats, `ReqItem`, `ReqStat`) |
| events | 1: **design session with you** (it has to happen before round 3) |

**Round 2** (world needs fx's music manager)

| Folder | Tasks |
|---|---|
| world | 4–7: world view, world loop and twin swap, map and fast travel, music provider |
| characters | 5–6: activities, encyclopedia |
| world | 8: **the real graph with you** (ids, place grouping, button positions; the graph itself is already transcribed in world/TASKS.md) |

**Round 3** (needs world's loop and characters' relationship model)

| Folder | Tasks |
|---|---|
| events | 2–8: definitions, progress, world hooks, event book and tracker, Story tab, replay |
| characters | 7–8: activities on NPCs in their slots, publish |
| world | 9: **NPC schedules with you**, then 10: publish |

**Round 4**

| Folder | Tasks |
|---|---|
| dev | 6: demo pack, a small test world built only from the public API (its shop and adventure parts wait for M3/M4) |

Decisions from you in M2: the events design (before round 3), the real graph session and the two places without a space (Ruins of Silver Cities, Satyr Forest), your NPC schedule plan, loading tips. Which characters get relationships, and character additions, are needed for story content, not for building the systems.

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
