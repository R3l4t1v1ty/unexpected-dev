# world/ tasks

Milestone: **M2**.

## Context
Kept from the old versions, but as a real graph:
- **Location**: smallest unit, id `space.place.location` (e.g. `town.home.living_room`). Background per time slot (slots 0–3 may share images), optional requirements (enforced; rebuild #2 stored them but never checked them), objects and NPCs.
- **Place** (`town.home`) and **space** (`town`): grouping only (maps, music).
- **Connection**: a button that moves you to another location. Declared explicitly; any location may link to any other, across places and spaces. Old versions were trees (each location linked only to its parent; don't do that). Two-way by default with a button position on each side; optional one-way; optional requirements.
- **Exit menu**: one button opening a popup of up to 4 connections.
- **NPC**: character at a location with activity, z-layer 0–9, position, verbs, `when` (a `Req` or a dict twin → `Req`), priority. A character appears at most once in the world at a time (highest priority wins).
- **Object**: like an NPC without a character.
- **Verbs** → content labels via `core.label_for(kind, id, verb)`. One verb: click runs it. Several: a floating icon menu.
- Optional bg/fg add-on images per interactable (drawn behind/in front).
- Tab highlights every clickable thing for 1.5 s.
- Per twin: current location, visited set, favourites (4 slots, unlocked over time), flags on locations/objects/NPCs.
- The world will grow a lot: two new whole spaces and cross-space connections. The user has a visual graph and will provide it.

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
- [ ] 8. **(needs user) Real world graph.** Enter the user's graph in `world_map_ini.rpy` (spaces, places, locations, connections, button positions). Done when: validator passes on the real graph.
- [ ] 9. **Publish.** Print the world section for game/code/CLAUDE.md.

## API to publish
`world.add_space/add_place/add_location/add_connection/add_menu/add_npc/add_object`, `world.here`, `world.go`, `world.idle`, `ReqVisited`, `label world_loop`, `screen world_view`, `label world_swap`, the three hook registries, `world_map_panel`, signals `location_entered`, `interacted`, `content_finished`.
