# Change-aware verification contracts

Choose the relevant contract at intake. Record evidence in the task ledger and reuse it while inputs remain unchanged. Do not run tests merely to restate an implementation.

| Task | Required completion evidence |
|---|---|
| Code/debug | Reproduce or establish the failing behavior; focused relevant check after correction; appropriate final regression/lint/typecheck/build once; reviewed final diff; fresh Git state |
| Files | Reread or list exact targets; verify requested contents/names/counts; expected hashes for previously read files when overwriting |
| GUI | Exact window/process and foreground established; bounded supported action; final app state verified through accessibility or a useful screenshot |
| Deployment | Appropriate local checks; provider deployment/version result; actual intended production endpoint/health; do not infer rollout from command exit alone |
| Connector write | Read back the changed remote object when supported; distinguish accepted request from observed completed state |
| Local server | Owned session/PID plus fresh logs; intended endpoint responds; ownership verified where necessary; stop only task-owned processes |
| Restricted project | Follow the project owner's current operating limits and evidence requirements; see `protected-projects.md` |

Before each rerun ask what changed that invalidates prior evidence. A focused failing test comes first. If fixes change other relevant behavior, broaden final regression once. An unrelated pre-existing failure is reported separately rather than silently repaired or relabeled as passing. Preserve mandatory project checks even when optimizing latency.

Record each distinct failure, current hypothesis and attempted correction. Retry only with a new justified change or new evidence. After repeated failure with the same cause, stop thrashing and name the concrete missing capability/input. Ordinary in-scope reversible recovery does not need a new permission question. Real economic trials are never retried to seek a better outcome.
