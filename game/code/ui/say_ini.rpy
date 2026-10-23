## The textbox skins the player can pick from. Backgrounds are in theme_ini.rpy.

init offset = 0

init python in uix:

    add_textbox_skin("simple", _("Simple"), tb_simple, tb_simple_thought)
    add_textbox_skin("fade", _("Side-Fade"), tb_fade, tb_fade_thought)
    add_textbox_skin("fancy", _("Fancy"), tb_fancy, tb_fancy_thought, bottom=50, name_y=35, text_y=95)
