## Content check report, shown by the test menu's Run button.

init offset = 0

screen dev_report(problems):

    modal True
    zorder 300
    style_prefix "dev"

    key "game_menu" action Hide("dev_report")

    frame:
        style "dev_panel"
        align (0.5, 0.5)
        xsize int(config.screen_width * 0.8)

        vbox:
            spacing 12

            text _("Content check") style "dev_title"

            viewport:
                xfill True
                yfill False
                ymaximum int(config.screen_height * 0.7)
                mousewheel True
                draggable True

                vbox:
                    spacing 6

                    if not problems:
                        text _("No problems found.")

                    for source, problem in problems:
                        text dev.plain("%s: %s" % (source, problem)) substitute False

            textbutton _("Close") action Hide("dev_report")
