# fx audio: channels, the track and sound tables, and the music manager.
#
# What should play is derived, never kept in init-time globals:
#   1. the override content set with fx.music / fx.ambient (saved in gs);
#   2. otherwise the first registered provider that answers.
# fx.reconcile() compares that with what fx last started and crossfades.
# "What fx last started" is also in gs, so it rolls back and loads together
# with Ren'Py's own record of the channels, and the two never disagree.
#
# fx owns the music1, music2 and ambience channels: never use `play music1`
# and the like directly, or the record in gs goes stale.

init offset = -400

init python in fx:
    _constant = True

    import re
    from store import core, config

    # Music crossfades between two channels; ambience loops on its own channel.
    # Music follows the music volume, ambience the sound volume.
    MUSIC_CHANNELS = ("music1", "music2")
    AMBIENT_CHANNEL = "ambience"
    # Ren'Py's built-in channel that plays overlapping sounds (sound volume).
    SOUND_CHANNEL = "audio"

    renpy.music.register_channel("music1", "music", loop=True)
    renpy.music.register_channel("music2", "music", loop=True)
    renpy.music.register_channel("ambience", "sfx", loop=True)

    # Default crossfade, in seconds.
    CROSSFADE = 2.0

    # As an override or a provider's answer: play nothing on that layer.
    SILENCE = ""

    KEY_RE = re.compile(r"[a-z][a-z0-9_]*\Z")

    # key -> (path, volume). Filled at init, never changed afterwards.
    TRACKS = {}
    SOUNDS = {}

    # (order, registration number, fn), sorted. Filled at init.
    PROVIDERS = []

    core.register_state("fx", {
        # Overrides: a track key, SILENCE, or None (providers decide).
        "music": None,
        "ambient": None,
        # What reconcile last started (a track key, or None when silent),
        # and which music channel holds it.
        "playing_music": None,
        "playing_ambient": None,
        "music_channel": MUSIC_CHANNELS[0],
        }, False)

    def init_only(what):
        if not renpy.is_init_phase():
            raise Exception("fx.%s can only be called at init." % what)

    def add_entry(table, what, key, path, volume):
        init_only(what)
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise Exception("fx.%s: %r is not a snake_case key." % (what, key))
        if key in table:
            raise Exception("fx.%s: %r is already registered." % (what, key))
        table[key] = (path, float(volume))

    def add_track(key, path, volume=1.0):
        """
        Registers a looping track for music or ambience, at init. `path` is
        relative to game/ (e.g. "audio/music/town_day.ogg"); `volume` is
        relative, 0.0-1.0.
        """
        add_entry(TRACKS, "add_track", key, path, volume)

    def add_sound(key, path, volume=1.0):
        """
        Registers a one-shot sound for fx.sound, at init.
        """
        add_entry(SOUNDS, "add_sound", key, path, volume)

    def sound(key, volume=1.0):
        """
        Plays a registered sound once. Sounds overlap.
        """
        entry = SOUNDS.get(key)
        if entry is None:
            if config.developer:
                raise Exception("fx.sound: unknown sound %r." % (key,))
            return
        path, base = entry
        renpy.music.play(path, channel=SOUND_CHANNEL, loop=False, relative_volume=base * volume)

    def register_music_provider(fn, order=100):
        """
        At init. fn(layer) gets "music" or "ambient" and returns a track key,
        SILENCE, or None (no opinion). Providers are asked in `order`; the
        first that doesn't return None decides. fn only reads state.
        """
        init_only("register_music_provider")
        PROVIDERS.append((order, len(PROVIDERS), fn))
        PROVIDERS.sort(key=lambda p: p[:2])

    def pick(layer, override, providers=None):
        """
        The track key that should play on `layer`, or None for silence.
        `providers` (a list of functions) replaces the registered ones, for tests.
        """
        key = override
        if key is None:
            if providers is None:
                providers = [p[2] for p in PROVIDERS]
            for fn in providers:
                key = fn(layer)
                if key is not None:
                    break
        if not key:
            return None
        if key not in TRACKS:
            if config.developer:
                raise Exception("fx: unknown track %r for %s." % (key, layer))
            return None
        return key

    def reconcile(fade=None):
        """
        Makes what plays match what should play. Cheap when nothing changed:
        world_loop calls it on every pass, and it runs after load.
        """
        if fade is None:
            fade = CROSSFADE
        st = core.state("fx")
        reconcile_music(st, fade)
        reconcile_ambient(st, fade)

    def reconcile_music(st, fade):
        want = pick("music", st["music"])
        if want == st["playing_music"]:
            return

        old = st["music_channel"]
        if st["playing_music"] is not None:
            renpy.music.stop(channel=old, fadeout=fade)

        if want is not None:
            # Always start on the other channel, so the old track can fade out.
            new = MUSIC_CHANNELS[1] if old == MUSIC_CHANNELS[0] else MUSIC_CHANNELS[0]
            path, volume = TRACKS[want]
            renpy.music.play(path, channel=new, loop=True, fadein=fade, relative_volume=volume)
            st["music_channel"] = new

        st["playing_music"] = want

    def reconcile_ambient(st, fade):
        want = pick("ambient", st["ambient"])
        if want == st["playing_ambient"]:
            return

        if want is None:
            renpy.music.stop(channel=AMBIENT_CHANNEL, fadeout=fade)
        else:
            path, volume = TRACKS[want]
            renpy.music.play(path, channel=AMBIENT_CHANNEL, loop=True, fadeout=fade, fadein=fade, relative_volume=volume)

        st["playing_ambient"] = want

    def set_override(layer, key, fade):
        if key is not None and key != SILENCE and key not in TRACKS:
            if config.developer:
                raise Exception("fx.%s: unknown track %r." % (layer, key))
            return
        core.state("fx")[layer] = key
        reconcile(fade)

    def music(key, fade=None):
        """
        Sets the music override and applies it at once: a track key, SILENCE,
        or None to hand music back to the providers. Stays until changed.
        """
        set_override("music", key, fade)

    def ambient(key, fade=None):
        """
        Same as fx.music, for the ambience layer.
        """
        set_override("ambient", key, fade)

    def stop_music(fade=None):
        """
        Silences music until the next fx.music(...). Ambience is unaffected.
        """
        set_override("music", SILENCE, fade)

    def on_game_started(**kwargs):
        # Main-menu music plays on Ren'Py's "music" channel; don't carry it into the game.
        renpy.music.stop(channel="music", fadeout=CROSSFADE)
        reconcile()

    def on_game_loaded(**kwargs):
        # Ren'Py restores what was playing; this catches providers that now
        # answer differently (e.g. after an update).
        reconcile()

    def validate():
        problems = []
        for table, what in ((TRACKS, "track"), (SOUNDS, "sound")):
            for key in sorted(table):
                path = table[key][0]
                if not renpy.loadable(path):
                    problems.append("%s %s: missing file %s" % (what, key, path))
        return problems
