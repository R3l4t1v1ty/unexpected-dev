# computer/ tasks

Milestone: **M5** (needs core, ui, events, characters).

## Context
From the released game:
- A desktop with program icons. Only GossipUp worked; HomeworkFolder, Amazin and HentaiViewer were stubs.
- GossipUp had a feed (posts, likes, comments), friend profiles with photo albums, and chats where some conversation options jumped into story events.
- About 10 profiles with posts and pictures were hardcoded in one 52 KB file.
- Bugs: both twins shared one computer, plus broken parameter names and leftover styles.

The user wants it back with a big rebuild. Direction (confirm in task 1):
- One computer per twin.
- An app shell with a registry.
- GossipUp as data definitions plus sparse per-twin state.
- Chat options that start events through the events API.
- Notifications and badges.
- A phone layout from the start.

## Uses
- core: `Definition`, registry, flags, `register_state`, `me()`, `Req…`, signals, `StateAction`, `asset`.
- ui: components, `uix.notify`, `uix.register_menu_tab` or `uix.register_hud_panel` (depending on how it opens).
- events: `events.start`, `ReqEventDone`.
- characters: `chars.get` (profile names, colours, portraits).

## Tasks
- [ ] 1. **(needs user) Design session.** Which apps, what GossipUp does, how the computer opens. Rewrite this Context with the result.
- [ ] 2. **App shell.** `call pc_open` (current twin's computer), desktop, windows, `pc.register_app(id, name, screen, requires=None)`, per-twin state section. Done when: a test app opens and closes on PC and under phone emulation.
- [ ] 3. **GossipUp data.** Definitions for profiles, posts, albums, chats (with options); unlock rules as `Req`s; per-twin state (seen, liked, chat progress). Done when: tests cover unlocking and state across save/load.
- [ ] 4. **GossipUp screens.** Feed, profile, album viewer, chat; phone layout. Done when: test content browsable on both layouts.
- [ ] 5. **Chats that start events.** A chat option can start an event via `events.start` and close the computer cleanly. Done when: a test chat starts a test event and returns.
- [ ] 6. **Notifications.** New posts/messages → `uix.notify` and an unread badge; signal `pc_notification`. Done when: test.
- [ ] 7. **Publish.** Print the computer section for game/code/CLAUDE.md.

## API to publish
`call pc_open`, `pc.register_app`, GossipUp definition functions (shape decided in tasks 1–3), signal `pc_notification`.
