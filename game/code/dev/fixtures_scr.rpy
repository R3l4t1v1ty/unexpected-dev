## Fixture saves screens: the Check report (with Accept) and Record, both
## opened from the test menu.

init offset = 0

## results: (name, version, problems, differences, can_accept) per fixture,
## from dev.check_fixture.
screen dev_fixture_report(results):

    modal True
    zorder 300
    style_prefix "dev"

    key "game_menu" action Hide("dev_fixture_report")

    frame:
        style "dev_panel"
        align (0.5, 0.5)
        xsize int(config.screen_width * 0.8)

        vbox:
            spacing 12

            text _("Fixture saves") style "dev_title"

            viewport:
                xfill True
                yfill False
                ymaximum int(config.screen_height * 0.7)
                mousewheel True
                draggable True

                vbox:
                    spacing 16

                    if not results:
                        text _("No fixtures yet. Record one in a game: Tests > Fixture saves > Record this game.")

                    for fname, fversion, problems, differences, can_accept in results:

                        vbox:
                            spacing 4

                            hbox:
                                spacing 16

                                text dev.plain("%s (save version %s)" % (fname, fversion)) bold True yalign 0.5 substitute False

                                if not problems and not differences:
                                    text _("matches") color "#7bd389" yalign 0.5
                                elif can_accept:
                                    textbutton _("Accept") action Function(dev.accept_fixture, fname)

                            for line in problems:
                                text dev.plain(line) color "#ff6b6b" substitute False

                            for line in differences:
                                text dev.plain(line) style "dev_small" substitute False

            text _("Red lines need a fix in code. The others are differences from the result accepted last time: accept them once they're right.") style "dev_small"

            hbox:
                textbutton _("Check again") action Function(dev.show_fixture_report)
                textbutton _("Close") action Hide("dev_fixture_report")


screen dev_fixture_record():

    modal True
    zorder 300
    style_prefix "dev"

    default fname = dev.default_fixture_name()

    key "game_menu" action Hide("dev_fixture_record")

    frame:
        style "dev_panel"
        align (0.5, 0.5)
        xmaximum int(config.screen_width * 0.8)

        vbox:
            spacing 12

            text _("Record this game") style "dev_title"

            text _("Saves this game's state (core.snapshot) as a fixture in dev/fixtures/, with what core.migrate gives now as its expected result.") style "dev_small"

            hbox:
                text _("Name:") yalign 0.5

                frame:
                    style "dev_field"
                    input value ScreenVariableInputValue("fname") allow "abcdefghijklmnopqrstuvwxyz0123456789_" length 60

            hbox:
                textbutton _("Record") action Function(dev.record_fixture, fname)
                textbutton _("Cancel") action Hide("dev_fixture_record")
