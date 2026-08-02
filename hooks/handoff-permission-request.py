#!/usr/bin/env python3
"""Codex PermissionRequest hook for handoff-friendly safe approvals."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import shlex
import sys


SHELL_TOOLS = {"Bash", "shell", "unified_exec", "exec_command"}
SAFE_RULES_PATHS = (
    Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "rules" / "default.rules",
    Path(__file__).resolve().parents[1] / "rules" / "default.rules",
)


def emit_decision(behavior: str, message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": behavior, "message": message},
                }
            },
            ensure_ascii=False,
        )
    )


def get_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
        arguments = tool_input.get("arguments")
        if isinstance(arguments, dict):
            for key in ("command", "cmd"):
                value = arguments.get(key)
                if isinstance(value, str):
                    return value
    return ""


def tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def first_program(tokens: list[str]) -> str:
    wrappers = {"command", "env", "nohup", "time", "timeout"}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token not in wrappers:
            return token.rsplit("/", 1)[-1]
        index += 1
        if token == "env":
            while index < len(tokens) and "=" in tokens[index] and not tokens[index].startswith("-"):
                index += 1
        elif token == "timeout" and index < len(tokens):
            index += 1
    return ""


def has_shell_metachar(command: str) -> bool:
    return any(token in command for token in (";", "&&", "||", "|", "$(", "`", ">", "<", "*", "?"))


def is_scoped_systemctl_kill(tokens: list[str]) -> bool:
    lower_tokens = [token.lower() for token in tokens]
    if "kill" not in lower_tokens:
        return False

    options_with_values = {"--kill-who", "--signal", "-s", "--job-mode"}
    targets: list[str] = []
    index = lower_tokens.index("kill") + 1
    while index < len(tokens):
        token = tokens[index]
        lower = lower_tokens[index]
        if lower in options_with_values:
            index += 2
            continue
        if lower.startswith("--kill-who=") or lower.startswith("--signal=") or lower.startswith("--job-mode="):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        targets.append(token)
        index += 1

    return bool(targets) and all(target.endswith(".scope") for target in targets)


def dangerous_reason(command: str) -> str | None:
    tokens = tokenize(command)
    if not tokens:
        return "Cannot safely parse the shell command; ask the user instead of auto-approving."

    lowered = " ".join(command.lower().split())
    if re.search(r"\b(drop\s+(database|schema|table)|truncate\s+table)\b", lowered):
        return "SQL destructive operation detected; require explicit user approval."

    program = first_program(tokens)
    lower_tokens = {token.lower() for token in tokens}
    if program in {"rm", "unlink", "rmdir", "shred", "srm", "sudo", "doas", "pkexec", "su"}:
        return f"{program} is intentionally not auto-approved."
    if program == "claude" and any(token in {"-p", "--print"} for token in tokens[1:]):
        return "Direct Claude print-mode commands are blocked. Use the Claude Companion plugin command path (`$claude:<mode> ...`) so Codex controls the review pack, tmux bridge, and outbox triage."
    if program in {"mkfs", "mkfs.ext4", "mkfs.xfs", "mkfs.btrfs", "mkswap", "wipefs", "fdisk", "parted", "sgdisk", "gdisk"}:
        return "Disk or filesystem mutation is intentionally not auto-approved."
    if program in {"shutdown", "reboot", "halt", "poweroff"}:
        return "Host power-management commands are intentionally not auto-approved."
    if program == "dd" and any(token.startswith("of=/dev/") or token == "of=/dev" for token in tokens):
        return "Raw device writes are intentionally not auto-approved."
    if program in {"npm", "pnpm", "yarn", "bun"}:
        if lower_tokens & {"publish", "deploy", "release", "changeset:publish", "release:patch", "release:minor", "release:major"}:
            return "Package publish/deploy/release commands require explicit user approval."
        if "audit" in lower_tokens and ("fix" in lower_tokens or "--fix" in lower_tokens):
            return "Package audit fix mutates dependencies and requires explicit user approval."
        if lower_tokens & {"prune", "cache"} and lower_tokens & {"clean", "delete", "clear"}:
            return "Package cache/prune cleanup requires explicit user approval."
        if lower_tokens & {"install", "i", "add"} and lower_tokens & {"-g", "--global"}:
            return "Global package installs require explicit user approval."
    if program == "git":
        if len(tokens) >= 3 and tokens[1] == "reset" and "--hard" in tokens:
            return "git reset --hard requires the preflight safety flow."
        if len(tokens) >= 2 and tokens[1] == "push" and lower_tokens & {"--force", "--force-with-lease", "-f"}:
            return "Force push requires explicit user approval."
        if len(tokens) >= 3 and tokens[1] == "branch" and "-D" in tokens:
            return "Forced branch deletion requires explicit user approval."
        if len(tokens) >= 3 and tokens[1] == "stash" and tokens[2] in {"clear", "drop"}:
            return "Stash deletion requires explicit user approval."
    if program in {"docker", "podman"}:
        if "prune" in lower_tokens or (len(tokens) >= 3 and tokens[1] == "volume" and tokens[2] in {"rm", "prune"}):
            return "Container prune or volume deletion requires explicit user approval."
    if program in {"kubectl", "oc"} and len(tokens) >= 2 and tokens[1] in {"delete", "drain", "cordon"}:
        return "Cluster destructive mutation requires explicit user approval."
    if program == "helm" and len(tokens) >= 2 and tokens[1] in {"uninstall", "delete", "rollback", "upgrade"}:
        return "Helm release mutation requires explicit user approval."
    if program in {"dropdb", "mysqladmin"} and "drop" in lower_tokens:
        return "Database deletion requires explicit user approval."
    return None


def read_allow_prefixes() -> list[list[str]]:
    prefixes: list[list[str]] = []
    text = ""
    for path in SAFE_RULES_PATHS:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            break
    for call in re.finditer(r"prefix_rule\((.*?)\)", text, re.DOTALL):
        body = call.group(1)
        if not re.search(r'decision\s*=\s*"allow"', body):
            continue
        match = re.search(r"pattern\s*=\s*(\[[^\]]+\])", body)
        if not match:
            continue
        try:
            pattern = ast.literal_eval(match.group(1))
        except (SyntaxError, ValueError):
            continue
        if isinstance(pattern, list) and all(isinstance(item, str) for item in pattern):
            prefixes.append(pattern)
    return prefixes


def command_matches_allow_prefix(command: str) -> bool:
    if has_shell_metachar(command):
        return False
    tokens = tokenize(command)
    if not tokens:
        return False
    for prefix in read_allow_prefixes():
        if tokens[: len(prefix)] == prefix:
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = str(payload.get("tool_name", ""))
    if tool_name not in SHELL_TOOLS:
        return 0

    command = get_command(payload)
    if not command:
        return 0

    reason = dangerous_reason(command)
    if reason:
        emit_decision("deny", reason)
        return 0

    if command_matches_allow_prefix(command):
        emit_decision("allow", "Auto-approved by starter-kit safe command rules for handoff development.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
