# computer/

## Purpose
The in-game computer: a desktop with apps, chiefly GossipUp (a fake social network with feed, profiles, albums and chats that can start story events). One computer per twin.

## Rules
- Namespace `pc`; screens and labels `pc_*`; GossipUp names `pc_gossip_*` / `pc.gossip_*`.
- Classes at init -300, data and screens at 0, registration at 100.
- Apps register with `pc.register_app`; the shell never hardcodes an app.
- Profiles, posts, albums and chats are definitions; per-twin state stores only what changed (seen, liked, chat progress).
- Starting an event from a chat goes through the events API, never by jumping to a label.
- Screen-driven state changes use `core.StateAction`.

@TASKS.md
