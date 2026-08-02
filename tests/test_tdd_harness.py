from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest import mock


HARNESS_PATH = Path(__file__).resolve().parents[1] / "hooks" / "tdd-harness.py"
SPEC = importlib.util.spec_from_file_location("tdd_harness", HARNESS_PATH)
assert SPEC is not None
tdd_harness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tdd_harness)


class TddHarnessTests(unittest.TestCase):
    def test_disabled_harness_does_not_block_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".harness").write_text("debugging\n", encoding="utf-8")
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "exec_command",
                "tool_input": {"workdir": str(root), "command": "git commit -m test"},
            }

            with mock.patch.object(tdd_harness, "emit_block") as emit_block:
                self.assertEqual(tdd_harness.handle_hook(payload), 0)

            emit_block.assert_not_called()

    def test_harness_control_command_skips_pretool_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "exec_command",
                "tool_input": {
                    "workdir": directory,
                    "command": "python3 /tmp/tdd-harness.py status",
                },
            }

            with mock.patch.object(tdd_harness, "verify_role", side_effect=AssertionError):
                self.assertEqual(tdd_harness.handle_hook(payload), 0)

    def test_active_harness_blocks_delivery_when_verification_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "exec_command",
                "tool_input": {"workdir": directory, "command": "git commit -m test"},
            }

            with (
                mock.patch.object(tdd_harness, "verify_role", return_value="verification failed"),
                mock.patch.object(tdd_harness, "emit_block") as emit_block,
            ):
                self.assertEqual(tdd_harness.handle_hook(payload), 0)

            emit_block.assert_called_once_with("Delivery command refused until harness passes.\n\nverification failed")

    def test_green_freezes_current_tests_not_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init"], cwd=root, stdout=subprocess.DEVNULL, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / ".codex").mkdir()
            (root / ".codex" / "starter-profile.json").write_text(
                '{"capabilities": ["python"], "context_mode": "compact"}\n',
                encoding="utf-8",
            )
            (root / ".codex" / "capabilities.toml").write_text(
                '[python]\ntest_roots = ["tests"]\nsource_roots = ["src"]\nharness = []\n',
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "src").mkdir()
            (root / "tests" / "test_demo.py").write_text("def test_old():\n    assert True\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=root, stdout=subprocess.DEVNULL, check=True)

            (root / "tests" / "test_demo.py").write_text(
                "def test_old():\n    assert True\n\n"
                "def test_new():\n    assert False\n",
                encoding="utf-8",
            )

            tdd_harness.set_phase(root, "green")

            self.assertIsNone(tdd_harness.verify_role(root))

            (root / "tests" / "test_demo.py").write_text(
                "def test_old():\n    assert True\n\n"
                "def test_new():\n    assert True\n",
                encoding="utf-8",
            )

            violation = tdd_harness.verify_role(root)
            self.assertIsNotNone(violation)
            self.assertIn("tests are frozen", violation)

    def test_state_files_are_not_counted_as_changed_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init"], cwd=root, stdout=subprocess.DEVNULL, check=True)
            (root / ".gauntlet").write_text('{"phase": "red"}\n', encoding="utf-8")
            (root / ".harness").write_text("debugging\n", encoding="utf-8")

            self.assertEqual(tdd_harness.changed_paths(root), [])


if __name__ == "__main__":
    unittest.main()
