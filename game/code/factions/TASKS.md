# factions/ tasks

Milestone: **M3** (after rpg tasks 4, 7 and 8). Adventure goals in quests: **M4**.

## Context
Designed with the user on 2026-10-23. Factions are part of both the RPG and the sandbox.

**Factions** (seven, from the user's world graph; each has its own location):

| Faction | Where | Opened by meeting |
|---|---|---|
| Alchemy Lab | off Ivory Paw (Henyutamei); also a craft station | Rina |
| Dim Hand Guild Outpost | off Underground (Henyutamei); has a shop | Merce |
| Vampire Lair | off Twilight Allure (Henyutamei) | Emi |
| Inya's Hideout | Hell Citadel | not decided |
| Throne | Hell Citadel | not decided |
| Eiko's Hideout | Order HQ | not decided |
| Council | Order HQ | not decided |

- Meeting the faction's character opens it: the faction's `opens` is a `Req` such as `ReqKnown("rina")`.
- No rival factions.

**Reputation.**
- Per twin.
- Tiers: the old game's 5 tiers from "unfriendly" to "exalted", thresholds 100/300/600/1000, cap 1500, as data. Confirm names and numbers with the user in task 2.
- Earned mainly through quests. Charisma raises gains (`rpg.stat("cha")`, factor from rpg).

**What factions give** (first version), by tier:
- shop access (`ReqRep` in rpg shop stock)
- discounts (`rpg.register_price_modifier`)
- recipes (`rpg.learn_recipe` as rewards)
- services (content at the faction location, gated by `ReqRep`)

**Quests.** Faction quests ask the twin to do something in adventure mode, make something, collect something, find something out from someone, etc.
- Objective kinds: have items (`rpg.has`), craft an item (signal `item_crafted`), an adventure goal (adventure signal: boss defeated, place reached, thing found), something learned (content calls `fac.complete_objective`), any `Req`.
- Rewards: reputation, items, money, recipes.
- Per twin: available → active → done; one-time or repeatable.
- To settle with the user in task 3: how quests are offered and handed in, how repeatable quests reset, where the quest log lives (game-menu tab or HUD panel).

## Uses
- core: `Definition`, registry, `register_state`/`state`, `me()`, `Req…`, signals, `StateAction`.
- rpg: `rpg.give/take/has`, `rpg.add_money`, `rpg.learn_recipe`, `rpg.stat`, `rpg.register_price_modifier`, signals `item_changed`, `item_crafted`.
- characters: `ReqKnown`.
- adventure (M4): its quest-goal signals.
- ui: `uix.register_menu_tab` or `uix.register_hud_panel`, components, `uix.notify`.

## Tasks
- [ ] 1. **Factions.** `fac.add(id, name, location, opens=Req)`, `fac.get`, `fac.is_open(faction)`; opening is checked when the `opens` Req first holds (on `character_introduced` and on load); signal `faction_opened`. Done when: `factions_test.rpy` opens a test faction by introducing its character, per twin.
- [ ] 2. **Reputation.** `fac.rep(faction, twin=None)`, `fac.add_rep(faction, amount)` (charisma factor, cap), `fac.tier(faction)`, tier names, `ReqRep(faction, tier)`; signal `reputation_changed`. Done when: tests, including the cap and tier changes.
- [ ] 3. **(needs user) Quests.** Settle the open points above with the user, then: `fac.add_quest(...)` with objectives and rewards, `fac.start`, `fac.complete_objective`, `fac.turn_in`, `fac.quest_state`, `ReqQuest(quest, state)`, progress from signals, repeatable quests; signals `quest_started`, `quest_completed`. Done when: a test quest with an item objective and a "learned" objective completes and pays out.
- [ ] 4. **Perks.** The price modifier for discounts; recipe rewards; an example `ReqRep`-gated shop item and service. Done when: prices drop at a tier in a test shop.
- [ ] 5. **Quest log.** Screen for active and finished quests per twin; phone layout. Done when: works on PC and under phone emulation.
- [ ] 6. **(M4) Adventure goals.** Objectives fed by adventure's signals. Done when: a test quest completes from a test adventure.
- [ ] 7. **Publish.** Print the factions section for game/code/CLAUDE.md.

## API to publish
`fac.add`, `fac.get`, `fac.is_open`, `fac.rep`, `fac.add_rep`, `fac.tier`, `ReqRep`, `fac.add_quest`, `fac.start`, `fac.complete_objective`, `fac.turn_in`, `fac.quest_state`, `ReqQuest`, the quest log screen, signals `faction_opened`, `reputation_changed`, `quest_started`, `quest_completed`.
