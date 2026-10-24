## Styles for dev/'s own panels (overlay, content check report). The test menu
## tab uses ui's styles instead, so it looks like the rest of the game menu.

init offset = 0

style dev_panel is default:
    background Solid("#10141aee")
    padding (16, 12, 16, 12)

style dev_field is default:
    background Solid("#000000aa")
    padding (8, 4, 8, 4)
    xminimum 200

style dev_text is default:
    size 22
    color "#e6e6e6"

style dev_title is dev_text:
    bold True
    color "#ffd166"

style dev_small is dev_text:
    size 18
    color "#9aa5b1"

style dev_input is dev_text:
    color "#ffffff"

style dev_button is default:
    background Solid("#273140")
    hover_background Solid("#3b4a60")
    selected_background Solid("#5a4a1e")
    insensitive_background Solid("#1b2028")
    padding (10, 4, 10, 4)

style dev_button_text is dev_text:
    hover_color "#ffffff"
    selected_color "#ffd166"
    insensitive_color "#5c6670"

style dev_hbox is hbox:
    spacing 6

style dev_vbox is vbox:
    spacing 6

## Phone layout: bigger text and buttons.

style dev_text variant "small":
    size 32

style dev_small variant "small":
    size 26

style dev_button variant "small":
    padding (18, 10, 18, 10)

## Test menu tab (inside ui's game menu shell).

style dev_heading is text:
    bold True

style dev_note is text:
    italic True
