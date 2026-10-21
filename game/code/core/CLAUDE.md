# core/

## Purpose
The foundation every other folder builds on: definitions and the registry, the saved state `gs` and its flags, twins, time, signals, the `Req` condition language, saving/loading/migrations, label and asset naming, and `label start`.

## Rules
- Namespace: `init python in core:` stores with `_constant = True` for definitions, the registry and signal handlers. Global names owned here: `gs` and the `Req…` base classes.
- core depends on no other folder. Never reference names from world/, events/, ui/ or anything else; other folders plug in through registries and signals.
- Init priority -500 for core code (use `init offset = -500`). The freeze-and-validate step runs at 900.
- Classes reachable from `gs` (`GameState`, `TwinState`) are pickled by name: never rename them, never add more without a very good reason.
- `gs` holds only plain data (see Shared rules in game/code/CLAUDE.md). Reading state never writes it.
- Everything other folders may use goes in the core section of game/code/CLAUDE.md.

@TASKS.md
