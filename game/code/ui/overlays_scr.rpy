## Screens Ren'Py shows on top of everything: confirm, skip indicator, notify.

init offset = 0

## Yes/no question (quitting, overwriting a save...).
screen confirm(message, yes_action, no_action):

    ## Other screens get no input while this is up.
    modal True

    zorder 200

    style_prefix "confirm"

    add "#000000b0"

    frame:

        vbox:
            xalign .5
            yalign .5
            spacing 45

            label _(message):
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton _("Yes") action yes_action
                textbutton _("No") action no_action

    ## Right-click and escape answer "no".
    key "game_menu" action no_action


style confirm_frame is empty
style confirm_prompt is gui_prompt
style confirm_prompt_text is gui_prompt_text
style confirm_button is uix_button
style confirm_button_text is uix_button_text

style confirm_frame:
    background uix.dark
    padding (60, 60, 60, 60)
    xalign .5
    yalign .5
    xminimum 800

style confirm_prompt_text:
    textalign 0.5
    layout "subtitle"

style confirm_button:
    xminimum 200

style confirm_button_text:
    xalign 0.5


## Shown while skipping.
screen skip_indicator():

    zorder 100
    style_prefix "skip"

    frame:

        hbox:
            spacing 9

            text _("Skipping")

            text "▸" at delayed_blink(0.0, 1.0) style "skip_triangle"
            text "▸" at delayed_blink(0.2, 1.0) style "skip_triangle"
            text "▸" at delayed_blink(0.4, 1.0) style "skip_triangle"


## Blinks the arrows one after another.
transform delayed_blink(delay, cycle):
    alpha .5

    pause delay

    block:
        linear .2 alpha 1.0
        pause .2
        linear .2 alpha 0.5
        pause (cycle - .4)
        repeat


style skip_frame is empty
style skip_text is gui_text
style skip_triangle is skip_text

style skip_frame:
    ypos gui.skip_ypos
    background Frame("gui/skip.png", gui.skip_frame_borders, tile=gui.frame_tile)
    padding gui.skip_frame_borders.padding

style skip_text:
    size gui.notify_text_size

style skip_triangle:
    ## Needs a font with the BLACK RIGHT-POINTING SMALL TRIANGLE glyph.
    font "DejaVuSans.ttf"


## Ren'Py's own notify screen. renpy.notify goes to uix.notify (toasts)
## instead; this stays for anything that shows "notify" directly.
screen notify(message):

    zorder 100
    style_prefix "notify"

    frame at notify_appear:
        text "[message!tq]"

    timer 3.25 action Hide('notify')


transform notify_appear:
    on show:
        alpha 0
        linear .25 alpha 1.0
    on hide:
        linear .5 alpha 0.0


style notify_frame is empty
style notify_text is gui_text

style notify_frame:
    ypos gui.notify_ypos

    background Frame("gui/notify.png", gui.notify_frame_borders, tile=gui.frame_tile)
    padding gui.notify_frame_borders.padding

style notify_text:
    properties gui.text_properties("notify")
