# Saves: versions, migrations, renamed ids, and what the load screen shows.
#
# After a save is loaded (after_load), in this order:
#   1. Migrations: each @core.migration(version) function newer than the
#      save's gs.version runs, oldest first, and gs.version goes up.
#   2. Renames: core.RENAMES ({kind: {old_id: new_id}}) is applied to flags,
#      and to the section keys registered with ids=.
#   3. Sections: missing sections and keys are added (ensure_sections).
# If anything changed, rollback is blocked. Then game_loaded is emitted.
#
# core.SAVE_VERSION is the highest migration version (1 with none), set when
# init ends, so a folder adding a migration doesn't need to change core.
# Migration numbers are shared by all folders: take the next free one, and
# never reuse one after a release.
#
# Each save's JSON (FileJson in the load screen) gets version, twin, day and
# slot, plus the fields from core.register_save_info() functions. In
# developer mode, saving also checks that gs holds only plain data.
#
# core.snapshot() gives gs as plain data, and core.migrate(data) runs such
# data through the same steps as a load, without touching the live gs (dev/'s
# fixture saves).

init offset = -500

init python in core:
    _constant = True

    import builtins
    import json
    import traceback

    import store

    # version -> function(gs)
    MIGRATIONS = { }

    # functions returning extra fields for the save JSON
    SAVE_INFO = [ ]

    ##########################################################################
    # Migrations.

    def check_version(version):
        if isinstance(version, bool) or not isinstance(version, int) or version < 2:
            raise ValueError("core: migration versions are whole numbers from 2 up (1 is the first layout), not %r." % (version,))

    def migration(version):
        """
        Decorator for a function that takes gs and updates a save older than
        `version` to that version's layout. Use at init.

            @core.migration(2)
            def migrate_world_2(gs):
                ...
        """
        if frozen:
            raise FrozenError("core: migrations are added at init; tried to add %r after init." % (version,))
        check_version(version)

        def register(fn):
            add_migration(MIGRATIONS, version, fn)
            return fn

        return register

    def add_migration(table, version, fn):
        """
        Adds fn to `table` (version -> function) as migration `version`.
        """
        check_version(version)
        if not callable(fn):
            raise TypeError("core: migration %r: %r can't be called." % (version, fn))
        if version in table:
            raise ValueError("core: migration %d is already %s. Give %s the next free number." % (version, describe_fn(table[version]), describe_fn(fn)))
        table[version] = fn

    def run_migrations(gs, migrations=None, target=None):
        """
        Runs the migrations newer than gs.version, oldest first, and sets
        gs.version to `target` (default: SAVE_VERSION). Returns True if it
        changed anything.
        """
        if migrations is None:
            migrations = MIGRATIONS
        if target is None:
            target = SAVE_VERSION

        version = gs.version
        if version > target:
            warn("this save is from a newer version of the game (save version %r, game version %r)." % (version, target))
            return False

        changed = False
        for v in builtins.sorted(migrations):
            if version < v <= target:
                migrations[v](gs)
                gs.version = v
                changed = True

        if gs.version != target:
            gs.version = target
            changed = True

        return changed

    ##########################################################################
    # Renames.

    def rename_problems(renames):
        """
        Problems in a RENAMES-style table: unknown kinds, old ids that still
        exist, new ids that don't.
        """
        rv = [ ]
        for kind, table in renames.items():
            if kind not in KINDS:
                rv.append("  RENAMES[%r]: unknown kind.%s" % (kind, did_you_mean(kind, KINDS)))
                continue
            for old, new in table.items():
                if old in REGISTRY[kind]:
                    rv.append("  RENAMES[%r][%r]: %r still exists, so it can't be an old id." % (kind, old, old))
                if new not in REGISTRY[kind]:
                    rv.append("  RENAMES[%r][%r]: the new id %r doesn't exist. Map each old id straight to the current id." % (kind, old, new))
        return rv

    def section_id_problems():
        """
        Problems in the ids= of registered sections: unknown kinds.
        """
        rv = [ ]
        for info in SYSTEMS.values():
            for key, kind in info.ids.items():
                if kind not in KINDS:
                    rv.append("  section %r: ids[%r] is unknown kind %r.%s" % (info.system, key, kind, did_you_mean(kind, KINDS)))
        return rv

    def rename_value(value, renames):
        """
        Applies `renames` ({old_id: new_id}) to one id, or to the ids in a
        list, set, tuple or the keys of a dict. Returns (value, changed).
        Lists, sets and dicts change in place; for a dict, a value already
        under the new id wins.
        """
        if isinstance(value, str):
            if value in renames:
                return renames[value], True
            return value, False

        if isinstance(value, tuple):
            new = tuple(renames.get(i, i) if isinstance(i, str) else i for i in value)
            return new, new != value

        if isinstance(value, builtins.list):
            changed = False
            for i, v in enumerate(value):
                if isinstance(v, str) and v in renames:
                    value[i] = renames[v]
                    changed = True
            return value, changed

        if isinstance(value, builtins.set):
            old = [ v for v in value if isinstance(v, str) and v in renames ]
            for v in old:
                value.discard(v)
                value.add(renames[v])
            return value, bool(old)

        if isinstance(value, builtins.dict):
            old = [ k for k in value if isinstance(k, str) and k in renames ]
            for k in old:
                v = value.pop(k)
                if renames[k] not in value:
                    value[renames[k]] = v
            return value, bool(old)

        return value, False

    def apply_renames(gs, renames=None):
        """
        Applies `renames` (default: RENAMES) to the flags in gs and to the
        id keys of sections. When flags exist under both ids, the new id's
        values win. Returns True if it changed anything.
        """
        if renames is None:
            renames = RENAMES

        changed = False

        for flags in [ gs.shared["flags"] ] + [ t.flags for t in gs.twins.values() ]:
            for kind, table in renames.items():
                ids = flags.get(kind)
                if not ids:
                    continue

                for old, new in table.items():
                    if old not in ids:
                        continue

                    keys = ids.pop(old)
                    changed = True

                    target = ids.get(new)
                    if target is None:
                        ids[new] = keys
                        continue

                    for k, v in keys.items():
                        if k not in target:
                            target[k] = v

        for info in SYSTEMS.values():
            for key, kind in info.ids.items():
                table = renames.get(kind)
                if not table:
                    continue

                for container in section_containers(gs, info):
                    section = container.get(info.system)
                    if section is None or key not in section:
                        continue

                    value, did = rename_value(section[key], table)
                    if did:
                        section[key] = value
                        changed = True

        return changed

    ##########################################################################
    # Loading.

    def update_state(gs, migrations=None, target=None, renames=None):
        """
        Brings a loaded gs up to date with the current code: migrations,
        then renames, then missing sections. Returns True if it changed
        anything.
        """
        changed = run_migrations(gs, migrations, target)
        if apply_renames(gs, renames):
            changed = True
        if ensure_sections(gs):
            changed = True
        return changed

    def after_load():
        """
        Runs after a save is loaded (config.after_load_callbacks).
        """
        if update_state(store.gs):
            renpy.block_rollback()

        emit("game_loaded")

    renpy.config.after_load_callbacks.append(after_load)

    ##########################################################################
    # Saving.

    def register_save_info(fn):
        """
        fn() returns a dict of extra fields for each save's JSON, which the
        load screen reads with FileJson. Keys are snake_case and unique
        across folders; values are JSON (None, bool, int, float, str, lists
        and dicts). Call at init.
        """
        if frozen:
            raise FrozenError("core: save info is registered at init; tried to register %r after init." % (fn,))
        if not callable(fn):
            raise TypeError("core: register_save_info: %r can't be called." % (fn,))
        SAVE_INFO.append(fn)

    def add_fields(d, fields, fn):
        """
        Adds the fields one save info function returned to the save JSON d.
        """
        if not isinstance(fields, builtins.dict):
            raise TypeError("core: save info from %s must be a dict, not %r." % (describe_fn(fn), fields))

        for k, v in fields.items():
            if not isinstance(k, str) or not SEGMENT_RE.fullmatch(k):
                raise ValueError("core: save info from %s: key %r is not ASCII snake_case." % (describe_fn(fn), k))
            if k in d:
                raise ValueError("core: save info from %s: field %r is already used." % (describe_fn(fn), k))
            try:
                json.dumps(v)
            except (TypeError, ValueError):
                raise TypeError("core: save info from %s: field %r is %r, which isn't JSON." % (describe_fn(fn), k, v))
            d[k] = v

    def add_save_info(d, providers, strict):
        """
        Adds the fields of each save info function to d. If `strict` is
        False, an error in one is logged and the others still run.
        """
        for fn in providers:
            if strict:
                add_fields(d, fn(), fn)
                continue

            try:
                add_fields(d, fn(), fn)
            except CONTROL_EXCEPTIONS:
                raise
            except Exception:
                warn("save info from %s failed; the save goes on without it.\n%s" % (describe_fn(fn), traceback.format_exc()))

    def check_saveable(gs):
        """
        Raises TypeError if gs holds something other than plain data.
        """
        where = find_unplain(gs, "gs", strict=True)
        if where is not None:
            raise TypeError("core: %s can't be in gs. gs holds only plain data: None, bool, int, float, str, and tuples, lists, dicts and sets made in .rpy code." % (where,))

    def save_json(d):
        """
        Adds version, twin, day, slot and the save info fields to a save's
        JSON (config.save_json_callbacks).
        """
        gs = getattr(store, "gs", None)
        if gs is None:
            return

        developer = renpy.config.developer
        if developer:
            check_saveable(gs)

        ts = gs.twins[gs.twin]
        d["version"] = gs.version
        d["twin"] = gs.twin
        d["day"] = ts.day
        d["slot"] = ts.slot

        add_save_info(d, SAVE_INFO, developer)

    renpy.config.save_json_callbacks.append(save_json)

    ##########################################################################

    def freeze_saves():
        """
        Checks RENAMES and section ids, and sets SAVE_VERSION. Called by
        freeze().
        """
        global SAVE_VERSION

        problems = rename_problems(RENAMES) + section_id_problems()
        if problems:
            raise LookupError("core: problems with renamed ids:\n" + "\n".join(problems))

        SAVE_VERSION = builtins.max(MIGRATIONS, default=1)

    ##########################################################################
    # Snapshots: gs as plain data, and migrating plain data (dev/'s fixture
    # saves).
    #
    #     {"version", "twin", "shared": {"flags", "sys"},
    #      "twins": {twin: {"day", "slot", "flags", "sys"}}}

    SNAPSHOT_SHAPE = ("version", "twin", "shared", "twins")
    SNAPSHOT_SHARED_SHAPE = ("flags", "sys")
    SNAPSHOT_TWIN_SHAPE = ("day", "slot", "flags", "sys")

    def snapshot_of(gs):
        """
        `gs` (a GameState) as new plain data in the snapshot shape.
        """
        twins = { }
        for twin, t in gs.twins.items():
            twins[twin] = { "day": t.day, "slot": t.slot, "flags": copy_plain(t.flags), "sys": copy_plain(t.sys) }

        return {
            "version": gs.version,
            "twin": gs.twin,
            "shared": { "flags": copy_plain(gs.shared["flags"]), "sys": copy_plain(gs.shared["sys"]) },
            "twins": twins,
            }

    def snapshot():
        """
        The live gs as new plain data that shares nothing with it:
        {"version", "twin", "shared": {"flags", "sys"}, "twins": {twin:
        {"day", "slot", "flags", "sys"}}}.
        """
        return snapshot_of(store.gs)

    def snapshot_error(message):
        return ValueError("core: migrate: %s. The data must have the shape of core.snapshot()." % (message,))

    def check_keys(d, keys, path):
        """
        Raises unless d is a dict with exactly these keys.
        """
        if not isinstance(d, builtins.dict):
            raise snapshot_error("%s is %r, not a dict" % (path, d))
        for k in keys:
            if k not in d:
                raise snapshot_error("%s has no %r" % (path, k))
        for k in d:
            if k not in keys:
                raise snapshot_error("%s has an unknown key %r" % (path, k))

    def check_number(value, path, allowed=None):
        """
        Raises unless value is a whole number from 1 up (or in `allowed`).
        """
        ok = not isinstance(value, bool) and isinstance(value, int)
        if ok:
            ok = value in allowed if allowed is not None else value >= 1
        if not ok:
            raise snapshot_error("%s is %r" % (path, value))

    def check_snapshot(data):
        """
        Raises ValueError unless `data` has the snapshot shape and holds
        only plain data.
        """
        check_keys(data, SNAPSHOT_SHAPE, "data")
        check_number(data["version"], "data['version']")
        if data["twin"] not in TWINS:
            raise snapshot_error("data['twin'] is %r, not one of %s" % (data["twin"], ", ".join(TWINS)))

        check_keys(data["shared"], SNAPSHOT_SHARED_SHAPE, "data['shared']")
        for k in SNAPSHOT_SHARED_SHAPE:
            if not isinstance(data["shared"][k], builtins.dict):
                raise snapshot_error("data['shared'][%r] is %r, not a dict" % (k, data["shared"][k]))

        check_keys(data["twins"], TWINS, "data['twins']")
        for twin in TWINS:
            path = "data['twins'][%r]" % (twin,)
            d = data["twins"][twin]
            check_keys(d, SNAPSHOT_TWIN_SHAPE, path)
            check_number(d["day"], path + "['day']")
            check_number(d["slot"], path + "['slot']", SLOTS)
            for k in ("flags", "sys"):
                if not isinstance(d[k], builtins.dict):
                    raise snapshot_error("%s[%r] is %r, not a dict" % (path, k, d[k]))

        where = find_unplain(data, "data")
        if where is not None:
            raise snapshot_error("%s isn't plain data" % (where,))

    def check_renames(renames):
        """
        Raises ValueError unless `renames` is {kind: {old_id: new_id}}.
        """
        ok = isinstance(renames, builtins.dict)
        if ok:
            for kind, table in renames.items():
                if not isinstance(kind, str) or not isinstance(table, builtins.dict):
                    ok = False
                    break
                if not builtins.all(isinstance(o, str) and isinstance(n, str) for o, n in table.items()):
                    ok = False
                    break
        if not ok:
            raise ValueError("core: migrate: renames must be {kind: {old_id: new_id}}, not %r." % (renames,))

    def gamestate_from(data):
        """
        A detached GameState holding a copy of snapshot-shaped data. Made
        without __init__, which would add sections before migrations run.
        """
        gs = GameState.__new__(GameState)
        gs.version = data["version"]
        gs.twin = data["twin"]
        gs.shared = { "flags": copy_plain(data["shared"]["flags"]), "sys": copy_plain(data["shared"]["sys"]) }
        gs.twins = { }

        for twin in TWINS:
            d = data["twins"][twin]
            ts = TwinState.__new__(TwinState)
            ts.day = d["day"]
            ts.slot = d["slot"]
            ts.flags = copy_plain(d["flags"])
            ts.sys = copy_plain(d["sys"])
            gs.twins[twin] = ts

        return gs

    def migrate(data, migrations=None, renames=None):
        """
        New plain data in the snapshot shape: `data` brought up to date by
        the code a load uses (update_state): migrations newer than
        data["version"], then renames, then missing sections and keys.

        `migrations`
            {version: function} to use instead of the registered migrations;
            the target version is then the highest of them. For tests.
        `renames`
            {kind: {old_id: new_id}} to use instead of core.RENAMES.

        The migrations get a detached GameState made from the data. While
        they run, store.gs is that GameState (as during a load, so helpers
        like core.state() work on it); the live gs is put back afterwards
        and never changed. Emits nothing and doesn't block rollback.
        """
        check_snapshot(data)

        if migrations is None:
            table = MIGRATIONS
            target = SAVE_VERSION
        else:
            if not isinstance(migrations, builtins.dict):
                raise TypeError("core: migrate: migrations must be {version: function}, not %r." % (migrations,))
            table = { }
            for version, fn in migrations.items():
                add_migration(table, version, fn)
            target = builtins.max(table, default=1)

        if renames is None:
            renames = RENAMES
        else:
            check_renames(renames)

        if data["version"] > target:
            raise ValueError("core: migrate: the data is version %r, newer than version %r." % (data["version"], target))

        gs = gamestate_from(data)

        had_live = hasattr(store, "gs")
        live = getattr(store, "gs", None)
        store.gs = gs

        try:
            update_state(gs, table, target, renames)
        finally:
            if had_live:
                store.gs = live
            else:
                del store.gs

        return snapshot_of(gs)
