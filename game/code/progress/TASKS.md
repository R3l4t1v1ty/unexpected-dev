# progress/ tasks

Milestone: **M5** (needs core, ui, events).

## Context
Both achievements and gallery unlocks are **per save** (shared between the twins within a save).

**Gallery** (kept; the most complete old system, so keep its data model):
- Reward gallery: event CGs plus achievement pictures, filterable by character.
- L.E.W.D.: per event, a slideshow of picture sets mixing images and looping webm (sets built from prefix + numbers + suffix; "anim" entries become `Movie`s), unlocked when the event is done.
- Old bugs: an `entires` typo, `zoom_mode` never initialised, a set builder that mutated its input list.
- Entries can offer a replay of their event via `events.replay_action(id)`.

**Achievements** (full rebuild). Old version: groups → achievements → goal objects (`goal_done`, `progress_text`), claimed by the player, a claim unlocked a gallery picture; only two goal types existed. Direction to confirm with the user:
- goals as `Req`s or counters fed by signals
- progress text and percentage
- claimable rewards
- a toast on unlock
- nothing during replays

## Uses
- core: `Definition`, registry, `register_state`, `Req…`, signals (`core.connect`), `StateAction`, `asset`.
- events: `events.done`, `events.replay_action`, signal `event_finished`.
- ui: `uix.register_menu_tab`, `uix.notify`, components.
- fx: `fx_mirage` (optional hover effects).
- Other signals for counters: `location_entered`, `item_changed`, `level_up`, `relationship_changed`, `time_changed`.

## Tasks
- [ ] 1. **(needs user) Achievement design.** Kinds of goals, rewards, and whether any also mirror to Steam or another platform. Rewrite this Context with the result.
- [ ] 2. **Gallery data.** `prog.add_gallery_set(id, ...)` for reward pictures and L.E.W.D. sets (images and webm), unlock rules (event done, achievement claimed), `prog.gallery_unlocked(id)`. Done when: tests cover unlocking per save.
- [ ] 3. **Gallery screens.** Reward gallery with character filter, L.E.W.D. slideshow with movies, replay button; phone layout; register the Gallery tab. Done when: test content works on both layouts.
- [ ] 4. **Achievements.** Definitions, goals (`Req` or signal counters), progress text, claim and rewards, `prog.unlocked(id)`, `prog.claim(id)`, toast, signal `achievement_unlocked`; ignored during replay. Done when: test achievements unlock from test signals and survive save/load.
- [ ] 5. **Achievements screen.** List with progress and claim; register the Achievements tab. Done when: works on both layouts.
- [ ] 6. **Publish.** Print the progress section for game/code/CLAUDE.md.

## API to publish
`prog.add_gallery_set`, `prog.gallery_unlocked`, `prog.add_achievement`, `prog.unlocked`, `prog.claim`, signal `achievement_unlocked`, Gallery and Achievements tabs.
