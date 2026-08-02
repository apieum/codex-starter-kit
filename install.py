#!/usr/bin/env python3
"""Install the Codex Starter Kit as an opinionated baseline."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_SKILLS_PREFIX = "/home/ubuntu/.agents/skills"


def stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def backup_path(path: Path) -> Path:
    return path.with_name(path.name + f".bak-{stamp()}")


def backup_or_remove(path: Path, *, dry_run: bool, backup: bool) -> None:
    if not path.exists():
        return
    if backup:
        bak = backup_path(path)
        kind = "directory" if path.is_dir() else "file"
        print(f"backup {kind} {path} -> {bak}")
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(bak))
        return
    kind = "directory" if path.is_dir() else "file"
    print(f"replace existing {kind} without backup -> {path}")
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def install_file(src: Path, dst: Path, *, dry_run: bool, backup: bool, label: str | None = None) -> None:
    backup_or_remove(dst, dry_run=dry_run, backup=backup)
    print(f"write {label or 'file'} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def install_text(text: str, dst: Path, *, dry_run: bool, backup: bool, label: str) -> None:
    backup_or_remove(dst, dry_run=dry_run, backup=backup)
    print(f"write {label} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")


def install_agents(*, dry_run: bool, backup: bool, codex_home: Path, skills_home: Path) -> None:
    src_dir = REPO_ROOT / "agents"
    dst_dir = codex_home / "agents"
    backup_or_remove(dst_dir, dry_run=dry_run, backup=backup)
    target_skills = str(skills_home)
    for src in sorted(src_dir.glob("*.toml")):
        text = src.read_text(encoding="utf-8").replace(SOURCE_SKILLS_PREFIX, target_skills)
        dst = dst_dir / src.name
        print(f"write agent {src.name} -> {dst}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")


def install_skills(*, dry_run: bool, backup: bool, skills_home: Path) -> None:
    src_dir = REPO_ROOT / "skills"
    backup_or_remove(skills_home, dry_run=dry_run, backup=backup)
    print(f"write skills tree {src_dir} -> {skills_home}")
    if not dry_run:
        skills_home.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_dir, skills_home)


def install_hooks(*, dry_run: bool, backup: bool, codex_home: Path) -> None:
    hooks_dir = codex_home / "hooks"
    backup_or_remove(hooks_dir, dry_run=dry_run, backup=backup)
    print(f"write hooks tree -> {hooks_dir}")
    if not dry_run:
        shutil.copytree(REPO_ROOT / "hooks", hooks_dir, ignore=shutil.ignore_patterns("hooks.template.json"))
    template = (REPO_ROOT / "hooks" / "hooks.template.json").read_text(encoding="utf-8")
    rendered = template.replace("${HOME}", str(Path.home()))
    install_text(rendered, codex_home / "hooks.json", dry_run=dry_run, backup=backup, label="hooks config")


def install_runtime_support(*, dry_run: bool, backup: bool, codex_home: Path) -> None:
    runtime_dir = codex_home / "starter-kit"
    backup_or_remove(runtime_dir, dry_run=dry_run, backup=backup)
    print(f"write starter-kit runtime support -> {runtime_dir}")
    if not dry_run:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "scripts" / "project_profile.py", runtime_dir / "project_profile.py")
        shutil.copy2(REPO_ROOT / "hooks" / "tdd-harness.py", runtime_dir / "tdd-harness.py")
        shutil.copy2(REPO_ROOT / "templates" / "capabilities.toml", runtime_dir / "capabilities.toml")


def install_rules(*, dry_run: bool, backup: bool, codex_home: Path) -> None:
    rules_dir = codex_home / "rules"
    backup_or_remove(rules_dir, dry_run=dry_run, backup=backup)
    print(f"write command approval rules -> {rules_dir}")
    if not dry_run:
        shutil.copytree(REPO_ROOT / "rules", rules_dir)


def install_local_plugins(*, dry_run: bool, backup: bool, codex_home: Path) -> None:
    marketplace_path = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        return
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    marketplace_name = marketplace["name"]
    for plugin in marketplace.get("plugins", []):
        if plugin.get("source", {}).get("source") != "local":
            continue
        plugin_name = plugin["name"]
        plugin_src = (REPO_ROOT / plugin["source"]["path"]).resolve()
        plugin_manifest = plugin_src / ".codex-plugin" / "plugin.json"
        if not plugin_manifest.exists():
            print(f"warning: skip local plugin {plugin_name}: missing {plugin_manifest}")
            continue
        version = json.loads(plugin_manifest.read_text(encoding="utf-8")).get("version", "local")
        plugin_dst = codex_home / "plugins" / "cache" / marketplace_name / plugin_name / version
        # Plugin cache directories are generated artifacts. Do not leave `.bak-*`
        # siblings inside the cache tree: Codex treats version-like directories as
        # load candidates and may pick the backup as the active skill root.
        backup_or_remove(plugin_dst, dry_run=dry_run, backup=False)
        print(f"write local plugin cache {plugin_name}@{marketplace_name} {plugin_src} -> {plugin_dst}")
        if not dry_run:
            plugin_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(plugin_src, plugin_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def install_config(*, dry_run: bool, backup: bool, codex_home: Path) -> None:
    snippet = (REPO_ROOT / "templates" / "config.recommended.toml").read_text(encoding="utf-8")
    marketplace_path = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
    if marketplace_path.exists():
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        plugin_entries = []
        for plugin in marketplace.get("plugins", []):
            if plugin.get("source", {}).get("source") != "local":
                continue
            plugin_name = plugin["name"]
            plugin_entries.append(f'[plugins."{plugin_name}@codex-starter-kit"]\nenabled = true')
        plugin_config = "\n\n".join(plugin_entries)
        snippet = snippet.rstrip() + f"""

