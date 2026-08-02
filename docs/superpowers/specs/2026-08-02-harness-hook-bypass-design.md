# Harness Hook Bypass Semantics

## Goal

Make the `.harness` marker suspend the TDD harness completely for its current
repository, without disabling independent shell-safety protections.

## Current Defect

The hook evaluates `verify_role()` during `PreToolUse` whenever `tool_name` is
present. Since PreToolUse payloads contain that field, read-only and harness
control commands can be blocked by RED or a failing harness. The disabled
marker also refuses delivery commands, preventing a user who explicitly
suspended the harness from committing.

## Target Behavior

- When `.harness` exists, `tdd-harness.py` emits context only and does not
  deny commands, including `git commit`, `git push`, or PR commands.
- `block-dangerous-shell.py` remains active and continues to protect against
  destructive shell operations.
- In normal mode, PreToolUse evaluates the harness only for delivery commands.
- PostToolUse evaluates the harness after relevant tool actions.
- Harness control invocations (`status`, `off`, `on`, `run`) bypass harness
  evaluation so status and recovery remain available.

## Tests

Tests will use representative hook payloads to prove that: a disabled harness
does not block a commit; a control command is not blocked by a failing harness;
and an active harness still blocks a delivery command when verification fails.

## Verification

Run the focused harness-hook tests, the pack validator, and Python syntax
checks. The complete repository harness is expected to remain red until its
unrelated Ruff and Mypy baseline failures are addressed.
