# Windows GUI, Mouse, Keyboard, and Window Control

Use only when a task genuinely requires desktop UI interaction.

## GUI is fallback

Prefer, in order: connector/API -> filesystem -> terminal/process -> browser-native automation/API -> desktop GUI. Do not click through a workflow that can be completed directly through a structured action.

## Reliability model

Never depend on a long blind coordinate macro. Establish the target window before keyboard or mouse input.

Preferred targeting order:

1. native app/browser automation or accessibility controls if available;
2. Windows UI Automation by HWND/process and unique accessibility selector;
3. URL navigation and app shortcuts;
4. process/window-title identification and foreground activation;
5. raw coordinates only when necessary.

Use `scripts/window_control.ps1` to list/find/activate ordinary top-level windows when native GUI tooling is unavailable. Use `scripts/gui_control.ps1` for screenshots and bounded pointer/keyboard actions.

## Efficient observe-act-verify

1. Verify the interactive desktop once at the start of a GUI segment.
2. Identify and activate the intended window.
3. Capture a screenshot at a decision point.
4. Execute a coherent small sequence.
5. Capture another screenshot when the UI result affects the next decision or final verification.

Do not screenshot after every trivial mouse move. Recheck focus before typing sensitive or consequential input, after window switches, or when the app may have opened a dialog.

## Helper deployment

If native GUI controls are unavailable, deploy the bundled scripts to a user-local path such as:

`%LOCALAPPDATA%\ChatGPT\WindowsLaptopOperator\`

Write exact copies from the skill. Do not modify them to bypass OS or product controls.

## `window_control.ps1`

Supported actions: `list`, `find`, `activate`, `active`.

Use it to obtain window title/process/handle and set the intended top-level window to foreground before GUI input. If activation cannot be verified, do not type blindly.

## `gui_control.ps1`

Supported actions include probe, screenshot, move, click, scroll, type, keys, and sequence.

The `sequence` action accepts bounded JSON operations so several deterministic UI actions can run in one helper process. Keep sequences short and coherent; include screenshots only at decision/final points.

Example shape:

```json
[
  {"action":"keys","keys":"^l"},
  {"action":"type","text":"https://example.com"},
  {"action":"keys","keys":"{ENTER}"}
]
```

Use raw coordinate clicks only after the correct active window and current screenshot make the target unambiguous.

## Boundaries

The helper acts only in the user's interactive desktop session. It must not bypass lock screen, UAC secure desktop, passwords, MFA, CAPTCHAs, app permissions, or platform restrictions.

Mouse/keyboard access does not remove confirmation gates. Stop before using GUI to perform destructive deletion, security weakening, account-security changes, purchases, transfers, trades, public-sharing changes, material legal acceptance, or secret transmission unless the relevant explicit authorization/confirmation requirement is satisfied.

## Window lock and UI Automation

Prefer the current host's native computer capability and obey its skill instructions. Do not use these helpers to bypass an unavailable or prohibited desktop capability. Through a permitted local terminal connector only, `uia_control.ps1` offers bounded inspect/find/invoke/focus/set-value using the Windows accessibility provider. First resolve an exact handle and PID with `window_control.ps1`, activate it, and verify foreground. Pass `-Handle <HWND> -ExpectedProcessId <PID>` on UIA calls; pass `-ExpectedHandle <HWND> -ExpectedProcessId <PID>` on all GUI input.

UIA selectors use exact `-Name`, `-AutomationId`, and/or `-ControlType` (for example Button or Edit). Mutation refuses missing/ambiguous matches, truncated trees, password controls, unsupported patterns and changed foreground. `-MaxNodes` caps traversal at 200; run with a connector timeout because an app accessibility provider can hang. Do not set-value on password/secret fields. Do not inspect unrelated account windows.

The input helper checks HWND/PID before every operation and each Unicode character. Losing focus aborts. This is a best-effort guard, not an OS-level atomic focus lock; never automate secret typing or high-impact confirmation dialogs. Reinspect after dialog transitions instead of continuing an old sequence. Coordinate clicks must lie inside the locked window and outside another overlapping window. Screenshot capture may contain private pixels: restrict scope, inspect before sharing, never package captures.

Use one decision view and one final verification when useful. UIA set-value verifies the value without returning it; Invoke still needs an app-state check. Native browser automation precedes desktop/UIA for web tasks.
