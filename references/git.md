# Git Operating Rules

Use for any Git-managed repository.

## Snapshot once

Before meaningful edits, determine in one bounded snapshot when possible:

- repository root;
- current branch;
- HEAD;
- working-tree status;
- staged changes;
- modified/untracked files;
- remotes.

Use `scripts/repo_snapshot.py` when useful. Cache the result for the task and refresh only after edits/commits or when correctness requires it.

## Preserve user work

Never blindly reset, clean, checkout over, restore, or discard unrelated changes. Inspect diffs before staging or committing. Keep task changes separable from pre-existing changes.

## Branches and commits

Create a local feature/task branch when repository/project workflow requires it or the user explicitly requests it. Do not create branches as ceremony for tiny non-Git tasks.

Commit only when requested or when a project-specific approved workflow requires a checkpoint. Before commit, verify intended files and exclude secrets, generated private data, and unrelated changes.

Never push automatically unless the user explicitly requested or clearly authorized the push and the destination is unambiguous.

## Completion state

For meaningful repo work, report exact final branch/HEAD plus modified, staged, and untracked state. Use one final snapshot rather than multiple redundant Git calls.
