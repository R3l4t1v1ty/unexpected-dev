# Unexpected: game code

Ren'Py 8.5 visual novel / sandbox for PC and Android, with twin protagonists Ayumu and Nemu. All game code lives in `game/code/`. Each subfolder owns one system and has its own CLAUDE.md (rules) and TASKS.md (context and task list). The full design is in `design/` at the project root. A session locked to a folder can't see it; what a folder needs is in its TASKS.md.

<!-- Update this table if folders change. -->
| Folder | Owns |
|---|---|
| `core/` | Definitions and registry, saved state `gs` and flags, twins, time, signals, `Req` conditions, saves and migrations, `label start` |
| `world/` | World mode: location graph, objects and NPCs, world view and loop, map and fast travel |
| `characters/` | Characters and speakers, encyclopedia, relationships (stats, statuses, activities) |
| `factions/` | Factions, reputation (per twin), quests |
| `events/` | Story events: lines, triggers, progress, event book, Story tab, replay |
| `rpg/` | Stats, abilities, items, gear, inventory, loot, crafting, currencies, shops, shared chest, gifts, combat numbers |
| `physics/` | Godot-style 2D math, collision and pathfinding (plain Python modules) |
| `adventure/` | Top-down adventure mode and its map maker (`editor_*.rpy`, not shipped) |
| `computer/` | In-game computer and GossipUp |
| `minigames/` | Loop puzzle, rune trace, minigame protocol |
| `progress/` | Achievements and gallery (per save) |
| `fx/` | Music and sound, camera transforms, reduced motion, fake loading, shader |
| `ui/` | gui.rpy, standard screens, main menu, say screen, game-menu tabs, HUD container, components |
| `story/` | The story (not started) |
| `dev/` | Debug tools, tests menu, validator, demo pack. Never shipped |

`options.rpy` (configuration and build settings) is the only file at this level.

## How Ren'Py treats these folders
- Ren'Py loads every `.rpy` file under `game/`, in every subfolder. Folders only organize the code; there are no imports between them.
- Labels, screens, images, transforms, styles and `define`/`default` names are global across all folders. A duplicate name either errors or silently replaces the other one, so check a name isn't taken before adding it.
- `init` code runs by priority, then by file path. Never rely on file names for order; use the init bands below.
- Never edit `.rpyc` files or anything in `game/cache/`. Ren'Py generates them. Ren'Py also loads a `.rpyc` that has no `.rpy`, so after moving or renaming a file, delete its old `.rpyc`.

## Working in one folder
When Claude is started inside one subfolder, it can only read and edit files in that folder. If a task needs a change in another folder, stop and say which file and what change, instead of working around the limit.

- **Publishing APIs.** When you add or change something other folders use (function, class, screen, label, signal, `Req`), finish by printing the exact lines to change in the Public API section below, and tick the task in your TASKS.md. You can't edit this file from a locked folder. The user applies the lines, or a session started in `game/code/` (not locked; the integration session) does.
- **Running the game.** Locked sessions can't run Ren'Py (it writes outside the folder). Ask the user to run, from the project root, `~/renpy-8.5.3-sdk/renpy.sh . lint` or `~/renpy-8.5.3-sdk/renpy.sh .`; phone layout with `RENPY_VARIANT="small phone touch android mobile"` in front.
- **Old code and reference files.** The old versions live outside the project, and the user's reference files (images, notes) are in `game/dev_resources/` (git-ignored, not shipped). A locked session can't read either: what a folder needs is transcribed into its TASKS.md. If you need more, ask the user to copy the file into your folder as `ref_*` (excluded from builds; delete when done).

Every folder under `game/code/` gets its lock, a starter CLAUDE.md and a starter TASKS.md from `.claude/sync-folders.py`. It runs by itself whenever `claude` starts from a terminal inside the project. After creating a folder in an unlocked session, run `python3 .claude/sync-folders.py` from `game/code/`. To change the lock for all folders, edit `.claude/folder-template/settings.json`, not the copies.

