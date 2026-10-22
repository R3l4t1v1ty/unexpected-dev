# Tests for req_py.rpy. Developer only; excluded from builds.
# Runs on a new-game gs, so the game you're in isn't changed.
#
# Run: start a game, press Shift+O, type: jump test_core_req

init offset = 0

init python in core_test:
    _constant = True

    import types

    from store import core, Req, ReqAll, ReqAny, ReqNot, ReqFlag, ReqSlot, ReqDay, ReqTwin

    class ReqConst(Req):
        """
        Always `value`, for truth tables.
        """

        def __init__(self, value, text=None):
            super().__init__(text)
            self.value = value

        def check(self, twin=None):
            return self.value

        def __repr__(self):
            return "ReqConst(%r)" % (self.value,)

    T = ReqConst(True)
    F = ReqConst(False)

    def set_clock(gs, twin, day, slot):
        ts = gs.twins[twin]
        ts.day = day
        ts.slot = slot

    def req_checks():
        c = Checks("core: req")
        living = "town.home.living_room"
        pairs = ((T, T), (T, F), (F, T), (F, F))

        with fresh_gs() as gs:

            # Combining.
            c.equal("ReqAll truth table", [ ReqAll(a, b).check() for a, b in pairs ], [ True, False, False, False ])
            c.equal("ReqAny truth table", [ ReqAny(a, b).check() for a, b in pairs ], [ True, True, True, False ])
            c.equal("ReqNot", (ReqNot(T).check(), ReqNot(F).check()), (False, True))
            c.equal("empty ReqAll is True, empty ReqAny is False", (ReqAll().check(), ReqAny().check()), (True, False))
            c.equal("nested", (ReqAll(T, ReqAny(F, ReqNot(F))).check(), ReqAny(F, ReqAll(T, F)).check()), (True, False))

            # Slots.
            results = [ ]
            for s in core.SLOTS:
                set_clock(gs, "ayumu", 1, s)
                results.append(ReqSlot(core.MORNING, core.EVENING).check())
            c.equal("ReqSlot(MORNING, EVENING) through a day", results, [ True, False, True, False ])

            # Days.
            for req, expected in (
                    (ReqDay(min=3), [ False, False, True, True, True ]),
                    (ReqDay(max=3), [ True, True, True, False, False ]),
                    (ReqDay(2, 4), [ False, True, True, True, False ]),
                    (ReqDay(3, 3), [ False, False, True, False, False ]),
                    ):
                results = [ ]
                for d in range(1, 6):
                    set_clock(gs, "ayumu", d, 0)
                    results.append(req.check())
                c.equal("%r on days 1 to 5" % (req,), results, expected)

            # Twins: check(twin) looks at that twin.
            set_clock(gs, "ayumu", 1, core.MORNING)
            set_clock(gs, "nemu", 4, core.EVENING)
            c.equal("ReqTwin",
                (ReqTwin("nemu").check(), ReqTwin("nemu").check("nemu"), ReqTwin("ayumu").check()), (False, True, True))

            req = ReqAll(ReqTwin("nemu"), ReqSlot(core.EVENING), ReqDay(min=4))
            c.equal("check(twin) uses that twin's clock", (req.check(), req.check("nemu")), (False, True))
            core.swap()
            c.equal("check() follows the twin being played", req.check(), True)
            core.swap()

            # Flags.
            c.equal("ReqFlag on defaults",
                (ReqFlag("core_test", "alpha", "seen").check(), ReqFlag("core_test", "alpha", "seen", False).check()), (False, True))
            core.set_flag("core_test", "alpha", "seen", True)
            core.set_flag("core_test", "alpha", "count", 7)
            c.equal("ReqFlag on set flags",
                (ReqFlag("core_test", "alpha", "seen").check(), ReqFlag("core_test", "alpha", "count", 7).check(), ReqFlag("core_test", "alpha", "count", 6).check()),
                (True, True, False))
            core.set_flag("core_test_place", living, "visited", True, "nemu")
            req = ReqFlag("core_test_place", living, "visited")
            c.equal("ReqFlag on a per-twin flag", (req.check(), req.check("nemu")), (False, True))

            # No side effects.
            before = snapshot(gs)
            for twin in (None, "ayumu", "nemu"):
                for r in (ReqSlot(0), ReqDay(min=2), ReqTwin("nemu"), ReqFlag("core_test", "alpha", "ratio", 0.5), ReqFlag("core_test_place", living, "visited")):
                    r.check(twin)
            c.check("checking changes nothing in gs", snapshot(gs) == before)

        # Bad Reqs.
        c.raises("ReqSlot()", ValueError, ReqSlot)
        c.raises("ReqSlot(4)", ValueError, ReqSlot, 4)
        c.raises("ReqDay()", ValueError, ReqDay)
        c.raises("ReqDay(min=0)", ValueError, ReqDay, 0)
        c.raises("ReqDay(min=5, max=3)", ValueError, ReqDay, 5, 3)
        c.raises("ReqDay(min=1.5)", ValueError, ReqDay, 1.5)
        c.raises("ReqTwin('eve')", ValueError, ReqTwin, "eve")
        c.raises("ReqAll of a non-Req", TypeError, ReqAll, T, 5)
        c.raises("ReqNot of a non-Req", TypeError, ReqNot, True)
        c.raises("ReqFlag with a list value", ValueError, ReqFlag, "core_test", "alpha", "count", [ ])
        c.raises("a Req subclass without check()", NotImplementedError, Req().check)

        # Validation.
        c.equal("validate: all good", ReqAll(ReqFlag("core_test", "alpha", "seen"), ReqSlot(0)).validate(), [ ])

        problems = ReqAll(
            ReqFlag("core_test", "alpha", "cuont"),
            ReqAny(ReqNot(ReqFlag("core_test", "delta", "seen")), ReqFlag("core_tset", "alpha", "seen")),
            ).validate()
        c.check("validate finds each bad reference, nested",
            len(problems) == 3 and "'count'" in problems[0] and "'delta'" in problems[1] and "'core_test'" in problems[2],
            problems)

        thing = types.SimpleNamespace(
            requires=ReqFlag("core_test", "alpha", "cuont"),
            options=(ReqSlot(0), ReqFlag("core_test", "gone", "seen")),
            by_name={ "x": ReqFlag("core_test", "alpha", "seen") },
            other=5,
            )
        problems = core.req_problems_of(thing, "thing")
        c.check("Reqs held by a definition's attributes are found",
            len(problems) == 2 and problems[0].startswith("  thing.requires:") and problems[1].startswith("  thing.options:"),
            problems)

        # Text.
        c.equal("describe: slots", ReqSlot(core.MORNING, core.EVENING).describe(), "Morning or Evening")
        c.equal("describe: days",
            tuple(r.describe() for r in (ReqDay(min=3), ReqDay(max=5), ReqDay(2, 4), ReqDay(3, 3))),
            ("From day 3", "Until day 5", "Days 2 to 4", "Day 3"))
        c.equal("describe: twin", ReqTwin("nemu").describe(), "Only as Nemu")
        c.equal("describe: a flag without text", ReqFlag("core_test", "alpha", "seen").describe(), None)
        c.equal("describe: text given", ReqFlag("core_test", "alpha", "seen", text="Meet Alpha first").describe(), "Meet Alpha first")
        c.equal("describe: ReqAll skips parts without text",
            ReqAll(ReqSlot(core.EVENING), ReqFlag("core_test", "alpha", "seen"), ReqDay(min=3)).describe(), "Evening · From day 3")
        c.equal("describe: ReqAny needs text for every part",
            (ReqAny(ReqSlot(0), ReqDay(min=3)).describe(), ReqAny(ReqSlot(0), ReqFlag("core_test", "alpha", "seen")).describe()),
            ("Morning or From day 3", None))
        c.equal("describe: ReqNot without text", ReqNot(ReqSlot(0)).describe(), None)
        c.equal("twin_name", (core.twin_name("ayumu"), core.twin_name("nemu")), ("Ayumu", "Nemu"))

        c.equal("repr",
            repr(ReqAll(ReqSlot(0, 2), ReqNot(ReqDay(min=3)), ReqTwin("nemu"), ReqFlag("core_test", "alpha", "count", 7))),
            "ReqAll(ReqSlot(0, 2), ReqNot(ReqDay(min=3, max=None)), ReqTwin('nemu'), ReqFlag('core_test', 'alpha', 'count', 7))")

        return c


label test_core_req:
    $ core_test_result = core_test.req_checks().report()
    call screen core_test_report(core_test_result)
    return
