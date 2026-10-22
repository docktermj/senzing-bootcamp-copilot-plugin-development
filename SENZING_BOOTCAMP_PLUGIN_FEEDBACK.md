# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** 2026-10-20

## Your Feedback

## Improvement: Senzing MCP capability requests fail at transport

**Date:** 2026-10-20
**Module:** Bootcamp graduation
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** mcp-server — Senzing MCP tool requests failed before returning results, independent of the bootcamp workflow.
**Upstream:** submission failed: MCP transport error

### What happened

During graduation, two `senzing-get_capabilities` calls failed before returning a result. Earlier `reporting_guide` requests during Query, Visualize, and Discover also failed at the transport layer. The returned messages included the exact phrases `MCP request failed: Transport send error` and `error sending request for url (https://mcp.senzing.com/mcp)`.

### Why it matters

The capability and reporting requests could not provide the MCP-grounded reference information required by the graduation workflow. Work could continue from verified local artifacts, but MCP-dependent checks remained unavailable.

### Suggested fix

None provided; the transport failure did not identify a cause.

### Context when reported

- **Time:** 2026-10-20 17:45 local
- **Plugin version:** Unknown (the expected manifest locations were absent)
- **Workstation:** Ubuntu 24.04 (x86_64)
- **Model / effort:** Unknown
- **Context size:** Unknown
- **Module / step:** `graduation` / pre-checks
- **Recent questions:** Ready to stop the visualization server?; Would you like to continue to the Graduation module?; What name would you like printed on your Certificate of Completion?
- **Bootcamper responses:** Yes; yes; supplied a display name (omitted).
- **Behind the scenes:** Graduation pre-checks called `senzing-get_capabilities`; the request failed before returning capabilities. Earlier reporting-guide calls had also failed during Query, Visualize, and Discover.
- **Observed problem:** The Senzing MCP tool calls returned transport errors instead of results.
- **Expected behavior:** `senzing-get_capabilities` returns the server's capabilities overview so the workflow can use current MCP references.
- **Divergence:** The client could not send the request to the MCP endpoint, so no tool result was available to ground the required checks.
