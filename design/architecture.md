# Architecture

The rules every system follows. The condensed version that Claude sessions load lives in `game/code/CLAUDE.md` under "Shared rules"; when you change a rule here, change it there too.

Ren'Py behaviour quoted here was checked against the Ren'Py 8.5.3 SDK source (`~/renpy-8.5.3-sdk`).

## 1. Definitions vs state (how saving works)

The game is split into two kinds of data:

| | Definitions | State |
|---|---|---|
| What | Locations, connections, objects, NPCs, characters, events, items, shops, achievements, gallery sets, map index… | Everything that changes while playing: flags, current twin, clocks, locations, inventory, relationship values… |
| Created | At init, from code | During play |
| Lives in | Named stores with `_constant = True` (`init -500 python in core:` … `_constant = True`) | One saved object: `default gs = core.GameState()` |
| Saved? | Never. Ren'Py skips constant stores for rollback, backup and saving | Yes, and nothing else is |
| After an update | Always the new code | Kept; new flags take template defaults |

This is the "rebuild the game on load and fill in the flags from the save" idea: definitions are rebuilt from code on every launch, so the save only has to carry flags.

Rules:
- **Definitions never change after init.** A Definition is frozen when init ends (setting an attribute raises in developer mode). Mutating an init-time object after init is wrong twice over: Ren'Py doesn't roll the change back, and it isn't reset by New Game, Load or Replay, so it leaks between saves in one session.
- **Never rebind a `define`d name.** `define` also marks the name constant for screen optimisation, so screens would show stale values.
- **Definitions pickle as ids.** The Definition base class implements `__reduce__` returning `(core.defref, (kind, id))`. Any stray reference that ends up in `gs`, a screen scope or a `Return` value is saved as an id and resolves to the current definition on load.
- **`gs` holds only plain data**: `bool`, `int`, `float`, `str`, `None`, `tuple`, and `list`/`dict`/`set` created in `.rpy` code (those are Ren'Py's revertable versions, so rollback works). Never displayables, `Character`s, definitions, callables, or JSON-loaded or `.py`-module objects (convert those to plain .rpy containers first).
- **At most ~3 classes are reachable from `gs`** (`GameState`, `TwinState`, maybe one more), defined in core with names frozen forever. Saves refer to classes by name, so renaming one breaks every save.
- **Flags are sparse.** Each definition declares a template of flag defaults. `gs` stores only values that differ from the template, as `flags[kind][id] = {key: value}`. Content added in an update reaches old saves automatically; removed content is ignored.
- **Reads never write.** No `setdefault`, no "create the entry on first read". Screens run during prediction and must not change state, and a `RevertableDict` copies itself on its first change after each checkpoint.
- **Shared vs per-twin.** `gs.shared.flags` holds world-wide flags; `gs.twins["ayumu"].flags` / `gs.twins["nemu"].flags` hold per-twin flags. Each definition kind declares which scope it uses when it registers.

### Changing state from screens
Ren'Py rolls back to the start of the current statement when a save is loaded, unless `renpy.retain_after_load()` was called. So a change made by a screen button (equip an item by drag, swap twin from the menu, read a chat on the computer, adventure position) is lost on load, and on Android's background autosave, unless:
- the button uses `core.StateAction(fn, *args)`, which runs `fn` and calls `renpy.retain_after_load()`, or
- the screen `Return`s a tuple and the label that called it makes the change.

Screen arguments, `Return` values and `call` arguments are ids, never objects: screen scopes and call arguments are saved.

### Loading and migrations
Load order in Ren'Py: roll back to the last checkpoint → run `default`s for variables missing from the save, then `config.after_default_callbacks` → run `config.after_load_callbacks` in list order → the `after_load` label.

- Migrations run in a core after-load callback. Each save stores `gs.version`. Migrations are small functions registered per version step; a rename table (`core.RENAMES`) maps old ids to new ones.
- If a migration changed anything, call `renpy.block_rollback()`: rollback entries from before the load still hold the old shapes.
- `config.save_json_callbacks` writes version, twin, day and location into each save's metadata, so save slots can show them and incompatible saves can be detected before loading.
- **After the first public release, commit `.rpyc` files.** They hold the statement identities that let saves load after the script is edited. `.gitignore` currently ignores them, which is fine until then.

