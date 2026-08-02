---
name: profile
description: Project capability profile workflow.
---

# Project Profile

Use this skill when the user invokes `$profile`.

- `status`: run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" status` and report effective, detected, user, and disabled capabilities plus context mode.
- `setup` or `refresh`: explain the proposed detected capabilities, ask for confirmation, then run the matching command. This writes `.codex/starter-profile.json` and `.codex/capabilities.toml` while preserving user additions/removals.
- `add cap1 cap2`: ask for confirmation, then run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" add cap1 cap2`. User-added capabilities are stored in `user_capabilities` and survive refresh.
- `remove cap1 cap2`: ask for confirmation, then run `python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/project_profile.py" remove cap1 cap2`. Removed capabilities are stored in `disabled_capabilities` so auto-detection does not re-enable them.
- Do not change Codex approvals, sandboxing, network settings, or MCP policy.
- Profiles are project-local at `.codex/starter-profile.json`; capability commands live in `.codex/capabilities.toml`. They guide task routing and the harness; they do not silently disable skills.
