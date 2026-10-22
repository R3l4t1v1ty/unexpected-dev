# Tests for signals_py.rpy. Developer only; excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_signals
#
# Also holds the recording handlers that twins_test.rpy and time_test.rpy use
# to see which signals were emitted.

init offset = 0

init python in core_test:
    _constant = True

    import builtins
    import contextlib

    import store
    from store import core

    # Calls seen by the test handlers while recording.
    CALLS = builtins.list()
    RECORDING = False

    def record(*call):
        if RECORDING:
            CALLS.append(call)

    def start_recording():
        global RECORDING
        del CALLS[:]
        RECORDING = True

    def stop_recording():
        """
        Stops recording and returns the calls seen, as a list of tuples.
        """
        global RECORDING
        RECORDING = False
        rv = builtins.list(CALLS)
        del CALLS[:]
        return rv

    @contextlib.contextmanager
    def fresh_gs():
        """
        Runs the with block on a new-game gs, then puts the real one back.
        """
        old = store.gs
        store.gs = core.GameState()
        try:
            yield store.gs
        finally:
            store.gs = old

    def on_ping_1(value):
        record("ping_1", value)

    def on_ping_2(value):
        record("ping_2", value)

    def on_bang():
        record("bang")
        raise RuntimeError("bang (raised on purpose by the test)")

    def on_after_bang():
        record("after_bang")

    def on_time_changed(twin, day, slot):
        record("time_changed", twin, day, slot)

    def on_twin_swapped(twin):
        record("twin_swapped", twin)

    core.register_signal("core_test_ping", "value")
    core.register_signal("core_test_bang")
    core.register_signal("core_test_quiet")


init offset = 100

init python in core_test:
    core.connect("core_test_ping", on_ping_1)
    core.connect("core_test_ping", on_ping_2)
    core.connect("core_test_bang", on_bang)
    core.connect("core_test_bang", on_after_bang)
    core.connect("time_changed", on_time_changed)
    core.connect("twin_swapped", on_twin_swapped)

    def signals_init_checks():
        c = Checks("init")

        c.raises("register_signal: same signal twice", ValueError, core.register_signal, "core_test_ping", "value")
        c.raises("register_signal: bad name", ValueError, core.register_signal, "Core Test")
        c.raises("register_signal: bad argument name", ValueError, core.register_signal, "core_test_bad", "Value")
        c.raises("register_signal: argument twice", ValueError, core.register_signal, "core_test_bad", "a", "a")
        c.check("register_signal: failed calls register nothing", "core_test_bad" not in core.SIGNALS)

        c.raises("connect: not callable", TypeError, core.connect, "core_test_ping", 5)
        c.raises("connect: bad name", ValueError, core.connect, "Core Test", on_ping_1)
        c.equal("connect: failed calls connect nothing", builtins.list(core.HANDLERS["core_test_ping"]), [ on_ping_1, on_ping_2 ])

        problems = core.unknown_connections([ ("core_test_ping", "here:1"), ("core_test_pnig", "here:2") ])
        c.check("connections to unknown signals are found",
            len(problems) == 1 and "core_test_pnig" in problems[0] and "here:2" in problems[0] and "core_test_ping" in problems[0],
            problems)

        return c

    SIGNALS_INIT = signals_init_checks()

    def signals_checks():
        c = Checks("core: signals")
        c.extend(SIGNALS_INIT)

        c.equal("core's signals",
            tuple(core.SIGNALS[i] for i in ("game_started", "game_loaded", "time_changed", "twin_swapped")),
            ((), (), ("twin", "day", "slot"), ("twin",)))
        c.check("handlers are read-only after init", type(core.HANDLERS["core_test_ping"]) is tuple)

        start_recording()
        core.emit("core_test_ping", value=1)
        c.equal("emit calls the handlers in connection order", stop_recording(), [ ("ping_1", 1), ("ping_2", 1) ])

        start_recording()
        core.emit("core_test_quiet")
        c.equal("emit with no handlers", stop_recording(), [ ])

        if renpy.config.developer:
            c.raises("emit: unknown signal", LookupError, core.emit, "core_test_pnig", value=1)
            c.raises("emit: missing argument", TypeError, core.emit, "core_test_ping")
            c.raises("emit: extra argument", TypeError, core.emit, "core_test_ping", value=1, other=2)
            c.raises("emit: misspelled argument", TypeError, core.emit, "core_test_ping", valeu=1)

            start_recording()
            c.raises("developer mode: an error in a handler propagates", RuntimeError, core.emit, "core_test_bang")
            c.equal("developer mode: ...and stops the handlers after it", stop_recording(), [ ("bang",) ])
        else:
            c.check("developer mode checks", False, "need developer mode")

        start_recording()
        c.no_raise("release: an error in a handler is logged", core.call_handlers, "core_test_bang", { }, False)
        c.equal("release: the other handlers still run", stop_recording(), [ ("bang",), ("after_bang",) ])
        c.check("release: Ren'Py's jumps and calls aren't swallowed",
            renpy.game.JumpException in core.CONTROL_EXCEPTIONS and renpy.game.CallException in core.CONTROL_EXCEPTIONS,
            core.CONTROL_EXCEPTIONS)

        c.raises("connect after init", core.FrozenError, core.connect, "core_test_ping", on_ping_1)
        c.raises("register_signal after init", core.FrozenError, core.register_signal, "core_test_late")
        c.equal("nothing connected after init", core.HANDLERS["core_test_ping"], (on_ping_1, on_ping_2))

        return c


label test_core_signals:
    $ core_test_result = core_test.signals_checks().report()
    call screen core_test_report(core_test_result)
    return
