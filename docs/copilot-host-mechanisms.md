# GitHub Copilot host mechanisms

**Status:** verified against the official GitHub Copilot and VS Code documentation linked
below on 2026-10-19. A verified format does not mean that this plugin has been exercised in
every Copilot client; per-client execution remains a manual release gate in the development
repository's `docs/test-checklist.md`.

| Question | Finding |
| --- | --- |
| How does Copilot discover and load the extension? | **Verified.** VS Code Agent Plugins use a root `plugin.json`; skills live in `skills/`, MCP settings in `mcp.json`, and Copilot-only components in `com.github.copilot/`. VS Code discovers, installs, and manages agent plugins from the Agents window. The manifest uses the Agent Plugins 1.0 schema. |
| Where does its manifest live? | **Verified.** At the plugin root as `plugin.json`, with `$schema` set to `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. |
| Which lifecycle events exist? | **Verified for Copilot CLI hooks.** `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, and `agentStop` are declared in the Copilot hook reference. There is no documented `preCompact` event in that event list. |
| Can lifecycle events block, and what can they see? | **Verified, event-specific.** `preToolUse` can deny a tool call, and `agentStop` can block turn completion and force continuation. `sessionStart` can contribute `additionalContext`; `sessionEnd` is used for cleanup and does not block. Hook commands receive event-specific JSON on stdin and run in the project/plugin environment. The stop adapter requires `last_assistant_message`; the manual check must confirm this field in each target harness. |
| How are hooks declared and what may they execute? | **Verified.** Copilot plugin hooks are in `com.github.copilot/hooks/hooks.json`, version 1. Command hooks may invoke local scripts; scripts and paths must be validated for the selected harness. Hook behavior depends on the client/harness and workspace trust. |
| How is the extension's own root addressed? | **Verified.** Agent Plugins 1.0 and Copilot plugin formats provide `${PLUGIN_ROOT}`; the hook commands use it for bundled scripts. |
| Is model or effort selection exposed? | **Verified with a client-dependent limitation.** VS Code custom agents can declare an optional model and the user can select among models available to their account/client. There is no portable family-wide model or effort identifier. The bootcamp uses capability-oriented guidance and does not hard-code a model ID. |
| Can an MCP server be configured? | **Verified.** Agent Plugins discover MCP server configuration from root `mcp.json`; Copilot CLI and VS Code also support MCP servers. The inherited Senzing HTTP endpoint is retained in that portable file. |
| How is pre-compaction handled? | **Verified gap.** The published Copilot hook event list does not include `preCompact`. The parent’s pre-compaction recap fold is therefore retained as an advisory skill instruction and is not claimed as an automatic hook. The bootcamper-facing recap checkpoint remains available for manual recovery. |

## References

- [Agent plugin authoring reference](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)
- [Agent skills in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Custom agents in VS Code](https://code.visualstudio.com/docs/agent-customization/custom-agents)
- [Configure agent hooks in VS Code](https://code.visualstudio.com/docs/agent-customization/hooks)
- [GitHub Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Adding MCP servers for Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)

The VS Code hooks experience is currently documented as preview. Copilot CLI and cloud-agent
support differ; this child targets the Copilot plugin format, not cloud-agent execution. Any
claim that a particular hook payload or client version behaves identically must be established
by the recorded host test, not inferred from shared file formats.
