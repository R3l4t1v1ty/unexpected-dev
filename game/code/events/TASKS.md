# events/ tasks

Milestone: **M2** (after world and characters have their first tasks done).

## Context
Reference: rebuild #2's event system.
- `StoryEvent`: name, characters, weight (for completion %), triggers, `about[before, after]` texts, label.
- Event lines: events in a line chain automatically in declaration order. Old rule: the line key is the event key without its `_N` suffix; make the line explicit instead. `connect()` linked across lines.
- Triggers: location (partial key: a place or space matches all its locations), time, item.
- A per-character event book in the encyclopedia; weight-based completion % per twin; replay of finished events.
- Its gaps, to fix:
  - AND logic was stored but never implemented ("TBD").
  - Item triggers were empty.
  - A time trigger compared a list to an int, so it never matched.
  - Event location keys were wrong in several places, which a validator would have caught.
- The released game also hid NPCs from the sandbox while an event involving them was pending, and showed pending events as markers on the map.
- Deeper changes are expected: task 1 is a design session with the user.
- **From the RPG and relationship design (2026-10-23):**
  - Relationship events: ten per relationship character, one per relationship status. Each unlocks when the twin first reaches its status (`ReqRelReached(char, status)` from characters) and stays unlocked. They don't chain in order like a line, so the model must allow events that only have conditions (or lines that don't auto-chain). They're one-time; replay can show them again.
  - **Tier rule** for relationship events (the user, 2026-10-23): statuses form tiers, t0 acquaintances; t1 friends, colleague, casual, buddy; t2 lovers, fwb, romantic, platonic; t3 soulmate (`chars.tier(status)`). An event can only be played once the twin has played at least one of that character's relationship events from the tier below (t0 needs nothing). Suggested shape: `events.add(..., rel=(char, status))` adds both conditions automatically.
  - The soulmate event can vary with the path the twin took (`chars.path(char)`, `ReqRelPath`).
  - Events can start from adventure mode (an area or object in a map), not only from world locations.
  - Choices inside events can carry `req=` (ui's choice screen greys out failed ones): stats (`ReqStat`), items (`ReqItem`), reputation (`ReqRep`), relationships (`ReqRel…`).

New-model sketch (confirm in task 1):
- Progress per twin: locked → available → done.
- An event can auto-start on entering a matching location, or wait for a marker or an NPC verb to start it.
- Cross-line requirements are `Req`s: `ReqEventDone`, combined with `ReqAll`/`ReqAny`.
- Event labels: `core.label_for("event", id)` → `event__<id>`, called and must `return`.

Replay facts (checked in the SDK):
- `Replay` starts from a fresh `gs` (defaults re-run).
- `scope` keys can be dotted attribute paths (`{"gs.twin": "nemu"}`), not dict items.
- `config.start_callbacks` run inside the replay after the scope is applied.
- Pass `locked=` explicitly, because unlocks are per save.

## Uses
- core: `Definition`, registry, flags, `register_state`, `me()`, `Req…`, signals, `label_for`, `StateAction`, `swap()`.
- world: `world.register_entry_hook`, `world.register_hidden_provider`, `world.register_marker_provider`, `world.idle()`, `label world_swap`, signal `location_entered`.
- characters: `chars.get`, `chars.register_page_section`, `ReqRelReached`, `chars.tier`, `chars.path` (relationship events).
- ui: `uix.register_menu_tab`, `uix.register_hud_panel`, `fx_mirage` from fx for the Story-tab hover.

## Tasks
- [ ] 1. **(needs user) Design session.** Go through the model above with the user, collect the changes beyond rebuild #2, and rewrite this Context with the result.
- [ ] 2. **Definitions.** `events.add_line`, `events.add`, automatic chaining within a line, cross-line requirements, triggers (location exact or partial, slot, `Req`), weights, `about` texts, `hides`, `auto`. Validator: unknown locations, characters and labels. Done when: `events_test.rpy` builds a small graph and availability matches expectations for each step.
- [ ] 3. **Progress.** Per-twin state; `events.available(twin=None)`, `events.done(id, twin=None)`, `events.start(id)`, `events.finish(id)`, `ReqEventDone(id)`; signals `event_started`, `event_finished`. Done when: progress survives save/load and is separate per twin.
- [ ] 4. **World hooks.** Register the entry hook (auto-start), the hidden provider (NPCs in pending events), the marker provider (pending events on the map). Done when: in the test world an event auto-starts on entry, its NPC is hidden while pending, and the map shows its marker.
- [ ] 5. **Event book, tracker, completion.** `events.completion(twin=None, char=None)`; event-book section on the character page; tracker HUD panel `events_tracker_panel`; Events tab. Done when: works with test events on PC and phone.
- [ ] 6. **Story tab.** Twin cards with completion % and a swap button (`renpy.jump_out_of_context("world_swap")`, enabled only when `world.idle()`), mirage hover. Done when: swap works from the tab and is disabled during content.
- [ ] 7. **Replay.** `events.replay_action(id)`; setup in `config.start_callbacks`; locked per save. Done when: replaying a finished test event returns to the menu without changing progress.
- [ ] 8. **Publish.** Print the events section for game/code/CLAUDE.md.

## API to publish
`events.add_line`, `events.add`, `events.available`, `events.done`, `events.start`, `events.finish`, `ReqEventDone`, `events.completion`, `events.replay_action`, screens `events_book`, `events_tracker_panel`, Story and Events tabs, signals `event_started`, `event_finished`.
