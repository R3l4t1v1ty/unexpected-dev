# factions/

Factions, reputation and quests: part of both the RPG and the sandbox. Designed with the user on 2026-10-23. This was in characters/ in the first plan; it moved to its own folder because it ties into rpg (shops, recipes), adventure (quest goals) and world (faction locations).

## Factions
Seven on the world graph, each with its own location:

| Faction | Where | Opened by meeting |
|---|---|---|
| Alchemy Lab | off Ivory Paw, Henyutamei | Rina |
| Dim Hand Guild Outpost | off Underground, Henyutamei | Merce |
| Vampire Lair | off Twilight Allure, Henyutamei | Emi |
| Inya's Hideout | Hell Citadel | (not decided) |
| Throne | Hell Citadel | (not decided) |
| Eiko's Hideout | Order HQ | (not decided) |
| Council | Order HQ | (not decided) |

- Meeting the faction's character opens the faction (in data: a `Req`, e.g. `ReqKnown("rina")`).
- No rivals: gaining reputation with one faction never costs reputation with another.

## Reputation
- **Per twin** (the first plan had it shared).
- Tiers: the old game's 5 tiers from "unfriendly" to "exalted", thresholds 100/300/600/1000, cap 1500, kept as tunable data. Names and numbers get confirmed when building.
- Earned mainly through quests; charisma raises gains (factions reads `rpg.stat("cha")`).

## What factions do for you (first version)
Unlocked by reputation tier:
- **Shop access**: shop stock gated with `ReqRep` (rpg shops).
- **Discounts**: a price modifier registered with `rpg.register_price_modifier`.
- **Recipes**: quest or tier rewards call `rpg.learn_recipe`.
- **Services**: actions at the faction's location gated with `ReqRep` (content).

## Quests
Faction quests ask the twin to do something in adventure mode, make something, collect something, find something out from someone, and so on.
- Objective kinds: have items (`rpg.has`), craft an item (`item_crafted`), an adventure goal (an adventure signal: boss defeated, place reached, thing found), something learned from someone (content marks it done), any `Req`.
- Rewards: reputation, items, money, recipes.
- Per twin: available → active → done; a quest is one-time or repeatable.
- Details for the build session to settle with the user: how quests are offered and handed in, how repeatable quests reset, where the quest log lives (game-menu tab or HUD panel).

## API shape (adjust while building)
`fac.add(id, name, location, opens=Req)`, `fac.get(id)`, `fac.is_open(faction)`, `fac.rep(faction, twin=None)`, `fac.add_rep(faction, amount)`, `fac.tier(faction)`, `ReqRep(faction, tier)`, `fac.add_quest(...)`, `fac.start(quest)`, `fac.complete_objective(quest, objective)`, `fac.turn_in(quest)`, `fac.quest_state(quest)`, `ReqQuest(quest, state)`. Signals `faction_opened(twin, faction)`, `reputation_changed(twin, faction, value)`, `quest_started(twin, quest)`, `quest_completed(twin, quest)`.

## Milestone
M3, after rpg's items, recipes and shops. Adventure goals in quests get wired in M4.
