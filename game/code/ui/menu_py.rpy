## Game-menu tabs: the registry systems plug their tabs into.
##
## A tab is a screen shown inside the game-menu shell (`uix_menu`, menu_scr.rpy).
## Tabs belong to a group: "story" (tabs systems register: Story, Characters,
## Events, Gallery, Achievements) or "system" (ui's: History, Save, Load,
## Preferences, Help, About). The shell's sidebar lists the current group's tabs
## plus one button that switches to the other group.

init offset = -400

init python in uix:

    import store

    MENU_GROUPS = ("story", "system")

    ## Shown on the button that switches to the group.
    MENU_GROUP_NAMES = {
        "story": _("Story"),
        "system": _("Game"),
        }

    class MenuTabInfo(object):
        """
        One registered tab. Built at init and never changed afterwards.
        """

        def __init__(self, id, name, screen, order, requires, group, main_menu, pc_only):
            self.id = id
            self.name = name
            self.screen = screen
            self.order = order
            self.requires = requires
            self.group = group
            self.main_menu = main_menu
            self.pc_only = pc_only

    ## id -> MenuTabInfo, and every tab sorted by (order, id). Filled at init.
    menu_tabs = {}
    menu_tab_list = []

    def register_menu_tab(id, name, screen, order=100, requires=None, group="story", main_menu=False, pc_only=False):
        """
        Adds a game-menu tab. Call at init (systems use init 100).

        `id`: snake_case, unique. `name`: the label, as _("..."). `screen`: the
        name of the screen shown in the content area; it receives the keyword
        arguments given to uix.MenuTab. `order`: lower comes first.
        `requires`: a Req; the tab is hidden while it fails. `group`: "story"
        or "system". `main_menu`: also offered from the main menu (only for
        tabs that don't need a game in progress). `pc_only`: hidden on phones,
        tablets and mobile web.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.register_menu_tab must be called at init.")

        if id in menu_tabs:
            raise Exception("Game-menu tab %r is registered twice." % (id,))

        if group not in MENU_GROUPS:
            raise Exception("Game-menu tab %r: group must be one of %r, not %r." % (id, MENU_GROUPS, group))

        if requires is not None and not hasattr(requires, "check"):
            raise Exception("Game-menu tab %r: requires must be a Req or None." % (id,))

        tab = MenuTabInfo(id, name, screen, order, requires, group, main_menu, pc_only)
        menu_tabs[id] = tab
        menu_tab_list.append(tab)
        menu_tab_list.sort(key=lambda t: (t.order, t.id))

    def menu_tab(id):
        """
        The MenuTabInfo for `id`. Raises if there's no such tab.
        """

        rv = menu_tabs.get(id, None)

        if rv is None:
            raise Exception("There is no game-menu tab %r." % (id,))

        return rv

    def has_menu_tab(id):
        """
        True if a tab `id` is registered and can be shown right now.
        """

        tab = menu_tabs.get(id, None)
        return tab is not None and tab_visible(tab)

    def pc_like():
        """
        True on a desktop (or desktop web), where Help and Quit make sense.
        """

        return renpy.variant("pc") or (renpy.variant("web") and not renpy.variant("mobile"))

    def tab_visible(tab):

        if store.main_menu and not tab.main_menu:
            return False

        if store._in_replay and tab.group == "story":
            return False

        if tab.pc_only and not pc_like():
            return False

        if tab.requires is not None and not tab.requires.check():
            return False

        return True

    def visible_tabs(group):
        """
        The tabs of `group` that can be shown right now, in order.
        """

        return [ t for t in menu_tab_list if t.group == group and tab_visible(t) ]

    def group_entry(group):
        """
        The id of the tab the group-switch button opens, or None when nothing
        in `group` can be shown.
        """

        for t in menu_tab_list:
            if t.group == group and tab_visible(t):
                return t.id

        return None

    class MenuTab(store.Action, store.DictEquality):
        """
        Opens the game menu on tab `id`. Extra keyword arguments go to the
        tab's screen, e.g. uix.MenuTab("characters", char_id="hana").
        Insensitive while the tab is hidden.
        """

        def __init__(self, id, **kwargs):
            self.id = id
            self.kwargs = kwargs

        def __call__(self):

            if not self.get_sensitive():
                return None

            return store.ShowMenu("uix_menu", self.id, **self.kwargs)()

        def get_sensitive(self):
            return has_menu_tab(self.id)

        def get_selected(self):
            return False


init offset = 900

init python in uix:

    def validate_menu_tabs():
        for tab in menu_tab_list:
            if not renpy.has_screen(tab.screen):
                raise Exception("Game-menu tab %r: there is no screen %r." % (tab.id, tab.screen))

    validate_menu_tabs()
