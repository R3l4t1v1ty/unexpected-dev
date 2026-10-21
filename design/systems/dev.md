# dev/

Developer tools. **Never ships**: `build.classify('game/code/dev/', None)` excludes the whole folder, so nothing outside dev/ may reference a dev/ name.

## Tools
- **Test menu**: lists every `test_<folder>_<name>` label in the game (found with `renpy.get_all_labels()`), grouped by folder; opened from the main menu (developer mode only) and a hotkey.
- **Debug overlay**: current twin, day and slot, location; flag inspector (per kind/id); jump to location; set time; give item; start an event. Grows as systems land.
- **Content validator**: runs at init 900+ in developer mode and on demand. Checks:
  - labels referenced by definitions (verbs, events, adventure entities) exist
  - images referenced through `core.asset` exist
  - no two files under `game/images/` share a basename (Ren'Py's automatic image names use the basename; the first file wins silently)
  - each system's own validator runs (world's graph check, events' references)
- **Fixture saves**: plain-data snapshots of old `gs` shapes, run through core's migrations and compared with expected results, so a release can't break old saves unnoticed.
- **Profiler helpers**: toggle `config.profile_screens`, show adventure tick time.
- **Integration demo pack**: a small test game built in dev/ only from the public API in `game/code/CLAUDE.md`:
  - 1 space, about 6 locations
  - 2 characters
  - 3 events
  - a shop
  - an adventure entrance

  It proves the documented API is enough for a folder that can't see the implementation, which is exactly the situation story/ will be in.
