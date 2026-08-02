# Harness Hook Bypass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `.harness` fully suspend the TDD harness while preserving the independent dangerous-shell guard.

**Architecture:** `hooks/tdd-harness.py` already parses the intercepted shell command. Add an early control-command exemption and ensure the disabled marker exits without a deny response. Restrict normal verification to PostToolUse, except for explicit delivery-command preflight.

**Tech Stack:** Python 3 standard library, `unittest`, Git fixtures.

---

### Task 1: Specify Hook Bypass Behavior

**Files:**
- Modify: `tests/test_tdd_harness.py`
- Test: `tests/test_tdd_harness.py`

- [ ] **Step 1: Add a failing disabled-harness delivery test**

```python
def test_disabled_harness_does_not_block_delivery(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".harness").write_text("debugging\n", encoding="utf-8")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "exec_command",
            "tool_input": {"workdir": str(root), "command": "git commit -m test"},
        }
        self.assertEqual(tdd_harness.handle_hook(payload), 0)
```

- [ ] **Step 2: Add a failing PreToolUse control-command test**

```python
def test_harness_control_command_skips_pretool_verification(self) -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "exec_command",
        "tool_input": {"command": "python3 /tmp/tdd-harness.py status"},
    }
    with mock.patch.object(tdd_harness, "verify_role", side_effect=AssertionError):
        self.assertEqual(tdd_harness.handle_hook(payload), 0)
```

- [ ] **Step 3: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_tdd_harness`

Expected: failure because the disabled branch emits a delivery denial and normal PreToolUse falls through to `verify_role()`.

### Task 2: Correct Hook Dispatch

**Files:**
- Modify: `hooks/tdd-harness.py`
- Test: `tests/test_tdd_harness.py`

- [ ] **Step 1: Add control-command detection**

Add a helper that tokenizes the command and recognizes the installed harness script followed by `status`, `off`, `on`, or `run`:

```python
def is_harness_control_command(command: str) -> bool:
    tokens = shlex.split(command, posix=True)
    for index, token in enumerate(tokens[:-1]):
        if Path(token).name == "tdd-harness.py":
            return tokens[index + 1] in {"status", "off", "on", "run"}
    return False
```

- [ ] **Step 2: Short-circuit disabled and control requests**

At the start of `handle_hook`, return context without denial when `.harness` exists. Immediately return `0` for an identified control command before delivery or verification logic.

- [ ] **Step 3: Restrict generic verification to PostToolUse**

Replace the broad condition with:

```python
if event == "PostToolUse":
    violation = verify_role(root)
    if violation:
        print(violation, file=sys.stderr)
        return 2
```

Keep `verify_role(root)` in the active-harness delivery-command PreToolUse branch so commits remain protected when the harness is enabled.

- [ ] **Step 4: Run the focused tests and confirm GREEN**

Run: `python3 -m unittest tests.test_tdd_harness`

Expected: all harness tests pass.

### Task 3: Verify Pack Integrity

**Files:**
- Verify: `hooks/tdd-harness.py`
- Verify: `scripts/validate-pack.py`

- [ ] **Step 1: Run syntax and pack validation**

Run: `python3 -m py_compile hooks/tdd-harness.py && python3 scripts/validate-pack.py`

Expected: compilation succeeds and `Pack validation passed.`

- [ ] **Step 2: Run the configured harness and record baseline result**

Run: `python3 hooks/tdd-harness.py --project . run`

Expected: it may report the known unrelated Ruff/Mypy baseline failures; do not suppress them.

- [ ] **Step 3: Commit the scoped change after re-enabling the harness**

Run:

```bash
python3 hooks/tdd-harness.py --project . on
git add hooks/tdd-harness.py tests/test_tdd_harness.py docs/superpowers/specs/2026-08-02-harness-hook-bypass-design.md docs/superpowers/plans/2026-08-02-harness-hook-bypass.md
git commit -m "Fix harness hook bypass semantics"
```

Expected: the hook permits the commit only after the active harness passes. If the baseline remains failing, report that exact blocker rather than bypassing it.