# Local Codex Starter Kit plugin marketplace. This lets Codex discover bundled
# repo-local plugins after `codex plugin marketplace upgrade`.
[marketplaces.codex-starter-kit]
source_type = "local"
source = "{REPO_ROOT}"

{plugin_config}
"""
    install_text(snippet, codex_home / "config.toml", dry_run=dry_run, backup=backup, label="baseline config")


def refresh_runtime_tools(*, dry_run: bool, codex_home: Path) -> None:
    if shutil.which("codex") is None:
        print("skip runtime refresh: codex CLI not found on PATH")
        return
    commands = [
        ["codex", "plugin", "marketplace", "upgrade"],
        ["codex", "mcp", "list"],
    ]
    for cmd in commands:
        print("run runtime check: " + " ".join(cmd))
        if dry_run:
            continue
        env = dict(os.environ)
        env["CODEX_HOME"] = str(codex_home)
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.returncode != 0:
            print(f"warning: {' '.join(cmd)} exited with {result.returncode}; continue")


def validate_agents(codex_home: Path) -> int:
    errors: list[str] = []
    agents_dir = codex_home / "agents"
    for path in sorted(agents_dir.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: TOML parse failed: {exc}")
            continue
        if data.get("name") != path.stem:
            errors.append(f"{path}: name={data.get('name')!r} does not match filename stem {path.stem!r}")
        for item in data.get("skills", {}).get("config", []):
            skill_path = item.get("path")
            if skill_path and not Path(skill_path).exists():
                errors.append(f"{path}: missing skill path {skill_path}")
    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Agent TOML validation passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install Codex Starter Kit as a ready-to-use baseline for ~/.codex and ~/.agents/skills."
    )
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--skills-home", default=str(Path.home() / ".agents" / "skills"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup-existing", action="store_true", help="Compatibility flag; backups are enabled by default.")
    parser.add_argument("--force", action="store_true", help="Overwrite starter-kit managed paths without backups. Dangerous.")
    parser.add_argument("--no-backup", action="store_true", help="Overwrite starter-kit managed paths without backups. Dangerous.")
    parser.add_argument("--install-config", action="store_true", help="Compatibility flag; baseline config is installed by default.")
    parser.add_argument("--skip-config", action="store_true")
    parser.add_argument("--skip-runtime-refresh", action="store_true", help="Do not run codex plugin/mcp refresh checks after install.")
    parser.add_argument("--skip-agents", action="store_true")
    parser.add_argument("--skip-skills", action="store_true")
    parser.add_argument("--skip-hooks", action="store_true")
    parser.add_argument("--skip-rules", action="store_true")
    parser.add_argument("--skip-plugins", action="store_true")
    parser.add_argument("--skip-global-agents-md", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)

    backup = not (args.force or args.no_backup)
    codex_home = Path(args.codex_home).expanduser()
    skills_home = Path(args.skills_home).expanduser()

    if args.validate_only:
        return validate_agents(codex_home)

    if backup:
        print("baseline mode: managed Codex files are replaced with timestamped backups")
    else:
        print("baseline mode: managed Codex files are replaced without backups")

    if not args.skip_global_agents_md:
        install_file(REPO_ROOT / "templates" / "AGENTS.md", codex_home / "AGENTS.md", dry_run=args.dry_run, backup=backup, label="global AGENTS.md")
    if not args.skip_agents:
        install_agents(dry_run=args.dry_run, backup=backup, codex_home=codex_home, skills_home=skills_home)
    if not args.skip_skills:
        install_skills(dry_run=args.dry_run, backup=backup, skills_home=skills_home)
    if not args.skip_hooks:
        install_hooks(dry_run=args.dry_run, backup=backup, codex_home=codex_home)
    install_runtime_support(dry_run=args.dry_run, backup=backup, codex_home=codex_home)
    if not args.skip_rules:
        install_rules(dry_run=args.dry_run, backup=backup, codex_home=codex_home)
    if not args.skip_plugins:
        install_local_plugins(dry_run=args.dry_run, backup=backup, codex_home=codex_home)
    if not args.skip_config:
        install_config(dry_run=args.dry_run, backup=backup, codex_home=codex_home)
    if not args.skip_runtime_refresh:
        refresh_runtime_tools(dry_run=args.dry_run, codex_home=codex_home)

    if not args.dry_run:
        return validate_agents(codex_home)
    print("Dry run complete. Re-run ./install.sh to install with backups, or ./install.sh --force to replace without backups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
