## Preferences: a tab of the game menu, with its own pages:
## General, Textbox, Accessibility and (when translations exist) Language.
##
## Tab pages are used screens, so their own variables change with
## SetLocalVariable, not SetScreenVariable.

init offset = 0

screen preferences():
    tag menu
    use uix_menu("preferences")


screen uix_prefs_page():

    default page = "general"

    vbox:
        spacing 30

        hbox:
            spacing 10

            textbutton _("General"):
                style "uix_button"
                action SetLocalVariable("page", "general")

            textbutton _("Textbox"):
                style "uix_button"
                action SetLocalVariable("page", "textbox")

            textbutton _("Accessibility"):
                style "uix_button"
                action SetLocalVariable("page", "accessibility")

            if uix.languages():
                textbutton _("Language"):
                    style "uix_button"
                    action SetLocalVariable("page", "language")

        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"

            if page == "general":
                use uix_prefs_general
            elif page == "textbox":
                use uix_prefs_textbox
            elif page == "accessibility":
                use uix_prefs_accessibility
            elif page == "language":
                use uix_prefs_language


screen uix_prefs_general():

    vbox:

        hbox:
            box_wrap True
            box_wrap_spacing 30

            if renpy.variant("pc") or renpy.variant("web"):

                vbox:
                    style_prefix "radio"
                    label _("Display")
                    textbutton _("Window") action Preference("display", "window")
                    textbutton _("Fullscreen") action Preference("display", "fullscreen")

            if renpy.variant("touch"):

                vbox:
                    style_prefix "radio"
                    label _("Rollback Side")
                    textbutton _("Disable") action Preference("rollback side", "disable")
                    textbutton _("Left") action Preference("rollback side", "left")
                    textbutton _("Right") action Preference("rollback side", "right")

            vbox:
                style_prefix "check"
                label _("Skip")
                textbutton _("Unseen Text") action Preference("skip", "toggle")
                textbutton _("After Choices") action Preference("after choices", "toggle")
                textbutton _("Transitions") action InvertSelected(Preference("transitions", "toggle"))

        null height (4 * gui.pref_spacing)

        hbox:
            style_prefix "slider"
            box_wrap True

            vbox:

                label _("Text Speed")

                bar value Preference("text speed")

                label _("Auto-Forward Time")

                bar value Preference("auto-forward time")

            vbox:

                if config.has_music:
                    label _("Music Volume")

                    hbox:
                        bar value Preference("music volume")

                if config.has_sound:

                    label _("Sound Volume")

                    hbox:
                        bar value Preference("sound volume")

                        if config.sample_sound:
                            textbutton _("Test") action Play("sound", config.sample_sound)

                if config.has_voice:
                    label _("Voice Volume")

                    hbox:
                        bar value Preference("voice volume")

                        if config.sample_voice:
                            textbutton _("Test") action Play("voice", config.sample_voice)

                if config.has_music or config.has_sound or config.has_voice:
                    null height gui.pref_spacing

                    textbutton _("Mute All"):
                        action Preference("all mute", "toggle")
                        style "mute_all_button"


screen uix_prefs_textbox():

    vbox:
        spacing 25

        hbox:
            spacing 15

            label _("Skin") style "pref_label"

            for skin in uix.textbox_skin_list:
                textbutton skin.name:
                    style "uix_button"
                    yalign 1.0
                    action SetField(persistent, "uix_tb_skin", skin.id)
                    selected uix.textbox_skin().id == skin.id

        hbox:
            box_wrap True
            spacing 60
            box_wrap_spacing 10

            vbox:
                use uix_tb_slider(_("Opacity"), "alpha")
                use uix_tb_slider(_("Width"), "width")
                use uix_tb_slider(_("Height"), "height")

            vbox:
                use uix_tb_slider(_("Text Size"), "text_size")
                use uix_tb_slider(_("Text Outline"), "outline_text")
                use uix_tb_slider(_("Name Outline"), "outline_name")

        label _("Preview") style "pref_label"

        hbox:
            spacing 30

            fixed:
                xysize (uix.tb("width"), uix.tb("height"))
                at Transform(zoom=0.4)
                use uix_textbox_preview()

            fixed:
                xysize (uix.tb("width"), uix.tb("height"))
                at Transform(zoom=0.4)
                use uix_textbox_preview(thought=True)


