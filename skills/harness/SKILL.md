---
name: harness
description: Project TDD harness status and RED/GREEN/REFACTOR phase workflow.
---

# Project Harness

Use this skill when the user invokes `$harness`.

Run commands through:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/tdd-harness.py" <command>
```

Commands:

- `status`: report phase, disabled state, active capabilities, and harness commands.
- `red`: enter RED. Write or change tests only, then run the focused failing test and stop.
- `green`: enter GREEN. The current test snapshot is frozen. Change production code only, make the RED test pass with minimal code, run the harness, and stop.
- `refactor`: enter REFACTOR/DESIGN. Tests stay frozen. Improve design without changing behavior, run the harness, summarize the design direction and next likely test.
- `done`: return to idle after a full green harness pass.
- `run`: run the configured harness for the active project capabilities.
- `on`: remove `.harness` and immediately run the harness.

For `$harness off`, require an explicit user request and include the reason:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/starter-kit/tdd-harness.py" off "reason"
```

Do not use `off` to make work pass, to bypass failing tests, or on your own initiative. If GREEN requires changing tests, stop and explain that the cycle must return to RED or the user must explicitly suspend the harness.
