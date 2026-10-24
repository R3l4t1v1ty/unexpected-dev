## A test run. dev.run_test() restarts Ren'Py into this label, so the test
## starts from a new game and nothing from the game you were in carries over.
## A test's `return` value, if it's a string, is shown as its note.

label dev_run_test:

    $ dev_test_label = dev.take_pending()

    if dev_test_label is None:
        $ renpy.full_restart()

    $ core.new_game()

    call expression dev_test_label

    $ dev.mark_done(dev_test_label, _return)

    call screen dev_test_done(dev_test_label)

    $ renpy.full_restart()
