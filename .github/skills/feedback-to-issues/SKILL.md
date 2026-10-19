---
name: feedback-to-issues
description: Triage collected bootcamper feedback, verify Senzing claims, route each item, and deduplicate issue filing.
---

# feedback-to-issues

Read one collected feedback file and account for every item. Do not treat feedback as permission
to change curriculum or publish anything.

1. Parse the file and derive a stable content hash for each entry. Check the feedback ledger;
   previously processed entries are reported as already handled and are not filed again.
2. For every new item, verify each Senzing fact against the live MCP server. A server defect goes
   to Senzing feedback, not the parent repository.
3. Show an explicit **parent-bound** or **local** verdict for each item and give the reason.
   Parent-bound means curriculum/content/Senzing fact/shared behavior; local means Copilot
   packaging, hooks, lifecycle, validation, or release.
4. Search the appropriate issue tracker before filing. Different feedback entries can describe
   the same defect; update the existing issue instead of creating a duplicate.
5. File local issues here. Hand parent-bound issues to `escalate-to-parent`; do not write to the
   parent through another operation.
6. Append the entry hash, verdict, destination, issue URL, and outcome to the ledger only after
   successful handling, using `python3 tools/bootcamp-transform/feedback_ledger.py record
   --entry-file <file> --decision <parent-bound|local> --destination <tracker> --outcome
   <filed|updated|server-feedback>`. The ledger stores hashes, not feedback text. Never archive a
   failed or unverified item as processed.

Report every item's routing decision, evidence, deduplication result, and ledger state.
