# Senzing Bootcamp for GitHub Copilot — development

This child repository transforms a tagged release of the parent Senzing Bootcamp Claude plugin
into a GitHub Copilot agent plugin. The parent owns the curriculum and every `INV-NNN`; this
repository owns only the host adaptation. It does not fork the curriculum.

The generated installable plugin is in [`plugins/senzing-bootcamp/`](plugins/senzing-bootcamp/).
The pinned parent release is recorded once in [`PARENT_VERSION`](PARENT_VERSION) and
[`PARENT_COMMIT`](PARENT_COMMIT). Rebuild it with:

```sh
python3 tools/bootcamp-transform/transform.py --tag "$(cat PARENT_VERSION)"
python3 tools/bootcamp-transform/validate.py
```

The transform requires an exact stable SemVer tag, exhaustively classifies every parent plugin
file, and prints a three-way reconciliation report before writing. It stops rather than overwriting
a conflicting local change. CI also rebuilds the pinned tag and rejects generated drift.

See [`docs/porting-framework.md`](docs/porting-framework.md) for the component map,
[`docs/copilot-host-mechanisms.md`](docs/copilot-host-mechanisms.md) for verified host behavior,
and the parent’s [family workflow](https://github.com/docktermj/senzing-bootcamp-claude-plugin-development/blob/main/docs/FAMILY_WORKFLOW.md)
for the normative cross-repository rules.

Maintainer operations are GitHub Copilot skills under `.github/skills/`. They are deliberately
separate from the generated bootcamper plugin. The public Copilot plugin repository does not yet
exist; `propagate-to-public` remains blocked until that prerequisite is created.
