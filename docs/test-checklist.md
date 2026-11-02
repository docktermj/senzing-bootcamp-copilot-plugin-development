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

Run the checks separately for each targeted client, including Desktop. CLI results do not
certify Desktop behavior. Record the exact tested repository revision as well as the plugin
version, and preserve earlier CLI evidence when adding Desktop results. The release-record
validator expects one canonical `TC-NN` row per check for the release's tested client; qualify
additional clients' row IDs (for example, `Desktop TC-02`) and use separate client sections.

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
| TC-09 | Yes | If a `preCompact` handler is configured, exercise it; otherwise record that automatic handling is not wired and verify the checkpoint fallback. |
| TC-10 | Yes | Walk one representative module end-to-end and verify one question per yielding turn against live Senzing MCP. |

## Marketplace distribution checks

These additional checks distinguish catalog discovery/installation from runtime compatibility.
Use a clean client configuration and the remote repository, not a local marketplace path or
`--plugin-dir`. Obtain approval before changing personal client configuration. Publication
requires separate explicit maintainer approval; do not push or merge merely to run these checks.

| ID | Check and required evidence |
| --- | --- |
| MP-01 | After the catalog and payload are published on the default branch, add `docktermj/senzing-bootcamp-copilot-plugin-development` remotely; browse and install `senzing-bootcamp@senzing-bootcamp-development`. Record client/version, date, revision, exact commands, and outcomes. |
| MP-02 | In Desktop Customize, add the repository through marketplace settings, find/install Senzing Bootcamp, then confirm it is enabled under Installed. Record the actual UI controls and evidence separately from CLI. |
| MP-03 | Run TC-02 through TC-10 in Desktop, including a live Senzing MCP call, project-scoped resume, notes capture, write/secret boundaries using synthetic data, cleanup, progress persistence, and one representative module. Record each outcome rather than inferring it from installation. |
| MP-04 | Exercise enable/disable, update, and removal in each targeted client. Record the actual controls/commands, resulting version/activation, and any unsupported Desktop management operations; do not assume CLI configuration is shared. |

Put results in `docs/test-records/<RELEASE_VERSION>.md` with clearly separated client sections.
Record authentication/access failures, policy restrictions, unsupported features, and unrun
checks as failed, blocked, or advisory with reasons, never passing. Required runtime checks
that are unsupported or unrun block Desktop certification; successful installation alone may
be described only as preview installation evidence. Keep issue #8 open until its remote and
Desktop requirements are satisfied. If fixes are needed, report them for separately approved
follow-up; do not weaken the existing release gate.

## Release record requirements

A missing test record, an unrun host-critical check, or a failed check blocks release. An
unavailable check must be recorded as blocked/advisory with its reason; it must not be marked
passing. The release operation must not infer success from a test script or a static audit.
