# Definitions and the registry.
#
# A definition is a piece of content made at init: a location, an NPC, an
# event... It has a kind, an id unique within its kind, and a template: the
# default values of its flags. Definitions are never saved. Pickling one
# stores only (kind, id), and loading finds it again in the current code, so
# saves always see the latest content.
#
# Everything here is frozen at the very end of init (init 999). After that,
# making a definition or a kind raises, and changing a definition raises in
# developer mode.
#
# This file defines core.all(), which hides Python's all() in every core file
# (they all share the core store). Use builtins.all() inside core.

init offset = -500

init python in core:
    _constant = True

    import builtins
    import collections
    import difflib
    import re
    import types

    import store

    class FrozenError(TypeError):
        """
        Raised when code tries to change definitions or the registry after
        init.
        """

    # True once freeze() has run, at the end of init.
    frozen = False

    # One lowercase snake_case word: starts with a letter, single underscores.
    SEGMENT = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*"
    SEGMENT_RE = re.compile(SEGMENT)

    # An id with any number of parts, for kinds that aren't registered.
    ANY_ID_RE = re.compile(SEGMENT + r"(?:\." + SEGMENT + r")*")

    # A folder under images/, like "world" or "adventure/maps".
    ASSET_DIR_RE = re.compile(SEGMENT + r"(?:/" + SEGMENT + r")*")

    # Values allowed in templates, alone or in (nested) tuples.
    PLAIN_TYPES = (type(None), bool, int, float, str)

    KindInfo = collections.namedtuple("KindInfo", ("kind", "per_twin", "id_parts", "pattern", "asset_dir"))

    # kind -> KindInfo
    KINDS = { }
    # kind -> {id: definition}, in creation order
    REGISTRY = { }
    # (kind, id) -> "file:line" where the definition was made, for error messages
    SOURCES = { }
    # kind -> tuple of all its definitions, filled by freeze()
    ALL_TUPLES = { }
    # {kind: {old_id: new_id}}: ids renamed after a release. Map each old id
    # straight to the current id. Other folders fill it at init.
    RENAMES = { }

    def warn(message):
        """
        Logs a problem that shouldn't stop the game.
        """
        print("core: " + message)

    def did_you_mean(word, choices):
        """
        " Did you mean 'x'?" for the choices close to `word`, or "".
        """
        if not isinstance(word, str):
            return ""
        close = difflib.get_close_matches(word, builtins.list(choices), n=3)
        if not close:
            return ""
        return " Did you mean " + " or ".join(repr(i) for i in close) + "?"

    def source_here():
        """
        The file and line of the statement running now, as "file:line".
        """
        try:
            filename, line = renpy.get_filename_line()
            return "%s:%s" % (filename, line)
        except Exception:
            return "an unknown place"

    def register_kind(kind, per_twin, id_parts=1, asset_dir=None):
        """
        Registers a kind of definition. Call at init, before making any
        definition of this kind.

        `per_twin`
            True if each twin has their own flags for definitions of this
            kind, False if the twins share them.
        `id_parts`
            How many dot-separated parts its ids have, e.g. 3 for locations
            ("space.place.location").
        `asset_dir`
            The folder under images/ that holds its assets (see
            core.asset), e.g. "world" for locations. Default: the kind.
        """
        if frozen:
            raise FrozenError("core: kinds are registered at init; tried to register %r after init." % (kind,))
        if not isinstance(kind, str) or not SEGMENT_RE.fullmatch(kind):
            raise ValueError("core: %r is not a valid kind name. Use ASCII snake_case, like 'npc' or 'gallery_set'." % (kind,))
        if kind in KINDS:
            raise ValueError("core: kind %r is already registered." % (kind,))
        if not isinstance(per_twin, bool):
            raise TypeError("core: register_kind(%r): per_twin must be True or False, not %r." % (kind, per_twin))
        if isinstance(id_parts, bool) or not isinstance(id_parts, int) or id_parts < 1:
            raise ValueError("core: register_kind(%r): id_parts must be a whole number from 1 up, not %r." % (kind, id_parts))

        if asset_dir is None:
            asset_dir = kind
        if not isinstance(asset_dir, str) or not ASSET_DIR_RE.fullmatch(asset_dir):
            raise ValueError("core: register_kind(%r): asset_dir %r must be snake_case folder names joined by '/', like 'world'." % (kind, asset_dir))

        pattern = re.compile(r"\.".join([ SEGMENT ] * id_parts))
        KINDS[kind] = KindInfo(kind, per_twin, id_parts, pattern, asset_dir)
        REGISTRY[kind] = { }

    def kind_info(kind):
        """
        The KindInfo of a registered kind. Raises LookupError for an unknown
        kind.
        """
        info = KINDS.get(kind)
        if info is None:
            raise LookupError("core: unknown kind %r.%s Kinds are added with core.register_kind()." % (kind, did_you_mean(kind, KINDS)))
        return info

    def check_id(kind, id):
        """
        Raises ValueError unless `id` is a valid id for `kind`.
        """
        info = kind_info(kind)
        if isinstance(id, str) and info.pattern.fullmatch(id):
            return

        word = "lowercase letters, digits and single underscores, starting with a letter"
        if info.id_parts == 1:
            shape = "ASCII snake_case (%s)" % word
        else:
            shape = "%d parts separated by dots, each ASCII snake_case (%s)" % (info.id_parts, word)
        raise ValueError("core: %r is not a valid %s id. Expected %s." % (id, kind, shape))

    def is_plain(value):
        """
        True if `value` may go in a template: None, bool, int, float, str, or
        a tuple of those.
        """
        if isinstance(value, tuple):
            return builtins.all(is_plain(i) for i in value)
        return isinstance(value, PLAIN_TYPES)

    def make_template(kind, id, template):
        """
        Checks a definition's template and returns a read-only copy.
        """
        rv = { }

        if template is not None:
            if not hasattr(template, "items"):
                raise TypeError("core: %s %r: template must be a dict, not %r." % (kind, id, template))

            for key, value in template.items():
                if not isinstance(key, str) or not SEGMENT_RE.fullmatch(key):
                    raise ValueError("core: %s %r: template key %r is not ASCII snake_case." % (kind, id, key))
                if not is_plain(value):
                    raise ValueError("core: %s %r: template value of %r is %r. Use None, bool, int, float, str, or a tuple of those." % (kind, id, key, value))
                rv[key] = value

        return types.MappingProxyType(rv)

    class Definition(store.NoRollback):
        """
        Base class for definitions. A subclass sets `kind` to a registered
        kind, and its __init__ calls Definition.__init__(self, id, template).

        `id`
            Unique within the kind; see check_id().
        `template`
            A dict of flag keys to default values: None, bool, int, float,
            str, or tuples of those. Kept as a read-only copy.

        The definition registers itself. It can be changed until the end of
        init; after that, setting or deleting an attribute raises FrozenError
        in developer mode.
        """

        kind = None

        def __init__(self, id, template=None):
            kind = self.kind

            if frozen:
                raise FrozenError("core: definitions are made at init; tried to make %s %r after init." % (kind, id))
            if kind is None:
                raise TypeError("core: %s has no kind. Set kind = \"...\" on the class." % type(self).__name__)

            check_id(kind, id)

            ids = REGISTRY[kind]
            if id in ids:
                raise ValueError("core: duplicate %s id %r. The first one was made at %s." % (kind, id, SOURCES.get((kind, id), "an unknown place")))

            self.id = id
            self.template = make_template(kind, id, template)

            ids[id] = self
            SOURCES[(kind, id)] = source_here()

        def __setattr__(self, name, value):
            if frozen and renpy.config.developer:
                raise FrozenError("core: %r is frozen; definitions can't change after init (tried to set %r)." % (self, name))
            super().__setattr__(name, value)

        def __delattr__(self, name):
            if frozen and renpy.config.developer:
                raise FrozenError("core: %r is frozen; definitions can't change after init (tried to delete %r)." % (self, name))
            super().__delattr__(name)

        def __reduce__(self):
            return (defref, (self.kind, self.id))

        def __repr__(self):
            return "<%s %s>" % (self.kind, getattr(self, "id", "?"))

    def defref(kind, id):
        """
        Finds a definition again when a pickle is loaded (see
        Definition.__reduce__). Follows RENAMES. Returns None, with a warning,
        if the definition no longer exists.
        """
        ids = REGISTRY.get(kind)
        if ids is None:
            warn("a save refers to %s %r, but kind %r no longer exists." % (kind, id, kind))
            return None

        renames = RENAMES.get(kind)
        if renames:
            id = renames.get(id, id)

        rv = ids.get(id)
        if rv is None:
            warn("a save refers to %s %r, which no longer exists." % (kind, id))
        return rv

    def get(kind, id):
        """
        The definition of `kind` with `id`. Raises LookupError if there is
        none.
        """
        ids = REGISTRY.get(kind)
        if ids is None:
            kind_info(kind) # raises LookupError

        rv = ids.get(id)
        if rv is None:
            raise LookupError("core: there is no %s with id %r.%s" % (kind, id, did_you_mean(id, ids)))
        return rv

    def exists(kind, id):
        """
        True if `kind` has a definition with `id`. Raises LookupError for an
        unknown kind.
        """
        ids = REGISTRY.get(kind)
        if ids is None:
            kind_info(kind) # raises LookupError
        return id in ids

    def all(kind):
        """
        A tuple of all definitions of `kind`, in creation order. Not for
        screens: precompute what a screen needs instead.
        """
        rv = ALL_TUPLES.get(kind)
        if rv is not None:
            return rv
        kind_info(kind) # raises LookupError for an unknown kind
        return tuple(REGISTRY[kind].values())

    def kinds():
        """
        The names of all registered kinds, sorted, as a tuple. Fine in
        screens.
        """
        return tuple(builtins.sorted(KINDS))

    def per_twin(kind):
        """
        True if each twin has their own flags for `kind`. Raises LookupError
        for an unknown kind.
        """
        return kind_info(kind).per_twin

    def is_frozen():
        """
        True once init has finished and definitions are frozen.
        """
        return frozen

    def freeze():
        """
        Freezes definitions and the registry. Runs once, at the end of init.
        """
        global frozen

        for kind, ids in REGISTRY.items():
            ALL_TUPLES[kind] = tuple(ids.values())

        freeze_signals() # signals_py.rpy
        freeze_saves() # saves_py.rpy
        check_reqs() # req_py.rpy

        frozen = True


# Freeze after all other init code, so other folders can still finish setting
# up their definitions at init 900 (validation), whatever their folder names.
init offset = 999

init python in core:
    freeze()
