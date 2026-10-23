# Copilot interaction contract

The curriculum and expected bootcamper outcomes remain parent-owned. This document records how
the GitHub Copilot host preserves the parent interaction contract and where host enforcement is
weaker.

- Follow the active curriculum skill and ask only the question or gate it specifies. Skills are
  portable Agent Skills; they are loaded from the plugin's `skills/` directory.
- Treat natural-language interactions as authoritative. Do not depend on parent-host slash
  command names or transcript formats.
- The Copilot `Stop` hook may request a continuation when an active bootcamp turn does not end
  with its required closing question. It uses the documented VS Code-compatible payload to read
  the assistant message. The hook is a safety net, not a replacement for question-by-question
  skill instructions.
- `preToolUse` invokes the inherited write gate and converts its explicit denial to Copilot's
  `permissionDecision: deny` response. The CLI payload's `toolCalls` and `apply_patch` targets are
  normalized before the write gate runs; tests must confirm both in-project allowance and
  out-of-project denial.
- `sessionStart`, `userPromptSubmitted`, and `sessionEnd` invoke the inherited lifecycle helpers
  through the Copilot adapter. The adapter returns only Copilot hook output fields and reports
  helper failures on stderr with a nonzero exit.
- Copilot CLI documents a `preCompact` event, but this plugin does not configure a handler in
  this build. Keep the recap checkpoint current at each skill-defined step boundary; manual
  guidance remains the fallback when compaction happens.
- Model selection and effort are client/account dependent. Follow the curriculum's
  interface-specific guidance: use its documented `/model` and `/effort` commands only in
  Copilot CLI; in other clients, describe the recommendation and direct the bootcamper to that
  interface's controls. Do not assume a model identifier or command is portable across clients.
- The live Senzing MCP server remains mandatory for Senzing facts. A plugin's MCP configuration
  does not count as evidence that the server is reachable; check it during the dry run.

The exact host requirements and their recorded verification status are in
[`copilot-host-mechanisms.md`](copilot-host-mechanisms.md). A passing static check cannot stand
in for the per-release manual record.
