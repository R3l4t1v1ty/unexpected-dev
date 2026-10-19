#!/usr/bin/env python3
"""Give every folder under game/code/ (at any depth) its own Claude setup.

Each folder gets:
  .claude/settings.json  the folder lock, kept identical to .claude/folder-template/settings.json.
                         Edit the template, not the copies: this script overwrites them.
  CLAUDE.md              a starter file from the template, only if the folder has none.

Safe to run any time. Prints only what it changed.
"""
import os

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(CODE, ".claude", "folder-template")
SKIP = {"__pycache__"}


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


settings = read(os.path.join(TEMPLATE, "settings.json"))
claude_md = read(os.path.join(TEMPLATE, "CLAUDE.md"))

for root, dirs, _files in os.walk(CODE):
    dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP)
    if root == CODE:
        continue
    folder = os.path.relpath(root, CODE).replace(os.sep, "/")

    settings_path = os.path.join(root, ".claude", "settings.json")
    current = read(settings_path)
    if current != settings:
        write(settings_path, settings)
        print(f"[claude] {'updated lock' if current else 'locked'}: {folder}/")

    md_path = os.path.join(root, "CLAUDE.md")
    if not os.path.exists(md_path):
        write(md_path, claude_md.replace("{folder}", folder))
        print(f"[claude] added CLAUDE.md: {folder}/")
