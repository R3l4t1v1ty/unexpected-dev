# computer/

The in-game computer and its apps, chiefly **GossipUp**, a fake social network. Comes back from the released game with a big rebuild. **Design with the user first (M5).**

## From the released game
- A desktop with program icons. Only GossipUp was implemented; `HomeworkFolder`, `Amazin` and `HentaiViewer` were stubs.
- GossipUp: feed with posts, likes and comments; friend profiles with photo albums; chats whose options can jump into story events.
- About 10 profiles, their posts and pictures were hardcoded in one 52 KB file, half of it data.
- Bugs: both twins shared one computer; a few broken parameter names; leftover styles from other prototypes.

## Direction
- **One computer per twin** (per-twin state: what's been seen, liked, read; chat progress).
- **App shell**: desktop, windows, app registry (`pc.register_app(id, name, screen, requires=None)`), so new apps are small and separate.
- **GossipUp as data**: profiles, posts, albums and chats are definitions; state holds only what changed. Chat options can start events (through the events API) and posts can unlock with `Req`s.
- **Notifications**: new posts or messages show a toast (`uix.notify`) and a badge.
- **Phone layout** from the start (the computer UI should feel natural on a phone screen).

## Open questions (design session)
- Which apps besides GossipUp.
- What GossipUp does beyond feed, profiles, albums and chats.
- How the computer is opened (an object in each twin's room, a HUD button, both?).
