# Changelog

## Unreleased — 2026-10-31 selected-directory scope repair

- Keep context discovery, source search, workspace aliases and cached project fingerprints within the explicitly selected directory, including subdirectories of a Git repository.
- Add two behavioral regressions using disposable Git repositories. Git status remains repository metadata; these helpers are not a sandbox.
- Existing aliases that previously expanded to a parent repository require explicit re-registration for the desired directory. No automatic registry migration or deployment.

## Unreleased — 2026-10-29 security hardening

- Reject DOS device names and ambiguous Windows file paths in guarded file helpers.
- Restrict runtime workspace alias lookups to the bound project root, preventing cross-project metadata inspection.
- Require explicit `--allow-shell-strings` for the legacy test-pipeline shell interface; exact argv arrays remain the default.
- Reject malformed/nonfinite pipeline timeouts before starting task-owned processes.
- Prevent pipeline timeout cleanup from taking over a separately started process with the same command label.
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

