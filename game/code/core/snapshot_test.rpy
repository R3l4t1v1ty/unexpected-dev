# Tests for core.snapshot() and core.migrate() (saves_py.rpy). Developer only;
# excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_snapshot

init offset = 0

init python in core_test:
    _constant = True

    import builtins
    import copy

    import store
    from store import core

    def initial_sections(per_twin):
        """
        Every registered section of one sort (per-twin or shared), as at a
        new game.
        """
        rv = { }
        for s in core.systems():
            if core.system_per_twin(s) == per_twin:
                rv[s] = core.copy_plain(core.SYSTEMS[s].initial)
        return rv

    def minimal_data():
        """
        The smallest valid snapshot-shaped data: version 1, nothing in it.
        """
        twins = { }
        for t in core.TWINS:
            twins[t] = { "day": 1, "slot": 0, "flags": { }, "sys": { } }
        return { "version": 1, "twin": core.TWINS[0], "shared": { "flags": { }, "sys": { } }, "twins": twins }

    def broken(fn):
        d = minimal_data()
        fn(d)
        return d

    def set_in(d, path, value):
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] = value

    def del_in(d, path):
        for k in path[:-1]:
            d = d[k]
        del d[path[-1]]

    def no_migration(gs):
        return

    def snapshot_checks():
        c = Checks("core: snapshot and migrate")
        living = "town.home.living_room"

        # Snapshot of a new game.
        with fresh_gs() as gs:
            snap = core.snapshot()

            c.equal("snapshot shape",
                (builtins.sorted(snap), builtins.sorted(snap["shared"]), builtins.list(snap["twins"]),
                    [ builtins.sorted(snap["twins"][t]) for t in core.TWINS ]),
                ([ "shared", "twin", "twins", "version" ], [ "flags", "sys" ], builtins.list(core.TWINS),
                    [ [ "day", "flags", "slot", "sys" ] ] * 2))
            c.equal("snapshot of a new game",
                snap,
                {
                    "version": core.SAVE_VERSION,
                    "twin": "ayumu",
                    "shared": { "flags": { }, "sys": initial_sections(False) },
                    "twins": {
                        "ayumu": { "day": 1, "slot": 0, "flags": { }, "sys": initial_sections(True) },
                        "nemu": { "day": 1, "slot": 0, "flags": { }, "sys": initial_sections(True) },
                        },
                    })
            c.check("snapshot is plain, rollback-safe data", core.find_unplain(snap, "snap", strict=True) is None,
                core.find_unplain(snap, "snap", strict=True))

            snap["shared"]["sys"]["core_test_shared"]["names"].append("changed")
            snap["twins"]["ayumu"]["sys"]["core_test_twin"]["visits"] = 9
            snap["twins"]["ayumu"]["day"] = 9
            c.equal("changing a snapshot leaves gs alone",
                (core.state("core_test_shared")["names"], core.state("core_test_twin", "ayumu")["visits"], core.day("ayumu")), ([ ], 0, 1))

            c.equal("migrating an up-to-date snapshot changes nothing", core.migrate(core.snapshot()), core.snapshot())

        # A hand-made version 1 save: two test migrations and two renames.
        old = {
            "version": 1,
            "twin": "nemu",
            "shared": { "flags": { "core_test": { "old_alpha": { "count": 5 } } }, "sys": { } },
            "twins": {
                "ayumu": { "day": 3, "slot": 2, "flags": { }, "sys": { "core_test_twin": { "where": "kitchen", "visits": 1 } } },
                "nemu": { "day": 1, "slot": 0, "flags": { "core_test_place": { "town.home.old_living_room": { "visited": True } } }, "sys": { } },
                },
            }
        old_copy = copy.deepcopy(old)

        seen = [ ]

        def m2(gs):
            seen.append((core.me(), store.gs is gs, "core_test_twin" in gs.twins["nemu"].sys))
            for t in gs.twins.values():
                section = t.sys.get("core_test_twin")
                if section is not None and "where" in section:
                    section["location"] = section.pop("where")

        def m3(gs):
            gs.shared["flags"]["core_test"]["old_alpha"]["label"] = "m3"

        renames = {
            "core_test": { "old_alpha": "alpha" },
            "core_test_place": { "town.home.old_living_room": living },
            }

        live = store.gs
        live_before = core.snapshot()

        start_recording()
        result = core.migrate(old, { 3: m3, 2: m2 }, renames)
        signals = stop_recording()

        ayumu_sys = initial_sections(True)
        ayumu_sys["core_test_twin"] = { "location": "kitchen", "visits": 1 }

        c.equal("a version 1 dict through two migrations and renames", result, {
            "version": 3,
            "twin": "nemu",
            "shared": { "flags": { "core_test": { "alpha": { "count": 5, "label": "m3" } } }, "sys": initial_sections(False) },
            "twins": {
                "ayumu": { "day": 3, "slot": 2, "flags": { }, "sys": ayumu_sys },
                "nemu": { "day": 1, "slot": 0, "flags": { "core_test_place": { living: { "visited": True } } }, "sys": initial_sections(True) },
                },
            })
        c.equal("migrations see the data's gs, as during a load, with only the data's sections", seen, [ ("nemu", True, False) ])
        c.check("the live gs is the same object afterwards", store.gs is live)
        c.check("the live gs is unchanged", core.snapshot() == live_before)
        c.equal("the data passed in is unchanged", old, old_copy)
        c.equal("migrate emits nothing", signals, [ ])
        c.check("the result shares nothing with the data", result["twins"]["ayumu"]["sys"]["core_test_twin"] is not old["twins"]["ayumu"]["sys"]["core_test_twin"])

        # Data that isn't in the snapshot shape.
        for name, data in (
                ("not a dict", [ ]),
                ("a missing key", broken(lambda d: del_in(d, [ "twin" ]))),
                ("an unknown key", broken(lambda d: set_in(d, [ "extra" ], 1))),
                ("version 0", broken(lambda d: set_in(d, [ "version" ], 0))),
                ("version as text", broken(lambda d: set_in(d, [ "version" ], "1"))),
                ("an unknown twin", broken(lambda d: set_in(d, [ "twin" ], "eve"))),
                ("a twin missing", broken(lambda d: del_in(d, [ "twins", "nemu" ]))),
                ("slot 4", broken(lambda d: set_in(d, [ "twins", "ayumu", "slot" ], 4))),
                ("day 0", broken(lambda d: set_in(d, [ "twins", "ayumu", "day" ], 0))),
                ("flags not a dict", broken(lambda d: set_in(d, [ "shared", "flags" ], [ ]))),
                ("a definition in a section", broken(lambda d: set_in(d, [ "twins", "nemu", "sys" ], { "x": ALPHA }))),
                ):
            c.raises("migrate rejects %s" % (name,), ValueError, core.migrate, data, { })

        newer = minimal_data()
        newer["version"] = 5
        c.raises("migrate rejects data newer than the target", ValueError, core.migrate, newer, { 2: no_migration })
        c.raises("migrate rejects migration number 1", ValueError, core.migrate, minimal_data(), { 1: no_migration })
        c.raises("migrate rejects migrations that aren't a dict", TypeError, core.migrate, minimal_data(), [ no_migration ])
        c.raises("migrate rejects renames of the wrong shape", ValueError, core.migrate, minimal_data(), { }, { "core_test": "alpha" })

        return c


label test_core_snapshot:
    $ core_test_result = core_test.snapshot_checks().report()
    call screen core_test_report(core_test_result)
    return
