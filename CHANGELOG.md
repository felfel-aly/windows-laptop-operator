# Changelog

## Unreleased — 2026-10-29 security hardening

- Reject DOS device names and ambiguous Windows file paths in guarded file helpers.
- Require explicit `--allow-shell-strings` for the legacy test-pipeline shell interface; exact argv arrays remain the default.
- Reject malformed/nonfinite pipeline timeouts before starting task-owned processes.
- Prevent screenshots from overwriting existing files or traversing linked output directories; improve mouse click targeting checks.
- Add isolated security regression tests and read-only Linux/Windows CI with pinned GitHub Actions.
- Correct public-package inventory drift for the previously published developer profile.
- Changes are repository-only; deployment and interactive GUI behavior require independent Windows verification.

## 0.1.0 — 2026-10-05

- Initial public source package for the Windows Laptop Operator skill and task-scoped runtime.
- Includes the updated local helper versions, non-Git workspace support and root-level language hints.
- Includes Git/context snapshots, guarded patching, named process management, Windows UIA and GUI helpers.
- Removes private project profiles and excludes all deployed machine state.
- Adds installation, connector, security, update and contribution documentation, isolated tests, an explicit public-file inventory and a fail-closed packaging check.
- Licensed under MIT.
