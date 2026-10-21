# dev/

## Purpose
Developer and debug tools: the test menu, the debug overlay, the content validator, fixture-save checks, profiler helpers, and an integration demo pack built only from the public API.

## Rules
- Namespace `dev`; screens and labels `dev_*`.
- This folder is excluded from builds (`build.classify('game/code/dev/', None)` in options.rpy). Nothing outside dev/ may reference a dev/ name, and dev/ must not define anything saves depend on (no `default`s other folders read).
- Everything here is active only when `config.developer` is True.
- Use only the public API listed in game/code/CLAUDE.md. If something can't be done with it, report the missing API instead of working around it. That gap matters for story/ later.

@TASKS.md
