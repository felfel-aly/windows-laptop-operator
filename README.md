# Windows Laptop Operator

A reusable skill and small Windows helper runtime for working with local projects, files, Git, task processes, and desktop applications through an **already authorized connector**.

The skill tells an agent how to choose tools, inspect current state, carry out a scoped task, and verify the result. The optional Python runtime batches related operations over standard input/output. PowerShell helpers provide Windows UI Automation and guarded GUI fallback where the host permits them.

**Start with [INSTALL.md](INSTALL.md).** Installing a skill does not connect a PC. This repository does not include Remote Desktop Commander, a remote-access server, credentials, or a hosted service.

## What it does

| Capability | Behavior |
|---|---|
| Project context packs | Fresh Git state, project markers, language hints, instruction locations, config hashes and bounded literal search |
| Workspace memory | Opt-in aliases for Git and non-Git projects; live state checks and cache invalidation |
| Git snapshots | Branch/HEAD, staged/modified/untracked paths, rename information and explicit truncation |
| Guarded file edits | Expected SHA-256 checks, bounded replacements, verified writes and guarded rollback after caught failures |
| Task processes | Reviewed named commands, owned process tokens, bounded output, exit status and sequential checks |
| Windows accessibility | Exact window/process targeting, bounded control inspection and unique-selector actions |
| GUI fallback | Screenshots, mouse and keyboard helpers with foreground/window checks |

Project detection recognizes common Python, Node, Java, Rust, Go and .NET markers, plus root-level JavaScript, TypeScript, PowerShell and MATLAB hints. A plain `.m` file is reported as MATLAB-or-Objective-C unless clearer MATLAB evidence exists. Detection does not install dependencies or execute project code.

## Architecture

```text
ChatGPT / Codex + SKILL.md
          |
          v
Authorized local connector or native local tools
          |
          +--> direct file / Git / browser operations
          |
          +--> task-scoped Python stdio runtime
          |      +--> context, hashes, guarded edits
          |      +--> private local workspace registry
          |      +--> reviewed direct child processes
          |
          +--> Windows UIA / GUI helpers, if permitted
```

The runtime has no control socket, HTTP listener, service, scheduled task, or startup hook. “Persistent” means one process reused during an active task, ending on `shutdown` or EOF. Its optional HTTP health check is an outbound loopback request, not a control server.

## Quick start

After cloning this repository and installing the requirements:

```powershell
python .\scripts\context_pack.py --root (Get-Location).Path
python .\scripts\operator_runtime.py --root (Get-Location).Path
```

In the runtime's stdin, send one JSON object per line:

```json
{"id":1,"op":"hello"}
{"id":2,"op":"project_snapshot"}
{"id":3,"op":"shutdown"}
```

Expect `ok: true`, protocol `1`, and `writes: false` from `hello`. The process exits after shutdown. A connector can send the same lines through a retained process session. One-shot context packs also work when the connector cannot retain stdin.

## Example requests

- “Use Windows Laptop Operator. Inspect this repository and explain the failing test before changing anything.”
- “Use Windows Laptop Operator. Fix the selected Java project and run its relevant checks. Preserve my existing edits.”
- “Register this folder as `demo-project`, then show the context pack. Do not run project code.”
- “Inspect the selected Windows app's accessible controls. Do not click or type yet.”
- “Start this reviewed development command, verify its response, then stop the process you started.”

The agent still needs the device and project selection, available tools, and authorization for the actual action.

## Requirements and limitations

- Windows 10/11 for desktop helpers; Python 3.12+ recommended (3.14 tested in this release), Git for repository operations, Windows PowerShell 5.1 for desktop helpers. Python helpers use the standard library. `rg` is optional.
- An authorized local execution connection. A GitHub/Drive connector alone cannot access your Windows desktop.
- An interactive unlocked desktop for UIA/input. Elevated windows, secure desktops, app accessibility providers, focus changes, remote-session state and display scaling can limit operation.
- These helpers are **not a sandbox**. Command manifests can execute powerful code. `--allow-writes` gates helper edits and registration, not side effects of approved processes.
- Redaction is pattern based, not a guarantee. Context output includes local paths and may include source excerpts. Review before sharing.
- Searches and output are bounded; a truncated result is incomplete. Detection is heuristic. Git failures are not silently relabeled as non-Git.
- File writes are atomic per file, not across an entire patch or a crash. Concurrent same-user filesystem changes are outside the guarantees.
- Process cleanup covers direct children, not detached descendants. Use a connector with verified process-tree management for complex launchers.
- No private project profile or machine state is shipped. Specialized projects can use [owner-defined restrictions](references/protected-projects.md).

## Documentation

- [Installation, stable runtime setup, updates and troubleshooting](INSTALL.md)
- [Connector setup and capability checklist](references/connector-setup.md)
- [Runtime protocol, workspace registry and patch semantics](references/runtime.md)
- [Windows UIA and GUI usage](references/gui-control.md)
- [Security and privacy model](SECURITY.md)
- [Contribution and validation workflow](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md) and [release notes](RELEASE_NOTES.md)

## Repository layout

```text
SKILL.md                 Agent instructions
agents/openai.yaml       Display metadata
assets/icon.svg          Reusable icon
scripts/                 Python runtime and PowerShell helpers
references/              Focused operating guides
tests/                   Synthetic isolated regression tests
tools/                   Public-file scanning and packaging
```

Run `python -m unittest discover -s tests -v` and `python tools/privacy_scan.py` before sharing a modified copy. Build an upload ZIP with `python tools/package_skill.py`; it includes only the validated public-file inventory.

## License

[MIT](LICENSE). This is an independent community project, not an official OpenAI, Microsoft, or Remote Desktop Commander product. Third-party connectors have their own installation, access, and license terms.
