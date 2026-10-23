## ui's own game-menu tabs (the "system" group). Systems register theirs the
## same way, in the "story" group.

init offset = 100

init python in uix:

    register_menu_tab("history", _("History"), "uix_history_page", order=10, group="system")
    register_menu_tab("save", _("Save"), "uix_save_page", order=20, group="system")
    register_menu_tab("load", _("Load"), "uix_load_page", order=30, group="system", main_menu=True)
    register_menu_tab("preferences", _("Preferences"), "uix_prefs_page", order=40, group="system", main_menu=True)
    register_menu_tab("help", _("Help"), "uix_help_page", order=50, group="system", main_menu=True, pc_only=True)
    register_menu_tab("about", _("About"), "uix_about_page", order=60, group="system", main_menu=True)