## Git
The git repo is the whole project folder (`unexpected-dev/`). A session locked to one folder can't see it, so git commands fail there with "not a git repository". That's expected: never run `git init` to fix it. Tell the user to commit from the project root instead.

## Shared rules

**State and saves**
- Definitions (locations, NPCs, characters, events, items…) are created at init in named stores with `_constant = True`, frozen at init 900, never changed afterwards, never saved. They pickle as `(kind, id)`.
- All mutable game state lives in `gs` (`default gs = core.GameState()`), through `core.flag`/`core.set_flag` and `core.state(system)`. Flags are sparse: only values that differ from the definition's template are stored.
- `gs` holds only `bool`/`int`/`float`/`str`/`None`/`tuple` and `list`/`dict`/`set` created in `.rpy` code. Never displayables, Characters, definitions, callables, or JSON/`.py`-module objects (convert first).
- Reading state never writes it (no `setdefault`). Screens never change state directly: use `core.StateAction(...)` or `Return` a tuple, or a load will undo the change.
- Screen arguments, `Return` values and `call` arguments are ids, not objects.
- Never mutate or rebind a `define`d or init-time object after init.
- Per-player settings (UI layout, textbox, accessibility) go in `persistent.<prefix>_*`, never in `gs`.

**Ids and names**
- Ids are ASCII `snake_case`, unique per kind, never shown to players, never renamed after a release (otherwise add to `core.RENAMES`). Location ids are `space.place.location`.
- Label names and asset paths come only from `core.label_for(kind, id, verb=None)` and `core.asset(kind, id, *parts)` (dots become `__` in labels; a Ren'Py label can't contain two dots).
- Visible text is `_()` literals; substitute with `[var]` or `__()`, never `_("…").format()`.
- Every global name starts with its folder's prefix: `core`, `world`, `chars`, `fac`, `events`, `rpg`, `uxphys_`, `adv`/`adventure_`, `pc`, `mini`, `prog`, `fx`, `uix`, `dev`. Exceptions: `gs`, `Req…` classes, Ren'Py's standard screen names, story speaker names.
- Never use these names: anything starting with `_`, `Condition`, `Gallery`, `achievement`, `ui`, `gui`, `audio`, `layout`, `config`, `style`, `map`, `filter`, `id`, `type`, `next`, `object`.

