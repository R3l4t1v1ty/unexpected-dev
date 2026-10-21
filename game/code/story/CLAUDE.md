# story/

## Purpose
The story: dialogue, scenes and story content (events' labels, NPC and object interactions, the real characters, events, shops and maps' dialogue). Not started yet; it begins after the game systems are built.

## Rules
- Use only the public API listed in game/code/CLAUDE.md. A session here can't see the system folders. If something is missing, say which API is needed instead of working around it.
- Content labels come from `core.label_for(...)` and must `return`; never `jump` back into the world.
- Further rules (file layout per twin/arc, label naming, writing style, character voices) are decided when story work starts.

@TASKS.md
