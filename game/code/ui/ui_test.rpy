## ui tests (developer mode; excluded from builds). Run them from dev/'s test
## menu, in a started game.
##
## - test_ui_menu: a tab registered here appears in the game menu and opens,
##   with an argument passed to its screen.
## - test_ui_hud: two test panels; drag an item between them with the mouse,
##   or tap it and tap a slot (try under touch emulation too).
## - test_ui_say: normal and thought lines in each textbox skin.
## - test_ui_choice: a menu with a met and an unmet requirement.
## - test_ui_components: panel, buttons, tooltip, toasts, confirm, message.

init offset = 100

## Shown in the game menu only while test_ui_menu runs.
init python:

    class ReqUiTestTab(Req):

        def check(self, twin=None):
            return bool(persistent.uix_test_tab)

default persistent.uix_test_tab = False

init python in uix_test:

    import store

    uix = store.uix
    core = store.core

    uix.register_menu_tab("uix_test", _("Test Tab"), "uix_test_tab", order=900, requires=store.ReqUiTestTab())

    ## Two panels of four slots; each slot holds a color name or None. The
    ## state keeps names; the screen draws them with these hex colors (Ren'Py
    ## colors must be hex).
    COLORS = { "red" : "#cc3333", "green" : "#33aa44", "blue" : "#3366cc" }

    core.register_state("uix_test", { "uix_test_a" : [ "red", None, "green", None ], "uix_test_b" : [ None, "blue", None, None ] }, False)

    def move(src_panel, src_key, dst_panel, dst_key):
        slots = core.state("uix_test")
        item = slots[src_panel][src_key]

        if item is None:
            return

        ## Swap with whatever is in the target slot.
        slots[src_panel][src_key] = slots[dst_panel][dst_key]
        slots[dst_panel][dst_key] = item

    def drop_a(src_panel, src_key, dst_key):
        move(src_panel, src_key, "uix_test_a", dst_key)

    def drop_b(src_panel, src_key, dst_key):
        move(src_panel, src_key, "uix_test_b", dst_key)

    uix.register_hud_panel("uix_test_a", "uix_test_panel", _("Test A"), order=900, size=(520, 220), drop=drop_a)
    uix.register_hud_panel("uix_test_b", "uix_test_panel", _("Test B"), order=901, size=(520, 220), drop=drop_b)

define uix_test_speaker = Character(_("Tester"))
define uix_test_thinker = Character(_("Tester"), show_thought=True)


## Menu ########################################################################

screen uix_test_tab(message=None):

    use uix_scroll():

        text _("This tab was registered from ui_test.rpy.")

        if message is not None:
            text message


label test_ui_menu:

    $ persistent.uix_test_tab = True
    $ uix.MenuTab("uix_test", message=_("It received an argument."))()
    $ persistent.uix_test_tab = False

    return


## HUD #########################################################################

screen uix_test_panel(panel, part):

    $ slots = core.state("uix_test")[panel]

    if part == "body":

        text _("Drag or tap the colors.") size 22 ypos 120

    else:

        for i, color in enumerate(slots):

            use uix_hud_slot(panel, i, (i * 120, 0))

            if color is not None:
                use uix_hud_item(panel, i, Solid(uix_test.COLORS[color], xysize=(70, 70)), (i * 120, 0))


screen uix_test_done(message):

    frame:
        style "uix_panel"
        align (0.5, 0.97)
        padding (30, 20, 30, 20)

        hbox:
            spacing 30

            text message yalign 0.5 size 26

            textbutton _("Done"):
                style "uix_accent_button"
                action Return()


label test_ui_hud:

    $ uix.hud_open("uix_test_a")
    $ uix.hud_open("uix_test_b")

    show screen hud_root
    call screen uix_test_done(_("Move the colors between the panels: drag them, or tap one and tap a slot."))
    hide screen hud_root

    return


## Say #########################################################################

label test_ui_say:

    $ persistent.uix_test_saved_skin = persistent.uix_tb_skin

    $ persistent.uix_tb_skin = "simple"
    uix_test_speaker "Simple skin: a normal line."
    uix_test_thinker "Simple skin: a thought line."

    $ persistent.uix_tb_skin = "fade"
    uix_test_speaker "Side-Fade skin: a normal line."
    uix_test_thinker "Side-Fade skin: a thought line."

    $ persistent.uix_tb_skin = "fancy"
    uix_test_speaker "Fancy skin: a normal line."
    uix_test_thinker "Fancy skin: a thought line."

    $ persistent.uix_tb_skin = persistent.uix_test_saved_skin

    return


## Choice ######################################################################

label test_ui_choice:

    menu:
        "Pick one. The last choice is locked."

        "A choice without a requirement.":
            pass

        "A met requirement (day 1 or later)." (req=ReqDay(min=1, text=_("Day 1"))):
            pass

        "An unmet requirement (day 999)." (req=ReqDay(min=999, text=_("Day 999"))):
            pass

    return


## Components ##################################################################

screen uix_test_components():

    frame:
        background None
        align (0.5, 0.4)

        use uix_panel(_("uix_panel")):

            text _("Hover the buttons for tooltips.")

            hbox:
                spacing 20

                textbutton _("uix_button"):
                    style "uix_button"
                    action NullAction()
                    tooltip _("A tooltip.")

                textbutton _("Toast"):
                    style "uix_button"
                    action Function(uix.notify, _("A toast from a button."))
                    tooltip _("Shows a toast.")

                textbutton _("Done"):
                    style "uix_accent_button"
                    action Return()

    use uix_tooltip


label test_ui_components:

    $ uix.notify(_("A toast."))
    $ uix.notify(_("A second toast, stacked under the first."))

    call screen uix_test_components

    $ renpy.confirm(_("The confirm screen. Either answer is fine."))

    call screen uix_message(_("A message with an OK button."), title=_("uix_message"))

    return
