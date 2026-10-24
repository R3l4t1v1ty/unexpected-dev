## Fixture saves: game states kept as plain data (core.snapshot()) in
## dev/fixtures/<name>.txt, each with the result core.migrate gave when it was
## last accepted. Check runs every fixture through core.migrate and lists what
## differs from that expected result, so a new migration shows exactly what it
## does to old saves; accept the result once it's right.
##
## A fixture file is a Python literal {"recorded", "accepted", "data",
## "expected"}, written by the test menu (Record, Accept). Developer mode only;
## dev/ is never shipped, so the files are read and written straight from
## game/code/dev/fixtures/.

init offset = -300

init python in dev:
    _constant = True

    import ast
    import builtins
    import datetime
    import io
    import os
    import re

    import store
    from store import core, renpy

    ## The fixture folder, under the game directory.
    FIXTURE_DIR = ("code", "dev", "fixtures")

    FIXTURE_HEADER = (
        "## dev/ fixture save. data: core.snapshot() of a game; expected: what\n"
        "## core.migrate(data) gave when it was last accepted. Written by the test\n"
        "## menu (Fixture saves); don't edit by hand.\n"
        )

    ## Most differences listed per fixture.
    DIFF_LIMIT = 40

    ## The made-up section the migration test adds, to check unknown sections are kept.
    MARK = "dev_fixture"

    ## Files #####################################################################

    def fixture_path(name=None):
        parts = (store.config.gamedir,) + FIXTURE_DIR

        if name is not None:
            parts += (name + ".txt",)

        return os.path.join(*parts)

    def fixture_names():
        """Sorted names of the fixture files. Reads the folder, so not for screens."""

        try:
            files = os.listdir(fixture_path())
        except OSError:
            return ()

        return builtins.tuple(sorted(f[:-4] for f in files if f.endswith(".txt") and not f.startswith(".")))

    def load_fixture(name):
        with io.open(fixture_path(name), "r", encoding="utf-8") as f:
            fixture = ast.literal_eval(f.read())

        if not isinstance(fixture, builtins.dict) or "data" not in fixture:
            raise ValueError("not a fixture: needs a dict with \"data\"")

        return fixture

    def write_fixture(name, fixture):
        text = FIXTURE_HEADER + pretty(fixture) + "\n"

        if ast.literal_eval(text) != fixture:
            raise ValueError("this state doesn't read back the same from a Python literal")

        if not os.path.isdir(fixture_path()):
            os.makedirs(fixture_path())

        with io.open(fixture_path(name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def today():
        return datetime.date.today().isoformat()

    ## Plain data ################################################################

    def pretty(value, depth=0):
        """value as a Python literal, one dict entry or list item per line, keys sorted."""

        pad = "    " * (depth + 1)
        end = "    " * depth

        if isinstance(value, builtins.dict) and value:
            items = sorted(value.items(), key=lambda kv: literal(kv[0]))
            return "{\n" + "".join("%s%s: %s,\n" % (pad, literal(k), pretty(v, depth + 1)) for k, v in items) + end + "}"

        if isinstance(value, builtins.list) and value:
            return "[\n" + "".join("%s%s,\n" % (pad, pretty(v, depth + 1)) for v in value) + end + "]"

        return literal(value)

    def brief(value, limit=100):
        """value as a literal, cut with ... past limit. Raw text: escape it for screens."""

        s = literal(value)

        if len(s) > limit:
            s = s[:limit - 3] + "..."

        return s

    def error_text(e):
        return "%s: %s" % (builtins.type(e).__name__, e)

    def path_join(path, key):
        if isinstance(key, str) and re.match(r"\w+\Z", key):
            return (path + "." + key) if path else key

        return "%s[%s]" % (path, literal(key))

    SCALARS = (bool, int, float, str)

    def kind_of(value):
        """value's plain-data type name. bool and int differ, unlike with ==."""

        if value is None:
            return "None"

        for t in SCALARS + (builtins.tuple, builtins.list, builtins.dict, builtins.set):
            if isinstance(value, t):
                return t.__name__

        return builtins.type(value).__name__

    def diff(old, new, path="", out=None):
        """Lines saying where new differs from old, at most DIFF_LIMIT."""

        if out is None:
            out = [ ]

        if len(out) >= DIFF_LIMIT:
            return out

        if isinstance(old, builtins.dict) and isinstance(new, builtins.dict):
            for k in sorted(builtins.set(old) | builtins.set(new), key=literal):
                if len(out) >= DIFF_LIMIT:
                    break

                p = path_join(path, k)

                if k not in new:
                    out.append("%s: removed (was %s)" % (p, brief(old[k])))
                elif k not in old:
                    out.append("%s: added %s" % (p, brief(new[k])))
                else:
                    diff(old[k], new[k], p, out)

        elif isinstance(old, builtins.list) and isinstance(new, builtins.list) and len(old) == len(new):
            for i, (a, b) in enumerate(zip(old, new)):
                diff(a, b, "%s[%d]" % (path, i), out)

        elif kind_of(old) != kind_of(new) or old != new:
            out.append("%s: %s -> %s" % (path or "(all)", brief(old), brief(new)))

        return out

    def plain_problems(value, path="", out=None):
        """A line for each place value holds something other than plain data."""

        if out is None:
            out = [ ]

        if value is None or isinstance(value, SCALARS):
            return out

        if isinstance(value, (builtins.tuple, builtins.list, builtins.set)):
            for i, v in enumerate(value):
                plain_problems(v, "%s[%d]" % (path, i), out)

        elif isinstance(value, builtins.dict):
            for k, v in value.items():
                if not (k is None or isinstance(k, SCALARS + (builtins.tuple,))):
                    out.append("%s: key %s isn't plain data" % (path or "(all)", brief(k)))

                plain_problems(v, path_join(path, k), out)

        else:
            out.append("%s: %s isn't plain data" % (path or "(all)", builtins.type(value).__name__))

        return out

    ## Shape #####################################################################

    def shape_problems(data):
        """What's wrong with data's shape, against what core.snapshot() makes."""

        if not isinstance(data, builtins.dict):
            return [ "it isn't a dict" ]

        out = [ "no %r" % k for k in ("version", "twin", "shared", "twins") if k not in data ]

        if out:
            return out

        if isinstance(data["version"], bool) or not isinstance(data["version"], int):
            out.append("version isn't a number")

        if data["twin"] not in core.TWINS:
            out.append("twin %s isn't in core.TWINS" % brief(data["twin"]))

        parts = [ ("shared", data["shared"], ("flags", "sys")) ]
        twins = data["twins"]

        if not isinstance(twins, builtins.dict) or builtins.set(twins) != builtins.set(core.TWINS):
            out.append("twins should have exactly %s" % brief(builtins.tuple(core.TWINS)))
        else:
            parts.extend(("twins." + t, twins[t], ("day", "slot", "flags", "sys")) for t in core.TWINS)

        for where, part, keys in parts:
            if not isinstance(part, builtins.dict):
                out.append("%s isn't a dict" % where)
                continue

            out.extend("%s has no %r" % (where, k) for k in keys if k not in part)

            if not isinstance(part.get("sys"), builtins.dict):
                out.append("%s.sys isn't a dict" % where)

        return out

    def sys_dicts(data, system):
        """((where, the sys dict that should hold system), ...): one per twin or the shared one."""

        if core.system_per_twin(system):
            return builtins.tuple(("twins.%s.sys" % t, data["twins"][t]["sys"]) for t in core.TWINS)

        return (("shared.sys", data["shared"]["sys"]),)

    def section_problems(data):
        """A line for each registered section data lacks."""

        out = [ ]

        for system in core.systems():
            for where, secs in sys_dicts(data, system):
                if system not in secs:
                    out.append("%s has no section %s" % (where, system))

        return out

    def result_problems(result, version):
        """What's wrong with core.migrate's result, which should be at `version`."""

        out = shape_problems(result)

        if out:
            return out

        out = plain_problems(result)

        if result["version"] != version:
            out.append("version is %s, should be %d" % (brief(result["version"]), version))

        out.extend(section_problems(result))
        return out

    ## Check, record, accept #####################################################

    def check_fixture(name):
        """
        (name, version, problems, differences, can_accept) for one fixture.
        Problems need a fix in code; differences from the expected result can
        be accepted once they're right.
        """

        try:
            fixture = load_fixture(name)
        except Exception as e:
            return (name, None, ("can't read the file: %s" % error_text(e),), (), False)

        data = fixture["data"]
        version = data.get("version") if isinstance(data, builtins.dict) else None
        problems = [ "fixture: " + p for p in shape_problems(data) ]

        if not problems and data["version"] > core.SAVE_VERSION:
            problems.append("it's from save version %d, newer than this game's %d" % (data["version"], core.SAVE_VERSION))

        if problems:
            return (name, version, builtins.tuple(problems), (), False)

        try:
            result = core.migrate(data)
        except Exception as e:
            return (name, version, ("core.migrate raised %s" % error_text(e),), (), False)

        problems = result_problems(result, core.SAVE_VERSION)

        if fixture.get("expected") is None:
            differences = [ "no expected result yet" ]
        else:
            differences = diff(fixture["expected"], result)

            if len(differences) >= DIFF_LIMIT:
                differences.append("(only the first %d differences are shown)" % DIFF_LIMIT)

        return (name, version, builtins.tuple(problems), builtins.tuple(differences), not problems and bool(differences))

    def show_fixture_report():
        results = builtins.tuple(check_fixture(n) for n in fixture_names())
        renpy.show_screen("dev_fixture_report", results=results)
        renpy.restart_interaction()

    def accept_fixture(name):
        """Makes what core.migrate gives now the fixture's expected result."""

        try:
            fixture = load_fixture(name)
            result = core.migrate(fixture["data"])
            problems = result_problems(result, core.SAVE_VERSION)

            if problems:
                notify("Not accepted: %s" % problems[0])
                return

            fixture["expected"] = result
            fixture["accepted"] = today()
            write_fixture(name, fixture)
        except Exception as e:
            notify("Not accepted: %s" % error_text(e))
            return

        show_fixture_report()

    def default_fixture_name():
        return "v%d_day%d_%s" % (core.SAVE_VERSION, core.day(), core.me())

    def record_fixture(name):
        """Saves this game's state as fixture `name`, with today's result as expected."""

        name = name.strip()

        if not re.match(r"[a-z0-9_]+\Z", name):
            notify("A fixture name uses only a-z, 0-9 and _.")
            return

        if os.path.exists(fixture_path(name)):
            notify("There's a fixture named %s already." % name)
            return

        data = core.snapshot()
        problems = shape_problems(data) + plain_problems(data)

        if problems:
            notify("Not recorded: %s" % problems[0])
            return

        try:
            fixture = { "recorded": today(), "accepted": today(), "data": data, "expected": core.migrate(data) }
            write_fixture(name, fixture)
        except Exception as e:
            notify("Not recorded: %s" % error_text(e))
            return

        renpy.hide_screen("dev_fixture_record")
        notify("Recorded fixture %s (save version %d)." % (name, data["version"]))
        renpy.restart_interaction()

    ## Tests #####################################################################

    def fixtures_note():
        """test_dev_fixtures: every fixture matches its expected result."""

        results = [ check_fixture(n) for n in fixture_names() ]

        if not results:
            return "No fixtures to check. Record one in a game: Tests > Fixture saves > Record this game."

        bad = [ ]

        for name, version, problems, differences, can_accept in results:
            if problems:
                bad.append("%s: %s" % (name, problems[0]))
            elif differences:
                bad.append("%s: %d difference%s, first %s" % (name, len(differences), "" if len(differences) == 1 else "s", differences[0]))

        if not bad:
            if len(results) == 1:
                return "Passed: the fixture matches its expected result."

            return "Passed: all %d fixtures match their expected results." % len(results)

        return "FAILED: " + "; ".join(bad) + ". Details: Tests > Fixture saves > Check."

    def migration_problems(name):
        """
        Runs fixture `name` through core.migrate with only a test migration,
        one version up, and no renames. The test migration changes nothing,
        so the result should be the fixture at the new version, plus what a
        load adds (missing sections and section keys), with the made-up
        section MARK kept as it was.
        """

        data = core.copy_plain(load_fixture(name)["data"])
        problems = shape_problems(data)

        if problems:
            return [ "fixture: " + p for p in problems ], None, None

        version = data["version"]

        data["shared"]["sys"][MARK] = { "mark": "shared" }

        for t in core.TWINS:
            data["twins"][t]["sys"][MARK] = { "mark": t }

        target = version + 1
        calls = [ ]

        def test_migration(*args):
            calls.append(builtins.type(args[0]).__name__ if args else "nothing")

        try:
            result = core.migrate(data, migrations={ target: test_migration }, renames={ })
        except Exception as e:
            return [ "core.migrate raised %s" % error_text(e) ], None, version

        if len(calls) != 1:
            return [ "the test migration ran %d times, not once" % len(calls) ], None, version

        problems = result_problems(result, target)

        if problems:
            return problems, calls[0], version

        expected = core.copy_plain(data)
        expected["version"] = target

        for system in core.systems():
            for (wexp, exp), (wres, res) in zip(sys_dicts(expected, system), sys_dicts(result, system)):
                if system not in exp:
                    exp[system] = core.copy_plain(res[system])
                elif isinstance(exp[system], builtins.dict) and isinstance(res[system], builtins.dict):
                    for key in res[system]:
                        if key not in exp[system]:
                            exp[system][key] = core.copy_plain(res[system][key])

        return diff(expected, result), calls[0], version

    def migration_note():
        """test_dev_fixture_migration: fixtures go through a test migration unharmed."""

        names = fixture_names()

        if not names:
            return "FAILED: no fixtures. Record one in a game: Tests > Fixture saves > Record this game."

        bad = [ ]
        got = None
        versions = [ ]

        for name in names:
            try:
                problems, received, version = migration_problems(name)
            except Exception as e:
                problems, received, version = [ error_text(e) ], None, None

            got = got or received

            if version is not None:
                versions.append(version)

            if problems:
                bad.append("%s: %s" % (name, problems[0]))

        if bad:
            return "FAILED: " + "; ".join(bad)

        return "Passed: %d fixture%s (save version %s) went through a test migration one version up; the migration got a %s, unknown sections were kept, nothing else changed." % (
            len(names), "" if len(names) == 1 else "s", ", ".join(builtins.str(v) for v in sorted(builtins.set(versions))), got)
