# ui/ tasks

Milestones: tasks 1–4 in **M1**, the rest in **M2**.

## Context
- `gui.rpy` and `screens.rpy` were moved here from game/code/ unchanged (Ren'Py 8.5 defaults, 1920×1080).
- Systems own their gameplay screens and plug into ui:
  - Game-menu tabs: `uix.register_menu_tab(id, name, screen, order=100, requires=None)`. Expected tabs: Story (events: twin swap + completion %), Characters, Events, Gallery, Achievements, plus the standard Save/Load/Preferences/History/Help.
  - HUD panels: `uix.register_hud_panel(id, screen, name, order=100)`. `hud_root` is one screen with a `draggroup` that includes each panel with `use`. Verified in the SDK: children of a `use`d screen are added directly to the enclosing draggroup (the used screen's context shares the parent's children list), so drag-and-drop between panels works with each panel in its own file. The old game had one 2,300-line HUD screen because of this; don't repeat it.
- Screen-variant names Ren'Py sets: PC `large pc`; phone `small phone touch android mobile`; tablet `medium tablet touch android mobile`. Lay out with `small`/`medium` (none = PC), handle input with `touch`. Test phone layout from the project root with `RENPY_VARIANT="small phone touch android mobile"`.
- Thought lines: a Character made with `show_thought=True` passes `thought=True` to the say screen (Ren'Py passes every `show_*` argument through).
- Old say screen to recreate: 3 skins (Simple, Side-Fade, Fancy), persistent sliders for opacity, width, height, text size, name/text outline, each with a Reset button.
- Old main menu: mouse parallax on a background plus 9 floating images bobbing with ATL, hover arrows and sound, social links (Discord, Patreon, Twitter, itch), version box. It was copy-pasted per image; make it data-driven, with a touch fallback.
- Changing state from a screen needs `core.StateAction` (or a `Return` tuple), or a load undoes it.

## Uses
- core: `core.StateAction`, `Req…`, `core.me()`.
- fx: `persistent.fx_reduced_motion`, `persistent.fx_fake_loading` (preferences toggles).
- minigames: `persistent.mini_skip_allowed` (preferences toggle).

## Tasks
- [ ] 1. **Tidy the standard screens.** Split `screens.rpy` into topic files (`menus_scr.rpy`, `say_scr.rpy`, `saveload_scr.rpy`, `prefs_scr.rpy`, …), keep Ren'Py's screen names, rename custom styles to `uix_*`, remove the starter comments that don't help. Done when: lint is clean and the game looks the same.
- [ ] 2. **Variants.** `small` and `medium` layouts for the standard screens and gui sizes; touch-friendly hit areas. Done when: every standard screen is usable under phone emulation.
- [ ] 3. **Game-menu shell and tab registry.** `uix.register_menu_tab`; tabs sorted by order, hidden when `requires` fails; standard screens shown as tabs inside the shell. Done when: a test tab registered from `ui_test.rpy` appears and opens.
- [ ] 4. **HUD.** `hud_root` with a draggroup; `uix.register_hud_panel`; open/close and positions saved in `persistent`; a tap-to-select/tap-to-place helper for touch. Done when: two test panels exist and a test item drags from one to the other with the mouse, and moves by tapping under touch emulation.
- [ ] 5. **Say screen.** `thought` parameter, 3 skins, sliders with Reset in preferences. Done when: a test label shows normal and thought lines in each skin.
- [ ] 6. **Components.** `uix_panel(title)`, buttons, tooltip, confirm, toast queue `uix.notify(text)`. Done when: test label shows each.
- [ ] 7. **Preferences.** Tabs: General, Textbox, Accessibility (reduced motion, fake loading, minigame skip, text size), Language. Done when: toggles change the persistent values.
- [ ] 8. **Main menu.** Data-driven parallax layers and floating items, touch fallback, links, version. Needs art from the user (placeholders until then). Done when: runs on PC and under phone emulation.
- [ ] 9. **Quick menu.** PC and touch versions with Game and Story buttons opening the game menu on the right tab. Done when: both versions work.
- [ ] 10. **Publish.** Print the ui section for game/code/CLAUDE.md.

## API to publish
`uix.register_menu_tab`, `uix.register_hud_panel`, `hud_root`, `uix.notify`, components, tap-to-place helper, say-screen thought support.
