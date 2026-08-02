# Project Profiles And Startup Validation

## Goal

Reduce default token consumption while keeping project-relevant tools available.
Codex starts with a minimal bootstrap profile, selects a persistent project
profile when one is missing, and validates the selected profile on every later
session start.

## Profiles

The initial profile set is `lite`, `web`, `backend`, `data`, `ops`, `security`,
and `full`. Each profile declares enabled MCP servers, hooks, and skill bundles.
`lite` is the fallback for unknown or empty repositories and has no remote MCP
servers or per-prompt classifier.

## Startup Flow

The SessionStart hook reads a project-local profile manifest. When absent, it
inspects only stable repository signals, asks the user to choose a profile, and
writes the manifest. The current session remains in bootstrap mode; the selected
profile becomes active after restart.

When a manifest exists, the hook validates its schema, profile version, and
required local executables or MCP endpoints. It emits no additional context when
healthy. On failure or profile drift, it emits a concise message identifying the
failed requirement and the available recovery action.

## Safety And Scope

Profile selection never auto-enables networked or mutating tools. The user must
confirm selection or changes. The existing `on-request` approval policy and
workspace-write sandbox remain unchanged.

## Verification

Tests cover profile parsing, selection persistence, startup health checks,
invalid manifests, and a temporary install for every profile. Pack validation
checks that each profile is syntactically valid and that `lite` does not enable
remote MCP servers or the intake classifier.
