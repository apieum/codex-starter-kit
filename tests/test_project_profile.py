from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from project_profile import compact_skill_descriptions, detect_capabilities, load_profile, save_profile


class ProjectProfileTests(unittest.TestCase):
    def test_detects_python_web_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["fastapi"]\n')

            self.assertEqual(detect_capabilities(root), ["backend", "web"])

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
            source = "---\nname: python-pro\ndescription: Write modern Python applications with architecture, testing, async behavior, and deployment guidance.\n---\n\n# Python\n"
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


if __name__ == "__main__":
    unittest.main()
