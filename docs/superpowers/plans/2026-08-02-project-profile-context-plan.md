# Project Profile And Context Catalogue Plan

**Goal:** Let `/project-profile` provide project capability guidance and let `/context` control starter-skill catalogue fidelity without weakening the security baseline.

**Implemented behavior:**

- `/project-profile` stores project-local auto-detection and detected capabilities.
- `/context compact` keeps all starter skills but shortens their catalogue descriptions; `/context full` restores originals from a global backup.
- `/context truncate` does not silently disable skills. Built-in tools, MCP schemas, hooks, and Codex's fixed skill allocation remain outside these controls.
- A read-only SessionStart hook reports missing, invalid, or active project profile state.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-pack.py
python3 -m py_compile install.py hooks/*.py scripts/*.py
git diff --check
```
