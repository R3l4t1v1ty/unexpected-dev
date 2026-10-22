# Tests for registry_py.rpy: definitions, kinds, ids, freezing, pickling.
# Developer only; excluded from builds.
#
# Run: start a game, press Shift+O, type: jump test_core_registry

init offset = 0

init python in core_test:
    _constant = True

    import copy
    import pickle

    from store import core

    class Thing(core.Definition):
        kind = "core_test"

    class Other(core.Definition):
        kind = "core_test_other"

    class Place(core.Definition):
        kind = "core_test_place"

    class Unregistered(core.Definition):
        kind = "core_test_unregistered"

    class NoKind(core.Definition):
        pass

    core.register_kind("core_test", False)
    core.register_kind("core_test_other", False)
    core.register_kind("core_test_place", True, id_parts=3)

    ALPHA_TEMPLATE = {
        "seen": False,
        "count": 0,
        "ratio": 0.5,
        "label": "Template Value",
        "pair": (1, ("a", None)),
        }

    ALPHA = Thing("alpha", ALPHA_TEMPLATE)
    BETA = Thing("beta")
    GAMMA = Thing("gamma_2")
    OTHER_ALPHA = Other("alpha")
    ROOM = Place("town.home.living_room", { "visited": False })
    HALL = Place("town.home.hall")

    core.RENAMES["core_test"] = { "old_alpha": "alpha" }

    def registry_init_checks():
        """
        Checks that can only run at init, before the registry is frozen.
        """
        c = Checks("init")

        c.raises("register_kind: same kind twice", ValueError, core.register_kind, "core_test", False)
        c.raises("register_kind: bad kind name", ValueError, core.register_kind, "Core-Test", False)
        c.raises("register_kind: per_twin not a bool", TypeError, core.register_kind, "core_test_bad", 1)
        c.raises("register_kind: id_parts 0", ValueError, core.register_kind, "core_test_bad", False, 0)
        c.check("register_kind: failed calls register nothing", "core_test_bad" not in core.KINDS)

        try:
            Thing("alpha")
            c.check("duplicate id raises", False, "did not raise")
        except ValueError as e:
            c.check("duplicate id raises", True, e)
            c.check("duplicate message says where the first was made", "registry_test.rpy" in str(e), e)
        c.check("duplicate keeps the first", core.get("core_test", "alpha") is ALPHA)
        c.check("same id in another kind is fine", core.get("core_test_other", "alpha") is OTHER_ALPHA)

        c.raises("bad id raises at creation", ValueError, Thing, "Bad")
        c.raises("3-part kind rejects a 2-part id", ValueError, Place, "town.home")
        c.raises("unregistered kind raises", LookupError, Unregistered, "x")
        c.raises("class without a kind raises", TypeError, NoKind, "x")
        c.raises("template that isn't a dict", TypeError, Thing, "t_1", 5)
        c.raises("template with a bad key", ValueError, Thing, "t_2", { "Bad Key": 1 })
        c.raises("template with a list value", ValueError, Thing, "t_3", { "items": [ ] })
        c.raises("template with a list inside a tuple", ValueError, Thing, "t_4", { "items": (1, [ ]) })
        c.check("failed creations register nothing",
            not any(core.exists("core_test", i) for i in ("Bad", "t_1", "t_2", "t_3", "t_4"))
            and not core.exists("core_test_place", "town.home"))

        ALPHA_TEMPLATE["count"] = 99
        c.equal("template is a copy of the dict passed in", ALPHA.template["count"], 0)

        c.check("not frozen during init", not core.is_frozen())
        GAMMA.extra = 1
        c.equal("definitions can change during init", GAMMA.extra, 1)

        return c

    REGISTRY_INIT = registry_init_checks()

    def set_item(d, key, value):
        d[key] = value

    def registry_checks():
        c = Checks("core: registry")
        c.extend(REGISTRY_INIT)

        c.check("frozen after init", core.is_frozen())

        # Ids.
        for kind, id in (
                ("core_test", "alpha"),
                ("core_test", "b"),
                ("core_test", "hana_1"),
                ("core_test", "a1_b2_c3"),
                ("core_test_place", "town.home.living_room"),
                ("core_test_place", "a.b2.c_d"),
                ):
            c.no_raise("good id %s %r" % (kind, id), core.check_id, kind, id)

        for kind, id in (
                ("core_test", ""),
                ("core_test", "Alpha"),
                ("core_test", "1abc"),
                ("core_test", "_a"),
                ("core_test", "a_"),
                ("core_test", "a__b"),
                ("core_test", "a-b"),
                ("core_test", "a b"),
                ("core_test", "a\n"),
                ("core_test", "a.b"),
                ("core_test", "café"),
                ("core_test", 5),
                ("core_test", None),
                ("core_test_place", "town.home"),
                ("core_test_place", "town..hall"),
                ("core_test_place", "town.home.hall."),
                ("core_test_place", "a.b.c.d"),
                ):
            c.raises("bad id %s %r" % (kind, id), ValueError, core.check_id, kind, id)

        # Lookups.
        c.check("get finds a definition", core.get("core_test", "alpha") is ALPHA)
        c.check("get finds a dotted id", core.get("core_test_place", "town.home.living_room") is ROOM)
        c.equal("exists: known id", core.exists("core_test", "alpha"), True)
        c.equal("exists: unknown id", core.exists("core_test", "delta"), False)
        c.raises("get: unknown id", LookupError, core.get, "core_test", "alpah")
        c.raises("get: unknown kind", LookupError, core.get, "core_tset", "alpha")
        c.raises("exists: unknown kind", LookupError, core.exists, "core_tset", "alpha")
        c.raises("all: unknown kind", LookupError, core.all, "core_tset")
        c.equal("all: creation order", core.all("core_test"), (ALPHA, BETA, GAMMA))
        c.equal("all: dotted kind", core.all("core_test_place"), (ROOM, HALL))
        c.check("all: same tuple every call", core.all("core_test") is core.all("core_test"))

        # Attributes.
        c.equal("kind and id", (ALPHA.kind, ALPHA.id), ("core_test", "alpha"))
        c.equal("template", dict(ALPHA.template), {
            "seen": False, "count": 0, "ratio": 0.5, "label": "Template Value", "pair": (1, ("a", None)) })
        c.equal("no template means empty", dict(BETA.template), { })
        c.equal("kind info", (core.kind_info("core_test_place").per_twin, core.kind_info("core_test_place").id_parts), (True, 3))

        # Frozen.
        c.raises("make a definition after init", core.FrozenError, Thing, "late")
        c.raises("register a kind after init", core.FrozenError, core.register_kind, "core_test_late", False)
        c.raises("change a template after init", TypeError, set_item, ALPHA.template, "seen", True)

        if renpy.config.developer:
            c.raises("set an attribute after init", core.FrozenError, setattr, ALPHA, "id", "changed")
            c.raises("add an attribute after init", core.FrozenError, setattr, ALPHA, "new_attr", 1)
            c.raises("delete an attribute after init", core.FrozenError, delattr, GAMMA, "extra")
        else:
            c.check("attribute checks", False, "need developer mode")

        c.equal("definition unchanged", (ALPHA.id, ALPHA.template["seen"], GAMMA.extra), ("alpha", False, 1))
        c.check("nothing made after init", not core.exists("core_test", "late"))

        # Pickling.
        c.equal("__reduce__ gives (defref, (kind, id))", ALPHA.__reduce__(), (core.defref, ("core_test", "alpha")))

        data = pickle.dumps(ALPHA, 2)
        c.check("pickle holds the kind and id", b"core_test" in data and b"alpha" in data, data)
        c.check("pickle holds no template data", b"Template Value" not in data, data)
        c.check("unpickling gives the same object", pickle.loads(data) is ALPHA)

        both = pickle.loads(pickle.dumps([ ALPHA, ROOM ], 2))
        c.check("unpickling inside a list", both[0] is ALPHA and both[1] is ROOM)
        c.check("copy and deepcopy give the same object", copy.copy(ALPHA) is ALPHA and copy.deepcopy(ALPHA) is ALPHA)
        c.check("renamed id follows RENAMES", core.defref("core_test", "old_alpha") is ALPHA)
        c.check("missing id loads as None", core.defref("core_test", "gone") is None)
        c.check("missing kind loads as None", core.defref("core_test_gone", "alpha") is None)

        return c


label test_core_registry:
    $ core_test_result = core_test.registry_checks().report()
    call screen core_test_report(core_test_result)
    return
