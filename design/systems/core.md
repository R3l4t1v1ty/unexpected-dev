# core/

The foundation: how definitions and state are stored, ids, twins, time, signals, conditions, saving and loading, and the start label. core depends on no other folder. Everything else depends on it.

See [architecture.md](../architecture.md) §1–§7 for the rules; this page is the data model and the plan.

## Data model

```
gs = core.GameState()                     # the only saved object
  version      int                        # save format version (core.SAVE_VERSION at creation)
  twin         "ayumu" | "nemu"           # current twin
  shared       {"flags": {kind: {id: {key: value}}},  "sys": {system: {...}}}
  twins        {"ayumu": TwinState, "nemu": TwinState}

TwinState
  day          int  (1, 2, 3, …)
  slot         int  (0 morning, 1 afternoon, 2 evening, 3 night)
  flags        {kind: {id: {key: value}}}  # sparse: only values different from the template
  sys          {system: {...}}             # each system's own plain-data section
```

- **Definitions** (`core.Definition` subclasses) carry `kind`, `id`, and `template` (flag defaults). They register themselves on creation, are frozen at init 900, and pickle as `(kind, id)`.
- **Kinds** are registered with their scope: `core.register_kind("location", per_twin=True)`. Per-twin kinds read and write the current twin's flags unless a twin is given.
- **System sections** hold state that isn't a flag on a definition (current location, inventory, favourites…). A system registers its initial section: `core.register_state("world", initial=fn, per_twin=True)`. Sections are created at new game, and after loading a save that lacks them. Never on read.

## API (planned)

| Name | Purpose |
|---|---|
| `gs` | The saved state |
| `core.Definition` | Base class for all definitions |
| `core.register_kind(kind, per_twin)`, `core.get(kind, id)`, `core.exists(kind, id)`, `core.all(kind)` | Registry (`all` is not for screens) |
| `core.flag(kind, id, key, twin=None)`, `core.set_flag(kind, id, key, value, twin=None)` | Sparse flags |
| `core.register_state(system, initial, per_twin)`, `core.state(system, twin=None)` | Per-system plain-data sections |
| `core.TWINS`, `core.me()`, `core.other()`, `core.swap(twin=None)` | Twins |
| `core.SLOTS`, `core.day()`, `core.slot()`, `core.advance(slots=1)`, `core.sleep()`, `core.slot_name(slot)` | Time (current twin's clock) |
| `core.connect(signal, fn)`, `core.emit(signal, **kw)` | Signals |
| `Req`, `ReqAll`, `ReqAny`, `ReqNot`, `ReqFlag`, `ReqSlot`, `ReqDay`, `ReqTwin` | Conditions: `.check(twin=None)`, `.describe()` |
| `core.StateAction(fn, *args, **kwargs)` | Screen action that changes state and survives load |
| `core.label_for(kind, id, verb=None)`, `core.asset(kind, id, *parts)` | Label names and asset paths from ids |
| `core.SAVE_VERSION`, `core.migration(version)`, `core.RENAMES`, `core.register_save_info(fn)` | Saves and migrations |
| `label start` | New game: build state, emit `game_started`, go to `world_loop` if it exists |

Signals: `game_started()`, `game_loaded()`, `time_changed(twin, day, slot)`, `twin_swapped(twin)`.

## Decisions
- Time slots are 0-based everywhere; days start at 1; there are no weeks.
- `core.swap()` only changes `gs.twin` and emits `twin_swapped`. When swapping is allowed (only while the world is idle) is world's business.
- `label start` uses `renpy.has_label("world_loop")` so core doesn't depend on world; until world exists it shows a placeholder.
- Migrations: each save has `gs.version`; registered migrations run in order in an after-load callback; renamed ids are rewritten in flags and system sections; `renpy.block_rollback()` if anything changed.

## Open questions
None for now.
