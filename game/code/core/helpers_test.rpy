# Tests for helpers_py.rpy. Developer only; excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_helpers
#
# StateAction with a real save and load: jump test_core_state_action, then
# follow the steps on screen.

init offset = 0

init python in core_test:
    _constant = True

    import builtins

    import store
    from store import core

    core.register_kind("core_test_spot", False, id_parts=2, asset_dir="core_test_world/spots")

    ACTION_CALLS = builtins.list()

    def note_call(*args, **kwargs):
        ACTION_CALLS.append((args, kwargs))
        return "ignored"

    # Loads seen this session, to check that test_core_state_action really
    # went through a load.
    LOAD_COUNT = 0
    LOADS_BEFORE = 0

    def count_loads():
        global LOAD_COUNT
        LOAD_COUNT += 1

    def mark_loads():
        global LOADS_BEFORE
        LOADS_BEFORE = LOAD_COUNT

    def helpers_init_checks():
        c = Checks("init")

        for bad in ("Bad Dir", "/images", "a//b", "a/../b", "a/", 5):
            c.raises("register_kind: asset_dir %r" % (bad,), ValueError, core.register_kind, "core_test_bad", False, 1, bad)
        c.check("register_kind: failed calls register nothing", "core_test_bad" not in core.KINDS)

        return c

    HELPERS_INIT = helpers_init_checks()

    def helpers_checks():
        c = Checks("core: helpers")
        c.extend(HELPERS_INIT)

        # label_for.
        c.equal("label_for",
            (
                core.label_for("core_test", "alpha"),
                core.label_for("core_test", "alpha", "chat"),
                core.label_for("core_test_place", "town.home.living_room"),
                core.label_for("core_test_place", "town.home.living_room", "look"),
                ),
            (
                "core_test__alpha",
                "core_test__alpha__chat",
                "core_test_place__town__home__living_room",
                "core_test_place__town__home__living_room__look",
                ))
        c.equal("label_for: the definition needn't exist", core.label_for("core_test", "not_made"), "core_test__not_made")
        c.equal("label_for: an unregistered kind takes any dotted id",
            core.label_for("core_test_adv", "cave.door_1", "open"), "core_test_adv__cave__door_1__open")
        c.raises("label_for: an id of the wrong shape for its kind", ValueError, core.label_for, "core_test_place", "town.home")
        c.raises("label_for: bad id", ValueError, core.label_for, "core_test_adv", "Cave")
        c.raises("label_for: bad kind", ValueError, core.label_for, "Core Test", "alpha")
        for verb in ("Chat", "a__b", "", "look.at", 5):
            c.raises("label_for: verb %r" % (verb,), ValueError, core.label_for, "core_test", "alpha", verb)

        # asset.
        c.equal("asset: the folder is the kind by default", core.asset("core_test", "alpha", "icon.webp"), "images/core_test/alpha/core_test__alpha__icon.webp")
        c.equal("asset: dotted id, several parts",
            core.asset("core_test_place", "town.home.living_room", "bg", "0.webp"),
            "images/core_test_place/town/home/living_room/core_test_place__town__home__living_room__bg__0.webp")
        c.equal("asset: asset_dir",
            core.asset("core_test_spot", "town.square", "bg_0.webp"), "images/core_test_world/spots/town/square/core_test_spot__town__square__bg_0.webp")
        c.equal("asset: no parts gives the folder", core.asset("core_test_spot", "town.square"), "images/core_test_world/spots/town/square")
        c.equal("asset: an unregistered kind",
            core.asset("core_test_adv", "cave.door_1", "open.webp"), "images/core_test_adv/cave/door_1/core_test_adv__cave__door_1__open.webp")
        c.equal("asset: the file name starts with the label name",
            core.asset("core_test_place", "town.home.hall", "bg_0.webp").rsplit("/", 1)[1], core.label_for("core_test_place", "town.home.hall") + "__bg_0.webp")
        c.check("asset: same id and file in two kinds give two file names",
            core.asset("core_test", "alpha", "icon.webp").rsplit("/", 1)[1] != core.asset("core_test_other", "alpha", "icon.webp").rsplit("/", 1)[1])
        for part in ("BG.webp", "a/b.webp", "..", "", "bg 0.webp", "a__b.webp", "bg_.webp", 5):
            c.raises("asset: part %r" % (part,), ValueError, core.asset, "core_test", "alpha", part)
        c.raises("asset: an extension before the last part", ValueError, core.asset, "core_test", "alpha", "bg.webp", "0")

        # StateAction (save and load: test_core_state_action).
        del ACTION_CALLS[:]
        action = core.StateAction(note_call, 1, x=2)
        c.check("StateAction is a screen action", isinstance(action, store.Action))
        c.equal("StateAction calls fn and returns None, so the screen stays up",
            (action(), builtins.list(ACTION_CALLS)), (None, [ ((1,), { "x": 2 }) ]))
        c.check("StateActions with the same function and arguments are equal", core.StateAction(note_call, 1, x=2) == action)
        c.check("...and differ otherwise", core.StateAction(note_call, 2, x=2) != action and core.StateAction(len, 1, x=2) != action)

        return c

    def state_action_checks():
        c = Checks("core: StateAction, save and load")
        c.check("a save was loaded while the screen was up", LOAD_COUNT > LOADS_BEFORE, "save and load while the test screen is up")
        c.equal("the change made by StateAction was kept", core.flag("core_test", "alpha", "count"), 42)
        return c


init offset = 100

init python in core_test:
    core.connect("game_loaded", count_loads)


screen core_test_state_action():
    zorder 200

    add Solid("#000000e0")

    $ count = core.flag("core_test", "alpha", "count")

    frame:
        align (0.5, 0.5)
        padding (40, 40)

        vbox:
            spacing 20

            text "StateAction test" size 32
            text "1. Press Set: the count becomes 42.\n2. Open the game menu and save, with this screen still up.\n3. Load that save.\n4. The count should still be 42. Press Done."
            text "count = [count]"

            hbox:
                spacing 40
                textbutton _("Set") action core.StateAction(core.set_flag, "core_test", "alpha", "count", 42)
                textbutton _("Done") action Return()


label test_core_helpers:
    $ core_test_result = core_test.helpers_checks().report()
    call screen core_test_report(core_test_result)
    return

label test_core_state_action:
    $ core.set_flag("core_test", "alpha", "count", 0)
    $ core_test.mark_loads()
    call screen core_test_state_action
    $ core_test_result = core_test.state_action_checks().report()
    call screen core_test_report(core_test_result)
    return
