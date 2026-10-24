# dev/ tasks

Milestones: tasks 1–3 in **M1**, then grows with each system. The demo pack (task 6) is in **M2**.

## Context
- Locked Claude sessions can't run Ren'Py, so the tools here are what the user (or a root session) runs to check work.
- Every folder writes tests as `label test_<folder>_<name>` in `*_test.rpy` files (developer mode only, excluded from builds). The test menu finds them all, so dev/ never needs editing when a folder adds tests.
- Ren'Py's automatic image names use the file's basename, and the first file found wins without warning. Duplicate basenames under `game/images/` must be caught.
- The demo pack is built only from the public API in game/code/CLAUDE.md. If dev/ can't build something from that list alone, the list is missing something, and story/ will hit the same gap later.
- How tests behave (from core's and ui's test files): core's tests check things and show their own report screen; ui's tests need the player (menus, HUD drags, say lines). Both expect to be `call`ed in a started game and end with `return`. A test passes if it returns; it may return a string, shown as its note. A failure is an exception on Ren'Py's error screen.

## Files
- `tools_py.rpy` shared helpers (`dev.on()`, text escaping, `dev.literal`, `dev.SetComputed`); `tools_scr.rpy` dev styles.
- `tests_py.rpy`, `tests.rpy`, `tests_scr.rpy`: test menu. A run keeps the label in `persistent.dev_pending_test` and calls `renpy.full_restart(label="dev_run_test")`, so every test starts from a new game (`core.new_game()`). Results of this session are in `persistent.dev_test_runs` (reset at init). Tab `dev_tests` (group "story", also on the main menu), Shift+T.
- `overlay_py.rpy`, `overlay_scr.rpy`: debug overlay (`config.overlay_screens`, F9; open state in `persistent.dev_overlay_open`).
- `profiler_py.rpy`: the overlay's Profile tab (screen times through `renpy.profile_screen`, slow frames through `config.profile`; settings in `persistent.dev_timed_screens`, `dev_profile_detail`, `dev_profile_frames`, applied at init).
- `validator_py.rpy`, `validator_scr.rpy`, `validator_test.rpy`: content check, lint hook, planted mistakes (`persistent.dev_plant`), `test_dev_validator`.
- `fixtures_py.rpy`, `fixtures_scr.rpy`, `fixtures_test.rpy`: fixture saves (Check, Accept, Record in the test menu), `test_dev_fixtures`, `test_dev_fixture_migration`. The fixtures themselves are `fixtures/<name>.txt`: a Python literal `{"recorded", "accepted", "data", "expected"}`, read and written with plain file access (dev/ only runs from source).

## Uses
Only public API from game/code/CLAUDE.md: core (`run_validators`, flags, registry, `me()`, `swap`, time, `Req`, `label_for`, `asset`, `snapshot`, `migrate`, `copy_plain`, `SAVE_VERSION`), world (`here`, `go`, definitions), events, rpg, characters, ui (`uix.register_menu_tab`, components), adventure (`call adventure`).

## Tasks
- [x] 1. **Test menu.** Screen listing all `test_*` labels grouped by folder (`renpy.get_all_labels()`), opened from a main-menu button and a hotkey, both only when `config.developer`. Done when: core's and ui's test labels appear and run.
  - Built and checked 2026-10-24.
- [x] 2. **Debug overlay.** Toggle with a hotkey: twin, day/slot, location (when world exists), flag and section inspector (pick a kind from `core.kinds()`, then an id from `core.all(kind)`, keys from its `template`; sections from `core.systems()`; `core.per_twin`/`core.system_per_twin` say whether to show one twin or shared; these lookups come with core task 14, until then type the kind by hand), set time, swap twin; later: jump to location, give item, start event. Done when: shows and edits core state; edits survive save/load.
  - Built and checked 2026-10-24. Time only goes forward (no `core.set_time`, by decision). Core task 14 exists now: kinds and sections are picked from `core.kinds()`/`core.systems()`, the twin choice uses `core.per_twin`/`core.system_per_twin`, and typing a kind or section by hand is gone.
  - Still to do: the location line (`world.here()`); swap through `world_swap` and grey out swap/time while not `world.idle()`, once world/ exists.