## One textbox slider: a label, the bar with its value on it, and Reset.
screen uix_tb_slider(title, key):

    vbox:
        style_prefix "slider"

        label title

        hbox:
            spacing 15

            fixed:
                xsize 525
                ysize gui.slider_size

                bar value uix.TextboxValue(key) xsize 525
                text str(uix.tb(key)) style "uix_slider_value_text"

            textbutton _("Reset"):
                action uix.TextboxReset(key)


screen uix_prefs_accessibility():

    vbox:

        hbox:
            box_wrap True
            box_wrap_spacing 30

            vbox:
                style_prefix "check"
                label _("Motion")
                textbutton _("Reduced Motion") action ToggleField(persistent, "fx_reduced_motion")
                textbutton _("Fake Loading Screens") action ToggleField(persistent, "fx_fake_loading")

            vbox:
                style_prefix "check"
                label _("Minigames")
                textbutton _("Allow Skipping") action ToggleField(persistent, "mini_skip_allowed")

            vbox:
                style_prefix "check"
                label _("Reading")
                textbutton _("High Contrast Text") action Preference("high contrast text", "toggle")
                textbutton _("Self-Voicing") action Preference("self voicing", "toggle")

        null height (4 * gui.pref_spacing)

        vbox:
            style_prefix "slider"

            label _("Text Size")

            hbox:
                spacing 15
                bar value Preference("font size")
                textbutton _("Reset") action Preference("font size", 1.0)

            label _("Line Spacing")

            hbox:
                spacing 15
                bar value Preference("font line spacing")
                textbutton _("Reset") action Preference("font line spacing", 1.0)


screen uix_prefs_language():

    vbox:
        style_prefix "radio"

        label _("Language")

        textbutton uix.base_language_name action Language(None)

        for lang in uix.languages():
            textbutton uix.language_name(lang) action Language(lang)


style pref_label is gui_label
style pref_label_text is gui_label_text
style pref_vbox is vbox

style radio_label is pref_label
style radio_label_text is pref_label_text
style radio_button is gui_button
style radio_button_text is gui_button_text
style radio_vbox is pref_vbox

style check_label is pref_label
style check_label_text is pref_label_text
style check_button is gui_button
style check_button_text is gui_button_text
style check_vbox is pref_vbox

style slider_label is pref_label
style slider_label_text is pref_label_text
style slider_slider is gui_slider
style slider_button is gui_button
style slider_button_text is gui_button_text
style slider_pref_vbox is pref_vbox

style mute_all_button is check_button
style mute_all_button_text is check_button_text

style pref_label:
    top_margin gui.pref_spacing
    bottom_margin 3

style pref_label_text:
    yalign 1.0

style pref_vbox:
    xsize 338

style radio_vbox:
    spacing gui.pref_button_spacing

style radio_button:
    properties gui.button_properties("radio_button")
    foreground "gui/button/radio_[prefix_]foreground.png"

style radio_button_text:
    properties gui.text_properties("radio_button")

style check_vbox:
    spacing gui.pref_button_spacing

style check_button:
    properties gui.button_properties("check_button")
    foreground "gui/button/check_[prefix_]foreground.png"

style check_button_text:
    properties gui.text_properties("check_button")

style slider_slider:
    xsize 525

style slider_button:
    properties gui.button_properties("slider_button")
    yalign 0.5
    left_margin 15

style slider_button_text:
    properties gui.text_properties("slider_button")

style slider_vbox:
    xsize 675

style uix_slider_value_text is gui_text:
    size 22
    color uix.muted
    outlines [ (2, "#000", 0, 0) ]
    align (0.5, 0.5)


## Tablet and phone #############################################################

style pref_vbox:
    variant "medium"
    xsize 675

style radio_button:
    variant "small"
    foreground "gui/phone/button/radio_[prefix_]foreground.png"

style check_button:
    variant "small"
    foreground "gui/phone/button/check_[prefix_]foreground.png"

style pref_vbox:
    variant "small"
    xsize 600

style slider_vbox:
    variant "small"
    xsize None

style slider_slider:
    variant "small"
    xsize 900
