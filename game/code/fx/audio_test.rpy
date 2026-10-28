# Tests for fx audio. Developer mode only; excluded from builds, together with
# the generated tones in test_audio/.

init offset = 0

init python in fx:
    from store import Text

    add_track("fx_test_low", "code/fx/test_audio/fx_test_low.wav")
    add_track("fx_test_high", "code/fx/test_audio/fx_test_high.wav")
    add_track("fx_test_noise", "code/fx/test_audio/fx_test_noise.wav", volume=0.6)
    add_sound("fx_test_click", "code/fx/test_audio/fx_test_click.wav")

    def test_raises(fn):
        try:
            fn()
        except Exception:
            return True
        return False

    def test_say(title, problems):
        if problems:
            text = "%s: %d failed.\n%s" % (title, len(problems), "\n".join(problems))
        else:
            text = "%s: all checks passed." % title
        renpy.say(None, text.replace("[", "[[").replace("{", "{{").replace("%", "%%"))

    def test_sound_checks():
        problems = []
        if config.developer and not test_raises(lambda: sound("fx_test_missing")):
            problems.append("fx.sound should reject an unknown sound")
        if not test_raises(lambda: add_sound("fx_test_late", "x.wav")):
            problems.append("add_sound should only work at init")
        if [p for p in validate() if "fx_test_" in p]:
            problems.append("validator: the test files should be loadable")
        return problems

    def test_music_checks():
        problems = []

        def check(ok, what):
            if not ok:
                problems.append(what)

        low, high, noise = "fx_test_low", "fx_test_high", "fx_test_noise"

        def nothing(layer):
            return None

        def high_music(layer):
            return high if layer == "music" else None

        def silence(layer):
            return SILENCE

        # Choosing what should play.
        check(pick("music", None, [nothing, high_music]) == high, "no override: the first provider that answers decides")
        check(pick("ambient", None, [high_music]) is None, "providers answer per layer")
        check(pick("music", low, [high_music]) == low, "an override beats providers")
        check(pick("music", SILENCE, [high_music]) is None, "a SILENCE override silences")
        check(pick("music", None, [silence, high_music]) is None, "a provider's SILENCE stops later providers")
        check(pick("music", None, []) is None, "no override and no provider: silence")

        if config.developer:
            check(test_raises(lambda: pick("music", "fx_test_missing", [])), "an unknown track should raise")
            check(test_raises(lambda: music("fx_test_missing")), "fx.music should reject an unknown track")
        check(test_raises(lambda: add_track("fx_test_late", "x.wav")), "add_track should only work at init")
        check(test_raises(lambda: register_music_provider(nothing)), "register_music_provider should only work at init")

        # Applying it. fade=0 so the checks don't wait.
        st = core.state("fx")
        before_music, before_ambient = st["music"], st["ambient"]

        music(low, fade=0)
        check(st["music"] == low and st["playing_music"] == low, "fx.music should start the track at once")
        first = st["music_channel"]
        music(high, fade=0)
        second = st["music_channel"]
        check(st["playing_music"] == high and second != first, "a change should move to the other channel")
        music(high, fade=0)
        check(st["music_channel"] == second, "the same track again should change nothing")
        stop_music(fade=0)
        check(st["music"] == SILENCE and st["playing_music"] is None, "fx.stop_music should silence")
        ambient(noise, fade=0)
        check(st["playing_ambient"] == noise, "fx.ambient should start the ambience")
        ambient(SILENCE, fade=0)
        check(st["playing_ambient"] is None, "fx.ambient(SILENCE) should stop it")

        st["music"], st["ambient"] = before_music, before_ambient
        reconcile(fade=0)
        return problems

    def test_info(st, at):
        s = core.state("fx")
        lines = [
            "override: music %r, ambient %r" % (s["music"], s["ambient"]),
            "playing_music %r on %s" % (s["playing_music"], s["music_channel"]),
            "playing_ambient %r" % (s["playing_ambient"],),
            ]
        for channel in MUSIC_CHANNELS + (AMBIENT_CHANNEL,):
            lines.append("%s: %s" % (channel, renpy.music.get_playing(channel) or "-"))
        return Text("\n".join(lines).replace("{", "{{"), size=18, substitute=False), 0.25

define fx_test_info = DynamicDisplayable(fx.test_info)

# Live view of fx's state and what each channel is really playing.
screen fx_test_audio():
    zorder 100
    frame:
        xalign 1.0
        yalign 0.0
        add fx_test_info

label test_fx_sound:
    "fx.sound: click to play a short blip."
    $ fx.sound("fx_test_click")
    "You should have heard a blip. Click for the same blip at 30 percent volume."
    $ fx.sound("fx_test_click", volume=0.3)
    "Quieter this time?"
    $ fx.test_say("fx.sound checks", fx.test_sound_checks())
    return

label test_fx_music:
    show screen fx_test_audio
    $ fx.test_say("fx music checks", fx.test_music_checks())

    $ fx.music("fx_test_low")
    "Step 1: a low chord is playing (see the box, top right). Open the game menu, save in any slot, then continue."

    $ fx.music("fx_test_high")
    "Step 2: high beeps crossfade in. Roll back once (mouse wheel up): the low chord should come back. Then roll forward to here."

    $ fx.ambient("fx_test_noise")
    "Step 3: a soft noise plays under the beeps. It's ambience, so the sound volume slider controls it."

    $ fx.ambient(fx.SILENCE)
    $ fx.stop_music()
    "Step 4: music and ambience fade out."

    menu:
        "Step 5: load the save from step 1. You should land on step 1 with the low chord playing, and the box should say playing_music 'fx_test_low'. Click through again and pick Finish here."
        "Finish":
            pass

    $ fx.music(None)
    $ fx.ambient(None)
    hide screen fx_test_audio
    return
