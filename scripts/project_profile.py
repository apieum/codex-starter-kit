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
CONTEXT_MODES = ("compact", "full", "truncate")


def detect_capabilities(project_root: Path) -> list[str]:
    capabilities: set[str] = set()
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="replace").lower()
        capabilities.add("backend")
        if any(name in text for name in ("fastapi", "django", "flask", "starlette")):
            capabilities.add("web")
        if any(name in text for name in ("sqlalchemy", "psycopg", "pandas", "numpy")):
            capabilities.add("data")
    package_json = project_root / "package.json"
    if package_json.exists():
        text = package_json.read_text(encoding="utf-8", errors="replace").lower()
        capabilities.add("web")
        if any(name in text for name in ("express", "fastify", "nestjs", "hono")):
            capabilities.add("backend")
        if any(name in text for name in ("prisma", "drizzle", "typeorm", "postgres", "mongodb")):
            capabilities.add("data")
    if (project_root / "go.mod").exists() or (project_root / "Cargo.toml").exists():
        capabilities.add("backend")
    if (project_root / "Dockerfile").exists() or (project_root / "compose.yaml").exists() or (project_root / "docker-compose.yml").exists():
        capabilities.add("ops")
    return sorted(capabilities) or ["lite"]


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
    words = [word for word in re.split(r"[-_]", name) if word not in {"pro", "expert", "specialist", "patterns", "skills"}]
    return f"{' '.join(words).title()} development workflow."


def compact_skill_descriptions(skills_root: Path, backup_path: Path) -> dict[str, list[str]]:
    originals: dict[str, str] = {}
    if backup_path.exists():
        try:
            saved = json.loads(backup_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved = {}
        if isinstance(saved, dict):
            originals.update({key: value for key, value in saved.items() if isinstance(key, str) and isinstance(value, str)})
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
    parser.add_argument("command", choices=("status", "setup", "refresh", "context"))
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    project = args.project.resolve()
    profile = load_profile(project)

    if args.command in {"setup", "refresh"}:
        profile.update({"auto_detect": True, "capabilities": detect_capabilities(project), "context_mode": profile.get("context_mode", "compact")})
        save_profile(project, profile)
    elif args.command == "context":
        if args.value not in CONTEXT_MODES:
            parser.error("context requires compact, full, or truncate")
        profile.setdefault("auto_detect", True)
        profile.setdefault("capabilities", detect_capabilities(project))
        profile["context_mode"] = args.value
        save_profile(project, profile)
        # Skills are installed globally, so their restoration record must not be
        # tied to the project that happened to enable compact mode.
        backup = args.skills_home / ".codex-starter-kit-descriptions.json"
        if args.value == "compact":
            compact_skill_descriptions(args.skills_home, backup)
        elif args.value == "full":
            restore_skill_descriptions(args.skills_home, backup)

    print(json.dumps({"configured": bool(profile), "capabilities": profile.get("capabilities", detect_capabilities(project)), "context_mode": profile.get("context_mode", "compact"), "managed_skill_root": str(args.skills_home)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
