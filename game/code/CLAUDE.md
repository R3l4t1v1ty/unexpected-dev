# Unexpected — game code

Ren'Py 8.5 visual novel. All game code lives in `game/code/`. Each subfolder owns one part of the codebase and has its own CLAUDE.md with the rules for that part.

<!-- Update this table if folders change. My one-line guesses below come from the folder names; fix them. -->
| Folder | Owns |
|---|---|
| `core/` | Shared systems the rest of the game builds on |
| `story/` | The story: labels, dialogue, scene flow |
| `dev/` | Developer and debug tools, not part of the released game |

`script.rpy`, `screens.rpy`, `gui.rpy` and `options.rpy` are Ren'Py's standard project files.

## How Ren'Py treats these folders
- Ren'Py loads every `.rpy` file under `game/`, in every subfolder. Folders only organize the code; there are no imports between them.
- Labels, screens, images and `define`/`default` names are global across all folders. A duplicate name either errors or silently replaces the other one, so check a name isn't taken before adding it.
- `init` code runs by priority, then by file path. If one file needs another file's init code to run first, give it an explicit priority (`init 1 python:`) rather than relying on file names.
- Never edit `.rpyc` files or anything in `game/cache/`. Ren'Py generates them.

## Working in one folder
When Claude is started inside one subfolder, it can only read and edit files in that folder. If a task needs a change in another folder, stop and say which file and what change, instead of working around the limit.

Every folder under `game/code/` gets its lock and a starter CLAUDE.md from `.claude/sync-folders.py`. It runs by itself whenever `claude` starts from a terminal inside the project. After creating a folder in an unlocked session, run `python3 .claude/sync-folders.py` from `game/code/`. To change the lock for all folders, edit `.claude/folder-template/settings.json`, not the copies.

## Shared rules
<!-- Project-wide rules go here: naming style, comment style, which folder may use which, etc.
     Also list anything from core/ that story/ or dev/ may call (functions, screens, variables),
     because a session locked into story/ can't open core/ to look. -->
