#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import tomllib

root = Path(__file__).resolve().parents[1]
errors = []
for path in sorted((root / "agents").glob("*.toml")):
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        continue
    if data.get("name") != path.stem:
        errors.append(f"{path}: name does not match filename")
    for server_name, server in data.get("mcp_servers", {}).items():
        if server.get("default_tools_approval_mode") != "prompt":
            errors.append(f"{path}: {server_name} MCP tools must prompt for approval")
    for item in data.get("skills", {}).get("config", []):
        skill_path = str(item.get("path", ""))
        if "/.codex/plugins/cache/" in skill_path or "/.codex/skills/.system/" in skill_path:
            errors.append(f"{path}: non-portable skill path {skill_path}")
for path in sorted((root / "skills").glob("*/SKILL.md")):
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        errors.append(f"{path}: missing YAML frontmatter")
for path in sorted((root / "plugins").glob("*/.codex-plugin/plugin.json")):
    try:
        plugin = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        continue
    plugin_root = path.parents[1]
    if plugin.get("name") != plugin_root.name:
        errors.append(f"{path}: name does not match plugin directory")
    skills_dir = plugin.get("skills")
    if skills_dir and not (plugin_root / skills_dir).exists():
        errors.append(f"{path}: skills path does not exist: {skills_dir}")
    for skill_path in sorted((plugin_root / "skills").glob("*/SKILL.md")):
        if not skill_path.read_text(encoding="utf-8", errors="replace").startswith("---"):
            errors.append(f"{skill_path}: missing YAML frontmatter")
marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
if marketplace_path.exists():
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{marketplace_path}: {exc}")
    else:
        for entry in marketplace.get("plugins", []):
            source = entry.get("source", {})
            path = source.get("path")
            if source.get("source") == "local" and path and not (root / path).exists():
                errors.append(f"{marketplace_path}: local plugin path does not exist: {path}")
try:
    config = tomllib.loads((root / "templates" / "config.recommended.toml").read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"templates/config.recommended.toml: {exc}")
else:
    if not config.get("features", {}).get("hooks"):
        errors.append("templates/config.recommended.toml: hooks feature is not enabled")
    if config.get("approval_policy") != "on-request":
        errors.append("templates/config.recommended.toml: approval_policy must be on-request")
    if config.get("sandbox_mode") != "workspace-write":
        errors.append("templates/config.recommended.toml: sandbox_mode must be workspace-write")
    if config.get("sandbox_workspace_write", {}).get("network_access") is not False:
        errors.append("templates/config.recommended.toml: workspace shell network access must be disabled")
    for plugin in ["github@openai-curated"]:
        if not config.get("plugins", {}).get(plugin, {}).get("enabled"):
            errors.append(f"templates/config.recommended.toml: plugin {plugin} is not enabled")
    if (root / "plugins" / "superpowers" / ".codex-plugin" / "plugin.json").exists():
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        local_plugins = {
            entry.get("name")
            for entry in marketplace.get("plugins", [])
            if entry.get("source", {}).get("source") == "local"
        }
        if "superpowers" not in local_plugins:
            errors.append(".agents/plugins/marketplace.json: missing local superpowers plugin")
    else:
        errors.append("plugins/superpowers/.codex-plugin/plugin.json: missing bundled Superpowers fork")
    for server in ["context7", "vue-docs", "nuxt-ui-remote", "nuxt-remote"]:
        if server not in config.get("mcp_servers", {}):
            errors.append(f"templates/config.recommended.toml: missing MCP server {server}")
        elif config["mcp_servers"][server].get("default_tools_approval_mode") != "prompt":
            errors.append(f"templates/config.recommended.toml: {server} MCP tools must prompt for approval")
for hook_name in [
    "block-dangerous-shell.py",
    "handoff-permission-request.py",
    "handoff-post-tool-use.py",
    "handoff-intake-classifier.py",
]:
    try:
        ast.parse((root / "hooks" / hook_name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"hooks/{hook_name}: syntax check failed: {exc}")
permission_hook = (root / "hooks" / "handoff-permission-request.py").read_text(encoding="utf-8")
if 'tool_name.startswith("mcp__")' in permission_hook:
    errors.append("hooks/handoff-permission-request.py: MCP tools must not be auto-approved")
if "is_handoff_service_control" in permission_hook:
    errors.append("hooks/handoff-permission-request.py: service controls must not be auto-approved")
try:
    hooks_config = json.loads((root / "hooks" / "hooks.template.json").read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"hooks/hooks.template.json: {exc}")
else:
    for event in ["PermissionRequest", "UserPromptSubmit", "PreToolUse", "PostToolUse"]:
        if event not in hooks_config.get("hooks", {}):
            errors.append(f"hooks/hooks.template.json: missing {event} hook")
rules_path = root / "rules" / "default.rules"
if not rules_path.exists():
    errors.append("rules/default.rules: missing command approval rules")
else:
    rules_text = rules_path.read_text(encoding="utf-8")
    prefix_rules = re.findall(r"prefix_rule\(pattern=\[(.*?)\]", rules_text)
    if len(prefix_rules) < 100:
        errors.append("rules/default.rules: expected broad read-only command allowlist")
    for unsafe in [
        'pattern = ["gio", "trash"]',
        'pattern = ["cp"]',
        'pattern = ["python"]',
        'pattern = ["python3"]',
        'pattern = ["pnpm"]',
        'pattern=["systemctl"]',
        'pattern=["git"]',
        'pattern=["curl"]',
        'pattern=["pnpm", "install"]',
        'pattern=["npm", "install"]',
        'pattern=["yarn", "install"]',
        'pattern=["gh", "repo"]',
        'pattern=["kubectl", "apply"]',
        'pattern=["docker", "compose", "up"]',
    ]:
        if unsafe in rules_text:
            errors.append(f"rules/default.rules: unsafe broad allow rule {unsafe}")
if errors:
    print("Validation failed:")
    for err in errors:
        print("-", err)
    raise SystemExit(1)
print("Pack validation passed.")
