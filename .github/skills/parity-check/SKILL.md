---
name: parity-check
description: Compare the generated GitHub Copilot bootcamp with an exact tagged parent release and file local parity issues.
---

# parity-check

Compare the checked-in Copilot plugin with a **tagged** release of
`Senzing/senzing-bootcamp-claude-plugin`. Never read `main`, `HEAD`, or an untagged commit.
This operation reads parent content and writes issues only to this child repository; it never
writes to the parent and does not run the transform.

1. Read `PARENT_VERSION` and `PARENT_COMMIT`. Resolve that exact parent tag and prove the commit
   matches. If the tag or commit cannot be verified, stop with the evidence.
2. Compare the generated plugin with the pinned tag, including every source file and both
   invariant registers. Distinguish a local Copilot adaptation from a real parity defect.
3. For every actionable delta, search this repository's issues for an existing report. Update an
   existing issue rather than filing a duplicate; otherwise file a self-contained local issue with
   the source tag, affected paths, expected parent behavior, Copilot behavior, and proposed owner.
4. Route curriculum, Senzing facts, or parent-owned behavior to `escalate-to-parent`; do not fix
   those defects in the child.
5. For an escalated issue, require the parent issue to be completed, the local issue to carry
   `awaiting-parity`, both issue bodies to cross-reference each other, and the fix commit to be
   an ancestor of the target parent tag. Confirm the development and public plugin trees match
   at that tag and that this checkout's parent pin names the same public commit.
6. Use `tools/bootcamp-transform/escalations.py` to produce the R7 verdict. Add `--apply` only
   when the verdict is `ready-to-close`; a parent `not_planned` closure is a human decision and
   never closes the local issue.
7. Report examined tag/SHA, each delta, deduplication evidence, and all issue URLs.

This is a read-and-triage operation. It does not write any working tree, run the transform, or
close an issue merely because a parent issue was closed.