**Init order and files**
- Init bands: physics loader -600 · core -500 · ui registries and fx Python -400 · system classes -300 · styles, screens, content data 0 · wiring (signal connections, tab/panel registration) 100 · validate 900 · core freezes definitions 999. Use `init offset = N` per file. Styles and screens never below 0 (`gui.init` resets styles).
- File suffixes: `<topic>_py.rpy` classes · `<topic>_ini.rpy` content data · `<topic>_scr.rpy` screens · `<topic>.rpy` labels · `<topic>_test.rpy` tests with `label test_<folder>_<name>` (developer mode only; dev/'s test menu lists them; excluded from builds).

**Flow**
- Content labels (NPC/object verbs, events, adventure interactions) are `call`ed and must `return`. Never `jump` back to the world.
- Use `renpy.random`, never Python's `random`. Code with side effects checks `_in_replay`.
- Twins: never branch on twin names; per-twin differences are data keyed by `core.TWINS`. Time: 4 slots per day (0 morning, 1 afternoon, 2 evening, 3 night), days from 1, no weeks.
- Systems talk through signals (`core.connect`/`core.emit`) and registries, not by reaching into each other. Never emit signals from screens.
- Every signal is registered once, with `core.register_signal`, by the folder that emits it.

**Screens**
- Layout by variant: none = PC, `small` = phone, `medium` = tablet; input by `touch` (no hover-only actions, tap alternatives to drag). Never check `renpy.android`.
- Screens never loop over every definition; precompute. Budget < 5 ms per screen.
- Images ≤ 4096 px per side (adventure chunks ≤ 2048). No two files in `game/images/` may share a basename.

## Public API
What each folder offers the others. ○ planned (names may change until done) · ✔ done. Update by the publishing rule above.

**core**
- ✔ `gs`: the saved state (`core.GameState`, per-twin parts in `core.TwinState`). `core.Definition(id, template=None)`: base class for definitions; a subclass sets `kind`. Attributes `kind`, `id`, `template` (read-only dict of flag defaults: None/bool/int/float/str or tuples of those). Frozen after init.
- ✔ `core.register_kind(kind, per_twin, id_parts=1, asset_dir=None)` (`id_parts`: dot-separated parts in ids, 3 for locations; `asset_dir`: folder under images/, default the kind), `core.get(kind, id)`, `core.exists(kind, id)`, `core.all(kind)` (not in screens)
- ✔ `core.flag(kind, id, key, twin=None)`, `core.set_flag(kind, id, key, value, twin=None)`: twin None = current twin for per-twin kinds. `key` must be in the definition's template; values are None/bool/int/float/str or tuples of those
- ✔ `core.register_state(system, initial, per_twin, ids=None)`, `core.state(system, twin=None)`: a system's plain-data section of `gs` (a dict); missing sections and missing top-level keys are added from `initial` on load; `ids={key: kind}` marks the keys that hold ids, so renames reach them. `core.copy_plain(value)`: rollback-safe deep copy of plain data (e.g. from JSON)
- ✔ `core.TWINS`, `core.me()`, `core.other(twin=None)`, `core.swap(twin=None)`, `core.twin_name(twin=None)`
- ✔ `core.SLOTS` = `(0, 1, 2, 3)` with `core.MORNING`/`AFTERNOON`/`EVENING`/`NIGHT`, `core.day(twin=None)`, `core.slot(twin=None)`, `core.advance(slots=1)`, `core.sleep()`, `core.slot_name(slot)`; changes act on the current twin
- ✔ `core.register_signal(signal, *args)` (each folder registers the signals it emits, at init), `core.connect(signal, fn)` (at init only, band 100), `core.emit(signal, **kw)`
- ✔ `Req(text=None)` (`.check(twin=None)`, `.describe()`: player text, translated, or None; `.validate()`), `ReqAll`, `ReqAny`, `ReqNot`, `ReqFlag(kind, id, key, value=True)`, `ReqSlot(*slots)`, `ReqDay(min=None, max=None)`, `ReqTwin(twin)`; every Req takes `text=_("...")`; Reqs held by definitions are validated when init ends
- ✔ `core.StateAction(fn, *args, **kwargs)`, `core.label_for(kind, id, verb=None)` (e.g. `npc__hana__chat`, `location__town__home__living_room`), `core.asset(kind, id, *parts)` (`images/<asset_dir>/<id, dots as slashes>/<label name>__<parts>`, e.g. `images/world/town/home/living_room/location__town__home__living_room__bg_0.webp`)
- ✔ `core.SAVE_VERSION` (the highest migration number, set when init ends), `@core.migration(version)` (numbers from 2, unique across folders), `core.RENAMES = {kind: {old_id: new_id}}` (fill at init), `core.register_save_info(fn)` (fn() returns a dict of extra save JSON fields; core writes `version`, `twin`, `day`, `slot`); in developer mode, saving raises if `gs` holds anything but plain data
- ✔ `label start`: `core.new_game()` (sections, then `game_started`), then `world_loop` if it exists
- Signals: ✔ `game_started()`, `game_loaded()`, `time_changed(twin, day, slot)`, `twin_swapped(twin)`

**world**
- ○ `world.add_space/add_place/add_location/add_connection/add_menu/add_npc/add_object(...)`
- ○ `world.here(twin=None)`, `world.go(location)`, `world.idle()`, `ReqVisited(location)`
- ○ `label world_loop`, `screen world_view`, `label world_swap` (via `renpy.jump_out_of_context`, only when idle)
- ○ `world.register_entry_hook(fn)`, `world.register_hidden_provider(fn)`, `world.register_marker_provider(fn)`
- ○ HUD panel `world_map_panel`. Content labels: `core.label_for("npc"|"object", id, verb)`
- Signals: ○ `location_entered(twin, location)`, `interacted(twin, kind, target, verb)`, `content_finished(twin, kind, target, verb)`

**characters**
- ○ `chars.add(...)`, `chars.get(id)`, story speaker names (decided in characters task 1)
- ○ `chars.introduce(id)`, `chars.known(id, twin=None)`, `ReqKnown(id)`
- ○ Relationships (per twin; stats `friendliness`, `commitment`, `attraction` 0–100; ten statuses `acquaintances`, `friends`, `buddy`, `colleague`, `casual`, `lovers`, `fwb`, `romantic`, `platonic`, `soulmate`): `chars.add_relationship(char, twins)`, `chars.rel(char, stat, twin=None)`, `chars.add_rel(char, stat, amount)`, `chars.status(char, twin=None)`, `chars.tier(status)` (0 acquaintances; 1 friends/colleague/casual/buddy; 2 lovers/fwb/romantic/platonic; 3 soulmate), `chars.reached(char, status, twin=None)`, `chars.path(char, twin=None)` (statuses entered since the last reset), `chars.reset_rel(char)`, `chars.register_gain_modifier(fn)`, `ReqRel(char, stat, min)`, `ReqRelStatus(char, *statuses)`, `ReqRelReached(char, status)`, `ReqRelPath(char, *statuses)`. A relationship event can only be played after at least one of that character's events from the tier below (events/ enforces it)
- ○ Activities: `chars.add_activity(...)`, `chars.add_beat(...)`, `call chars_activity(activity_id)` (costs 1 slot)
- ○ `screen chars_encyclopedia`, `screen chars_page(char_id)`, `chars.register_page_section(id, screen)`
- Signals: ○ `character_introduced(twin, char)`, `relationship_changed(twin, char, stat, value)`, `relationship_status_changed(twin, char, status)`

**factions** (M3)
- ○ `fac.add(id, name, location, opens=Req)`, `fac.get(id)`, `fac.is_open(faction)`
- ○ `fac.rep(faction, twin=None)`, `fac.add_rep(faction, amount)`, `fac.tier(faction)`, `ReqRep(faction, tier)` (reputation is per twin)
- ○ Quests: `fac.add_quest(...)`, `fac.start(quest)`, `fac.complete_objective(quest, objective)`, `fac.turn_in(quest)`, `fac.quest_state(quest)`, `ReqQuest(quest, state)`, quest log screen
- Signals: ○ `faction_opened(twin, faction)`, `reputation_changed(twin, faction, value)`, `quest_started(twin, quest)`, `quest_completed(twin, quest)`

**events**
- ○ `events.add_line(...)`, `events.add(...)`; event labels `core.label_for("event", id)`
- ○ `events.available(twin=None)`, `events.done(id, twin=None)`, `events.start(id)`, `events.finish(id)`, `ReqEventDone(id)`
- ○ `events.completion(twin=None, char=None)`, `events.replay_action(id)`
- ○ `screen events_book(char_id)`, HUD panel `events_tracker_panel`, Story and Events tabs
- Signals: ○ `event_started(twin, event)`, `event_finished(twin, event)`

**rpg** (stats `str`, `int`, `dex`, `cha`; currencies `gold`, `yen`; all per twin)
- ○ `rpg.give(item, n=1)`, `rpg.take(item, n=1)`, `rpg.has(item, n=1)`, `ReqItem(item, n=1)`
- ○ `rpg.stat(stat, twin=None)` (base + gear + effects), `rpg.base(stat, twin=None)`, `rpg.train(stat, amount)`, `ReqStat(stat, min)`. Stat checks are fixed thresholds, no dice: gate a menu choice with `req=ReqStat(...)` (see ui)
- ○ `rpg.learn(ability)`, `rpg.empower(ability, upgrade)`, `rpg.knows(ability)`, `ReqAbility(ability)`, `rpg.set_weapon(weapon)`
- ○ `rpg.money(currency)`, `rpg.add_money(currency, n)`, `ReqMoney(currency, n)`
- ○ `call rpg_shop(shop_id)`, `call rpg_craft(station_id)`, `call rpg_chest`, `call rpg_gift(char_id)`, `rpg.learn_recipe(recipe)`, `rpg.roll_loot(table_id)`, `rpg.register_price_modifier(fn)`
- ○ HUD panels `rpg_inventory_panel`, `rpg_character_panel`; combat numbers for adventure (derived stats, ability data, damage)
- Signals: ○ `item_changed(twin, item, count)`, `stat_changed(twin, stat, value)`, `ability_learned(twin, ability)`, `item_crafted(twin, item, count)`

**physics** (`import uxphys_math` etc., after init -600; plain .py modules, physics objects are never saved)
- ✔ `uxphys_math`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D` (Godot 4.4), Godot helpers (`lerp`, `move_toward`, `clampf`, `snapped`, `lerp_angle`…)
- ✔ `uxphys_collide`: `CollisionGrid(columns, rows, cell_size, cells, terrains, outside)` with `Terrain(layer, speed)`: `add`, `remove`, `remove_owner`, `step()` once per tick, `raycast`, `intersect_point`, `intersect_shape`, `is_free`
- ✔ `uxphys_collide`: `RectShape`, `CircleShape`; `StaticBody`; `Body` (`velocity`, `move_and_slide(delta)`, `move_and_collide`, `get_slide_collision`); `Area` (signals `body_entered`, `body_exited`, `area_entered`, `area_exited`)
- ✔ `uxphys_path`: `astar`, `smooth_path`, `find_path` (tap-to-move), `segment_clear`

**adventure**
- ○ `call adventure(world_id, entry_id)`: runs adventure mode until the player leaves; `_return` says how
- ○ `adv.entity_type(name)`; adventure content labels `core.label_for("adv", id, verb)`
- ○ Map files under `game/maps/<world>/` (format v1, see adventure/)
- ○ A run costs 1 time slot; loot is kept on leaving or victory, lost on defeat
- Signals: ○ `adventure_entered(twin, world)`, `adventure_left(twin, world, how)`, quest-goal signals (boss defeated, place reached, thing found; names decided in adventure task 8)

**computer**
- ○ `call pc_open`, `pc.register_app(id, name, screen, requires=None)`, GossipUp definitions (after design)
- Signals: ○ `pc_notification(twin, app, text)`

**minigames**
- ○ `call minigame(kind, puzzle_id)`: `_return` is `"win"`, `"lose"` or `"skip"`. `mini.register(kind, screen)`, `persistent.mini_skip_allowed`

**progress**
- ○ `prog.add_gallery_set(...)`, `prog.gallery_unlocked(id)`, `prog.add_achievement(...)`, `prog.unlocked(id)`, `prog.claim(id)`
- Signals: ○ `achievement_unlocked(id)`

**fx**
- ○ `fx.music(key)`, `fx.ambient(key)`, `fx.stop_music()`, `fx.reconcile()`, `fx.register_music_provider(fn)`, `fx.sound(id)`
- ○ transforms `fx_zoom`, `fx_slide`, `fx_slide_zoom`, `fx_rotate`, `fx_blur`, `fx_shake`; `persistent.fx_reduced_motion`
- ○ `call fx_loading(tips=None)`, `fx.add_tip(text, group=None)`, `persistent.fx_fake_loading`, `fx_mirage`

**ui**
- ○ `uix.register_menu_tab(id, name, screen, order=100, requires=None)`, `uix.register_hud_panel(id, screen, name, order=100)`, `screen hud_root`
- ○ `uix.notify(text)`, components `uix_panel(title)` and friends, tap-to-place helper
- ○ Say screen: thought lines via `Character(..., show_thought=True)`
- ○ Choice screen: a choice with `req=` (any `Req`), e.g. `"Lift the beam" (req=ReqStat("str", 12)):`, shows greyed out with `req.describe()` when it fails; use `if` to hide a choice instead

**dev**: nothing; no folder may depend on dev/.
