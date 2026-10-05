# Installation and updates

## 1. Download and inspect

```powershell
git clone https://github.com/felfel-aly/windows-laptop-operator.git
Set-Location windows-laptop-operator
python --version
git --version
```

Use Windows 10/11 and Python 3.12 or newer. The Python code has no pip dependencies. Git is required for Git work; ripgrep is optional. Use Windows PowerShell 5.1 for the desktop helpers. No Administrator privileges or execution-policy changes are required by this project; if your policy blocks a script, follow your organization's approved review/signing process.

Read [SECURITY.md](SECURITY.md), inspect the source, then validate the public copy:

```powershell
python -m unittest discover -s tests -v
python tools/privacy_scan.py
python tools/package_skill.py
```

The final command creates `dist/windows-laptop-operator.zip` with a single top-level skill folder. It excludes Git history, local runtime state, caches and anything outside `PUBLIC_FILES.json`.

## 2. Install the skill in your host

In ChatGPT desktop, open **Skills**. If your version exposes an upload/import action, select the generated ZIP, review the skill, and enable it. Select it with `@` in a new chat. Skill-management availability and labels can differ by account or workspace policy; if upload is unavailable, consult the current [official skill guide](https://learn.chatgpt.com/docs/build-skills). This project is a standalone source package, not a published plugin-directory listing.

For local Codex, place the complete skill folder at `$HOME/.agents/skills/windows-laptop-operator`, or ask `$skill-installer` to install this GitHub repository. Invoke `$windows-laptop-operator`; restart if it is not discovered. The [official guide](https://learn.chatgpt.com/docs/build-skills) documents local discovery. Do not keep duplicate skill copies with the same name.

Installing the skill does not install a Windows connector or grant device access. A cloud sandbox containing the scripts is not your laptop. Continue with the connection and runtime setup below.

## 3. Connect your Windows computer

Follow [connector setup](references/connector-setup.md). Use a provider-supported Remote Desktop Commander installation or another authorized connector that actually offers local execution. This repository does not distribute that provider's installer or guess its endpoint.

Verify the connected device and least required scope. The connector must be able to run Python on that Windows host. A persistent session additionally needs retained stdin/stdout; without it, use one-shot helpers. GUI tasks require separately permitted access to the interactive desktop.

## 4. Deploy a stable runtime

From the repository root, the following creates a versioned runtime directory. It copies an explicit helper list only, refuses to overwrite an existing version, and checks hashes. It leaves previous installations and private workspace metadata in place.

```powershell
$operatorVersion = '0.1.0'
$operatorBase = Join-Path $env:LOCALAPPDATA 'ChatGPT\WindowsLaptopOperator'
$operatorTarget = Join-Path $operatorBase "runtime-$operatorVersion"
if (Test-Path -LiteralPath $operatorTarget) { throw 'Version already exists; inspect it before updating.' }
$operatorNames = @(
  'operator_core.py','operator_runtime.py','context_pack.py','process_manager.py',
  'project_detect.py','repo_snapshot.py','test_pipeline.py','probe_environment.py',
  'uia_control.ps1','window_control.ps1','gui_control.ps1'
)
New-Item -ItemType Directory -Path $operatorTarget -Force | Out-Null
foreach ($operatorName in $operatorNames) {
  $operatorSource = Join-Path '.\scripts' $operatorName
  $operatorCopy = Join-Path $operatorTarget $operatorName
  Copy-Item -LiteralPath $operatorSource -Destination $operatorCopy
  if ((Get-FileHash -LiteralPath $operatorSource).Hash -ne (Get-FileHash -LiteralPath $operatorCopy).Hash) {
    throw "Hash mismatch: $operatorName"
  }
}
```

Keep the chosen runtime path in your **private** host configuration. No public `runtime-info.json` is supplied. Existing installations can keep using their existing runtime path until the new version passes a smoke test. Do not copy an old registry or screenshots into this repository.

## 5. Verify a session

Choose a disposable ordinary project folder and set `$operatorProject` to its absolute path. The next command binds the helper to that folder; it does not enable writes or command execution.

```powershell
$operatorProject = (Get-Location).Path
python -u (Join-Path $operatorTarget 'operator_runtime.py') --root $operatorProject
```

Send these lines to the same process, waiting for each response:

```json
{"id":1,"op":"hello"}
{"id":2,"op":"health"}
{"id":3,"op":"project_snapshot"}
{"id":4,"op":"shutdown"}
```

Verify protocol 1, the intended root, disabled writes, successful results and process exit. For a non-Git folder, context packs report `is_git: false`; calling `repo_snapshot` itself still requires Git. Do not test against a sensitive project just to prove installation.

For GUI capability, when your host permits local desktop helpers, run this read-only probe:

```powershell
powershell.exe -NoProfile -File (Join-Path $operatorTarget 'gui_control.ps1') -Action probe
```

It does not click, type or capture a screenshot. UIA details and exact window parameters are in [GUI control](references/gui-control.md).

## 6. Workspace aliases and commands

Registration is optional and explicit. Start a task session with `--allow-writes` for a folder you intend to register, then send:

```json
{"id":1,"op":"workspace_update","args":{"alias":"demo-project"}}
{"id":2,"op":"workspace_lookup","args":{"alias":"demo-project"}}
{"id":3,"op":"shutdown"}
```

The private registry is `%LOCALAPPDATA%\ChatGPT\WindowsLaptopOperator\workspace_registry.json`. It contains local paths and project metadata. Do not publish it. Lookup refreshes live state and returns `cache_authority: false`. Non-Git projects have no Git change-tracking guarantee.

For task processes, create a reviewed manifest **outside the repository**, mapping labels to argv arrays. For example, `{"check":["python","-c","print('operator-process-ok')"]}`. Pass its path with `--commands`, then use `process_start`, `process_status` and `shutdown` as documented in [the protocol](references/runtime.md). Review every command's side effects even if helper writes are disabled. Use the actual intended interpreter when multiple Python installations exist.

## Updates and rollback

1. Stop task-owned sessions cleanly and preserve any private local registry separately.
2. In an unmodified download clone, fetch the new release and inspect its changelog and diff. Preserve local changes before updating; do not reset over them.
3. Run tests and the privacy scan, build a new ZIP, and replace the installed skill through your host's supported workflow.
4. Deploy scripts to a new version directory using the explicit list and hash checks above. Smoke-test it before changing the connector's runtime path.
5. If a regression occurs, point the connector back to the previous version. Do not roll back project files or clear workspace history as part of a runtime update.

## Troubleshooting

| Symptom | Check and response |
|---|---|
| Skill is visible but PC is unavailable | Verify the local connector is connected to the intended device; skill installation alone is insufficient |
| Python/Git not found | Check the connector's environment and use the intended executable path; do not dump all environment variables |
| Git discovery fails | Confirm the root, permissions and repository health; do not relabel an error as a non-Git folder |
| JSON request fails | Use one object per line, numeric IDs, documented operation names and relative file paths; errors are deliberately sanitized |
| Writes refused | Verify task authorization, session `--allow-writes`, file bounds, path restrictions and exact original hashes |
| Registry busy | Check for an active writer; inspect stale locks only after verifying the owner has exited |
| Workspace stale/moved | Reverify that project only and explicitly refresh registration; do not crawl the whole profile |
| UIA target missing/truncated | Reinspect the intended app with bounded selectors; do not invoke ambiguous results |
| Foreground lock lost | Stop input and resolve the current HWND/PID again |
| Desktop probe unavailable | Check interactive session and host policy; use supported native tools instead of bypassing restrictions |
| Child service remains after shutdown | The fallback owns direct children only; inspect verified descendant ownership through your connector |
| Output contains sensitive details | Do not share raw output; review locally and provide a minimal sanitized reproduction |

Only smoke-tested host combinations are claimed in the release notes. Connector-specific setup and account access remain provider responsibilities.
