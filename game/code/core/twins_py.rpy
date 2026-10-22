# Twins: who is being played, and swapping.
#
# The twins are core.TWINS (in state_py.rpy). Never branch on their names:
# per-twin differences are data keyed by twin.

init offset = -500

init python in core:
    _constant = True

    import store
    from store import _

    # What players see as each twin's name.
    TWIN_NAMES = { "ayumu": _("Ayumu"), "nemu": _("Nemu") }

    def twin_name(twin=None):
        """
        The name of `twin` (default: the twin being played), translated.
        """
        return renpy.translate_string(TWIN_NAMES[resolve_twin(twin)])

    def me():
        """
        The twin being played.
        """
        return store.gs.twin

    def other(twin=None):
        """
        The twin who isn't `twin` (default: who isn't being played).
        """
        twin = resolve_twin(twin)
        return TWINS[(TWINS.index(twin) + 1) % len(TWINS)]

    def swap(twin=None):
        """
        Switches play to `twin` (default: the other twin) and emits
        twin_swapped(twin). Does nothing if `twin` is already being played.
        Scene changes are up to world (label world_swap).
        """
        if twin is None:
            twin = other()
        else:
            twin = resolve_twin(twin)

        gs = store.gs
        if gs.twin == twin:
            return

        gs.twin = twin
        emit("twin_swapped", twin=twin)
