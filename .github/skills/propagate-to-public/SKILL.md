---
name: propagate-to-public
description: Preview or apply a normalized plugin payload to the public Copilot repository's working tree only; never publish it.
---

# propagate-to-public

Propagate the tested plugin payload into the working tree of
`Senzing/senzing-bootcamp-copilot-plugin` for maintainer review. Do not commit, stage, branch,
push, open a pull request, tag, or release.

1. Verify that the public repository exists and is explicitly checked out as a separate working
   tree. If it does not exist, stop as **blocked** and report the missing prerequisite.
2. Preview mode is read-only and prints the complete normalized diff.
3. Apply mode requires an explicit existing review branch and a clean target worktree. Copy only
   the generated bootcamper plugin payload. Rewrite development self-references to the public
   repository slug; do not change curriculum content.
4. Show the post-apply diff and verify that the target index, refs, branch, and remote state did
   not change. Stop for human review and runtime testing.
5. The public repository owns its publication decision. This operation never commits or
   publishes, and must not treat a successful copy as a tested public release.
