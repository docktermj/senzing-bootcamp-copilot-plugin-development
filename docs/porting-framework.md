# Claude-to-Copilot porting framework

This child transforms a tagged parent Claude plugin into a GitHub Copilot agent plugin. The
parent owns curriculum and `INV-NNN` identifiers. The child owns only Copilot packaging,
host mechanisms, and the compatibility decisions needed to preserve the bootcamper experience.

| Component | Canonical home | Gate |
| --- | --- | --- |
| A. Provenance | [`PARENT_VERSION`](../PARENT_VERSION), [`PARENT_COMMIT`](../PARENT_COMMIT), [`provenance-convention.md`](provenance-convention.md) | Exact SemVer tag and full resolved SHA; CI rejects non-tags. |
| B. Contract | [`contract.yaml`](../tools/bootcamp-transform/contract.yaml) | Every parent plugin file matches exactly one copy/ignore rule. |
| C. Inherited dispositions | `invariant_disposition_register` in the contract | Every parent invariant is honored, preserved/restated, or discounted with a conflict and resolution; a changed source release blocks until review. |
| D. Copilot invariants | [`INVARIANTS.md`](../specs/INVARIANTS.md) | Structural linter passes and every CPINV is evaluated on update. |
| E. Port checks | [`validate.py`](../tools/bootcamp-transform/validate.py) | Manifest, references, residual host terms, imports, and declared hook scripts validate. |
| F. Reconciliation | [`transform.py`](../tools/bootcamp-transform/transform.py) and `.build-manifest.json` | Pre-write report names additions, modifications, removals, preserved paths, and conflicts; conflicts stop the write. |
| G. Recorded host tests | [`test-checklist.md`](test-checklist.md) and `test-records/` | Required manual results are recorded for every release. |
| H. Determinism | [`.github/workflows/verify-build-determinism.yml`](../.github/workflows/verify-build-determinism.yml) | Rebuild at the pinned tag leaves no generated, provenance, or build-manifest drift. |
| I. Governance | [Maintainer skills](../.github/skills/) and `tools/bootcamp-transform/` | Canonical operations route issues to their owner and enforce write boundaries. |

The pre-write reconciler never resolves a conflict on behalf of a maintainer. A Copilot-specific
adaptation that cannot be expressed mechanically remains visible in the disposition register and
manual test record. Both invariant registers are release blockers.

The public mirror `Senzing/senzing-bootcamp-copilot-plugin` does not yet exist. Public propagation
is consequently blocked until the destination is created; no operation may substitute a guessed
repository or publish elsewhere.

The family rules live canonically in the parent’s
[FAMILY_WORKFLOW.md](https://github.com/docktermj/senzing-bootcamp-claude-plugin-development/blob/main/docs/FAMILY_WORKFLOW.md).
This index links to rather than duplicates them.
