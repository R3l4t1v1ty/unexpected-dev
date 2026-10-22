# Tests for start.rpy and new_game(). Developer only; excluded from builds.
# Runs on a new-game gs, so the game you're in isn't changed.
#
# Run: start a game, press Shift+O, type: jump test_core_start
# Also check by hand: New Game on the main menu reaches the placeholder line
# "The world isn't built yet." (until world/ has a world_loop).

init offset = 0

init python in core_test:
    _constant = True

    from store import core

    def on_game_started():
        record("game_started")

    def start_checks():
        c = Checks("core: start")

        c.check("label start exists", renpy.has_label("start"))

        with fresh_gs() as gs:
            del gs.shared["sys"]["core_test_shared"]

            start_recording()
            core.new_game()
            c.equal("new_game emits game_started", stop_recording(), [ ("game_started",) ])
            c.equal("new_game makes sure every section exists", gs.shared["sys"].get("core_test_shared"), expected_shared())

        return c


init offset = 100

init python in core_test:
    core.connect("game_started", on_game_started)


label test_core_start:
    $ core_test_result = core_test.start_checks().report()
    call screen core_test_report(core_test_result)
    return
