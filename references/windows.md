# Windows System and Local Tooling

Use for Windows filesystem, processes, terminals, environments, local services, package managers, and troubleshooting.

## Filesystem

Prefer direct file tools for listing, reading, writing, moving, and metadata. Use terminal only when it adds value such as globbing, transformation, archive tooling, or a project-native command.

Preserve unrelated content. Inspect scope before broad replacements or moves. Prefer reversible deletion where supported; permanent/bulk deletion is confirmation-gated.

## Terminal and process efficiency

Prefer PowerShell for Windows-native tasks and the project's own shell when appropriate.

- Reuse an existing interactive session for several related commands when supported.
- Otherwise combine compatible read-only or verification commands into one bounded invocation.
- Quote paths safely.
- Capture exit codes and enough output to verify success.
- Avoid opening a new PowerShell process for every tiny state check.
- Do not silently elevate privileges or weaken security controls.

`scripts/probe_environment.py` can collect common developer-tool availability in one call when environment facts are not already known.

## Project detection and environments

Use `scripts/project_detect.py` to identify common project markers and discovered package scripts without guessing commands. Respect project virtual environments, lockfiles, package managers, Java build tools, and repo-local configuration.

## Local services

For local web servers or background services:

1. inspect whether the intended process/port is already in use;
2. start the project-defined service with a persistent process tool when available;
3. read process output rather than repeatedly restarting;
4. verify the endpoint or health check;
5. terminate only the process created for the task unless the user requested broader process management.

## Windows automation

Use Startup/task scheduling only when explicitly needed by the task. Prefer application-supported startup mechanisms or Task Scheduler through legitimate system tooling. Do not create persistence outside the user's request, hide tasks, or bypass system policy.

## Troubleshooting

Inspect concrete evidence first: process state, service output, event/application logs when available, file/config state, environment variables, network response, or project logs. Make bounded fixes and verify them. Broad registry, boot, driver, firewall, account, or security-policy changes are confirmation-gated.

## Optional task process manager

Use a connector-owned persistent process session first. The optional runtime can also launch exact task-approved argv manifests, read bounded log tails, report alive/exit state, reuse a live label, check loopback HTTP, and stop its owned process tokens. No shell strings or arbitrary PID stopping API. Prefer direct long-lived executables: descendant process trees are not managed by this fallback. Use a connector with verified tree ownership for tools that fork/detach children. Stop sessions explicitly; EOF and normal runtime shutdown stop direct children, but abrupt runtime termination cannot guarantee cleanup. A live PID and HTTP response alone do not prove endpoint ownership.
