## Test menu screens: the "Tests" game-menu tab and the screen shown after a
## test returns.

init offset = 0

screen dev_tests_tab():

    use uix_scroll(spacing=24):

        if not main_menu and not dev.in_test_game():
            text _("Running a test ends this game and starts a fresh one.")

        if not dev.TESTS:
            text _("No tests found. A test is a label named test_<folder>_<name>.")

        for folder, tests in dev.TESTS:

            vbox:
                spacing 10

                text folder style "dev_heading"

                for tlabel, tname in tests:

                    $ ran, note = dev.result(tlabel)

                    hbox:
                        spacing 20

                        textbutton tname:
                            style "uix_button"
                            action dev.run_action(tlabel)

                        if ran:
                            text dev.plain(note or _("done")) style "dev_note" yalign 0.5 substitute False

        vbox:
            spacing 10

            text _("Content check") style "dev_heading"

            hbox:
                spacing 20

                textbutton _("Run"):
                    style "uix_accent_button"
                    action Function(dev.show_report)

                textbutton (_("Planted mistakes: on") if persistent.dev_plant else _("Planted mistakes: off")):
                    style "uix_button"
                    action Function(dev.set_plant, not persistent.dev_plant)

            text _("Planted mistakes add a missing label, a missing image and two clashing image files to the check, here and in lint.") style "dev_note"

        vbox:
            spacing 10

            text _("Fixture saves") style "dev_heading"

            hbox:
                spacing 20

                textbutton _("Check"):
                    style "uix_accent_button"
                    action Function(dev.show_fixture_report)

                if not main_menu:
                    textbutton _("Record this game"):
                        style "uix_button"
                        action Show("dev_fixture_record")

            text _("A fixture is a game's state kept as plain data in dev/fixtures/. Check runs each one through core.migrate and shows what changed since its result was last accepted. Record fixtures before every change to the save format.") style "dev_note"


## Shown by dev_run_test after the test returns.
screen dev_test_done(tlabel):

    modal True
    zorder 200

    $ ran, note = dev.result(tlabel)

    frame:
        background None
        align (0.5, 0.97)

        use uix_panel(_("Test finished")):

            text tlabel substitute False

            if note:
                text dev.plain(note) substitute False

            hbox:
                spacing 20

                textbutton _("Run again"):
                    style "uix_accent_button"
                    action Function(dev.run_test, tlabel)

                textbutton _("Tests"):
                    style "uix_button"
                    action uix.MenuTab("dev_tests")

                textbutton _("Main menu"):
                    style "uix_button"
                    action Return()
