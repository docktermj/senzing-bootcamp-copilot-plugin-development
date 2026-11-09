# Senzing Bootcamp for GitHub Copilot — development

This child repository transforms a tagged release of the parent Senzing Bootcamp Claude plugin
into a GitHub Copilot agent plugin. The parent owns the curriculum and every `INV-NNN`; this
repository owns only the host adaptation. It does not fork the curriculum.

The generated installable plugin is in [`plugins/senzing-bootcamp/`](plugins/senzing-bootcamp/).
This repository also hosts its development marketplace; a separate public repository is not
required to install from this catalog.

## Install Senzing Bootcamp (preview)

Anyone with repository read access and a supported GitHub Copilot client can try the plugin,
subject to their organization/enterprise plugin policies. You need a signed-in Copilot account;
review the plugin's hooks and requested tool permissions before trusting them.

The stable marketplace name is `senzing-bootcamp-development`; the plugin identifier is
`senzing-bootcamp@senzing-bootcamp-development`. This is a development/preview distribution,
not a claim of Desktop runtime certification. The catalog and plugin must first be published
on this repository's default branch for the remote instructions below to work.
Existing [host evidence](docs/test-records/0.6.1.md) covers CLI only; installation success does
not prove that Desktop skills, MCP, hooks, write boundaries, or progress persistence work.

### GitHub Copilot Desktop app

1. Open **Customize** and select the marketplace settings control beside the marketplace dropdown.
2. Follow the prompts to add
   `https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development`.
3. Find **Senzing Bootcamp** in Customize and click **Install**.
4. Open **Installed** and confirm the plugin's toggle is on. Turn it off there to disable it.

These are GitHub's [documented Desktop controls](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app#adding-plugins),
not a record of a successful Desktop test. Desktop-specific update/removal controls have not
been verified here. Explicit update and uninstall commands are documented below for CLI;
do not assume they manage a separate Desktop configuration. Record the actual Desktop controls
and outcomes using the [host checklist](docs/test-checklist.md) before claiming support.

### GitHub Copilot CLI

```sh
copilot plugin marketplace add docktermj/senzing-bootcamp-copilot-plugin-development
copilot plugin marketplace browse senzing-bootcamp-development
copilot plugin install senzing-bootcamp@senzing-bootcamp-development
copilot plugin enable senzing-bootcamp@senzing-bootcamp-development
copilot plugin list
```

Start a new session after changing plugin activation. In a bootcamp project, invoke
`bootcamp-onboarding` by skill name. The installed package contains the bootcamper curriculum,
not this checkout's maintainer operations under `.github/skills/`.

To refresh the catalog and update the installed plugin:

```sh
copilot plugin marketplace update senzing-bootcamp-development
copilot plugin update senzing-bootcamp@senzing-bootcamp-development
```

To disable it temporarily, or uninstall it and then remove the catalog:

```sh
copilot plugin disable senzing-bootcamp@senzing-bootcamp-development
# Run these only when you want to remove the plugin and marketplace:
copilot plugin uninstall senzing-bootcamp@senzing-bootcamp-development
copilot plugin marketplace remove senzing-bootcamp-development
```

See the [CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference).
If registration or installation fails, check repository access, authentication, default-branch
catalog availability, and organization policy. Do not treat denied access or blocked plugins
as a successful installation or bypass managed policy.

## Rebuild and maintain

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
separate from the generated bootcamper plugin. Distribution through this development marketplace
does not change `propagate-to-public`, which copies only the plugin payload into a separately
checked-out public repository's working tree.

## Public-owned content

The public repository (`Senzing/senzing-bootcamp-copilot-plugin`) owns content this repository
does not mirror: the quick-start page `docs/index.html` and `docs/index.css`, the stub pages
`docs/README.md`, `best-practices.md`, `errors.md` and `examples.md`, and Senzing organization
boilerplate (workflows, `CODEOWNERS`, linters, community files, `.claude/`). The quick-start
page hard-codes the plugin version, marketplace and plugin names, install commands and client
verification status. The `propagate-to-public` preview runs
`tools/bootcamp-transform/public_page.py` to report where the page disagrees with the payload;
updating the page remains a public-repository decision.

## Marketplace validation scope

`tools/bootcamp-transform/validate.py` is the only marketplace validator here. It stays
dependency-free, matching the JSON-formatted `contract.yaml`, which exists so that the build needs
no YAML or third-party package. The public repository instead runs a schema-based validator
(`tools/validate_marketplace.py`, using `jsonschema` and `PyYAML`) with its own CI workflow. That
validator is not adopted here, since it expects the public catalog name `senzing-bootcamp` and
owner `Senzing`, while this catalog is `senzing-bootcamp-development`.

Both validators check the catalog name and owner, plugin names, repository-relative source paths,
and name and version agreement between the catalog and `plugin.json`. Three public checks are
accepted gaps here:

- Full JSON-Schema validation of `plugin.json` and `mcp.json`; `validate.py` checks only the
  `$schema` URL and the Senzing server definition.
- Skill `SKILL.md` frontmatter validation.
- Rejection of duplicate JSON keys.

The pinned-parent rebuild and the generated-file hashes in `.build-manifest.json` already catch
unexpected changes to generated output. Revisit this decision if a malformed hand-authored
manifest or skill reaches a release.
