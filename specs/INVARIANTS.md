# GitHub Copilot child invariants

The parent owns the curriculum and all `INV-NNN` identifiers. This register contains only
Copilot-native guarantees that have no upstream invariant. It must not restate an upstream
`INV-NNN` or an entry in the disposition register in
[`contract.yaml`](../tools/bootcamp-transform/contract.yaml). The contract owns inherited
invariant dispositions; this file owns host packaging, execution, and release guarantees.

## Maintenance rules

- Never delete, reuse, or renumber a `CPINV-NNN` identifier.
- State each invariant as one testable MUST or ALWAYS condition.
- Add every new identifier to exactly one subject in the index in the same change.
- Keep [`check_invariants.py`](check_invariants.py) passing.
- Supersession is established only by the two exact bullets below, with zero-padded IDs:
  - **Superseded by:** CPINV-014 — the guarantee moved into the interaction contract
  - **Supersedes:** CPINV-006
- `Superseded by:` means status `superseded`; its absence means `active`. There is no third state.
- Never use prose, a status word, or strikethrough as a supersession marker.
- On every parent update, evaluate both the parent's applicable `INV-NNN` entries and every
  active `CPINV-NNN`; a failure in either register blocks release.

## Invariants

- **CPINV-001** — The generated plugin MUST contain a valid root Agent Plugins manifest whose
  name and version match this repository's release metadata.
- **CPINV-002** — Every generated Copilot hook command MUST resolve its bundled script through
  `${PLUGIN_ROOT}` and the referenced script MUST exist.
- **CPINV-003** — Every maintainer operation MUST be exposed as a Copilot skill under its
  canonical family name.
- **CPINV-004** — A parent guarantee without an equivalent documented Copilot mechanism MUST
  be recorded as an advisory degradation and MUST NOT be reported as host-enforced.
- **CPINV-005** — Every parent update MUST evaluate both the parent disposition register and
  this Copilot-native register before generated output is written.
- **CPINV-006** — A release MUST be blocked when its required per-release host test record is
  missing, incomplete, or non-passing.
- **CPINV-007** — The transform MUST classify every file in the pinned parent plugin exactly
  once and MUST fail before writing when any file is unmatched or multiply matched.
- **CPINV-008** — A deterministic rebuild MUST leave generated files, provenance, and the build
  manifest byte-for-byte unchanged.
- **CPINV-009** — The public propagation operation MUST stop before writing when the public
  Copilot plugin repository does not exist.
- **CPINV-010** — The feedback ledger MUST identify entries by content hash and MUST NOT mark a
  duplicate entry as newly processed.

## Index by subject

| Subject | Invariants |
| --- | --- |
| Packaging and manifests | CPINV-001 |
| Hooks and host execution | CPINV-002, CPINV-004 |
| Maintainer operation surface | CPINV-003 |
| Update and release gates | CPINV-005, CPINV-006, CPINV-008, CPINV-010 |
| Transform coverage | CPINV-007 |
| Public propagation boundary | CPINV-009 |
