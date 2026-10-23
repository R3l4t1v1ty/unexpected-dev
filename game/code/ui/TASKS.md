# ui/ tasks

Milestones: tasks 1–4 in **M1**, the rest in **M2**.

## Status (2026-10-24)
Tasks 1–11 done: the user ran lint and every `test_ui_*` label, the main menu and the quick menu, on PC and under phone emulation, and all work. Task 11's API lines are printed for game/code/CLAUDE.md. Left: task 12 (clean up, waits on the asset layout and URLs) and the open questions below.

## Files
| File | What |
|---|---|
| `gui.rpy` | Ren'Py's gui settings (init -2, NVL settings removed) |
| `theme_ini.rpy` | Colors and every ui asset (placeholders), init -400 |
| `styles_scr.rpy` | Base styles (default, button, bars, frame) |
| `menu_py.rpy`, `menu_scr.rpy`, `menu_ini.rpy` | Tab registry, `uix.MenuTab`, the `uix_menu` shell, `uix_scroll`; ui's own tabs |
| `saveload_scr.rpy`, `history_scr.rpy`, `help_scr.rpy`, `about_scr.rpy`, `prefs_py.rpy`, `prefs_scr.rpy` | The standard screens (Ren'Py names kept as entry points) and their tab pages |
| `say_py.rpy`, `say_ini.rpy`, `say_scr.rpy` | Textbox skins and settings; say, input, preview |
| `choice_scr.rpy` | Choice screen with `req=` |
| `quick_menu_scr.rpy` | Quick menu, PC and touch |
| `main_menu_py.rpy`, `main_menu_ini.rpy`, `main_menu_scr.rpy` | Main menu data API, placeholder content, screen |
| `notify_py.rpy`, `components_scr.rpy`, `overlays_scr.rpy` | Toasts, shared components, confirm/skip/notify |
| `hud_py.rpy`, `hud_scr.rpy` | HUD registry and `hud_root` |
| `ui_test.rpy` | `test_ui_menu`, `test_ui_hud`, `test_ui_say`, `test_ui_choice`, `test_ui_components` |

## Context
- `gui.rpy` and `screens.rpy` came from game/code/ as Ren'Py 8.5 defaults (1920×1080). `screens.rpy` is now split into the files above and deleted.
- Tab pages and HUD panel screens are *used* screens: their own `default` variables change with `SetLocalVariable`/`LocalVariableValue`. `SetScreenVariable` sets the outer screen's variable instead.
- `FileAction` picks save or load from the screen name, which is `uix_menu` here, so the slots use `FileSave`/`FileLoad` explicitly.
- HUD selection (tap-to-place) lives in the top-level screen's scope (`uix_hud_sel`), read and written only through `uix.hud_*` functions. That works whether `hud_root` is shown or used inside another screen.
- In drags, child widgets win focus over the drag itself, so buttons inside a window or the version box work. A drag remembers its position until its `pos` changes; dropped items snap back to their start and the redraw puts them where the state says.
- Systems own their gameplay screens and plug into ui:
  - Game-menu tabs: `uix.register_menu_tab(id, name, screen, order=100, requires=None, group="story", main_menu=False, pc_only=False)`. Expected tabs: Story (events: twin swap + completion %), Characters, Events, Gallery, Achievements, plus the standard Save/Load/Preferences/History/Help.
  - HUD panels: `uix.register_hud_panel(id, screen, name, order=100, size=(600, 400), drop=None)`; the panel screen takes `(panel, part)`, see hud_py.rpy. `hud_root` is one screen with a `draggroup` that includes each panel with `use`. Verified in the SDK: children of a `use`d screen are added directly to the enclosing draggroup (the used screen's context shares the parent's children list), so drag-and-drop between panels works with each panel in its own file. The old game had one 2,300-line HUD screen because of this; don't repeat it.
- Screen-variant names Ren'Py sets: PC `large pc`; phone `small phone touch android mobile`; tablet `medium tablet touch android mobile`. Lay out with `small`/`medium` (none = PC), handle input with `touch`. Test phone layout from the project root with `RENPY_VARIANT="small phone touch android mobile"`.
- Thought lines: a Character made with `show_thought=True` passes `thought=True` to the say screen (Ren'Py passes every `show_*` argument through).
- Old say screen to recreate: 3 skins (Simple, Side-Fade, Fancy), persistent sliders for opacity, width, height, text size, name/text outline, each with a Reset button.
- Old main menu: mouse parallax on a background plus 9 floating images bobbing with ATL, hover arrows and sound, social links (Discord, Patreon, Twitter, itch), version box. It was copy-pasted per image; make it data-driven, with a touch fallback.
- Changing state from a screen needs `core.StateAction` (or a `Return` tuple), or a load undoes it.
- `ref_old_screens.txt` in this folder: rebuild #2's screens (all of its `screens/` plus its sandbox HUD overlay), with an index saying which task or folder each part belongs to now. Reference only; delete it when ui/ is done.

## Decisions (2026-10-23)
- Styles: keep Ren'Py's standard style names (screens and `gui.*_properties` look them up by name); `uix_` only for styles ui adds.
- No NVL mode and no built-in speech bubbles: their screens, styles and settings are removed. Custom bubbles may come later as a new task.
- Init: ui styles and screens at `init offset = 0` like everyone else; `gui.rpy` stays at -2 (it calls `gui.init`).
- Layouts: phone (`small`) has its own layout; tablet (`medium`) uses the PC layout with touch-sized hit areas.
- Game menu (from the old game): left sidebar with the tab title on top and Close at the bottom. Tabs belong to a group: `story` (registered by systems: Story, Characters, Events, Gallery, Achievements) or `system` (ui's: History, Save, Load, Preferences, Help, About). The sidebar shows the current group plus one button to switch. From the main menu only system tabs that make sense there (Load, Preferences, About, Help). Help and Quit on PC only. In a replay the story group is hidden and End Replay appears. Sub-pages are not hidden tabs: an action opens a tab with arguments for its screen.
- Quick menu: a Story button opens the story group on the `story` tab (hidden when nothing registered it). No Game button.
- Main menu: keep the art-set picker (choice saved in `persistent`), the changelog panel, hide-UI toggle, hover arrows (also on keyboard focus), version box. Link URLs: none yet, the user adds new ones later (don't reuse the old ones).
- Assets: placeholders until the user decides the asset layout; every ui asset path is defined in one place so it's easy to move.
- HUD: ui only provides `hud_root`; world/ decides when it shows. Panel positions saved per layout (PC, phone, tablet). On phone panels dock to the left or right half, at most two open; on PC/tablet they float and drag.
- Text size: the Textbox tab's slider is dialogue text only; Accessibility's is Ren'Py's global font scale.
- `uix.notify` replaces the stock notify screen, so `renpy.notify` goes through the toast queue too.
- Language tab lists the translations found in `game/tl/`, hidden when there's only one language.

## Uses
- core: `core.StateAction`, `Req…`, `core.me()`.
- fx: `persistent.fx_reduced_motion`, `persistent.fx_fake_loading` (preferences toggles).
- minigames: `persistent.mini_skip_allowed` (preferences toggle).

## Tasks
- [x] 1. **Tidy the standard screens.** Split `screens.rpy` into topic files (`menus_scr.rpy`, `say_scr.rpy`, `saveload_scr.rpy`, `prefs_scr.rpy`, …), keep Ren'Py's screen names, rename custom styles to `uix_*`, remove the starter comments that don't help. Done when: lint is clean and the game looks the same.
- [x] 2. **Variants.** `small` and `medium` layouts for the standard screens and gui sizes; touch-friendly hit areas. Done when: every standard screen is usable under phone emulation.
- [x] 3. **Game-menu shell and tab registry.** `uix.register_menu_tab`; tabs sorted by order, hidden when `requires` fails; standard screens shown as tabs inside the shell. Done when: a test tab registered from `ui_test.rpy` appears and opens.
- [x] 4. **HUD.** `hud_root` with a draggroup; `uix.register_hud_panel`; open/close and positions saved in `persistent`; a tap-to-select/tap-to-place helper for touch. Done when: two test panels exist and a test item drags from one to the other with the mouse, and moves by tapping under touch emulation.
- [x] 5. **Say screen.** `thought` parameter, 3 skins, sliders with Reset in preferences. Done when: a test label shows normal and thought lines in each skin.
- [x] 6. **Components.** `uix_panel(title)`, buttons, tooltip, confirm, toast queue `uix.notify(text)`. Done when: test label shows each.
- [x] 7. **Preferences.** Tabs: General, Textbox, Accessibility (reduced motion, fake loading, minigame skip, text size), Language. Done when: toggles change the persistent values.
- [x] 8. **Main menu.** Data-driven parallax layers and floating items, touch fallback, links, version. Needs art from the user (placeholders until then). Done when: runs on PC and under phone emulation.
- [x] 9. **Quick menu.** PC and touch versions with a Story button opening the game menu on the `story` tab (no Game button; touch keeps Menu). Done when: both versions work.
- [x] 10. **Choice screen with requirements.** A menu choice may carry `req=` (any `Req`), e.g. `"Lift the beam" (req=ReqStat("str", 12)):`. Ren'Py passes per-choice arguments to `screen choice` as `i.kwargs` (checked in the 8.5 SDK, renpy/exports/menuexports.py). When `i.kwargs["req"].check()` fails, show the choice greyed out and insensitive, with `req.describe()` beside it ("Strength 12"); choices without `req` work as usual. Done when: a test menu shows a met and an unmet requirement on PC and phone, and the unmet one can't be picked by mouse, keyboard or touch.
- [x] 11. **Publish.** Print the ui section for game/code/CLAUDE.md. (Printed 2026-10-23 and 2026-10-24 for the user to apply.)
- [ ] 12. **Clean up.** Delete `ref_old_screens.txt`; swap placeholders for art once the asset layout is decided (all in `theme_ini.rpy` and `main_menu_ini.rpy`); add the real link URLs.

## Open questions
- The old main menu had unused Nemu/Ayumu toggles. They're rebuilt as optional toggle layers plus hotspots (`toggle=` on a layer, `uix.add_main_menu_hotspot`). Confirm that's what they were for.
- Custom speech bubbles (future task).

## API to publish
`uix.register_menu_tab`, `uix.register_hud_panel`, `hud_root`, `uix.notify`, components, tap-to-place helper, say-screen thought support, choice `req=` support.
