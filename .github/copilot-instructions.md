# Copilot instructions

## Repository model

This repository is a deterministic **GitHub Copilot host adaptation** of the
Senzing Bootcamp parent plugin. The parent owns the curriculum and all
`INV-NNN` identifiers; this repository owns Copilot packaging, hooks, host
compatibility decisions, and `CPINV-NNN` invariants.

- `tools/bootcamp-transform/transform.py` rebuilds
  `plugins/senzing-bootcamp/` from the exact parent tag in `PARENT_VERSION`.
  It verifies the resolved `PARENT_COMMIT`, classifies every upstream file
  through `contract.yaml`, applies substitutions, generates Copilot-specific
  artifacts, and records hashes in `.build-manifest.json`.
- `tools/bootcamp-transform/contract.yaml` is JSON-formatted YAML so the build
  has no YAML dependency. It defines upstream copy/ignore rules, inherited
  invariant dispositions, substitutions, and generated Copilot artifacts.
- `tools/bootcamp-transform/validate.py` is the static release gate. It checks
  manifests, MCP configuration, hook commands, host-term substitutions,
  generated-file hashes, maintainer-operation boundaries, and invariants.
- `.github/skills/` contains maintainer operations, separate from the generated
  bootcamper skills in `plugins/senzing-bootcamp/skills/`. The operation set and
  its cross-repository write boundaries are enforced by `operations.json` and
  `check_operations.py`.

## Generated output and provenance

- Treat `plugins/senzing-bootcamp/` and `.build-manifest.json` as generated
  output. Do not hand-edit them; change the transform contract, an explicitly
  sourced Copilot artifact, or the pinned parent release, then rebuild.
- Rebuild only from the exact stable SemVer tag in `PARENT_VERSION`; it must
  resolve to the full lowercase SHA in `PARENT_COMMIT`. Never use a branch,
  `HEAD`, or an untagged commit.
- The transform reports reconciliation conflicts before writing. Resolve the
  conflict deliberately rather than overwriting local changes.
- For parent updates, review the contract's inherited invariant disposition
  register and `specs/INVARIANTS.md`. Add new `CPINV-NNN` entries sequentially,
  phrase each as one testable `MUST` or `ALWAYS`, and add it exactly once to the
  subject index.

## Commands

Use Python 3.12, matching CI.

```sh
# Rebuild the checked-in plugin from its pinned parent release
python3 tools/bootcamp-transform/transform.py --tag "$(cat PARENT_VERSION)"

# Static validation and invariant-register validation
python3 tools/bootcamp-transform/validate.py
python3 specs/check_invariants.py

# Focused operation-boundary validation
python3 tools/bootcamp-transform/check_operations.py

# Full Python unit suite
python3 -m unittest discover -s tools/bootcamp-transform/tests -v

# One test module, class, or test method
python3 -m unittest tools/bootcamp-transform/tests/test_transform.py -v
python3 -m unittest tools.bootcamp-transform.tests.test_transform.TransformTests.test_added_path_collision_is_a_conflict -v
```

There is no separate lint command. `validate.py` and
`specs/check_invariants.py` provide the repository's static checks. CI rebuilds,
validates, runs the full unit suite, then rejects drift in generated output and
version metadata.

## Release-specific behavior

`docs/test-records/<RELEASE_VERSION>.md` is a required release gate, not an
optional record. It must document passing live-Copilot host checks, including a
live Senzing MCP call; static checks cannot replace it. Use the `release` skill
for releases so version metadata, the changelog, generated output, the local
commit, and tag are updated atomically. Maintainer operations must not publish
to remotes; only `escalate-to-parent` may create external issues, and only
`propagate-to-public` may write the public plugin worktree.

## Senzing MCP

The generated plugin's root `mcp.json` declares the `senzing` HTTP server at
`https://mcp.senzing.com/mcp`. Preserve that root configuration when changing
the transform contract or regenerating the plugin. Use the live Senzing MCP
server to verify Senzing-specific claims and release behavior; do not treat the
presence of `mcp.json` or a static check as evidence that a client can connect
and make a call.
