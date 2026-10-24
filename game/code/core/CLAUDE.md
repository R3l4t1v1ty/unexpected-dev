# core/

## Purpose
The foundation every other folder builds on: definitions and the registry, the saved state `gs` and its flags, twins, time, signals, the `Req` condition language, saving/loading/migrations, label and asset naming, and `label start`.

## Rules
- Namespace: `init python in core:` stores with `_constant = True` for definitions, the registry and signal handlers. Global names owned here: `gs` and the `Req…` base classes.
- core depends on no other folder. Never reference names from world/, events/, ui/ or anything else; other folders plug in through registries and signals.
- Init priority -500 for core code (use `init offset = -500`). `freeze()` (registry_py.rpy) runs at 999, after other folders' init 900 validation.
- Classes reachable from `gs` (`GameState`, `TwinState`) are pickled by name: never rename them, never add more without a very good reason.
- `gs` holds only plain data (see Shared rules in game/code/CLAUDE.md). Reading state never writes it.
- Everything other folders may use goes in the core section of game/code/CLAUDE.md.
- All core files run at init -500, in file-name order, sharing the `core` store. At -500 a file only defines names and never calls into another core file; cross-file checks run in `freeze()` at init 999. `core.all` hides Python's `all()` in the core store: use `builtins.all()`.
- Ren'Py rewrites names starting with `__` into file-private names (`_m1_<file>__x`), even inside string literals in Python blocks. Never start a string with `__` followed by a letter or digit: build such names with `"__".join(...)`. Dunders like `__init__` are left alone.
- Containers made at runtime that must be rollback-safe come from literals in .rpy code or `copy_plain`; use `builtins.dict/list/set` only for type checks and for data that is never saved.
- Tests: `jump test_core_all` runs every test that needs no save/load. Two need one and are run on their own: `test_core_state` (save, restart, load, then `test_core_state_loaded`) and `test_core_state_action`. Test kinds, sections, signals and validators are named `core_test*`. Test validators report problems only while their test runs, so dev/'s validator report stays clean.

@TASKS.md
