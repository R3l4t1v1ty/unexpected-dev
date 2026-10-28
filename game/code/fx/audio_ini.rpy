# fx's own audio, and the audio wiring.
#
# fx-owned tracks and sounds go here at band 0 (files under game/audio/music,
# game/audio/ambience, game/audio/sfx), e.g.
#
#     init python in fx:
#         add_track("rain", "audio/ambience/rain.ogg", volume=0.7)
#         add_sound("door_open", "audio/sfx/door_open.ogg")
#
# Other folders register theirs with fx.add_track / fx.add_sound in their own
# _ini files.

init offset = 0

init 100 python in fx:
    core.connect("game_started", on_game_started)
    core.connect("game_loaded", on_game_loaded)
    core.register_validator("fx", validate)
