# Tests for the lookups dev/'s inspector uses: core.kinds(), core.per_twin(),
# core.systems(), core.system_per_twin(). Developer only; excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_lookups

init offset = 0

init python in core_test:
    _constant = True

    import builtins

    from store import core

    def lookups_checks():
        c = Checks("core: lookups")

        kinds = core.kinds()
        c.check("kinds() is a sorted tuple", type(kinds) is tuple and builtins.list(kinds) == builtins.sorted(kinds), kinds)
        c.check("kinds() has the test kinds", "core_test" in kinds and "core_test_place" in kinds, kinds)
        c.equal("per_twin", (core.per_twin("core_test"), core.per_twin("core_test_place")), (False, True))
        c.raises("per_twin: unknown kind", LookupError, core.per_twin, "core_tset")

        systems = core.systems()
        c.check("systems() is a sorted tuple", type(systems) is tuple and builtins.list(systems) == builtins.sorted(systems), systems)
        c.check("systems() has the test sections", "core_test_shared" in systems and "core_test_twin" in systems, systems)
        c.equal("system_per_twin", (core.system_per_twin("core_test_shared"), core.system_per_twin("core_test_twin")), (False, True))
        c.raises("system_per_twin: unknown system", LookupError, core.system_per_twin, "core_test_nope")

        c.check("the same answer every call", core.kinds() == kinds and core.systems() == systems)

        return c


label test_core_lookups:
    $ core_test_result = core_test.lookups_checks().report()
    call screen core_test_report(core_test_result)
    return
