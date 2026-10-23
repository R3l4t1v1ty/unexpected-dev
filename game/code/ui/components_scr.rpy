## Shared pieces other screens build with.
##
## - uix_panel(title=None): a framed panel; put the content inside it.
## - Button styles: uix_button (dark, accent on hover), uix_accent_button.
## - uix_tooltip: add `use uix_tooltip` at the end of a screen and give buttons
##   `tooltip _("...")`. Tooltips need hover, so never hide anything a touch
##   player needs in one.
## - uix_message(message, title=None): a modal message with OK
##   (`call screen uix_message(_("..."))`).
## - confirm: the standard yes/no screen (overlays_scr.rpy), in the same look.
## - uix.notify(text): toasts (notify_py.rpy), shown by uix_toasts below.

init offset = 0

screen uix_panel(title=None):

    frame:
        style "uix_panel"

        vbox:

            if title is not None:
                frame:
                    style "uix_panel_title"
                    text title style "uix_panel_title_text"

            frame:
                style "uix_panel_body"

                vbox:
                    spacing 15
                    transclude


screen uix_tooltip():

    $ tip = GetTooltip()

    if tip:

        nearrect:
            focus "tooltip"
            prefer_top True

            frame:
                style "uix_tooltip_frame"
                text tip style "uix_tooltip_text"


screen uix_message(message, title=None):

    modal True
    zorder 200

    add "#000000b0"

    frame:
        style "uix_message_frame"

        use uix_panel(title):

            text message style "uix_message_text"

            textbutton _("OK"):
                style "uix_accent_button"
                xalign 0.5
                action Return(True)

    key "game_menu" action Return(True)


screen uix_toasts(entries):

    zorder 300
    style_prefix "uix_toast"

    vbox:
        for start, message in entries:
            frame at uix_toast_appear:
                text "[message!tq]"

    timer 0.5 repeat True action Function(uix.toast_tick)


transform uix_toast_appear:
    alpha 0.0 xoffset 40
    easein 0.25 alpha 1.0 xoffset 0
    pause (uix.TOAST_TIME - 0.75)
    linear 0.5 alpha 0.0


style uix_panel is empty:
    background uix.dark
    padding (0, 0, 0, 0)

style uix_panel_title is empty:
    xfill True
    background uix.accent
    padding (20, 8, 20, 8)

style uix_panel_title_text is gui_text:
    font gui.interface_text_font
    size gui.label_text_size
    color "#ffffff"

style uix_panel_body is empty:
    padding (30, 25, 30, 25)

style uix_button is button:
    background uix.dark
    hover_background uix.accent
    selected_background "#ffffff"
    insensitive_background uix.dark
    padding (24, 10, 24, 10)

style uix_button_text is button_text:
    font gui.interface_text_font
    idle_color uix.idle
    hover_color "#ffffff"
    selected_color uix.accent
    insensitive_color uix.locked
    textalign 0.5

style uix_accent_button is uix_button:
    background uix.accent
    hover_background "#e066a3"

style uix_accent_button_text is uix_button_text:
    idle_color "#ffffff"
    hover_color "#ffffff"

## In a nearrect, xalign places the tooltip relative to the hovered widget:
## 0.5 centers it (Ren'Py keeps it on screen near the edges).
style uix_tooltip_frame is empty:
    background "#000000e0"
    padding (16, 10, 16, 10)
    xalign 0.5

style uix_tooltip_text is gui_text:
    size 24
    color uix.muted

style uix_message_frame is empty:
    xalign 0.5
    yalign 0.4
    xsize 900

style uix_message_text is gui_text:
    xalign 0.5
    textalign 0.5
    layout "subtitle"

style uix_toast_vbox is vbox:
    xalign 1.0
    xoffset -30
    ypos gui.notify_ypos
    spacing 10

style uix_toast_frame is empty:
    background uix.dark
    left_padding 30
    right_padding 30
    top_padding 10
    bottom_padding 10
    xalign 1.0

style uix_toast_text is gui_text:
    properties gui.text_properties("notify")


## Bigger touch targets on phones.
style uix_button:
    variant "small"
    padding (36, 20, 36, 20)

style uix_message_frame:
    variant "small"
    xsize 1400
