---
name: profile
description: Project capability profile workflow.
---

# Project Profile

Use this skill when the user invokes `$profile`.

- `status`: run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" status` and report detected capabilities and context mode.
- `setup` or `refresh`: explain the proposed detected capabilities, ask for confirmation, then run the matching command. This writes `.codex/starter-profile.json` and `.codex/capabilities.toml`.
- Do not change Codex approvals, sandboxing, network settings, or MCP policy.
- Profiles are project-local at `.codex/starter-profile.json`; capability commands live in `.codex/capabilities.toml`. They guide task routing and the harness; they do not silently disable skills.
