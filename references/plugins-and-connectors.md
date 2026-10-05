# Plugins and Connectors

Use installed connectors when they materially improve the current task.

## Selection rule

Choose the most specific capable tool. Examples include local-computer connectors for filesystem/terminal/process work; GitHub for remote repo/PR/issue actions; Supabase for database/project operations; Google Drive for Drive files; Gmail for mail; Notion for workspace content; Malwarebytes for reputation checks; transcript tools for supported media; and web search for public current information.

Do not hard-code an assumption that any connector is installed or connected.

## Discovery without churn

If the required capability is not already visible in the current tool set, discover/search once when needed. Cache the availability result for the task. Do not repeatedly probe the same connector.

Do not enumerate every installed plugin for every request. Discovery should be driven by the actual task.

## Fallback

If the best connector is unavailable:

1. use the next-fastest safe mechanism that can actually accomplish the task;
2. state the missing capability only if it materially blocks completion;
3. do not claim access you do not have;
4. do not silently hand off to Work.

## Connector actions

Prefer structured read/write actions over browser GUI because they are faster, less fragile, and easier to verify. Respect each connector's authorization and permission boundaries.

For consequential writes, follow `security.md` even when a connector technically exposes the action.

## Optional profiles (inspect actual exposed schemas)

- Remote Desktop Commander or equivalent: batch file reads/search/metadata directly; retain device and interactive session IDs; do not repeatedly probe the device. Reuse supported process input/output sessions for the optional stdio runtime.
- GitHub: structured PR/issue/repository operations, with final object readback. Local Git remains the source of working-tree state.
- Supabase: structured project/database actions with scoped queries and the installed Supabase instructions; do not route through its dashboard when a direct action exists.
- Browser Use or equivalent: DOM/accessibility locators in an existing authorized session. Prefer this over desktop coordinates.
- Google Drive and Notion: direct file/page actions and targeted readback.
- Gmail: direct search/read/draft; send only when explicitly requested with unambiguous recipient/content.

Discover a missing capability once per task. Cache both availability and absence; recheck only after a connection change or failure. Connector names here are capability examples, not asserted installed tool names. If a supported orchestrator can issue independent calls concurrently, use one orchestration invocation and inspect each result; sequential dependencies stay sequential.
