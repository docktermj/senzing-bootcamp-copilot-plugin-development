# GitHub Copilot host test checklist

This checklist is a release gate, not a set of claims that static validation can prove. Record
results in `docs/test-records/<RELEASE_VERSION>.md` and include client, version, date, outcome,
and evidence for each critical behavior.

## Static checks

- [ ] `python3 tools/bootcamp-transform/transform.py --tag "$(cat PARENT_VERSION)"` passes.
- [ ] `python3 tools/bootcamp-transform/validate.py` passes.
- [ ] `python3 specs/check_invariants.py` passes.
- [ ] The parent and Copilot invariant registers were both evaluated.

## Host behavior (run in the Copilot client targeted for release)

| ID | Required | Host test |
| --- | --- | --- |
| TC-01 | Yes | Install the generated root `plugin.json` in the target Copilot client. |
| TC-02 | Yes | Confirm all parent curriculum skills are discoverable and invoked by skill name. |
| TC-03 | Yes | Confirm root `mcp.json` exposes Senzing and verify a live MCP call. |
| TC-04 | Yes | Confirm `sessionStart` resumes active bootcamp context without leaking into an unrelated project. |
| TC-05 | Yes | Confirm `userPromptSubmitted` captures feedback/notes only during an active bootcamp. |
| TC-06 | Yes | Confirm `preToolUse` allows an in-project write and denies an out-of-project or obvious-secret write. |
| TC-07 | Yes | Confirm `agentStop` allows a closing question and requests one continuation when it is missing. |
| TC-08 | Yes | Confirm `sessionEnd` performs its intended cleanup. |
| TC-09 | Yes | Observe compaction behavior; verify the checkpoint fallback and record that automatic `preCompact` is unavailable. |
| TC-10 | Yes | Walk one representative module end-to-end and verify one question per yielding turn against live Senzing MCP. |

## Release record requirements

A missing test record, an unrun host-critical check, or a failed check blocks release. An
unavailable check must be recorded as blocked/advisory with its reason; it must not be marked
passing. The release operation must not infer success from a test script or a static audit.