## 2. Ids, names and assets

- **Ids** are ASCII `snake_case`, unique per kind, never shown to players, and **never renamed after a release** (if unavoidable, add the rename to `core.RENAMES`).
- **Location ids** are dotted: `space.place.location`, e.g. `town.home.living_room`. Spaces are `town`, places `town.home`.
- **Display names** are separate, translatable `_()` literals.
- **Label names** come only from `core.label_for(kind, id, verb=None)`. A Ren'Py label may contain at most one dot (`a.b` is a local label), so dots become `__`: the "chat" label of NPC `hana` is `npc__hana__chat`; the label of event `hana_1` is `event__hana_1`.
- **Asset paths** come only from `core.asset(kind, id, *parts)`, which builds paths like `images/world/town/home/living_room/bg_0.webp`. One helper per kind keeps the naming in one place, and the dev validator checks every path that definitions reference.
- **Reserved names.** Don't create store names that start with `_`, or that Ren'Py or Python already use: `Condition` (layered images assign it), `Gallery`, `achievement`, `ui`, `gui`, `audio`, `layout`, `config`, `style`, `map`, `filter`, `id`, `type`, `next`, `object`. That's why the condition language is `Req…` and the ui namespace is `uix`.
- **Namespaces.** Each folder owns one named store / prefix:

| Folder | Namespace / prefix |
|---|---|
| core | `core` (+ global `Req…` base classes, `gs`) |
| world | `world` |
| characters | `chars` |
| events | `events` |
| rpg | `rpg` |
| physics | `uxphys_*` Python modules |
| adventure | `adv` |
| computer | `pc` |
| minigames | `mini` |
| progress | `prog` |
| fx | `fx` (transforms `fx_*`) |
| ui | `uix` (styles `uix_*`) |
| dev | `dev` |

Screens, labels, transforms and styles are global in Ren'Py, so their names start with the folder prefix too (`world_view`, `chars_page`, `fx_shake`), except the standard Ren'Py screens that ui/ owns (`say`, `choice`, `main_menu`, …).

## 3. Conditions: `Req`

One condition language for everything that asks "is this allowed now?": location and connection requirements, NPC schedules, event triggers, shop stock, achievement goals, dialogue options.

- Base class `Req` with `check(twin) -> bool` and `describe() -> str` (for hints and tooltips). Requirements have no side effects and never write state.
- core provides: `ReqAll(*reqs)`, `ReqAny(*reqs)`, `ReqNot(req)`, `ReqFlag(kind, id, key, value=True)`, `ReqSlot(*slots)`, `ReqDay(min=None, max=None)`, `ReqTwin(twin)`.
- Other folders add their own: `ReqVisited` (world), `ReqEventDone` (events), `ReqRel`, `ReqKnown` (characters), `ReqItem`, `ReqStat` (rpg).
- `Req…` classes are global names (not namespaced) because content uses them constantly.

## 4. Signals

A small synchronous publish/subscribe in core, Godot-flavoured: `core.connect("location_entered", fn)` at init, `core.emit("location_entered", twin=..., location=...)` from game code.

- Handlers are registered at init (priority 100, "wiring") and live in the constant store. Never store callables in `gs`.
- Never emit from screens (screens are re-evaluated and predicted). Emit from labels and from functions called by labels or `StateAction`.
- Signals keep locked folders decoupled: achievements listen to everything, events listen to location and time, music listens to location and time, and none of them need the emitter's code.
- Every signal and its arguments is listed in `game/code/CLAUDE.md`.

## 5. Twins and time

- `core.TWINS = ("ayumu", "nemu")`. `gs.twin` is the current twin. Code never branches on twin names; per-twin differences go in data tables keyed by twin id.
- Shared between twins: the world graph, characters, factions and reputation, gallery, achievements.
- Separate per twin: clock, current location, favourite locations, event progress, location/object/NPC flags, relationship values, RPG character (stats, gear, inventory), computer.
- Each twin has its own clock: `day` (1, 2, 3, …) and `slot` (0 morning, 1 afternoon, 2 evening, 3 night). **No weeks.** Slots are 0-based everywhere. `core.advance(n)` moves forward n slots, `core.sleep()` moves to the next morning; both emit `time_changed`.
- Swapping twins happens from the game menu only while the world loop is idle (not during content). It uses `renpy.jump_out_of_context("world_swap")`.

