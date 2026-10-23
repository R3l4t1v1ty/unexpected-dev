## Main menu data: art sets made of layers, social links, and the changelog.
##
## An art set is a stack of layers, drawn in the order added. Each layer moves
## with the mouse (parallax) and can bob up and down. On touch devices, where
## there's no mouse, the layers drift slowly on their own; with reduced motion
## (persistent.fx_reduced_motion) they stand still. The player picks the set
## in the main menu's corner; the newest set is the default.

init offset = -400

init python in uix:

    import store
    import math

    class MainMenuLayer(object):
        """
        One layer of an art set. Built at init and never changed afterwards.
        """

        def __init__(self, image, pos, move, bob, toggle):
            self.image = image
            self.x, self.y = pos
            self.move_x, self.move_y = move
            self.bob = bob
            self.toggle = toggle

        def update(self, trans, st, at):
            """
            The ATL function that places the layer (see uix_mm_move).
            """

            trans.subpixel = True

            if store.persistent.fx_reduced_motion:
                trans.xpos = self.x
                trans.ypos = self.y
                trans.xoffset = 0
                trans.yoffset = 0
                trans.zoom = 1.0
                return None

            if renpy.variant("touch"):
                fx = 0.5 + 0.35 * math.sin(st * 0.25)
                fy = 0.5 + 0.35 * math.sin(st * 0.18 + 1.0)
            else:
                mx, my = renpy.get_mouse_pos()
                fx = mx / float(store.config.screen_width)
                fy = my / float(store.config.screen_height)

            ## absolute(): a plain float position would mean a fraction of
            ## the screen, not pixels.
            trans.xpos = absolute(self.x + self.move_x * (fx - 0.5))
            trans.ypos = absolute(self.y + self.move_y * (fy - 0.5))

            if self.bob is not None:
                dx, dy, dzoom, period = self.bob
                phase = math.sin(st * 2.0 * math.pi / period)
                trans.xoffset = dx * phase
                trans.yoffset = -dy * phase
                trans.zoom = 1.0 + dzoom * phase

            return 0

    class MainMenuHotspot(object):
        """
        An invisible button that shows or hides the layers of one toggle.
        """

        def __init__(self, toggle, rect):
            self.toggle = toggle
            self.x, self.y, self.w, self.h = rect

    class MainMenuSet(object):
        """
        One art set. Built at init and never changed afterwards.
        """

        def __init__(self, id, name, preview):
            self.id = id
            self.name = name
            self.preview = preview
            self.layers = [ ]
            self.hotspots = [ ]

    main_menu_sets = {}
    main_menu_set_list = []

    def add_main_menu_set(id, name, preview=None):
        """
        Adds an art set (at init). `preview` is a small image shown in the
        set picker; None shows the set's name.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_main_menu_set must be called at init.")

        if id in main_menu_sets:
            raise Exception("Main-menu set %r is added twice." % (id,))

        s = MainMenuSet(id, name, preview)
        main_menu_sets[id] = s
        main_menu_set_list.append(s)

    def add_main_menu_layer(set_id, image, pos=(0, 0), move=(0, 0), bob=None, toggle=None):
        """
        Adds a layer on top of the set's others (at init).

        `pos`: (x, y) of the layer when the mouse is in the middle of the
        screen. `move`: how far, in pixels, the layer travels as the mouse
        crosses the screen, (x, y); a background bigger than the screen needs
        margins of half that on each side. `bob`: None, or (dx, dy, dzoom,
        period), the layer swaying by dx and dy pixels and zooming by dzoom
        over `period` seconds. `toggle`: None, or the id of a toggle; the
        layer then shows only while a hotspot has switched that toggle on.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_main_menu_layer must be called at init.")

        main_menu_sets[set_id].layers.append(MainMenuLayer(image, pos, move, bob, toggle))

    def add_main_menu_hotspot(set_id, toggle, rect):
        """
        Adds an invisible button over `rect` (x, y, width, height) that
        switches the layers of `toggle` on and off (at init).
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_main_menu_hotspot must be called at init.")

        main_menu_sets[set_id].hotspots.append(MainMenuHotspot(toggle, rect))

    def main_menu_set():
        """
        The art set the player picked, or the newest one.
        """

        rv = main_menu_sets.get(store.persistent.uix_mm_set, None)

        if rv is None:
            rv = main_menu_set_list[-1]

        return rv

    def main_menu_buttons():
        """
        The main-menu buttons, as (label, action) pairs.
        """

        rv = [
            (_("Start"), store.Start()),
            (_("Load"), MenuTab("load")),
            (_("Options"), MenuTab("preferences")),
            (_("About"), MenuTab("about")),
            ]

        if pc_like():
            rv.append((_("Help"), MenuTab("help")))

        ## Quit is banned on iOS and pointless on Android and web.
        if renpy.variant("pc"):
            rv.append((_("Quit"), store.Quit(confirm=False)))

        return rv

    class MainMenuLink(object):

        def __init__(self, id, name, icon, url):
            self.id = id
            self.name = name
            self.icon = icon
            self.url = url

    main_menu_links = []

    def add_main_menu_link(id, name, icon, url=None):
        """
        Adds a link to the main menu's link bar (at init). A link without a
        url is hidden, except in developer mode, where it shows greyed out.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_main_menu_link must be called at init.")

        main_menu_links.append(MainMenuLink(id, name, icon, url))

    def visible_links():
        return [ l for l in main_menu_links if l.url or store.config.developer ]

    ## (title, text) sections of the changelog panel, in order.
    changelog = []

    def add_changelog(title, text):
        """
        Adds a section to the main menu's changelog panel (at init). The
        Changelog button only shows when there's at least one section.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_changelog must be called at init.")

        changelog.append((title, text))


default persistent.uix_mm_set = None
