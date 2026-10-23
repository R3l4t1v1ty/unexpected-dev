## Save and Load. Ren'Py opens these by name; both are tabs of the game menu.

init offset = 0

screen save():
    tag menu
    use uix_menu("save")

screen load():
    tag menu
    use uix_menu("load")


screen uix_save_page():
    use uix_file_slots("save")

screen uix_load_page():
    use uix_file_slots("load")


## `mode` is "save" or "load". (FileAction can't tell them apart here: it looks
## at the screen name, which is uix_menu.)
screen uix_file_slots(mode):

    default page_name_value = FilePageNameInputValue(pattern=_("Page {}"), auto=_("Automatic saves"), quick=_("Quick saves"))

    fixed:

        ## The input gets the enter key before any of the buttons do.
        order_reverse True

        ## The page name; click it to rename the page.
        button:
            style "page_label"

            key_events True
            xalign 0.5
            action page_name_value.Toggle()

            input:
                style "page_label_text"
                value page_name_value

        grid gui.file_slot_cols gui.file_slot_rows:
            style_prefix "slot"

            xalign 0.5
            yalign 0.5

            spacing gui.slot_spacing

            for i in range(gui.file_slot_cols * gui.file_slot_rows):

                $ slot = i + 1
                $ slot_action = FileSave(slot) if mode == "save" else FileLoad(slot)

                button:
                    action slot_action

                    has vbox

                    add FileScreenshot(slot) xalign 0.5

                    text FileTime(slot, format=_("{#file_time}%A, %B %d %Y, %H:%M"), empty=_("empty slot")):
                        style "slot_time_text"

                    text FileSaveName(slot):
                        style "slot_name_text"

                    key "save_delete" action FileDelete(slot)

        vbox:
            style_prefix "page"

            xalign 0.5
            yalign 1.0

            hbox:
                xalign 0.5

                spacing gui.page_spacing

                textbutton _("<") action FilePagePrevious()
                key "save_page_prev" action FilePagePrevious()

                if config.has_autosave:
                    textbutton _("{#auto_page}A") action FilePage("auto")

                if config.has_quicksave:
                    textbutton _("{#quick_page}Q") action FilePage("quick")

                for page in range(1, 10):
                    textbutton "[page]" action FilePage(page)

                textbutton _(">") action FilePageNext()
                key "save_page_next" action FilePageNext()

            if config.has_sync:
                if mode == "save":
                    textbutton _("Upload Sync"):
                        action UploadSync()
                        xalign 0.5
                else:
                    textbutton _("Download Sync"):
                        action DownloadSync()
                        xalign 0.5


style page_label is gui_label
style page_label_text is gui_label_text
style page_button is gui_button
style page_button_text is gui_button_text

style slot_button is gui_button
style slot_button_text is gui_button_text
style slot_time_text is slot_button_text
style slot_name_text is slot_button_text

style page_label:
    xpadding 75
    ypadding 5
    xalign 0.5

style page_label_text:
    textalign 0.5
    layout "subtitle"
    hover_color gui.hover_color

style page_button:
    properties gui.button_properties("page_button")

style page_button_text:
    properties gui.text_properties("page_button")

style slot_button:
    properties gui.button_properties("slot_button")

style slot_button_text:
    properties gui.text_properties("slot_button")
