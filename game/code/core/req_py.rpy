# Req: conditions on the game state, like "evening, from day 3".
#
#     requires = ReqAll(ReqSlot(core.EVENING), ReqDay(min=3))
#     if requires.check():
#         ...
#
# check(twin=None) is True if the condition holds for `twin` (default: the
# twin being played). It never changes anything.
#
# describe() is the text players see, translated: given with text=_("..."),
# or made up from the condition (ReqSlot, ReqDay, ReqTwin, and ReqAll/ReqAny
# of those), or None when there's nothing to show (e.g. a ReqFlag without
# text).
#
# A Req doesn't change once made. When init ends, core validates the Reqs held
# by definitions (in an attribute, or in a tuple, list or dict attribute), so a
# misspelled kind, id or flag fails at startup. Other folders add Req
# subclasses: they override check(), and maybe default_text(), validate() and
# __repr__().

init offset = -500

init python in core:
    _constant = True

    import builtins
    import types

    import store
    from store import _

    REQ_OR = _("[a] or [b]")
    REQ_AND = _("[a] · [b]")

    def req_tuple(owner, reqs):
        """
        `reqs` as a tuple. Raises TypeError if one isn't a Req.
        """
        for r in reqs:
            if not isinstance(r, store.Req):
                raise TypeError("core: %s takes Reqs, not %r." % (owner, r))
        return tuple(reqs)

    def join_texts(texts, pattern):
        """
        Joins texts two at a time with `pattern` (REQ_OR or REQ_AND).
        """
        rv = texts[0]
        for t in texts[1:]:
            rv = renpy.substitute(pattern, { "a": rv, "b": t })
        return rv

    def req_problems_of(obj, where):
        """
        Problems found by validate() in the Reqs held by `obj`'s attributes,
        directly or in a tuple, list or dict.
        """
        rv = [ ]

        for name, value in vars(obj).items():
            if isinstance(value, store.Req):
                reqs = [ value ]
            elif isinstance(value, (tuple, builtins.list)):
                reqs = [ i for i in value if isinstance(i, store.Req) ]
            elif isinstance(value, (builtins.dict, types.MappingProxyType)):
                reqs = [ i for i in value.values() if isinstance(i, store.Req) ]
            else:
                continue

            for r in reqs:
                for p in r.validate():
                    rv.append("  %s.%s: %s" % (where, name, p))

        return rv

    def check_reqs():
        """
        Validates the Reqs held by all definitions. Called by freeze().
        """
        problems = [ ]
        for ids in REGISTRY.values():
            for defn in ids.values():
                problems.extend(req_problems_of(defn, repr(defn)))

        if problems:
            raise LookupError("core: some Reqs in definitions refer to things that don't exist:\n" + "\n".join(problems))


