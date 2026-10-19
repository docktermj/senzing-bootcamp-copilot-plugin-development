---
name: release
description: Create a tested local release by atomically updating version metadata, changelog, commit, and tag in this repository only.
---

# release

Create a release in this development repository only. Never write to the parent or public mirror.

1. Require a clean working tree, a stable SemVer target, and the complete passing host test
   record for the release. A missing, blocked, incomplete, or failing record blocks release.
2. Preview the exact changes with:

   ```sh
   python3 tools/bootcamp-transform/release.py --branch <review-branch> \
     --version <new-version> --notes "<release notes>"
   ```

3. Review the diff and obtain explicit approval before applying. The helper runs transform,
   mechanical checks, invariant linters, tests, and release-record validation before creating
   version metadata.
4. Apply with the same arguments plus `--apply`. The helper updates the generated plugin
   manifest, `RELEASE_VERSION`, changelog, and build manifest and atomically updates the local
   branch and annotated tag. If interrupted, use `--recover` with the same branch.
5. Touch only this repository. Do not push, open a PR, publish, or create a release elsewhere.

The operation must stop and report an error rather than leave a partial release.
