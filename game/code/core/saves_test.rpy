# Tests for saves_py.rpy: migrations, renames, loading, save JSON, and the
# plain-data check. Developer only; excluded from builds.
# Runs on a new-game gs, so the game you're in isn't changed.
#
# Run: start a game, press Shift+O, type: jump test_core_saves

init offset = 0

init python in core_test:
    _constant = True

    import builtins

    from store import core

    core.RENAMES["core_test_place"] = { "town.home.old_living_room": "town.home.living_room" }

    core.register_state("core_test_ids",
        { "here": "town.home.hall", "seen": [ ], "by_id": { }, "pair": () },
        True,
        ids={ "here": "core_test_place", "seen": "core_test_place", "by_id": "core_test", "pair": "core_test" })

    def core_test_save_info():
        return { "core_test_info": "info for " + core.me() }

    core.register_save_info(core_test_save_info)

    def on_game_loaded():
        record("game_loaded")

    def saves_init_checks():
        c = Checks("init")

        c.raises("migration(1)", ValueError, core.migration, 1)
        c.raises("migration('2')", ValueError, core.migration, "2")
        c.raises("migration(True)", ValueError, core.migration, True)

        table = { }
        core.add_migration(table, 2, len)
        c.raises("two migrations with one number", ValueError, core.add_migration, table, 2, abs)
        c.raises("a migration that can't be called", TypeError, core.add_migration, table, 3, 5)

        c.raises("register_state: an ids key not in initial", ValueError, core.register_state, "core_test_bad", { "a": 1 }, False, ids={ "b": "core_test" })
        c.raises("register_state: ids not a dict", TypeError, core.register_state, "core_test_bad", { "a": 1 }, False, ids=[ "a" ])
        c.raises("register_save_info: not callable", TypeError, core.register_save_info, 5)

        return c

    SAVES_INIT = saves_init_checks()

    def expected_ids():
        return { "here": "town.home.hall", "seen": [ ], "by_id": { }, "pair": () }

    def saves_checks():
        c = Checks("core: saves")
        c.extend(SAVES_INIT)
        living = "town.home.living_room"

        c.equal("SAVE_VERSION is the highest migration (1 with none)", core.SAVE_VERSION, builtins.max(core.MIGRATIONS, default=1))
        c.equal("no problems in the real RENAMES and section ids", core.rename_problems(core.RENAMES) + core.section_id_problems(), [ ])

        problems = core.rename_problems({ "core_test": { "beta": "alpha", "gone": "nope" }, "core_tset": { "a": "b" } })
        c.check("rename problems are found",
            len(problems) == 3 and "'beta' still exists" in problems[0] and "'nope' doesn't exist" in problems[1] and "unknown kind" in problems[2],
            problems)

        with fresh_gs() as gs:
            c.equal("a new game has the current version", gs.version, core.SAVE_VERSION)

            # An old save: version 1, made before migrations 2, 3 and 5, with
            # old ids, and without two sections.
            old = core.GameState()
            old.version = 1

            for t in old.twins.values():
                section = t.sys["core_test_twin"]
                section["where"] = section.pop("location")

            del old.shared["sys"]["core_test_shared"]
            del old.twins["nemu"].sys["core_test_ids"]

            old.shared["flags"]["core_test"] = { "old_alpha": { "count": 5, "label": "Old" }, "alpha": { "label": "New" } }
            old.twins["nemu"].flags["core_test_place"] = { "town.home.old_living_room": { "visited": True } }
            old.twins["ayumu"].sys["core_test_ids"] = {
                "here": "town.home.old_living_room",
                "seen": [ "town.home.old_living_room", "town.home.hall" ],
                "by_id": { "old_alpha": 1, "beta": 2 },
                "pair": ("old_alpha", "beta"),
                }

            ran = [ ]

            def m2(gs):
                ran.append(2)
                for t in gs.twins.values():
                    section = t.sys["core_test_twin"]
                    section["location"] = section.pop("where")

            def m3(gs):
                ran.append(3)

            def m5(gs):
                ran.append(5)

            migrations = { 5: m5, 2: m2, 3: m3 }

            c.check("updating an old save changes it", core.update_state(old, migrations, 5))
            c.equal("migrations run oldest first", ran, [ 2, 3, 5 ])
            c.equal("the save's version goes up", old.version, 5)
            c.equal("a migration's change", [ t.sys["core_test_twin"] for t in old.twins.values() ], [ { "location": "start", "visits": 0 } ] * 2)
            c.equal("flags under an old id move to the new id; the new id's values win",
                old.shared["flags"]["core_test"], { "alpha": { "label": "New", "count": 5 } })
            c.equal("per-twin flags under an old id move too", old.twins["nemu"].flags["core_test_place"], { living: { "visited": True } })
            c.equal("ids in sections are renamed (one id, list, dict keys, tuple)", old.twins["ayumu"].sys["core_test_ids"], {
                "here": living,
                "seen": [ living, "town.home.hall" ],
                "by_id": { "alpha": 1, "beta": 2 },
                "pair": ("alpha", "beta"),
                })
            c.equal("missing sections are added",
                (old.shared["sys"]["core_test_shared"], old.twins["nemu"].sys["core_test_ids"]), (expected_shared(), expected_ids()))

            del ran[:]
            c.check("updating again changes nothing", not core.update_state(old, migrations, 5))
            c.equal("...and runs no migration", ran, [ ])

            mid = core.GameState()
            mid.version = 3
            core.update_state(mid, migrations, 5)
            c.equal("a version 3 save runs only the newer migrations", ran, [ 5 ])

            newer = core.GameState()
            newer.version = 9
            c.check("a save from a newer game isn't migrated", not core.run_migrations(newer, migrations, 5) and newer.version == 9)

            # Loading.
            start_recording()
            core.after_load()
            c.equal("after_load emits game_loaded", stop_recording(), [ ("game_loaded",) ])

            # Save JSON.
            d = { }
            core.save_json(d)
            c.equal("save JSON", d, { "version": core.SAVE_VERSION, "twin": "ayumu", "day": 1, "slot": 0, "core_test_info": "info for ayumu" })

            core.swap()
            core.advance(2)
            d = { }
            core.save_json(d)
            c.equal("save JSON follows the twin being played", (d["twin"], d["day"], d["slot"], d["core_test_info"]), ("nemu", 1, 2, "info for nemu"))
            core.swap()

            c.raises("save info: a field that's taken", ValueError, core.add_save_info, { "day": 1 }, [ lambda: { "day": 2 } ], True)
            c.raises("save info: not JSON", TypeError, core.add_save_info, { }, [ lambda: { "x": set() } ], True)
            c.raises("save info: bad key", ValueError, core.add_save_info, { }, [ lambda: { "Bad Key": 1 } ], True)
            c.raises("save info: not a dict", TypeError, core.add_save_info, { }, [ lambda: [ 1 ] ], True)

            d = { }
            c.no_raise("release: a failing save info function is logged", core.add_save_info, d, [ lambda: 1 // 0, lambda: { "x": 1 } ], False)
            c.equal("release: the others still add their fields", d, { "x": 1 })

            # Only plain data in gs.
            c.no_raise("a new game's gs is plain data", core.check_saveable, gs)

            section = core.state("core_test_shared")
            for name, value, where in (
                    ("a definition", ALPHA, "gs.shared['sys']['core_test_shared']['bad'] (Thing)"),
                    ("a function", len, "['bad'] (builtin_function_or_method)"),
                    ("a plain Python dict", builtins.dict(), "isn't rollback-safe"),
                    ("a plain Python list", builtins.list(), "isn't rollback-safe"),
                    ):
                section["bad"] = value
                try:
                    core.check_saveable(gs)
                    c.check("%s in gs is caught" % name, False, "did not raise")
                except TypeError as e:
                    c.check("%s in gs is caught" % name, where in str(e), e)
                del section["bad"]

            gs.twins["nemu"].extra = ALPHA
            c.raises("a definition on a TwinState is caught", TypeError, core.check_saveable, gs)
            del gs.twins["nemu"].extra

        return c


init offset = 100

init python in core_test:
    core.connect("game_loaded", on_game_loaded)


label test_core_saves:
    $ core_test_result = core_test.saves_checks().report()
    call screen core_test_report(core_test_result)
    return
