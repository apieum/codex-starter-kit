#!/usr/bin/env python3
"""Project TDD harness hook and CLI."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tomllib
from typing import Any


STATE_FILE = ".gauntlet"
DISABLED_FILE = ".harness"
PROFILE_FILE = Path(".codex/starter-profile.json")
PROJECT_CAPABILITIES_FILE = Path(".codex/capabilities.toml")
PHASES = {"idle", "red", "green", "refactor"}
DELIVERY_COMMANDS = (
    ("git", "commit"),
    ("git", "push"),
    ("gh", "pr", "create"),
    ("gh", "pr", "merge"),
)


def emit_block(reason: str) -> None:
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": reason,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
            },
            ensure_ascii=False,
        )
    )


def emit_context(message: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"additionalContext": message}}, ensure_ascii=False))


def repo_root(start: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return start.resolve()
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return start.resolve()


def get_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        arguments = tool_input.get("arguments")
        if isinstance(arguments, dict):
            merged = dict(tool_input)
            merged.update(arguments)
            return merged
        return tool_input
    return payload


def get_workdir(payload: dict[str, Any]) -> Path:
    tool_input = get_tool_input(payload)
    for key in ("workdir", "cwd"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    return Path.cwd().resolve()


def get_command(payload: dict[str, Any]) -> str:
    tool_input = get_tool_input(payload)
    for key in ("command", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def changed_paths(root: Path) -> list[str]:
    commands = (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            paths.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(path for path in paths if path not in {STATE_FILE, DISABLED_FILE})


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def state_path(root: Path) -> Path:
    return root / STATE_FILE


def load_state(root: Path) -> dict[str, Any]:
    state = read_json(state_path(root))
    phase = state.get("phase", "idle")
    if phase not in PHASES:
        state["phase"] = "idle"
    state.setdefault("version", 1)
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    write_json(state_path(root), state)


def default_catalog_path() -> Path | None:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    runtime = codex_home / "starter-kit" / "capabilities.toml"
    if runtime.exists():
        return runtime
    repo_template = Path(__file__).resolve().parents[1] / "templates" / "capabilities.toml"
    if repo_template.exists():
        return repo_template
    return None


def load_catalog(root: Path) -> dict[str, dict[str, Any]]:
    path = root / PROJECT_CAPABILITIES_FILE
    if not path.exists():
        fallback = default_catalog_path()
        if fallback is None:
            return {}
        path = fallback
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    nested = data.get("capabilities", {})
    capabilities: dict[str, dict[str, Any]] = {}
    if isinstance(nested, dict):
        capabilities.update(
            {name: config for name, config in nested.items() if isinstance(name, str) and isinstance(config, dict)}
        )
    reserved = {"meta", "harness", "context", "profile", "capabilities"}
    capabilities.update(
        {
            name: config
            for name, config in data.items()
            if isinstance(name, str) and name not in reserved and isinstance(config, dict)
        }
    )
    return capabilities


def active_capability_names(root: Path, catalog: dict[str, dict[str, Any]]) -> list[str]:
    profile = read_json(root / PROFILE_FILE)
    names = profile.get("capabilities")
    if isinstance(names, list):
        return [name for name in names if isinstance(name, str) and name in catalog]
    return []


def list_values(config: dict[str, Any], key: str) -> list[str]:
    value = config.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def active_configs(root: Path) -> list[dict[str, Any]]:
    catalog = load_catalog(root)
    return [catalog[name] for name in active_capability_names(root, catalog)]


def roots_for(configs: list[dict[str, Any]], key: str) -> list[str]:
    roots: list[str] = []
    for config in configs:
        roots.extend(list_values(config, key))
    return sorted(set(root.strip("/") for root in roots if root.strip("/")))


def path_in_roots(path: str, roots: list[str]) -> bool:
    if not roots:
        return False
    normalized = path.strip("/")
    return any(normalized == root or normalized.startswith(root + "/") for root in roots)


def tracked_test_paths(root: Path, test_roots: list[str]) -> list[str]:
    if not test_roots:
        return []
    paths: set[str] = set()
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return []
    for line in result.stdout.splitlines():
        path = line.strip()
        if path and path_in_roots(path, test_roots) and (root / path).is_file():
            paths.add(path)
    return sorted(paths)


def test_snapshot(root: Path, test_roots: list[str]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for relative in tracked_test_paths(root, test_roots):
        content = (root / relative).read_bytes()
        snapshot[relative] = hashlib.sha256(content).hexdigest()
    return snapshot


def ensure_green_snapshot(root: Path, state: dict[str, Any], test_roots: list[str]) -> dict[str, Any]:
    if "test_snapshot" not in state:
        state["test_snapshot"] = test_snapshot(root, test_roots)
        save_state(root, state)
    return state


def command_fragments(command: str) -> list[list[str]]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return [[command]]
    fragments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in {";", "&&", "||", "|"}:
            if current:
                fragments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        fragments.append(current)
    return fragments


def is_delivery_command(command: str) -> bool:
    for fragment in command_fragments(command):
        lowered = [token.rsplit("/", 1)[-1] if index == 0 else token for index, token in enumerate(fragment)]
        for prefix in DELIVERY_COMMANDS:
            if tuple(lowered[: len(prefix)]) == prefix:
                return True
    return False


def quote_paths(root: Path, paths: list[str], pattern: str | None = None) -> str:
    selected = paths
    if pattern:
        selected = [path for path in paths if fnmatch.fnmatch(path, pattern)]
    return " ".join(shlex.quote(str(root / path)) for path in selected)


def render_command(command: str, root: Path, changed: list[str]) -> str:
    replacements = {
        "$PROJECT_ROOT": shlex.quote(str(root)),
        "$HARNESS_CHANGED_FILES": quote_paths(root, changed),
        "$HARNESS_CHANGED_PY": quote_paths(root, changed, "*.py"),
    }
    rendered = command
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered


def harness_commands(configs: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for config in configs:
        commands.extend(list_values(config, "harness"))
    return commands


def run_harness(root: Path, configs: list[dict[str, Any]], changed: list[str]) -> tuple[bool, str]:
    failures: list[str] = []
    for command in harness_commands(configs):
        rendered = render_command(command, root, changed)
        try:
            result = subprocess.run(
                ["bash", "-lc", rendered],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"$ {rendered}\nTimed out after 120 seconds.")
            continue
        if result.returncode != 0:
            tail = "\n".join(result.stdout.splitlines()[-20:])
            failures.append(f"$ {rendered}\n{tail}")
    return (not failures, "\n\n".join(failures))


def verify_role(root: Path) -> str | None:
    configs = active_configs(root)
    if not configs:
        return None
    changed = changed_paths(root)
    test_roots = roots_for(configs, "test_roots")
    source_roots = roots_for(configs, "source_roots")
    state = load_state(root)
    phase = state.get("phase", "idle")

    if phase == "red":
        outside_tests = [path for path in changed if not path_in_roots(path, test_roots)]
        if outside_tests:
            return "RED phase violation: only test files may change.\n" + "\n".join(outside_tests)
        return None

    if phase in {"green", "refactor"}:
        state = ensure_green_snapshot(root, state, test_roots)
        current = test_snapshot(root, test_roots)
        if current != state.get("test_snapshot", {}):
            changed_tests = sorted(set(current) ^ set(state.get("test_snapshot", {})))
            for path, digest in current.items():
                if state.get("test_snapshot", {}).get(path) != digest:
                    changed_tests.append(path)
            changed_summary = "\n".join(sorted(set(changed_tests)))
            return f"{phase.upper()} phase violation: tests are frozen in this phase.\n{changed_summary}"

    source_changed = [path for path in changed if path_in_roots(path, source_roots)]
    if source_changed and harness_commands(configs):
        ok, output = run_harness(root, configs, changed)
        if not ok:
            return "Harness failed:\n" + output
    return None


def handle_hook(payload: dict[str, Any]) -> int:
    root = repo_root(get_workdir(payload))

    command = get_command(payload)
    event = str(payload.get("hook_event_name") or payload.get("hookEventName") or "")
    tool_name = str(payload.get("tool_name", ""))

    if (root / DISABLED_FILE).exists():
        if event == "PreToolUse" and command and is_delivery_command(command):
            emit_block(
                "Delivery command refused: project harness is disabled by .harness. "
                "Re-enable it with $harness on and pass the harness before committing, pushing, or creating a PR."
            )
        else:
            emit_context(
                "Project harness is disabled by .harness. "
                "Do not claim completion; re-enable it with $harness on when debugging is finished."
            )
        return 0

    if event == "PreToolUse" and command and is_delivery_command(command):
        state = load_state(root)
        phase = state.get("phase", "idle")
        if phase in {"red", "green"}:
            emit_block(
                f"Delivery command refused: TDD cycle is still in {phase.upper()} phase. "
                "Finish GREEN and REFACTOR/DESIGN before committing or pushing."
            )
            return 0
        violation = verify_role(root)
        if violation:
            emit_block("Delivery command refused until harness passes.\n\n" + violation)
        return 0

    if event == "PostToolUse" or tool_name:
        violation = verify_role(root)
        if violation:
            print(violation, file=sys.stderr)
            return 2
    return 0


def set_phase(root: Path, phase: str) -> None:
    state = load_state(root)
    state["phase"] = phase
    if phase in {"idle", "red"}:
        state.pop("test_snapshot", None)
    if phase == "green":
        configs = active_configs(root)
        state["test_snapshot"] = test_snapshot(root, roots_for(configs, "test_roots"))
    save_state(root, state)


def status(root: Path) -> dict[str, Any]:
    catalog = load_catalog(root)
    configs = active_configs(root)
    state = load_state(root)
    return {
        "phase": state.get("phase", "idle"),
        "disabled": (root / DISABLED_FILE).exists(),
        "active_capabilities": active_capability_names(root, catalog),
        "harness_commands": harness_commands(configs),
        "state_file": str(state_path(root)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status")
    subparsers.add_parser("red")
    subparsers.add_parser("green")
    subparsers.add_parser("refactor")
    subparsers.add_parser("done")
    subparsers.add_parser("run")
    off_parser = subparsers.add_parser("off")
    off_parser.add_argument("reason", nargs="*", default=[])
    subparsers.add_parser("on")
    args = parser.parse_args(argv)

    if args.command is None:
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError:
            return 0
        return handle_hook(payload)

    root = repo_root(args.project.resolve())
    if args.command == "status":
        print(json.dumps(status(root), sort_keys=True))
        return 0
    if args.command in {"red", "green", "refactor"}:
        set_phase(root, args.command)
        print(json.dumps(status(root), sort_keys=True))
        return 0
    if args.command == "done":
        set_phase(root, "idle")
        print(json.dumps(status(root), sort_keys=True))
        return 0
    if args.command == "off":
        reason = " ".join(args.reason).strip() or "disabled by explicit user request"
        (root / DISABLED_FILE).write_text(reason + "\n", encoding="utf-8")
        print(json.dumps(status(root), sort_keys=True))
        return 0
    if args.command == "on":
        disabled = root / DISABLED_FILE
        if disabled.exists():
            disabled.unlink()
        violation = verify_role(root)
        if violation:
            print(violation, file=sys.stderr)
            return 2
        print(json.dumps(status(root), sort_keys=True))
        return 0
    if args.command == "run":
        violation = verify_role(root)
        if violation:
            print(violation, file=sys.stderr)
            return 2
        print(json.dumps(status(root), sort_keys=True))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
