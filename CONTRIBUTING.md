# Contributing

Use a fork and a focused pull request. Explain the concrete problem, expected behavior, verification and material limitations. Keep the skill instructions aligned with actual helper behavior.

## Development

Use Python 3.12+ and Git. The helpers and tests use the standard library. Windows desktop helpers should be checked with Windows PowerShell 5.1 in an authorized interactive session. Tests use disposable fixtures; do not use a real personal project, registry or desktop action as a default test fixture.

```powershell
python -m unittest discover -s tests -v
python tools/privacy_scan.py
python tools/package_skill.py
```

For a new public source file, review it and add its relative path to `PUBLIC_FILES.json`. Do not add generated state to make the scanner pass. Review runtime changes for Windows behavior, bounded output, clear failures, process ownership and privacy. Add a focused behavioral regression test when changing a guard or protocol contract.

Keep the protocol version stable for compatible changes and document breaking changes. Update `CHANGELOG.md`, relevant references and installation instructions when behavior changes. Do not claim stronger atomicity, redaction, sandboxing, GUI locking or process-tree guarantees than the code provides.

## Release checklist

1. Review the complete diff and allowlisted files; verify no private paths, credentials, project profiles or machine state were introduced.
2. Run tests, privacy scan and packaging on the intended source. Inspect ZIP entries and test the runtime with a disposable fixture.
3. Update version references and release notes with actual tested environments and limitations.
4. Commit only the public inventory. Inspect Git history and remote destination before an explicitly authorized push.
5. Verify the repository README, links, source tree and downloadable artifact after publication. A successful push alone does not verify rendering.

Contributions are submitted under the repository's MIT license. Use only material you have the right to contribute. Report security issues using [SECURITY.md](SECURITY.md), not public logs or private data dumps.
