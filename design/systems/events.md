# events/

Story events: event lines, their order, triggers, per-twin progress, the event book, the tracker, the Story tab (twin swap + completion), and replay.

Rebuild #2 is the reference; deeper changes come from a design session with the user before building.

## Model (from rebuild #2, with its gaps fixed)
- **Event line**: a storyline (e.g. a character's route or an arc for one twin). Events in a line chain automatically in declaration order.
- **Event**: id, line, name, characters involved, weight (for completion %), `about` texts (before and after it's done), where and when it can start, which NPCs it hides from the world while pending.
- **Links across lines** with AND/OR (rebuild #2 stored AND but never implemented it). Expressed with `ReqEventDone` combined by `ReqAll`/`ReqAny`, so the same condition language works everywhere.
- **Triggers**: location (exact or partial: a place or a space), slot, any `Req` (items, relationships, stats, flags). An event either auto-starts when its trigger matches on entering a location, or waits to be started from a marker or an NPC verb.
- **Progress per twin**: locked → available → done.
- **Event labels** come from `core.label_for("event", id)` and must `return`.

```
events.add_line("hana_route", _("Hana"), twin="ayumu", characters=("hana",))
events.add("hana_1", line="hana_route", at="town.park", when=ReqSlot(1), weight=2,
    about=(_("Hana seems to wait for someone at the park."), _("Ayumu met Hana at the park.")),
    hides=("hana",), auto=True)
events.add("hana_2", line="hana_route", requires=ReqEventDone("yui_3"))   # plus the automatic hana_1 link
```
(Shape only; decided in events task 2.)

## Hooks into other systems
- world: `world.register_entry_hook` (auto-start events on entering a location), `world.register_hidden_provider` (hide NPCs busy in pending events), `world.register_marker_provider` (pending events on the map).
- characters: the event book section on the character page via `chars.register_page_section`.
- ui: Story tab (twin cards with completion % and swap, the old story-swap screen with the mirage hover), Events tab, tracker HUD panel.
- progress: listens to `event_finished` to unlock gallery entries and achievement goals.

## Replay
`events.replay_action(id)` returns a `Replay(label, scope, locked)` with `locked` taken from this save's progress and the right twin in scope (`{"gs.twin": ...}`). Replay setup runs from `config.start_callbacks`. Side effects check `_in_replay`.

## Open questions
- What changes beyond rebuild #2 (design session).
