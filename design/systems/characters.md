# characters/

Characters, the encyclopedia, factions and reputation, and the relationship system.

## Characters (rebuild #2 baseline)
`Chara` definitions: id, name, surname, colour, encyclopedia card, factions, outfits, `about` text per outfit, info. Each builds the `Character` objects story needs:
- normal speech
- thought (`show_thought=True`; the say screen gets `thought=True`)
- unknown ("???" until the twin has been introduced)
- one more variant if needed (rebuild #2 had four)

Per twin: introduced or not, outfits seen. The exact way story refers to speakers (store names like `hana`) is decided in characters task 1 and written into game/code/CLAUDE.md, because story/ will rely on it.

The user will add more to characters later.

## Encyclopedia (rebuild #2, kept)
A game-menu tab: card grid filtered by faction; a character page with outfit box, zoom, relationship bars, and the event book (provided by events through `chars.register_page_section`). Zoom and selected outfit are screen variables, not saved data (rebuild #2 stored them on saved objects).

## Factions and reputation
Shared between twins. Reputation tiers (old values: 5 tiers from "unfriendly" to "exalted", thresholds 100/300/600/1000, cap 1500); revisit with the RPG design.

## Relationships (new, core of world-mode play)
Chosen NPCs have their own storylines in world mode, driven by relationship progress. Values are per twin. Design comes later with the user; until then a skeleton with the old three stats (attraction, friendliness, commitment, 0–100), `chars.rel`, `chars.add_rel`, `ReqRel`, and the `relationship_changed` signal, so world, events and rpg can be built against it.

## Open questions
- Relationship system design.
- Character additions beyond rebuild #2.
