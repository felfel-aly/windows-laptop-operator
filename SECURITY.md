# Security and privacy

## Trust boundary

The user's authorization, host permissions, Windows account permissions and connector controls are the access boundary. The skill and helper process are not a sandbox, credential vault, remote-access service or approval engine. Run them as a normal user against a deliberately selected project.

The runtime accepts stdio JSONL only. It creates no control listener, scheduled task, service, startup entry or permanent daemon. Approved processes can make their own network requests and filesystem changes; review their behavior separately.

`--allow-writes` enables helper patching and workspace registration. It does **not** prevent side effects from commands supplied using `--commands`. Review exact argv and project code before execution. Direct Python module calls also bypass the runtime's capability switch.

## Data handled locally

- Context packs can contain absolute local paths, file names, branch names, project metadata and bounded source snippets.
- The opt-in workspace registry stores aliases, roots, detection metadata, branch/HEAD, timestamps and config hashes. It is private machine state even without credentials.
- Process output remains in a bounded in-memory buffer in this helper, but the connector/chat may retain tool output under its own policy.
- Screenshots and accessibility text may expose sensitive application content. Capture only the task's needed view and review before sharing.
- The helpers contain no analytics or telemetry client. Information returned to the assistant still travels through the chosen host/connector.

Common credential paths and text patterns are refused or redacted. Pattern matching cannot identify all secrets, personal data or proprietary content. Never deliberately send credentials, environment dumps, private keys, cookies or sensitive databases through the helpers.

## Implementation limits

File guards reject traversal and common protected paths, check expected hashes and verify replacements. They are defense in depth. Concurrent same-user path replacement remains possible; stop competing editors. Replacement can affect ACL inheritance or alternate streams. Multi-file edits are not crash-atomic.

Process ownership is limited to direct children. Abrupt termination and detached descendants require connector-level inspection. A loopback HTTP response does not prove that the owned process serves that port.

Window/PID/focus checks reduce accidental GUI input but are not an atomic OS lock. Do not use the input helpers for secrets, secure desktops or high-impact confirmation dialogs. Accessibility providers can hang; use connector timeouts. Respect host restrictions even if a script could technically perform the action.

## Before publishing a fork or release

Run `python tools/privacy_scan.py` and review the complete diff and `PUBLIC_FILES.json`. The scanner refuses unlisted files, common private-state names, links, machine-specific paths and recognized credential patterns without printing matching values. Build archives only with the provided packager. A clean scan is supporting evidence, not a guarantee that arbitrary source is safe to publish. Human review remains necessary.

Never add `.env` files, local registries, runtime-info files, command manifests, screenshots, logs, credentials, caches, databases, private context packs or project state. `.gitignore` is only a convenience; it does not remove already tracked content or Git history.

## Reporting a vulnerability

Use GitHub's private **Report a vulnerability** feature if it is enabled for this repository. If unavailable, open a minimal issue asking the maintainer for a private reporting channel, without exploit details or sensitive material. Do not attach real device IDs, credentials, full logs or private project files. Use synthetic examples. No guaranteed response-time commitment is made for this community project.
