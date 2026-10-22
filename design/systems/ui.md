# ui/

The UI framework: `gui.rpy`, Ren'Py's standard screens, the main menu, preferences, the say screen and its skins, the game-menu shell with its tab registry, the HUD container, shared components and styles, and layouts for PC, phone and tablet.

Gameplay screens belong to their systems (world view, encyclopedia, inventory, computer…), which plug in through registries. See [architecture.md](../architecture.md) §8.

## Pieces

**Game menu.** A shell screen with tabs. Tabs come from `uix.register_menu_tab(id, name, screen, order=100, requires=None)`, the data-driven registry idea from rebuild #2 (`UnexpectedNavigation`). Expected tabs: Story (twin swap + completion, owned by events), Characters (characters), Events (events), Gallery and Achievements (progress), plus Save, Load, Preferences, History, Help.

**HUD.** `hud_root` is one screen containing a `draggroup`. Each panel is a screen owned by its system and registered with `uix.register_hud_panel(id, screen, name, order=100)`; `hud_root` includes each with `use`. Verified in the SDK: a `use`d screen's children go straight into the enclosing draggroup, so items can be dragged between panels (inventory → gear) while every panel lives in its own file. The old one-screen-of-2,300-lines problem goes away. Panel positions and open/closed state are per player (`persistent`), not per save. On touch devices dragging is fiddly, so panels also support tap-to-select then tap-to-place, through a helper ui provides.

**Say screen.** `thought=True` comes from `Character(..., show_thought=True)` (replaces the old `"___"` name prefix). Three skins (Simple, Side-Fade, Fancy) and persistent sliders: opacity, width, height, text size, name and text outlines, each with Reset. New art may come later.

**Choice screen.** A menu choice may carry a requirement, `"Lift the beam" (req=ReqStat("str", 12)):`. Ren'Py passes per-choice arguments to the choice screen as `i.kwargs` (checked in the 8.5 SDK). A choice whose `req` fails shows greyed out and can't be picked, with `req.describe()` beside it ("Strength 12"). This is how stats, items, reputation and relationships gate dialogue options (RPG design, 2026-10-23).

**Components.** Panel frame, buttons, tooltip, confirm dialog, toast queue (`uix.notify(text)`), all styled `uix_*`.

**Preferences.** Adds: reduced motion (`persistent.fx_reduced_motion`, owned by fx), fake loading on/off (`persistent.fx_fake_loading`), language, text size, minigame skip (owned by minigames).

**Main menu.** Parallax with floating items (data-driven, not nine copy-pasted functions), touch fallback (gentle automatic drift instead of following the mouse), social links, version.

**Quick menu.** PC: Back, History, Skip, Auto, Save, Q.Save, Q.Load, Prefs, Game, Story. Touch: Back, Skip, Auto, Story, Menu, Hide.

## Layouts
Designed at 1920×1080. Variants: default = PC (`large pc`), `small` = phone, `medium` = tablet; `touch` changes input behaviour (bigger hit areas, no hover-only actions, tap alternatives to drag). Emulate with `RENPY_VARIANT`.

## Open questions
- Which HUD panels exist and whether they stay draggable (depends on the RPG and relationship designs).
- New textbox art.
