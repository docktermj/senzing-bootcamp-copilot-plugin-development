# GitHub Copilot host mechanisms

**Status:** verified against the official GitHub Copilot and VS Code documentation linked
below on 2026-10-19. A verified format does not mean that this plugin has been exercised in
every Copilot client; per-client execution remains a manual release gate in the development
repository's `docs/test-checklist.md`.

| Question | Finding |
| --- | --- |
| How does Copilot discover and load the extension? | **Verified.** VS Code Agent Plugins use a root `plugin.json`; skills live in `skills/`, MCP settings in `mcp.json`, and Copilot-only components in `com.github.copilot/`. VS Code discovers, installs, and manages agent plugins from the Agents window. The manifest uses the Agent Plugins 1.0 schema. |
| Where does its manifest live? | **Verified.** At the plugin root as `plugin.json`, with `$schema` set to `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. |
| Which lifecycle events exist? | **Verified for Copilot CLI hooks.** `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `agentStop`, and `preCompact` are declared in the Copilot hook reference. The stop adapter uses the documented `Stop` alias to receive the VS Code-compatible payload. This plugin does not currently configure a `preCompact` handler. |
| Can lifecycle events block, and what can they see? | **Verified, event-specific.** `preToolUse` can deny a tool call, and `Stop` can block turn completion and force continuation. `sessionStart` can contribute `additionalContext`; `sessionEnd` is used for cleanup and does not block. Hook commands receive event-specific JSON on stdin and run from the project root (`cwd: "."`), while their scripts resolve from the plugin root. |
| How are hooks declared and what may they execute? | **Verified.** Copilot plugin hooks are in `com.github.copilot/hooks/hooks.json`, version 1. Command hooks may invoke local scripts; scripts and paths must be validated for the selected harness. Hook behavior depends on the client/harness and workspace trust. |
| How is the extension's own root addressed? | **Verified.** Agent Plugins 1.0 and Copilot plugin formats provide `${PLUGIN_ROOT}`; the hook commands use it for bundled scripts. |
| Is model or effort selection exposed? | **Verified with a client-dependent limitation.** VS Code custom agents can declare an optional model and the user can select among models available to their account/client. There is no portable family-wide model or effort identifier. The bootcamp uses capability-oriented guidance and does not hard-code a model ID. |
| Can an MCP server be configured? | **Verified.** Agent Plugins discover MCP server configuration from root `mcp.json`; Copilot CLI and VS Code also support MCP servers. The inherited Senzing HTTP endpoint is retained in that portable file. |
| What if Senzing MCP tools are missing from the conversation? | **Recovery procedure; deferred-tool discovery is observed, not documented.** See [Senzing MCP tools unavailable](#senzing-mcp-tools-unavailable). |
| How is pre-compaction handled? | **Not wired in this build.** Copilot CLI documents a `preCompact` event, but this plugin does not configure it. The parent’s pre-compaction recap fold remains an advisory instruction; the bootcamper-facing recap checkpoint is the manual recovery path. |

## Copilot CLI Stop-hook visibility check

The documented [`agentStop` contract](https://docs.github.com/en/copilot/reference/hooks-reference#agentstop--subagentstop-decision-control)
uses `reason` as the prompt for a continuation. In an isolated Copilot CLI 1.0.109 interactive
check, the terminal also rendered the plugin's Stop-hook reason directly after the assistant's
message. This identifies the observed turn-check text as the hook reason, not an assistant echo
or a separate host diagnostic. Keep this reason user-facing; do not label it internal or instruct
the assistant to conceal it. The current hook asks for the module's prescribed closing question
in user-facing language and requires an actual question mark after its single 👉 marker.

The prompt-mode check did not display the reason in CLI output, so this behavior is specific to
the tested interactive session. These synthetic checks reproduce the hook text, but do not
establish that every client or any different, unreported message has the same source. See the
evidence in `docs/test-records/0.6.1.md`.

## Senzing MCP tools unavailable

Use this when Senzing MCP tools cannot be called in the conversation. These are recovery
measures, not a confirmed root-cause fix or a guarantee against recurrence.

1. **Discover deferred tools before declaring an outage.** *Observed, not documented in the
   Copilot documentation:* the host can list Senzing tools as deferred, so they must be
   discovered through the host's tool-search facility before they can be called.
2. **Call `get_capabilities` live.** A successful result (server version and tool list) shows
   the tools are exposed and the endpoint is reachable.
3. **Retry once** if the call fails. Do not loop.
4. **Separate tool exposure from endpoint reachability.** An endpoint that answers direct
   requests does not prove the tools are exposed in the conversation. In Copilot CLI,
   `/mcp list` shows live server status and `/mcp get <server-name>` opens its details and
   tools. The shell commands `copilot mcp list` and `copilot mcp get <name>` show
   configuration, not live status. Project-level servers load only after folder trust, and
   a disabled server is not used. In VS Code, a configuration is not proof of use: complete
   a tool call to verify.
   The documented interactive `/mcp reload` command rereads configuration and restarts
   servers, but is a user action; current Copilot CLI documentation does not describe a
   plugin-callable reconnect/rebind API. A reload alone is not proof of recovery; verify
   with a normal `get_capabilities` call.
5. **Preserve workflow state.** Do not change the connection configuration, and resume at the
   exact step without repeating completed work.
6. **After one failed retry, stop and tell the Bootcamper** what was checked. Report a
   suspected server defect for Senzing feedback; submitting it needs the Bootcamper's
   explicit approval.

## References

- [Agent plugin authoring reference](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)
- [Agent skills in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Custom agents in VS Code](https://code.visualstudio.com/docs/agent-customization/custom-agents)
- [Configure agent hooks in VS Code](https://code.visualstudio.com/docs/agent-customization/hooks)
- [GitHub Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Adding MCP servers for Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
- [Add MCP servers in VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers)

The VS Code hooks experience is currently documented as preview. Copilot CLI and cloud-agent
support differ; this child targets the Copilot plugin format, not cloud-agent execution. Any
claim that a particular hook payload or client version behaves identically must be established
by the recorded host test, not inferred from shared file formats.
