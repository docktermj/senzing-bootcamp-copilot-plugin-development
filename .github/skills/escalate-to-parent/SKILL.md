---
name: escalate-to-parent
description: File a self-contained parent issue for a defect owned by the canonical Claude bootcamp parent.
---

# escalate-to-parent

This is the only operation that may create or update an issue in
`docktermj/senzing-bootcamp-claude-plugin-development`. Use it only for parent-owned curriculum,
content, Senzing facts, or behavior shared by every host. Copilot packaging, hooks, lifecycle,
validation, and release issues stay local.

1. Verify ownership. A wording correction in shipped curriculum prose is parent-bound even when
   discovered in this child.
2. Re-verify every Senzing fact against the live Senzing MCP server before asserting it upstream.
   If a claim concerns the MCP server itself, route it to Senzing feedback instead.
3. Search the parent tracker for duplicates. If one exists, update it rather than filing a second.
4. File a self-contained issue that explains the observed behavior, expected behavior, paths,
   reproduction, evidence, and requested outcome. A parent maintainer must be able to act without
   this repository.
5. Cross-reference the parent issue and this child issue in both directions.
6. Add the `awaiting-parity` label to the local issue. Do not close it when the parent issue
   closes; closure waits until `parity-check` confirms the fix in a tagged parent release. If
   the parent issue is closed as not planned, surface the local issue for a human decision.

No other maintainer operation may write outside this repository. Public-mirror working-tree
propagation is a separate, constrained operation and is not permission to create or publish
issues elsewhere.
