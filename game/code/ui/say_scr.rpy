## The say screen (dialogue), the input screen, and a textbox preview for
## Preferences. All three follow the player's textbox skin and settings.

init offset = 0

## `thought` is True for a Character made with show_thought=True. Other show_*
## arguments a Character passes land in kwargs.
screen say(who, what, thought=False, **kwargs):

    $ skin = uix.textbox_skin()
    $ width = uix.tb("width")

    window:
        id "window"
        xsize width
        ysize uix.tb("height")
        yoffset -skin.bottom
        background uix.textbox_background(skin, thought)

        if who is not None:

            window:
                id "namebox"
                style "namebox"
                xpos (width - int(width * 0.75)) // 2
                ypos skin.name_y

                text who id "who":
                    outlines uix.tb_outlines("outline_name")

        text what id "what":
            ypos skin.text_y
            xsize int(width * 0.75)
            size uix.tb("text_size")
            outlines uix.tb_outlines("outline_text")

    ## Side images don't fit on phones.
    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0


## Lets a Character style its namebox with namebox_* arguments.
init python:
    config.character_id_prefixes.append('namebox')


style window is default
style say_label is default
style say_dialogue is default
style say_thought is say_dialogue

style namebox is default
style namebox_label is say_label

## The say screen sets the size and background of the textbox.
style window:
    xalign 0.5
    yalign gui.textbox_yalign
    background None

style namebox:
    background None
    padding (0, 0, 0, 0)

style say_label:
    properties gui.text_properties("name", accent=True)

style say_dialogue:
    properties gui.text_properties("dialogue")
    xalign 0.5
    adjust_spacing False


## Input screen: shows renpy.input. Must have an input with id "input".
screen input(prompt):

    style_prefix "input"

    $ skin = uix.textbox_skin()
    $ width = uix.tb("width")

    window:
        xsize width
        ysize uix.tb("height")
        yoffset -skin.bottom
        background uix.textbox_background(skin)

        vbox:
            xalign 0.5
            xsize int(width * 0.75)
            ypos skin.name_y
            spacing 15

            text prompt style "input_prompt"
            input id "input"

style input_prompt is default

style input_prompt:
    properties gui.text_properties("input_prompt")

style input:
    xmaximum 1400


## A textbox as the say screen would draw it, for Preferences > Textbox.
screen uix_textbox_preview(thought=False):

    $ skin = uix.textbox_skin()
    $ width = uix.tb("width")
    $ height = uix.tb("height")

    fixed:
        xysize (width, height)

        add uix.textbox_background(skin, thought)

        text _("Name"):
            style "say_label"
            xpos (width - int(width * 0.75)) // 2
            ypos skin.name_y
            outlines uix.tb_outlines("outline_name")

        text _("This is how dialogue will look. Drag the sliders to change the textbox."):
            style "say_dialogue"
            ypos skin.text_y
            xsize int(width * 0.75)
            size uix.tb("text_size")
            outlines uix.tb_outlines("outline_text")
