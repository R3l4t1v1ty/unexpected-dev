# core/ tasks

Milestone: **M1** (first folder to build).

## Context
The old versions saved the whole game (`default game = deepcopy(base)`) and needed hand-written merge code after every update. This rebuild splits data in two:
- **Definitions** (locations, NPCs, characters, events, items…) are built at init in constant stores, frozen at init 900, never saved. They always come from current code.
- **State** lives in one saved object, `default gs = core.GameState()`, holding only plain data. Flags are sparse: `flags[kind][id] = {key: value}`, only values that differ from the definition's template. New content reaches old saves automatically.

```
gs
  version   int
  twin      "ayumu" | "nemu"
  shared    {"flags": {kind: {id: {key: value}}}, "sys": {system: {...}}}
  twins     {"ayumu": TwinState, "nemu": TwinState}
TwinState
  day int (from 1), slot int (0 morning, 1 afternoon, 2 evening, 3 night)
  flags {kind: {id: {key: value}}}
  sys   {system: {...}}       # per-system plain data, e.g. world's current location
```

Ren'Py facts this relies on (checked in the 8.5.3 SDK):
- Named stores with `_constant = True` are skipped by rollback, backup and save.
- Objects created at init and mutated later are neither saved nor rolled back, and leak across saves in a session. So definitions must be frozen.
- In `.rpy` code `object`, `dict`, `list`, `set` are revertable (rollback-safe). JSON-loaded data and `.py`-module objects are not; convert before storing in `gs`.
- `RevertableDict.setdefault` counts as a change; screens run during prediction. So reads never write.
- On load Ren'Py rolls back to the start of the current statement unless `renpy.retain_after_load()` was called. Screen buttons that change state need `StateAction`.
- Load order: `default`s for missing variables → `config.after_default_callbacks` → `config.after_load_callbacks` (in order) → `after_load` label.
- A label name may contain at most one dot, so ids with dots map to `__` in label names.
- Don't use the name `Condition` (layered images assign `store.Condition`), nor `Gallery`, `achievement`, `ui`, `gui`, `audio`, `layout`, `map`, `id`, `type`.

Twins: `("ayumu", "nemu")`. Never branch on twin names; per-twin differences are data. Each twin has its own clock. No weeks, just days.

## Uses
Nothing from other folders.

## Tasks
- [x] 1. **Stores and Definition base.** `core.Definition` with `kind`, `id`, `template`; registers itself; `__reduce__` returns `(core.defref, (kind, id))`; frozen at the very end of init, init 999, so other folders' init 900 code can still finish its definitions whatever the folder order (setting attributes raises in developer mode). Done when: a test label shows that pickling a definition gives its id, and mutating one after init raises.
- [x] 2. **Registry.** `core.register_kind(kind, per_twin, id_parts=1)`, `core.get`, `core.exists`, `core.all`. Id validation: ASCII snake_case, `id_parts` dot-separated parts (3 for `location`: `space.place.location`, so core never names other folders' kinds); duplicate ids raise at init with a clear message. Done when: test covers good ids, bad ids, duplicates, unknown ids.
- [x] 3. **GameState and flags.** `GameState`, `TwinState`; `core.flag(kind, id, key, twin=None)` returns the stored value or the template default; `core.set_flag(...)` stores only values that differ from the template (setting a value back to the default removes it). Shared vs per-twin by kind. Flag keys must be keys of the definition's template (typos raise); values are None/bool/int/float/str/tuples. Done when: test round-trips a save/load with flags set; reading unset flags adds nothing to `gs`.
- [x] 4. **System sections.** `core.register_state(system, initial, per_twin)`, `core.state(system, twin=None)`; `initial` is a dict of plain data; sections created at new game and by an after-load callback when missing, and missing top-level keys are filled from `initial` on load. Done when: test registers a section, saves, adds a second section in code, loads, both exist.
- [x] 5. **Twins.** `core.TWINS`, `core.me()`, `core.other(twin=None)`, `core.swap(twin=None)` emitting `twin_swapped` (swapping to the current twin does nothing). Done when: test.
- [x] 6. **Time.** `core.SLOTS` (`(0, 1, 2, 3)`, also `core.MORNING`/`AFTERNOON`/`EVENING`/`NIGHT`), `core.day(twin=None)`, `core.slot(twin=None)`, `core.advance(slots=1)` (rolls over into following days), `core.sleep()` (next day, slot 0), `core.slot_name(slot)` (translated). All act on the current twin; emit `time_changed(twin, day, slot)`. Done when: test, including advancing across several days.
- [x] 7. **Signals.** `core.register_signal(signal, *args)` (every signal is registered with its argument names, so typos raise: connecting to an unregistered signal raises at the end of init, and in developer mode `emit` checks the signal and its arguments), `core.connect(signal, fn)` (at init only), `core.emit(signal, **kw)`; handlers kept in the constant store; in developer mode an exception in a handler propagates, in release it's logged and the rest still run. Done when: test.
- [x] 8. **Req.** `Req` base with `check(twin=None)` and `describe()`; `ReqAll`, `ReqAny`, `ReqNot`, `ReqFlag(kind, id, key, value=True)`, `ReqSlot(*slots)`, `ReqDay(min=None, max=None)`, `ReqTwin(twin)`. No side effects. Every Req takes `text=`; `describe()` returns that text translated, or text made from slots/days/twin (`core.twin_name`), or None. `validate()` lists bad references; the Reqs held by definitions are validated when init ends. Done when: truth-table test.
- [x] 9. **Saves and migrations.** `core.SAVE_VERSION` (the highest migration number, set when init ends, so other folders add migrations without touching core); `gs.version`; `@core.migration(version)` functions run in order in an after-load callback; `core.RENAMES = {kind: {old_id: new_id}}` applied to flags and to section keys declared with `register_state(..., ids={key: kind})`, checked when init ends; `renpy.block_rollback()` if anything changed; `config.save_json_callbacks` writes version, twin, day, slot plus extra fields from `core.register_save_info(fn)` (world adds the location); in developer mode saving raises if `gs` holds anything but plain, rollback-safe data. Emit `game_loaded`. Done when: a test builds an old-shaped `gs`, runs the migrations and checks the result.
- [x] 10. **Helpers.** `core.StateAction(fn, *args, **kwargs)` (runs `fn`, calls `renpy.retain_after_load()`, restarts the interaction); `core.label_for(kind, id, verb=None)` → e.g. `npc__hana__chat`, `event__hana_1`, `location__town__home__living_room`; `core.asset(kind, id, *parts)` → `images/<asset_dir>/<id, dots as slashes>/<label_for(kind, id)>__<parts joined by __>`, e.g. `images/world/town/home/living_room/location__town__home__living_room__bg_0.webp` (the label name in the file name keeps basenames unique across images/, as the shared rules require); `asset_dir` is set by `register_kind(..., asset_dir=None)` (default: the kind). Both take unregistered kinds too (adventure entities from map files), and the definition needn't exist. Done when: test screen changes a flag through `StateAction`, save, load, the change is kept.
- [x] 11. **Start.** Replace the Ren'Py placeholder in `start.rpy`: `label start` calls `core.new_game()` (builds the state sections, emits `game_started`), jumps to `world_loop` if `renpy.has_label("world_loop")`, otherwise shows a simple placeholder. Done when: New Game reaches the placeholder.
- [x] 12. **Publish.** Print the final core section for game/code/CLAUDE.md (mark each name ✔).

## API to publish
Everything listed under "core" in game/code/CLAUDE.md. Update it if names change.
