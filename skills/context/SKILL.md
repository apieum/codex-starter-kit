---
name: context
description: Skill catalogue context workflow.
---

# Skill Catalogue Context

Use this skill when the user invokes `$context`.

- `status`: run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" status` and state that built-in tools and MCP schemas are outside this control.
- `compact`: explain that every starter skill remains available but its catalogue description becomes concise on the next startup; ask for confirmation, then run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" context compact`.
- `full`: explain that original starter-skill descriptions will be restored on the next startup; ask for confirmation, then run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" context full`.
- `truncate`: do not disable any skills automatically. Show that disabling skills reduces discoverability and ask the user to choose a project profile instead.
- This command is unrelated to Codex's built-in `/compact`, which compacts chat history.
