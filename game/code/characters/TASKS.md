# characters/ tasks

Milestone: **M2**.

## Context
Baseline is rebuild #2's design:
- `Chara`: id, name, surname, colour, encyclopedia card image, factions (ids from factions/, for the encyclopedia filter), outfits, `about` text per outfit, info. Builds `Character` objects: normal; thought (`Character(..., show_thought=True)` passes `thought=True` to the say screen); unknown (shows "???" until the current twin has been introduced); a fourth variant only if a need appears.
- About 50 characters in the old game. 53 were declared in rebuild #2.
- Encyclopedia: card grid filtered by faction; character page with outfit box, zoom, relationship bars and status, event book.
- Rebuild #2 bugs to avoid: `introduced` was inverted; `Relationship.get_type()` could return None and crash the page; zoom/outfit were stored on saved objects; the factions page was a stub.
- Factions and reputation moved to factions/.
- The user will add more character features later.

**Relationships** (designed with the user, 2026-10-23). The core of world-mode play. Which characters get one isn't decided; build with test characters.
- **Stats**, per twin, 0–100: friendliness (f), commitment (c), attraction (a). They only go down through the reset item.
- **Ten statuses** from the stats, with rebuild #2's formulas kept as tunable data. S = a + f + c; the first matching rule wins:
  ```
  soulmate      S >= 250
  fwb           a + f - c >= 150
  romantic      a + c - f >= 150
  platonic      f + c - a >= 150
  lovers        S >= 150
  buddy         f - a - c >= 50
  colleague     c - a - f >= 50
  casual        a - f - c >= 50
  friends       S >= 50
  acquaintances otherwise
  ```
  Path: acquaintances → friends → colleague/buddy/casual → lovers → fwb/romantic/platonic → soulmate. Tiers (by total 0–49, 50–149, 150–249, 250+): **t0** acquaintances; **t1** friends, colleague, casual, buddy; **t2** lovers, fwb, romantic, platonic; **t3** soulmate. Checked over all 0–100 combinations: always exactly one status; matches the old code. Because stats only go up, a branch can't turn into another branch of the same tier (Buddy → Casual); it can move back to the tier's main status (Buddy → Friends) by raising the other stats. Switching branches needs the reset item; the user is fine with that for now.
- **Events**: one per status (ten). The first time a twin reaches a status, its event unlocks and stays unlocked (`ReqRelReached(char, status)`). It can only be played once the twin has played at least one event of the tier below (t0 needs nothing); until then it waits, unlocked. The events are ordinary events in events/, which enforces the tier rule using `chars.tier(status)`.
- **Stats rise freely**; nothing holds them back (the user, 2026-10-23).
- **Path**: per twin, the statuses entered since the last reset, in order (`chars.path(char)`, `ReqRelPath(char, *statuses)`). The path to soulmate can change the soulmate scene.
- **Activities**: three per character, one per stat (e.g. helping Rina at the maid café raises commitment). An activity plays several beats (short scenes, each a label): sometimes picked at random, sometimes offered as a choice. Higher statuses add beats to the pool and raise how many play (Friends 3, Lovers 5). Each costs 1 time slot and is available only in its slot(s), where the NPC is (world/ places NPCs by schedule).
- **Reset item**: a consumable (crafted in rpg/). Using it calls `chars.reset_rel(char)`: the current twin's three stats go to 0 and the path starts over. Played events stay played; reached statuses stay reached.
- **Twins**: a relationship lists its twins (usually one, both possible).
- **RPG ties**: other folders scale gains with `chars.register_gain_modifier(fn)` (rpg: charisma); gifts call `chars.add_rel`; events may require stats themselves.

## Uses
- core: `Definition`, registry, flags (per twin), `register_state`, `Req…`, signals, `asset`, `StateAction`, `advance()`.
- ui: `uix.register_menu_tab`, components, phone layout rules.
- factions: faction ids and names for the encyclopedia filter (`fac.get`), once factions exists; placeholder until then.

## Tasks
- [ ] 1. **Characters and speakers.** `chars.add(...)`, `chars.get(id)`; build the Character variants; decide how story names speakers (e.g. a store name per character such as `hana`, and how thought/unknown variants are written in dialogue), write that into the published API. Done when: a test label speaks with every variant.
- [ ] 2. **Introductions.** `chars.introduce(id)` (current twin), `chars.known(id, twin=None)`, `ReqKnown(id)`; unknown speaker shows "???" until introduced; signal `character_introduced`. Done when: test shows the name change after introduction, per twin.
- [x] 3. **(needs user) Relationship design.** Done 2026-10-23; see Context.
- [ ] 4. **Relationship model.** `chars.add_relationship(char, twins)`; stats per twin; status and tier tables as data; `chars.tier(status)` (0–3); `chars.rel(char, stat, twin=None)`, `chars.add_rel(char, stat, amount)` (clamped 0–100, gain modifiers), `chars.status(char, twin=None)`, `chars.reached(char, status, twin=None)`, `chars.path(char, twin=None)`, `chars.reset_rel(char)`, `chars.register_gain_modifier(fn)`; `ReqRel(char, stat, min)`, `ReqRelStatus(char, *statuses)`, `ReqRelReached(char, status)`, `ReqRelPath(char, *statuses)`; signals `relationship_changed`, `relationship_status_changed`. Done when: tests cover the whole 0–100 grid (step 5 is enough) giving one status each, the path (and that reset starts it over while reached statuses stay), a gain modifier, and per-twin separation.
- [ ] 5. **Activities.** `chars.add_activity(id, char, stat, slots, gain, mode="random"|"choice")`, `chars.add_beat(activity, id, from_status)` (beat labels via `core.label_for`), how many beats play per status; `call chars_activity(activity_id)` plays the beats, applies the gain, advances 1 slot. Done when: a test activity plays 3 beats at friends and 5 at lovers, in both modes.
- [ ] 6. **Encyclopedia.** `screen chars_encyclopedia` (grid, faction filter), `screen chars_page(char_id)` (outfits, zoom, relationship bars and status, sections from `chars.register_page_section(id, screen)`); phone layout; register the Characters tab. Done when: works on PC and under phone emulation with test characters.
- [ ] 7. **World hooks.** After world tasks 2 and 6: activities as verbs on the NPC when its slot matches; a marker provider showing where activities are. Done when: a test NPC offers its activity only in its slot.
- [ ] 8. **Publish.** Print the characters section for game/code/CLAUDE.md.

## API to publish
`chars.add`, `chars.get`, speaker names, `chars.introduce`, `chars.known`, `ReqKnown`, `chars.add_relationship`, `chars.rel`, `chars.add_rel`, `chars.status`, `chars.tier`, `chars.reached`, `chars.path`, `chars.reset_rel`, `chars.register_gain_modifier`, `ReqRel`, `ReqRelStatus`, `ReqRelReached`, `ReqRelPath`, `chars.add_activity`, `chars.add_beat`, `call chars_activity`, `chars.register_page_section`, screens `chars_encyclopedia`, `chars_page`, signals `character_introduced`, `relationship_changed`, `relationship_status_changed`.
