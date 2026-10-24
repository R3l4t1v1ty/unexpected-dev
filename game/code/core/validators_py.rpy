# Validators: each folder that defines content registers one function that
# lists what its content is missing (labels, art...). Core never runs them:
# missing labels and art are normal while content is being written, so
# startup must not fail on them. dev/ runs them from its menu and in lint.
# (Core's own checks of Reqs, renames and signals still raise at the freeze.)

init offset = -500

init python in core:
    _constant = True

    import builtins
    import traceback

    # folder name -> function returning a list of problem strings
    VALIDATORS = { }

    def register_validator(name, fn):
        """
        Registers the validator of folder `name` (like "world"). fn() returns
        a list of problem strings, empty when all is fine. Call at init (the
        wiring band, init 100); one per folder.
        """
        if frozen:
            raise FrozenError("core: validators are registered at init; tried to register %r after init." % (name,))
        if not isinstance(name, str) or not SEGMENT_RE.fullmatch(name):
            raise ValueError("core: %r is not a valid validator name. Use the folder's name, like 'world'." % (name,))
        if name in VALIDATORS:
            raise ValueError("core: %r already has a validator; a folder registers one." % (name,))
        if not callable(fn):
            raise TypeError("core: register_validator(%r): %r can't be called." % (name, fn))

        VALIDATORS[name] = fn

    def run_validators():
        """
        Runs every validator, in registration order, and returns their
        problems as a list of (name, problem). A validator that raises, or
        returns something other than a list, gives one problem line instead
        of stopping the others.
        """
        rv = [ ]

        for name, fn in VALIDATORS.items():
            try:
                problems = fn()
            except CONTROL_EXCEPTIONS:
                raise
            except Exception as e:
                rv.append((name, "the validator raised %s%s: %s" % (type(e).__name__, raised_at(e), e)))
                continue

            if not isinstance(problems, (builtins.list, tuple)):
                rv.append((name, "the validator returned %r instead of a list of problems." % (problems,)))
                continue

            for p in problems:
                rv.append((name, str(p)))

        return rv

    def raised_at(e):
        """
        " at file:line" where exception `e` was raised, or "".
        """
        frames = traceback.extract_tb(e.__traceback__)
        if not frames:
            return ""
        return " at %s:%s" % (frames[-1].filename, frames[-1].lineno)