- [x] 3. **Content validator** (needs core task 13). dev/ can't know which labels or images a system needs, so each system registers its own check with `core.register_validator`. dev/ runs `core.run_validators()` plus its own duplicate image name check, and shows the report in two places: the test menu, and lint through `config.lint_hooks` (lint runs after init, so every definition exists). Duplicate rule, from Ren'Py's image scan: the name is the file's basename, lowercased, extension dropped, and anything from `@` on dropped (`bg@2.png` is `bg`); folders don't count; the first file found wins without a warning. Report any two files under `game/images/` that get the same name. Done when: a planted missing label, missing asset and pair of clashing files all show up in the menu and in lint.
  - Built and checked 2026-10-24: the planted missing label, missing image and image clash show in the menu, in lint and in `test_dev_validator`. If its note ever says FAILED, it quotes dev/'s report lines. The planted files aren't real files: they're added to the list the check reads, since dev/ can't write under game/images/.
- [x] 4. **Fixture saves.** Store plain-data snapshots of old `gs` shapes; run core's migrations on them; compare with expected results. Done when: a fixture from the first save version passes after a test migration.
  - Built 2026-10-24 on core task 15 (`core.snapshot()`, `core.migrate(data, migrations=None, renames=None)`). Fixtures are recorded from a game (Tests > Fixture saves > Record this game), never written by hand. Check runs each through `core.migrate` and lists problems (shape, plain data, version not `core.SAVE_VERSION`, a registered section missing) and differences from the expected result; Accept makes the current result the expected one once the differences are right. dev/ never registers a migration (that would raise `core.SAVE_VERSION` in developer runs only); the test migration goes through `migrations=`.
  - The test migration changes nothing: migrations get a `core.GameState`, whose attributes aren't in the public API. It checks that the migration runs once, the version goes up by one, made-up sections (`dev_fixture`) are kept and nothing else changes. Logic checked outside Ren'Py against a stand-in core.
  - Checked 2026-10-24 with new-game fixtures from save version 1: `test_dev_fixture_migration` and `test_dev_fixtures` pass.
  - Keep doing: record fixtures before every change to the save format, including one from a game with more state once world/ and the content folders exist. Commit `dev/fixtures/` with them.
- [x] 5. **Profiler helpers.** Toggle `config.profile_screens`; show adventure tick time (once adventure exists). Done when: toggles work.
  - Built 2026-10-24 (overlay tab Profile, `profiler_py.rpy`): tap a screen to time it (shown-now screens are listed, others typed), Detail, Slow frames, Frame graph (Ren'Py's F3 screen, so phone layouts get it too). Uses `renpy.profile_screen` rather than `config.profile_screens`: the config list only logs how statements were evaluated, without the screen's name or time; Detail turns that same output on. A screen that's already showing starts being timed the next time it's shown (Ren'Py looks the profile up when a screen is shown). Output is buffered: profile_screen.txt is complete once Ren'Py quits.
  - Checked 2026-10-24: timing `say` writes SHOW/UPDATE lines with times to profile_screen.txt, and Detail adds the statement lines.
  - Still to do: show adventure tick time, once adventure/ exists.
- [ ] 6. **Integration demo pack (M2).** Using only the public API: 1 space with about 6 locations, 2 characters, 3 events, a shop (after rpg), an adventure entrance (after adventure). List every API gap found. Done when: the demo plays start to finish for both twins and the gaps are reported.
- [x] 7. **Publish.** dev/ publishes no API; just confirm the `test_<folder>_*` convention is in game/code/CLAUDE.md. Confirmed 2026-10-24 (Init order and files).
