# Remote Desktop Commander and other local connectors

The skill can use Remote Desktop Commander or an equivalent authorized local execution connector. No connector implementation, installer, server address, device ID or credential is bundled. Names refer to capability options, not a claim of affiliation or a guaranteed available tool schema.

## Setup procedure

1. Obtain the connector from its verified provider through your host's supported app/plugin directory or your organization's approved distribution. Follow that provider's current Windows installation and pairing documentation. Do not reuse an endpoint from someone else's configuration.
2. Review the connection's requested access. Connect only the intended Windows computer and grant the scope needed for your tasks. Keep pairing information and credentials in the provider's secure flow, outside this repository.
3. Confirm the device is online through the connector. Inspect the available operations and verify a harmless local command such as the Python version. Device identifiers stay in private session state.
4. Deploy the runtime using [INSTALL.md](../INSTALL.md). Give the agent the verified local runtime path through private host configuration.
5. For a persistent runtime, verify the connector exposes a process/session handle, stdin writes, stdout reads and exit status. Send `hello`, then `shutdown`; confirm the same process responds and exits.
6. For desktop tasks, separately verify host permission and the intended interactive session. Start with a read-only probe and accessibility inspection before authorized input.

## Capability mapping

| Connector exposes | Supported approach |
|---|---|
| Native file/Git/process actions | Prefer those actions when they meet the task |
| Terminal execution only | One-shot `context_pack.py`, `repo_snapshot.py` or project detection |
| Retained stdin/stdout sessions | Optional JSONL runtime for multiple related operations |
| Native Windows UIA | Prefer the native supported implementation |
| Permitted desktop-capable PowerShell | Bundled window/UIA/GUI fallback |
| Only cloud files or GitHub | Remote repository work only; no implied Windows access |

If the provider does not expose a required capability, report the missing capability and use a supported alternative. Do not add a public listener, weaken Windows controls, or route around a disabled computer-use capability. A GitHub publication does not create a ChatGPT marketplace connection.
