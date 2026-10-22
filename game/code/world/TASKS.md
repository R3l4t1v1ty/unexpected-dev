# world/ tasks

Milestone: **M2**.

## Context
Kept from the old versions, but as a real graph:
- **Location**: smallest unit, id `space.place.location` (e.g. `town.home.living_room`). Background per time slot (slots 0–3 may share images), optional requirements (enforced; rebuild #2 stored them but never checked them), objects and NPCs.
- **Place** (`town.home`) and **space** (`town`): grouping only (maps, music).
- **Connection**: a button that moves you to another location. Declared explicitly; any location may link to any other, across places and spaces. Old versions were trees (each location linked only to its parent; don't do that). Two-way by default with a button position on each side; optional one-way (the real graph has none so far); optional requirements. **Portals** are ordinary connections between far-apart places, drawn with a portal button style (`style=` on the connection), not destination pickers.
- **Exit menu**: one button opening a popup of up to 4 connections.
- **NPC**: character at a location with activity, z-layer 0–9, position, verbs, `when` (a `Req` or a dict twin → `Req`), priority. A character appears at most once in the world at a time (highest priority wins).
- **Object**: like an NPC without a character.
- **Verbs** → content labels via `core.label_for(kind, id, verb)`. One verb: click runs it. Several: a floating icon menu.
- Optional bg/fg add-on images per interactable (drawn behind/in front).
- Tab highlights every clickable thing for 1.5 s.
- Per twin: current location, visited set, favourites (4 slots, unlocked over time), flags on locations/objects/NPCs.
- The world grows a lot: two new spaces (Hell Citadel, Order HQ) joined to the town by portals. The full graph is below, under "World graph".
- **NPC schedules**: NPCs follow schedules (where they are in each slot). The user has a detailed plan and gives it to this folder's session in task 9.
- **What sits on locations** besides NPCs and objects, all as objects/verbs that call content or other folders' labels:
  - adventure entrances (`call adventure(world_id, entry_id)`);
  - shops (`call rpg_shop`), craft stations (`call rpg_craft`), the shared chest at Home (`call rpg_chest`);
  - faction locations (factions/);
  - relationship activities (characters/; verbs on the NPC, only in their time slots);
  - sandbox activities: repeatable mechanics not tied to an NPC, each different, with varied rewards (Wardrobe, Shapeshifting Statue, Passers-by, Slime Sandbox, Summoning Circle, Spa Day). Their mechanics are built later; world only gives them a place;
  - training spots that raise rpg stats (Gym, Library, Pool…; content calls `rpg.train`).

**The world loop** (rules from game/code/CLAUDE.md):
```
label world_loop:
    # entry hooks (events), fx.reconcile(), prediction
    call screen world_view        # returns ("move", loc) / ("interact", kind, id, verb) / ("travel", loc) ...
    # handle; content: call expression target from world_ret_content
    # after content: emit content_finished, renpy.force_autosave()
    jump world_loop
```
`call screen` checkpoints with its return value, so each action is one rollback step. Return values and call arguments are ids only. Twin swap: the game menu calls `renpy.jump_out_of_context("world_swap")`, allowed only while `world.idle()` is true (in the loop, not in content).

## World graph
Transcribed from the user's `game/dev_resources/graph.png` (2026-10-23; this session can't open it). The user's notes:
- Every connection is two-way.
- Ignore the dashed lines in the image; they were drawn inconsistently.
- Portals are plain connections between far-apart places.
- Space and place grouping matter little. Rebuild #2 grouped Henyutamei into home, school, dorm, underground, cafe (Ivory Paw), beach, park, tamikos and hanas.

Each space's node in the graph is its hub location, linking to the places (rebuild #2 linked Henyutamei's places to a `henyutamei` root the same way). Names below are display names; ids are agreed in task 8. `[…]` marks what sits on a location.

**Henyutamei** (the town; the hub links to Home Entrance, Dorm Garden, Beach, Park, Ivory Paw, School Yard, Hana's, Tamiko's, Underground)
- Home: Home Entrance – Livingroom – Kitchen; Home Entrance – Upstairs; Upstairs – Ayumu's Room, Bathroom, Nemu's Room. [Nemu's Room: Wardrobe (sandbox activity)] [the shared chest goes somewhere at Home]
- Dorm: Dorm Garden – Fountain, Statue, Rina & Chizuru (their room), Emi & Yui (their room), Yuto (his room). [Statue: Shapeshifting Statue (sandbox activity)]
- Beach. [adventure entrance]
- Park. [Hana; Passers-by (sandbox activity); a Shrine from the story, not in world mode for now]
- Ivory Paw (café) – Alchemy Lab. [Ivory Paw: Rina; a Shrine from the story, not in world mode for now] [Alchemy Lab: faction, craft station, Slime Sandbox (sandbox activity)]
- School: School Yard – Gym, Pool, Ground Floor; Ground Floor – Lounge, Infirmary, Chess Club, Art Club, First Floor; First Floor – Investigation Club, Library, Rooftop, Classroom A, Classroom B.
- Hana's – Hell Citadel hub (portal). [Summoning Circle (sandbox activity)] (Rebuild #2 had Hana's Livingroom and Basement; the graph shows one node.)
- Tamiko's – Order HQ hub (portal).
- Underground – Dim Hand Guild Outpost, Twilight Allure; Twilight Allure – Vampire Lair. [Underground: Merce, adventure entrance] [Dim Hand Guild Outpost: faction, shop] [Twilight Allure: Emi, shop] [Vampire Lair: faction]

