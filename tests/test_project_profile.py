from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from project_profile import (
    compact_skill_descriptions,
    detect_capabilities,
    detect_domains,
    load_capability_catalog,
    load_profile,
    render_project_capabilities,
    save_profile,
    write_project_capabilities,
)


PROFILE_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_profile.py"


class ProjectProfileTests(unittest.TestCase):
    def run_profile(self, root: Path, *args: str) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(PROFILE_SCRIPT), "--project", str(root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        return payload

    def test_detects_python_web_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["fastapi"]\n')

            self.assertEqual(detect_capabilities(root), ["python"])
            self.assertEqual(detect_domains(root), ["backend", "web"])

    def test_detects_python_project_from_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "script.py").write_text("print('hello')\n")

            self.assertEqual(detect_capabilities(root), ["python"])

    def test_persists_project_profile_without_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            save_profile(root, {"auto_detect": True, "capabilities": ["web"], "context_mode": "compact"})

            self.assertEqual(
                load_profile(root),
                {"auto_detect": True, "capabilities": ["web"], "context_mode": "compact"},
            )
            self.assertFalse((root / ".codex" / "config.toml").exists())

    def test_compact_preserves_full_skill_and_writes_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "python-pro" / "SKILL.md"
            skill.parent.mkdir()
            source = (
                "---\nname: python-pro\n"
                "description: Write modern Python applications with architecture, testing, async behavior, "
                "and deployment guidance.\n---\n\n# Python\n"
            )
            skill.write_text(source)

            result = compact_skill_descriptions(root, root / "descriptions.json")

            self.assertEqual(result["changed"], ["python-pro"])
            self.assertIn("Python", skill.read_text())
            self.assertIn("description: Python development workflow.", skill.read_text())
            self.assertIn("architecture, testing", (root / "descriptions.json").read_text())

    def test_repeated_compaction_keeps_original_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "python-pro" / "SKILL.md"
            skill.parent.mkdir()
            skill.write_text("---\nname: python-pro\ndescription: Original detailed description.\n---\n")
            backup = root / "descriptions.json"

            compact_skill_descriptions(root, backup)
            compact_skill_descriptions(root, backup)

            self.assertIn("Original detailed description.", backup.read_text())

    def test_capability_catalog_uses_top_level_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "capabilities.toml"
            catalog.write_text(
                '[python]\ndetect_files = ["pyproject.toml"]\nharness = ["pytest"]\n\n[meta]\nversion = "1"\n',
                encoding="utf-8",
            )

            self.assertEqual(sorted(load_capability_catalog(catalog)), ["python"])

    def test_project_capabilities_render_top_level_sections(self) -> None:
        text = render_project_capabilities(
            {"python": {"detect_files": ["pyproject.toml"], "mcp": [], "harness": ["pytest"]}},
            ["python"],
        )

        self.assertIn("[python]", text)
        self.assertNotIn("[capabilities.python]", text)

    def test_writes_project_capability_file_from_default_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            path = write_project_capabilities(root, ["python"])

            text = path.read_text(encoding="utf-8")
            self.assertEqual(path, root / ".codex" / "capabilities.toml")
            self.assertIn("[python]", text)
            self.assertIn("harness =", text)

    def test_adds_user_capability_and_keeps_it_on_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\nname = \"demo\"\n")

            self.run_profile(root, "setup")

            added = self.run_profile(root, "add", "node")
            self.assertEqual(added["detected_capabilities"], ["python"])
            self.assertEqual(added["user_capabilities"], ["node"])
            self.assertEqual(added["disabled_capabilities"], [])
            self.assertEqual(added["capabilities"], ["node", "python"])

            refreshed = self.run_profile(root, "refresh")
            self.assertEqual(refreshed["detected_capabilities"], ["python"])
            self.assertEqual(refreshed["user_capabilities"], ["node"])
            self.assertEqual(refreshed["capabilities"], ["node", "python"])
            self.assertIn("[node]", (root / ".codex" / "capabilities.toml").read_text())

    def test_removes_detected_capability_until_added_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\nname = \"demo\"\n")

            self.run_profile(root, "setup")

            removed = self.run_profile(root, "remove", "python")
            self.assertEqual(removed["detected_capabilities"], ["python"])
            self.assertEqual(removed["disabled_capabilities"], ["python"])
            self.assertEqual(removed["capabilities"], ["lite"])

            refreshed = self.run_profile(root, "refresh")
            self.assertEqual(refreshed["detected_capabilities"], ["python"])
            self.assertEqual(refreshed["disabled_capabilities"], ["python"])
            self.assertEqual(refreshed["capabilities"], ["lite"])

            added = self.run_profile(root, "add", "python")
            self.assertEqual(added["disabled_capabilities"], [])
            self.assertEqual(added["capabilities"], ["python"])


if __name__ == "__main__":
    unittest.main()
