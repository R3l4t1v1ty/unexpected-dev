# Helpers: a screen action that changes the game state, and the names of
# content labels and asset files.

init offset = -500

init python in core:
    _constant = True

    import builtins
    import re

    import store

    class StateAction(store.Action, store.DictEquality):
        """
        A screen action that calls fn(*args, **kwargs) to change the game
        state. Screens change state only through this (or by returning a
        value): the change is kept if the player saves while the screen is
        up and later loads that save (renpy.retain_after_load), and screens
        update. fn's return value is ignored, so the screen stays up.
        """

        def __init__(self, fn, *args, **kwargs):
            self.fn = fn
            self.args = args
            self.kwargs = kwargs

        def __call__(self):
            self.fn(*self.args, **self.kwargs)
            renpy.retain_after_load()
            renpy.restart_interaction()

    def check_any_id(kind, id):
        """
        Checks a kind and id used in a name. For a registered kind, the id
        must fit the kind; any other snake_case kind takes ids with any
        number of dot-separated parts (e.g. adventure entities from map
        files). The definition doesn't have to exist.
        """
        if kind in KINDS:
            check_id(kind, id)
            return
        if not isinstance(kind, str) or not SEGMENT_RE.fullmatch(kind):
            raise ValueError("core: %r is not a valid kind name; use ASCII snake_case." % (kind,))
        if not isinstance(id, str) or not ANY_ID_RE.fullmatch(id):
            raise ValueError("core: %r is not a valid %s id: snake_case parts joined by dots." % (id, kind))

    def label_for(kind, id, verb=None):
        """
        The name of the content label of (kind, id), with a verb if given.
        Dots in the id become "__", and the parts are joined with "__":

            label_for("npc", "hana", "chat") -> "npc__hana__chat"
            label_for("event", "hana_1") -> "event__hana_1"
            label_for("location", "town.home.living_room") -> "location__town__home__living_room"

        Ids and verbs never contain "__", so each name has one meaning.
        """
        check_any_id(kind, id)

        parts = [ kind ] + id.split(".")

        if verb is not None:
            if not isinstance(verb, str) or not SEGMENT_RE.fullmatch(verb):
                raise ValueError("core: %r is not a valid verb; use ASCII snake_case like 'chat'." % (verb,))
            parts.append(verb)

        return "__".join(parts)

    # A part of an asset's file name: lowercase ASCII words joined by single
    # underscores. Only the last part may have an extension.
    ASSET_PART_RE = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
    ASSET_LAST_PART_RE = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*(?:\.[a-z0-9]+)?")

    def asset(kind, id, *parts):
        """
        The path, relative to game/, of an asset of (kind, id). The folder
        comes from the asset dir and the id. The file name starts with the
        definition's label name, so no two files in images/ share a name:

            images/<asset dir>/<id, dots as slashes>/<label_for(kind, id)>__<parts joined by __>

        The asset dir is set with register_kind(asset_dir=...); it's the
        kind by default, or the kind of an unregistered kind. For example,
        with locations registered with asset_dir="world":

            asset("location", "town.home.living_room", "bg_0.webp")
                -> "images/world/town/home/living_room/location__town__home__living_room__bg_0.webp"

        With no parts, it's the folder. The file doesn't have to exist (check
        with renpy.loadable).
        """
        check_any_id(kind, id)

        info = KINDS.get(kind)
        asset_dir = info.asset_dir if info is not None else kind
        folder = "/".join([ "images", asset_dir ] + id.split("."))

        if not parts:
            return folder

        for i, p in enumerate(parts):
            pattern = ASSET_LAST_PART_RE if i == len(parts) - 1 else ASSET_PART_RE
            if not isinstance(p, str) or not pattern.fullmatch(p):
                raise ValueError("core: asset(%r, %r): %r is not a valid file name part. Use lowercase ASCII words joined by single underscores, like 'bg_0'; only the last part has an extension, like 'bg_0.webp'." % (kind, id, p))

        return folder + "/" + "__".join([ label_for(kind, id) ] + builtins.list(parts))
