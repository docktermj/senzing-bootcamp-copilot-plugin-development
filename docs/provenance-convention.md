# Parent provenance

`PARENT_VERSION` is the exact stable SemVer tag in the parent public plugin repository.
`PARENT_COMMIT` is the full commit SHA resolved from that tag. These two root files are the
single source of truth; the build manifest mirrors their values but does not replace them.

Never use a branch name, `HEAD`, a moving alias, or an untagged commit as the parent version.
The build clones the requested tag, verifies the plugin manifest version and resolved commit,
then compares that release with the manifest and disposition register. A newer parent tag is
not buildable until both invariant registers are reviewed and the pin is intentionally updated.

The provenance path and guard implement family rule R2. The invariant manifest is read from the
parent development repository at the same tag because it is generated and published there for
child disposition work.
