# progress/

## Purpose
Achievements and the gallery (reward gallery and L.E.W.D. picture sets). Both are per save.

## Rules
- Namespace `prog`; screens `prog_*`. Never use the store names `achievement` or `Gallery` (Ren'Py owns them).
- Classes at init -300, data and screens at 0, signal connections and tab registration at 100.
- Unlocks and achievement progress live in `gs` (per save, shared between twins), never in `persistent`.
- Achievements learn about the game only through signals and `Req`s; progress/ never edits other folders.
- Nothing unlocks during a replay (`_in_replay`).

@TASKS.md
