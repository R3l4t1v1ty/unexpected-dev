# The saved state: gs, flags and system sections.
#
# All mutable game state lives in one saved object, gs (a GameState):
#
#     gs.version   save format version
#     gs.twin      the twin being played
#     gs.shared    {"flags": {...}, "sys": {...}}, shared by both twins
#     gs.twins     {twin: TwinState}, with .day, .slot, .flags, .sys
#
# Flags are sparse: flags[kind][id][key] holds only values that differ from
# the definition's template, so new content reaches old saves by itself.
# Kinds registered with per_twin=True keep their flags in the twin's
# TwinState, others in gs.shared.
#
# A section is a dict of plain data owned by one system, e.g. world's current
# location: sys[system]. Sections are made at new game; on load, missing
# sections and missing top-level keys are added from their initial values.
#
# gs holds only plain data: None, bool, int, float, str, tuples, and lists,
# dicts and sets made in .rpy code (Ren'Py makes those rollback-safe).
# GameState and TwinState are pickled by name: never rename them.

init offset = -500

default gs = core.GameState()

init python in core:
    _constant = True

    import builtins
    import collections
    import types

    import store

    TWINS = ("ayumu", "nemu")

    # The version of gs's layout: the highest migration version, set when init
    # ends (saves_py.rpy). Read it only after init.
    SAVE_VERSION = 1

    # A read-only empty dict, for lookups that must not write.
    EMPTY = types.MappingProxyType({ })

    class GameState(store.object):
        """
        The saved state. There is one: gs.
        """

        def __init__(self):
            super().__init__()

            self.version = SAVE_VERSION
            self.twin = TWINS[0]
            self.shared = { "flags": { }, "sys": { } }
            self.twins = { }

            for twin in TWINS:
                self.twins[twin] = TwinState()

            ensure_sections(self)

    class TwinState(store.object):
        """
        The saved state of one twin.
        """

        def __init__(self):
            super().__init__()

            self.day = 1
            self.slot = 0
            self.flags = { }
            self.sys = { }

    def resolve_twin(twin):
        """
        `twin`, or the current twin if it's None. Raises ValueError for an
        unknown twin.
        """
        if twin is None:
            return store.gs.twin
        if twin not in TWINS:
            raise ValueError("core: unknown twin %r. The twins are %s." % (twin, ", ".join(TWINS)))
        return twin

    def twin_state(twin=None):
        """
        The TwinState of `twin` (default: the current twin).
        """
        return store.gs.twins[resolve_twin(twin)]

    def new_game():
        """
        Called by label start: makes sure every section exists, then emits
        game_started.
        """
        ensure_sections(store.gs)
        emit("game_started")

    ##########################################################################
    # Plain data.

    # The rollback-safe dict, list and set types that .rpy code makes.
    REVERTABLE_TYPES = (type({ }), type([ ]), type(set()))

    def find_unplain(value, path="value", strict=False):
        """
        Where `value` holds something that isn't plain data, as a path like
        "value['x'][0] (Thing)", or None if it's all plain data: None, bool,
        int, float, str, and tuples, lists, dicts and sets of those.

        With `strict`, lists, dicts and sets must also be rollback-safe, and
        GameState and TwinState objects are looked into: this checks gs.
        """
        if strict:
            if isinstance(value, (GameState, TwinState)):
                for k, v in vars(value).items():
                    rv = find_unplain(v, "%s.%s" % (path, k), strict)
                    if rv is not None:
                        return rv
                return None

            if isinstance(value, (builtins.dict, builtins.list, builtins.set)) and type(value) not in REVERTABLE_TYPES:
                return "%s (a %s that isn't rollback-safe: make it in .rpy code, or copy it with core.copy_plain)" % (path, type(value).__name__)

        if isinstance(value, builtins.dict):
            for k, v in value.items():
                if not is_plain(k):
                    return "%s key %r (%s)" % (path, k, type(k).__name__)
                rv = find_unplain(v, "%s[%r]" % (path, k), strict)
                if rv is not None:
                    return rv
            return None

        if isinstance(value, (builtins.list, builtins.set, tuple)):
            for i, v in enumerate(value):
                rv = find_unplain(v, "%s[%d]" % (path, i), strict)
                if rv is not None:
                    return rv
            return None

        if isinstance(value, PLAIN_TYPES):
            return None

        return "%s (%s)" % (path, type(value).__name__)

    def copy_plain(value):
        """
        A deep copy of plain data, with lists, dicts and sets made here so
        they're rollback-safe.
        """
        if isinstance(value, builtins.dict):
            rv = { }
            for k, v in value.items():
                rv[k] = copy_plain(v)
            return rv

        if isinstance(value, builtins.list):
            rv = [ ]
            for i in value:
                rv.append(copy_plain(i))
            return rv

        if isinstance(value, builtins.set):
            rv = set()
            for i in value:
                rv.add(copy_plain(i))
            return rv

        if isinstance(value, tuple):
            return tuple(copy_plain(i) for i in value)

        return value

    ##########################################################################
    # Flags.

    def kind_flags(kind, twin):
        """
        The flags dict that holds `kind`'s flags: the twin's or the shared
        one.
        """
        twin = resolve_twin(twin)
        if KINDS[kind].per_twin:
            return store.gs.twins[twin].flags
        return store.gs.shared["flags"]

    def template_default(defn, key):
        """
        The default of flag `key` of `defn`. Raises LookupError if the
        template has no such key.
        """
        try:
            return defn.template[key]
        except KeyError:
            pass
        raise LookupError("core: %r has no flag %r.%s Flags are the keys of the definition's template." % (defn, key, did_you_mean(key, defn.template)))

    def flag(kind, id, key, twin=None):
        """
        The value of flag `key` of definition (kind, id): the stored value,
        or the template's default. `twin` (default: the current twin)
        matters only for per-twin kinds. Never changes gs.
        """
        default = template_default(get(kind, id), key)
        return kind_flags(kind, twin).get(kind, EMPTY).get(id, EMPTY).get(key, default)

    def set_flag(kind, id, key, value, twin=None):
        """
        Sets flag `key` of definition (kind, id). Only values that differ
        from the template's default are stored; setting the default (same
        value and type) removes the flag.
        """
        defn = get(kind, id)
        default = template_default(defn, key)

        if not is_plain(value):
            raise ValueError("core: flag %r of %r can't be %r. Use None, bool, int, float, str, or a tuple of those." % (key, defn, value))

        flags = kind_flags(kind, twin)

        if type(value) is type(default) and value == default:
            ids = flags.get(kind)
            if ids is None:
                return
            keys = ids.get(id)
            if keys is None or key not in keys:
                return

            del keys[key]
            if not keys:
                del ids[id]
                if not ids:
                    del flags[kind]
            return

        ids = flags.get(kind)
        if ids is None:
            ids = flags[kind] = { }

        keys = ids.get(id)
        if keys is None:
            keys = ids[id] = { }

        keys[key] = value

    ##########################################################################
    # System sections.

    SystemInfo = collections.namedtuple("SystemInfo", ("system", "initial", "per_twin", "ids"))

    # system -> SystemInfo
    SYSTEMS = { }

    def register_state(system, initial, per_twin, ids=None):
        """
        Registers a system's section of gs. Call at init.

        `initial`
            A dict of plain data: the section at new game. Keys missing from
            a loaded save are filled from it.
        `per_twin`
            True if each twin has their own section.
        `ids`
            {key: kind} for the keys of the section that hold ids of a kind:
            one id, or a list, set or tuple of ids, or a dict keyed by id.
            On load, core.RENAMES is applied to them.
        """
        if frozen:
            raise FrozenError("core: sections are registered at init; tried to register %r after init." % (system,))
        if not isinstance(system, str) or not SEGMENT_RE.fullmatch(system):
            raise ValueError("core: %r is not a valid system name. Use ASCII snake_case, like 'world'." % (system,))
        if system in SYSTEMS:
            raise ValueError("core: system %r already has a section." % (system,))
        if not isinstance(per_twin, bool):
            raise TypeError("core: register_state(%r): per_twin must be True or False, not %r." % (system, per_twin))
        if not isinstance(initial, builtins.dict):
            raise TypeError("core: register_state(%r): initial must be a dict, not %r." % (system, initial))

        where = find_unplain(initial, "initial")
        if where is not None:
            raise ValueError("core: register_state(%r): %s isn't plain data. Sections hold only None, bool, int, float, str, and tuples, lists, dicts and sets of those." % (system, where))

        if ids is None:
            ids = { }
        if not isinstance(ids, builtins.dict):
            raise TypeError("core: register_state(%r): ids must be a dict of {key: kind}, not %r." % (system, ids))
        for key, kind in ids.items():
            if key not in initial:
                raise ValueError("core: register_state(%r): ids names key %r, which isn't in initial." % (system, key))
            if not isinstance(kind, str):
                raise TypeError("core: register_state(%r): ids[%r] must be a kind name, not %r." % (system, key, kind))

        SYSTEMS[system] = SystemInfo(system, copy_plain(initial), per_twin, types.MappingProxyType(builtins.dict(ids)))

    def system_info(system):
        """
        The SystemInfo of a registered system. Raises LookupError for an
        unknown one.
        """
        info = SYSTEMS.get(system)
        if info is None:
            raise LookupError("core: unknown system %r.%s Sections are added with core.register_state()." % (system, did_you_mean(system, SYSTEMS)))
        return info

    def state(system, twin=None):
        """
        The section (a dict) of `system`. `twin` (default: the current twin)
        matters only for per-twin sections. Change it only from Python code
        that runs in the game, never from screens.
        """
        info = system_info(system)
        twin = resolve_twin(twin)

        if info.per_twin:
            container = store.gs.twins[twin].sys
        else:
            container = store.gs.shared["sys"]

        rv = container.get(system)
        if rv is None:
            raise LookupError("core: gs has no %r section, which should have been made at new game or on load." % (system,))
        return rv

    def section_containers(gs, info):
        """
        The dicts of `gs` that hold sections of system `info`: each twin's
        sys for a per-twin system, else the shared one.
        """
        if info.per_twin:
            return [ t.sys for t in gs.twins.values() ]
        return [ gs.shared["sys"] ]

    def ensure_sections(gs):
        """
        Adds missing sections to `gs`, and missing top-level keys to
        existing ones, from their initial values. Returns True if it changed
        anything.
        """
        changed = False

        for info in SYSTEMS.values():
            for container in section_containers(gs, info):
                section = container.get(info.system)

                if section is None:
                    container[info.system] = copy_plain(info.initial)
                    changed = True
                    continue

                for key, value in info.initial.items():
                    if key not in section:
                        section[key] = copy_plain(value)
                        changed = True

        return changed
