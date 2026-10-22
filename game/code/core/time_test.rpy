# Tests for time_py.rpy. Developer only; excluded from builds.
# Runs on a new-game gs, so the game you're in isn't changed.
#
# Run: start a game, press Shift+O, type: jump test_core_time

init offset = 0

init python in core_test:
    _constant = True

    from store import core

    def now(twin=None):
        return (core.day(twin), core.slot(twin))

    def time_checks():
        c = Checks("core: time")

        c.equal("SLOTS and their names",
            (core.SLOTS, core.MORNING, core.AFTERNOON, core.EVENING, core.NIGHT), ((0, 1, 2, 3), 0, 1, 2, 3))
        c.equal("slot_name", tuple(core.slot_name(i) for i in core.SLOTS), ("Morning", "Afternoon", "Evening", "Night"))
        c.raises("slot_name: not a slot", ValueError, core.slot_name, 4)
        c.raises("slot_name: not a number", ValueError, core.slot_name, "0")

        with fresh_gs():
            c.equal("a new game starts on day 1, morning", now(), (1, 0))

            start_recording()
            core.advance()
            c.equal("advance()", now(), (1, 1))
            core.advance(2)
            c.equal("advance(2)", now(), (1, 3))
            core.advance()
            c.equal("advancing past night goes to the next morning", now(), (2, 0))
            core.advance(4 * 3 + 2)
            c.equal("advancing across several days", now(), (5, 2))
            core.advance(0)
            c.equal("advance(0) does nothing", now(), (5, 2))
            core.sleep()
            c.equal("sleep: next day, morning", now(), (6, 0))
            core.sleep()
            c.equal("sleeping in the morning still goes to the next day", now(), (7, 0))
            c.equal("time_changed after each change", stop_recording(), [
                ("time_changed", "ayumu", 1, 1),
                ("time_changed", "ayumu", 1, 3),
                ("time_changed", "ayumu", 2, 0),
                ("time_changed", "ayumu", 5, 2),
                ("time_changed", "ayumu", 6, 0),
                ("time_changed", "ayumu", 7, 0),
                ])

            c.raises("advance(-1)", ValueError, core.advance, -1)
            c.raises("advance(1.5)", ValueError, core.advance, 1.5)
            c.raises("advance(True)", ValueError, core.advance, True)
            c.equal("bad advances change nothing", now(), (7, 0))

            c.equal("each twin has their own clock", (now("ayumu"), now("nemu")), ((7, 0), (1, 0)))

            start_recording()
            core.swap()
            core.advance()
            c.equal("time acts on the twin being played", (now("ayumu"), now()), ((7, 0), (1, 1)))
            c.equal("time_changed names that twin", stop_recording(), [ ("twin_swapped", "nemu"), ("time_changed", "nemu", 1, 1) ])

            c.raises("day of an unknown twin", ValueError, core.day, "eve")
            c.raises("slot of an unknown twin", ValueError, core.slot, "eve")

        return c


label test_core_time:
    $ core_test_result = core_test.time_checks().report()
    call screen core_test_report(core_test_result)
    return
