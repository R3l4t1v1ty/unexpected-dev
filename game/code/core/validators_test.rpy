# Tests for validators_py.rpy. Developer only; excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_validators
#
# The test validators report problems only while this test runs, so dev/'s
# validator report stays clean.

init offset = 0

init python in core_test:
    _constant = True

    from store import core

    VALIDATORS_ON = False

    def validators_on(on):
        global VALIDATORS_ON
        VALIDATORS_ON = on

    def validate_two():
        if not VALIDATORS_ON:
            return [ ]
        return [ "first problem", "second problem" ]

    def validate_raises():
        if VALIDATORS_ON:
            raise RuntimeError("raised on purpose by the test")
        return [ ]

    def validate_not_a_list():
        if VALIDATORS_ON:
            return "not a list"
        return [ ]


init offset = 100

init python in core_test:
    core.register_validator("core_test_two", validate_two)
    core.register_validator("core_test_raises", validate_raises)
    core.register_validator("core_test_not_a_list", validate_not_a_list)

    def validators_init_checks():
        c = Checks("init")

        c.raises("register_validator: same name twice", ValueError, core.register_validator, "core_test_two", validate_two)
        c.raises("register_validator: bad name", ValueError, core.register_validator, "Core Test", validate_two)
        c.raises("register_validator: not callable", TypeError, core.register_validator, "core_test_bad", 5)
        c.check("register_validator: failed calls register nothing", "core_test_bad" not in core.VALIDATORS)

        return c

    VALIDATORS_INIT = validators_init_checks()

    def test_validator_lines():
        """
        The lines of run_validators() from the test validators, with them
        switched on.
        """
        validators_on(True)
        try:
            return [ r for r in core.run_validators() if r[0].startswith("core_test") ]
        finally:
            validators_on(False)

    def validators_checks():
        c = Checks("core: validators")
        c.extend(VALIDATORS_INIT)

        lines = test_validator_lines()
        two = [ r for r in lines if r[0] in ("core_test_two", "core_test_raises") ]

        c.equal("one validator returning two problems and one that raises give three lines", len(two), 3)
        c.equal("problems come back as (name, problem)",
            two[:2], [ ("core_test_two", "first problem"), ("core_test_two", "second problem") ])
        c.check("a validator that raises becomes a problem line saying what and where",
            len(two) == 3 and two[2][0] == "core_test_raises" and "RuntimeError" in two[2][1]
            and "raised on purpose" in two[2][1] and "validators_test.rpy" in two[2][1],
            two[2:])
        c.check("a validator that doesn't return a list becomes a problem line",
            [ r for r in lines if r[0] == "core_test_not_a_list" and "'not a list'" in r[1] ] != [ ],
            lines)
        c.equal("switched off, the test validators report nothing",
            [ r for r in core.run_validators() if r[0].startswith("core_test") ], [ ])

        c.raises("register_validator after init", core.FrozenError, core.register_validator, "core_test_late", validate_two)

        return c


label test_core_validators:
    $ core_test_result = core_test.validators_checks().report()
    call screen core_test_report(core_test_result)
    return
