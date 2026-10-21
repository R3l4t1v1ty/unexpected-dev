# events/

## Purpose
Story events: event lines and their order, triggers, per-twin progress, the event book, the event tracker, the Story tab (twin swap and completion), and replay.

## Rules
- Namespace `events`; screens `events_*`. Event labels come from `core.label_for("event", id)` and must `return`.
- Classes at init -300, data and screens at 0, hook/tab/panel registration at 100.
- Conditions are `Req` objects (`ReqEventDone`, `ReqAll`, `ReqAny`…). Don't invent a second condition system.
- Progress is per twin. Replay must never change real progress: check `_in_replay`.
- events plugs into world, characters and ui through their registries; it never edits their files.

@TASKS.md
