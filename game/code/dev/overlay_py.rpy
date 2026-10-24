## Debug overlay (F9): twin, day and slot, the flag inspector, the gs section
## inspector and the profiler (profiler_py.rpy). Every state edit goes through
## core.StateAction, so it survives save and load. Developer mode only.

init offset = -300

init python in dev:
    _constant = True

    import ast
    import builtins

    import store
    from store import core, uix, renpy

    ## Ids per page in the flag inspector.
    PAGE = 24

    ## Text colors of a flag that differs from its default, and of one that doesn't.
    CHANGED = "#ffd166"
    SAME = "#e6e6e6"

    def toggle_overlay():
        if on():
            store.persistent.dev_overlay_open = not store.persistent.dev_overlay_open
            renpy.restart_interaction()

    def close_overlay():
        store.persistent.dev_overlay_open = False
        renpy.restart_interaction()

    def overlay_width():
        share = 0.9 if renpy.variant("small") else 0.4
        return int(store.config.screen_width * share)

    def overlay_height():
        return int(store.config.screen_height * 0.85)

    def status():
        """The header line: twin, day, slot."""

        try:
            return plain("%s, day %d, %s" % (core.twin_name(), core.day(), core.slot_name(core.slot())))
        except Exception:
            return "no game state"

    def twin_or_me(twin):
        return twin or core.me()

    ## Time ####################################################################

    def slots_until(slot):
        """Slots to advance to reach the next `slot` (a whole day for the current one)."""

        n = (slot - core.slot()) % len(core.SLOTS)
        return n or len(core.SLOTS)

    def go_to_day(text):
        """Advances to the morning of day `text`. Time only goes forward."""

        try:
            target = int(text.strip())
        except ValueError:
            notify("Not a day number: %s" % text)
            return

        slots = (target - core.day()) * len(core.SLOTS) - core.slot()

        if slots <= 0:
            notify("Time only goes forward: pick a later day.")
            return

        core.advance(slots)

    ## Flags ###################################################################

    def ids_of(kind):
        """Sorted ids of a kind's definitions. Not for screens."""

        return builtins.tuple(sorted(getattr(d, "id", d) for d in core.all(kind)))

    def template_items(kind, def_id):
        """((key, default), ...) of a definition's flags, sorted by key."""

        try:
            template = core.get(kind, def_id).template
        except Exception:
            return ()

        return builtins.tuple(sorted(template.items()))

    def control(val, dflt):
        """Which buttons a flag gets: "toggle", "number" or "text"."""

        if isinstance(val, bool) or (val is None and isinstance(dflt, bool)):
            return "toggle"

        if isinstance(val, (int, float)):
            return "number"

        return "text"

    def edit_text(val, dflt):
        """The text an Edit box starts with: strings as they are, the rest as literals."""

        if isinstance(dflt, str):
            return val if isinstance(val, str) else ""

        return literal(val)

    def parse_flag(text, dflt):
        """
        The value typed for a flag. A string flag takes the text as it is;
        any other is a Python literal of the default's type, or None.
        """

        if isinstance(dflt, str):
            return text

        try:
            val = ast.literal_eval(text.strip())
        except Exception:
            raise ValueError("Not a Python literal: %s" % text)

        if val is None or dflt is None:
            return val

        if isinstance(dflt, bool):
            ok = isinstance(val, bool)
        elif isinstance(dflt, int):
            ok = isinstance(val, int) and not isinstance(val, bool)
        elif isinstance(dflt, float):
            ok = isinstance(val, (int, float)) and not isinstance(val, bool)
            if ok:
                val = float(val)
        else:
            ok = isinstance(val, builtins.tuple)

        if not ok:
            raise ValueError("Needs the default's type (%s): %s" % (builtins.type(dflt).__name__, text))

        return val

    def set_flag_text(kind, def_id, key, text, twin):
        """Sets a flag from typed text. Run through core.StateAction."""

        dflt = core.get(kind, def_id).template[key]

        try:
            core.set_flag(kind, def_id, key, parse_flag(text, dflt), twin=twin)
        except (ValueError, TypeError) as e:
            notify(e)

    ## Sections ################################################################

    def section_items(system, twin):
        """((key, value), ...) of a gs section's top-level keys."""

        section = core.state(system, twin)
        return builtins.tuple((k, section[k]) for k in sorted(section, key=builtins.str))

    def set_section_text(system, key, text, twin):
        """Sets a section's top-level key from a typed literal. Run through core.StateAction."""

        try:
            val = core.copy_plain(ast.literal_eval(text.strip()))
        except Exception as e:
            notify("Not plain data: %s" % (e,))
            return

        core.state(system, twin)[key] = val
