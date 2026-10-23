## The game-menu shell: a sidebar with the current group's tabs, and the tab's
## screen in the content area. Open it with uix.MenuTab(id) (or ShowMenu with a
## standard screen name: save, load, preferences, history, help, about).

init offset = 0

screen uix_menu(tab, **kwargs):

    tag menu

    $ info = uix.menu_tab(tab)
    $ tabs = uix.visible_tabs(info.group)
    $ other = "system" if info.group == "story" else "story"
    $ other_entry = uix.group_entry(other)

    if main_menu:
        add gui.main_menu_background
    else:
        add gui.game_menu_background

    frame:
        style "uix_menu_content"

        fixed:
            use expression info.screen pass (**kwargs)

    frame:
        style "uix_menu_sidebar"

        fixed:

            text info.name style "uix_menu_title"

            vbox:
                style "uix_menu_tabs"

                if other_entry is not None:
                    textbutton uix.MENU_GROUP_NAMES[other]:
                        style "uix_menu_switch_button"
                        action uix.MenuTab(other_entry)

                    null height 30

                for t in tabs:
                    textbutton t.name:
                        style "uix_menu_button"
                        action uix.MenuTab(t.id)
                        selected t.id == tab

                if info.group == "system":

                    null height 30

                    if _in_replay:
                        textbutton _("End Replay"):
                            style "uix_menu_button"
                            action EndReplay(confirm=True)

                    elif not main_menu:
                        textbutton _("Main Menu"):
                            style "uix_menu_button"
                            action MainMenu()

                    ## Quit is banned on iOS and pointless on Android and web.
                    if renpy.variant("pc"):
                        textbutton _("Quit"):
                            style "uix_menu_button"
                            action Quit(confirm=not main_menu)

            textbutton _("Return"):
                style "uix_menu_close_button"
                action Return()

    frame:
        style "uix_menu_divider"

    if main_menu:
        key "game_menu" action ShowMenu("main_menu")


## Scrolling content for a tab: `use uix_scroll():` and put the content inside.
screen uix_scroll(yinitial=0.0, spacing=0):

    style_prefix "uix_menu"

    viewport:
        yinitial yinitial
        scrollbars "vertical"
        mousewheel True
        draggable True
        pagekeys True
        side_yfill True

        vbox:
            spacing spacing

            transclude


style uix_menu_sidebar is empty:
    xpos 0
    xsize uix.menu_sidebar_width
    yfill True
    background uix.dark

style uix_menu_divider is empty:
    xpos uix.menu_sidebar_width
    xsize 5
    yfill True
    background uix.accent

style uix_menu_content is empty:
    xpos uix.menu_sidebar_width + 5
    xsize config.screen_width - uix.menu_sidebar_width - 5
    yfill True
    left_padding 60
    right_padding 40
    top_padding 60
    bottom_padding 45

style uix_menu_title is gui_text:
    font gui.interface_text_font
    size 65
    color uix.accent
    xalign 0.5
    ypos 60

style uix_menu_tabs is vbox:
    xfill True
    yalign 0.5
    spacing 0

style uix_menu_button is button:
    xfill True
    ysize 64
    xpadding 20
    ypadding 0
    background uix.dark
    hover_background uix.accent
    selected_background "#ffffff"
    selected_hover_background "#ffffff"
    insensitive_background uix.dark

style uix_menu_button_text is button_text:
    font gui.interface_text_font
    size gui.interface_text_size
    xalign 0.5
    textalign 0.5
    idle_color uix.idle
    hover_color "#ffffff"
    selected_color uix.accent
    selected_hover_color uix.accent
    insensitive_color uix.locked

style uix_menu_switch_button is uix_menu_button

style uix_menu_switch_button_text is uix_menu_button_text:
    idle_color uix.accent

style uix_menu_close_button is uix_menu_button:
    yalign 0.94

style uix_menu_close_button_text is uix_menu_button_text

style uix_menu_viewport is viewport:
    xfill True

style uix_menu_side is side:
    spacing 15

style uix_menu_vscrollbar is vscrollbar:
    unscrollable gui.unscrollable

style uix_menu_vbox is vbox


## Phone ######################################################################

style uix_menu_sidebar:
    variant "small"
    xsize uix.menu_sidebar_width_small

style uix_menu_divider:
    variant "small"
    xpos uix.menu_sidebar_width_small

style uix_menu_content:
    variant "small"
    xpos uix.menu_sidebar_width_small + 5
    xsize config.screen_width - uix.menu_sidebar_width_small - 5
    left_padding 30
    right_padding 20
    top_padding 30
    bottom_padding 20

style uix_menu_title:
    variant "small"
    size 72
    ypos 30

style uix_menu_button:
    variant "small"
    ysize 96

style uix_menu_close_button:
    variant "small"
    yalign 0.97
