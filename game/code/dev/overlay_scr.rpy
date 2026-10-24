## Debug overlay, shown through config.overlay_screens (so it's hidden in the
## game and main menus). F9 opens and closes it.

init offset = 0

screen dev_overlay():

    zorder 500
    style_prefix "dev"

    ## Also here so they work over modal screens.
    key "dev_overlay" action Function(dev.toggle_overlay)
    key "dev_tests" action Function(dev.open_tests)

    default tab = "time"
    default folded = False

    ## The one text box open at a time: None, "day", "screen", ("flag", key)
    ## or ("section", key); etext is its text.
    default edit = None
    default etext = ""

    ## Flag inspector: kind, its ids (worked out on picking the kind), page,
    ## picked id, twin (None = the current twin).
    default kind = None
    default ids = None
    default page = 0
    default pick = None
    default ftwin = None

    ## Section inspector: section name and twin.
    default system = None
    default stwin = None

    if dev.on() and persistent.dev_overlay_open and not main_menu:

        ## A button, so clicks on the panel don't reach the game below.
        button:
            style "dev_panel"
            action NullAction()
            keyboard_focus False
            align (1.0, 0.0)
            xsize dev.overlay_width()

            vbox:
                spacing 10

                text dev.status() style "dev_title" substitute False

                hbox:
                    box_wrap True

                    textbutton _("Time"):
                        selected (tab == "time" and not folded)
                        action [ SetScreenVariable("tab", "time"), SetScreenVariable("edit", None), SetScreenVariable("folded", False) ]

                    textbutton _("Flags"):
                        selected (tab == "flags" and not folded)
                        action [ SetScreenVariable("tab", "flags"), SetScreenVariable("edit", None), SetScreenVariable("folded", False) ]

                    textbutton _("Sections"):
                        selected (tab == "sections" and not folded)
                        action [ SetScreenVariable("tab", "sections"), SetScreenVariable("edit", None), SetScreenVariable("folded", False) ]

                    textbutton _("Profile"):
                        selected (tab == "profile" and not folded)
                        action [ SetScreenVariable("tab", "profile"), SetScreenVariable("edit", None), SetScreenVariable("folded", False) ]

                    textbutton (_("Unfold") if folded else _("Fold")):
                        action ToggleScreenVariable("folded")

                    textbutton _("Close"):
                        action Function(dev.close_overlay)

                if not folded:

                    viewport:
                        xfill True
                        yfill False
                        ymaximum dev.overlay_height()
                        mousewheel True
                        draggable True

                        vbox:
                            spacing 10

                            ## Time and twin #################################

                            if tab == "time":

                                hbox:
                                    box_wrap True
                                    textbutton _("Swap twin") action core.StateAction(core.swap)
                                    textbutton _("+1 slot") action core.StateAction(core.advance, 1)
                                    textbutton _("Sleep") action core.StateAction(core.sleep)

                                text _("Forward to the next:") style "dev_small"

                                hbox:
                                    box_wrap True
                                    for s in core.SLOTS:
                                        textbutton core.slot_name(s) action core.StateAction(core.advance, dev.slots_until(s))

                                if edit == "day":
                                    hbox:
                                        text _("Day:") yalign 0.5
                                        frame:
                                            style "dev_field"
                                            input value ScreenVariableInputValue("etext") allow "0123456789" length 6
                                        textbutton _("Go") action [ core.StateAction(dev.go_to_day, etext), SetScreenVariable("edit", None) ]
                                        textbutton _("Cancel") action SetScreenVariable("edit", None)
                                else:
                                    textbutton _("Go to day...") action [ SetScreenVariable("etext", str(core.day() + 1)), SetScreenVariable("edit", "day") ]

                            ## Flags #########################################

                            elif tab == "flags":

                                $ kind_list = core.kinds()

                                if not kind_list:
                                    text _("No kinds are registered yet.")

                                hbox:
                                    box_wrap True
                                    for k in kind_list:
                                        textbutton k:
                                            selected (kind == k)
                                            action [ SetScreenVariable("kind", k), dev.SetComputed("ids", dev.ids_of, k), SetScreenVariable("pick", None), SetScreenVariable("page", 0), SetScreenVariable("edit", None) ]

                                if kind is not None and pick is None:

                                    if not ids:
                                        text _("No definitions of this kind.")
                                    else:
                                        $ last = (len(ids) - 1) // dev.PAGE
                                        $ shown = ids[page * dev.PAGE:(page + 1) * dev.PAGE]

                                        hbox:
                                            box_wrap True
                                            for i in shown:
                                                textbutton i action [ SetScreenVariable("pick", i), SetScreenVariable("edit", None) ]

                                        if last > 0:
                                            hbox:
                                                textbutton _("Previous") action SetScreenVariable("page", page - 1) sensitive (page > 0)
                                                text ("%d / %d" % (page + 1, last + 1)) yalign 0.5
                                                textbutton _("Next") action SetScreenVariable("page", page + 1) sensitive (page < last)

                                if pick is not None:

                                    $ per_twin = core.per_twin(kind)
                                    $ tw = ftwin if per_twin else None
                                    $ rows = dev.template_items(kind, pick)

                                    hbox:
                                        textbutton _("Back") action [ SetScreenVariable("pick", None), SetScreenVariable("edit", None) ]
                                        text pick yalign 0.5 substitute False

                                    if per_twin:
                                        hbox:
                                            for t in core.TWINS:
                                                textbutton core.twin_name(t):
                                                    selected (dev.twin_or_me(ftwin) == t)
                                                    action [ SetScreenVariable("ftwin", t), SetScreenVariable("edit", None) ]

                                    if not rows:
                                        text _("No flags.")

                                    for fkey, dflt in rows:

                                        $ val = core.flag(kind, pick, fkey, tw)
                                        $ how = dev.control(val, dflt)

                                        vbox:
                                            spacing 2

                                            hbox:
                                                spacing 12
                                                text fkey substitute False
                                                text dev.show(val) substitute False color (dev.CHANGED if val != dflt else dev.SAME)

                                            hbox:
                                                box_wrap True

                                                if how == "toggle":
                                                    textbutton _("Toggle") action core.StateAction(core.set_flag, kind, pick, fkey, not val, twin=tw)
                                                elif how == "number":
                                                    for n in (-10, -1, 1, 10):
                                                        textbutton ("%+d" % n) action core.StateAction(core.set_flag, kind, pick, fkey, val + n, twin=tw)

                                                textbutton _("Edit") action [ SetScreenVariable("etext", dev.edit_text(val, dflt)), SetScreenVariable("edit", ("flag", fkey)) ]
                                                textbutton _("Reset") action core.StateAction(core.set_flag, kind, pick, fkey, dflt, twin=tw) sensitive (val != dflt)

                                            if edit == ("flag", fkey):
                                                hbox:
                                                    frame:
                                                        style "dev_field"
                                                        input value ScreenVariableInputValue("etext") length 200 copypaste True
                                                    textbutton _("OK") action [ core.StateAction(dev.set_flag_text, kind, pick, fkey, etext, tw), SetScreenVariable("edit", None) ]
                                                    textbutton _("Cancel") action SetScreenVariable("edit", None)

                            ## Sections ######################################

                            elif tab == "sections":

                                $ system_list = core.systems()

                                if not system_list:
                                    text _("No sections are registered yet.")

                                hbox:
                                    box_wrap True
                                    for s in system_list:
                                        textbutton s:
                                            selected (system == s)
                                            action [ SetScreenVariable("system", s), SetScreenVariable("edit", None) ]

                                if system is not None:

                                    $ per_twin = core.system_per_twin(system)
                                    $ tw = stwin if per_twin else None
                                    $ items = dev.section_items(system, tw)

                                    if per_twin:
                                        hbox:
                                            for t in core.TWINS:
                                                textbutton core.twin_name(t):
                                                    selected (dev.twin_or_me(stwin) == t)
                                                    action [ SetScreenVariable("stwin", t), SetScreenVariable("edit", None) ]

                                    if not items:
                                        text _("Empty section.")

                                    for skey, sval in items:

                                        vbox:
                                            spacing 2

                                            hbox:
                                                spacing 12
                                                text dev.plain(skey) substitute False
                                                textbutton _("Edit") action [ SetScreenVariable("etext", dev.literal(sval)), SetScreenVariable("edit", ("section", skey)) ]

                                            text dev.show(sval, 300) substitute False

                                            if edit == ("section", skey):
                                                hbox:
                                                    frame:
                                                        style "dev_field"
                                                        input value ScreenVariableInputValue("etext") length 2000 copypaste True
                                                    textbutton _("OK") action [ core.StateAction(dev.set_section_text, system, skey, etext, tw), SetScreenVariable("edit", None) ]
                                                    textbutton _("Cancel") action SetScreenVariable("edit", None)

                            ## Profile #######################################

                            else:

                                $ timed = dev.timed_screens()
                                $ slow_ms = int(round(dev.FRAME_TIME * 1000))

                                text _("Screen times") bold True

                                text _("Tap a screen to time it. Each time it's shown or updated, its time goes to profile_screen.txt next to log.txt (complete once Ren'Py quits). A screen that's already showing starts being timed the next time it's shown.") style "dev_small"

                                hbox:
                                    box_wrap True
                                    for sname in dev.screen_choices():
                                        textbutton sname:
                                            selected (sname in timed)
                                            action Function(dev.time_screen, sname, sname not in timed)

                                if edit == "screen":
                                    hbox:
                                        text _("Screen:") yalign 0.5
                                        frame:
                                            style "dev_field"
                                            input value ScreenVariableInputValue("etext") length 60 copypaste True
                                        textbutton _("Time it") action [ Function(dev.time_screen, etext.strip(), True), SetScreenVariable("edit", None) ]
                                        textbutton _("Cancel") action SetScreenVariable("edit", None)
                                else:
                                    textbutton _("Other screen...") action [ SetScreenVariable("etext", ""), SetScreenVariable("edit", "screen") ]

                                textbutton (_("Detail: on") if persistent.dev_profile_detail else _("Detail: off")):
                                    selected bool(persistent.dev_profile_detail)
                                    action Function(dev.set_profile_detail, not persistent.dev_profile_detail)

                                text _("Detail also logs how each statement of a timed screen was evaluated (constant, reused or new). Times aren't reliable while it's on.") style "dev_small"

                                text _("Frames") bold True

                                hbox:
                                    box_wrap True

                                    textbutton (_("Slow frames: on") if persistent.dev_profile_frames else _("Slow frames: off")):
                                        selected bool(persistent.dev_profile_frames)
                                        action Function(dev.set_frame_profiling, not persistent.dev_profile_frames)

                                    textbutton _("Frame graph") action ToggleScreen("_performance")

                                text _("Slow frames logs a step-by-step breakdown of every frame slower than [slow_ms] ms to log.txt. Frame graph (also F3) shows frame times. F8 logs the next frame once.") style "dev_small"
