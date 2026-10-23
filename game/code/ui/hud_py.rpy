## HUD: panels that systems register, shown together by `screen hud_root`.
##
## hud_root holds one draggroup. Each open panel is a window (a drag with a
## title bar) plus the slots and items its screen adds; because they share the
## draggroup, items drag from one panel to another.
##
## A panel's screen takes (panel, part):
## - part "body": what's drawn inside the window (text, buttons...).
## - part "drags": only `use uix_hud_slot(...)` and `use uix_hud_item(...)`.
##   Anything else there breaks the draggroup.
## Both parts share the same coordinates: (0, 0) is the top left of the
## window's content area.
##
## Moving an item: the player drags it onto a slot, or taps it (selects) and
## then taps a slot or another item (places). Either way ui calls the drop
## function of the panel that owns the target slot, through core.StateAction:
## drop(src_panel, src_key, dst_key). It changes the game state; the screen
## then redraws the items where the state says they are.
##
## Open panels and window positions are saved in persistent, separately for
## PC, tablet and phone. On PC and tablet windows float and can be dragged by
## the title bar; on phone they dock to the left or right half, two at most.

init offset = -400

init python in uix:

    import store

    HUD_TITLE_H = 44
    HUD_PAD = 12
    HUD_TOP = 90
    HUD_SLOT_SIZE = (96, 96)

    class HudPanelInfo(object):
        """
        One registered HUD panel. Built at init, never changed afterwards.
        """

        def __init__(self, id, screen, name, order, size, drop):
            self.id = id
            self.screen = screen
            self.name = name
            self.order = order
            self.size = size
            self.drop = drop

    hud_panels = {}
    hud_panel_list = []

    def register_hud_panel(id, screen, name, order=100, size=(600, 400), drop=None):
        """
        Adds a HUD panel (at init; systems use init 100).

        `screen` takes (panel, part), see above. `name`: the window title and
        the HUD bar button, as _("..."). `order`: lower comes first in the
        bar. `size`: the window's (width, height). `drop`: None, or a function
        drop(src_panel, src_key, dst_key) called when an item lands on one of
        this panel's slots.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.register_hud_panel must be called at init.")

        if id in hud_panels:
            raise Exception("HUD panel %r is registered twice." % (id,))

        p = HudPanelInfo(id, screen, name, order, tuple(size), drop)
        hud_panels[id] = p
        hud_panel_list.append(p)
        hud_panel_list.sort(key=lambda p: (p.order, p.id))

    ## Layouts and saved state ##############################################

    def hud_layout():
        if renpy.variant("small"):
            return "small"
        elif renpy.variant("medium"):
            return "medium"
        else:
            return "pc"

    def hud_floating():
        """
        True when windows float and drag (PC, tablet); False when they dock.
        """

        return hud_layout() != "small"

    def hud_state():
        """
        This layout's saved state, {"open": [ids], "pos": {id: pos}}. Don't
        change it in place; use set_hud_state.
        """

        saved = store.persistent.uix_hud or { }
        return saved.get(hud_layout(), None) or { "open" : [ ], "pos" : { } }

    def set_hud_state(open_ids, pos):
        saved = dict(store.persistent.uix_hud or { })
        saved[hud_layout()] = { "open" : list(open_ids), "pos" : dict(pos) }
        store.persistent.uix_hud = saved

    def hud_open_panels():
        """
        The open panels, bottom to top.
        """

        return [ hud_panels[i] for i in hud_state()["open"] if i in hud_panels ]

    def hud_is_open(id):
        return id in hud_state()["open"]

    def hud_open(id):
        st = hud_state()
        open_ids = [ i for i in st["open"] if i != id and i in hud_panels ]
        pos = dict(st["pos"])

        if not hud_floating():

            ## Docked: two at most, the new one replacing the oldest.
            if len(open_ids) >= 2:
                pos.pop(open_ids.pop(0), None)

            taken = [ pos.get(i, None) for i in open_ids ]
            pos[id] = "right" if "left" in taken else "left"

        open_ids.append(id)
        set_hud_state(open_ids, pos)

    def hud_close(id):
        st = hud_state()
        open_ids = [ i for i in st["open"] if i != id ]
        pos = dict(st["pos"])

        if not hud_floating():
            pos.pop(id, None)

        set_hud_state(open_ids, pos)

    class HudToggle(store.Action, store.DictEquality):
        """
        Opens or closes HUD panel `id`. Selected while it's open.
        """

        def __init__(self, id):
            self.id = id

        def __call__(self):

            if hud_is_open(self.id):
                hud_close(self.id)
            else:
                hud_open(self.id)

            renpy.restart_interaction()

        def get_selected(self):
            return hud_is_open(self.id)

    def hud_window_pos(p):
        """
        Where panel `p`'s window goes, (x, y).
        """

        saved = hud_state()["pos"].get(p.id, None)

        if not hud_floating():
            if saved == "right":
                return (store.config.screen_width // 2 + 10, HUD_TOP)
            else:
                return (20, HUD_TOP)

        if isinstance(saved, tuple):
            return saved

        k = hud_panel_list.index(p)
        return (120 + 50 * k, HUD_TOP + 40 * k)

    def hud_origin(panel):
        """
        The screen position of (0, 0) in `panel`'s content area.
        """

        x, y = hud_window_pos(hud_panels[panel])
        return (x + HUD_PAD, y + HUD_TITLE_H + HUD_PAD)

    ## Window dragging ####################################################

    def hud_join(drag):
        """
        drag_joined for a window: its slots and items move with it.
        """

        rv = [ (drag, 0, 0) ]

        group = drag.drag_group
        panel = drag.drag_name[1]

        if group is None or drag.x is None:
            return rv

        for c in group.children:
            name = c.drag_name

            if c is drag or c.x is None:
                continue

            if isinstance(name, tuple) and len(name) == 3 and name[1] == panel:
                rv.append((c, c.x - drag.x, c.y - drag.y))

        return rv

    def hud_window_dragged(drags, drop):
        """
        Saves where a window was dropped, and puts it on top.
        """

        d = drags[0]
        panel = d.drag_name[1]

        st = hud_state()
        pos = dict(st["pos"])
        pos[panel] = (int(d.x), int(d.y))
        open_ids = [ i for i in st["open"] if i != panel ] + [ panel ]

        set_hud_state(open_ids, pos)
        renpy.restart_interaction()

        return None

    ## Items: drag and drop, tap to select and place #######################

    ## The selected item lives in the top-level screen's scope (hud_root, or
    ## the screen that uses it), never in saved state.

    def hud_selection():
        """
        The selected item as (panel, key), or None.
        """

        cs = renpy.current_screen()

        if cs is None:
            return None

        return cs.scope.get("uix_hud_sel", None)

    def set_hud_selection(value):
        cs = renpy.current_screen()

        if cs is not None:
            cs.scope["uix_hud_sel"] = value

        renpy.restart_interaction()

    def hud_is_selected(panel, key):
        return hud_selection() == (panel, key)

    def hud_drop(src_panel, src_key, dst_panel, dst_key):
        """
        Moves item (src_panel, src_key) onto slot (dst_panel, dst_key) by
        calling the target panel's drop function through core.StateAction.
        """

        if (src_panel, src_key) == (dst_panel, dst_key):
            return None

        p = hud_panels.get(dst_panel, None)

        if p is None or p.drop is None:
            return None

        return renpy.run(store.core.StateAction(p.drop, src_panel, src_key, dst_key))

    def hud_item_dragged(drags, drop):
        """
        dragged for an item: drop it on the slot under it, or send it back.
        """

        d = drags[0]
        kind, src_panel, src_key = d.drag_name

        set_hud_selection(None)

        target = None

        if drop is not None:
            name = drop.drag_name
            if isinstance(name, tuple) and len(name) == 3 and name[0] == "uix_slot":
                target = name

        if target is None:
            d.snap(d.start_x, d.start_y, 0.2)
            return None

        ## Back to its start at once: if the drop moves the item, the redraw
        ## shows it in its new slot; if not, it's where it was.
        d.snap(d.start_x, d.start_y)

        return hud_drop(src_panel, src_key, target[1], target[2])

    def hud_clicked(drag):
        """
        clicked for slots and items: tap an item to select it, tap it again to
        deselect, tap a slot or another item to place the selected item there.
        """

        kind, panel, key = drag.drag_name
        sel = hud_selection()

        if sel is None:
            if kind == "uix_item":
                set_hud_selection((panel, key))
            return None

        set_hud_selection(None)

        if sel == (panel, key):
            return None

        return hud_drop(sel[0], sel[1], panel, key)


default persistent.uix_hud = None


init offset = 900

init python in uix:

    def validate_hud_panels():
        for p in hud_panel_list:
            if not renpy.has_screen(p.screen):
                raise Exception("HUD panel %r: there is no screen %r." % (p.id, p.screen))

    validate_hud_panels()
