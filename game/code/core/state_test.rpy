# Tests for state_py.rpy and saves_py.rpy: gs, flags, sections, save and load.
# Developer only; excluded from builds.
#
# Part 1: start a new game, press Shift+O, type: jump test_core_state
# It ends by asking you to save, quit Ren'Py, start it again and load. Then
# part 2: press Shift+O, type: jump test_core_state_loaded
#
# Uses the test kinds and definitions from registry_test.rpy.

init offset = 0

init python in core_test:
    _constant = True

    import copy
    import pickle

    import store
    from store import core

    LIVING = "town.home.living_room"

    SHARED_INITIAL = {
        "count": 0,
        "names": [ ],
        "seen": set(),
        "pos": (0, 0),
        "nested": { "a": { "b": 1 } },
        }

    TWIN_INITIAL = { "location": "start", "visits": 0 }

    core.register_state("core_test_shared", SHARED_INITIAL, False)
    core.register_state("core_test_twin", TWIN_INITIAL, True)

    # Part 1 sets this persistent flag, so after a restart this section is
    # registered: it stands for a section added in code after a save.
    EXTRA_REGISTERED = bool(store.persistent.core_test_extra_section)
    if EXTRA_REGISTERED:
        core.register_state("core_test_extra", { "ready": True }, True)

    def state_init_checks():
        c = Checks("init")

        c.raises("register_state: same system twice", ValueError, core.register_state, "core_test_shared", { }, False)
        c.raises("register_state: bad name", ValueError, core.register_state, "Core Test", { }, False)
        c.raises("register_state: per_twin not a bool", TypeError, core.register_state, "core_test_bad", { }, 1)
        c.raises("register_state: initial not a dict", TypeError, core.register_state, "core_test_bad", [ ], False)
        c.raises("register_state: a definition in initial", ValueError, core.register_state, "core_test_bad", { "x": { "y": [ ALPHA ] } }, False)
        c.raises("register_state: a function in initial", ValueError, core.register_state, "core_test_bad", { "f": len }, False)
        c.check("register_state: failed calls register nothing", "core_test_bad" not in core.SYSTEMS)

        SHARED_INITIAL["names"].append("changed")
        c.equal("register_state copies initial", core.SYSTEMS["core_test_shared"].initial["names"], [ ])

        return c

    STATE_INIT = state_init_checks()

    def expected_shared():
        return { "count": 0, "names": [ ], "seen": set(), "pos": (0, 0), "nested": { "a": { "b": 1 } } }

    def expected_twin():
        return { "location": "start", "visits": 0 }

    # What part 1 leaves in gs, for part 2 to find after loading.
    SAVED_FLAGS = { "alpha": { "pair": (2, ("b", None)), "label": "Saved", "count": 7 } }
    SAVED_SHARED = { "count": 1, "names": [ "saved" ], "seen": { "saved" }, "pos": (0, 0), "nested": { "a": { "b": 2 } } }
    SAVED_AYUMU = { "location": "kitchen", "visits": 2 }

    def clear_test_state(gs):
        """
        Removes what earlier test runs left in gs.
        """
        for flags in [ gs.shared["flags"] ] + [ t.flags for t in gs.twins.values() ]:
            for kind in ("core_test", "core_test_other", "core_test_place"):
                flags.pop(kind, None)

        gs.shared["sys"].pop("core_test_shared", None)
        for t in gs.twins.values():
            t.sys.pop("core_test_twin", None)

        core.ensure_sections(gs)

    def snapshot(gs):
        """
        A deep copy of everything in gs, to compare.
        """
        return copy.deepcopy((gs.version, gs.twin, gs.shared, [ (t.day, t.slot, t.flags, t.sys) for t in gs.twins.values() ]))

    def type_names(*values):
        return tuple(type(v).__name__ for v in values)

    def mro_names(cls):
        return [ k.__name__ for k in cls.__mro__ ]

    def state_checks():
        c = Checks("core: state, part 1")
        c.extend(STATE_INIT)

        gs = store.gs
        clear_test_state(gs)

        # Shape.
        c.check("gs is a GameState", type(gs) is core.GameState, type(gs))
        c.check("GameState and TwinState are rollback-safe",
            "RevertableObject" in mro_names(core.GameState) and "RevertableObject" in mro_names(core.TwinState),
            mro_names(core.GameState))
        c.equal("one TwinState per twin", [ (k, type(v).__name__) for k, v in gs.twins.items() ], [ ("ayumu", "TwinState"), ("nemu", "TwinState") ])
        c.check("current twin is a twin", gs.twin in core.TWINS, gs.twin)
        c.equal("version", gs.version, core.SAVE_VERSION)

        fresh = core.GameState()
        c.equal("new game: twin, version, days, slots",
            (fresh.twin, fresh.version, [ (t.day, t.slot) for t in fresh.twins.values() ]),
            ("ayumu", core.SAVE_VERSION, [ (1, 0), (1, 0) ]))
        c.equal("new game: no flags", (fresh.shared["flags"], fresh.twins["ayumu"].flags, fresh.twins["nemu"].flags), ({ }, { }, { }))
        c.equal("new game: sections made",
            (fresh.shared["sys"]["core_test_shared"], fresh.twins["ayumu"].sys["core_test_twin"], fresh.twins["nemu"].sys["core_test_twin"]),
            (expected_shared(), expected_twin(), expected_twin()))

        shared = core.state("core_test_shared")
        c.equal("containers are rollback-safe",
            type_names(gs.shared, gs.shared["flags"], gs.twins["ayumu"].sys, shared, shared["names"], shared["seen"], shared["nested"]["a"]),
            ("RevertableDict", "RevertableDict", "RevertableDict", "RevertableDict", "RevertableList", "RevertableSet", "RevertableDict"))

        # Reading never writes.
        before = snapshot(gs)
        for twin in (None, ) + core.TWINS:
            for key in ALPHA.template:
                core.flag("core_test", "alpha", key, twin)
            core.flag("core_test_place", LIVING, "visited", twin)
            core.state("core_test_shared", twin)
            core.state("core_test_twin", twin)
        c.check("reading unset flags and sections adds nothing to gs", snapshot(gs) == before)

        # Shared flags.
        c.equal("unset flags read the template",
            tuple(core.flag("core_test", "alpha", k) for k in ("seen", "count", "ratio", "label", "pair")),
            (False, 0, 0.5, "Template Value", (1, ("a", None))))

        core.set_flag("core_test", "alpha", "count", 3)
        c.equal("shared flag: same for both twins",
            (core.flag("core_test", "alpha", "count", "ayumu"), core.flag("core_test", "alpha", "count", "nemu")), (3, 3))
        c.equal("shared flag: stored sparse in gs.shared", gs.shared["flags"].get("core_test"), { "alpha": { "count": 3 } })
        c.check("shared flag: not in the twins' flags", not any("core_test" in t.flags for t in gs.twins.values()))

        core.set_flag("core_test", "alpha", "count", 0)
        c.check("setting the default removes the flag and empty dicts", "core_test" not in gs.shared["flags"], gs.shared["flags"])

        core.set_flag("core_test", "alpha", "seen", 0)
        c.equal("a value of another type than the default is kept",
            (gs.shared["flags"].get("core_test"), type(core.flag("core_test", "alpha", "seen")).__name__),
            ({ "alpha": { "seen": 0 } }, "int"))
        core.set_flag("core_test", "alpha", "seen", False)

        core.set_flag("core_test", "alpha", "pair", (2, ("b", None)))
        core.set_flag("core_test", "alpha", "label", "Saved")
        core.set_flag("core_test", "alpha", "count", 7)
        core.set_flag("core_test", "alpha", "count", 7)
        c.equal("several flags", gs.shared["flags"].get("core_test"), SAVED_FLAGS)

        # Per-twin flags.
        me = gs.twin
        other = [ t for t in core.TWINS if t != me ][0]

        core.set_flag("core_test_place", LIVING, "visited", True)
        c.equal("per-twin flag: set for the current twin only",
            (core.flag("core_test_place", LIVING, "visited", me), core.flag("core_test_place", LIVING, "visited", other)), (True, False))
        c.check("per-twin flag: stored in that twin's TwinState",
            gs.twins[me].flags.get("core_test_place") == { LIVING: { "visited": True } }
            and "core_test_place" not in gs.twins[other].flags
            and "core_test_place" not in gs.shared["flags"])

        core.set_flag("core_test_place", LIVING, "visited", False)
        core.set_flag("core_test_place", LIVING, "visited", True, "nemu")
        c.equal("per-twin flag: set for a given twin",
            (core.flag("core_test_place", LIVING, "visited", "ayumu"), core.flag("core_test_place", LIVING, "visited", "nemu")), (False, True))

        # Errors.
        c.raises("unknown flag key", LookupError, core.flag, "core_test", "alpha", "cuont")
        c.raises("set: unknown flag key", LookupError, core.set_flag, "core_test", "alpha", "cuont", 1)
        c.raises("unknown id", LookupError, core.flag, "core_test", "delta", "count")
        c.raises("unknown kind", LookupError, core.flag, "core_tset", "alpha", "count")
        c.raises("unknown twin", ValueError, core.flag, "core_test_place", LIVING, "visited", "eve")
        c.raises("unknown twin, shared kind", ValueError, core.flag, "core_test", "alpha", "count", "eve")
        c.raises("set: a list", ValueError, core.set_flag, "core_test", "alpha", "count", [ 1 ])
        c.raises("set: a definition", ValueError, core.set_flag, "core_test", "alpha", "count", ALPHA)
        c.equal("failed sets change nothing", gs.shared["flags"].get("core_test"), SAVED_FLAGS)

        # Sections.
        c.equal("shared section starts as its initial value", shared, expected_shared())
        c.check("shared section: same for both twins",
            core.state("core_test_shared", "ayumu") is shared and core.state("core_test_shared", "nemu") is shared)

        shared["count"] += 1
        shared["names"].append("saved")
        shared["seen"].add("saved")
        shared["nested"]["a"]["b"] = 2
        c.equal("changing a section leaves its initial value alone", core.SYSTEMS["core_test_shared"].initial, expected_shared())

        ayumu = core.state("core_test_twin", "ayumu")
        nemu = core.state("core_test_twin", "nemu")
        c.check("per-twin sections are separate", ayumu is not nemu)
        c.check("current twin's section by default", core.state("core_test_twin") is gs.twins[gs.twin].sys["core_test_twin"])

        ayumu["location"] = "kitchen"
        ayumu["visits"] = 2
        c.equal("other twin's section unchanged", nemu, expected_twin())

        c.raises("unknown system", LookupError, core.state, "core_test_nope")
        c.raises("unknown twin", ValueError, core.state, "core_test_twin", "eve")
        c.raises("register_state after init", core.FrozenError, core.register_state, "core_test_late", { }, False)

        # Pickling, and repairing a save made before a section existed.
        loaded = pickle.loads(pickle.dumps(gs, 2))
        c.check("pickle round trip keeps everything", snapshot(loaded) == snapshot(gs))
        c.check("pickle round trip keeps the classes", type(loaded) is core.GameState and type(loaded.twins["nemu"]) is core.TwinState)

        del loaded.shared["sys"]["core_test_shared"]
        del loaded.twins["nemu"].sys["core_test_twin"]
        del loaded.twins["ayumu"].sys["core_test_twin"]["visits"]

        c.check("ensure_sections reports a change", core.ensure_sections(loaded))
        c.equal("missing shared section made again", loaded.shared["sys"]["core_test_shared"], expected_shared())
        c.equal("missing twin section made again", loaded.twins["nemu"].sys["core_test_twin"], expected_twin())
        c.equal("missing key filled, other keys kept", loaded.twins["ayumu"].sys["core_test_twin"], { "location": "kitchen", "visits": 0 })
        c.check("ensure_sections again changes nothing", not core.ensure_sections(loaded))

        # Set up part 2.
        if EXTRA_REGISTERED:
            store.persistent.core_test_extra_section = False
            c.check("part 2 setup", False, "left over from an earlier run: quit Ren'Py, start it again, and run part 1 again")
        else:
            store.persistent.core_test_extra_section = True
            c.check("part 2 setup", True, "a new section will be registered after the restart")

        return c

    def state_loaded_checks():
        c = Checks("core: state, part 2 (after load)")
        gs = store.gs

        c.check("gs is a GameState with TwinStates",
            type(gs) is core.GameState and builtins.all(type(t) is core.TwinState for t in gs.twins.values()))

        c.equal("shared flags kept", gs.shared["flags"].get("core_test"), SAVED_FLAGS)
        c.equal("shared flags read back",
            tuple(core.flag("core_test", "alpha", k) for k in ("seen", "count", "label", "pair")),
            (False, 7, "Saved", (2, ("b", None))))
        c.equal("per-twin flags kept",
            (core.flag("core_test_place", LIVING, "visited", "ayumu"), core.flag("core_test_place", LIVING, "visited", "nemu")), (False, True))

        c.equal("shared section kept", core.state("core_test_shared"), SAVED_SHARED)
        c.equal("twin sections kept",
            (core.state("core_test_twin", "ayumu"), core.state("core_test_twin", "nemu")), (SAVED_AYUMU, expected_twin()))

        c.check("a section was added in code after the save", EXTRA_REGISTERED, "quit Ren'Py and start it again before loading")
        if EXTRA_REGISTERED:
            c.equal("the new section was added to both twins on load",
                (core.state("core_test_extra", "ayumu"), core.state("core_test_extra", "nemu")), ({ "ready": True }, { "ready": True }))

        shared = core.state("core_test_shared")
        c.equal("loaded containers are rollback-safe",
            type_names(gs.shared, gs.twins["nemu"].flags, shared, shared["names"], shared["seen"]),
            ("RevertableDict", "RevertableDict", "RevertableDict", "RevertableList", "RevertableSet"))

        store.persistent.core_test_extra_section = False

        return c


label test_core_state:
    $ core_test_result = core_test.state_checks().report()
    call screen core_test_report(core_test_result)
    "Part 2: save in any slot, quit Ren'Py, start it again and load that save. Then press Shift+O and type: jump test_core_state_loaded"
    return

label test_core_state_loaded:
    $ core_test_result = core_test.state_loaded_checks().report()
    call screen core_test_report(core_test_result)
    return
