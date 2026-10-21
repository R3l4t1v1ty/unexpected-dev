# fx/ tasks

Milestone: **M2** (can start as soon as core is done).

## Context
Ported from the released game, with fixes:
- **Music manager.** Old API (used 308 times by story): keys `ambient`, `vibe`, `stage`; crossfade between two music channels; event tracks; sandbox music by time of day. Old flaw: an init-time global, not saved, not rollback-safe. New rule: what should play is derived from state. Content sets an override with `fx.music(key)` (stored as plain data in fx's section via `core.register_state`); otherwise registered providers decide (world registers one that picks a track by location and slot). `fx.reconcile()` compares wanted vs playing and crossfades. world_loop calls it on every pass, and it runs after load.
- **Transforms.** Zoom, slide, slide+zoom, rotate in/out, blur, `fx_shake`. With `persistent.fx_reduced_motion` on, each becomes a no-op. Old bug: the no-op swap was stored in save `default`s, so the setting was ignored after New Game or Load. Read the persistent value when the transform runs.
- **Fake loading screen.** Random 1–6 s wait, random background, tips the player can cycle, click to continue; off switch `persistent.fx_fake_loading`. Tips registry; text from the user.
- **Mirage shader.** Noise distortion, desaturate, tint; used for hover effects. Render the noise texture once and cache it.

## Uses
- core: `core.register_state`, `core.state`, `core.connect` (`game_loaded`), `core.StateAction`.

## Tasks
- [ ] 1. **Audio channels and sounds.** Register `music1`/`music2` (and `ambience` if needed); `fx.sound(id)` with sound ids from a table. Done when: test plays a sound.
- [ ] 2. **Music manager.** `fx.music(key)`, `fx.ambient(key)`, `fx.stop_music()`, `fx.register_music_provider(fn)`, `fx.reconcile()` with crossfade; reconcile after load. Done when: a test sets music, saves, changes it, loads, and the right track plays; rollback restores the previous track.
- [ ] 3. **Transforms.** `fx_zoom`, `fx_slide`, `fx_slide_zoom`, `fx_rotate`, `fx_blur`, `fx_shake`; each a no-op when `persistent.fx_reduced_motion` is on, checked live. Done when: toggling the setting mid-game changes the next use without restarting.
- [ ] 4. **Transitions.** A small named set (dissolves, image-mask wipes; the old game's masks are in its `misc/` folder, ask the user to copy them into `game/images/` or a new `game/fx/` asset folder). Done when: test label shows each.
- [ ] 5. **Mirage shader.** `fx_mirage` displayable with the shader and a cached noise texture. Done when: test screen with 10 instances has no per-frame texture work (check with the profiler).
- [ ] 6. **Fake loading.** `call fx_loading(tips=None)`, `fx.add_tip(text, group=None)`, `default persistent.fx_fake_loading = True`. Done when: test shows it, the off switch skips it.
- [ ] 7. **Publish.** Print the fx section for game/code/CLAUDE.md.

## API to publish
`fx.music`, `fx.ambient`, `fx.stop_music`, `fx.reconcile`, `fx.register_music_provider`, `fx.sound`, the `fx_*` transforms, `persistent.fx_reduced_motion`, `fx_mirage`, `call fx_loading`, `fx.add_tip`, `persistent.fx_fake_loading`.
