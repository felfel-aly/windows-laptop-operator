# Local Operator Performance Core

Use this reference for the default execution model on the authorized Windows computer.

## Fastest safe path first

Choose the narrowest capable mechanism in this order:

1. structured connector/API action;
2. direct filesystem action;
3. existing terminal/process session or one bounded command batch;
4. browser automation/API;
5. GUI control only when no faster deterministic route exists.

Do not manually reproduce a connector/API capability with GUI clicks when the direct action is available.

## Task-context cache

Within one user task, remember and reuse verified facts such as:

- connected device ID and online state;
- repository root, branch, HEAD, remotes, and pre-existing changes;
- project/runtime type and relevant virtual environment;
- project commands already discovered;
- files already read and their relevant contents;
- tests/checks already run and their result;
- active browser/site/deployment target;
- project-specific roots and governing docs;
- screenshots already inspected if UI state has not changed materially.

Do not rediscover these without a reason. Reverify when stale state could change correctness, and always before consequential destructive/security-sensitive actions.

## Batching

Aggressively reduce round trips when operations are independent and bounded.

Prefer:

- multi-file reads over one read per file;
- one repo snapshot helper over separate `git status`, `branch`, `rev-parse`, and `remote` calls;
- one terminal invocation for compatible read-only state checks;
- one `test_pipeline.py` execution for a known list of project checks;
- one coherent GUI sequence plus screenshots at decision points instead of screenshot-per-click;
- connector batch actions where a connector exposes them.

Do not batch unrelated destructive actions or hide failure boundaries that need separate decisions.

## Autonomy

For a clearly requested task, proceed through ordinary reversible steps without repeatedly asking whether to continue. Typical automatic steps include inspection, search, edits, normal file creation, dependency inspection, tests, lint/typecheck/build, bounded bug fixes, Git inspection, a required local feature branch, documentation lookup, API research, explicitly requested deployment, and verification.

Stop only for a real blocker, a project-governance approval point, or a confirmation gate in `security.md`.

## Error recovery

When something fails:

1. inspect the actual error;
2. identify the most likely root cause from evidence;
3. make the smallest justified correction;
4. rerun only the relevant failed check plus any necessary regression check;
5. continue toward the requested end state.

Do not blindly retry the same command. Do not dump an ordinary fixable error on the user if the available tools can safely diagnose and repair it.

## Low-noise execution

During work, be concise. Do not narrate every command or flood the chat with logs. Surface material decisions, failures, safety boundaries, and final verification.

For small tasks, use: inspect -> execute -> verify.
For large tasks, make a brief internal execution plan and continue without turning the plan into a long user-facing preamble.

## Cross-turn workspace memory

Use `workspace_lookup` for a known alias instead of searching the machine again. Git is always refreshed; config fingerprints and TTL decide whether project detection can be reused. Cache values are hints, never authority for edits, deployment or protected state. See `runtime.md`.

When the environment exposes orchestration, batch independent connector reads in one invocation (for example an available JavaScript orchestrator with `Promise.allSettled`), inspect every result, then handle dependent operations sequentially. Do not invent orchestration tools or parallelize approvals, edits to shared state, or dependent commands.
