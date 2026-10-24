## Profiler helpers, in the debug overlay's Profile tab (overlay_scr.rpy).
##
## Screen times: renpy.profile_screen logs how long a screen took each time
## it's shown or updated, to profile_screen.txt next to log.txt. "Detail" also
## logs how each screen statement was evaluated (constant, reused or new).
## config.profile_screens logs only that detail, without the screen's name or
## its time, so it isn't used.
##
## Slow frames: config.profile logs a breakdown of every frame slower than
## config.profile_time to log.txt.
##
## The settings are in persistent (dev_timed_screens, dev_profile_detail,
## dev_profile_frames), so they survive Shift+R, and are applied at init.
## Developer mode only.

init offset = -300

init python in dev:
    _constant = True

    import builtins

    import store
    from store import renpy

    ## Screen name -> the object renpy.profile_screen made for it. A screen
    ## keeps the object it was shown with, so the objects are changed in place,
    ## never replaced. Session data, never saved.
    PROFILES = builtins.dict()

    def timed_screens():
        """The names of the screens being timed, as a set."""

        return builtins.set(store.persistent.dev_timed_screens or ())

    def apply_profiling():
        """Sets Ren'Py's screen profiling to match persistent."""

        timed = timed_screens()
        detail = bool(store.persistent.dev_profile_detail)

        for name in timed | builtins.set(PROFILES):
            p = PROFILES.get(name)

            if p is None:
                p = PROFILES[name] = renpy.profile_screen(name)

            timing = name in timed

            p.show = timing
            p.update = timing
            p.time = timing
            p.debug = timing and detail

    def time_screen(name, value):
        """Starts (value True) or stops timing the screen `name`."""

        timed = timed_screens()

        if value:
            if not renpy.has_screen(name):
                notify("No screen named %s" % name)
                return

            timed.add(name)
        else:
            timed.discard(name)

        store.persistent.dev_timed_screens = builtins.tuple(sorted(timed))
        apply_profiling()
        renpy.restart_interaction()

    def set_profile_detail(value):
        store.persistent.dev_profile_detail = bool(value)
        apply_profiling()
        renpy.restart_interaction()

    def set_frame_profiling(value):
        store.persistent.dev_profile_frames = bool(value)
        store.config.profile = bool(value)

        ## F8 (Ren'Py's "profile one frame") raises the threshold to 10 s.
        store.config.profile_time = FRAME_TIME

        renpy.restart_interaction()

    def screen_choices():
        """
        The screens shown now (but Ren'Py's own, named _...) plus the ones being
        timed, sorted. Cheap enough for a screen.
        """

        names = timed_screens()

        for layer in store.config.layers:
            for tag in renpy.get_showing_tags(layer, sort=True):
                if not tag.startswith("_") and renpy.has_screen(tag):
                    names.add(tag)

        return sorted(names)


init offset = 100

init python in dev:

    ## The slow-frame threshold, as options.rpy left it (Ren'Py's default is 20 ms).
    FRAME_TIME = store.config.profile_time

    if on():
        apply_profiling()

        if store.persistent.dev_profile_frames:
            store.config.profile = True
