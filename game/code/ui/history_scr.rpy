## Dialogue history, a tab of the game menu.

init offset = 0

screen history():
    tag menu
    predict False
    use uix_menu("history")


screen uix_history_page():

    ## Can be very large, so it isn't predicted.
    predict False

    use uix_scroll(yinitial=1.0, spacing=gui.history_spacing):

        style_prefix "history"

        for h in _history_list:

            $ thought = getattr(h, "show_args", {}).get("thought", False)
            $ what = renpy.filter_text_tags(h.what, allow=gui.history_allow_tags)

            window:

                ## Lays things out properly when history_height is None.
                has fixed:
                    yfit True

                if h.who:

                    label h.who:
                        style "history_name"
                        substitute False

                        ## Use the Character's name color, if it has one.
                        if "color" in h.who_args:
                            text_color h.who_args["color"]

                text what:
                    substitute False
                    italic thought

        if not _history_list:
            label _("The dialogue history is empty.")


## The text tags allowed in the history.
define gui.history_allow_tags = { "alt", "noalt", "rt", "rb", "art" }


style history_window is empty

style history_name is gui_label
style history_name_text is gui_label_text
style history_text is gui_text

style history_label is gui_label
style history_label_text is gui_label_text

style history_window:
    xfill True
    ysize gui.history_height

style history_name:
    xpos gui.history_name_xpos
    xanchor gui.history_name_xalign
    ypos gui.history_name_ypos
    xsize gui.history_name_width

style history_name_text:
    min_width gui.history_name_width
    textalign gui.history_name_xalign

style history_text:
    xpos gui.history_text_xpos
    ypos gui.history_text_ypos
    xanchor gui.history_text_xalign
    xsize gui.history_text_width
    min_width gui.history_text_width
    textalign gui.history_text_xalign
    layout ("subtitle" if gui.history_text_xalign else "tex")

style history_label:
    xfill True

style history_label_text:
    xalign 0.5
