## Quick menu: the row of buttons under the textbox in-game.
##
## Story opens the game menu on the "story" tab; it only shows when a system
## registered that tab (and it can be shown now: not in a replay).

init offset = 0

screen quick_menu():

    zorder 100

    if quick_menu:

        hbox:
            style_prefix "quick"
            style "quick_menu"

            textbutton _("Back") action Rollback()
            textbutton _("History") action ShowMenu("history")
            textbutton _("Skip") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("Auto") action Preference("auto-forward", "toggle")
            textbutton _("Save") action ShowMenu("save")
            textbutton _("Q.Save") action QuickSave()
            textbutton _("Q.Load") action QuickLoad()
            textbutton _("Prefs") action ShowMenu("preferences")

            if uix.has_menu_tab("story"):
                textbutton _("Story") action uix.MenuTab("story")


## Touch: fewer, bigger buttons. Menu is the way into the game menu when
## there's no Escape key.
screen quick_menu():
    variant "touch"

    zorder 100

    if quick_menu:

        hbox:
            style_prefix "quick"
            style "quick_menu"

            textbutton _("Back") action Rollback()
            textbutton _("Skip") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("Auto") action Preference("auto-forward", "toggle")
            textbutton _("Menu") action ShowMenu()

            if uix.has_menu_tab("story"):
                textbutton _("Story") action uix.MenuTab("story")


## Shows the quick menu in-game, unless the player hid the interface.
init python:
    config.overlay_screens.append("quick_menu")

default quick_menu = True

style quick_menu is hbox
style quick_button is default
style quick_button_text is button_text

style quick_menu:
    xalign 0.5
    yalign 1.0

style quick_button:
    properties gui.button_properties("quick_button")

style quick_button_text:
    properties gui.text_properties("quick_button")
