#!/usr/bin/env python3
"""Manage project capability hints and starter-skill catalogue descriptions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tomllib
from typing import Any


PROFILE_PATH = Path(".codex/starter-profile.json")
PROJECT_CAPABILITIES_PATH = Path(".codex/capabilities.toml")
CONTEXT_MODES = ("compact", "full", "truncate")
PROFILE_COMMANDS = ("status", "setup", "refresh", "context", "add", "remove")


def default_capabilities_path() -> Path:
    runtime = Path(__file__).with_name("capabilities.toml")
    if runtime.exists():
        return runtime
    return Path(__file__).resolve().parents[1] / "templates" / "capabilities.toml"


def load_capability_catalog(path: Path | None = None) -> dict[str, dict[str, Any]]:
    catalog_path = path or default_capabilities_path()
    if not catalog_path.exists():
        return {}
    try:
        data = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid capability catalog {catalog_path}: {exc}") from exc
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


def list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(set(values))


def profile_names(profile: dict[str, Any], key: str) -> list[str]:
    return unique_sorted(list_strings(profile.get(key)))


def real_capability_names(names: list[str]) -> list[str]:
    return [name for name in names if name != "lite"]


def detect_real_capabilities(project_root: Path) -> list[str]:
    return real_capability_names(detect_capabilities(project_root))


def effective_capabilities(detected: list[str], user: list[str], disabled: list[str]) -> list[str]:
    active = (set(detected) | set(user)) - set(disabled)
    return sorted(active) or ["lite"]


def sync_effective_capabilities(profile: dict[str, Any]) -> None:
    detected = profile_names(profile, "detected_capabilities")
    user = profile_names(profile, "user_capabilities")
    disabled = profile_names(profile, "disabled_capabilities")
    profile["detected_capabilities"] = detected
    profile["user_capabilities"] = user
    profile["disabled_capabilities"] = disabled
    profile["capabilities"] = effective_capabilities(detected, user, disabled)


def parse_capability_values(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        names.extend(part.strip() for part in value.split(",") if part.strip())
    return unique_sorted(names)


def validate_capability_values(names: list[str], catalog: dict[str, dict[str, Any]]) -> None:
    unknown = [name for name in names if name not in catalog]
    if unknown:
        known = ", ".join(sorted(catalog)) or "none"
        raise ValueError(f"unknown capabilities: {', '.join(unknown)}; known capabilities: {known}")


def detect_catalog_capabilities(project_root: Path, catalog: dict[str, dict[str, Any]]) -> set[str]:
    detected: set[str] = set()
    for name, config in catalog.items():
        patterns = list_strings(config.get("detect_files"))
        if any(any(project_root.glob(pattern)) for pattern in patterns):
            detected.add(name)
    return detected


def detect_capabilities(project_root: Path) -> list[str]:
    capabilities: set[str] = set()
    capabilities.update(detect_catalog_capabilities(project_root, load_capability_catalog()))
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        capabilities.add("python")
    package_json = project_root / "package.json"
    if package_json.exists():
        capabilities.add("node")
    if (project_root / "go.mod").exists():
        capabilities.add("go")
    if (project_root / "Cargo.toml").exists():
        capabilities.add("rust")
    if (
        (project_root / "Dockerfile").exists()
        or (project_root / "compose.yaml").exists()
        or (project_root / "docker-compose.yml").exists()
    ):
        capabilities.add("ops")
    return sorted(capabilities) or ["lite"]


def detect_domains(project_root: Path) -> list[str]:
    domains: set[str] = set()
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="replace").lower()
        domains.add("backend")
        if any(name in text for name in ("fastapi", "django", "flask", "starlette")):
            domains.add("web")
        if any(name in text for name in ("sqlalchemy", "psycopg", "pandas", "numpy")):
            domains.add("data")
    package_json = project_root / "package.json"
    if package_json.exists():
        text = package_json.read_text(encoding="utf-8", errors="replace").lower()
        domains.add("web")
        if any(name in text for name in ("express", "fastify", "nestjs", "hono")):
            domains.add("backend")
        if any(name in text for name in ("prisma", "drizzle", "typeorm", "postgres", "mongodb")):
            domains.add("data")
    if (project_root / "go.mod").exists() or (project_root / "Cargo.toml").exists():
        domains.add("backend")
    if (
        (project_root / "Dockerfile").exists()
        or (project_root / "compose.yaml").exists()
        or (project_root / "docker-compose.yml").exists()
    ):
        domains.add("ops")
    return sorted(domains)


def toml_string(value: str) -> str:
    return json.dumps(value)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(value) for value in values) + "]"


def render_project_capabilities(catalog: dict[str, dict[str, Any]], names: list[str]) -> str:
    lines = [
        "# Generated by Codex Starter Kit. Edit this file to customize project capabilities.",
        "# Harness command strings run from the git root.",
        "# $PROJECT_ROOT and $HARNESS_CHANGED_* are expanded by the harness.",
        "",
    ]
    for name in names:
        config = catalog.get(name)
        if not config:
            continue
        lines.append(f"[{name}]")
        for key in ("detect_files", "skills", "hooks", "mcp", "test_roots", "source_roots", "harness"):
            values = list_strings(config.get(key))
            if values or key in {"mcp", "harness"}:
                lines.append(f"{key} = {toml_array(values)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_project_capabilities(project_root: Path, names: list[str]) -> Path:
    catalog = load_capability_catalog()
    managed_names = [name for name in names if name in catalog]
    path = project_root / PROJECT_CAPABILITIES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_project_capabilities(catalog, managed_names), encoding="utf-8")
    return path


def profile_path(project_root: Path) -> Path:
    return project_root / PROFILE_PATH


def load_profile(project_root: Path) -> dict[str, Any]:
    path = profile_path(project_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"invalid profile {path}: expected an object")
    return data


def save_profile(project_root: Path, profile: dict[str, Any]) -> None:
    path = profile_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compact_description(name: str) -> str:
    words = [
        word
        for word in re.split(r"[-_]", name)
        if word not in {"pro", "expert", "specialist", "patterns", "skills"}
    ]
    return f"{' '.join(words).title()} development workflow."


def compact_skill_descriptions(skills_root: Path, backup_path: Path) -> dict[str, list[str]]:
    originals: dict[str, str] = {}
    if backup_path.exists():
        try:
            saved = json.loads(backup_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved = {}
        if isinstance(saved, dict):
            originals.update(
                {key: value for key, value in saved.items() if isinstance(key, str) and isinstance(value, str)}
            )
    changed: list[str] = []
    for skill_path in sorted(skills_root.glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8", errors="replace")
        match = re.match(r"^(---\n)(.*?)(\n---\n)", text, re.DOTALL)
        if not match:
            continue
        description = re.search(r"^description:\s*(.+)$", match.group(2), re.MULTILINE)
        if not description:
            continue
        compact = compact_description(skill_path.parent.name)
        if description.group(1).strip().strip('"') == compact:
            continue
        originals.setdefault(str(skill_path.relative_to(skills_root)), text)
        replacement = f"description: {compact}"
        rewritten = text[: match.start(2)] + re.sub(
            r"^description:\s*.+$", replacement, match.group(2), count=1, flags=re.MULTILINE
        ) + text[match.end(2) :]
        skill_path.write_text(rewritten, encoding="utf-8")
        changed.append(skill_path.parent.name)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(originals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"changed": changed}


def restore_skill_descriptions(skills_root: Path, backup_path: Path) -> list[str]:
    if not backup_path.exists():
        return []
    originals = json.loads(backup_path.read_text(encoding="utf-8"))
    restored: list[str] = []
    for relative, text in originals.items():
        path = skills_root / relative
        if path.exists():
            path.write_text(text, encoding="utf-8")
            restored.append(path.parent.name)
    return restored


def default_skills_home() -> Path:
    return Path.home() / ".agents" / "skills"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--skills-home", type=Path, default=default_skills_home())
    parser.add_argument("command", choices=PROFILE_COMMANDS)
    parser.add_argument("values", nargs="*")
    args = parser.parse_args()
    project = args.project.resolve()
    profile = load_profile(project)

    if args.command in {"setup", "refresh"}:
        detected = detect_real_capabilities(project)
        profile.update(
            {
                "auto_detect": True,
                "detected_capabilities": detected,
                "user_capabilities": profile_names(profile, "user_capabilities"),
                "disabled_capabilities": profile_names(profile, "disabled_capabilities"),
                "domains": detect_domains(project),
                "context_mode": profile.get("context_mode", "compact"),
            }
        )
        sync_effective_capabilities(profile)
        save_profile(project, profile)
        write_project_capabilities(project, profile["capabilities"])
    elif args.command == "context":
        if len(args.values) != 1 or args.values[0] not in CONTEXT_MODES:
            parser.error("context requires compact, full, or truncate")
        profile.setdefault("auto_detect", True)
        profile.setdefault("detected_capabilities", detect_real_capabilities(project))
        profile.setdefault("user_capabilities", [])
        profile.setdefault("disabled_capabilities", [])
        sync_effective_capabilities(profile)
        profile["context_mode"] = args.values[0]
        save_profile(project, profile)
        # Skills are installed globally, so their restoration record must not be
        # tied to the project that happened to enable compact mode.
        backup = args.skills_home / ".codex-starter-kit-descriptions.json"
        if args.values[0] == "compact":
            compact_skill_descriptions(args.skills_home, backup)
        elif args.values[0] == "full":
            restore_skill_descriptions(args.skills_home, backup)
    elif args.command in {"add", "remove"}:
        names = parse_capability_values(args.values)
        if not names:
            parser.error(f"{args.command} requires at least one capability")
        try:
            validate_capability_values(names, load_capability_catalog())
        except ValueError as exc:
            parser.error(str(exc))
        profile.setdefault("auto_detect", True)
        profile.setdefault("detected_capabilities", detect_real_capabilities(project))
        profile.setdefault("user_capabilities", [])
        profile.setdefault("disabled_capabilities", [])
        profile.setdefault("domains", detect_domains(project))
        profile.setdefault("context_mode", "compact")
        user = set(profile_names(profile, "user_capabilities"))
        disabled = set(profile_names(profile, "disabled_capabilities"))
        if args.command == "add":
            user.update(names)
            disabled.difference_update(names)
        else:
            user.difference_update(names)
            disabled.update(names)
        profile["user_capabilities"] = sorted(user)
        profile["disabled_capabilities"] = sorted(disabled)
        sync_effective_capabilities(profile)
        save_profile(project, profile)
        write_project_capabilities(project, profile["capabilities"])

    print(
        json.dumps(
            {
                "configured": bool(profile),
                "capabilities": profile.get("capabilities", detect_capabilities(project)),
                "detected_capabilities": profile.get("detected_capabilities", detect_real_capabilities(project)),
                "user_capabilities": profile.get("user_capabilities", []),
                "disabled_capabilities": profile.get("disabled_capabilities", []),
                "domains": profile.get("domains", detect_domains(project)),
                "context_mode": profile.get("context_mode", "compact"),
                "project_capabilities": str(project / PROJECT_CAPABILITIES_PATH),
                "managed_skill_root": str(args.skills_home),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
