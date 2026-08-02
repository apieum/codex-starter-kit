# Project Profile And Context Catalogue Plan

**Goal:** Let `/profile` select project-relevant capabilities and let `/context` control skill-catalogue fidelity, without changing a skill's full instructions or weakening the security baseline.

**Decisions:**

- `/profile` owns project capability selection and language/framework auto-detection.
- `/context` owns catalogue metadata only: `compact` keeps every skill with concise descriptions, `full` restores source descriptions, and `truncate` disables selected skills only after displaying the exact next-session impact and receiving confirmation.
- The profile manager keeps a project-local manifest and manages only a clearly delimited generated block in `.codex/config.toml`. Existing configuration remains unchanged.
- Context modes apply on the next Codex startup. They cannot remove tools or skills already injected in the current session.
- Built-in tools, MCP schemas, hook definitions, and Codex's fixed skills allocation are reported as outside the manager's control.

## Work Items

1. Add test-first `unittest` coverage for profile persistence, project detection, description compaction/restoration, truncation preview/apply, and generated-block preservation.
2. Implement a standard-library profile manager, installed under `$CODEX_HOME/starter-kit`, and policy data for project capabilities and concise skill descriptions.
3. Add `/profile` and `/context` skills. Changes require explicit confirmation; status and previews are read-only.
4. Register a read-only SessionStart hook that reports setup state, selected capabilities, context mode, and configuration drift within a bounded message.
5. Extend pack validation, document the modes in both READMEs, then run focused tests, pack validation, Python compilation, and whitespace checks.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-pack.py
python3 -m py_compile install.py hooks/*.py scripts/*.py
git diff --check
```

Before committing, inspect the complete diff and run the repository-required GitNexus change check when available.
