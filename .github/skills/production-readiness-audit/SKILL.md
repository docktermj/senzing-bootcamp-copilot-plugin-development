---
name: production-readiness-audit
description: Review the complete generated GitHub Copilot bootcamp for consistency, coherence, completeness, and correctly routed findings.
---

# production-readiness-audit

Perform a static semantic review of the entire generated plugin after mechanical port checks
pass. This is not the transform validator and it is not a runtime dry run.

1. Inventory every shipped skill, document, script, hook, manifest, and MCP declaration.
2. Read the instructions as one bootcamp. Trace referenced skills/files, transitions, gates,
   user questions, lifecycle claims, and Senzing claims for contradictions, omissions, or
   unreachable behavior.
3. Review generated and Copilot-owned files, including interaction-contract and host-mechanism
   documents. Do not treat an unchanged parent file as automatically correct for Copilot.
4. Evaluate the parent `INV-NNN` dispositions and every active `CPINV-NNN`; identify uncovered
   guarantees and any claim stronger than its evidence.
5. Deduplicate findings. Route curriculum/content/shared behavior through `escalate-to-parent`;
   file Copilot-only defects locally.
6. Report the exact inventory reviewed, every finding or explicit clean area, ownership verdict,
   evidence, and issue URL. Semantic conclusions require human review; this skill does not turn
   the audit into a mechanical release pass.
