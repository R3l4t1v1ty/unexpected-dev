## Main menu: the art set's layers, the buttons, the link bar, the version box
## with its changelog, the art-set picker, and a toggle that hides it all.
## Content (sets, links, changelog) is in main_menu_ini.rpy.

init offset = 0

screen main_menu():

    ## Replaces any other menu screen.
    tag menu

    default hidden = False
    default picking = False
    default changelog_open = False
    default focused = None
    default toggles = set()

    $ mmset = uix.main_menu_set()
    $ links = uix.visible_links()

    for layer in mmset.layers:
        if layer.toggle is None or layer.toggle in toggles:
            add layer.image at uix_mm_move(layer)

    for spot in mmset.hotspots:
        button:
            pos (spot.x, spot.y)
            xysize (spot.w, spot.h)
            background None
            action ToggleSetMembership(toggles, spot.toggle)

    if not hidden:

        add uix.mm_logo pos (760, 135)

        fixed:
            style "uix_mm_panel"

            add uix.mm_buttons_bg

            vbox:
                style "uix_mm_buttons"

                for i, entry in enumerate(uix.main_menu_buttons()):

                    fixed:
                        style "uix_mm_row"

                        ## Arrows beside the button under the mouse or the
                        ## keyboard focus.
                        if focused == i:
                            if persistent.fx_reduced_motion:
                                add uix.mm_arrow_left xalign 0.1 yalign 0.5
                                add uix.mm_arrow_right xalign 0.9 yalign 0.5
                            else:
                                add uix.mm_arrow_left xalign 0.1 yalign 0.5 at uix_mm_arrow(1)
                                add uix.mm_arrow_right xalign 0.9 yalign 0.5 at uix_mm_arrow(-1)

                        textbutton entry[0]:
                            style "uix_mm_button"
                            action entry[1]
                            hovered SetScreenVariable("focused", i)
                            unhovered SetScreenVariable("focused", None)

        if links:

            fixed:
                style "uix_mm_link_bar"

                add uix.mm_link_bar

                hbox:
                    align (0.5, 0.5)
                    spacing 30

                    for link in links:
                        button:
                            style "uix_mm_link_button"
                            action (OpenURL(link.url) if link.url else None)
                            tooltip link.name
                            add link.icon

        drag:
            align (0.97, 0.95)
            drag_raise False

            frame:
                style "uix_mm_version_frame"

                vbox:
                    spacing 10
                    align (0.5, 0.5)

                    label _("Version [config.version]") style "uix_mm_version_label"

                    if uix.changelog:
                        textbutton _("Changelog"):
                            style "uix_button"
                            xalign 0.5
                            action SetScreenVariable("changelog_open", True)

        ## The art-set picker, top left.
        if len(uix.main_menu_set_list) > 1:

            if picking:

                frame:
                    style "uix_mm_picker"

                    vbox:
                        spacing 20

                        for s in uix.main_menu_set_list:
                            button:
                                style "uix_mm_preview_button"
                                action [ SetField(persistent, "uix_mm_set", s.id), SetScreenVariable("picking", False) ]
                                selected s is mmset

                                if s.preview is not None:
                                    add s.preview
                                else:
                                    text s.name

                        textbutton _("Close"):
                            style "uix_button"
                            xalign 0.5
                            action SetScreenVariable("picking", False)

            else:

                button:
                    style "uix_mm_corner_button"
                    align (0.0, 0.0)
                    action SetScreenVariable("picking", True)
                    tooltip _("Change the main menu art")

                    add uix.mm_corner at uix_mm_flip

        if changelog_open:

            button:
                style "uix_mm_dim"
                action SetScreenVariable("changelog_open", False)

            frame:
                style "uix_mm_changelog"

                vbox:
                    spacing 20

                    label _("Changelog") style "uix_mm_changelog_title"

                    viewport:
                        mousewheel True
                        draggable True
                        scrollbars "vertical"

                        vbox:
                            spacing 30

                            for title, body in uix.changelog:
                                vbox:
                                    spacing 8
                                    text title style "uix_mm_changelog_heading"
                                    text body style "uix_mm_changelog_text"

                    textbutton _("Close"):
                        style "uix_button"
                        xalign 0.5
                        action SetScreenVariable("changelog_open", False)

    ## Hides or shows everything but the art (also the H key).
    button:
        style "uix_mm_corner_button"
        align (1.0, 1.0)
        action ToggleScreenVariable("hidden")
        tooltip _("Hide the menu")

        add uix.mm_corner

    key "hide_windows" action ToggleScreenVariable("hidden")

    use uix_tooltip


## Places a layer: parallax and bobbing (MainMenuLayer.update).
transform uix_mm_move(layer):
    function layer.update

## The arrows' sway.
transform uix_mm_arrow(direction):
    subpixel True
    easeout 0.7 xoffset direction * (-10)
    easein 0.7 xoffset direction * 10
    repeat

transform uix_mm_flip:
    rotate 180


style uix_mm_panel is empty:
    pos (760, 245)
    xysize (400, 600)

style uix_mm_buttons is vbox:
    ypos 110
    xfill True
    spacing 0

style uix_mm_row is empty:
    xfill True
    ysize 70

style uix_mm_button is button:
    align (0.5, 0.5)
    background None
    hover_sound uix.mm_hover_sound

style uix_mm_button_text is button_text:
    font gui.interface_text_font
    size 41
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.hover_color
    insensitive_color gui.insensitive_color
    xalign 0.5

style uix_mm_link_bar is empty:
    pos (635, 990)
    xysize (650, 90)

style uix_mm_link_button is button:
    background None
    padding (0, 0, 0, 0)

style uix_mm_version_frame is empty:
    background uix.dark
    xysize (300, 200)

style uix_mm_version_label is gui_label

style uix_mm_version_label_text is gui_label_text:
    xalign 0.5
    textalign 0.5

style uix_mm_corner_button is button:
    background None
    padding (8, 8, 8, 8)

style uix_mm_picker is empty:
    pos (25, 25)
    background uix.dark
    padding (20, 20, 20, 20)

style uix_mm_preview_button is button:
    background None
    selected_background uix.accent
    hover_background uix.accent
    padding (6, 6, 6, 6)

style uix_mm_dim is button:
    xfill True
    yfill True
    background "#000000a0"

style uix_mm_changelog is empty:
    align (0.5, 0.45)
    xysize (1100, 860)
    background uix.dark
    padding (40, 40, 40, 40)

style uix_mm_changelog_title is gui_label

style uix_mm_changelog_title_text is gui_label_text:
    size 50

style uix_mm_changelog_heading is gui_text:
    color uix.accent
    size 34

style uix_mm_changelog_text is gui_text:
    size 26


## Phone: bigger buttons and text.
style uix_mm_panel:
    variant "small"
    pos (660, 200)
    xysize (600, 760)

style uix_mm_row:
    variant "small"
    ysize 100

style uix_mm_button_text:
    variant "small"
    size 56

style uix_mm_changelog:
    variant "small"
    xysize (1600, 960)
