#!/usr/bin/env python3
"""Claude Code hook: block file edits outside the folder Claude was started in.

Each code subfolder's .claude/settings.json runs this before every Edit/Write.
Exit code 2 blocks the edit and shows Claude the message.
"""
import json
import os
import sys

data = json.load(sys.stdin)
tool_input = data.get("tool_input") or {}
path = tool_input.get("file_path") or tool_input.get("notebook_path")
if not path:
    sys.exit(0)

project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
target = os.path.realpath(os.path.join(data.get("cwd") or project, os.path.expanduser(path)))


def inside(root):
    return target == root or target.startswith(root + os.sep)


# Claude's own scratch files and memory notes don't count as leaving the folder.
claude_projects = os.path.realpath(os.path.expanduser("~/.claude/projects"))
is_memory_note = inside(claude_projects) and os.path.relpath(target, claude_projects).split(os.sep)[1:2] == ["memory"]

if inside(project) or is_memory_note or inside(os.path.realpath(f"/tmp/claude-{os.getuid()}")):
    sys.exit(0)

print(
    f"Blocked: {target} is outside {project}. This session may only edit files in that folder. "
    "Tell the user which change is needed elsewhere instead.",
    file=sys.stderr,
)
sys.exit(2)
