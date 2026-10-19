---
name: implement-github-issue
description: Implement one explicitly selected local GitHub issue on its own branch through plan and pre-push approval gates.
---

# implement-github-issue

Implement a selected issue from this repository's tracker through an open pull request. **Never
merge, commit to `main`, force-push, or select work autonomously.**

1. If invoked without an issue number, ask which issue and stop. Do not recommend or choose one.
2. Confirm it is an open local issue, search for duplicates, and check dependencies. If invalid,
   duplicate, or already fixed, stop and report evidence without manufacturing a change.
3. For Senzing facts, use the live Senzing MCP server before editing. An absence claim must name
   the route that owns the fact; otherwise it is a blocker.
4. Present a concrete plan, paths, behavior, and tests. Wait for explicit approval. Silence is
   not approval.
5. Work on a new issue branch, make the smallest complete change, run targeted tests and relevant
   release checks, and review the diff.
6. Present the final diff, test results, and exact push/PR plan. Wait for a second explicit
   approval before pushing or opening the PR. Silence is not approval.
7. Push only the issue branch and open a pull request. Stop before merge.
8. When closing a parity issue, advance `PARENT_VERSION` and `PARENT_COMMIT` to the tagged parent
   release containing the fix, update both invariant evaluations, rebuild, and record evidence.
   A parent issue closing without a released tag does not satisfy parity.

The operation ends with an open PR or an evidence-backed no-change outcome.
