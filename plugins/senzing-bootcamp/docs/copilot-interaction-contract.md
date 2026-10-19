# Copilot interaction contract

The curriculum and expected bootcamper outcomes remain parent-owned. This document records how
the GitHub Copilot host preserves the parent interaction contract and where host enforcement is
weaker.

- Follow the active curriculum skill and ask only the question or gate it specifies. Skills are
  portable Agent Skills; they are loaded from the plugin's `skills/` directory.
- Treat natural-language interactions as authoritative. Do not depend on parent-host slash
  command names or transcript formats.
- The Copilot `agentStop` hook may request a continuation when an active bootcamp turn does not
  end with its required closing question. The hook is a safety net, not a replacement for the
  question-by-question skill instructions. Confirm its event payload in the target client before
  relying on it.
- `preToolUse` invokes the inherited write gate and converts its explicit denial to Copilot's
  `permissionDecision: deny` response. A host test must confirm tool names, file-path payloads,
  and denial behavior.
- `sessionStart`, `userPromptSubmitted`, and `sessionEnd` invoke the inherited lifecycle helpers
  through the Copilot adapter. The adapter returns only Copilot hook output fields and reports
  helper failures on stderr with a nonzero exit.
- There is no documented Copilot `preCompact` event. Keep the recap checkpoint current at the
  skill-defined step boundaries; compaction recovery is advisory rather than an automatic host
  guarantee.
- Model selection and effort are client/account dependent. Describe capabilities and task goals;
  do not request a model by a fixed identifier.
- The live Senzing MCP server remains mandatory for Senzing facts. A plugin's MCP configuration
  does not count as evidence that the server is reachable; check it during the dry run.

The exact host requirements and their recorded verification status are in
[`copilot-host-mechanisms.md`](copilot-host-mechanisms.md). A passing static check cannot stand
in for the per-release manual record.
