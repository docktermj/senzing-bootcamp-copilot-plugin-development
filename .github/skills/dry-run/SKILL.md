---
name: dry-run
description: Exercise the generated Senzing bootcamp against a live GitHub Copilot client and Senzing MCP server in gated phases.
---

# dry-run

Run the bootcamp itself in a real Copilot client. Static validation and direct script execution
are not substitutes. Record each result in `docs/test-records/<PARENT_VERSION>.md`.

1. **MCP contracts:** confirm the live Senzing MCP endpoint is reachable; verify the required
   tools and representative responses. Re-verify every Senzing fact exercised. If this phase
   fails, stop and do not claim later phases passed.
2. **Hooks and scripts:** install the generated plugin in the target Copilot harness. Exercise
   `sessionStart`, `userPromptSubmitted`, `preToolUse`, `agentStop`, and `sessionEnd`; record
   actual payloads, return values, client/version, and whether denial/continuation behaved as
   expected. Do not infer behavior from JSON validation alone.
3. **Conversation:** walk at least one representative bootcamp module. Verify skill discovery,
   the MCP-first rule, one question per yielding turn, project write boundaries, progress
   persistence, and the closing question.
4. Do not begin a later phase when its prerequisites failed. For unavailable events such as
   pre-compaction, record the documented advisory degradation; do not mark an unrun test as
   passing.
5. Attach concise, reproducible evidence to the per-release record. This dry run does not publish
   or release the plugin.
