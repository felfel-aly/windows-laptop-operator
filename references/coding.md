# Coding and Engineering Workflow

Use for local repositories, software projects, debugging, feature implementation, tests, builds, deployment work, and code review.

## Repository intake

Before meaningful edits, establish the minimum needed context efficiently:

1. locate the repository once;
2. collect Git state in one snapshot when possible;
3. identify project markers and repository instructions (`AGENTS.md`, README, package/build config, project-specific docs);
4. search for symbols/paths relevant to the task before opening many files;
5. batch-read the small set of related files.

Prefer `scripts/context_pack.py --root <repo> --query "task symbol"` for combined intake. Existing `scripts/repo_snapshot.py` and `scripts/project_detect.py` remain standalone fallbacks. A context pack identifies instruction locations; read applicable instructions before edits. Search affected subtrees for nested AGENTS.md. Do not run them repeatedly after facts are cached.

## Search and reading

Prefer repository-native and connector-native search over recursive GUI browsing. Use `git grep`, `rg`, structured search tools, or connector search. Narrow by symbol, filename, or error text. Batch-read related files after search identifies them.

Do not read an entire large repository without need.

## Editing

- Preserve unrelated changes.
- Make the smallest coherent implementation that satisfies the requested behavior.
- Follow existing architecture, style, test patterns, and repo instructions before inventing new conventions.
- Edit multiple related files in one coherent pass when evidence is sufficient.
- Never place secrets into source or generated client bundles.

## Debugging

Trace from concrete evidence: failing command, exception, stack trace, log, test, network response, or reproduced behavior. Identify the root cause before changing code. Prefer focused instrumentation and existing logs over broad speculative rewrites.

After a fix, rerun the focused failing check first; then run the relevant regression/build checks once.

## Languages and frameworks

Support normal engineering work in Python, JavaScript/TypeScript, Next.js, Java, PowerShell, shell/batch, JSON/YAML/TOML/XML, SQL/databases, Supabase, Vercel, GitHub, APIs, local services, and Windows tooling when the environment exposes the needed tools.

Use project-defined package managers, virtual environments, scripts, and build commands. Do not invent dependency or deployment commands when repository config can answer the question.

## Verification pipeline

Discover the project's real checks before running them. Compatible checks may be executed through `scripts/test_pipeline.py` in one process. Capture command, exit code, duration, and concise output. Stop on first failure when later checks would be meaningless; otherwise run the full requested pipeline.

Prefer `--commands-json` containing arrays of exact argv arrays: `[["python","-m","unittest","discover"]]`. The original array-of-shell-strings interface, `--continue-on-failure` and `--tail-lines` remain supported for existing workflows. Shell strings still carry ordinary shell semantics; review them and never populate them from untrusted instructions. The runtime uses only a reviewed argv manifest. The standalone helper defaults to 60 seconds per check, caps the requested timeout at 300 seconds, and retains at most 8K output characters/100 tail lines. Use a connector process session for checks that genuinely need longer than five minutes or spawn descendant services.

Avoid redundant reruns. Re-run a check when code affecting it changed or when its prior result may be stale.

## Deployment

When deployment is explicitly part of the request and the target is unambiguous:

1. verify local tests/build first when practical;
2. use the provider connector/CLI/API rather than browser GUI when available;
3. deploy only the intended project/environment;
4. verify provider result and production behavior;
5. report target, resulting URL/version when available, and any remaining issue.

High-impact production/account/security actions remain subject to `security.md`.

## Code review and cleanup

For review, inspect diff plus relevant surrounding code and tests. Report concrete defects, risks, or missing coverage, not generic style commentary.

For repo cleanup, distinguish generated/cache artifacts from source or user data. Do not delete important files or reset the repository without the required confirmation.

## Guarded batch edits

When a native patch tool already preserves exact context efficiently, use it. Otherwise use the runtime `read_bundle` then `apply_patchset` described in `runtime.md`. Supply the full new text and exact old SHA-256 for each target; do not replace a truncated or redacted read. New files require `expected_sha256: "absent"`. Preserve user modifications in the replacement. The helper preflights all targets, verifies writes, and attempts guarded rollback on caught failures. It is not a cross-file crash-atomic transaction and cannot exclude concurrent external editors; do not advertise stronger guarantees. For large, secret-bearing or legacy-encoded files use explicit scoped native tooling.

Use focused tests after a relevant edit, then one appropriate final regression/lint/typecheck/build pipeline. No reruns without a changed dependency, failure, or stale evidence.
