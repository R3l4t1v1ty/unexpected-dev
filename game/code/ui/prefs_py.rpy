## Helpers for the Preferences page.

init offset = -400

init python in uix:

    ## The name of the language the game is written in (no translation).
    base_language_name = _("English")

    def languages():
        """
        The translations in game/tl/, sorted. Empty when there are none.
        """

        return sorted(l for l in renpy.known_languages() if l)

    def language_name(lang):
        """
        A readable name for translation `lang` ("brazilian_portuguese" ->
        "Brazilian Portuguese").
        """

        return lang.replace("_", " ").title()
