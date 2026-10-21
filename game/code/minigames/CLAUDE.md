# minigames/

## Purpose
Minigames called from content through one protocol: the loop puzzle and the rune trace from the released game, and any new ones.

## Rules
- Namespace `mini`; screens and labels `mini_*`, plus the shared entry label `minigame`.
- Every minigame follows the protocol: `call minigame(kind, puzzle_id)` returns `"win"`, `"lose"` or `"skip"` in `_return`. Kinds register with `mini.register(kind, screen)`.
- Every minigame works with touch (drag, tap); never rely on hover.
- Every minigame can be skipped when `persistent.mini_skip_allowed` is on.
- Puzzle data are definitions; a minigame's in-progress state stays in the screen and is not saved (a load restarts the minigame).

@TASKS.md
