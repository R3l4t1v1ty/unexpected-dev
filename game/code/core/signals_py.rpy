# Signals: how systems tell each other what happened.
#
# A signal is registered once with the names of its arguments. Handlers
# connect to it at init (the wiring band, init 100), and emit() calls them in
# the order they connected, with keyword arguments:
#
#     core.register_signal("location_entered", "twin", "location")
#     core.connect("location_entered", on_location_entered)
#     core.emit("location_entered", twin="ayumu", location="town.home.hall")
#
# In developer mode, emit() checks the signal and its arguments, and an error
# in a handler stops the game as usual. In release, the error is logged and
# the other handlers still run. Never emit signals from screens.

init offset = -500

init python in core:
    _constant = True

    import builtins
    import traceback

    # signal -> tuple of argument names. Core's own signals:
    SIGNALS = {
        "game_started": (),
        "game_loaded": (),
        "time_changed": ("twin", "day", "slot"),
        "twin_swapped": ("twin",),
        }

    # signal -> handlers in connection order (a tuple once init is over)
    HANDLERS = { }

    # (signal, "file:line") for each connect(), to report unknown signals
    CONNECTIONS = [ ]

    # Exceptions Ren'Py uses for jumps, calls, restarts...: never swallowed.
    CONTROL_EXCEPTIONS = tuple(getattr(renpy.game, "CONTROL_EXCEPTIONS", ()))

    def register_signal(signal, *args):
        """
        Registers a signal and the names of the keyword arguments it's emitted
        with. Call at init.
        """
        if frozen:
            raise FrozenError("core: signals are registered at init; tried to register %r after init." % (signal,))
        if not isinstance(signal, str) or not SEGMENT_RE.fullmatch(signal):
            raise ValueError("core: %r is not a valid signal name. Use ASCII snake_case, like 'location_entered'." % (signal,))
        if signal in SIGNALS:
            raise ValueError("core: signal %r is already registered." % (signal,))
        for a in args:
            if not isinstance(a, str) or not SEGMENT_RE.fullmatch(a):
                raise ValueError("core: signal %r: argument name %r is not ASCII snake_case." % (signal, a))
        if len(builtins.set(args)) != len(args):
            raise ValueError("core: signal %r: an argument name is repeated in %r." % (signal, args))

        SIGNALS[signal] = tuple(args)

    def connect(signal, fn):
        """
        Calls fn(**arguments) each time `signal` is emitted. Call at init (the
        wiring band, init 100). Handlers run in the order they connected.
        """
        if frozen:
            raise FrozenError("core: handlers connect at init; tried to connect to %r after init." % (signal,))
        if not isinstance(signal, str) or not SEGMENT_RE.fullmatch(signal):
            raise ValueError("core: %r is not a valid signal name." % (signal,))
        if not callable(fn):
            raise TypeError("core: connect(%r): %r can't be called." % (signal, fn))

        HANDLERS.setdefault(signal, [ ]).append(fn)
        CONNECTIONS.append((signal, source_here()))

    def emit(signal, **kwargs):
        """
        Calls the handlers of `signal` with these keyword arguments. Never
        from screens.
        """
        developer = renpy.config.developer
        if developer:
            check_emit(signal, kwargs)
        call_handlers(signal, kwargs, developer)

    def check_emit(signal, kwargs):
        """
        Raises if `signal` isn't registered or `kwargs` don't match its
        arguments.
        """
        args = SIGNALS.get(signal)
        if args is None:
            raise LookupError("core: unknown signal %r.%s Signals are added with core.register_signal()." % (signal, did_you_mean(signal, SIGNALS)))

        if builtins.set(kwargs) != builtins.set(args):
            raise TypeError("core: signal %r is emitted with %s, not %s." % (signal, names(args), names(builtins.sorted(kwargs))))

    def names(args):
        return ", ".join(args) or "no arguments"

    def call_handlers(signal, kwargs, propagate):
        """
        Calls the handlers of `signal`. If `propagate` is False, an error in
        a handler is logged and the other handlers still run.
        """
        for fn in HANDLERS.get(signal, ()):
            if propagate:
                fn(**kwargs)
                continue

            try:
                fn(**kwargs)
            except CONTROL_EXCEPTIONS:
                raise
            except Exception:
                warn("a handler of signal %r, %s, raised an error; the other handlers still run.\n%s" % (signal, describe_fn(fn), traceback.format_exc()))

    def describe_fn(fn):
        """
        A function's name for messages, like "store.world.on_time_changed".
        """
        name = getattr(fn, "__qualname__", None) or repr(fn)
        module = getattr(fn, "__module__", None)
        if module:
            return module + "." + name
        return name

    def unknown_connections(connections):
        """
        A message for each (signal, source) in `connections` whose signal was
        never registered.
        """
        rv = [ ]
        for signal, source in connections:
            if signal not in SIGNALS:
                rv.append("  %r, connected at %s.%s" % (signal, source, did_you_mean(signal, SIGNALS)))
        return rv

    def freeze_signals():
        """
        Checks that every connected signal is registered, and makes the
        handler lists read-only. Called by freeze().
        """
        problems = unknown_connections(CONNECTIONS)
        if problems:
            raise LookupError("core: handlers are connected to signals that were never registered:\n" + "\n".join(problems))

        for signal, handlers in HANDLERS.items():
            HANDLERS[signal] = tuple(handlers)
