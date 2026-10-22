# characters/

## Purpose
Character definitions and the speaker objects story uses, the encyclopedia screens, and the relationship system (stats, statuses, activities).

## Rules
- Namespace `chars`; screens `chars_*`. Speaker store names for story are the one exception, decided in task 1 and listed in game/code/CLAUDE.md.
- Classes at init -300, character data and screens at 0, tab registration at 100.
- Introduced state, outfits seen and relationship values are per twin.
- Encyclopedia UI state (zoom, selected outfit, filter) lives in screen variables, never in `gs`.
- characters doesn't reference events or rpg. They plug in through `chars.register_gain_modifier` and `chars.register_page_section`; events/ enforces the relationship tier rule for its own events.

@TASKS.md
