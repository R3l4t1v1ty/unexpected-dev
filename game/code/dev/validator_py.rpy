## Content check: every folder's validator (core.run_validators) plus dev/'s
## own image-name check. Shown from the test menu (dev_report) and
## printed in lint (config.lint_hooks, which run after init, so every
## definition exists). Never run at init. Developer mode only.
##
## Planted mistakes (persistent.dev_plant, toggled in the test menu) add a
## missing label, a missing image and two clashing image files, to check that
## the report shows them.

init offset = -300

init python in dev:
    _constant = True

    import os

    import store
    from store import core, uix, renpy

    ## Never counted in the image-name check: OS junk files.
    JUNK_FILES = ("thumbs.db", "desktop.ini")

    ## Planted mistakes: a definition id with no label and no image, and two
    ## files that get the same image name. The files don't exist; they're
    ## added to the list of files the check reads.
    PLANTED_LABEL = ("dev_planted", "ghost", "chat")
    PLANTED_ASSET = ("dev_planted", "ghost", "bg_0.webp")
    PLANTED_FILES = ("images/dev_planted/a/dev_planted_clash.png", "images/dev_planted/b/Dev_Planted_Clash@2.webp")

    def image_name(path):
        """
        The image name Ren'Py's image scan gives a file: the basename,
        lowercased, extension dropped, and everything from @ on dropped
        (bg@2.png is bg). Folders don't count.
        """

        base = os.path.splitext(os.path.basename(path))[0]
        return base.partition("@")[0].lower()

    def image_clashes(files):
        """A problem line for each image name that two or more files under images/ get."""

        prefix = (store.config.images_directory or "images").rstrip("/") + "/"
        by_name = { }

        for fn in files:
            if not fn.startswith(prefix):
                continue

            base = os.path.basename(fn)

            if base.startswith(".") or base.lower() in JUNK_FILES:
                continue

            by_name.setdefault(image_name(fn), [ ]).append(fn)

        rv = [ ]

        for name in sorted(by_name):
            paths = sorted(by_name[name])

            if len(paths) > 1:
                rv.append("image name '%s' is used by %d files: %s" % (name, len(paths), ", ".join(paths)))

        return rv

    def validate():
        """[(source, problem), ...]: every folder's validator, then the image names."""

        rv = list(core.run_validators())

        files = list(renpy.list_files())

        if store.persistent.dev_plant:
            files.extend(PLANTED_FILES)

        rv.extend(("images", p) for p in image_clashes(files))

        return rv

    def own_problems():
        """dev/'s own validator. Only the planted mistakes, for now."""

        if not store.persistent.dev_plant:
            return [ ]

        rv = [ ]

        label = core.label_for(*PLANTED_LABEL)

        if not renpy.has_label(label):
            rv.append("missing label %s (planted)" % label)

        path = core.asset(*PLANTED_ASSET)

        if not renpy.loadable(path):
            rv.append("missing image %s (planted)" % path)

        return rv

    def set_plant(value):
        store.persistent.dev_plant = bool(value)

        ## Lint runs in its own process and reads persistent from disk.
        renpy.save_persistent()
        renpy.restart_interaction()

    def show_report():
        renpy.show_screen("dev_report", problems=validate())
        renpy.restart_interaction()

    def lint():
        if not on():
            return

        problems = validate()

        print("")
        print("Content check (dev/): %d problem%s." % (len(problems), "" if len(problems) == 1 else "s"))

        for source, problem in problems:
            print("  %s: %s" % (source, problem))

    ## Used by test_dev_validator: what each planted mistake leaves in the report.
    PLANT_MARKS = (
        ("missing label", "dev_planted__ghost__chat"),
        ("missing image", "dev_planted__ghost__bg_0.webp"),
        ("clashing image files", "'dev_planted_clash'"),
        )

    def planted_check():
        old = store.persistent.dev_plant
        store.persistent.dev_plant = True

        try:
            lines = [ "%s: %s" % (source, problem) for source, problem in validate() ]
        finally:
            store.persistent.dev_plant = old

        report = "\n".join(lines)
        missing = [ what for what, mark in PLANT_MARKS if mark not in report ]

        if not missing:
            return "Passed: the report has the planted missing label, missing image and clashing image files."

        note = "FAILED: the report doesn't have the planted %s." % ", ".join(missing)

        ## If dev/'s validator raised, core turned that into a "dev:" line.
        own = [ line for line in lines if line.startswith("dev: ") ]

        if own:
            note += " dev/'s report lines: " + " | ".join(own)

        return note


init offset = 100

init python in dev:

    core.register_validator("dev", own_problems)

    store.config.lint_hooks.append(lint)
