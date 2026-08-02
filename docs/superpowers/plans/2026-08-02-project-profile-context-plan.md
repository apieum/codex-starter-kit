# Project Profile And Context Budget Plan

> **For Codex:** execute this plan using the appropriate implementation workflow and test each step before moving on.

**Goal:** Add project-scoped `/profile` capability selection and `/context low|medium|high` budget controls that are checked on every Codex startup without widening permissions.

**Architecture:** Install a small standard-library Python profile manager with the existing hooks. It stores user choices in a project-local manifest, detects languages/frameworks from conventional manifest files, and produces a concise startup health report. `/profile` and `/context` are enabled skills which invoke the manager. The manager must preserve existing Codex configuration and only manage its own manifest; startup checks report configuration drift instead of modifying tool configuration during a session.

**Stack:** Python 3 standard library, TOML, Codex enabled skills, lifecycle hooks, `unittest`.

## Scope And Acceptance Checks

| ID | Area | Acceptance check |
| --- | --- | --- |
| P1 | Profile state | A project manifest stores auto-detection, selected capabilities, and context budget without overwriting user config. |
| P2 | Detection | Python, Node/TypeScript, Go, Rust, and common web frameworks map deterministically to suggested capabilities. |
| P3 | Commands | Installed `/profile` and `/context` skills document and invoke supported actions with explicit confirmation for changes. |
| P4 | Startup | A SessionStart hook reports the active profile, detected drift, and a one-time setup prompt for unconfigured projects. |
| P5 | Token control | `low`, `medium`, and `high` control only the starter kit's generated context and hook verbosity; permissions remain unchanged. |
| P6 | Quality | Unit tests cover persistence, detection, invalid inputs, and startup output; pack validation and syntax checks pass. |

## 1. Define The Profile Manager Through Tests

**Files:**
- Create: `tests/test_project_profile.py`
- Create: `scripts/project_profile.py`

1. Add failing `unittest` cases for default profile creation, TOML persistence, unsupported values, deterministic detection, and a minimal profile report.
2. Run `python3 -m unittest tests.test_project_profile` and confirm it fails because the manager does not exist.
3. Implement a standard-library manager that owns only `.codex/starter-profile.toml`.
4. Add commands for `status`, `setup`, `refresh`, `auto on|off`, `set <capabilities>`, and `context <low|medium|high>`.
5. Re-run the unit tests.

## 2. Add Explicit Capability And Budget Policies

**Files:**
- Create: `profiles/capabilities.toml`
- Modify: `scripts/project_profile.py`
- Modify: `tests/test_project_profile.py`

1. Add failing tests for language and framework signals from `pyproject.toml`, `package.json`, `go.mod`, and `Cargo.toml`.
2. Define a concise registry for `web`, `backend`, `data`, `ops`, `security`, and `lite` capabilities.
3. Define `low`, `medium`, and `high` as generated-context limits and hook reporting limits only. Do not change approval policy, sandbox mode, shell/network access, or MCP approval modes.
4. Re-run profile tests, including negative cases and malformed manifests.

## 3. Make The Controls Slash-Invokable

**Files:**
- Create: `skills/profile/SKILL.md`
- Create: `skills/context/SKILL.md`
- Modify: `install.py`
- Modify: `scripts/validate-pack.py`

1. Add failing validator tests/checks for both skills and the shipped manager.
2. Create concise enabled skills named `profile` and `context`, so Codex exposes `/profile` and `/context`.
3. Instruct `/profile` to ask before writing project state; support status and refresh without mutation.
4. Instruct `/context` to accept exactly `low`, `medium`, or `high`, explain the current effective limits, and write only after confirmation.
5. Ensure the installer copies the manager and policy registry alongside existing installed assets.
6. Re-run unit tests and pack validation.

## 4. Check Profiles At Session Startup

**Files:**
- Create: `hooks/project-profile-startup.py`
- Modify: `hooks/hooks.template.json`
- Modify: `scripts/validate-pack.py`
- Modify: `tests/test_project_profile.py`

1. Add a failing test for unconfigured-project guidance, configured profile reporting, and detection drift reporting.
2. Add a SessionStart hook that invokes the installed manager in read-only report mode.
3. Keep the startup message bounded by the selected context budget and ensure no shell/MCP/permission policy mutation occurs.
4. Add validation that the hook is registered and Python-parseable.
5. Run focused tests and `python3 scripts/validate-pack.py`.

## 5. Document And Verify The Installed Experience

**Files:**
- Modify: `README.md`
- Modify: `README.fr.md`
- Modify: `docs/superpowers/specs/2026-08-02-configurable-clone-location-design.md`

1. Document `/profile` first-run setup, later refresh/status behavior, and `/context` levels.
2. State the limitation clearly: a running session cannot remove tools already loaded; profile changes take effect on the next startup and startup reports any drift.
3. Run:

   ```bash
   python3 -m unittest discover -s tests -p 'test_*.py'
   python3 scripts/validate-pack.py
   python3 -m py_compile install.py hooks/*.py scripts/*.py
   git diff --check
   ```

4. Review the changed files for permission regressions. Run the available Claude Companion reviewer if its runner is available and the review can be performed without exposing secrets.
5. Before any commit, inspect the diff and run the repository's required change-impact check if GitNexus is available.
