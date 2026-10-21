# fx/

Presentation helpers: music and sound, camera-style transforms and screen shake, the reduced-motion setting, fake loading screens with tips, transitions, and the mirage shader. All kept from the old versions, with fixes.

## Music
The released game's `MusicManager` had the right API (308 story calls): ambient/vibe/stage keys, crossfade between two channels (`music1`, `music2`), event tracks, sandbox music by time of day. Its flaw: an init-time global, not saved and not rollback-safe.

New version:
- The **wanted** music is derived from state: content can set an override (`fx.music(key)`, stored as plain data in fx's state section), otherwise music providers decide (world registers one: track per location/place/slot).
- `fx.reconcile()` compares what should play with what is playing and crossfades if needed. world_loop calls it every pass; it also runs after load. So music survives rollback and load without tracking.

## Transforms
Camera-style zoom, slide, slide+zoom, rotate in/out, blur, and `fx_shake`. With reduced motion on, each becomes a no-op. The released game stored the swapped transforms as save `default`s, so the persistent setting was ignored after New Game or Load. New version: the transforms read `persistent.fx_reduced_motion` when they run.

## Fake loading screens
Deliberate fake loading screen between scenes: random 1–6 s, random background, tips you can cycle, click to continue. Off switch `persistent.fx_fake_loading`. Tips come from a registry (`fx.add_tip(text, group=None)`); the text itself comes from the user.

## Shader
`mirage` (noise distortion, desaturate, tint), used for hover effects. Render the noise texture once and reuse it (the old one rendered it in every constructor, and some were created inline in screens).

## Open questions
- Tips text.
