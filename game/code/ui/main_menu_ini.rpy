## Main menu content: art sets, links, changelog.
##
## Placeholders until the art exists. Positions and motion are the old game's:
## a 2080×1170 background travelling 80×30 px with the mouse, and nine
## floating items travelling 40×15 px and bobbing. To add a layer that only
## shows when clicked (e.g. a twin over one side), give it toggle="some_id"
## and add a hotspot: uix.add_main_menu_hotspot(set_id, "some_id", (x, y, w, h)).

init offset = 0

init python in uix:

    import store

    ## (x, y, bob) of the nine floating items; bob is (dx, dy, dzoom, period).
    MAIN_MENU_ITEMS = [
        (556, 98, (2, 15, -0.05, 3.4)),
        (727, 390, (7, 19, -0.07, 3.4)),
        (755, 150, (2, 15, 0.02, 3.4)),
        (1000, 126, (7, 15, 0.03, 3.4)),
        (1196, 159, (7, 15, 0.03, 3.4)),
        (1207, 490, (7, 15, 0.03, 3.4)),
        (694, 365, (7, 15, 0.03, 3.4)),
        (1079, 295, (7, 15, 0.03, 3.4)),
        (930, 393, (7, 15, 0.03, 3.4)),
        ]

    def add_placeholder_set(id, name, bg_color, item_color):

        add_main_menu_set(id, name, preview=placeholder(name, (384, 216), color=bg_color))

        add_main_menu_layer(id, placeholder("background " + id, (2080, 1170), color=bg_color, text_color="#ffffff20"),
            pos=(-100, -65), move=(80, 30))

        for n, (x, y, bob) in enumerate(MAIN_MENU_ITEMS):
            add_main_menu_layer(id, placeholder("item %d" % (n + 1), (110, 110), color=item_color),
                pos=(x, y), move=(40, 15), bob=bob)

    add_placeholder_set("set_1", _("Set 1"), "#1d1420", "#3a2433")
    add_placeholder_set("set_2", _("Set 2"), "#0d1024", "#202a4a")

    ## Links: no URLs yet (the user adds them). Without a URL a link is hidden,
    ## except in developer mode.
    add_main_menu_link("discord", _("Discord"), placeholder("Discord", (60, 60)))
    add_main_menu_link("patreon", _("Patreon"), placeholder("Patreon", (60, 60)))
    add_main_menu_link("twitter", _("Twitter"), placeholder("Twitter", (60, 60)))
    add_main_menu_link("itch", _("itch.io"), placeholder("itch", (60, 60)))

    ## A sample changelog section, in developer mode only, so the panel can be
    ## checked before there's a real changelog.
    if store.config.developer:
        add_changelog(_("Sample"), _("Changelog sections go here: uix.add_changelog(title, text) at init."))
