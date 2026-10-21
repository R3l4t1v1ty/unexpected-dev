# dev/ tasks

Milestones: tasks 1–3 in **M1**, then grows with each system. The demo pack (task 6) is in **M2**.

## Context
- Locked Claude sessions can't run Ren'Py, so the tools here are what the user (or a root session) runs to check work.
- Every folder writes tests as `label test_<folder>_<name>` in `*_test.rpy` files (developer mode only, excluded from builds). The test menu finds them all, so dev/ never needs editing when a folder adds tests.
- Ren'Py's automatic image names use the file's basename, and the first file found wins without warning. Duplicate basenames under `game/images/` must be caught.
- The demo pack is built only from the public API in game/code/CLAUDE.md. If dev/ can't build something from that list alone, the list is missing something, and story/ will hit the same gap later.

## Uses
Only public API from game/code/CLAUDE.md: core (flags, registry, `me()`, `swap`, time, `Req`, `label_for`, `asset`, migrations), world (`here`, `go`, definitions), events, rpg, characters, ui (`uix.register_menu_tab`, components), adventure (`call adventure`).

## Tasks
- [ ] 1. **Test menu.** Screen listing all `test_*` labels grouped by folder (`renpy.get_all_labels()`), opened from a main-menu button and a hotkey, both only when `config.developer`. Done when: core's and ui's test labels appear and run.
- [ ] 2. **Debug overlay.** Toggle with a hotkey: twin, day/slot, location (when world exists), flag inspector by kind and id, set time, swap twin; later: jump to location, give item, start event. Done when: shows and edits core state; edits survive save/load.
- [ ] 3. **Content validator.** On demand and at init 900+ in developer mode: missing labels for definitions, missing images from `core.asset`, duplicate basenames under `game/images/`, plus each system's validator. Done when: planted mistakes in a test file are all reported.
- [ ] 4. **Fixture saves.** Store plain-data snapshots of old `gs` shapes; run core's migrations on them; compare with expected results. Done when: a fixture from the first save version passes after a test migration.
- [ ] 5. **Profiler helpers.** Toggle `config.profile_screens`; show adventure tick time (once adventure exists). Done when: toggles work.
- [ ] 6. **Integration demo pack (M2).** Using only the public API: 1 space with about 6 locations, 2 characters, 3 events, a shop (after rpg), an adventure entrance (after adventure). List every API gap found. Done when: the demo plays start to finish for both twins and the gaps are reported.
- [ ] 7. **Publish.** dev/ publishes no API; just confirm the `test_<folder>_*` convention is in game/code/CLAUDE.md.