init python:

    class Req(NoRollback):
        """
        Base class of conditions. `text`: what describe() returns, usually
        _("...").
        """

        def __init__(self, text=None):
            self.text = text

        def check(self, twin=None):
            """
            True if the condition holds for `twin` (default: the twin being
            played).
            """
            raise NotImplementedError("%s doesn't define check()." % type(self).__name__)

        def describe(self):
            """
            The text players see, translated, or None.
            """
            if self.text is not None:
                return renpy.substitute(self.text)
            return self.default_text()

        def default_text(self):
            """
            describe() when no text was given.
            """
            return None

        def validate(self):
            """
            A list of problems, like references to things that don't exist.
            """
            return [ ]

        def __repr__(self):
            return "%s()" % type(self).__name__

    class ReqAll(Req):
        """
        True if all of `reqs` are (or if there are none).
        """

        def __init__(self, *reqs, text=None):
            super().__init__(text)
            self.reqs = core.req_tuple("ReqAll", reqs)

        def check(self, twin=None):
            for r in self.reqs:
                if not r.check(twin):
                    return False
            return True

        def default_text(self):
            texts = [ t for t in (r.describe() for r in self.reqs) if t ]
            if not texts:
                return None
            return core.join_texts(texts, core.REQ_AND)

        def validate(self):
            return [ p for r in self.reqs for p in r.validate() ]

        def __repr__(self):
            return "ReqAll(%s)" % ", ".join(repr(r) for r in self.reqs)

    class ReqAny(Req):
        """
        True if any of `reqs` is (False if there are none).
        """

        def __init__(self, *reqs, text=None):
            super().__init__(text)
            self.reqs = core.req_tuple("ReqAny", reqs)

        def check(self, twin=None):
            for r in self.reqs:
                if r.check(twin):
                    return True
            return False

        def default_text(self):
            texts = [ r.describe() for r in self.reqs ]
            if not texts or not all(texts):
                return None
            return core.join_texts(texts, core.REQ_OR)

        def validate(self):
            return [ p for r in self.reqs for p in r.validate() ]

        def __repr__(self):
            return "ReqAny(%s)" % ", ".join(repr(r) for r in self.reqs)

    class ReqNot(Req):
        """
        True if `req` isn't.
        """

        def __init__(self, req, text=None):
            super().__init__(text)
            self.req = core.req_tuple("ReqNot", (req,))[0]

        def check(self, twin=None):
            return not self.req.check(twin)

        def validate(self):
            return self.req.validate()

        def __repr__(self):
            return "ReqNot(%r)" % (self.req,)

    class ReqFlag(Req):
        """
        True if flag `key` of definition (kind, id) equals `value`.
        """

        def __init__(self, kind, id, key, value=True, text=None):
            super().__init__(text)

            if not core.is_plain(value):
                raise ValueError("core: ReqFlag(%r, %r, %r): value %r isn't a flag value." % (kind, id, key, value))

            self.kind = kind
            self.id = id
            self.key = key
            self.value = value

        def check(self, twin=None):
            return core.flag(self.kind, self.id, self.key, twin) == self.value

        def validate(self):
            try:
                core.template_default(core.get(self.kind, self.id), self.key)
            except LookupError as e:
                return [ str(e) ]
            return [ ]

        def __repr__(self):
            return "ReqFlag(%r, %r, %r, %r)" % (self.kind, self.id, self.key, self.value)

    class ReqSlot(Req):
        """
        True in any of `slots` (core.MORNING...).
        """

        def __init__(self, *slots, text=None):
            super().__init__(text)

            if not slots:
                raise ValueError("core: ReqSlot needs at least one slot.")
            for i in slots:
                core.slot_name(i) # raises ValueError if it isn't a slot

            self.slots = tuple(slots)

        def check(self, twin=None):
            return core.slot(twin) in self.slots

        def default_text(self):
            return core.join_texts([ core.slot_name(i) for i in self.slots ], core.REQ_OR)

        def __repr__(self):
            return "ReqSlot(%s)" % ", ".join(repr(i) for i in self.slots)

    class ReqDay(Req):
        """
        True from day `min` to day `max`, both included. Either may be None.
        """

        def __init__(self, min=None, max=None, text=None):
            super().__init__(text)

            for name, value in (("min", min), ("max", max)):
                if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                    raise ValueError("core: ReqDay: %s must be a day (a whole number from 1 up) or None, not %r." % (name, value))
            if min is None and max is None:
                raise ValueError("core: ReqDay needs min, max or both.")
            if min is not None and max is not None and min > max:
                raise ValueError("core: ReqDay: min (%r) is after max (%r)." % (min, max))

            self.min = min
            self.max = max

        def check(self, twin=None):
            day = core.day(twin)
            if self.min is not None and day < self.min:
                return False
            if self.max is not None and day > self.max:
                return False
            return True

        def default_text(self):
            scope = { "first": self.min, "last": self.max }
            if self.max is None:
                return renpy.substitute(_("From day [first]"), scope)
            if self.min is None:
                return renpy.substitute(_("Until day [last]"), scope)
            if self.min == self.max:
                return renpy.substitute(_("Day [first]"), scope)
            return renpy.substitute(_("Days [first] to [last]"), scope)

        def __repr__(self):
            return "ReqDay(min=%r, max=%r)" % (self.min, self.max)

    class ReqTwin(Req):
        """
        True when checked for `twin`.
        """

        def __init__(self, twin, text=None):
            super().__init__(text)

            if twin not in core.TWINS:
                raise ValueError("core: ReqTwin: unknown twin %r. The twins are %s." % (twin, ", ".join(core.TWINS)))

            self.twin = twin

        def check(self, twin=None):
            return core.resolve_twin(twin) == self.twin

        def default_text(self):
            return renpy.substitute(_("Only as [name]"), { "name": core.twin_name(self.twin) })

        def __repr__(self):
            return "ReqTwin(%r)" % (self.twin,)
