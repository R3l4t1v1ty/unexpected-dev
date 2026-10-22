# world/

World mode, the sandbox: the location graph, objects and NPCs, the world view, the world loop that runs content, the map and fast travel, and twin swapping.

## Model (kept from the old versions, made a real graph)

- **Location**: the smallest unit. Id `space.place.location`, e.g. `town.home.living_room`. Has a background per time slot (several slots may share one image), optional requirements, and its clickable objects and NPCs.
- **Place** (`town.home`) and **space** (`town`): grouping only, used by maps and music.
- **Connection**: a button on a location that moves you to another location. Declared explicitly, so any location can link to any other, across places and spaces (the old versions were trees: each location linked only to its parent). Two-way by default with a button position on each side; can be one-way; can have requirements; can have a button style (portals).
- **Exit menu**: a popup button grouping up to 4 connections (old `SBXMenu`, e.g. "Clubs").
- **NPC**: a character placed at a location with an activity, z-layer (0–9), position, verbs (chat, look, …), and when it's there (a `Req`, or a dict twin → `Req`). A character shows at most once in the whole world at a time; the highest priority wins (released game rule).
- **Object**: same, without a character (bed, computer, posters…).
- **Verbs** map to content labels by `core.label_for("npc"|"object", id, verb)`, e.g. `npc__hana_bench__chat`. One verb clicks straight through; several open the floating icon menu.

```
world.add_space("town", _("Town"))
world.add_place("town.home", _("Home"))
world.add_location("town.home.living_room", _("Living Room"), slots=(0, 0, 1, 2))   # bg per slot
world.add_connection("town.home.living_room", "town.home.hallway", pos=(475, 475), back_pos=(50, 550))
world.add_menu("town.school.yard", "clubs", _("Clubs"), pos=(1600, 450))
world.add_npc("hana_bench", character="hana", location="town.park.bench", activity="reading",
    z=5, pos=(903, 246), verbs=("chat", "look"), when=ReqAll(ReqSlot(0, 1), ReqEventDone("hana_1")))
world.add_object("ayumu_bed", location="town.home.ayumu_room", z=3, pos=(400, 700),
    verbs=("sleep",), when=ReqTwin("ayumu"))
```
(Exact signatures are decided in world task 1; this shows the shape.)

## State (per twin)
Current location, visited locations, favourite slots (4, unlocked over time), and flags on locations, objects and NPCs.

## The world loop
See [architecture.md](../architecture.md) §6. `call screen world_view` returns an action tuple (`("move", loc)`, `("interact", kind, id, verb)`, `("travel", loc)`…); content labels are called with `call expression … from world_ret_content` and return; then bookkeeping: signals, `fx.reconcile()`, autosave. Content changes time itself with `core.advance()` / `core.sleep()`.

Other folders hook in without world depending on them:
- `world.register_entry_hook(fn)`: on entering a location, returns a label to call (events uses it for auto-triggered events).
- `world.register_hidden_provider(fn)`: character ids to hide right now (events hides NPCs who are busy in a pending event).
- `world.register_marker_provider(fn)`: markers on the map (events: where pending events are; characters: where NPCs are).

## World view
Background for the slot, connection buttons (insensitive when requirements fail), exit menus, objects and NPCs by z-layer with bg/fg add-on images, floating verb menu, Tab highlights everything clickable for 1.5 s, the HUD (`use hud_root`). Phone layout: larger hit areas, tap instead of hover.

## Map and fast travel
A HUD panel: the current space's places and locations, markers from providers, favourites with fast travel.

## Prediction
On entering a location, predict neighbouring locations' backgrounds (`renpy.start_predict` / `renpy.stop_predict` in pairs).

## Validation (developer mode)
Dangling connections, locations unreachable from the start location, verbs without labels, missing background images.

## The real graph (from the user, 2026-10-23)
The user's image is `game/dev_resources/graph.png`. A text version, which the locked world session can read, is in `game/code/world/TASKS.md` under "World graph".
- **Spaces:** Henyutamei (the town) plus two new ones, Hell Citadel and Order HQ: 56 locations in all.
- **Hubs:** each space's node is a hub location linking to its places.
- **Connections:** every connection is two-way. Portals are ordinary connections between far-apart places, with a portal button style: Hana's ↔ Hell Citadel, Tamiko's ↔ Order HQ, and both hubs to Ruins of Silver Cities and Satyr Forest.
- **On the map:** 10 adventure entrances, 7 faction locations, 4 shops, 3 craft stations.
- **Sandbox activities:** repeatable mechanics not tied to an NPC, each different, with varied rewards: Wardrobe, Shapeshifting Statue, Passers-by, Slime Sandbox, Summoning Circle, Spa Day. Their mechanics are built later; world gives them a place as objects.
- **Relationship activities:** verbs on the NPC, only in their time slots. The graph leaves them off.
- **Training spots** (Gym, Library, Pool…) raise rpg stats through content.
- **Not in world mode for now:** the Shrine nodes, which come from the story.

## NPC schedules
NPCs follow schedules (where they are each slot). The user has a detailed plan and gives it to the world session that builds it (world task 9).

## Open questions
- Which space Ruins of Silver Cities and Satyr Forest belong to.
- The Shrine (a story element; how to include it later).
