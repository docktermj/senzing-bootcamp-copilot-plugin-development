---
name: retrofit-from-public
description: Compare a checked-in Copilot public plugin snapshot with the development build and file routed issues without writing a working tree.
---

# retrofit-from-public

Compare the development build with the public Copilot plugin repository
`Senzing/senzing-bootcamp-copilot-plugin`. This operation is strictly read-only: it never writes
any working tree. The repository is a known prerequisite and may not exist yet.

1. Verify that the public repository exists and identify an exact public revision. If it does not
   exist, stop and report **blocked**; do not guess another destination or create one.
2. Compare the public payload with the normalized generated plugin and identify every divergence.
3. Classify each item as local Copilot packaging or parent-owned curriculum/content/Senzing
   behavior, and explain the evidence.
4. Search the local tracker before filing. File deduplicated local issues here; route parent-owned
   items through `escalate-to-parent`.
5. Report all divergences, dispositions, issue links, and confirm that no working-tree file,
   index, ref, or public repository was changed.
