# minigames/ tasks

Milestone: **M5** (only needs core and ui, so it can start any time after M1).

## Context
From the released game (its files are outside this folder; ask the user to copy them in as `ref_*.txt` when porting):
- **Loop puzzle** (`loopylooploop_py.rpy`): rotate tiles until pipes form closed loops. `LoopyTilesetGenerator` grew a random ~50%-filled grid; `LoopyTile` shapes 0–4; `is_solved()` checked completion. Its screen lived in story code (`the map/5. delving inside.rpy`).
- **Rune trace** (`core/rpg/rpg char/abilities/minigame/`): get from a Start circle to an End circle without touching the rune symbol image (`focus_mask`); a `VFXFireTrail` displayable draws a fire trail with particles behind the pointer. It started on hovering "Start" and failed on hovering the symbol. Hover is unreliable on Android touch, so the new version is drag-based. Old bugs: the `vfx` parameter was ignored, labels defaulted to `"x"`, one puzzle's position was a list.

Protocol (shared with all minigames): `call minigame(kind, puzzle_id)` → `_return` is `"win"`, `"lose"` or `"skip"`.

## Uses
- core: `Definition`, registry, `asset`.
- ui: components, phone layout rules; preferences shows `persistent.mini_skip_allowed`.
- fx: transitions, `persistent.fx_reduced_motion` (tone down particles).

## Tasks
- [ ] 1. **Protocol.** `label minigame(kind, puzzle_id)`, `mini.register(kind, screen)`, `default persistent.mini_skip_allowed = False`, a skip button when allowed. Done when: a trivial test minigame returns each result.
- [ ] 2. **Loop puzzle.** Generator, tiles, solved check, screen with tap-to-rotate, phone layout; puzzle definitions (size, seed, fill). Done when: generated puzzles are always solvable (test with a solver) and playable on both layouts.
- [ ] 3. **Rune trace.** Drag from Start to End, fail on touching the symbol (mask), cached fire-trail displayable (lighter with reduced motion); puzzle definitions (rune image, start, end). Done when: playable with mouse and under touch emulation.
- [ ] 4. **Publish.** Print the minigames section for game/code/CLAUDE.md.

## API to publish
`call minigame(kind, puzzle_id)` and its results, `mini.register`, puzzle definition functions, `persistent.mini_skip_allowed`.
