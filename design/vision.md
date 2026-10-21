# Vision

## The game
Unexpected is a visual novel / sandbox game, 8+ hours long, with two protagonists: the twins **Ayumu** (brother) and **Nemu** (sister). The player switches between them; each has their own storyline, time, location and progress in a shared world.

This rebuild is the third attempt at the codebase:
1. The released game (6 releases), `_Unexpected Core - android`.
2. A first rebuild with more elaborate systems that stalled before any content was wired in, `Unexpected`.
3. This one: plan first, save only state, stable ids, one folder per system, PC and Android from the start.

## Two modes

**World mode** (the sandbox). The world is a graph of **locations**, the smallest unit. Locations are grouped into **places** (Home, School, Park), and places into **spaces** (Town). Spaces and places are only for grouping and maps. Each location shows a background for the time of day, buttons for its connections, and clickable **objects** and **NPCs**. Clicking one opens its actions (chat, look, …), which run content. The world will grow a lot: two new whole spaces and connections between spaces.

The core of world-mode play is the **relationship system**: chosen NPCs have their own storylines in world mode, driven by relationship progress.

**Adventure mode** (new). A top-down, RPG Maker–like mode, entered from the world. Painted rooms, free movement, NPCs and objects to interact with, doors and room edges, combat. Maps are made in a map maker.

## Systems

| System | Folder | Status | Notes |
|---|---|---|---|
| State, ids, twins, time, saves | `core/` | Changed | Saves hold only flags; stable ids; days without weeks |
| World | `world/` | Kept, grows | Same model, but a real graph with cross-space connections |
| Characters + encyclopedia | `characters/` | Kept (rebuild #2 baseline) | More additions to come |
| Relationships | `characters/` | **New** | Core of world-mode play; design later |
| Events | `events/` | Changed | Rebuild #2 as reference, deeper changes later |
| RPG | `rpg/` | **Full rebuild** | Combat, stat checks, items/gear/shops, progression; most important system |
| Physics | `physics/` | **New** (light Godot port) | Pure Python; used by adventure mode and maybe minigames |
| Adventure mode + map maker | `adventure/` | **New** | Reference: ActionAdventureMode prototype |
| Computer + GossipUp | `computer/` | Big rebuild | Fake social network; chats can start events |
| Minigames | `minigames/` | Kept, improved | Loop puzzle, rune trace (drag-based for touch) |
| Gallery | `progress/` | Kept | Per save |
| Achievements | `progress/` | Full rebuild | Per save |
| Music, loading screens, camera transforms, shader | `fx/` | Kept, improved | |
| UI: menus, textbox, HUD, game-menu tabs | `ui/` | Kept / changed | PC + phone + tablet layouts |
| Debug tools, tests | `dev/` | New | Never ships |
| Story | `story/` | Later | |
| Content-preference gate | — | **Dropped** | |

## Platforms
PC (Windows, Linux, Mac) and Android, with layouts for PC, phone and tablet using Ren'Py's built-in screen variants. See architecture.md §8 and §12.

## What must be better this time
- **Saves survive updates** without hand-written merge code: definitions never go into saves; only flags do.
- **Ids are stable** and separate from display names, image paths and label names.
- **No giant files**: the HUD is split into one file per panel, data lives in tables.
- **Unfinished code doesn't hide crashes**: every system has test labels, and dev/ has a validator.
- **Touch works**: drag alternatives, no hover-only interactions.