**Hell Citadel** (new; the hub links to Lava Pools, Planetarium, Prison, Poison Caverns, Inya's Hideout, Throne, and by portal to Hana's, Destruction Fields, Frostlands, Ruins of Silver Cities, Satyr Forest)
- Lava Pools [Spa Day (sandbox activity)], Planetarium, Prison [adventure entrance], Poison Caverns [shop, craft station], Inya's Hideout [faction], Throne [faction], Destruction Fields [adventure entrance], Frostlands [adventure entrance].

**Order HQ** (new; the hub links to Spec Ops, Eiko's Hideout, Council, Workshop, Magical Forest, and by portal to Tamiko's, Ruins of Silver Cities, Satyr Forest)
- Spec Ops [adventure entrance], Eiko's Hideout [faction], Council [faction], Workshop [craft station, shop], Magical Forest [adventure entrance] – Shroomie Caves [adventure entrance].

**Reachable from both new hubs by portal**: Ruins of Silver Cities [adventure entrance], Satyr Forest [adventure entrance]. Which space they belong to isn't decided.

Totals: 3 spaces, 56 locations (38 in Henyutamei, 9 in Hell Citadel, 7 in Order HQ, 2 shared), 10 adventure entrances, 7 factions, 4 shops, 3 craft stations, 6 sandbox activities.

## Uses
- core: `Definition`, registry, flags, `register_state`/`state`, `me()`, `swap()`, `slot()`, `Req…`, signals, `label_for`, `asset`, `register_save_info`, `StateAction`.
- ui: `hud_root`, `uix.register_hud_panel`, components.
- fx: `fx.reconcile()`, `fx.register_music_provider`.
- characters: speaker/portrait lookup for NPC images (`chars.get`). Until characters exists, use placeholders.

## Tasks
- [ ] 1. **Graph definitions.** `world.add_space`, `world.add_place`, `world.add_location`, `world.add_connection` (two-way/one-way, requirements), `world.add_menu`; adjacency built at init; validator (developer mode): dangling connections, locations unreachable from the start location, missing background images. Done when: `world_test.rpy` declares a small two-space graph and the validator reports a planted dangling link and an unreachable location.
- [ ] 2. **Interactables.** `world.add_npc`, `world.add_object`; verbs → labels; `when` as `Req` or per-twin dict; z, pos, add-ons; one-appearance-per-character rule; `world.register_hidden_provider`. Done when: test shows an NPC appearing and disappearing by slot, and a hidden-provider hiding it.
- [ ] 3. **Per-twin state.** `world.here(twin=None)`, `world.go(location)` (emits `location_entered`), visited set, favourites; `ReqVisited(location)`; `core.register_save_info` adds the location name to save slots. Done when: the twins keep separate locations across swap and save/load.
- [ ] 4. **World view.** `screen world_view`: slot background, connection buttons (insensitive with a tooltip from `Req.describe()` when blocked), exit menus, interactables by z with add-ons, floating verb menu, Tab highlight, `use hud_root`; returns action tuples. Phone layout. Done when: test world is playable on PC and under phone emulation.
- [ ] 5. **World loop.** `label world_loop`, dispatch, content calls `from world_ret_content`, `world.register_entry_hook`, bookkeeping, `world.idle()`, `label world_swap`. Done when: saving inside content and inside the loop both load correctly; one rollback step undoes one action; swapping is blocked during content.
- [ ] 6. **Map and fast travel.** HUD panel `world_map_panel` (registered with `uix.register_hud_panel`): places and locations of the current space, markers from `world.register_marker_provider`, favourites, travel. Done when: travel works and a test marker shows.
- [ ] 7. **Music provider and prediction.** Register a music provider (track per location/place/slot from a table); predict neighbour backgrounds on entry (`start_predict`/`stop_predict` in pairs). Done when: moving between test locations changes music and shows no loading hitch.
- [ ] 8. **(needs user) Real world graph.** Enter the World graph (above) in `world_map_ini.rpy`: spaces, places, locations, connections. Agree ids, place grouping and button positions with the user (backgrounds come later; use placeholders). Done when: the validator passes on the real graph and every location is reachable from Home.
- [ ] 9. **(needs user) NPC schedules.** Ask the user for their schedule plan, write it into this Context, then build it (where each NPC is per slot and day, how `when` and priorities express it). Done when: test NPCs move between locations across slots as the plan says.
- [ ] 10. **Publish.** Print the world section for game/code/CLAUDE.md.

## API to publish
`world.add_space/add_place/add_location/add_connection/add_menu/add_npc/add_object`, `world.here`, `world.go`, `world.idle`, `ReqVisited`, `label world_loop`, `screen world_view`, `label world_swap`, the three hook registries, `world_map_panel`, signals `location_entered`, `interacted`, `content_finished`.
