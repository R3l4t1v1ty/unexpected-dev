## Shared helpers for dev/'s tools. Developer mode only; dev/ is excluded from
## builds.

init offset = -300

init python in dev:
    _constant = True

    import builtins

    import store
    from store import core, uix, renpy

    def on():
        """True while developer mode is on. Every dev/ tool checks it."""

        return bool(store.config.developer)

    def plain(s):
        """s as text that shows exactly as written (use with substitute False)."""

        return builtins.str(s).replace("{", "{{")

    def notify(message):
        """A toast that shows message exactly as written."""

        uix.notify(builtins.str(message).replace("{", "{{").replace("[", "[["))

    def literal(value):
        """value written as a Python literal, so ast.literal_eval reads it back."""

        if isinstance(value, builtins.dict):
            return "{" + ", ".join("%s: %s" % (literal(k), literal(v)) for k, v in value.items()) + "}"

        if isinstance(value, builtins.list):
            return "[" + ", ".join(literal(v) for v in value) + "]"

        if isinstance(value, builtins.tuple):
            inner = ", ".join(literal(v) for v in value)
            return "(" + inner + ("," if len(value) == 1 else "") + ")"

        if isinstance(value, (builtins.set, builtins.frozenset)):
            if not value:
                return "set()"
            return "{" + ", ".join(sorted(literal(v) for v in value)) + "}"

        return repr(value)

    def show(value, limit=120):
        """value as short display text: a literal, cut with ... past limit."""

        s = literal(value)

        if len(s) > limit:
            s = s[:limit - 3] + "..."

        return plain(s)

    class SetComputed(store.Action, store.FieldEquality):
        """
        Like SetScreenVariable, but the value is fn(*args), worked out when the
        button is pressed instead of every time the screen is drawn. For
        lookups screens mustn't make, like core.all(kind).
        """

        identity_fields = [ "fn" ]
        equality_fields = [ "name", "args" ]

        def __init__(self, name, fn, *args):
            self.name = name
            self.fn = fn
            self.args = args

        def __call__(self):
            cs = renpy.current_screen()

            if cs is None:
                return

            cs.scope[self.name] = self.fn(*self.args)
            renpy.restart_interaction()
