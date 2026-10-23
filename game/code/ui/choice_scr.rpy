## Choice screen: the choices of a menu statement.
##
## A choice may carry a requirement: "Lift the beam" (req=ReqStat("str", 12)):
## When req.check() fails, the choice is shown greyed out, can't be picked, and
## has req.describe() beside it. To hide a choice instead, use `if`.

init offset = 0

screen choice(items):

    style_prefix "choice"

    $ locked_count = 0

    vbox:
        for i in items:

            $ req = i.kwargs.get("req", None)

            if req is None or req.check():

                textbutton i.caption action i.action

            else:

                $ locked_count += 1
                $ why = req.describe()

                button:
                    action i.action
                    sensitive False

                    hbox:
                        xalign 0.5
                        spacing 20

                        text i.caption style "choice_button_text"

                        if why:
                            text "([why!q])" style "uix_choice_req_text"

        ## Developer aid: a menu whose every choice is locked can't be left.
        if config.developer and items and locked_count == len(items):
            text "Every choice in this menu is locked." style "uix_choice_dev_text"


style choice_vbox is vbox
style choice_button is button
style choice_button_text is button_text

style choice_vbox:
    xalign 0.5
    ypos 405
    yanchor 0.5

    spacing gui.choice_spacing

style choice_button is default:
    properties gui.button_properties("choice_button")

style choice_button_text is default:
    properties gui.text_properties("choice_button")

style uix_choice_req_text is choice_button_text:
    size gui.choice_button_text_size - 6
    color uix.accent
    insensitive_color uix.accent
    yalign 0.5

style uix_choice_dev_text is default:
    size 24
    color "#ff4040"
    xalign 0.5
