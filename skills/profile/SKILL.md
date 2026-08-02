---
name: profile
description: Project capability profile workflow.
---

# Project Profile

Use this skill when the user invokes `/profile`.

- `status`: run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" status` and report detected capabilities and context mode.
- `setup` or `refresh`: explain the proposed detected capabilities, ask for confirmation, then run the matching command.
- Do not change Codex approvals, sandboxing, network settings, or MCP policy.
- Profiles are project-local at `.codex/starter-profile.json` and guide task routing; they do not silently disable skills.
