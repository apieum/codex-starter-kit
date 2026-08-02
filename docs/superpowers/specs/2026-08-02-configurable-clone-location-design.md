# Configurable Clone Location

## Goal

Let a person choosing the copy-paste installation flow select where the
starter-kit repository is cloned instead of prescribing `~/projects`.

## Scope

Update the English and Russian README installation snippets only. The existing
installer continues to use the standard `~/.codex` and `~/.agents/skills`
locations and receives no new options.

## Flow

The installation snippet prompts for a destination directory. Pressing Enter
selects `~/workspace/codex-starter-kit`; another entered path is used as-is.
It expands a leading `~`, rejects an existing destination, clones the
repository, and changes into the cloned directory before continuing with the
documented installation command.

## Error Handling

The shell snippet exits on errors. If the selected destination already exists,
it prints an error instead of overwriting or merging into that directory.

## Verification

The pack validator remains green. The README snippets will be reviewed for
matching behavior in English and Russian and verified with shell syntax checks.
