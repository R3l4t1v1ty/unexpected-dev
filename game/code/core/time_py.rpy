# Time: each twin has their own clock, a day (from 1) and a slot of the day.
# No weeks. Everything that changes time acts on the twin being played and
# emits time_changed(twin, day, slot).

init offset = -500

init python in core:
    _constant = True

    import store
    from store import _

    SLOTS = (0, 1, 2, 3)
    MORNING, AFTERNOON, EVENING, NIGHT = SLOTS

    SLOT_NAMES = (_("Morning"), _("Afternoon"), _("Evening"), _("Night"))

    def day(twin=None):
        """
        The day of `twin` (default: the twin being played), from 1.
        """
        return twin_state(twin).day

    def slot(twin=None):
        """
        The slot of the day of `twin` (default: the twin being played).
        """
        return twin_state(twin).slot

    def advance(slots=1):
        """
        Moves the current twin's clock forward by `slots`, into the following
        days if needed.
        """
        if isinstance(slots, bool) or not isinstance(slots, int) or slots < 0:
            raise ValueError("core: advance() takes a whole number of slots from 0 up, not %r." % (slots,))
        if not slots:
            return

        ts = twin_state()
        total = ts.slot + slots
        ts.day += total // len(SLOTS)
        ts.slot = total % len(SLOTS)

        emit("time_changed", twin=store.gs.twin, day=ts.day, slot=ts.slot)

    def sleep():
        """
        Moves the current twin to the next day, in the morning.
        """
        ts = twin_state()
        ts.day += 1
        ts.slot = SLOTS[0]

        emit("time_changed", twin=store.gs.twin, day=ts.day, slot=ts.slot)

    def slot_name(slot):
        """
        The name of a slot, translated, like "Morning".
        """
        if isinstance(slot, bool) or not isinstance(slot, int) or slot not in SLOTS:
            raise ValueError("core: %r is not a slot. Slots are %s." % (slot, ", ".join(str(i) for i in SLOTS)))
        return renpy.translate_string(SLOT_NAMES[slot])
