# progress/

Achievements and the gallery. **Both are per save**: each save has its own unlocks, and a new game starts locked.

## Gallery (kept)
The most complete system in the old versions; keep its data model:
- **Reward gallery**: event CGs and achievement pictures, filterable by character.
- **L.E.W.D.**: per-event picture sets mixing images and looping webm movies (sets built from prefix + numbers + suffix; "anim" entries become `Movie`s), unlocked when the event is done.
- Viewing an entry can offer a replay of its event (`events.replay_action(id)`, locked per save).

## Achievements (full rebuild)
Old: groups → achievements → goal objects (`goal_done`, `progress_text`), claimed manually, a claim unlocked a gallery picture; only "time played" and one guessing-game goal existed, with placeholder groups copy-pasted.

New direction (confirm in the design session):
- Achievement definitions with a goal expressed as a `Req` (one-off conditions) or a counter fed by signals (`event_finished`, `location_entered`, `item_changed`, `item_crafted`, `relationship_status_changed`, `quest_completed`…), so achievements need no code in other folders.
- Progress text and percentage for counters.
- Claiming gives rewards (gallery pictures, maybe items or currency), with a toast on unlock.
- Signals are ignored during replays (`_in_replay`).

## Open questions
- Achievement design: kinds of goals, rewards, and whether some also go to Steam or another platform (Ren'Py's `achievement` module is global, not per save, so it would be a separate mirror).
