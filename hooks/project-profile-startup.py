#!/usr/bin/env python3
"""Emit a small project-profile health message at Codex session start."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def emit(message: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": message}}))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}
    root = Path(str(payload.get("cwd") or Path.cwd()))
    profile_path = root / ".codex" / "starter-profile.json"
    if not profile_path.exists():
        emit(
            "Project profile is not configured. Ask whether this project should enable auto-detection, "
            "then use $profile setup after confirmation."
        )
        return 0
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        emit("Project profile is invalid. Use $profile status and repair it before relying on capability guidance.")
        return 0
    capabilities = ", ".join(profile.get("capabilities", ["lite"]))
    context_mode = profile.get("context_mode", "compact")
    harness_path = root / ".gauntlet"
    harness = "disabled" if (root / ".harness").exists() else "enabled"
    if harness_path.exists():
        try:
            phase = json.loads(harness_path.read_text(encoding="utf-8")).get("phase", "idle")
        except (OSError, json.JSONDecodeError):
            phase = "invalid"
    else:
        phase = "idle"
    emit(
        f"Project profile: capabilities={capabilities}; skill catalogue mode={context_mode}; "
        f"harness={harness}, phase={phase}. "
        "Use $profile status, $context status, or $harness status to inspect it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