## 6. Flow: the world loop

```
label world_loop:
    # bookkeeping: events that trigger here, music, prediction
    call screen world_view            # returns ("move", loc_id) / ("interact", target_id, verb) / ...
    # handle the action; content labels are called:
    call expression target from world_ret_content
    # after content: time cost, signals, renpy.force_autosave()
    jump world_loop
```

- `call screen` checkpoints with its return value, so each world action is one rollback step. Return values are plain tuples of ids.
- Content labels are called and must `return`. They never `jump` back to the world. `from world_ret_content` gives the return point a stable name so saves taken inside content survive script edits.
- Music, ambience and prediction are recomputed from state on each pass instead of being tracked, so they survive rollback and load.
- Use `renpy.random` only (it rolls back correctly), never Python's `random`.
- Adventure mode uses the same shape: `call screen adventure_view` returns actions such as `("talk", npc_id)`.

## 7. Replay (gallery and event book)

- `Replay(label, scope=..., locked=...)` starts with a fresh `gs` (Ren'Py resets the store and runs `default`s), then applies `scope`.
- Scope keys can be dotted attribute paths (`{"gs.twin": "nemu"}`); dictionary items can't be set this way.
- `config.start_callbacks` run inside the replay after the scope is applied; events/ hooks its replay setup there.
- Because unlocks are per save, always pass `locked=` explicitly (the default uses Ren'Py's global seen-label data).
- Code with side effects (achievements, signals, autosave) checks `_in_replay` and does nothing during a replay.

## 8. Screens and UI

- **ui/ owns the framework**: `gui.rpy`, the standard screens (say, choice, menus, save/load, preferences, history…), the main menu, the say screen with its skins, the game-menu tab registry, the HUD container, reusable components and styles.
- **Each system owns its gameplay screens** (world view, encyclopedia, inventory panel, computer, minigames…) and plugs into ui through registries: `uix.register_menu_tab(...)`, `uix.register_hud_panel(...)`.
- **HUD:** `hud_root` is one screen with a `draggroup`. Each panel is its own screen in its own folder, included with `use`. Verified in the SDK: children of a `use`d screen are added straight into the enclosing draggroup, so drag-and-drop between panels works while each panel stays in its own file. On touch devices panels also support tap-to-select, tap-to-place.
- **Screen variants.** Ren'Py sets these automatically:

| Device | Variants |
|---|---|
| PC | `large pc` |
| Android phone | `small phone touch android mobile` |
| Android tablet | `medium tablet touch android mobile` |

  Choose layouts by `small` / `medium` (no variant = PC), choose input behaviour by `touch`. Never check `renpy.android` (it ignores emulation). Emulate a phone with `RENPY_VARIANT="small phone touch android mobile"`.
- **Thought lines:** `Character(..., show_thought=True)` passes `thought=True` to the say screen (Ren'Py passes every `show_*` argument through), replacing the old `"___"` name prefix.
- **Styles and screens at init priority ≥ 0.** `gui.rpy` runs at offset -2 and `gui.init` resets all styles.
- **Visible text** is `_()` literals; format with `[var]` substitution or `__()`, never `_("…").format()`.
- **Performance:** no loops over all definitions inside screens; precompute per location. Check with `config.profile_screens` (budget: < 5 ms per screen).

## 9. Init priorities and files

| Priority | What |
|---|---|
| -600 | physics loader (`renpy.add_python_directory`, imports) |
| -500 | core |
| -400 | ui registries, fx Python |
| -300 | system classes (`*_py.rpy`) |
| 0 | styles, screens, content data (`*_ini.rpy`) |
| 100 | wiring: signal connections, tab and panel registration |
| 900 | freeze definitions, validate (developer mode) |

Your code can use -999…999; Ren'Py's own code sits outside that range. Use `init offset = N` at the top of a file instead of numbering each block.

File suffixes inside every folder:

| Suffix | Contents |
|---|---|
| `<topic>_py.rpy` | classes and functions |
| `<topic>_ini.rpy` | content data (definitions) |
| `<topic>_scr.rpy` | screens |
| `<topic>.rpy` | labels |
| `<topic>_test.rpy` | tests: `label test_<folder>_<name>` (developer mode only, excluded from builds) |

## 10. Physics as plain Python

The physics library (`game/code/physics/`) is plain `.py` modules, not `.rpy`:
- Loaded with `renpy.add_python_directory("code/physics/")` at init -600 and imported as `import uxphys_math` etc. Never import it through a package path (`code.physics…`): a `.py` file under `game/code/` would otherwise make Ren'Py's importer treat `code` as a package, which shadows Python's standard `code` module and duplicates classes.
- `.py` modules don't get Ren'Py's rollback rewriting, so per-frame physics objects cost nothing extra.
- `config.reload_modules.append(...)` makes Shift+R reload them.
- Unit tests run outside Ren'Py: `cd game/code/physics && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest`. Write Python 3.12-compatible code (the SDK bundles 3.12).
- Files stay flat in `physics/` (no subfolders), because every subfolder would get its own Claude lock.

In adventure mode, per-frame objects defined in `.rpy` derive from `python_object` instead of the store's `object`: store objects log every attribute change for rollback.

## 11. Testing

- Every folder writes `*_test.rpy` files with `label test_<folder>_<name>` (guarded by `config.developer`). dev/ has a test menu that lists every `test_*` label automatically.
- dev/ also has a debug overlay, a content validator, a fixture-save runner and an integration demo pack. The demo pack is written in dev/ using only the API listed in `game/code/CLAUDE.md`, the same way story/ will later. If dev/ can't build something from that API alone, the API list is incomplete.
- **Locked sessions can't run Ren'Py** (it writes to `game/cache/` and `log.txt`, outside their folder). Lint and play from the project root:
  - `~/renpy-8.5.3-sdk/renpy.sh . lint`
  - `~/renpy-8.5.3-sdk/renpy.sh .`
  - phone layout: `RENPY_VARIANT="small phone touch android mobile" ~/renpy-8.5.3-sdk/renpy.sh .`

## 12. Platforms, assets and performance

- **Android size.** An APK or Play bundle holds at most 2 GB (a bundle is four 500 MB packs; each file goes into one pack, every RPA archive must stay under 500 MB). With 4–5 GB of assets this needs a decision in M1: Ren'Py's Downloader for Large Games (the released game already had an "Unexpected Downloader" project), or a reduced Android asset set.
- **Textures.** Keep every image ≤ 4096 px per side (Android's limit). Adventure rooms are cut into chunks of ≤ 2048 px.
- **Asset names** come from ids (section 2). Formats: WebP/AVIF for images, webm video at most 1080p (720p for Android). No two images may share a basename under `game/images/` (Ren'Py's automatic image names use the basename and the first file wins silently); the dev validator checks this.
- **Memory:** watch `config.image_cache_size_mb` (default 400) and webm decoding on Android.
- **Prediction:** the world predicts neighbouring locations' backgrounds with `renpy.start_predict(...)` and always pairs it with `renpy.stop_predict(...)` (the prediction set is saved).
- **Budgets:** screens < 5 ms; adventure tick < 4 ms; no redraws while nothing moves.
- **Accessibility:** reduced-motion setting read live from `persistent`, skip option for minigames, readable at larger text sizes, colour-blind-safe bars and highlights.
- **Translation:** all visible text through `_()`; a language picker in preferences.

## 13. Working with locked folders

- Each folder under `game/code/` is one system. A Claude session started inside it sees only that folder and the CLAUDE.md files above it (`game/code/CLAUDE.md`). It can't read `design/`, sibling folders, or edit files outside its folder.
- So each folder's `TASKS.md` is self-contained (it repeats the design details the folder needs), and every public API (functions, classes, screens, labels, signals) is listed in `game/code/CLAUDE.md`.
- When a locked session adds or changes something another folder uses, it finishes by printing the exact lines to add to `game/code/CLAUDE.md`, and ticks the task in its own `TASKS.md`. Apply those lines from a session started in `game/code/` (that folder isn't locked; it's the integration session) or by hand.
- Cross-folder wiring that needs edits in several folders is done from the integration session.
- Git works only from the project root.
