# Old versions

Notes from reading the three earlier projects' code (story folders and assets skipped), so later sessions don't need to re-read them. Paths are on the Windows desktop, seen from WSL:

| Project | Path | What it is |
|---|---|---|
| Released game | `/mnt/c/Users/H2PHO3/Desktop/_RPY proj/_Unexpected Core - android/game/script/` | 6 releases, ~223 .rpy files. Systems in `core/`, UI in `screens/`, story in `story/` |
| Rebuild #2 | `/mnt/c/Users/H2PHO3/Desktop/_RPY proj/Unexpected/game/code/` | ~73 .rpy files, more elaborate systems, no story wired in; stalled while connecting sandbox objects to content |
| Adventure prototype | `/mnt/c/Users/H2PHO3/Desktop/_RPY proj/ActionAdventureMode/game/code/` | Top-down mode, Godot math port, map editor; has its own CLAUDE.md |

A locked session can't read these paths. If a task needs old code, port it from a session started at the project root, or copy the needed file into the folder first.

## Worth keeping, by system

**World** (rebuild #2 `core/world/`, released `core/rpg/world/`)
- Spaces → places → locations, `SBXMove` exit buttons with images derived from keys, `SBXMenu` popups that group up to 4 exits, favourite-location fast travel (4 slots).
- Interactables with a z-layer (0–9), position, several verbs (`labels`) shown as a floating icon menu, bg/fg add-on images, per-twin requirements, Tab to highlight everything clickable for 1.5 s.
- Character "circles" on the map showing where NPCs and pending events are, with teleport.
- Problem: both versions were trees (each location linked only to its parent; `add_location(place, parent, key, …)`). Location requirements in rebuild #2 were stored but never checked.

**Twins** (rebuild #2 `core/unexpected.rpy`)
- `stories{"ayumu","nemu"}` each with their own calendar, event manager and RPG character; `curr/other`; swap via a confirm dialog → `swap_label` → `block_rollback()` → back to the sandbox.
- Story-swap screen with each twin's completion % and a mirage-shader hover effect.

**Events** (rebuild #2 `core/events/event_py.rpy`)
- `StoryEvent`: name, characters, weight (for completion %), triggers, `about[before, after]` texts, label `event_<key>_label`.
- Event lines: events of a line chain automatically in declaration order (the line key is the event key without its `_N` suffix); `connect()` links across lines.
- Triggers: location (partial key tuple), time, item. Per-character "event book" in the encyclopedia.
- Problems: AND logic never implemented ("TBD"), item triggers empty, time trigger compared a list to an int, several wrong location keys.

**Characters** (rebuild #2 `core/encyclopedia/`)
- `Chara`: key, surname, colour, card, factions, `about` per outfit, info, outfits; builds 4 `Character` objects (normal, thought, unknown "???", one more).
- Encyclopedia: card grid filtered by faction; character page with outfit box, zoom, relationship bars, event book linking to event lines.
- Relationship: attraction, friendliness, commitment (0–100), relationship type picked by linear inequalities.
- Problems: `introduced` flag inverted, `get_type()` can return None and crash the page, UI state (zoom, outfit) stored on saved objects, factions page a stub.

**RPG** (both; to be rebuilt)
- Ideas: stats int/dex/str/cha with derived values, 6 gear slots, 20-slot inventory, 4 currencies, drag-and-drop equip with tooltips, reputation tiers (unfriendly…exalted, thresholds 100/300/600/1000, cap 1500), a shop with tabs.
- In practice almost nothing was wired: no story code changed XP or reputation; combat classes were sketches with inverted hit and crit checks.

**Gallery** (released `core/gallery/`, rebuild #2 `core/gallery/`): the most complete system. Reward gallery (event CGs + achievement pictures, filtered by character) and L.E.W.D. (per-event picture sets mixing images and looping webm, unlocked when the event is done). Keep the data model.

**Achievements**: groups → achievements → goal objects (`goal_done`, `progress_text`), claimed by the player, a claim unlocks a gallery picture. Only time and guessing-game goals existed. Rebuild fully.

**Audio** (released `core/music/music.rpy`): `MusicManager` with ambient/vibe/stage keys, crossfading between two channels (`music1`, `music2`), event tracks, sandbox music by time of day. 308 story calls used it, so its API was right. Problems: an init-time global, not saved and not rollback-safe.

**Loading screens**: `FakeLoadingManager`, a deliberate fake loading screen (random 1–6 s, random background, tips you can cycle, click to continue), switchable with `persistent.fake_loading`.

**Transforms**: camera-style zoom, slide, slide+zoom, rotate, blur; `screen_shake`; a reduced-motion ("dynamic effects") toggle that swaps every transform for a no-op. Problem: the swapped transforms were save `default`s, so the persistent setting was ignored on new game and load.

**Shader**: `mirage.story_swap` (noise distortion, desaturate, tint) in a `MirageImage` displayable. Problem: renders its noise texture in every constructor, some created inline in screens.

**Textbox**: custom say screen, 3 skins (Simple, Side-Fade, Fancy), persistent sliders (opacity, width, height, text size, outlines) each with Reset.

**Computer** (released `core/computer/computer.rpy`, 52 KB): desktop with program icons; only GossipUp implemented: feed with posts, likes and comments, friend profiles with photo albums, chats whose options can jump into events. Both twins shared one computer (a bug).

**Minigames**: loop-rotation puzzle (`LoopyLoopLoop` with a random tileset generator; its screen lived in story code) and rune trace (trace a path from Start to End without touching the symbol; hover-based, so unreliable on touch) with a `VFXFireTrail` particle displayable.

**UI**: main menu with mouse parallax and floating items; game menu hub (Characters, Events, Gallery, Achievements); rebuild #2's data-driven tab registry (`UnexpectedNavigation` with check functions) and `menu_layout` wrapper; quick menu with Story and Game buttons, touch variant.

**Adventure prototype** (`ActionAdventureMode`)
- Godot 4.4 math ports (`Vector2`, `Vector2i`, `Rect2`, `Rect2i`, `Transform2D`), Godot-style `AdventureInput` actions, `ready/update/queue_free` lifecycle.
- One `renpy.Displayable` with a fixed 60 Hz tick accumulator; Camera2D-like camera with smoothing and limits.
- `CollisionGrid`: terrain mask from `collision.png`, cell-hashed static solids, swept AABB (X then Y) so nothing tunnels; A* plus string pulling; click-to-move and click-to-interact.
- `@adventure_type` object registry and `editor_properties` driving a ~2000-line in-game editor (rooms browser, mask painting with undo, object placement, property panels, playtest).
- Rooms placed side by side in one coordinate space with seamless edges; doors for interiors; per-twin `permanent` progress; minimap.
- Calling a Ren'Py label from inside the mode and resuming afterwards (`renpy.call(label, from_current=True)` plus re-running the `run()` statement).

## Mistakes not to repeat

- **Pickling the whole game into saves** (`default game = deepcopy(base)`), then hand-writing `AfterLoadManager.merge()` and one-off patches each version (released), or never reaching old saves at all (rebuild #2). The adventure prototype pickled its whole displayable, maps and art.
- **Display names as keys** ("Ayumu's Room", "The Art Club 2") that doubled as image paths, label names and save keys.
- **Hardcoded twin pairs**: `{"ayumu": …, "nemu": …}` literals everywhere, `if name == "nemu"`, `isinstance(game.story, AyumuStory)`, near-identical Ayumu/Nemu classes.
- **Jump-based content flow**: content started with `call hide_ui` and ended with `jump sandbox_update_label` (300 places); `renpy.checkpoint()` on every sandbox loop.
- **Giant screens**: the released HUD was one 2,300-line screen with the inventory and character panels copy-pasted three times.
- **Mutable default arguments** (`labels=[]`, then used as a dict).
- **Mixed indexing**: time slots 0–3 in one place and 1–4 in another.
- **Weekends always skipped**, so day-6/7 triggers never fired.
- **Globals without `default`** (`evflags`, `just_ended_event`), init-time mutable globals (`musicM`).
- **Per-frame allocations** in the adventure prototype (new `Transform`s and `Solid`s every frame, full sort every frame, redraw while paused) and editor screens scanning the disk on every evaluation.
- **Speculative code** never wired up: physics colliders, combat effects, talents, quests, a reputation curve, 4 currencies with no use. Build what a task needs.
