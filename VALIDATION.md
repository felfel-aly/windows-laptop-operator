# Release validation

Validated on Windows with Python 3.14. No real project or deployed workspace registry was used for testing.

- 12 isolated behavioral tests passed: Git/non-Git context, Git error preservation, guarded patches, read-only gates, registry invalidation, named process execution, JSONL lifecycle, redaction and public-file scanning.
- Skill frontmatter and structure validation passed.
- All three PowerShell helpers parsed without syntax errors. Desktop control actions were not exercised during this publication task.
- The eleven shipped runtime helpers match the current deployed reusable source byte for byte at packaging time.
- Public inventory, relative documentation links, archive entries and recognized private-data patterns were checked before publication.
- Gitleaks 8.30.1 reported no leaks in the prepared source. The scanner binary was downloaded from its official release and checked against the published SHA-256 checksum.

These checks do not constitute an exhaustive security audit or prove compatibility with every Windows app or connector. No live GUI-input, trading, deployment or private-project test is claimed.
