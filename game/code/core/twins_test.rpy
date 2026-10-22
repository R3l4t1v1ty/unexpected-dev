# Tests for twins_py.rpy. Developer only; excluded from builds.
# Runs on a new-game gs, so the game you're in isn't changed.
#
# Run: start a game, press Shift+O, type: jump test_core_twins

init offset = 0

init python in core_test:
    _constant = True

    import store
    from store import core

    def twins_checks():
        c = Checks("core: twins")
        living = "town.home.living_room"

        with fresh_gs() as gs:
            c.equal("TWINS", core.TWINS, ("ayumu", "nemu"))
            c.equal("a new game starts with the first twin", core.me(), "ayumu")
            c.equal("other", (core.other(), core.other("ayumu"), core.other("nemu")), ("nemu", "nemu", "ayumu"))

            start_recording()
            core.swap()
            c.equal("swap() switches to the other twin", (core.me(), gs.twin), ("nemu", "nemu"))
            core.swap("nemu")
            c.equal("swapping to the twin being played does nothing", core.me(), "nemu")
            core.swap("ayumu")
            c.equal("swap(twin)", core.me(), "ayumu")
            c.equal("twin_swapped is emitted for each change", stop_recording(), [ ("twin_swapped", "nemu"), ("twin_swapped", "ayumu") ])

            c.raises("swap to an unknown twin", ValueError, core.swap, "eve")
            c.raises("other of an unknown twin", ValueError, core.other, "eve")
            c.equal("an unknown twin changes nothing", core.me(), "ayumu")

            core.swap()
            core.set_flag("core_test_place", living, "visited", True)
            c.equal("per-twin flags follow the twin being played",
                (core.flag("core_test_place", living, "visited", "ayumu"), core.flag("core_test_place", living, "visited", "nemu")), (False, True))

        c.check("the real gs is back afterwards", store.gs is not gs)

        return c


label test_core_twins:
    $ core_test_result = core_test.twins_checks().report()
    call screen core_test_report(core_test_result)
    return
