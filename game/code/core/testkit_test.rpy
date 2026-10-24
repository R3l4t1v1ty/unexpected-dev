# A small test kit for core's tests (developer only; excluded from builds).
#
# A test label collects results with core_test.Checks, then shows them:
#
#     label test_core_something:
#         $ core_test_result = core_test.something_checks().report()
#         call screen core_test_report(core_test_result)
#         return
#
# Failures are also printed to the terminal.
#
# Run every core test that needs no restart: Shift+O, jump test_core_all

init offset = -1

init python in core_test:
    _constant = True

    import builtins

    def esc(s):
        """
        `s` as text that Ren'Py shows as is (with substitution off).
        """
        return str(s).replace("{", "{{")

    class Checks(builtins.object):
        """
        Collects check results as (ok, name, detail) rows.
        """

        def __init__(self, title):
            self.title = title
            self.rows = builtins.list()

        def check(self, name, ok, detail=""):
            ok = bool(ok)
            self.rows.append((ok, name, str(detail)))
            return ok

        def equal(self, name, got, expected):
            if got == expected:
                return self.check(name, True, repr(got))
            return self.check(name, False, "got %r, expected %r" % (got, expected))

        def raises(self, name, exc_type, fn, *args, **kwargs):
            """
            Passes if fn(*args, **kwargs) raises exc_type.
            """
            try:
                fn(*args, **kwargs)
            except exc_type as e:
                return self.check(name, True, "%s: %s" % (type(e).__name__, e))
            except Exception as e:
                return self.check(name, False, "raised the wrong error, %s: %s" % (type(e).__name__, e))
            return self.check(name, False, "did not raise")

        def no_raise(self, name, fn, *args, **kwargs):
            """
            Passes if fn(*args, **kwargs) doesn't raise.
            """
            try:
                fn(*args, **kwargs)
            except Exception as e:
                return self.check(name, False, "%s: %s" % (type(e).__name__, e))
            return self.check(name, True)

        def extend(self, other, prefix=None):
            """
            Adds the rows of another Checks, e.g. checks run at init, with
            `prefix` (default: its title) before their names.
            """
            if prefix is None:
                prefix = other.title
            for ok, name, detail in other.rows:
                self.rows.append((ok, prefix + ": " + name, detail))

        def report(self):
            """
            Prints the failures and returns (title, summary, lines) for the
            core_test_report screen. Failures come first.
            """
            failed = [ r for r in self.rows if not r[0] ]
            summary = "%d checks, %d failed" % (len(self.rows), len(failed))

            print("%s: %s" % (self.title, summary))
            for r in failed:
                print("  FAIL %s: %s" % (r[1], r[2]))

            lines = [ ]
            for ok, name, detail in sorted(self.rows, key=lambda r: r[0]):
                text = ("PASS  " if ok else "FAIL  ") + name
                if detail:
                    text += "  :  " + detail
                lines.append((ok, esc(text)))

            return (esc(self.title), summary, tuple(lines))


init offset = 0

screen core_test_report(result):
    modal True
    zorder 200

    add Solid("#000000e0")

    frame:
        margin (40, 40)
        padding (24, 24)
        xfill True
        yfill True

        vbox:
            spacing 12

            text result[0] size 32 substitute False

            hbox:
                spacing 40
                text result[1] substitute False
                textbutton _("Close") action Return()

            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"

                vbox:
                    spacing 4
                    for ok, line in result[2]:
                        text line size 22 substitute False color ("#80e080" if ok else "#ff7070")

    key "game_menu" action Return()


init python in core_test:

    def all_checks():
        """
        Every core test that needs no restart (not state_test.rpy).
        """
        c = Checks("core: all tests but state")
        for prefix, fn in (
                ("registry", registry_checks),
                ("signals", signals_checks),
                ("twins", twins_checks),
                ("time", time_checks),
                ("req", req_checks),
                ("saves", saves_checks),
                ("helpers", helpers_checks),
                ("start", start_checks),
                ("validators", validators_checks),
                ("lookups", lookups_checks),
                ("snapshot", snapshot_checks),
                ):
            c.extend(fn(), prefix)
        return c


label test_core_all:
    $ core_test_result = core_test.all_checks().report()
    call screen core_test_report(core_test_result)
    return
