# Unexpected: game code

Ren'Py 8.5 visual novel / sandbox for PC and Android, with twin protagonists Ayumu and Nemu. All game code lives in `game/code/`. Each subfolder owns one system and has its own CLAUDE.md (rules) and TASKS.md (context and task list). The full design is in `design/` at the project root. A session locked to a folder can't see it; what a folder needs is in its TASKS.md.

<!-- Update this table if folders change. -->
| Folder | Owns |
|---|---|
| `core/` | Definitions and registry, saved state `gs` and flags, twins, time, signals, `Req` conditions, saves and migrations, `label start` |
| `world/` | World mode: location graph, objects and NPCs, world view and loop, map and fast travel |
| `characters/` | Characters and speakers, encyclopedia, factions and reputation, relationships |
| `events/` | Story events: lines, triggers, progress, event book, Story tab, replay |
| `rpg/` | Stats, items, gear, inventory, currencies, shops, progression, stat checks, combat rules |
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
- **Old code.** The old versions live outside the project. When porting, ask the user to copy the needed files into your folder as `ref_*.txt` (excluded from builds; delete them when done).

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
- Every global name starts with its folder's prefix: `core`, `world`, `chars`, `events`, `rpg`, `uxphys_`, `adv`/`adventure_`, `pc`, `mini`, `prog`, `fx`, `uix`, `dev`. Exceptions: `gs`, `Req…` classes, Ren'Py's standard screen names, story speaker names.
- Never use these names: anything starting with `_`, `Condition`, `Gallery`, `achievement`, `ui`, `gui`, `audio`, `layout`, `config`, `style`, `map`, `filter`, `id`, `type`, `next`, `object`.

**Init order and files**
- Init bands: physics loader -600 · core -500 · ui registries and fx Python -400 · system classes -300 · styles, screens, content data 0 · wiring (signal connections, tab/panel registration) 100 · freeze and validate 900. Use `init offset = N` per file. Styles and screens never below 0 (`gui.init` resets styles).
- File suffixes: `<topic>_py.rpy` classes · `<topic>_ini.rpy` content data · `<topic>_scr.rpy` screens · `<topic>.rpy` labels · `<topic>_test.rpy` tests with `label test_<folder>_<name>` (developer mode only; dev/'s test menu lists them; excluded from builds).

**Flow**
- Content labels (NPC/object verbs, events, adventure interactions) are `call`ed and must `return`. Never `jump` back to the world.
- Use `renpy.random`, never Python's `random`. Code with side effects checks `_in_replay`.
- Twins: never branch on twin names; per-twin differences are data keyed by `core.TWINS`. Time: 4 slots per day (0 morning, 1 afternoon, 2 evening, 3 night), days from 1, no weeks.
- Systems talk through signals (`core.connect`/`core.emit`) and registries, not by reaching into each other. Never emit signals from screens.

**Screens**
- Layout by variant: none = PC, `small` = phone, `medium` = tablet; input by `touch` (no hover-only actions, tap alternatives to drag). Never check `renpy.android`.
- Screens never loop over every definition; precompute. Budget < 5 ms per screen.
- Images ≤ 4096 px per side (adventure chunks ≤ 2048). No two files in `game/images/` may share a basename.

## Public API
What each folder offers the others. ○ planned (names may change until done) · ✔ done. Update by the publishing rule above.

**core**
- ○ `gs`: the saved state. `core.Definition`: base class for definitions (`kind`, `id`, `template`).
- ○ `core.register_kind(kind, per_twin)`, `core.get(kind, id)`, `core.exists(kind, id)`, `core.all(kind)` (not in screens)
- ○ `core.flag(kind, id, key, twin=None)`, `core.set_flag(kind, id, key, value, twin=None)`: twin None = current twin for per-twin kinds
- ○ `core.register_state(system, initial, per_twin)`, `core.state(system, twin=None)`: a system's plain-data section of `gs`
- ○ `core.TWINS`, `core.me()`, `core.other()`, `core.swap(twin=None)`
- ○ `core.SLOTS`, `core.day()`, `core.slot()`, `core.advance(slots=1)`, `core.sleep()`, `core.slot_name(slot)`
- ○ `core.connect(signal, fn)`, `core.emit(signal, **kw)`
- ○ `Req` (`.check(twin=None)`, `.describe()`), `ReqAll`, `ReqAny`, `ReqNot`, `ReqFlag(kind, id, key, value=True)`, `ReqSlot(*slots)`, `ReqDay(min=None, max=None)`, `ReqTwin(twin)`
- ○ `core.StateAction(fn, *args, **kwargs)`, `core.label_for(kind, id, verb=None)`, `core.asset(kind, id, *parts)`
- ○ `core.SAVE_VERSION`, `@core.migration(version)`, `core.RENAMES`, `core.register_save_info(fn)`
- ○ `label start`: new game, then `world_loop`
- Signals: ○ `game_started()`, `game_loaded()`, `time_changed(twin, day, slot)`, `twin_swapped(twin)`

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
- ○ `chars.add_faction(id, name)`, `chars.rep(faction)`, `chars.add_rep(faction, amount)`
- ○ `chars.rel(id, stat, twin=None)`, `chars.add_rel(id, stat, amount)`, `ReqRel(id, stat, min)` (skeleton until the relationship design)
- ○ `screen chars_encyclopedia`, `screen chars_page(char_id)`, `chars.register_page_section(id, screen)`
- Signals: ○ `character_introduced(twin, char)`, `relationship_changed(twin, char, stat, value)`, `reputation_changed(faction, value)`

**events**
- ○ `events.add_line(...)`, `events.add(...)`; event labels `core.label_for("event", id)`
- ○ `events.available(twin=None)`, `events.done(id, twin=None)`, `events.start(id)`, `events.finish(id)`, `ReqEventDone(id)`
- ○ `events.completion(twin=None, char=None)`, `events.replay_action(id)`
- ○ `screen events_book(char_id)`, HUD panel `events_tracker_panel`, Story and Events tabs
- Signals: ○ `event_started(twin, event)`, `event_finished(twin, event)`

**rpg** (shape depends on the RPG design)
- ○ `rpg.give(item, n=1)`, `rpg.take(item, n=1)`, `rpg.has(item, n=1)`, `ReqItem(item, n=1)`
- ○ `rpg.stat(name, twin=None)`, `rpg.check(stat, difficulty)`, `ReqStat(stat, min)`
- ○ `rpg.money(currency)`, `rpg.add_money(currency, n)`, `call rpg_shop(shop_id)`
- ○ HUD panels `rpg_inventory_panel`, `rpg_character_panel`; combat API for adventure
- Signals: ○ `item_changed(twin, item, count)`, `level_up(twin, level)`, `stat_checked(twin, stat, success)`

**physics** (`import uxphys_math` etc., after init -600)
- ○ `uxphys_math`: `Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`
- ○ `uxphys_collide`: `CollisionGrid`, `Body` (`move_and_slide`), `Area`, `raycast`
- ○ `uxphys_path`: `astar`, `smooth_path`

**adventure**
- ○ `call adventure(world_id, entry_id)`: runs adventure mode until the player leaves; `_return` says how
- ○ `adv.entity_type(name)`; adventure content labels `core.label_for("adv", id, verb)`
- ○ Map files under `game/maps/<world>/` (format v1, see adventure/)
- Signals: ○ `adventure_entered(twin, world)`, `adventure_left(twin, world, how)`

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

**dev**: nothing; no folder may depend on dev/.
