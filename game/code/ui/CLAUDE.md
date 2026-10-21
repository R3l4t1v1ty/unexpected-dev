# ui/

## Purpose
The UI framework: `gui.rpy`, Ren'Py's standard screens (say, choice, menus, save/load, preferences, history, help, confirm…), main menu, quick menu, the say screen and its skins, the game-menu shell and tab registry, the HUD container `hud_root` and panel registry, shared components and styles, and the PC/phone/tablet layouts.

## Rules
- Namespace `uix` (not `ui`: Ren'Py owns that name). Styles `uix_*`, screens `uix_*`, except Ren'Py's standard screen names.
- Registries (`uix.register_menu_tab`, `uix.register_hud_panel`) are created at init -400 so systems can register at 100. Styles and screens at priority ≥ 0 (`gui.init` resets styles at -2).
- Gameplay screens belong to their systems. ui/ never references world, events, rpg or other system names; they plug in through the registries.
- Layout by variant: default = PC, `small` = phone, `medium` = tablet; input by `touch`. Never `renpy.android`.
- Per-player UI settings (panel positions, textbox sliders) go in `persistent`, never in `gs`.

@TASKS.md
