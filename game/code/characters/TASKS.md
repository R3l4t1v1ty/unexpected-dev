# characters/ tasks

Milestone: **M2**.

## Context
Baseline is rebuild #2's design:
- `Chara`: id, name, surname, colour, encyclopedia card image, factions, outfits, `about` text per outfit, info. Builds `Character` objects: normal; thought (`Character(..., show_thought=True)` passes `thought=True` to the say screen); unknown (shows "???" until the current twin has been introduced); a fourth variant only if a need appears.
- About 50 characters in the old game. 53 were declared in rebuild #2.
- Encyclopedia: card grid filtered by faction; character page with outfit box, zoom, relationship bars, event book.
- Rebuild #2 bugs to avoid: `introduced` was inverted; `Relationship.get_type()` could return None and crash the page; zoom/outfit were stored on saved objects; the factions page was a stub.
- Factions and reputation are shared between twins. Old reputation: 5 tiers from "unfriendly" to "exalted", thresholds 100/300/600/1000 XP, cap 1500 (revisit with the RPG design).
- **Relationships** are new and the core of world-mode play: chosen NPCs have their own world storylines driven by relationship progress, per twin. The design comes later with the user. Until then: a skeleton with three stats (attraction, friendliness, commitment, 0–100).
- The user will add more character features later.

## Uses
- core: `Definition`, registry, flags (per twin), `Req…`, signals, `asset`, `StateAction`.
- ui: `uix.register_menu_tab`, components, phone layout rules.

## Tasks
- [ ] 1. **Characters and speakers.** `chars.add(...)`, `chars.get(id)`; build the Character variants; decide how story names speakers (e.g. a store name per character such as `hana`, and how thought/unknown variants are written in dialogue), write that into the published API. Done when: a test label speaks with every variant.
- [ ] 2. **Introductions.** `chars.introduce(id)` (current twin), `chars.known(id, twin=None)`, `ReqKnown(id)`; unknown speaker shows "???" until introduced; signal `character_introduced`. Done when: test shows the name change after introduction, per twin.
- [ ] 3. **Factions and reputation.** `chars.add_faction(id, name)`, `chars.rep(faction)`, `chars.add_rep(faction, amount)`, tier names; signal `reputation_changed`. Done when: test.
- [ ] 4. **(needs user) Relationship design.** Talk through the relationship system with the user (values or stages, NPC storylines in world mode, ties to events and RPG) and write the result into this file's Context.
- [ ] 5. **Relationship skeleton.** `chars.rel(id, stat, twin=None)`, `chars.add_rel(id, stat, amount)` (clamped), `ReqRel(id, stat, min)`, signal `relationship_changed`. Replace with the real design after task 4. Done when: test.
- [ ] 6. **Encyclopedia.** `screen chars_encyclopedia` (grid, faction filter), `screen chars_page(char_id)` (outfits, zoom, relationship bars, sections from `chars.register_page_section(id, screen)`); phone layout; register the Characters tab. Done when: works on PC and under phone emulation with test characters.
- [ ] 7. **NPC storyline hook.** After tasks 4 and events' design: how a relationship storyline exposes its next step to world (marker provider, `Req`s). Done when: agreed design implemented with a test NPC.
- [ ] 8. **Publish.** Print the characters section for game/code/CLAUDE.md.

## API to publish
`chars.add`, `chars.get`, speaker names, `chars.introduce`, `chars.known`, `ReqKnown`, `chars.add_faction`, `chars.rep`, `chars.add_rep`, `chars.rel`, `chars.add_rel`, `ReqRel`, `chars.register_page_section`, screens `chars_encyclopedia`, `chars_page`, signals `character_introduced`, `relationship_changed`, `reputation_changed`.
