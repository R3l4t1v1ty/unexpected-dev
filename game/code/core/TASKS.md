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
- [ ] 1. **Stores and Definition base.** `core.Definition` with `kind`, `id`, `template`; registers itself; `__reduce__` returns `(core.defref, (kind, id))`; frozen at init 900 (setting attributes raises in developer mode). Done when: a test label shows that pickling a definition gives its id, and mutating one after init raises.
- [ ] 2. **Registry.** `core.register_kind(kind, per_twin)`, `core.get`, `core.exists`, `core.all`. Id validation: ASCII snake_case, dotted for kind `location` (`space.place.location`); duplicate ids raise at init with a clear message. Done when: test covers good ids, bad ids, duplicates, unknown ids.
- [ ] 3. **GameState and flags.** `GameState`, `TwinState`; `core.flag(kind, id, key, twin=None)` returns the stored value or the template default; `core.set_flag(...)` stores only values that differ from the template (setting a value back to the default removes it). Shared vs per-twin by kind. Done when: test round-trips a save/load with flags set; reading unset flags adds nothing to `gs`.
- [ ] 4. **System sections.** `core.register_state(system, initial, per_twin)`, `core.state(system, twin=None)`; sections created at new game and by an after-load callback when missing. Done when: test registers a section, saves, adds a second section in code, loads, both exist.
- [ ] 5. **Twins.** `core.TWINS`, `core.me()`, `core.other()`, `core.swap(twin=None)` emitting `twin_swapped`. Done when: test.
- [ ] 6. **Time.** `core.SLOTS`, `core.day()`, `core.slot()`, `core.advance(slots=1)` (rolls over into following days), `core.sleep()` (next day, slot 0), `core.slot_name(slot)` (translated). All act on the current twin; emit `time_changed(twin, day, slot)`. Done when: test, including advancing across several days.
- [ ] 7. **Signals.** `core.connect(signal, fn)`, `core.emit(signal, **kw)`; handlers kept in the constant store; in developer mode an exception in a handler propagates, in release it's logged and the rest still run. Done when: test.
- [ ] 8. **Req.** `Req` base with `check(twin=None)` and `describe()`; `ReqAll`, `ReqAny`, `ReqNot`, `ReqFlag(kind, id, key, value=True)`, `ReqSlot(*slots)`, `ReqDay(min=None, max=None)`, `ReqTwin(twin)`. No side effects. Done when: truth-table test.
- [ ] 9. **Saves and migrations.** `core.SAVE_VERSION`; `gs.version`; `@core.migration(version)` functions run in order in an after-load callback; `core.RENAMES = {kind: {old_id: new_id}}` applied to flags and sections; `renpy.block_rollback()` if anything changed; `config.save_json_callbacks` writes version, twin, day, slot plus extra fields from `core.register_save_info(fn)` (world adds the location). Emit `game_loaded`. Done when: a test builds an old-shaped `gs`, runs the migrations and checks the result.
- [ ] 10. **Helpers.** `core.StateAction(fn, *args, **kwargs)` (runs `fn`, calls `renpy.retain_after_load()`, restarts the interaction); `core.label_for(kind, id, verb=None)` → e.g. `npc__hana__chat`, `event__hana_1`, `location__town__home__living_room`; `core.asset(kind, id, *parts)` → e.g. `images/world/town/home/living_room/bg_0.webp` (path scheme per kind, documented in game/code/CLAUDE.md). Done when: test screen changes a flag through `StateAction`, save, load, the change is kept.
- [ ] 11. **Start.** Replace the Ren'Py placeholder in `start.rpy`: `label start` builds the state sections, emits `game_started`, jumps to `world_loop` if `renpy.has_label("world_loop")`, otherwise shows a simple placeholder. Done when: New Game reaches the placeholder.
- [ ] 12. **Publish.** Print the final core section for game/code/CLAUDE.md (mark each name ✔).

## API to publish
Everything listed under "core" in game/code/CLAUDE.md. Update it if names change.
