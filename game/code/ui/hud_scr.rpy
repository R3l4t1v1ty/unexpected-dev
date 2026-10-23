## The HUD container and the slot/item pieces panels are built from.
## How panels plug in: hud_py.rpy. world/ shows hud_root (`show screen
## hud_root`) when it wants the HUD; ui never shows it by itself.

init offset = 0

screen hud_root():

    $ panels = uix.hud_open_panels()
    $ floating = uix.hud_floating()

    ## One button per registered panel, to open and close it.
    hbox:
        style "uix_hud_bar"

        for p in uix.hud_panel_list:
            textbutton p.name:
                style "uix_hud_bar_button"
                action uix.HudToggle(p.id)

    draggroup:

        for p in panels:

            $ wx, wy = uix.hud_window_pos(p)
            $ ww, wh = p.size

            ## The window: dragged by its title bar (minus the close button);
            ## its slots and items move with it (uix.hud_join).
            drag:
                drag_name ("uix_win", p.id)
                pos (wx, wy)
                draggable floating
                droppable False
                drag_raise True
                drag_handle (0, 0, ww - 56, uix.HUD_TITLE_H)
                drag_joined uix.hud_join
                dragged uix.hud_window_dragged

                frame:
                    style "uix_hud_window"
                    xysize (ww, wh)

                    fixed:

                        frame:
                            style "uix_hud_title"
                            xysize (ww, uix.HUD_TITLE_H)

                            text p.name style "uix_hud_title_text"

                        textbutton "×":
                            style "uix_hud_close_button"
                            xpos ww - 52
                            action uix.HudToggle(p.id)

                        fixed:
                            pos (uix.HUD_PAD, uix.HUD_TITLE_H + uix.HUD_PAD)
                            xysize (ww - 2 * uix.HUD_PAD, wh - uix.HUD_TITLE_H - 2 * uix.HUD_PAD)

                            use expression p.screen pass (p.id, "body")

            ## The panel's slots and items join the draggroup directly.
            use expression p.screen pass (p.id, "drags")


## A place an item can be dropped on. `xy` is relative to the panel's content
## area; `key` is the panel's own id for the slot.
screen uix_hud_slot(panel, key, xy, size=None):

    $ ox, oy = uix.hud_origin(panel)
    $ sw, sh = size or uix.HUD_SLOT_SIZE

    drag:
        drag_name ("uix_slot", panel, key)
        pos (ox + xy[0], oy + xy[1])
        draggable False
        droppable True
        drag_raise False
        clicked uix.hud_clicked

        frame:
            style "uix_hud_slot"
            xysize (sw, sh)


## An item sitting in slot `key`. `child` is what's drawn (an icon).
screen uix_hud_item(panel, key, child, xy, size=None):

    $ ox, oy = uix.hud_origin(panel)
    $ sw, sh = size or uix.HUD_SLOT_SIZE
    $ chosen = uix.hud_is_selected(panel, key)

    drag:
        drag_name ("uix_item", panel, key)
        pos (ox + xy[0], oy + xy[1])
        draggable True
        droppable False
        drag_raise True
        dragged uix.hud_item_dragged
        clicked uix.hud_clicked

        frame:
            style ("uix_hud_item_chosen" if chosen else "uix_hud_item")
            xysize (sw, sh)

            add child align (0.5, 0.5)


style uix_hud_bar is hbox:
    xalign 0.5
    ypos 10
    spacing 8

style uix_hud_bar_button is uix_button
style uix_hud_bar_button_text is uix_button_text

style uix_hud_window is empty:
    background uix.hud_window_bg
    padding (0, 0, 0, 0)

style uix_hud_title is empty:
    background uix.hud_title_bg
    left_padding 14
    right_padding 60

style uix_hud_title_text is gui_text:
    font gui.interface_text_font
    size 26
    color "#ffffff"
    yalign 0.5

style uix_hud_close_button is button:
    xysize (48, 44)
    background None
    hover_background "#ffffff30"

style uix_hud_close_button_text is button_text:
    font "DejaVuSans.ttf"
    size 30
    idle_color "#ffffff"
    hover_color "#ffffff"
    align (0.5, 0.5)

style uix_hud_slot is empty:
    background uix.hud_slot_bg
    hover_background uix.hud_slot_hover_bg
    selected_background uix.hud_slot_hover_bg

style uix_hud_item is empty:
    background None
    hover_background "#ffffff20"

style uix_hud_item_chosen is empty:
    background uix.hud_selected_bg


## Phone: bigger title bar text.
style uix_hud_title_text:
    variant "small"
    size 34
