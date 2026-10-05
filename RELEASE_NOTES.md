# Release notes — 0.1.0

This is the first public packaging release of an existing Windows skill and runtime. It includes current reusable helper source and general operating references. Private machine settings and project-specific profiles are deliberately omitted.

The runtime is optional, task-scoped and stdio-only. Installing this package does not create a remote-access connection. Use an authorized local connector and follow [INSTALL.md](INSTALL.md).

Validation is recorded in [VALIDATION.md](VALIDATION.md). Compatibility outside the tested environment is not established by this release. GUI behavior depends on host permissions, interactive desktop state and each application's accessibility support.

Known limits include pattern-based redaction, bounded searches, per-file rather than cross-file crash atomicity, direct-child-only process cleanup, and best-effort foreground checks. Read [SECURITY.md](SECURITY.md) before use.
