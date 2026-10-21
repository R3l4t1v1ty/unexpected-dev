# fx/

## Purpose
Presentation helpers: music and sound, camera-style transforms and screen shake with the reduced-motion setting, fake loading screens with tips, transitions, and the mirage shader.

## Rules
- Namespace `fx`; transforms and screens `fx_*`; persistent settings `persistent.fx_*`.
- Python at init -400; transforms, screens and images at ≥ 0.
- Music state is derived, not tracked: what should play comes from `gs` (overrides) and providers; `fx.reconcile()` makes it so. Never keep playback state in init-time globals.
- Every motion effect checks `persistent.fx_reduced_motion` when it runs, not at init or game start.
- fx doesn't reference other systems; they register providers (`fx.register_music_provider`).

@TASKS.md
