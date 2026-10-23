## Textbox skins and the player's textbox settings.
##
## A skin is a background for normal lines and one for thought lines (a
## Character made with show_thought=True), plus where the name and the
## dialogue sit inside it. The player picks a skin and adjusts opacity, size,
## text size and outlines in Preferences > Textbox; each setting is a
## persistent.uix_tb_* value, None meaning "the default for this device".

init offset = -400

init python in uix:

    import store

    class TextboxSkin(object):
        """
        One textbox skin. Built at init and never changed afterwards.
        """

        def __init__(self, id, name, background, thought_background, bottom, name_y, text_y):
            self.id = id
            self.name = name
            self.background = background
            self.thought_background = thought_background
            self.bottom = bottom
            self.name_y = name_y
            self.text_y = text_y

    textbox_skins = {}
    textbox_skin_list = []

    ## The skin used until the player picks one.
    TEXTBOX_DEFAULT_SKIN = "fancy"

    def add_textbox_skin(id, name, background, thought_background, bottom=0, name_y=25, text_y=85):
        """
        Adds a textbox skin (at init). `background` and `thought_background`
        are displayables or image paths. `bottom` is the gap between the
        textbox and the bottom of the screen; `name_y` and `text_y` are the
        tops of the name and the dialogue inside the textbox, in pixels.
        """

        if not renpy.is_init_phase():
            raise Exception("uix.add_textbox_skin must be called at init.")

        if id in textbox_skins:
            raise Exception("Textbox skin %r is added twice." % (id,))

        skin = TextboxSkin(id, name, background, thought_background, bottom, name_y, text_y)
        textbox_skins[id] = skin
        textbox_skin_list.append(skin)

    def textbox_skin():
        """
        The skin the player picked (or the default one).
        """

        rv = textbox_skins.get(store.persistent.uix_tb_skin, None)

        if rv is None:
            rv = textbox_skins.get(TEXTBOX_DEFAULT_SKIN, None)

        if rv is None:
            rv = textbox_skin_list[0]

        return rv

    ## Settings: key -> (default on PC and tablet, default on phone, min, max).
    TEXTBOX_SETTINGS = {
        "alpha": (20, 20, 0, 100),
        "width": (1350, 1920, 920, 1920),
        "height": (300, 360, 250, 500),
        "text_size": (30, 45, 15, 60),
        "outline_text": (2, 2, 0, 5),
        "outline_name": (4, 4, 0, 5),
        }

    def tb_default(key):
        pc, phone, lo, hi = TEXTBOX_SETTINGS[key]

        if renpy.variant("small"):
            return phone
        else:
            return pc

    def tb(key):
        """
        The current value of textbox setting `key`.
        """

        pc, phone, lo, hi = TEXTBOX_SETTINGS[key]

        value = getattr(store.persistent, "uix_tb_" + key)

        if value is None:
            value = tb_default(key)

        return max(lo, min(hi, value))

    def tb_outlines(key):
        """
        An outlines list for the "outline_text" or "outline_name" setting.
        """

        width = tb(key)

        if width:
            return [ (width, "#000", 0, 0) ]
        else:
            return [ ]

    def textbox_background(skin, thought=False):
        """
        The skin's background (or its thought background) at the player's
        opacity.
        """

        if thought:
            d = skin.thought_background
        else:
            d = skin.background

        return store.Transform(d, alpha=tb("alpha") / 100.0)

    class TextboxValue(store.BarValue, store.DictEquality):
        """
        A bar value for textbox setting `key`, for a slider in Preferences.
        """

        def __init__(self, key):
            self.key = key

        def get_adjustment(self):
            pc, phone, lo, hi = TEXTBOX_SETTINGS[self.key]

            return ui.adjustment(
                range=hi - lo,
                value=tb(self.key) - lo,
                changed=self.changed,
                step=1,
                force_step=True,
                )

        def changed(self, value):
            pc, phone, lo, hi = TEXTBOX_SETTINGS[self.key]

            setattr(store.persistent, "uix_tb_" + self.key, int(round(value)) + lo)
            renpy.restart_interaction()

        def get_style(self):
            return "slider", "vslider"

    def TextboxReset(key):
        """
        An action that puts textbox setting `key` back to its default.
        Insensitive when it already is.
        """

        return store.If(
            getattr(store.persistent, "uix_tb_" + key) is not None and tb(key) != tb_default(key),
            store.SetField(store.persistent, "uix_tb_" + key, None),
            None,
            )


default persistent.uix_tb_skin = None
default persistent.uix_tb_alpha = None
default persistent.uix_tb_width = None
default persistent.uix_tb_height = None
default persistent.uix_tb_text_size = None
default persistent.uix_tb_outline_text = None
default persistent.uix_tb_outline_name = None
