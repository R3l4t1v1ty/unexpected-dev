## Test menu: every label named test_<folder>_<name>, grouped by folder, in the
## game-menu tab "Tests" (also on the main menu) and on Shift+T.
##
## A test runs in a fresh game: dev.run_test() keeps the label in
## persistent.dev_pending_test and restarts Ren'Py into label dev_run_test
## (tests.rpy), which starts a new game, calls the test, then shows
## dev_test_done. A test passes if it returns; it may return a string to show
## as a note. A failure is an exception, on Ren'Py's error screen.
## Developer mode only.

init offset = -300

init python:

    class ReqDevMode(Req):
        """Met while developer mode is on. Shows dev/'s game-menu tab."""

        def check(self, twin=None):
            return bool(config.developer)


init python in dev:
    _constant = True

    import store
    from store import core, uix, renpy

    ## game/code/ folders, in the menu's order. Other names come after, A to Z.
    FOLDERS = ("core", "world", "characters", "factions", "events", "rpg", "physics", "adventure",
        "computer", "minigames", "progress", "fx", "ui", "story", "dev")

    def find_tests(labels):
        """((folder, ((label, name), ...)), ...) for every test_<folder>_<name> label."""

        groups = { }

        for label in labels:
            if not label.startswith("test_") or "." in label:
                continue

            folder, sep, name = label[5:].partition("_")

            if not folder:
                continue

            groups.setdefault(folder, [ ]).append((label, name or label))

        def order(folder):
            if folder in FOLDERS:
                return (FOLDERS.index(folder), folder)
            return (len(FOLDERS), folder)

        return tuple((folder, tuple(sorted(groups[folder]))) for folder in sorted(groups, key=order))

    def in_test_game():
        """True in a game that dev_run_test started."""

        return getattr(store, "dev_test_label", None) is not None

    def run_test(label):
        """Restarts Ren'Py into a fresh game that runs the test `label`."""

        store.persistent.dev_pending_test = label
        renpy.full_restart(transition=None, label="dev_run_test")

    def run_action(label):
        """The action of a test's button: asks first when it would end a game."""

        action = store.Function(run_test, label)

        if store.main_menu or in_test_game():
            return action

        return store.Confirm(_("Run this test? This game ends and a fresh one starts. Unsaved progress is lost."), action)

    def take_pending():
        """The test label dev_run_test should run, or None. Clears it."""

        label = store.persistent.dev_pending_test
        store.persistent.dev_pending_test = None

        if label is None or not renpy.has_label(label):
            return None

        return label

    def mark_done(label, note):
        """Records that a test returned, with its note (a string) if any."""

        if store.persistent.dev_test_runs is None:
            store.persistent.dev_test_runs = { }

        store.persistent.dev_test_runs[label] = note if isinstance(note, str) else None

    def result(label):
        """(ran, note): whether the test returned this session, and its note."""

        runs = store.persistent.dev_test_runs or { }

        if label in runs:
            return (True, runs[label])

        return (False, None)

    def open_tests():
        if on():
            renpy.run(uix.MenuTab("dev_tests"))


init offset = 100

init python in dev:

    ## Every label exists once the script is loaded, so this never changes.
    TESTS = find_tests(renpy.get_all_labels())

    ## Tests that returned this session (since Ren'Py started or Shift+R):
    ## label -> note. Kept in persistent because a test run restarts Ren'Py.
    store.persistent.dev_test_runs = { }

    uix.register_menu_tab("dev_tests", _("Tests"), "dev_tests_tab", order=950,
        requires=store.ReqDevMode(), group="story", main_menu=True)

    ## Shift+T: test menu. F9: debug overlay (overlay_scr.rpy).
    store.config.keymap["dev_tests"] = [ "T", "shift_K_t" ]
    store.config.keymap["dev_overlay"] = [ "K_F9" ]
    store.config.underlay.append(renpy.Keymap(dev_tests=open_tests, dev_overlay=toggle_overlay))

    store.config.overlay_screens.append("dev_overlay")
