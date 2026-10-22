# New Game starts here (Ren'Py jumps to label start).
#
# gs was just made by its default statement. new_game() makes sure every
# section exists and emits game_started, so each system can set up its part
# of the new game. Then world/ takes over, once it exists.

label start:
    $ core.new_game()

    if renpy.has_label("world_loop"):
        jump world_loop

    # Until world/ has a world_loop.
    "The world isn't built yet."
    return
