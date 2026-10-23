## Toasts: short messages that stack in a corner and fade after a few seconds.
##
## uix.notify(text) adds one. renpy.notify (quick save, screenshots...) goes
## through it too. The queue lives in the uix_toasts screen, not in saved state.

init offset = -400

init python in uix:

    import store
    import time

    ## Seconds a toast stays, and how many show at once (oldest drop first).
    TOAST_TIME = 3.5
    TOAST_MAX = 4

    def toast_entries():
        """
        The toasts still showing, as a list of (start_time, text).
        """

        s = renpy.get_screen("uix_toasts")

        if s is None:
            return [ ]

        now = time.time()
        return [ e for e in s.scope.get("entries", ()) if now - e[0] < TOAST_TIME ]

    def notify(text):
        """
        Shows `text` as a toast. Safe to call from labels and from actions.
        """

        entries = toast_entries()
        entries.append((time.time(), text))
        entries = entries[-TOAST_MAX:]

        renpy.show_screen("uix_toasts", entries=entries)

        ## Self-voicing reads the newest toast.
        import renpy.display.tts as tts
        import renpy.text.extras as extras
        tts.notify_text = extras.filter_alt_text(text)

        renpy.restart_interaction()

    def toast_tick():
        """
        Drops expired toasts; hides the screen when none are left.
        """

        s = renpy.get_screen("uix_toasts")

        if s is None:
            return

        entries = toast_entries()

        if not entries:
            renpy.hide_screen("uix_toasts")
        elif len(entries) != len(s.scope.get("entries", ())):
            renpy.show_screen("uix_toasts", entries=entries)

        renpy.restart_interaction()

    store.config.notify = notify
