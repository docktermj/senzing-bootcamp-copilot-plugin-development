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
2. Preview mode is read-only and prints the complete normalized diff, plus a diff of
   `site/index.html` and `site/index.css` against the public `docs/index.html` and
   `docs/index.css`. It also runs `python3 tools/bootcamp-transform/public_page.py --public
   <checkout>` and includes its table: the public page's version, plugin identifier and install
   commands against the payload, plus its client-status text beside the test record's status for
   human review. A mismatch is reported to the maintainer and never blocks propagation. The
   preview also diffs `.vscode/cspell.json` and `.vscode/cspell-bootcamp.txt` against the public
   copies.
3. Apply mode requires an explicit existing review branch and a clean target worktree. Copy the
   generated bootcamper plugin payload and, as the only other files, `site/index.html` and
   `site/index.css` to the public `docs/index.html` and `docs/index.css`, and
   `.vscode/cspell.json` and `.vscode/cspell-bootcamp.txt` to the public `.vscode/`. Rewrite
   development self-references in the payload to the public repository slug; do not change
   curriculum content. Never copy `.vscode/cspell.dev.json` (local only) and never touch other
   public files.
4. Show the post-apply diff and verify that the target index, refs, branch, and remote state did
   not change. Stop for human review and runtime testing.
5. The public repository owns its publication decision. This operation never commits or
   publishes, and must not treat a successful copy as a tested public release.
