# minigames/

Small games called from content. Two carry over from the released game, possibly improved; more can be added on the same protocol.

## Protocol
`call minigame(kind, puzzle_id)` → `_return` is `"win"`, `"lose"` or `"skip"`. Each kind registers its screen: `mini.register(kind, screen)`. A skip option (accessibility; `persistent.mini_skip_allowed`, toggled in preferences) lets players pass any minigame. Puzzles are definitions (seed, size, difficulty…).

## Loop puzzle (from the released game)
Rotate tiles until every pipe connects into closed loops. `LoopyTilesetGenerator` grew a random ~50%-filled grid; tile shapes 0–4; `is_solved()` checked it. Its screen lived in story code; now it lives here.

## Rune trace (from the released game)
Trace a path from a Start circle to an End circle without touching the rune symbol; a fire-trail particle effect (`VFXFireTrail`, a custom displayable with trails and particles) follows the pointer. It ran entirely on mouse hover, which is unreliable on touch. New version: drag-based (press on Start, drag to End), with the same feel on PC; the effect is a cached displayable.

## Open questions
- Improvements beyond touch support, new minigames.
