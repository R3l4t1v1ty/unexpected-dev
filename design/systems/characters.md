# characters/

Characters, the encyclopedia, and the relationship system. (Factions and reputation moved to [factions.md](factions.md) on 2026-10-23.)

## Characters (rebuild #2 baseline)
`Chara` definitions: id, name, surname, colour, encyclopedia card, factions (ids from factions/, used to filter the encyclopedia), outfits, `about` text per outfit, info. Each builds the `Character` objects story needs:
- normal speech
- thought (`show_thought=True`; the say screen gets `thought=True`)
- unknown ("???" until the twin has been introduced)
- one more variant if needed (rebuild #2 had four)

Per twin: introduced or not, outfits seen. The exact way story refers to speakers (store names like `hana`) is decided in characters task 1 and written into game/code/CLAUDE.md, because story/ will rely on it.

The user will add more to characters later.

## Encyclopedia (rebuild #2, kept)
A game-menu tab: card grid filtered by faction; a character page with outfit box, zoom, relationship bars and status, and the event book (provided by events through `chars.register_page_section`). Zoom and selected outfit are screen variables, not saved data (rebuild #2 stored them on saved objects).

## Relationships (designed with the user, 2026-10-23)
The core of world-mode play. Some characters get a relationship; which ones isn't decided yet. Diagram: `game/dev_resources/char relatiionship progression.png`. Old code: `game/dev_resources/relationships_py.txt`.

**Stats.** Friendliness (f), commitment (c), attraction (a): 0–100 each, per twin.

**Statuses.** Ten, worked out from the stats with rebuild #2's formulas (kept, as tunable data). The diagram's path is Acquaintances → Friends → Colleague / Buddy / Casual → Lovers → FWB / Romantic / Platonic → Soulmate. With S = a + f + c, the first matching rule wins:

| Status | Rule |
|---|---|
| Soulmate | S ≥ 250 |
| FWB | a + f − c ≥ 150 (no commitment) |
| Romantic | a + c − f ≥ 150 (no friendliness) |
| Platonic | f + c − a ≥ 150 (no attraction) |
| Lovers | S ≥ 150 |
| Buddy | f − a − c ≥ 50 (friendliness only) |
| Colleague | c − a − f ≥ 50 (commitment only) |
| Casual | a − f − c ≥ 50 (attraction only) |
| Friends | S ≥ 50 |
| Acquaintances | otherwise |

Checked over every combination of 0–100: each gives exactly one status, and this table matches the old code's list of inequalities. (Rebuild #2's page crash came from elsewhere, e.g. random starting values; keep a test anyway.)

**Moving sideways.** The status is recomputed on every change, so it moves between a tier's main status and its branches (Friends ↔ Buddy, Lovers ↔ FWB). Because stats only go up, one branch can never turn directly into another branch of the same tier (checked): Buddy → Casual would need attraction to beat friendliness + commitment by 50, which pushes the total into the next tier. A player sees another branch by using the reset item. The user is fine with that for now (2026-10-23).

**Tiers.** t0: Acquaintances. t1: Friends, Colleague, Casual, Buddy. t2: Lovers, FWB, Romantic, Platonic. t3: Soulmate.

**Events.** Ten per character, one per status. The first time a twin reaches a status, its event unlocks and stays unlocked. They're one-time (replay may show them again, always the same). They're ordinary events in events/, with the status as their condition (`ReqRelReached`).

**Tier rule** (the user, 2026-10-23): stats rise freely, but an event can only be played once the twin has played at least one event of the tier below (t0 needs nothing). An unlocked event waits until then. events/ enforces this with `chars.tier(status)`.

**Path.** characters records, per twin, the statuses entered since the last reset, in order (`chars.path`, `ReqRelPath`). The path to soulmate can change the soulmate scene.

**Activities.** Three per character, one per stat (e.g. helping Rina at the maid café raises commitment).
- Replayable and a bit different each time: an activity plays a few **beats** (short scenes); sometimes the beats are picked at random, sometimes offered as a choice.
- Higher statuses add beats to the pool and raise how many play (Friends: 3 tasks at the café, Lovers: 5).
- Each costs 1 time slot and is available only in its time slot(s) of the day, where the NPC is by their schedule.
- The graph's "Character Repeatable Event" nodes are these activities (left off the drawing).

**Reset item.** A consumable crafted from a base item plus something specific to that character. Using it sets that character's three stats to 0 for the current twin and starts the path over. Played events stay played, so a new run through the statuses can unlock other branches' events.

**Twins.** Values are per twin. A relationship NPC usually belongs to one twin, but the definition lists its twins (one or both), so an NPC can be shared later.

**RPG ties.** Charisma speeds up gains (rpg registers a gain modifier); gift items raise stats (`call rpg_gift`); relationship events can require stats (`ReqStat` in the event's conditions).

**Schedules.** NPCs follow schedules (where they are in each slot). The user has a detailed plan and will give it to the world/ session that builds schedules.

## Open questions
- Which characters get relationships.
- Character additions beyond rebuild #2.
