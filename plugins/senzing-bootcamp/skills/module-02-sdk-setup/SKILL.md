---
name: module-02-sdk-setup
description: 'Bootcamp Module 2: SDK setup (installing and configuring the Senzing SDK). Use when the bootcamper starts or resumes Module 2, or needs to install/configure the Senzing SDK, set up the database, or run the verification test.'
---

# Module 2: SDK setup

The Bootcamper-facing name of this module is **SDK setup** — the spelling in
`../bootcamp-preparation/SKILL.md`'s module table. Use it in the module-start banner, the
journey map, and every transition question (INV-079); "installing and configuring the SDK"
describes what the module does but is not its name.

> **MCP grounding (mandatory — applies to this entire skill).** Every Senzing fact you present —
> SDK method and attribute names, config options, error codes, and entity-resolution specifics —
> MUST come from the Senzing MCP tools, never from training data, memory, or speculation.
> **Pre-response checklist:** if a reply contains any Senzing specific, you MUST have called an MCP
> tool this turn to obtain it; if not, stop and call it first. This has the same precedence as a ⛔
> gate. The full rule and tool routing are the "MCP-first invariant" in
> `../bootcamp-onboarding/ground-rules.md`.

Follow `../bootcamp-onboarding/ground-rules.md` throughout (👉 one-question-at-a-time,
MCP-first, file placement, checkpointing). Execute every numbered step one at a time, in
order. Never skip, combine, or abbreviate a step containing a 👉 question, and never skip a
mandatory gate. This has absolute precedence: no internal reasoning or token-budget concern
overrides it.

**First:** Read `config/bootcamp_progress.json`, then (per ground-rules) show the module start
banner, journey map, before/after framing, a brief numbered overview of this module's steps, an estimated time-to-complete (INV-096), and the recommended model/effort nudge (INV-063), before any module work. Resume at
`current_step` if progress already exists.

Install and configure the Senzing SDK natively on the bootcamper's machine. This is the first
setup step of the bootcamp: once the SDK is installed, all subsequent modules use it directly.

**Before/After:** You have a project directory but no Senzing SDK. After this module, the SDK
is installed, configured, and verified, ready to load data and resolve entities.

**Prerequisites:** None (this is the first setup module).

**Language:** Use the bootcamper's chosen programming language from the language selection step
in onboarding. All code generation, scaffold calls, and examples in this module must use that
language.

**Success indicator:** ✅ SDK installed + DB configured + test passes + an engine-class call
(`SzEngine`/`SzDiagnostic`) succeeds — a version query alone does not qualify (Step 9).

> **User reference:** A detailed background document for this module (`MODULE_2_SDK_SETUP.md`)
> is a later porting phase. For now, teach the steps directly from this skill.

## Error Handling

When the bootcamper hits an error during this module:

1. **SENZ error code** (message contains `SENZ` + digits, e.g. `SENZ2027`): call
   `explain_error_code(error_code="<code>", version="current")` and present the explanation and
   recommended fix. If it returns nothing, continue to step 2.
2. Present the matching pitfall/fix for this module (full `common-pitfalls` reference is a
   later porting phase; for now, use `search_docs` to look up the symptom).
3. If no match, use `search_docs` against the Troubleshooting-by-Symptom guidance and general
   pitfalls.

> The TypeScript from-source build has its own recovery branch (see Step 3). A mid-build
> compile failure is handled there, not by this generic SENZ-code path.

## Step 1: Check for Existing Installation (MUST DO FIRST)

Before doing anything else in this module, check if the Senzing SDK is already installed and
working. There is no reason to re-install it.

Run a language-appropriate import/version check for the bootcamper's chosen language. Use
`sdk_guide(topic='install', platform='<user_platform>', language='<chosen_language>', version='current')`
to get the correct verification command.

**Filesystem fallback (if the import check fails):** The import check fails for reasons that have
nothing to do with the SDK being absent — `PYTHONPATH` unset on Linux, `DYLD_LIBRARY_PATH` not
exported before the JVM starts on macOS, `CLASSPATH` unset on Windows — so before concluding
anything, check for the **platform's native library**. That is the artifact which must exist for the
SDK to work, and it is what `sdk_guide` names for each platform (**INV-001**: all three are
supported, so all three are listed):

| Platform | Native library — verify this exists |
|---|---|
| `linux_apt`, `linux_yum` | `/opt/senzing/er/lib/libSz.so` |
| `macos_arm` | `$(brew --prefix)/opt/senzing/er/lib/libSz.dylib` (never a hardcoded `/opt/homebrew`) |
| `windows` | `%SENZING_DIR%\lib\Sz.dll` — `SENZING_DIR` already points at the `er` subdirectory |
| `docker` | Not applicable — there is no host install to probe; the image tag is the version |

(Each path as `sdk_guide(topic='install', platform=…)` gives it under `post_install`/`env_vars`,
verified on MCP server 1.32.9, docs indexed 2026-08-11 20:52 UTC, 2026-08-13.)

If the library is present, report the SDK as installed and skip the **installation** — Step 2, and
Step 3's install commands (its Phase 1 EULA question and its Phase 2 SDK package).
⛔ **(INV-339) Not Step 3 entirely: its Phase 3 and its environment-script work still run**, and the
environment script is the single most likely thing an existing install is missing — see
"Required stops" in the V4.0+ branch below. Then proceed to Step 4 verification.

⛔ **Only conclude "not installed" for a platform whose library you actually checked.** If the
platform is undetermined, or the check could not run, the result is **unknown** — say so and name
why (INV-163), then treat it as unknown rather than reporting an absent SDK. Concluding "not
installed" from a path that cannot exist on this platform is how a Bootcamper with a working install
gets sent to reinstall it, which is exactly what this step opens by forbidding.

**Reading the version once the library is found:** use the primary route — the language version
check, or `SzProduct.get_version()`, whose response fields Step 4 states. Failing that, build
metadata sits in `szBuildVersion.json` — see "Comparing the two versions" in Step 1b.

⛔ **(INV-285) Its provenance differs by platform, so it is stated per platform.** One caveat spanning all
three is what let the Windows half go stale while reading as reviewed.

- **Windows — MCP-sourced.** Under the **sibling** `data` directory, not under `%SENZING_DIR%`:
  Scoop sets `SENZING_DIR=<scoop-app-dir>\er` and the support data installs to
  `<scoop-app-dir>\data`. Stated by the server itself, in the `gotchas[]` of
  `sdk_guide(topic='install', platform='windows')`, which names `szBuildVersion.json` among that
  support data (server **1.35.3**, 2026-09-01; the server cites the MSI Directory table for
  4.3.3.26191).
- **Linux — environment observation, not MCP-sourced (INV-149).** `/opt/senzing/er/` and also
  `/opt/senzing/data/`. Observed on a real install, both files present and identical, reporting
  `BUILD_VERSION 4.4.0.26242` (2026-09-01). No MCP route states it:
  `sdk_guide(topic='install', platform='linux_apt')` gives `default_paths` and a
  `ls /opt/senzing/er/lib/libSz.so` verification step and never mentions the file.
- **macOS — unknown, and the route was asked.** `sdk_guide(topic='install', platform='macos_arm')`
  names the support data under `$(brew --prefix)/opt/senzing/data` as `address_datamodel`,
  `nomicon` and the `*TransRules.sz` modules, and stops there — no `szBuildVersion.json` anywhere
  (server **1.35.3**, 2026-09-01). Do not guess it by analogy with Linux.

If the file is not where expected, read the version through the SDK rather than concluding the SDK
is missing.
<!-- MCP-NEGATIVE: search_docs(query='szBuildVersion.json build version file location') — no indexed document gives that file's path on any platform; the corpus serves SDK version-READING material for it (the get_version() examples) and build/packaging documents, none stating where the file lives — owner: search_docs IS the corpus route for a documented file location, and the version fact the corpus does serve is the SDK's get_version() rather than a file, so the SDK route is where the reader must go (routing negative; NOTE the Windows path IS served, by sdk_guide(topic='install', platform='windows') in its gotchas[] — this claim is scoped to search_docs and to Linux/macOS) — server 1.37.13, 2026-09-26 -->

**If the SDK is found and version is V4.0+:**

Tell the user: "Senzing SDK is already installed (version [X]). No need to reinstall: I'll skip the
installation, then set up this project's environment script (and your language's bindings, if it
needs them) before verifying it."

Then run **Step 1b** below to see whether a newer release is available, and offer it. A working
install is never replaced without the bootcamper saying so.

This is the **existing-install path** (INV-339). It is the same whether Step 1b finds no newer version, the
bootcamper declines the update, or they decline the EULA for it, and an accepted update rejoins it
(Step 1b, "After updating"):

- **Skip the *installation* — Step 2, and Step 3's install commands: Step 3's Phase 1 (EULA
  acceptance) and Phase 2 (the SDK package).** Not Step 3 entirely: see the required stops below.
  What is redundant on an existing install is fetching and installing the SDK; nothing else in
  Step 3 is.
- **(INV-338) Do not re-ask the EULA.** Phase 1 gates installing the SDK, and this path installs no SDK.
  Only an update the bootcamper accepts in Step 1b asks it, because an update is an install.
- **(INV-339) Still run Step 3's Phase 3** (install language bindings). The Java, C#, Rust and TypeScript
  bindings are per-project, so an existing SDK install does not provide them. For Python,
  Phase 3 installs nothing: the bindings ship inside the SDK runtime and are made importable by
  the environment script.
- **(INV-339) Still do Step 3's environment-script work** ("Create the project-local environment script"), then
  jump to Step 4 (verify installation) to confirm it works with the chosen language.
- If Step 4 passes, proceed to Step 5 (License), which confirms the built-in evaluation license
  without prompting (the License Key gate is in Module 4, per INV-093). After Step 5, proceed to
  Step 6 (create the project directory structure), then Step 7 (database).
- Mark Module 2 as complete once verification passes.

> **Required stops (INV-339):** These steps are NEVER skipped, even when the SDK is already installed:
>
> - **Step 3's environment script** (`src/scripts/senzing-env.sh`, or `src\scripts\senzing-env.ps1` on
>   Windows, dot-sourced; its Windows form is unverified on Windows PowerShell 5.1 here, INV-163):
>   ⛔ **the single most likely thing an existing install is missing.** Step 3 is titled "Install
>   Senzing SDK" and does **two** jobs — it installs the SDK *and* it writes the project-local script
>   that exports the library and Python paths. Only the first is redundant here. Skipping both leaves
>   the bootcamper with a healthy install and no environment, and every later module then fails at
>   import with `libSz.so: cannot open shared object file` — which reads as a broken install, in a
>   *later* module, far from this decision. Step 1's own fallback predicts exactly this state (it
>   exists because the import check can fail with `PYTHONPATH` unset on a working install), so
>   routing past the step that fixes it is the specific trap.
>   **Take the variable values from `sdk_guide(topic='install', platform=…, language=…)`** —
>   `install.platform.env_vars` carries them — rather than from an install transcript, because no
>   install ran (INV-080). Write the script with the **same** implementation the install path uses:
>   the zsh/bash path-resolution idiom, the fail-loudly root check, and the empty-value guard (see
>   "The env script MUST resolve its own path…" in Step 3). One implementation, not two.
> - **Step 3's Phase 3** (install language bindings): the Java, C#, Rust and TypeScript bindings
>   belong to the project, not to the SDK install. Python has nothing to install here.
> - **Step 4** (Verify Installation): confirms the SDK works with the chosen language.
> - **Step 5** (License): a brief, no-prompt confirmation that the built-in evaluation license is
>   active (the volume-gated License Key gate itself lives in Module 4, per INV-093).

**If the SDK is found but version is incompatible (<V4.0):**

Tell the user: "Senzing SDK found but it's version [X]. The bootcamp requires V4.0+. We'll need
to upgrade." Proceed with Steps 2-3 for the upgrade.

**If the SDK is NOT found:**

Tell the user: "Senzing SDK is not installed yet. Let's set it up, this is a one-time process."
Proceed with Step 2.

**Checkpoint:** write step 1 to `config/bootcamp_progress.json`.

## Step 1b: Offer an update when a newer release exists (V4.0+ installs only)

Step 1 compares the installed version against the **V4.0 floor**. That answers "is it new enough
to work", not "is it the newest available" — two different questions. Ask the second one too,
then **offer**. Never update silently, and never treat declining as a problem.

⛔ **Non-blocking, start to finish (INV-048).** A check that cannot run, a repository that is
unreachable, or an update that fails must warn and continue with the working install. This step
improves a working state; it is never a prerequisite for Module 2.

### The three platform families need three different mechanisms

⛔ **The package manager that installed Senzing is the authority on what is available** — not the
MCP server. `get_capabilities` reports `senzing_version` as the string `"current"`, not a number
(server 1.32.2, verified 2026-07-31), so it cannot answer this.

⛔ **Two kinds of command follow, and they have different owners. Do not treat them alike.**

- **Server-documented (on loan — re-read it, do not trust the copy below).** Two routes carry
  these. The *install* command comes from
  `sdk_guide(topic='install', platform='<platform>', language='<language>')`. The macOS and
  Windows *update* command comes from `search_docs`, which serves the official Homebrew tap and
  Scoop bucket READMEs (the two queries are under "The update command" below). Each live response
  is authoritative; the forms below are a dated illustration (install: server 1.32.2, verified
  2026-07-31; update: server 1.37.14, docs index 2026-09-28 03:23 UTC, verified 2026-09-28) so
  you can see the shape without a round trip. If a response differs, **the response wins.** If
  `search_docs` is unreachable, use the update form below as last verified on that date and say
  that it could not be re-checked (INV-163).
- **Plugin-owned (there is nothing to re-ask).** The **installed-version query** and the
  **available-version check** are ordinary package-manager commands. `sdk_guide` returns *install*
  commands and *presence* checks (`ls libSz.so`, `Test-Path Sz.dll`) — it documents **no version
  query and no update check on any of the four platforms** (verified 2026-07-31). So if you look
  for these in its response and do not find them, that is expected, not an error: use the ones
  below as given.

  ⚠️ **The plugin-owned commands are exercised on Linux only.** This plugin's own test suite runs
  on Linux, so the `brew` and `scoop` forms below are standard package-manager usage that no test
  here has ever executed. Treat their *output* as the thing to check, not their success: read what
  the command actually printed rather than assuming the version it reported, and on macOS obey the
  zero-exit-code warning further down without exception. This is the same discipline INV-163
  requires — say what you could not verify — applied to a command rather than a check.

**The update command.** ⚠️ **On macOS and Windows the update command is server-documented through
`search_docs`, not through `sdk_guide`.** `sdk_guide(topic='install')` gives the install command;
the update command is in the official tap and bucket READMEs, which `search_docs` serves (server
1.37.14, docs index 2026-09-28 03:23 UTC, 2026-09-28):

- **macOS:** `search_docs(query='homebrew-senzingsdk upgrade cask brew upgrade senzingsdk')`
  returns `senzing/homebrew-senzingsdk`, section "Upgrade": `brew update`, then
  `brew upgrade --cask senzingsdk`. ⚠️ A V3→V4 migration FAQ ranks above it; read down to the
  README section rather than concluding from the first result.
- **Windows:** `search_docs(query='scoop-senzingsdk update scoop update senzingsdk')` returns
  `senzing/scoop-senzingsdk`, section "Update": `scoop update senzingsdk`.

Only on apt and yum is the update command the same server-documented `install` command from
`sdk_guide`. The coverage gap reported upstream on 2026-08-13 — the server documented installing,
not updating — is **partly closed**: the update commands are now served, while the
installed-version query, the available-version check and version-exact pins for casks and Scoop
are still absent.
<!-- Date corrected from 2026-07-31 on 2026-08-13: the earlier claim was unsubstantiated. A
     feature request WAS sent on 2026-07-31, but for the stdio-mode / private-deployment route — a
     different subject — and the two had been conflated, so 2026-08-13 is this gap's first report
     rather than a duplicate. Full evidence chain in the maintainer's development record. -->
<!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='macos_arm') and the same call with platform='windows' — install_commands, gotchas and post_install carry no brew upgrade --cask and no scoop update — owner: search_docs IS the route that carries the update command for each package manager: search_docs(query='homebrew-senzingsdk upgrade cask brew upgrade senzingsdk') returns the tap README's Upgrade section and search_docs(query='scoop-senzingsdk update scoop update senzingsdk') returns the bucket README's Update section, so the reader must go there rather than conclude the command is undocumented (routing negative) — server 1.37.14, 2026-09-28 -->

**Linux, apt (`linux_apt`):**

<!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='linux_apt') — install_commands, gotchas and post_install carry no dpkg-query and no apt-cache policy; it verifies with ls /opt/senzing/er/lib/libSz.so, an existence probe — owner: sdk_guide(topic='install', platform='linux_apt') IS the route that would carry an installed-version query for apt, and it documents installing and existence-verification only (absence negative) — server 1.36.0, 2026-09-02 -->

```bash
# plugin-owned — sdk_guide documents neither of these
dpkg-query -W -f='${Version}\n' senzingsdk-runtime   # installed, e.g. 4.3.3-26191
apt-cache policy senzingsdk-runtime                  # Candidate: is what the repo offers
# server-documented — re-read from sdk_guide; this form is a dated illustration
sudo apt install -y senzingsdk-runtime senzingsdk-setup   # takes the newest available
```

**Linux, yum/dnf (`linux_yum`):** *plugin-owned* —
`rpm -q --qf '%{VERSION}-%{RELEASE}\n' senzingsdk-runtime` for installed, and
`yum check-update senzingsdk-runtime` for available (**`dnf` on RHEL 8+/Fedora**).
*Server-documented* — `sudo yum install -y senzingsdk-runtime senzingsdk-setup` to update
(re-read it from `sdk_guide`; the form here is a dated illustration).

> ⚠️ **Do not use `direct_download` on yum.** `sdk_guide(platform='linux_yum')` returns a
> `direct_download` block, but its packages are **`.deb` files with `sudo apt install` commands**
> (verified 2026-07-31, server 1.32.2). They are wrong for an rpm system. `direct_download` is the
> apt/firewalled route only.

**macOS, Homebrew cask (`macos_arm`):**

<!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='macos_arm') and search_docs(query='brew outdated brew info senzingsdk installed version check') — neither carries brew outdated or brew info for the cask; the corpus serves the tap README's install, upgrade and uninstall usage for it and no version-check command — owner: sdk_guide(topic='install', platform='macos_arm') IS the route for the cask's commands and search_docs IS the corpus route for the tap README, so the routes that would carry a version check were asked and carry none (absence negative) — server 1.37.14, 2026-09-28 -->

```bash
# plugin-owned — the server documents no brew version check:
# neither outdated nor info (sdk_guide and search_docs, checked 2026-09-28)
brew outdated --cask senzingsdk    # nothing printed = up to date
brew info --cask senzingsdk        # installed and latest versions
# server-documented — re-read from search_docs; this form is a dated illustration
brew update
brew upgrade --cask senzingsdk     # takes the newest available
```

⛔ **A ZERO EXIT CODE FROM `brew` DOES NOT MEAN IT INSTALLED** (INV-218). If the EULA variable's name or
value is wrong the cask prints "No interactive terminal detected", purges the download, then
**still prints its Caveats block listing install paths** — so it reads as success while installing
nothing. After any macOS update, probe the artifact:

```bash
test -f "$(brew --prefix)/opt/senzing/er/lib/libSz.dylib" && ls "$(brew --prefix)/opt/senzing/data"/*TransRules.sz
```

Also on macOS: the tap must be trusted on Homebrew 6+ (`brew trust senzing/senzingsdk`), and
**`SENZING_ROOT` can move between versions** — re-export the env vars from
`sdk_guide(topic='install', platform='macos_arm')` after updating rather than assuming the old
paths still resolve.

**Windows, Scoop (`windows`):**

<!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='windows') and search_docs(query='scoop status scoop info senzingsdk installed version check') — neither carries scoop status or scoop info; the corpus serves the bucket README's install, update and uninstall usage for it and no version-check command — owner: sdk_guide(topic='install', platform='windows') IS the route for the bucket's commands and search_docs IS the corpus route for the bucket README, so the routes that would carry a version check were asked and carry none (absence negative) — server 1.37.14, 2026-09-28 -->

```powershell
# plugin-owned — the server documents no scoop version check:
# neither status nor info (sdk_guide and search_docs, checked 2026-09-28)
scoop status                          # lists packages with updates available
scoop info senzingsdk/senzingsdk      # installed and latest versions
# server-documented — re-read from search_docs; this form is a dated illustration
scoop update senzingsdk               # takes the newest available
# server-documented — the presence probe sdk_guide gives under post_install
Test-Path "$env:SENZING_DIR\lib\Sz.dll"   # verify it actually installed
```

**Docker (`docker`):** there is nothing to update in place — the **image tag is the version**.
Offer to pull a newer tag and recreate the container instead, and do not run a package-manager
update inside it.

### Comparing the two versions

⚠️ **`szBuildVersion.json` and the package version differ by one character.** Step 1's filesystem
fallback reads `BUILD_VERSION` from that file, which uses a **dot** where every package manager
uses a **hyphen**:

| Source | Value |
|---|---|
| `dpkg-query` / `rpm -q` / `direct_download` filename | `4.3.3-26191` |
| `szBuildVersion.json` → `BUILD_VERSION` | `4.3.3.26191` |

Comparing those two raw strings reports a difference where none exists. (Observed on a real
4.3.3-26191 install, 2026-07-31 — an environment observation, not an MCP-sourced fact.) On Windows
that file is in the **sibling** `data` directory, not under `%SENZING_DIR%`.

⛔ **(INV-290) The two sources disagree for two different reasons, and only one of them is cosmetic —
normalize the separator FIRST, then read what is left.**

- **Same version, different separator** (`4.3.3-26191` vs `4.3.3.26191`) — a formatting artifact.
  Normalize and treat them as equal; the package manager's string is the one to report.
- **Genuinely different values after normalizing** — the install on disk is **not** the one the
  package manager records. That happens on an extracted, POC or hand-placed install, and then
  `szBuildVersion.json` describes what will actually **load**, so it wins. Reporting the package
  manager's number here states a wrong version as fact about the very thing this module exists to
  establish. Observed 2026-09-01 on Ubuntu 24.04: `dpkg-query` reported `4.3.4-26210` while
  `/opt/senzing/er/szBuildVersion.json` read `4.4.0.26242`, and `SzProduct.get_version()` — once
  Step 3's environment script had run — returned `4.4.0`, agreeing with the file and not with
  `dpkg`. Environment observation, not an MCP-sourced fact.
- **The package manager reports nothing at all** — no such package, empty output, or no package
  manager. That is **not** "not installed": it means the install is not package-manager-owned, and
  `szBuildVersion.json` is the source. ⚠️ **This is a route the server documents rather than an
  exotic case** — `sdk_guide(topic='install', platform='linux_apt')` gives
  `dpkg-deb -x senzingsdk-runtime_*.deb /opt/senzing` for containers, CI and no-sudo environments
  (server 1.35.3, 2026-09-01), and on it no package is ever registered.

⚠️ **`SzProduct.get_version()` is the tiebreaker, and it is reachable later than you need it.**
It is authoritative for the library that will actually load, but the import fails until Step 3's
environment script exports `LD_LIBRARY_PATH` — which is exactly why Step 1 can be forced onto the
filesystem fallback. Once Step 3 has run, use it to settle any disagreement, and correct the
version aloud if what you reported at Step 1 turns out to have been the package manager's.

⛔ **If the available version cannot be determined, say the check was skipped and name why**
(INV-163). "No data" is never "up to date" — an unreachable repository, a missing package manager,
or an install that no package manager owns are all *unknown*, and reporting them as current is the
one outcome worse than not checking.

### Before the offer: read the target's release notes

Only when a newer version is genuinely available. With no newer version, or when the check was
skipped, there is no lookup and no offer: record the outcome (see the checkpoint below) and continue
on the existing-install path in Step 1. The **target** is the newest available version. Read its
notes **now, before the offer**, so that the offer turn relays what applies instead of asking
before it has looked. A version the bootcamper names in reply to the offer gets the same lookup
then, before it is installed (see "The offer").

⚠️ **A 4.x → 4.y update is covered by the target version's release notes, not by a generic
procedure.** `sdk_guide` has no `upgrade` topic, and the migration material a generic upgrade
query finds is for V3→V4 only. `sz_dbupgrade`, `sz_configupgrade` and `sz_configtool` are V3→V4
migration tools, and which of them a migration uses depends on the V4 version doing it:
`sz_dbupgrade` and `sz_configupgrade` for v4.0–v4.3, and `sz_dbtool upgrade` and `sz_configtool`
(configuration upgrades folded in) for 4.4.0 and later. A 4.x → 4.y update needs none of them.
(The tool table is in *v4.4.0 Detailed Release Notes*, "Command-line Tools & SDKs", from
`search_docs(query='sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native command-line tools', category='release_notes')`;
server 1.37.15, docs index 2026-09-28 23:38 UTC, 2026-09-28.) What a point release needs is in the
*target* version's "Migration & Action Required" notes, which `search_docs` serves under
`category='release_notes'` (server 1.37.14, docs index 2026-09-28 03:23 UTC, 2026-09-28). Relay
what applies in the offer turn, above its question.
<!-- MCP-NEGATIVE: search_docs(query='upgrade Senzing SDK 4.3 to 4.4 procedure') plus get_capabilities' sdk_guide topic enum — no 4.x-to-4.y procedure for that phrasing; the corpus serves V3-to-V4 migration material for it, and the topic list carries no upgrade entry — owner: search_docs(query='upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change required migration action required', category='release_notes') IS the route that carries the point-release notes, and it returns the v4.4.0 Detailed Release Notes' Migration & Action Required section, so the reader must go there rather than conclude that no procedure is documented (routing negative) — server 1.37.14, 2026-09-28 -->

- **Target 4.4.0.** Run
  `search_docs(query='upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change required migration action required', category='release_notes')`.
  ⚠️ The first hit is *What's New in v4* "Migration guides", a V3→V4 link list. The section you
  want, *v4.4.0 Detailed Release Notes* "Migration & Action Required", ranks just below it: read
  past the first hit rather than concluding the notes are missing. It covers upgrading from
  v4.0.0 through v4.3.x. Relay the items that apply:
  - **No schema change required** when upgrading from any v4 version.
  - **License:** confirm the license string is valid. A corrupt value now fails startup instead
    of silently falling back to the evaluation license.
  - **Configuration:** the `WEBSITE` feature, the `TAX_ID_TYPE` attribute and the
    very-common-attribute performance changes take effect only in a configuration that includes
    them. A new install's default configuration already does; for an existing configuration,
    Senzing Support gives the steps.
  - **SQL Server only:** the datastore must use a UTF-8 collation, which on an existing datastore
    is a rebuild and reload. Relay it only when the datastore is SQL Server; it does not apply
    under the SQLite default.
  - **Coming from 4.2.x or earlier only:** the Windows `.zip` and macOS `.dmg` installers were
    discontinued in 4.3.0. Relay it only when the installed version is 4.2.x or earlier.
- **Any other target** (a 4.4.x patch, 4.5 or later). Query `category='release_notes'` for the
  *target* version's "Migration & Action Required", for example
  `search_docs(query='upgrading to <target version> migration action required', category='release_notes')`
  with the version filled in. That phrasing was never executed for a later target, so if the
  results are empty or off-topic, re-query with the target's own wording before concluding
  anything. Relay the notes when they cover the installed version. Only when the target's notes
  do not cover it is the step **undocumented, not known to be unnecessary**; say so in the offer.
- **`search_docs` unreachable.** Relay the 4.4.0 items above as last verified on 2026-09-28, and
  say that they could not be re-checked (INV-163).

If the bootcamper already has a populated repository, mention that the update touches the SDK and
not their data. Add, from the 4.4.0 notes, that many matching improvements apply to already-loaded
data only after reprocessing, so the new matching does not reach that data by itself. The offer's
question then lets them decide.

### The offer

The offer comes only after the lookup above. In the offer turn, above the question, relay the items
from the target's notes that apply to this install, and the populated-repository note when it
applies. They are statements, not further questions.

Only when a newer version is genuinely available. **One 👉 question, its own turn** (INV-251), and
it ends the turn:

> 👉 **Senzing [available] is available and you have [installed] installed — would you like to
> update?** (reply no to keep your current version; or name a specific version)

- **On no:** one line — "Keeping [installed]." — then Step 1's existing-install path. Nothing recorded as a
  failure, and **do not ask again** this session or the next (INV-006).
- **On yes:** update to the newest available using the platform command above.
- **On a named version:** run the lookup above for that version and relay what applies (see
  below), then install. On **apt**, use the versioned `direct_download` URL from
  `sdk_guide(topic='install', platform='linux_apt')` — the filenames carry the version and each
  has a `sha256`; **verify that checksum before installing**, and note the download needs
  `mcp.senzing.com` reachable with no inline fallback. ⛔ For **Homebrew casks and Scoop**, a
  version-exact install is **not documented by the server** — say so and offer the latest instead,
  rather than inventing a pin.

**A named version's notes are relayed, not asked about.** When the bootcamper names a version, run
the lookup above for that version before installing, and relay what applies in the next turn, above
the EULA question. Do not ask another 👉 question about it (INV-251): the bootcamper has already
chosen, and the EULA question is the only one left before the install. When that version's notes do
not cover the installed version, say the step is undocumented, not known to be unnecessary ("Any
other target" above), then install. On Homebrew or Scoop the offer falls back to the latest, whose
notes the offer turn already relayed.

⛔ **(INV-338) Ask the EULA question before any package installs** — reuse the existing wording in Step 3
Phase 1 rather than writing a second copy. An update is an install.

⛔ **(INV-338) The EULA variable differs per platform, and a wrong one is silently ignored:**

| Platform | Variable | Value |
|---|---|---|
| `linux_apt`, `linux_yum` | `SENZING_ACCEPT_EULA` | `I_ACCEPT_THE_SENZING_EULA` |
| `macos_arm` | `HOMEBREW_SENZING_ACCEPT_EULA` | `i_accept_the_senzing_eula` (**lowercase**) |
| `windows` | `SENZING_ACCEPT_EULA` | `I_ACCEPT_THE_SENZING_EULA` |

(All three verified against `sdk_guide` on server 1.32.2, 2026-07-31.) Getting the name or value
wrong does not error — the install does nothing and reports success, which is why the
verification below is required rather than advisory.

**(INV-338) If they decline the EULA here, the working install is kept and Module 2 continues** (non-blocking,
INV-048). Install nothing. Say one line, "Keeping [installed].", record `update-declined`, and do not
offer the update again (INV-006). Then continue on the existing-install path in Step 1: Step 3's
Phase 3 and environment script, then Step 4. A declined EULA here is never recorded as a failure.
Step 3 Phase 1's "Stop here" does not apply: that branch is for a fresh install or the upgrade from
below V4.0, where there is no working install to keep.

### After updating

1. **Re-run Step 4** (verify installation), after rejoining the existing-install path in Step 1:
   Step 3's Phase 3 and its environment script, with the values re-read for the updated install.
   Step 4 is already a required stop; route through it.
2. **Probe the platform artifact** as shown above — exit 0 is not evidence (INV-218).
3. **If verification fails**, say so plainly, **name the version that was working**, and do
   **not** mark Module 2 complete. Reinstalling the previous version is the fallback; on apt its
   exact `.deb` is still addressable by filename.

**Checkpoint:** record the outcome — `up-to-date`, `update-declined`, `updated-to-[version]`, or
`check-skipped-[reason]` — under step 1 in `config/bootcamp_progress.json`, so a resumed session
does not re-offer what was already declined.

## Step 2: Determine Platform

**Detect first, do not ask.** This gate is satisfied by *determining* the platform, not by asking
a question. Read `os`/`arch` from `config/bootcamp_preferences.yaml` (persisted during onboarding);
if absent, detect from the environment/system context (else run `uname`/`systeminfo`). State the
detected platform in one line and proceed — e.g. "Detected macOS on Apple Silicon; say so if that's
wrong." For macOS, also establish whether it is Apple Silicon (M1/M2/M3/M4) or Intel from the same
source.

**Fallback only** — when detection is genuinely unavailable or ambiguous, ask this pinned question
and wait:

👉 **Which operating system and processor architecture are you using? Reply with a number:**

1. Linux (x86-64)
2. Linux (ARM64)
3. macOS (Apple Silicon)
4. macOS (Intel)
5. Windows (x86-64)

*(Internal: end the turn on this question and wait.)*

Then resolve the `sdk_guide` platform value using the rules below. Do NOT assume a native
install: several OS + language combinations require Docker. The MCP server is authoritative;
if uncertain, call `sdk_guide(topic='install')` with no platform to get the live decision tree.

**Platform options for `sdk_guide`:**

- `platform='linux_apt'`: Debian/Ubuntu/Mint (apt/dpkg)
- `platform='linux_yum'`: RHEL/Fedora/Amazon Linux (yum/dnf)
- `platform='macos_arm'`: macOS Apple Silicon (Homebrew cask; the tap is a preview release, below)
- `platform='windows'`: Windows 10/11 (Scoop; the bucket is a preview release, below)
- `platform='docker'`: Platform-independent container; the fallback and the required path for
  several cases below

⚠️ **The Homebrew tap and the Scoop bucket are preview releases that Senzing does not support.**
Each README opens with "**Preview Release — Unsupported** … provided as-is with no warranty and is
**not supported**". For `macos_arm`,
`search_docs(query='homebrew-senzingsdk preview release unsupported tap install cask')` returns it
as the `senzing/homebrew-senzingsdk` section "homebrew-senzingsdk". For `windows`,
`search_docs(query='scoop-senzingsdk update scoop update senzingsdk')` returns it at the top of the
`senzing/scoop-senzingsdk` README (server 1.37.14, docs index 2026-09-28 03:23 UTC, 2026-09-28).
When you name either route, say this once, as a fact about the tap or the bucket, not as advice
against it: they remain the native routes in rules 3 and 4 below.

**Routing rules (apply in order):**

1. Chosen language is Python AND OS is macOS or Windows → a **Linux environment**, and there are
   two, not one. The Python SDK is supported on Linux only, so it needs one either way:
   - **A container** → **`platform='docker'`**. Available on macOS and Windows.
   - **WSL2 (Windows only)** → the SDK installs natively *inside* the Linux distribution, so the
     platform resolves to **`platform='linux_apt'`** and the rest of this module follows the
     `linux_apt` path unchanged. This is the route a Bootcamper who wants a native-feeling
     toolchain will pick, and Bootcamp preparation now names its cost at the language gate.
   Both are what the server offers: `sdk_guide(topic='install', platform='windows',
   language='python')` returns *"use Docker or WSL2 to run Python inside a Linux container"*
   (server **1.33.0, 2026-08-21**). ⚠️ On macOS only the container route exists — the same server
   sentence appears under `platform='macos_arm'` and its WSL2 half is wrong there.
2. macOS Intel → **`platform='docker'`**. There is no native Intel-Mac install: the Homebrew
   tap is Apple Silicon (ARM64) only.
3. macOS Apple Silicon (non-Python) → **`platform='macos_arm'`**. Relay the tap's preview
   status above. If the chosen language runs on the JVM (Java), also read "The launch
   environment" in Step 3 before the first run — installing the SDK is not the same as being
   able to launch against it.
4. Windows without Scoop (non-Python) → **`platform='docker'`**. With Scoop available →
   **`platform='windows'`**, and relay the bucket's preview status above.
5. Linux → **`platform='linux_apt'`** or **`platform='linux_yum'`** based on the package
   manager.

When a learner lands on Docker because of these rules, briefly explain why (e.g., "The Senzing
Python SDK is Linux-only, so on macOS we'll run it in a container") so the redirect doesn't
feel arbitrary.

Use `sdk_guide` with `topic='install'`, the resolved `platform`, and the bootcamper's chosen
language as the `language` parameter to get current installation commands. The MCP server
always has the latest instructions.

**Checkpoint:** write step 2 to `config/bootcamp_progress.json`.

## Step 3: Install Senzing SDK

Follow the platform-specific instructions from `sdk_guide`. Installation has three phases, and
the EULA question comes first: nothing is installed until the bootcamper accepts it (INV-338). An existing
V4.0+ install (Step 1's existing-install path) skips Phase 1 and Phase 2, is not asked the EULA
again, and starts at Phase 3; it still writes the environment script ("Create the project-local
environment script" below) (INV-339).

**Before recommending any approach**, call `search_docs` with `category='anti_patterns'` to
check for known pitfalls on the user's platform.

**Phase 1: EULA acceptance (requires bootcamper input, before anything is installed):**

The Senzing SDK requires EULA acceptance before it is installed, so this question comes before
**every** install command on **every** path: adding the Senzing package repository (the apt or
yum `senzingrepo` package, the Homebrew tap, the Scoop bucket), installing the SDK package, and
the `docker` path's in-container `linux_apt` install (INV-338). Tell the bootcamper they can review it at
<https://senzing.com/end-user-license-agreement/>, then present the EULA question:

👉 **Do you accept the Senzing End User License Agreement (EULA)?** (respond yes or no)

*(Internal: end the turn on this question and wait. Do not proceed until the bootcamper
answers.)*

Once the bootcamper responds, act on their answer:

- **If they accept the EULA:** proceed to Phase 2 to install the SDK package, then Phase 3 to
  install the language-specific SDK bindings. Both run without stopping for another question.
- **(INV-338) If they decline the EULA:** install nothing — no package repository, no SDK package and
  no language bindings. On a fresh install, or the upgrade from below V4.0, there is no working
  SDK to fall back on. Explain: "The Senzing SDK cannot be used without EULA acceptance. The
  remaining installation steps and subsequent bootcamp modules require the SDK." Do not write
  the checkpoint. Stop here. An update of a working V4.0+ install declined here does not stop:
  Step 1b states its outcome (keep the working install and continue).

**Phase 2: Install the SDK package (only after EULA acceptance; execute without stopping):**

Before the package install, set the EULA variable for the bootcamper's platform, taking its name
and value from the table in Step 1b ("The EULA variable differs per platform") (INV-338). The install then
runs without prompting; a wrong name or value makes it do nothing and report success. On the
`docker` path, set the `linux_apt` variable inside the container.

For native installs (`linux_apt`, `linux_yum`, `macos_arm`, `windows`):

1. Add the Senzing package repository.
2. Install the Senzing SDK package.

For the `docker` path (Intel Mac, Python on macOS/Windows, or Windows without Scoop):

- **Do not use the pre-built `senzing/senzingsdk-tools` images.** They require PostgreSQL and
  do not support SQLite, which is the bootcamp default (Step 7). Instead, run a plain Linux
  container (e.g., `debian:bookworm-slim`) and follow the `linux_apt` steps inside it so SQLite
  keeps working.
- Mount the bootcamper's project directory into the container so all artifacts (database,
  config, source) land in the working directory, not inside an ephemeral container layer.
- Call `sdk_guide(topic='install', platform='docker', language='<chosen_language>')` for the
  current container commands and image names.
- Never drive interactive Senzing CLI tools (`sz_configtool`, `sz_explorer`): they require
  human input. Generate SDK code via `generate_scaffold` instead.
- Senzing publishes native ARM64 images, so no x86 emulation is needed on Apple Silicon.
- ⛔ **On this path, a syntax error in a file you just wrote is retried once before it is
  believed** — files are written host-side and run container-side across the bind mount you set up
  in the previous bullet, and a partially-synced read reports a parse error at a well-formed line.
  The rule, the in-container compile check that confirms it, and why a host/container
  version split is *not* the first explanation are in
  `../bootcamp-onboarding/ground-rules.md` → "Running a file you just wrote, when the run happens
  somewhere else". Do not restate them here (INV-183, INV-300): the rule applies from this module through
  query programs, so it lives with the cross-cutting execution rules and is linked from the step
  that creates the condition.
- **Record the container for lifecycle tracking (INV-101).** When you start the container,
  give it a stable `--name` and append an entry to a `docker_containers` list in
  `config/bootcamp_progress.json` — at least its `name` and the `runtime` you actually used
  (`docker`, `podman`, or `container` for Apple's `container` CLI); also `image` and `purpose`
  when handy. **Record the runtime truthfully**: the hooks stop and report each container with
  the CLI named there, so a wrong value means a container is reported under a tool that never
  started it. An entry with no `runtime` is treated as `docker`. The `sessionEnd` hook stops
  recorded containers on exit (`<runtime> stop`, not remove) and `sessionStart` surfaces them on
  resume so they can be restarted or regenerated. (The list key stays `docker_containers` for
  compatibility with in-flight bootcamps, whatever runtime its entries name.)

**Phase 3: Install language bindings (after Phase 1's EULA acceptance, or directly on Step 1's
existing-install path, which skips Phase 1 and Phase 2; INV-338, INV-339):**

3. Install the language-specific SDK bindings for the chosen language — Python, Java, C#, Rust or
   TypeScript — **by the route the Senzing MCP server names for that language, never from a public
   package registry that route does not name, and NOT from a package manager at all for Python.**
   Each language's route is below; read it at run time rather than from this file (INV-080).

   ⛔ **Python: there is nothing to install here, and `pip install senzing` is an error-severity
   anti-pattern.** (INV-222 — INV-066's pip rules govern the plugin's own tooling only.) The `senzing` and `senzing_core` packages **ship inside `senzingsdk-runtime`**,
   which the earlier phase already installed, so Python's Step 3 work is to make them importable —
   not to fetch them. Take the paths from the server, never from this file (INV-080):
   `sdk_guide(topic='install', platform='<platform>', language='python')` returns them in
   `install.platform.env_vars` and repeats the rule verbatim in `install.platform.gotchas[]`.

   ⛔ **On `linux_apt` with Python, BOTH `PYTHONPATH` and `LD_LIBRARY_PATH` are required — set both.**
   ⚠️ **One `sdk_guide` payload says this two different ways, and the governing half is the
   language-specific one.** Re-verified on MCP server **1.32.9, 2026-08-17**,
   `sdk_guide(topic='install', platform='linux_apt', language='python')`:

   - The **Python SDK** entry in `install.platform.gotchas[]` states it unconditionally, and this is
     the one that governs for `language='python'`:

     > "The senzing and senzing-core packages are included in senzingsdk-runtime at
     > /opt/senzing/er/sdk/python. Do NOT pip install them — instead set
     > PYTHONPATH=/opt/senzing/er/sdk/python:$PYTHONPATH **and**
     > LD_LIBRARY_PATH=/opt/senzing/er/lib:$LD_LIBRARY_PATH"

   - The **same response** hedges the same variable twice — `env_vars.LD_LIBRARY_PATH` reads
     *"(only needed if native lib not found automatically)"*, and the first `gotchas[]` entry repeats
     that as a general note. `sdk_guide(topic='configure', platform='linux_apt', language='python')`
     returns `environment.env_vars` with the identical hedged string, so changing topic does not
     resolve it.

   **Both readings are in the payload; do not silently pick one — the contradiction is the fact the
   reader needs.** Reported upstream 2026-08-16 (`submit_feedback`, `bug`, anonymous); do not
   re-file. Until the server changes, treat the language-specific line as authoritative on this
   platform.

   ⚠️ **The cost of getting this wrong lands a module later.** An environment script written from
   `env_vars` alone sets only `PYTHONPATH`; the import then fails at the first engine call with
   `libSz.so: cannot open shared object file: No such file or directory` — which reads as a **broken
   SDK install** rather than an incomplete environment, in a module that did not cause it. (Observed
   on Senzing SDK 4.3.4-26210, apt-installed at `/opt/senzing`, no custom location; the loader
   behavior itself is observation-only.) Take the values from `sdk_guide` rather than from this
   file — the paths above are quoted with their route, version and date, not adopted (INV-080).
   `generate_scaffold(language='python', workflow=<any>)` carries the same rule as an
   `anti_patterns[]` entry at **`severity: error`**, for **every** workflow it scaffolds — quoted
   below because the wording is the argument (re-verified live, MCP server 1.32.9, 2026-08-14):

   > "The senzing and senzing-core Python packages ship with senzingsdk-runtime at
   > /opt/senzing/er/sdk/python. Set PYTHONPATH=/opt/senzing/er/sdk/python:$PYTHONPATH — do NOT pip
   > install them. The PyPI packages are for unsupported community projects only."

   ⛔ **Why this matters more than most wrong commands: it succeeds.** `pip install senzing` exits 0,
   so this module reports a clean install — and the PyPI packages then **shadow** the SDK-shipped
   ones on `sys.path`. The damage surfaces a module later, as System verification's SDK
   initialization failing with `libSz.so: cannot open shared object file`, which reads as an
   environment fault rather than as the install instruction that caused it. It is also a **version
   skew**: this module's version check reads the *engine's* version through the native library, so
   it reports a current install while the bindings actually imported are older. The plugin's own
   shipped example recap records this happening on a real run
   (`../../docs/examples/bootcamp_recap.example.md`).

   **Detection — run it, do not assume:**

   ```bash
   python3 -c "import senzing, sys; print(senzing.__file__)"
   ```

   If the path is **not** under the SDK's Python directory (`PYTHONPATH` as the server returned it),
   PyPI packages are shadowing the real ones. Remedy: uninstall them
   (`python3 -m pip uninstall -y senzing senzing_core`) **or** prepend the SDK path to `PYTHONPATH`
   so the shipped bindings win. Report which was done; do not leave both installed silently.

   ⚠️ **Platform asymmetry, stated deliberately.** The server's `platform_note` on
   `generate_scaffold(language='python', …)` is explicit (same server and date): the Python SDK is
   **only** supported on Linux, and "even if pip install appears to succeed, it is unsupported and
   may produce runtime errors" on macOS or Windows. So there is no macOS/Windows Python install to
   perform: the routes are another language (Java and C# official; Rust and TypeScript
   community-supported) or Docker/WSL2, which this module's platform routing already covers.

   For **Java, C#, Rust and TypeScript**, the bindings come through that ecosystem's tooling
   (Maven or Gradle, NuGet, Cargo, npm), but **not from its public registry unless the route
   names one**. Call `sdk_guide(topic='install', platform='<platform>', language='<language>')`
   first for every language, then follow the route for the chosen one. The quotes below are
   dated evidence of what each route said, not the command to run:

   - **Java:** `sdk_guide`'s install reply names no source for the Java bindings, so the route is
     the Java SDK reference: `search_docs(query='Java SDK sz-sdk.jar Maven Usage local Maven
     repository')`, and follow its "Maven Usage" and "Installation in Local Maven Repository"
     sections. Its top hit is an FAQ about a JAR-verification warning: read past the first hit to
     those two sections. On server 1.37.16 (2026-09-30) they said `sz-sdk.jar` "is not provided via Maven
     Central" and is the one "provided with the Senzing product", used as a system-scoped
     dependency or installed into the **local** Maven repository (`java -jar sz-sdk.jar` prints
     the `mvn install:install-file` command for it).
     <!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='linux_apt', language='java') — the reply carries no compatibility_notes and no source for the Java bindings, only the platform install and the Python gotcha — owner: search_docs IS the route that carries the Java SDK reference: search_docs(query='Java SDK sz-sdk.jar Maven Usage local Maven repository') returns its "Maven Usage" and "Installation in Local Maven Repository" sections, so the reader must go there rather than conclude the source is undocumented (routing negative) — server 1.37.16, 2026-09-30 -->
   - **C#:** call `sdk_guide(topic='install', platform='<platform>', language='csharp')` and follow
     its `gotchas`: where the reply has a C# line, that line names the package source. On server
     1.37.16 (2026-10-01) the **`windows`** reply's gotcha said "C# / .NET: the Senzing.Sdk NuGet
     package is included in the SDK install (`sdk\dotnet\`), NOT published to nuget.org. Use:
     `dotnet nuget add source "$env:SENZING_DIR\sdk\dotnet" --name SenzingLocal; dotnet add
     package Senzing.Sdk --source SenzingLocal`". That is the `windows` reply's form, with the
     Windows install variable in its path, so present it to a Windows bootcamper only (INV-283).
     On the same date the `linux_apt`, `linux_yum` and `macos_arm` replies had no C# line, and
     `docker` follows `linux_apt`. When the reply names no source, go down this list in order,
     stop at the first step that gives an answer, and tell the bootcamper which step it was:
     1. **The C# SDK reference:** `search_docs(query='C# .NET SDK Senzing.Sdk NuGet package')`.
        On server 1.37.16 (2026-10-01) it said "After adding the `Senzing.Sdk` NuGet package to
        your project dependencies" and did not say where that package comes from.
     2. **What this machine's install holds:** look for a `Senzing.Sdk.*.nupkg` file in the
        `dotnet/` directory of the install's `sdk/` directory. Locate that `sdk/` directory from
        this platform's own install reply (the directory its `PYTHONPATH` or `sz-sdk.jar` path
        sits in), never from another platform's reply. If the file is there, use that `dotnet/`
        directory as a local NuGet source (`dotnet nuget add source <that directory> --name
        SenzingLocal`, then `dotnet add package Senzing.Sdk --source SenzingLocal`), and tell the
        bootcamper the source was **observed in their install, not named by the MCP server**
        (INV-283). No directory, or a directory with no `Senzing.Sdk.*.nupkg`, means nothing
        was observed.
     3. **Neither:** tell the bootcamper that no MCP route names the package source for their
        platform, and that nothing in their install supplied one.

     ⛔ **Never add a public NuGet feed for `Senzing.Sdk` (nuget.org or any other) on your own (INV-222).**
     <!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='linux_apt', language='csharp'), the same call with platform='linux_yum' and with platform='macos_arm', and search_docs(query='C# .NET SDK Senzing.Sdk NuGet package') — on linux_apt, linux_yum and macos_arm no reply says where the Senzing.Sdk NuGet package comes from: the install replies carry no C# line in their gotchas, and the reference says only "After adding the Senzing.Sdk NuGet package to your project dependencies" — owner: sdk_guide(topic='install', platform=<platform>) IS the route that carries the package source per platform, and its windows reply names it in its gotchas ("included in the SDK install (sdk\dotnet\), NOT published to nuget.org"), so the claim is scoped to the platforms asked and is not a claim that no platform's reply names it; search_docs carries the C# SDK reference ("Senzing.Sdk for C#", the top hit) and states no source (absence negative) — server 1.37.16, 2026-10-01 -->
   - **Rust:** call `sdk_guide(topic='install', platform='<platform>', language='rust')` and follow
     its `compatibility_notes`, taking the dependency line from that reply. On server 1.37.16
     (2026-09-30) it said "The Rust SDK (sz-rust-sdk) is NOT on crates.io. You MUST use a git
     dependency."
   - **TypeScript:** call `sdk_guide(topic='install', platform='<platform>', language='typescript')`
     and follow its `compatibility_notes`, taking the install command from that reply. On server
     1.37.16 (2026-09-30) it said "The TypeScript/Node.js SDK (sz-napi) is NOT on npm. You MUST
     install from the GitHub repository". The build-from-source warning below still applies.

   ⚠️ The bare-`pip` prohibition still applies to the plugin's **own** tooling installs (`fpdf2`,
   Playwright — INV-066): always an explicit `python3 -m pip`, never a bare `pip`, and PEP 668
   handled with a project-local virtualenv. That rule is about *how* to run pip for the plugin's
   helpers; it never authorizes pip for the Senzing SDK, which is not a pip package at all.

**TypeScript/Node.js warning:** The TypeScript SDK (`sz-napi`) may require building from source
if prebuilt binaries are not available for the user's platform. This involves installing the
Rust toolchain, cloning `sz-rust-sdk` and `sz-rust-sdk-configtool` as Cargo dependencies, and
building the native addon with `napi-rs`. Warn the user upfront: "The TypeScript SDK setup is
more involved than other languages, it may require building native bindings from source, which
needs the Rust toolchain. If you'd prefer a faster setup, Java or C# typically have simpler
install paths." If they proceed with TypeScript, guide them through the full build sequence in
one go rather than letting them discover steps through trial and error.

**Windows-specific:** Building the TypeScript SDK from source on Windows requires Visual Studio
Build Tools (not the full IDE) with the "Desktop development with C++" workload. Install via
`winget install Microsoft.VisualStudio.2022.BuildTools` or download from
visualstudio.microsoft.com. The Rust toolchain installer (`rustup-init.exe`) will detect the
build tools automatically.

### Recovery: build-from-source failures (TypeScript)

> **Applies to the TypeScript from-source build only.** This branch handles a failure *during*
> the `sz-napi` from-source build described just above (the Rust toolchain / `napi-rs` /
> native-addon compile). It does not apply to other languages or to Senzing engine/runtime
> errors.

**1. Detection and routing.** If the from-source build exits non-zero, or reports a
native-addon, `node-gyp`, toolchain, or Node-version failure while compiling `sz-napi`, treat
it as a mid-build failure and enter **this** recovery branch. Do NOT fall through to the
module's generic Error Handling block (the `SENZ`-code → pitfalls → symptom path). That generic
path is tuned for Senzing engine/runtime errors and will not recognize a half-finished native
compile.

**2. Summarize before offering options.** Before presenting any options, state in plain
language which build stage failed and the single most likely cause, chosen from the known-cause
table below. Name the specific cause (for example, "the native addon failed to compile because
the C++ build toolchain is missing") rather than pasting the raw build log. If the failure
signal does not match any known cause, say so plainly ("this is an unrecognized build failure")
and still continue to the options: an unrecognized failure is never a dead end.

**3. Known-cause table.** Match the failure signal to one cause. The detailed per-cause fixes
live in a TypeScript "Common Environment Issues" reference (`lang-typescript.md`) that is a
later porting phase; until then, source the fixes from the Senzing MCP server (see item 5) and
the inline pointers here.

| Cause | Failure signal | Fix reference ("Common Environment Issues") |
|---|---|---|
| `NODE_VERSION` | `SyntaxError` on modern syntax, `ERR_UNSUPPORTED_ESM_URL_SCHEME`, Node.js older than 18 | "Node.js Version Conflicts" — ⚠️ **on the `docker` path, rule out bind-mount propagation lag first**: retry once (see the Phase 2 `docker` bullets), because a version conflict reproduces and lag does not |
| `NATIVE_ADDON` | `gyp ERR! build error`, `Cannot find module '.../*.node'` | "Native Addon Build Failures (node-gyp)" |
| `TOOLCHAIN` | missing C++ compiler, missing Rust toolchain, or missing Visual Studio Build Tools | "Native Addon Build Failures (node-gyp)" plus the Windows note above in this Phase 3 |
| `MODULE_SYSTEM` | `ERR_REQUIRE_ESM`, `Cannot use import statement outside a module` | "ESM vs CommonJS Module Resolution" |
| `PKG_MANAGER` | `ERESOLVE unable to resolve dependency tree`, lockfile conflicts | "Package Manager Conflicts" |

**4. Offer targeted options.** After the summary, always offer, at minimum, these three:

- **Fix the common cause:** apply the fix for the matched cause (see sourcing in the next
  item), then retry.
- **Retry the build:** re-run the from-source build sequence.
- **Fallback path:** proceed without a successful from-source build (see item 6). One fallback
  is switching to a language with a simpler install path (Java or C# typically have simpler
  paths); another is any prebuilt/alternative install route the MCP server reports as available.

**5. Sourcing (no hardcoded URLs).** For the detailed fix steps, use the Senzing MCP server:
`sdk_guide(topic='install', platform='<user_platform>', language='typescript')` and
`search_docs(query='community wrapper not the official SDK package registry',
category='anti_patterns')`. ⛔ **`query` is `search_docs`' only REQUIRED parameter — a bare
`category=` is a call a schema-respecting client cannot construct at all**, so the retrieval
vocabulary belongs here rather than being left to the reader (INV-212). That query returns
*Senzing Anti-Patterns: Ecosystem and Dependencies* as its top hit — official-vs-community
packages, repository choice, and the `senzing-garage` caution — which is the on-point article
when a community wrapper's from-source build has just failed (verified server 1.37.19, docs
index 2026-10-02 18:46 UTC, 2026-10-04). Never paste external URLs into this recovery flow; all
external/toolchain knowledge comes from the MCP tools (and, once ported, the `lang-typescript.md`
reference). If an MCP tool is unavailable, the fallback path still applies, so guidance degrades
gracefully rather than dead-ending.

**6. Resume or continue Module 2.** Neither continuation requires deep toolchain debugging:

- **On a successful retry** (the build now succeeds), resume the normal sequence: continue
  Phase 3 (install the language bindings) and proceed to Step 4 (verify installation).
- **On the fallback path**, continue Module 2 without a successful from-source build: proceed to
  Step 4 verification using the prebuilt/alternative install (or the newly chosen language) so
  setup is never blocked on the from-source compile.

**7. Never a dead end.** There is always a way forward: retry after a fix, or the fallback path.
If a retry fails again, re-summarize against the known-cause table (re-classifying on the new
signal) and re-offer the options; do not silently loop on the same error. If every option has
genuinely been exhausted, do not re-run the same failing command: state the current blocker in
plain language and present the support / next-step options (for example, capture the failure
details for a support request via `search_docs`, or take the fallback path if not already
tried). This terminal state names the blocker and the next step rather than looping.

### Create the project-local environment script

(INV-339) Every path through Step 3 ends here, including Step 1's existing-install path, which skips the
install phases and still writes this script.

**🚨 NEVER modify the user's global shell configuration** (`~/.zshrc`, `~/.bashrc`,
`~/.profile`, PowerShell `$PROFILE`, etc.) to set Senzing environment variables — **INV-199**.
Instead, create a project-local environment script at `src/scripts/senzing-env.sh` (on Windows,
`src\scripts\senzing-env.ps1`; see [the Windows script](#env-script-windows)) that sets
`SENZING_ROOT`, library paths, and any other Senzing-specific variables. Source this script before
running bootcamp tasks; on Windows, dot-source it with `. .\src\scripts\senzing-env.ps1` (unverified
on Windows PowerShell 5.1 here, INV-163). This keeps the bootcamp self-contained and avoids side
effects on the user's system.

⛔ **`sdk_guide` will tell you to persist to a shell profile. Do not act on it — say so instead.**
`sdk_guide(topic='install', platform='macos_arm', language='java')` returns *"DYLD_LIBRARY_PATH must
be set at the shell level before any JVM or Python launch. Add to `~/.zshrc` to persist"*
(re-verified on MCP server 1.32.8, 2026-08-11), and the Windows guidance is equivalent. That is
correct advice for a human operator configuring their own machine, and forbidden here: the bootcamp
does not edit the Bootcamper's home directory on their behalf. When you relay this guidance, state
that the bootcamp writes the project-local script instead and that persisting it globally is their
choice to make later, by hand. This is the likeliest way INV-199 gets breached, which is why it is
called out at the step rather than left to the ground rules (INV-183).

<a id="env-script-path-resolution"></a>

**The env script MUST resolve its own path in the platform's *default* shell, not only in bash.**
This is the canonical statement of the rule; other modules link here rather than restating it (INV-300).
Because the documented pattern is to **source** the script into the bootcamper's interactive shell
(see the same-shell requirement below), the shell it has to work in is whatever that bootcamper's
shell actually is — and on macOS that is **zsh**, not bash. `${BASH_SOURCE[0]}` — the idiom anyone
reaching for self-location writes first — is a bash array and expands to **empty** under zsh. The
script then resolves the project root to the wrong directory and keeps going, so the failure lands
later and somewhere else. Branch on the shell:

```bash
# --- resolve this script's own location (bash and zsh) ------------------------
# ${BASH_SOURCE[0]} is bash-only and expands to EMPTY under zsh, macOS's default
# shell, so branch rather than assume bash. bash parses the zsh-only expansion in
# the untaken branch without complaint.
if [ -n "${ZSH_VERSION:-}" ]; then
  _sz_self=${(%):-%x}                # zsh: this file's own path
else
  _sz_self=${BASH_SOURCE[0]:-$0}     # bash: this file's own path
fi
_sz_root=$(cd -- "$(dirname -- "$_sz_self")/../.." && pwd)

# --- fail loudly, naming the path that was computed --------------------------
# config/bootcamp_progress.json exists from project setup on, so it marks the root
# at every step this script is sourced from (engine_config.json waits for Step 8).
if [ ! -f "$_sz_root/config/bootcamp_progress.json" ]; then
  printf 'senzing-env.sh: resolved project root has no config/bootcamp_progress.json\n' >&2
  printf 'senzing-env.sh:   resolved root: %s\n' "$_sz_root" >&2
  printf 'senzing-env.sh:   this is a path-resolution fault, not your Senzing install\n' >&2
  unset _sz_self _sz_root
  return 1 2>/dev/null || exit 1
fi

# --- engine configuration: skip while absent, never export an empty one -----
if [ ! -f "$_sz_root/config/engine_config.json" ]; then
  # Before Step 8 writes it: leave the variable unset and keep going.
  printf 'senzing-env.sh: config/engine_config.json not written yet, so SENZING_ENGINE_CONFIGURATION_JSON is not set; source this script again after Step 8\n' >&2
elif _sz_settings=$(cat -- "$_sz_root/config/engine_config.json"); [ -z "$_sz_settings" ]; then
  printf 'senzing-env.sh: %s is empty — refusing to export an empty configuration\n' \
    "$_sz_root/config/engine_config.json" >&2
  unset _sz_self _sz_root _sz_settings
  return 1 2>/dev/null || exit 1
else
  export SENZING_ENGINE_CONFIGURATION_JSON="$_sz_settings"
fi

export SENZING_PROJECT_ROOT="$_sz_root"
# Platform-specific exports (SENZING_ROOT, DYLD_LIBRARY_PATH / LD_LIBRARY_PATH, jar
# paths) go here — take them from sdk_guide(topic='install', platform=…, language=…),
# never from memory or from this file (INV-080).
#
# THAT LIST IS ILLUSTRATIVE, NOT A CHECKLIST. The authority for the FULL variable set is
# the language-specific gotchas[] entry in the SAME sdk_guide response: export every
# variable it names, whether or not this comment happens to list it (INV-222 -- the SDK's
# language packages are made available BY PATH, and the paths come from that lookup). This comment names
# no language on purpose (INV-002) -- the lookup above is what resolves the set for
# whichever language was chosen.
#
# READ gotchas[] FOR YOUR LANGUAGE, NOT env_vars ALONE. env_vars is a summary and it
# disagrees with gotchas[] in BOTH directions, so neither the summary nor a fixed list is
# safe alone: it hedges LD_LIBRARY_PATH as "only needed if native lib not found
# automatically" while the language-specific gotchas[] entry in the SAME response requires
# it, and it marks other variables required that a fixed list like the one above can simply
# omit.
#
# IF gotchas[] HAS NO ENTRY FOR YOUR LANGUAGE, THAT IS A GAP TO FILL -- NOT AN EMPTY SET.
# The rule above assumes an entry exists. On some platform/language pairs it does not: the
# response then carries nothing for the chosen language at all, and passing the language
# argument returns the same response as passing none. Exporting only what env_vars happens
# to carry then produces a script holding the native library path and NOTHING FOR THE
# LANGUAGE -- a runtime that starts and cannot find the SDK.
# So: when the chosen language has no entry for the detected platform, derive that language's
# own paths from the INSTALL LAYOUT, export them here, and record them as an observation with
# the version they were measured against -- never as a server fact (INV-080/INV-149). Say in
# the script's header that the value was derived rather than returned.
#
# AN OMITTED VARIABLE FAILS IN ONE OF TWO WAYS, AND ONLY ONE OF THEM IS LOUD.
#   - Loud: the runtime cannot find the native library, and the first engine call fails --
#     "libSz.so: cannot open shared object file" -- one module after this script was
#     written, where it reads as a broken install.
#   - Silent: the runtime finds a DIFFERENT copy of the language bindings on its own module
#     search path, imports it, raises nothing, and every later module runs against a
#     different SDK version than the one this module just verified.
# The second is why Step 4 prints the RESOLVED BINDING PATH and not just a version.
unset _sz_self _sz_root _sz_settings
```

⚠️ **The concrete case, because the general rule above names no language and the omission it
guards against is invisible.** On `linux_apt` with **Python**, `sdk_guide(topic='install',
platform='linux_apt', language='python')` returns **both** variables in `install.platform.env_vars`
— `PYTHONPATH` marked *"required for Python SDK — the senzing and senzing-core packages ship with
senzingsdk-runtime here"* and `LD_LIBRARY_PATH` carrying the *"only needed if…"* hedge — and its
Python `gotchas[]` entry requires both unconditionally: *"Do NOT pip install them — instead set
`PYTHONPATH=…` and `LD_LIBRARY_PATH=…`"* (server 1.33.0, verified 2026-08-26). **So the server
supplies `PYTHONPATH`; a script that lacks it lost it here, not upstream.** This is **INV-222** at
the site that writes the script: the SDK's language packages are made available *by path*, and those
paths come from `sdk_guide` at run time rather than from memory or from this file (INV-080). This template has now
been wrong at each end in turn — once naming `PYTHONPATH` and omitting `LD_LIBRARY_PATH`, then
naming `LD_LIBRARY_PATH` and omitting `PYTHONPATH` — which is why the rule above routes to
`gotchas[]` instead of carrying a longer list. `PYTHONPATH` is Linux-only because the Python SDK is:
*"The Senzing Python SDK is ONLY supported on Linux"* (`platform='macos_arm', language='python'` →
`compatibility_notes`, same server and date), so there is no macOS/Windows counterpart to add.

⚠️ **The other shape of the same problem: a pair the response says nothing about.** The Python case
above is a *disagreement* between `env_vars` and `gotchas[]`; the harder one is a platform/language
pair for which the response carries **no language content at all**, so there is nothing to disagree
with and the omission looks like "this language needs nothing extra". A JVM language on `linux_apt`
is that case — no SDK jar path, and no entry to route to — and a script built from `env_vars` alone
is then missing the one path that language needs. **The classpath bullet under *The launch
environment* below records what that route returns, with its dated `MCP-NEGATIVE` marker, and gives
the path to export and the check that confirms it.** Follow it rather than re-deriving the negative
here (INV-183, INV-300: the rule lives where the reader needs it, and a second dated copy is a second thing
to keep true).

Four things in that block are the point, not decoration:

- **`return 1`, never `exit 1`.** A sourced script shares the bootcamper's shell, so `exit` closes
  their terminal and `set -e` leaks into their session. `return 1 2>/dev/null || exit 1` returns when
  sourced and still exits if someone runs the file directly.
- **The guard names the path it computed (INV-175).** A wrong root that exports nothing produces an error many
  steps later that reads as a Senzing fault; a guard that prints the resolved root is diagnosable on
  sight (the same fail-loudly rule INV-111 applies to generators). The root marker is
  `config/bootcamp_progress.json`, which project setup creates, so the guard holds from Step 4 on.
  It is never `config/engine_config.json`: Step 8 writes that, and a guard on it blames path
  resolution for what is only step order.
- **Skip only the settings export while `config/engine_config.json` is absent (INV-175).** Before Step 8 the
  script prints a one-line notice, leaves `SENZING_ENGINE_CONFIGURATION_JSON` **unset**, still
  exports `SENZING_PROJECT_ROOT` and the platform variables, and returns 0. Step 8 re-sources it.
- **Refuse to export an empty value rather than exporting one.** Senzing's own official code snippets
  guard initialization with `if (settings == null)` — they test for **unset**, not empty — so an
  `export SENZING_ENGINE_CONFIGURATION_JSON=""` sails straight past that check and fails later,
  deeper, and less legibly than no export at all. (Verified against the MCP server: `search_docs` returns
  `senzing/code-snippets-v4` `java/snippets/information/GetVersion.java` and the C# equivalents doing
  exactly this; MCP server 1.32.1, 2026-07-28.)

<a id="env-script-windows"></a>

**Windows keeps its own script: `src\scripts\senzing-env.ps1`, dot-sourced.** Assume Windows
PowerShell 5.1 (the ground rules' "Windows and PowerShell"). A `.bat` file run from PowerShell runs in
a child `cmd.exe`, so the variables it sets never reach the PowerShell window, and nothing reports it:
the next program fails later or finds the wrong library. So Windows gets a PowerShell script and no
`.bat`, and never both: two Windows scripts would drift (one implementation, not two). `$PSScriptRoot`
is the script's own directory however it was reached, so none of the zsh material applies there. The
Bootcamper loads it from the project root, in the PowerShell window that will run their programs, with
`. .\src\scripts\senzing-env.ps1`. This snippet is unverified on Windows PowerShell 5.1 here: CI runs
it under `pwsh` 7 on Linux only (INV-163).

```powershell
# --- refuse to run unless dot-sourced ------------------------------------------
# Every site gives the dot-sourced form. Run any other way, the script prints that
# form, sets nothing and returns.
if ($MyInvocation.InvocationName -ne '.') {
  Write-Host 'senzing-env.ps1: dot-source this script, with the leading dot and space:'
  Write-Host '  . .\src\scripts\senzing-env.ps1'
  return
}

# --- resolve this script's own location -------------------------------------------
# $PSScriptRoot is this file's directory (src\scripts) however it was reached, so the
# project root does not depend on the current directory.
$_sz_root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# --- fail loudly, naming the path that was computed --------------------------------
# config/bootcamp_progress.json exists from project setup on, so it marks the root
# at every step this script is loaded from (engine_config.json waits for Step 8).
# Use return, never exit (INV-175): return ends this script and leaves the
# session as it was.
$_sz_progress = Join-Path (Join-Path $_sz_root 'config') 'bootcamp_progress.json'
if (-not (Test-Path -LiteralPath $_sz_progress -PathType Leaf)) {
  Write-Host 'senzing-env.ps1: resolved project root has no config/bootcamp_progress.json'
  Write-Host "senzing-env.ps1:   resolved root: $_sz_root"
  Write-Host 'senzing-env.ps1:   this is a path-resolution fault, not your Senzing install'
  Remove-Variable -Name _sz_root, _sz_progress -ErrorAction SilentlyContinue
  return
}

# --- engine configuration: skip while absent, never set an empty one ---------------
$_sz_config = Join-Path (Join-Path $_sz_root 'config') 'engine_config.json'
$_sz_settings = $null
if (Test-Path -LiteralPath $_sz_config -PathType Leaf) {
  # Explicit UTF-8: without -Encoding, Windows PowerShell 5.1 reads the file in the
  # ANSI codepage (INV-166).
  $_sz_settings = Get-Content -LiteralPath $_sz_config -Raw -Encoding utf8
  if ([string]::IsNullOrWhiteSpace($_sz_settings)) {
    Write-Host "senzing-env.ps1: $_sz_config is empty - refusing to set an empty configuration"
    Remove-Variable -Name _sz_root, _sz_progress, _sz_config, _sz_settings -ErrorAction SilentlyContinue
    return
  }
} else {
  # Before Step 8 writes it: leave the variable unset and keep going.
  Write-Host 'senzing-env.ps1: config/engine_config.json not written yet, so SENZING_ENGINE_CONFIGURATION_JSON is not set; dot-source this script again after Step 8'
}

$env:SENZING_PROJECT_ROOT = $_sz_root
if ($null -ne $_sz_settings) {
  $env:SENZING_ENGINE_CONFIGURATION_JSON = $_sz_settings.Trim()
}
# Platform-specific settings go here, each as $env:NAME = '...' -- take them from
# sdk_guide(topic='install', platform='windows', language=...): its env_vars AND the
# gotchas[] entry for the chosen language in the SAME response, never from memory or
# from this file (INV-080). Do not set what that response says the install already
# sets. Never use setx, which writes the user's global environment (INV-199).
Remove-Variable -Name _sz_root, _sz_progress, _sz_config, _sz_settings -ErrorAction SilentlyContinue
```

What the snippet carries, and why (INV-175's rules for a sourced script, in PowerShell). The script is
unverified on Windows PowerShell 5.1 here, and so is each rule below (INV-163):
- **Dot-sourced, or nothing.** Run as `.\src\scripts\senzing-env.ps1`, without the leading `. `, it
  prints the dot-sourced command, sets nothing and returns, so every window loads it the one way
  every site gives.
- **`return`, never `exit` (INV-175).** A dot-sourced script runs in the Bootcamper's own session, and
  `return` ends the script while leaving that session as it was. INV-175 forbids `exit` in a sourced
  script. What `exit` does there is not the reason: under `pwsh` 7 a dot-sourced `exit` was measured
  ending only the script, and under Windows PowerShell 5.1 it is unverified here.
- **The root guard and the settings rule are the `.sh`'s (INV-175).** It checks the resolved root for
  `config/bootcamp_progress.json` and names the path it computed on failure, setting nothing. While
  `config/engine_config.json` is absent it prints the one-line notice, leaves
  `SENZING_ENGINE_CONFIGURATION_JSON` unset, sets the rest and returns normally; Step 8 dot-sources it
  again. It refuses an empty configuration and sets nothing.
- **Explicit UTF-8 in, ASCII only in the script (INV-166).** It reads the configuration with
  `-Encoding utf8`. Write the script itself through your file tools, UTF-8 with no BOM and ASCII only:
  Windows PowerShell 5.1 reads a `.ps1` that has no BOM in the ANSI codepage, so any other character
  in it would be misread.
- **The variable set comes from `sdk_guide` (INV-080).** On `sdk_guide(topic='install',
  platform='windows', language=…)` (server 1.37.19, 2026-10-04), `env_vars` says the Scoop install
  sets `SENZING_DIR` and puts `er\lib` on `PATH` itself, and the language's `gotchas[]` entry names
  what that language adds; for Java it is the SDK jar on `$env:CLASSPATH`. Read them again at run
  time rather than from this paragraph.

**When PowerShell refuses to run the script.** The Windows client's default execution policy refuses
scripts. The Scoop install that `sdk_guide` gives sets `RemoteSigned` for the current user, but an
install made another way may never have run it. When dot-sourcing fails with "running scripts is
disabled on this system", tell the Bootcamper to run `Set-ExecutionPolicy -Scope Process Bypass` and
then dot-source `. .\src\scripts\senzing-env.ps1` again. It lasts only for that PowerShell window and
changes no global configuration (INV-199). This fallback is unverified on Windows PowerShell 5.1
here (INV-163).

### The launch environment (JVM languages, and macOS generally)

Installing the SDK is not the same as being able to **launch** against it. These are
launch-environment problems, **not** Senzing misconfigurations — say so when one appears, so the
bootcamper does not go hunting through their engine config for a fault that is not there. Each
presents as an error far from its cause.

⛔ **Confirm the specifics for the bootcamper's platform via
`sdk_guide(topic='install', platform='<platform>', language='<language>')` — from the server,
not from this file** (a sourcing floor) — the
library path, the jar path, and the platform gotchas come from MCP, never from memory or from this
file (INV-080). What follows is the shape of the problem, not a substitute for that lookup.

**macOS + a JVM language (a first-class combination here: `macos_arm` plus Java or C#).**

- **The native library is found through the shell environment, not a JVM flag.** Per the MCP
  install guidance for `macos_arm`, `DYLD_LIBRARY_PATH` must be set **at the shell level before the
  JVM starts**, and `-Djava.library.path` **alone is insufficient**. This is the opposite of the
  natural guess — that a JVM flag can fix a JVM library-path error — which is what makes it cost
  time. A process cannot repair its own dynamic-linker search path after it has started, so the
  variable has to be in the environment of the shell that launches `java`.
- **That is why `senzing-env.sh` must be sourced in the same shell that launches the JVM** — not
  merely created. Because the global shell config is off-limits (the rule above), a **project-local
  launcher script** that sources the env script and then executes `java` in one step is the reliable
  pattern: it keeps "set the environment" and "start the JVM" inseparable, which is precisely what
  the requirement demands. Generate one and use it for every subsequent JVM invocation.
- **Do not pass flags through an unquoted variable.** `java $SENZING_JAVA_OPTS` does not word-split
  in zsh (macOS's default shell), so multiple flags arrive as a single argument. Write the flags
  explicitly in the launcher script.
- **Classpath — and it is platform-specific, which the example does not look like.** The install
  guidance's example is the **`macos_arm` response's**, quoted from its Java `gotchas[]` entry:
  `java -cp "${SENZING_ROOT}/sdk/java/sz-sdk.jar:myapp.jar" MyApp`
  (`sdk_guide(topic='install', platform='macos_arm', language='java')`, server **1.35.1**,
  re-confirmed 2026-08-31). Note the SDK **jar** lives under `sdk/java/`, while the **native**
  library lives under `lib/` — two different paths for two different things, and confusing them
  produces a class-not-found or a library-not-found error depending on which you get wrong.
  - ⛔ **(INV-283) Never carry `${SENZING_ROOT}` to Linux.** The macOS install sets it and nothing on
    `linux_apt` does; the server's own anti-pattern list names it for macOS and Windows only
    (*"SENZING_DIR on macOS → correct: SENZING_ROOT (macOS uses different env var than Windows)"*,
    same response). Applied verbatim on Linux it expands to `-cp "/sdk/java/sz-sdk.jar"`, every
    `com.senzing.sdk` import fails to compile, and the failure surfaces in **System verification**
    or later — one module away from the step that omitted the path, where it reads as a broken
    install rather than a wrong classpath.
    <!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='linux_apt', language='java') — carries no SENZING_ROOT, no jar path and no Java gotchas[] entry; env_vars holds only PYTHONPATH and LD_LIBRARY_PATH, and the response is identical to the same call with no language argument, so the parameter is inert on this platform — owner: sdk_guide(topic='install', platform='linux_apt', language='java') IS the route that would carry a Java jar path for Linux, asked directly and answered with neither the path nor a Java entry (absence negative) — server 1.36.0, 2026-09-02 -->
  - **On Linux the jar is at `/opt/senzing/er/sdk/java/sz-sdk.jar`** — ⚠️ **observation-only**
    (INV-080/INV-149), measured against `senzingsdk-runtime` **4.3.4-26210** on 2026-08-31, because
    **no MCP route serves a Java path for `linux_apt`**. Treat it as a starting point to verify on
    the bootcamper's machine, never as a server fact: `ls /opt/senzing/er/sdk/java/sz-sdk.jar`. If
    it is not there, derive it from the `default_paths` the `linux_apt` response *does* return
    (`resource_path` is `/opt/senzing/er/resources`, so the SDK root is `/opt/senzing/er`) rather
    than guessing, and say the path was derived.
  - **Confirm the native library path via `sdk_guide`** — that one the Linux route does answer
    (`LD_LIBRARY_PATH` → `/opt/senzing/er/lib`). It is only the **jar** that has no Linux route.
- **If you see `.dylib`/`.so` "not found" errors, do not symlink or copy Senzing libraries.** Per
  the MCP anti-patterns, Senzing tries both extensions and may report one even when the other works;
  the real cause is usually a missing dependency or an unset `DYLD_LIBRARY_PATH`. Re-run the
  `sdk_guide` install lookup and follow its gotchas for the installed version.

**MCP Java scaffolds may need a JSON library the install does not provide.** The authoritative Java
snippets from `generate_scaffold` (e.g. `loading/LoadWithInfoViaFutures.java`) `import javax.json.*`
and call `Json.createReader(...)` to parse records and `WITH_INFO` responses. `javax.json` (JSON-P)
is an external dependency: it is **not** part of the Java SE standard library, and the bootcamp
compiles with plain `javac` and never sets up Maven or Gradle. So:

1. **Verify before compiling, not after.** When a scaffold imports a package outside the standard
   library, check whether the environment actually provides it (inspect the install's jars) and
   resolve it *then* — rather than surfacing a raw `javac` import error the bootcamper has to
   diagnose. Verify per install; do not assume it is present or absent.
2. **State the safety asymmetry plainly when it comes up — this is the line that matters.**
   Replacing the **JSON library** is safe. Altering the **SDK calls** is not. Without that, a
   bootcamper facing an import error may "fix" it by rewriting the Senzing calls, which is exactly
   the failure `generate_scaffold` exists to prevent.
3. **Prefer a dependency-free JSON reader** for the bootcamp's own generated Java, so the code
   compiles under plain `javac`. Reuse one reader across modules rather than re-deriving it.
4. **Record the deviation in the source header** — what was substituted and why — so the take-home
   code shows where it departs from the authoritative scaffold. Never silently strip the import.

**`timeout` is not available on a stock macOS shell** (it is GNU coreutils; `gtimeout` exists only
if the user installed them). This is not Java-specific — it affects **any** command you wrap in a
timeout on macOS. Use a background process plus a polling loop with a deadline instead, or skip the
timeout. Check before relying on it rather than assuming a Linux userland.

**Other platforms.** On **Linux**, the equivalent variable is `LD_LIBRARY_PATH` and the same
"set it in the launching shell" rule applies — confirm the specifics via `sdk_guide`. ⛔ **(INV-283) For
Linux + a JVM language, `sdk_guide` answers the library half and not the classpath half** — see the
classpath bullet above: the jar path is an install-layout observation there, not a server fact, and
`${SENZING_ROOT}` must not be used to build it. ⚠️ **This is
not a JVM-only concern:** on `linux_apt` with **Python**, `LD_LIBRARY_PATH` is required too, and
`sdk_guide`'s `env_vars` hedges it while its language-specific `gotchas[]` entry does not — see
Step 3's Python note, which is where a non-JVM author will be. On
**Windows**, the DYLD/LD variables do not apply at all and the env script is `senzing-env.ps1`,
dot-sourced with `. .\src\scripts\senzing-env.ps1` (unverified on Windows PowerShell 5.1 here,
INV-163); the classpath separator is `;`, not `:`. The zsh word-splitting caveat is macOS/zsh-specific and the
`timeout` caveat is macOS-specific — **neither applies on Linux**, where both behave as expected.
Non-JVM languages need none of the JVM-specific items above.

**Checkpoint:** write step 3 to `config/bootcamp_progress.json`.

## Step 4: Verify Installation

⛔ **This step verifies the BINDING, not the engine.** What it can prove here is that the language
binding loads, the native library is found, and the SDK answers: the factory constructs and
`SzProduct.get_version()` returns a version. **Do not create an engine at this step.** An
engine-class call needs an engine configuration (Step 8) and a datastore holding a registered
default config (Steps 7 and 8a) — three to four steps away — so a script that initializes the engine
here **cannot succeed even on a perfectly healthy, current install**.

This module already says so at its own success indicator: *"an engine-class call
(`SzEngine`/`SzDiagnostic`) succeeds — a version query alone does not qualify (**Step 9**)"*. That is
**Step 9**'s bar, after the database and the seeded config exist. Step 4 must not duplicate it early.

**Record the version the SDK reported, because graduation reads it from here.** When
`SzProduct.get_version()` returns, write the `VERSION` value from its JSON into
`config/bootcamp_progress.json` as `sdk_version` (the value only, e.g. `4.4.1`, not
`BUILD_VERSION`, `BUILD_DATE` or the whole document), and record where it came from as
`sdk_version_measured_at: "module-02 step 4 (SzProduct.get_version)"`, following Step 5a's
`license_record_limit` pattern. The call is the chosen binding's product version method:
`get_version()` in Python and Rust, `getVersion()` in Java and TypeScript, `GetVersion()` in C#.
Its response documents `VERSION` as a top-level string beside `BUILD_VERSION`
(`get_sdk_reference(topic='response_schemas', filter='getVersion')`, server **1.37.13**,
2026-09-26). If a value was already recorded and this reading differs, replace it and say so,
naming both versions. This is the one place the installed version is recorded: graduation's recap
reads `sdk_version` and records "Unknown" when it is absent, because the Senzing MCP server is
remote and cannot report what is installed on this machine. (INV-329) So do not fill the field from the
package manager, `szBuildVersion.json` or the MCP server. A Step 1b update runs before this step,
so the reading here is already the post-update version. The version does not move when later
steps write configuration, so unlike `license_record_limit` its marker records provenance, not a
provisional reading.

⛔ **(INV-269) Report WHERE the binding resolved from, not only that it loaded — and print it beside the
version.** A version query answers through the **native library**, so it reports the *engine's*
version and says nothing about which language package was imported. Those are two different places:
the engine comes through the native library, the binding through the interpreter's own module search
path. **Agreement between them is the thing being verified**, so print both:

- the **engine** version, from the `workflow='information'` snippet below; and
- the **resolved binding path** — for Python, `python3 -c "import senzing; print(senzing.__file__)"`;
  for other languages, the equivalent "where did this module come from" probe for that runtime
  (the loaded jar's location for JVM languages, the assembly path for C#).

⛔ **A resolved path outside the SDK's own language directory means locally installed packages are
shadowing the shipped ones** — the exact failure **INV-222** exists to prevent, reached here by an
install that predates this bootcamp rather than by a `pip install` inside it. The remedy is Step 3's:
uninstall them, **or** prepend the SDK path to the language's module search path so the shipped
bindings win. Report which was done.

⛔ **(INV-269) Print the PATH, not a package-metadata version — the metadata reports the wrong package.**
It is tempting to print a binding *version* beside the engine version and compare numbers. Do not
substitute that for the path. Measured on the development machine 2026-08-26 (observation-only,
INV-080/INV-149 — no MCP route reports a language package's metadata layout): the SDK-shipped Python
binding exposes **no** `__version__`, `VERSION` or `version` attribute at all, and
`importlib.metadata.version("senzing")` returns **`4.1.2`** — the *PyPI distribution's* number —
**even when the module actually imported is the SDK-shipped one** under `/opt/senzing/er/sdk/python`,
because that directory ships no distribution metadata and the lookup falls through to
`site-packages`. A version comparison built on it therefore reports the shadowing package's version
while the correct module is loaded: the same silent skew this check exists to catch, wearing the
check's own uniform. **The resolved path is the signal that cannot lie.**

⚠️ **Why this check exists here and not only in Step 3.** A shadowed install produces a working
import *and* a plausible, current-looking version, so a step that merely reports success is exactly
what the defect hides behind (the fail-loudly reasoning INV-111 applies to generators). It is placed
at Step 4 because **Step 4 is on every path**: Step 1's existing-install route skips Step 2 and Step
3's install commands — which is where Step 3's own `senzing.__file__` detection lives — so a
bootcamper who already had the SDK installed would otherwise never run it. Reproduced on the
development machine 2026-08-26: with `PYTHONPATH` unset, `import senzing` resolved to
`~/.local/lib/python3.12/site-packages/senzing/__init__.py` while the SDK-shipped bindings sat
unreachable at `/opt/senzing/er/sdk/python`; with `PYTHONPATH` set, it resolved to the latter
(observation-only — interpreter module-resolution order, which no MCP route reports; INV-080/INV-149).

<!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='macos_arm', language='python') — returns no install_commands, no env_vars and no gotchas at all, only compatibility_notes stating the Python SDK is Linux-only and offering Java/C# (official) or Docker/WSL2 instead, so there is no macOS PYTHONPATH counterpart to export — owner: sdk_guide(topic='install', platform=<that platform>, language='python') IS the route that would carry a per-platform Python variable set, and it answers by declining the platform rather than by omitting a variable (absence negative) — server 1.36.0, 2026-09-02 -->
⚠️ **Do not invent a counterpart where the server says there is none.** `PYTHONPATH` is a
Linux-only concern because the Python SDK itself is: *"The Senzing Python SDK is ONLY supported on
Linux. It is NOT supported on macOS or Windows"* (`sdk_guide(topic='install', platform='macos_arm',
language='python')` → `compatibility_notes`, server 1.33.0, 2026-08-26). So this check has no
macOS/Windows Python form to add, and the `DYLD_LIBRARY_PATH` and Windows env-script guidance stays
exactly as it is.

⚠️ **What it looks like when the engine is attempted here** (measured live on a healthy install,
Senzing 4.3.4 build 4.3.4.26210, 2026-08-14): `SzProduct.get_version()` returns `4.3.4` **and** the
engine call fails with

```text
SzBadInputError - SENZ7426|Transliteration failed: No transliteration rules found!
Transliteration requires at least one module.
```

⛔ **`SENZ7426` and `SENZ7220` before Step 7 mean "not configured yet" — they are the EXPECTED
result, not a defect.** Do **not** send them through this module's `explain_error_code` → pitfalls
path here. Both that tool and `sdk_guide(topic='install', platform='macos_arm' | 'windows')` document
a **real** `SENZ7426` cause — a wrong `SUPPORTPATH` on those platforms — and Step 8 covers it
properly, with its conditions and its provenance. That is the right diagnosis *after* the
configuration steps have run, and the wrong one here: at Step 4 there is no engine configuration yet
by design, so the same code means only that Steps 7–8a are still ahead. Reading it as a path fault
sends a bootcamper with a healthy install hunting something that does not exist. If you see either
code before Step 7, continue to Step 5.

So Step 4 needs **one** `generate_scaffold` call:

- `generate_scaffold(language='<chosen_language>', workflow='information', version='current')` —
  the **version-print** half, which is what this step runs. This is where the version snippet lives
  (for Python, `information/get_version.py`, which calls `SzProduct.get_version()`).

The `workflow='initialize'` call is still needed — at **Step 8a** (its `configuration/` snippets seed
the default config) and **Step 9** (its factory-lifecycle snippets make the engine call), which is
where both already cite it. Nothing is lost by dropping it here; it was simply four steps early. The
two-workflow fact below is why it cannot be the source for a version check, and it stays recorded at
this step because this is where a reader would otherwise reach for it.

⛔ **`workflow='initialize'` alone cannot satisfy a version check.** Verified live on server 1.32.9,
2026-08-12 (re-confirmed 2026-08-14), for **Python and Java**: its snippets are factory/engine **lifecycle** plus
configuration helpers — abstract-factory / environment variants, engine priming, repository purge,
factory destroy, signal handling, and the `configuration/` entries that seed a default config and
register data sources — and **none of them prints the version**. That **absence** is the
load-bearing fact. The version snippet lives only under `workflow='information'`
(for Python, `information/get_version.py`), re-confirmed on the same server and date.

⛔ **Do not restate this as a snippet count or a single directory.** The inventory varies on two
axes at once: it has **widened over time** (Python gained the `configuration/` entries between
1.32.2 and 1.32.9), and it **differs per language** in count and in path (on 1.32.9, Python returns
snippets under `python/initialization/` and `python/configuration/`, Java a smaller set under
`java/snippets/…`). A count is therefore wrong somewhere the moment it is written, while the
conclusion above stays true — which is exactly how a correct ⛔ comes to look discredited by its own
evidence. Citing it alone leaves
the guide to invent the missing half from memory, which is exactly the training-data fallback
INV-080 forbids. (Step 8a already carries this warning for a different need, and Step 9 cites
`workflow='initialize'` correctly for its own — the lesson generalizes: **check what a workflow's
snippets actually contain before citing it for a specific need.**)

⛔ **`generate_scaffold` returns a **listing**, not code — you must fetch each file.** Its response
carries `file_path`, `source_url`, `raw_url`, `size_bytes` and `line_count` per snippet and **no
source text**, so there is nothing to "save" until you fetch it: follow the response's own
`access_steps` step 1 and fetch each `raw_url`
(`raw.githubusercontent.com/senzing/code-snippets-v4/...`), or clone the repo per step 2 if the
fetch is blocked. If both fail, take the terminal step in `../bootcamp-onboarding/ground-rules.md`
→ "Once `raw_url` and `git clone` have both failed" (INV-160). This differs from `sdk_guide`, which
does inline a `code.code` string — do not carry that expectation across.

⛔ **Never pass `inline=true` to `generate_scaffold`.** Its own `access_steps` step 3 advertises
that parameter as a "last resort", but the tool's **declared schema has no `inline` parameter at
all** — only `language`, `version` and `workflow` (both confirmed live, server 1.32.9,
2026-08-13).
<!-- MCP-NEGATIVE: generate_scaffold's declared schema — carries no inline parameter, only language, version and workflow, while the response's own access_steps step 3 advertises the undeclared inline=true — owner: the tool's declared schema as the server advertises it is the authority on what it accepts, and it was read directly rather than inferred from the response prose (routing negative — the schema is the route, the prose is not) — server 1.36.0, 2026-09-02 --> Passing it is not a fallback, it is a call that cannot work, and it teaches nothing
about why. This is INV-160's rule applied to a sibling tool: **an undeclared parameter MUST NOT be
adopted as the remedy even when the response's own prose advertises one.** Fetch the `raw_url`
instead — that path is confirmed working.

If verification fails, use `explain_error_code` for any SENZ error codes and `search_docs` for
troubleshooting.

**Checkpoint:** write step 4 to `config/bootcamp_progress.json`, together with `sdk_version` and
`sdk_version_measured_at` from the version reading above.

## Step 5: License (record capacity)

> **Internal note:** this step does NOT prompt for a License Key. The single, volume-gated
> Senzing License Key prompt is presented once, at the start of Data collection (Module 4),
> per INV-093. SDK setup **measures** the active license's record capacity and records it;
> the "License Key" reference notes below are kept for context.

> **License check order:** project-local `licenses/g2.lic` → the `SENZING_LICENSE_FILE` path → system
> CONFIGPATH → the built-in evaluation license.
>
> <!-- MCP-NEGATIVE: search_docs and sdk_guide(topic='install'|'configure') — neither names a license environment variable; exactly one route returns it — owner: sdk_guide(topic='load', language='python', record_count=1000) compatibility_notes name it verbatim, "place the license file at the path specified by SENZING_LICENSE_FILE or in the etc/ directory", re-asked and confirmed (routing negative — the name exists, go there) — server 1.36.0, 2026-09-02 -->
> ⛔ **The license environment variable is `SENZING_LICENSE_FILE`, and only ONE tool route returns
> it — do not go looking for it anywhere else.** (INV-208) It appears in the `compatibility_notes` of
> `sdk_guide(topic='load', language=…, record_count=<above the default limit>)`, which says a
> bootcamper with a license should "place the license file at the path specified by
> `SENZING_LICENSE_FILE` or in the `etc/` directory". Verified on server **1.32.9, 2026-08-13**, for
> `language='python', record_count=1000` and `language='java', record_count=600` — the note is
> language-independent and appears only when the count exceeds the limit.
>
> ⛔ **`SENZING_LICENSE_PATH` is a confabulation — never use that spelling.** No tool returns it, and
> it shipped in graduation's `.env.example` for a time. Wrong environment-variable names are on the
> MCP server's own `common_confabulations` list, so the spelling matters more than it looks.
>
> ⚠️ **Do not conclude from the wrong route that the variable does not exist.** The topics you would
> naturally try return nothing: `sdk_guide(topic='configure', language='python',
> platform='linux_apt')` returns exactly two env vars (`LD_LIBRARY_PATH`, `PYTHONPATH`),
> `sdk_guide(topic='install', platform='macos_arm')` shows license only as the `PIPELINE` keys
> `LICENSEFILE`/`LICENSESTRINGBASE64`, and `search_docs` returns no variable name at all (all three
> re-checked on 1.32.9, 2026-08-13). An earlier pass took that silence as proof of absence and wrote
> "there is no license-path environment variable" into this note — the INV-194 failure mode: one
> tool's empty field is not evidence the server lacks the fact. Ask the tool that owns it.
>
> A `PIPELINE` license key remains the other supported route — `LICENSEFILE` for a `.lic` path,
> `LICENSESTRINGBASE64` for an inline Base64 key — which is what Module 4 Step 8a wires.
> The record capacity **is** looked up, not written here (INV-080) — see below.

> **"Senzing License Key" vs. the EULA:** the **Senzing License Key** configured in this step is a
> *runtime-capacity* license (it sets how many records Senzing will resolve) — supplied as a `.lic`
> file or a Base64-encoded key, or the built-in evaluation license by default. It is distinct from
> the **Senzing End User License Agreement (EULA)** accepted during SDK install in Step 3. When
> this step says "License Key", it means the runtime license, never the EULA.

### 5a. Measure the active license's record limit (no prompt)

⛔ **(INV-244) Measure the license here — never infer it from what the state file does or does not
say.** This is the first step where the measurement is possible: Step 3 wrote the env script that
supplies the settings and Step 4 has just verified the SDK works, so the capacity the bootcamper is
told is a reading of **their** machine rather than an assumption about it. Take the reading **before**
branching on anything recorded, and let it govern everything below (INV-012).

⛔ **(INV-295) This reading is PROVISIONAL, and Step 8a re-takes it — `get_license()` resolves the license
from the settings it is handed, and the settings here do not yet carry `CONFIGPATH`.** The check
order above has four tiers, and the third is *system CONFIGPATH* — a `PIPELINE` key that **Step 8**
writes, three steps after this one. So a reading taken here can only ever return one of the first
two tiers or the built-in default: it cannot see a license installed at the system config path, and
on a machine that has one it reports the built-in figure with no indication anything was missed.
Measured on **Senzing SDK 4.4.0** (build `4.4.0.26242`), 2026-09-01, on a machine carrying a license
at `/etc/opt/senzing`: `{"PIPELINE": {}}` returns `recordLimit: 500`, while the same call with
`CONFIGPATH` in force returns `recordLimit: 0` — no cap. Which tier wins for a given settings string
is engine behavior no MCP route reports, so this stays **observation-only** with its version and date
(INV-080/INV-149).

**A reading is only complete once the engine configuration is**, which is why Step 8a re-measures and
why sub-step 3's replace-and-say-both-numbers rule below is reachable at all. Take this reading
anyway — it is the right conservative figure until Step 8 exists, and its "cannot measure yet" branch
still applies — but record it as provisional, per sub-step 3.

1. **Take the reading.** `SzProduct`'s license method takes no arguments and returns the active
   license as a JSON string — `getLicense()` in Java and TypeScript, `get_license()` in Python and
   Rust, `GetLicense()` in C# (`get_sdk_reference(topic='parameters', filter='getLicense')`, server
   **1.35.1**, 2026-08-31). The snippet ships in the **same** scaffold Step 4 already fetched:
   `generate_scaffold(language='<chosen_language>', workflow='information')` returns `GetLicense`
   beside the `GetVersion` this module ran one step ago (confirmed for Java on server **1.35.1**,
   2026-08-31 — `java/snippets/information/GetLicense.java`). Fetch its `raw_url` like any other
   scaffold snippet; the response is a listing, not source.
   - ⚠️ **No engine configuration is needed, and its absence is not a failure.** `SzProduct` needs no
     support data, which is exactly why Step 4's version call succeeds here while engine calls still
     raise `SENZ7426` with Steps 7–8a still ahead. If the license call itself raises `SENZ7426` or
     `SENZ7220`, treat it as the "cannot measure yet" branch below, not as a broken install.
   - Save the returned JSON to `config/license.json`, because later steps read it.
     `get_sdk_reference(topic='response_schemas', filter='get_license')` documents `recordLimit`
     (integer) (MCP server 1.37.14, 2026-09-28), so that is the field to parse. An empty or shallow
     result from that lookup is coverage, not a failed call: do not retry it (INV-149). **Only if
     `recordLimit` is absent from the saved file, read the file to find the name the field actually
     carries before parsing it** (INV-115).
   - Parse `recordLimit`: `0` means **no record cap (unlimited)**; a positive value is the cap.

2. **State what was measured** — as a statement, **not a question:** "Your Senzing license allows up
   to N records," or "Your Senzing license has **no record cap (unlimited)**" when `recordLimit` is
   `0`. Name it as a reading of the installed license, so it is not mistaken for a published default.

3. **Persist it.** **Write the measured value into `config/bootcamp_progress.json`** as
   `license_record_limit`, and **record when it was taken** as
   `license_record_limit_measured_at: "module-02 step 5a (provisional — engine configuration not yet
   written)"`. If a value was already recorded and the measurement disagrees with it,
   replace the recorded one and **say the recorded figure was withdrawn** — naming both numbers.

   ⛔ **(INV-295) The `_measured_at` marker is not bookkeeping — it is what lets a later step tell a complete
   reading from an incomplete one.** Both are genuine measurements, so the figure alone cannot
   distinguish them, and every downstream reader treats a present value as authoritative *because* it
   was measured. Module 4's Step 8a reads this marker for exactly that reason. Write it on every path
   that writes the field, here and at Step 8a.
   Do not re-ask anything (INV-006).
   - ⛔ **(INV-278) Presence is not proof of detection, which is why the reading comes first.** A
     figure already in the file is not evidence that anyone measured it — on 2026-08-25 a value
     written from a Bootcamper's statement (100,000) sat in this field against an install whose
     real limit was **500**. Measuring before reading it is what makes that unfalsifiable state
     impossible here, rather than merely discouraged.

⛔ **(INV-278) Persisting it is the point, not a detail.** Module 4's Step 8a reads this field and
**volume-skips** its License-Key gate when the collected total is at or below the recorded limit, so
a measurement that stays on screen leaves that gate driven by a figure nobody measured — which is the
defect this step exists to close, not a smaller version of it. ⚠️ **A correction that makes the
reported capacity smaller is the one worth stating out loud**, because anything already sized against
the larger figure — a generated scenario, a collection plan — was sized against a ceiling that does
not exist.

⛔ **(INV-244, INV-278) Write this field ONLY from the reading taken here, and never from an
assumption.** That is the whole contract: the field's authority rests on being measured, so a value
that was stated, remembered, defaulted, or inferred from the absence of another value must never
reach it. ⛔ **When the measurement cannot run, write nothing** — leave the field absent and take the
branch below. An absent `license_record_limit` therefore means *no measurement has been taken yet*,
which is what every step reading it relies on; a written one means this step, or Module 4's Step 8a,
actually measured.

**Only if the measurement genuinely cannot run** — the SDK call fails, the language's scaffold cannot
be fetched, or the settings are not yet usable — say what could not be determined, and:

- **If a value was already recorded**, present it as **recorded, not verified** — never as detected —
  and say the check could not be run this session. Leave it in place; it is the best figure available
  and replacing it with an assumption would be strictly worse.
- **Otherwise**, present the built-in evaluation figure **as an assumption**, naming what could not be
  determined:

⛔ **Fill `{record limit}` below from the MCP server before presenting this — the figure is not
written into this skill on purpose.** The route that answers it is `sdk_guide` with a
`record_count` above the default limit, whose `compatibility_notes` name the limit outright:

```text
sdk_guide(topic='load', language='<chosen_language>', platform='<user_platform>', record_count=1000)
```

<!-- MCP-NEGATIVE: search_docs(query='evaluation license record limit how many records without a license') — the top-ranked hits are EULA grant-of-license prose ("solely for up to the number of DSRs designated therein") that states no figure; the figure appears only in a lower-ranked FAQ ("limited to 500 Distinct Source Records (DSRs)"), so a guide reading the top hit comes away without it — owner: sdk_guide(topic='load', record_count=<above the limit>) states the figure in a fixed field, compatibility_notes, "exceeds the default Senzing license limit of 500", and explain_error_code('SENZ9000') calls it the default 500-DSR free tier; both re-asked (routing negative — the figure exists, go there) — server 1.37.13, 2026-09-24 -->
The tool is named here, rather than left as "a Senzing MCP tool", because `sdk_guide` states the
figure in a fixed field, `compatibility_notes`. `search_docs` ranks its results instead: asked for
the evaluation license's record limit, its top-ranked hits are EULA grant-of-license prose that
states no figure, and the figure sits in a lower-ranked FAQ, so a guide reading the top hit comes
away without it. Present exactly what the server returns (waiting up to 30 seconds). If it
returns no figure, drop the parenthetical entirely and say the current limit is unavailable from
the MCP server. Never substitute a hardcoded or remembered figure — the published
capacity has changed before, and a stale number here is a Senzing fact asserted from memory
(INV-080), in the one place the bootcamper is most likely to plan against it.

"I couldn't read your license from the SDK just now, so this is the **assumption** rather than a
measurement: Senzing uses a **built-in evaluation license** automatically when no custom license is
present (limited to {record limit} records) — no license file needed. What I could not determine is
whether a custom license is installed on this machine, and what its record limit is. That's enough
for the demo modules that come next (System verification and Truth Set visualization), which run on
small synthetic and Truth Set data. If your **own** data later exceeds the evaluation limit, we'll
set up a Senzing License Key in the Data collection module, where your data volume is known. Nothing
to do here."

> **Where the License Key is handled now:** the interactive License-Key **setup** (asking whether the
> bootcamper has a key, decoding/placing a `.lic` or Base64 key, wiring `LICENSEFILE`, and requesting
> an evaluation license via the MCP server or Senzing support) is the single, volume-gated gate at the
> start of Data collection (Module 4, Step 8a), per INV-093. SDK setup does not perform it. ⚠️ **Reading
> the installed license is not setting one up** — this step measures the capacity that is already
> there, which needs no prompt and no volume, and Module 4's gate is what asks for a key when the
> collected volume actually exceeds it.

**Checkpoint:** write step 5 to `config/bootcamp_progress.json`.

## Step 6: Create Project Directory Structure

Create the organized project layout that all subsequent modules use, following the file
placement layout in `../bootcamp-onboarding/ground-rules.md` (`src/`, `src/scripts/`, `data/`,
`database/`, `docs/`, `config/`, `licenses/`, `src/resources/`, `data/mapping/`, `data/temp/`).
(The full Kiro agent-instructions directory-creation script is a later porting phase; create
the layout directly per the ground-rules placement rules for now.)

After creation, inform the user: "I've set up the project directory structure. All files will
be organized properly throughout the bootcamp."

**Checkpoint:** write step 6 to `config/bootcamp_progress.json`.

## Step 7: Configure Database

Ask: 👉 **Which database would you like to use? Reply with a number:**

1. **SQLite** — recommended for learning and evaluation.
2. **PostgreSQL** — better for production; can run in a Docker container (recommended when Docker is available), a local install, or an existing server.

*(Internal: end the turn on this question and wait.)*

**Once the Bootcamper answers, before either branch below.** Both instructions sit here, ahead of
the branches, because every path through this step passes this point; an instruction placed after
the last branch is skipped by a guide that follows the other one.

1. ⛔ **Record the choice where later modules read it.** Write the engine chosen to
   `config/bootcamp_preferences.yaml` under the key **`database_type`**, with the value **`sqlite`**
   or **`postgresql`** (lowercase, exactly these two spellings). Set the key, replacing any earlier
   value — when Step 7 runs again, on a resume or a changed mind, never add a second entry:

   ```yaml
   database_type: sqlite   # or: postgresql
   ```

   This is the **only** step in the bootcamp that knows which engine was chosen. These read
   `database_type` from that file by name, and each handles an absent key with a fallback of its
   own:

   - **Module 4** (`../module-04-data-collection/SKILL.md`) **Step 8b**, the SQLite load-time
     warning — notes the defect and falls back to the engine recorded in
     `config/bootcamp_progress.json`.
   - **Module 6** (`../module-06-data-processing/phaseA-build-loading.md`) **§3**, the loader's
     worker count — treats the engine as SQLite and serializes the writes, which on PostgreSQL is
     merely slower.
   - **Module 6**, the same file's **SQLite volume pre-load check** — falls back to
     `config/bootcamp_progress.json` and notes the gap.
   - **Graduation** (`../graduation/SKILL.md`) **`## Pre-checks`** — notes the defect and carries
     on with the value indeterminate; **Step 3**'s production configuration files take the value
     from there.
   - **`../graduation/database-backup.md`** — determines the engine from
     `config/engine_config.json`'s connection string.

   A fallback is a guess about what this write would have said, and a wrong guess hands a
   PostgreSQL Bootcamper a serialized loader and SQLite warnings with no reason given. Do not
   record the choice only in `config/bootcamp_progress.json`: the readers look there only after
   this key is missing, and a different key name is the same failure as no key at all.

2. **Checkpoint:** write step 7 to `config/bootcamp_progress.json` **when the chosen branch's
   setup is finished, before Step 8** — not now. A checkpoint written as Step 7 starts marks the
   step done before the database exists, and a resume would skip the setup; until it is written,
   a resumed session runs Step 7 again.

**For SQLite** (recommended for bootcamp):

⛔ **Before creating it, check whether the project sits on a mounted host filesystem — measure the
datastore, do not assume it.** The datastore always goes in the project directory
(`database/G2C.db`, INV-200), which is right on every platform except one: when the SDK runs in a
Linux environment while the project lives on the host's filesystem, the database is reached over a
translation layer instead of a native one. The signature cases are **WSL2 with the project under
`/mnt/`** and a Docker bind mount. Nothing fails; it is simply one to two orders of magnitude
slower, and a Bootcamper has no reason to suspect storage.

1. **Detect the crossing.** WSL2 with the project path under `/mnt/` is the case to look for; the
   Docker path has the equivalent via its bind mount. Say plainly what it means before the datastore
   is created, not after the load is slow.
2. **Measure it rather than asserting it.** Senzing's own instrument answers this in seconds:
   `check_repository_performance` on `SzDiagnostic` reports an insert rate. Take the call and its
   argument from the server at the point of use rather than from this file (INV-080) — it is a
   diagnostic-hub call, not an engine one. Report the number to the Bootcamper. **Non-blocking:** if
   it cannot run, say so in one line and continue (INV-048); an unavailable measurement is not a
   reason to stall setup.
3. **Senzing owns the reason, so relay it rather than re-deriving it.**
   `search_docs(query='loading', category='anti_patterns')` returns *"Do Not Use Low-IOPS Storage"* —
   *"Senzing entity resolution is I/O intensive … Avoid network-attached storage (NAS/NFS) for the
   database data directory … Run `check_repository_performance()` to validate your storage meets
   requirements"* — and *"Do Not Skip check_repository_performance() Before Production"*, which says
   to run it **before** a large load (re-verified server **1.37.19**, docs index 2026-10-02 18:46
   UTC, **2026-10-02**). The second is in the top hit, *Senzing Anti-Patterns: Configuration and
   Initialization*; the first is in the next, *Architecture and Performance*, so read past the
   first hit. A mount crossed by a translation layer is that case.

⚠️ **Observation-only, one workstation, recorded with its conditions rather than asserted as a rule:**
on Windows 11 + WSL2 Ubuntu with Senzing SDK 4.3.4 and SQLite, `check_repository_performance(5)`
reported **1,112** inserts on `/mnt/c/...` against **326,606** on a WSL-native path, and end-to-end
load throughput moved from **3 records/second** to **138–180** — about 7.5 hours down to about 9
minutes for 83,338 records, same code, same data, same machine (2026-08-18). Treat the shape as
indicative and the number as this one machine's; the measurement in rung 2 is what speaks for the
Bootcamper's.

⛔ **Do not relocate the datastore out of the project directory on your own initiative.** INV-200
exists because files appearing where the Bootcamper did not put them is its own defect, and the
trade-off is real: a datastore outside the project is not alongside their other artifacts and is not
picked up by copying the project folder. Report the measurement and let them decide; the default
stays `database/G2C.db`.

⛔ **SQLite is not "no setup". The database file is not auto-created and its schema is not
auto-applied** — the same as PostgreSQL, and for the same reason. Skipping the schema does not fail
here; it fails at Step 9 with `SENZ1001|Critical Database Error '(14:unable to open database file)'`,
which reads as a path or permissions fault. There are **three rungs**, and only the third is
Step 8a's:

1. **Create the database directory:** `mkdir -p database` (Linux/macOS) or
   `New-Item -ItemType Directory -Force -Path database` (PowerShell).
2. **Apply the Senzing schema** to `database/G2C.db`. Get the schema file's path from
   `sdk_guide(topic='install', platform='<platform>')` rather than hardcoding it (INV-080) — it is
   returned in `install.platform.post_install[]`, and `install.engine_config_notes[]` states the
   requirement in words: the DB file is **not** auto-created, and the schema step is **required**
   when using `senzingsdk-setup`, which is what this module installs. (Re-verified live, MCP server
   1.32.9, 2026-08-14. The `senzingsdk-poc` package's `sz_create_project` would do all three rungs
   automatically — that is not what the bootcamp installs.)

   ⛔ **Apply it with Python, not the `sqlite3` CLI.** Windows is a supported platform (INV-001) and
   ships no `sqlite3` binary; Python 3 is already a hard bootcamp prerequisite, and its stdlib
   `sqlite3` module runs the same DDL identically on all three platforms:

   ```bash
   python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.executescript(open(sys.argv[2]).read()); c.commit(); c.close()" \
     database/G2C.db "<schema path from sdk_guide>"
   ```

   The server returns the CLI form (`sqlite3 <db> < <schema>.sql`) — treat that as the illustration
   of *what* to apply, not as the command to run.
3. **Seed the Senzing configuration** — that is Step 8a, below. Do not attempt it here.

⛔ **The `SQL.CONNECTION` path must be ABSOLUTE.** Written relative, the engine cannot open the
database **from any working directory, including the project root** — it fails with the same
`SENZ1001 (14: unable to open database file)`, so this is not something a `cd` fixes. The reason is
visible in the engine's own SQLite log: given `sqlite3://na:na@database/G2C.db` it tries to open
**`/G2C.db`** — the relative prefix is not resolved against the working directory, it is discarded
(observed on Senzing 4.3.4, 2026-08-14). Use the
absolute resolution of the project's `database/G2C.db`, with the `/` immediately after `@`:

```text
sqlite3://na:na@/absolute/path/to/<project>/database/G2C.db
```

This is INV-200-compatible, not in tension with it: the file still lives **inside the project** at
`database/G2C.db`; it is the connection *string* that carries that path's absolute form.

- **IMPORTANT:** Never use `/tmp/` or in-memory databases. If `generate_scaffold`,
  `ExampleEnvironment` or `sdk_guide` defaults to `/tmp/` (the server's own example path is
  `/tmp/sqlite/G2C.db`), override the path to `database/G2C.db` — **including in the schema command
  above**, not only in the connection string.

**How to tell where you are:** after rung 2, `create_engine()` still fails — with
`SENZ7220|No engine configuration registered in datastore`. That is the expected state and exactly
what Step 8a closes. `SENZ1001 (14: unable to open database file)` means rung 2 has **not** been
done; do not diagnose it as a permissions or path problem.

**For PostgreSQL** (production): first choose HOW to run it. Detect Docker availability
(`docker version`); when Docker is present, offer the container option **first and recommended** —
a real, production-style PostgreSQL with no system-wide install or admin rights, easy to tear down.
Pin this 👉 question verbatim (neutral lead + numbered list, INV-051/INV-056):

👉 **How would you like to run PostgreSQL? Reply with a number:**

1. **In a Docker container** — recommended when Docker is available; self-contained and production-style.
2. **Install PostgreSQL locally.**
3. **Use an existing PostgreSQL server.**
4. **Switch to SQLite** (the bootcamp default).

*(Internal: end the turn on this question and wait.)* When Docker is not available, omit option 1
and say so.

**MCP-first (INV-080):** confirm the current PostgreSQL connection-URL format, the schema-DDL path,
and the engine-config wiring from the Senzing MCP server at runtime — do not treat the values below
as authoritative. Use `search_docs(query='Senzing engine configuration PostgreSQL connection')`,
whose top hit is the *Senzing Engine Configuration* page's introduction: read past the first hit
to the same page's "Section: SQL > CONNECTION", which carries the PostgreSQL connection-URL
format. Use `search_docs(query='PostgreSQL schema DDL initialization', category='anti_patterns')`,
whose top hit is *Senzing Anti-Patterns: Database Initialization and Container Setup* → "PostgreSQL
Schema Is NOT Auto-Created by the SDK", with the schema-DDL path per platform. Generate the engine
config with `sdk_guide(topic='configure', ...)` — never hand-construct
`SENZING_ENGINE_CONFIGURATION_JSON`.

**Option 1 — PostgreSQL in a Docker container:**

1. Generate a strong, project-specific database password **once** — it is baked into the
   project-local volume on first initialization, so reuse the same value everywhere below and
   never regenerate it on a later restart:

   ```bash
   python3 -c "import secrets; print(secrets.token_hex(16))"
   ```

   Then run an official `postgres` image with a stable `--name`, a **project-local volume** (data
   persists in the working directory, not an ephemeral layer), the generated password (never the
   guessable default `senzing`), and the port **bound to localhost only** (`127.0.0.1:`, so the
   database is not exposed on other network interfaces):

   ```bash
   docker run -d --name bootcamp-postgres \
     -e POSTGRES_USER=senzing -e POSTGRES_PASSWORD=<generated-password> -e POSTGRES_DB=G2 \
     -p 127.0.0.1:5432:5432 -v "$(pwd)/database/postgres:/var/lib/postgresql/data" postgres:16
   ```

   On a later resume, restart the existing container with `docker start bootcamp-postgres` (which
   preserves the baked-in password) rather than a fresh `docker run`.

2. Record the container for lifecycle tracking (INV-101): append it to `docker_containers` in
   `config/bootcamp_progress.json` — at least its `name` and the `runtime` you actually used
   (`docker`, or `podman` / `container` if that is what started it) — so the sessionEnd hook
   stops it on exit and sessionStart offers to restart it.
3. Wait until the server is ready (poll `docker exec bootcamp-postgres pg_isready`).
4. Apply the Senzing PostgreSQL schema DDL **before any SDK use** — the SDK does NOT auto-create it
   (unlike SQLite). MCP confirms the DDL ships with the SDK install at
   `/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql`; apply it against the
   container:

   ```bash
   docker exec -i bootcamp-postgres psql -U senzing -d G2 \
     < /opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql
   ```

   Re-confirm the exact path via MCP; the Windows/macOS SDK install path differs (see the
   initialization anti-patterns doc).
5. Wire the connection into the engine config (Step 8): the `SQL.CONNECTION` URL is
   `postgresql://user:password@host:port/database` (MCP-confirmed), where `password` is the
   generated value from Step 1 (not the old `senzing` default). Generate the full engine config
   via `sdk_guide(topic='configure', ...)` and save it to `config/engine_config.json`.

**Option 2 — Install PostgreSQL locally:** install and start a local PostgreSQL server, create the
Senzing database, apply the schema DDL as above (`psql -f .../szcore-schema-postgresql-create.sql`),
then wire the `postgresql://` connection via `sdk_guide(topic='configure', ...)`.

**Option 3 — Use an existing PostgreSQL server:** obtain the host/port/database/credentials, apply
the schema DDL to that database, and wire the `postgresql://` connection as above. Managed cloud
PostgreSQL typically requires SSL (`PGSSLMODE=require`) — confirm via MCP.

**Option 4 — Switch to SQLite:** first rewrite `database_type` to `sqlite` by applying
instruction 1 at the head of this step again (it replaces the `postgresql` value written there),
then proceed with the SQLite setup above.

SQLite remains the default recommendation for pure evaluation; PostgreSQL (especially via Docker)
is the production-style path. INV-037 is satisfied by any of these paths.

## Step 8: Create Engine Configuration

**🚨 NEVER guess the engine-configuration VALUES.** `CONFIGPATH`, `RESOURCEPATH`, `SUPPORTPATH` and
the connection-string form all come from
`sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>', version='current')`
— never from directory patterns or memory (INV-080). The correct paths vary by platform and
installation method, and guessing causes engine
initialization failures (e.g., SENZ2027 when SUPPORTPATH is wrong).

⛔ **`platform` is not optional here, even though the schema says it is.** `sdk_guide` declares
`platform` with `"default": null` ("Omit to get the platform decision tree"), so a call without it
**succeeds** — and returns no `environment` block at all: no `engine_config`, and no
`default_paths` either. Every value this step needs lives in that block, so the omission does not
raise an error, it just leaves you with the bootstrap code and nothing to configure. Pass the
bootcamper's platform. If the response has no `environment` key, that is what happened — re-issue
the call with `platform` rather than reconstructing the paths by hand.

<!-- MCP-NEGATIVE: sdk_guide(topic='configure', language='python') — returns no `environment` block, so neither `engine_config` nor `default_paths` — owner: sdk_guide(topic='configure', platform='linux_apt', language='python') IS the route that carries it and returned `environment.default_paths` plus `environment.engine_config` when asked (routing negative) — server 1.36.0, 2026-09-02 -->

**Build the JSON from `environment.default_paths`, not from the `engine_config` blob.** That response
carries both — **provided `platform` was passed** (above). `default_paths` gives plain, correct
strings — `config_path`, `support_path`, `resource_path` — and assembling the document from them
yields valid JSON on the first try.

⛔ **The response's `engine_config` field must NOT be written to disk as-is. It needs two corrections,
not one:**

1. **It is not valid JSON.** Every brace in it is doubled (`{{` … `}}`), which is `str.format`'s
   escape for a literal brace — the server appears to return the template rather than the rendered
   result. `json.loads` on it raises `JSONDecodeError: Expecting property name enclosed in double
   quotes: line 1 column 2`. Observed on **MCP server 1.32.9, 2026-08-14** (both `topic='configure'`
   and `topic='install'` return the same doubled form), so a future reader can check whether it is
   still true. If it has been fixed upstream, the `default_paths` route above is still the more
   robust source and needs no change.
2. **Its `SQL.CONNECTION` is `/tmp/sqlite/G2C.db`**, which INV-200 forbids — override it to the
   absolute resolution of the project's `database/G2C.db` (see Step 7's SQLite branch).

⚠️ Fixing those two things is **not** the manual construction the 🚨 forbids. What is forbidden is
inventing the *values*; deriving the document from the values the server returned is exactly what
this step asks for. The distinction matters because the old wording ("use the exact JSON") could not
be obeyed at all: pasting it produced a config the SDK cannot parse, and repairing it looked like a
violation of the same sentence.

**What `SENZ2027` is actually telling you: the support data is not where the configuration points.**
Call `explain_error_code('SENZ2027')` first as always (INV-080) — it returns
`EAS_ERR_PLUGIN_INIT: Plugin initialization error`. The actionable detail is in the Senzing FAQ
(`search_docs`, verified 2026-07-30 on MCP server 1.32.2):

> **I get SENZ2027 Plugin initialization error GNR data files failed to load** — You are missing the
> senzingsdk-runtime data directory. The libraries are present but the GNR data files (in
> `resources/data/`) are not deployed.

So the code means *the libraries loaded and their data did not* — which is exactly what a wrong
SUPPORTPATH produces, and on Windows/Scoop exactly the sibling-directory case the `Test-Path` check
below fixes. Look for a misplaced data directory, not for a broken install.

⚠️ **Because those two can be present independently, a version query does not validate the engine.**
An `SzProduct` call can answer while the support data is absent, so "the SDK imports and reports its
version" is not evidence that an engine can initialize — see Step 9, which requires an engine-class
call for exactly this reason.

> **This masking is now MCP-confirmed on two platforms, and it has a concrete failure code.**
> `sdk_guide(topic='install', platform='windows')` states that building `SUPPORTPATH` as
> `%SENZING_DIR%\data` — which on Scoop resolves to a directory that does not exist — makes
> "every SzEngine/SzDiagnostic call … fail with `SENZ7426 EAS_ERR_XLITERATOR_FAILED` ('No
> transliteration rules found! Transliteration requires at least one module') **while SzProduct
> keeps working — so the install looks healthy**" (verified on MCP server 1.32.2, 2026-07-30).
>
> **The macOS cask has the same defect, and the server documents it in more detail.**
> `sdk_guide(topic='install', platform='macos_arm')` states that `SENZ7426` on
> `getEngine`/`getDiagnostic`/`addRecord` "means SUPPORTPATH is WRONG — it is NOT a broken
> install": on cask 4.4.x and earlier, the cask's own shipped `etc/sz_engine_config.ini` sets
> `SUPPORTPATH=${INSTALLPATH}/senzing/er/data`, **a directory that does not exist**, while the real
> support data (`address_datamodel`, `nomicon`, and the `*TransRules.sz` transliteration modules)
> lives one level up at `$(brew --prefix)/opt/senzing/data`. The server reports this confirmed
> end-to-end on cask 4.4.0.26206 and **reported against 4.3.3.26191, which ships the same wrong
> path** (verified on MCP server 1.32.3, 2026-07-31).
>
> ⛔ **Both tools agree on the diagnosis and the fix — not on the macOS literal** (INV-169) —
> re-verified on **MCP server 1.37.14, 2026-09-28**. `explain_error_code('7426')` ranks
> *"SUPPORTPATH points at a directory with no transliteration modules … This is a configuration
> error, NOT a broken install"* as `common_causes[0]` with *"Check SUPPORTPATH FIRST"* as
> `resolution_steps[0]`, naming this same macOS cask case and pointing back at
> `sdk_guide topic='install'` for the platform detail. Both give the same fix: set `SUPPORTPATH` to
> `$(brew --prefix)/opt/senzing/data`, and do not use the shipped `.ini` as-is. **They differ on
> what the shipped ini says.** `explain_error_code`'s macOS cause still quotes the
> `${INSTALLPATH}/senzing/er/data` literal, which holds for cask 4.4.x and earlier only.
> `sdk_guide(topic='install', platform='macos_arm', language='java')` now says the literal "has
> already drifted once" — cask 4.5.0.26245 ships a Linux path instead, and its `CONFIGPATH` and
> `RESOURCEPATH` are Linux paths too — and tells the reader *"Do not pin the literal"*. So relay
> either tool for the diagnosis and the fix, relay `sdk_guide` for the platform detail, and never
> tell a Bootcamper that `explain_error_code`'s macOS literal is what their ini says. Keep
> `sdk_guide` cited for what it still owns — the paths, env vars and EULA variable — and note that
> the principle the earlier note rested on is unchanged: **ask the tool that owns the fact.** Only
> its example is obsolete: the two coverages have converged on the diagnosis, not on the literal.
>
> ⚠️ `sdk_guide` gates this response on `language`: asked with `language='python'` for this platform
> it returns only the "Python is Linux-only" compatibility note and **no install detail at all**, so
> the gotcha above is invisible. Ask with a macOS-supported binding (Java or C#) to see it.
> (Observed 1.37.14, 2026-09-28.)
> <!-- MCP-NEGATIVE: sdk_guide(topic='install', platform='macos_arm', language='python') — returns no install detail, only the Linux-only note — owner: sdk_guide(topic='install', platform='macos_arm', language='python') compatibility_notes state the Python SDK is Linux-only — the absence IS the answer, not a gap — server 1.36.0, 2026-09-02 -->
>
> `SENZ7426` still fires at `getEngine()`, **before any record is submitted**, so "validate your
> input data" would send the reader to inspect something that does not yet exist — which is exactly
> why `explain_error_code` now ranks that cause last and conditions it on the engine having
> initialized successfully.

Use `sdk_guide` with `topic='configure'` to generate the correct engine configuration JSON for
the user's platform and database choice. Save the MCP-returned JSON directly to
`config/engine_config.json`; do not modify the paths.

**On Windows, verify SUPPORTPATH exists before saving the configuration:**

After receiving the MCP-returned JSON, check that the SUPPORTPATH directory actually exists on
the filesystem. This is a targeted path verification, not manual JSON construction: the
MCP-returned JSON remains the starting point.

1. Extract the SUPPORTPATH value from the MCP-returned configuration JSON.
2. Use `Test-Path` in PowerShell to confirm the SUPPORTPATH directory exists:

   ```powershell
   Test-Path -Path "$SENZING_DIR\data"
   ```

3. If `$SENZING_DIR\data` does not exist, check `$SENZING_DIR\..\data` (one level up from the
   `er` directory):

   ```powershell
   Test-Path -Path "$SENZING_DIR\..\data"
   ```

4. If the parent-level path exists, update SUPPORTPATH in the configuration JSON to use
   `$SENZING_DIR\..\data` before saving to `config/engine_config.json`.
5. If neither path exists, report the error clearly: "SUPPORTPATH directory not found at either
   `$SENZING_DIR\data` or `$SENZING_DIR\..\data`. Please verify your Senzing installation."

> **Why the Scoop layout differs:** The Windows Scoop package — Senzing's own bucket,
> `github.com/Senzing/scoop-senzingsdk`, which `sdk_guide(topic='install', platform='windows')`
> calls "the official Senzing Scoop bucket" (verified on MCP server 1.32.2, 2026-07-30) — places
> `SENZING_DIR`
> at the `er` subdirectory within the Scoop app folder (e.g.,
> `C:\Users\<user>\scoop\apps\senzingsdk\current\er`). The `data` directory containing
> `g2SifterRules.ibm` and other GNR support files is at the Scoop app version root, one level
> above `er`, rather than inside it. This is why the fallback to `$SENZING_DIR\..\data` is
> needed for Scoop installs.

**This verification is about a *layout*, not a platform — run it wherever the support data can be a
sibling of `er` rather than a child.** That is currently **two** platforms, both documented by
`sdk_guide`: Windows/Scoop (above) and macOS/Homebrew.

**On macOS, the same check with the Homebrew paths:**

1. Confirm the `SUPPORTPATH` in the MCP-returned configuration exists —
   `test -d "$(brew --prefix)/opt/senzing/data"`, and that it holds the transliteration modules:
   `ls "$(brew --prefix)/opt/senzing/data"/*TransRules.sz`.
2. If it does not, the cask's own `etc/sz_engine_config.ini` is the likely source: its
   `SUPPORTPATH` does not resolve to a directory holding `*TransRules.sz`, whatever its literal.
   Test the directory's content, never the string — the literal has changed between cask
   releases, so matching one value misses the next. On cask 4.5.0 the shipped ini's `CONFIGPATH`
   and `RESOURCEPATH` are Linux paths too, one more reason the file is wrong for a Homebrew
   install. **Do not use the shipped `.ini` as-is, and do not copy transliteration files around**
   — set `SUPPORTPATH` to `$(brew --prefix)/opt/senzing/data`, the `support_path` `sdk_guide`
   already returns.
3. If neither path exists, report both that were tried rather than guessing a third.

⚠️ **Linux was not re-checked for this layout** (verified 2026-07-31: `sdk_guide` was asked for
`macos_arm` and `windows` only). Use the MCP-returned paths on Linux without modification, and if a
Linux install ever produces `SENZ7426`, ask `sdk_guide(topic='install', platform='linux_apt' |
'linux_yum')` before assuming this case applies — do not widen it by inference.

**Re-source the env script now that `config/engine_config.json` exists.** Until this step the script
skipped `SENZING_ENGINE_CONFIGURATION_JSON` with a notice, and a shell that sourced it earlier keeps
that variable unset until it sources the script again. Source `src/scripts/senzing-env.sh` once more
(on Windows, dot-source `. .\src\scripts\senzing-env.ps1` again, unverified on Windows PowerShell 5.1
here, INV-163) in the shell that launches the Bootcamper's programs, and confirm the "not written
yet" notice no longer prints.

**Checkpoint:** write step 8 to `config/bootcamp_progress.json`.

## Step 8a: Seed the default configuration (a freshly created datastore has none)

⛔ **A datastore you just schema-created has NO registered Senzing configuration, and the
data-source registration snippet assumes one exists.** Do this before Step 9 and before any
data-source registration.

⚠️ **"Schema-created" is true of BOTH database branches.** PostgreSQL applies
`szcore-schema-postgresql-create.sql` in Step 7; SQLite applies
`szcore-schema-sqlite-create.sql` there too (rung 2 of its three rungs). If you arrived here on the
SQLite branch without having applied the schema, this step cannot help — go back and apply it, or
`create_engine()` fails with `SENZ1001 (14: unable to open database file)` rather than the
`SENZ7220`/`SENZ7221` this step exists to fix.

`sdk_guide(topic='configure')`'s primary `RegisterDataSources` snippet opens by reading the default
config id and building a config **from** it. On an unseeded datastore there is nothing to read, and
the attempt fails with

```text
SENZ7221 EAS_ERR_NO_CONFIG_REGISTERED_FOR_DATA_ID
```

**The error now names its own remedy — call it and follow it.** `explain_error_code('SENZ7221')`
returns as its first cause *"No default config has EVER been registered on this datastore — it was
schema-created (e.g. via `szcore-schema-*-create.sql`) but never seeded"*, and as its first
resolution step *"Seed a default config first: `create_config_from_template()` (or
`create_config()`), then `set_default_config(config_json, comment)` — see `sdk_guide`
topic='configure'"* — which is exactly Step 8a below (verified on MCP server 1.32.2, 2026-07-30;
through 1.32.1 the entry was generic and this note warned you to disregard it). It also names two
further causes worth knowing: calling `create_config_from_config_id(0)` on the unseeded value, and
an engine pointed at a different datastore than the one you seeded. Seed first and it never arises.

**How to seed — take the code from MCP, do not hand-write it (INV-080):**

⛔ **`data_sources` is the switch that decides which snippet you get.** `sdk_guide(topic='configure')`
returns **one** primary `code` block, and which one depends on whether you passed `data_sources` —
the other becomes an entry in `alternatives`. Getting this backwards is why the seeding step is easy
to misread: you ask one way and look for the answer in the place the *other* call puts it. Verified
on MCP server 1.32.8, 2026-08-11, calling both ways in `language='python'`:

| Call | Primary `code.source_path` | In `alternatives` |
|---|---|---|
| `sdk_guide(topic='configure', language=…)` — **no** `data_sources` | `python/configuration/init_default_config.py` | `register_data_sources` |
| `sdk_guide(topic='configure', language=…, data_sources=[…])` | `python/configuration/register_data_sources.py` | `init_default_config` |

1. **Seed:** call `sdk_guide(topic='configure', language='<chosen_language>')` **without
   `data_sources`**. The **primary `code` block** is the seeding snippet — confirm
   `code.source_path` ends `configuration/init_default_config.py`. Its sequence: read the default
   config id → `create_config_from_template()` → `set_default_config(...)`, which registers the new
   config and makes it default.
2. **Register:** call it again **with** `data_sources=[…]`. Now the primary `code` block is the
   registration snippet (`configuration/register_data_sources.py`), and it has a config to build
   from.

⛔ **Locate the snippet by its `source_path`, never by its position in the response.** Both snippets
are always present; only which one is "primary" moves. A step that says "take the alternative" breaks
the moment the call's arguments change — which is exactly how this instruction went stale once
already.

**The tool now states this precondition itself — relay it rather than asserting it.** The
`data_sources` call carries a `compatibility_notes` entry (same verification, 1.32.8, 2026-08-11):

> "PRECONDITION: this snippet reads the CURRENT default config (`get_default_config_id()` ->
> `create_config_from_config_id()`) and replaces it — it assumes a default config is ALREADY
> registered. On a freshly schema-created datastore, `get_default_config_id()` returns 0 and
> `create_config_from_config_id(0)` raises SENZ7221 … call `sdk_guide(topic='configure', …)` WITHOUT
> `data_sources` first — that returns the `init_default_config` snippet"

Read `compatibility_notes` on each call and follow what it says; it is the authority on ordering here,
not this file. The seeding call's own note adds the step after: `env.reinitialize(config_id)` must
follow `set_default_config()` before loading records, using the id `set_default_config()` returned.

`generate_scaffold(language='<chosen_language>', workflow='initialize')` reaches the same code by
another route: alongside the factory-lifecycle snippets it returns the `configuration/` ones — for
Python, `init_default_config.py`, `register_data_sources.py`, `get_config_registry.py`,
`get_data_source_registry.py` (re-verified 1.32.9, 2026-08-12). The set is
**language-dependent** — Java returns `InitDefaultConfig.java` and `RegisterDataSources.java` and
not the two registry readers (same server and date) — so read what your language's response
actually lists rather than expecting these four. Either route is fine; `sdk_guide` is
preferred here because it also carries the `compatibility_notes` above, which `generate_scaffold`
does not. Step 9's connection test uses the factory-lifecycle snippets from the same response.

**Verify the seed before moving on:** confirm a default config id is now present. If it is not, stop
here and report it — a missing config surfaces at this step as one clear failure, or later as
`SENZ7221` several steps from its cause.

### 8a.1 Re-measure the license — the reading is only complete now

⛔ **(INV-244) Re-take the license reading here, and treat this one as the authoritative value.**
Step 5a's reading was provisional by construction: `get_license()` resolves the license from the
settings it is handed, and until Step 8 wrote `CONFIGPATH` those settings could not reach a license
installed at the system config path. That tier is the third of the four in Step 5's check order, so
the earlier reading could only ever return one of the first two or the built-in default.

Take the reading by Step 5a's sub-step 1, which calls `SzProduct.get_license()` and parses
`recordLimit`; follow it rather than restating it (INV-300), using the settings that now carry
`CONFIGPATH`.
Then apply Step 5a's sub-step 3 rules to the result:

- **Write it** to `config/bootcamp_progress.json` as `license_record_limit`, with
  `license_record_limit_measured_at: "module-02 step 8a (engine configuration in force)"`.
- **When it disagrees with the provisional figure, say the earlier one was withdrawn — naming both
  numbers**, exactly as sub-step 3 requires. ⚠️ **A correction that RAISES the capacity still gets
  said out loud.** It is the pleasant direction and therefore the one most likely to be swallowed,
  and it is load-bearing: anything already sized against the smaller figure — a sampling plan, a
  generated scenario — was sized against a ceiling that does not exist.
- **When the re-measurement cannot run**, leave the provisional value and its `_measured_at` marker
  in place, say the check could not be re-run, and continue. Never blank the field: absence means
  *never measured* to every step that reads it (INV-244), and a provisional figure is strictly
  better than that.

⚠️ **This is the step that makes Step 5a's replace-and-withdraw machinery reachable.** Nothing else
in this module writes `license_record_limit` a second time, so before this step existed those rules
described a situation that could not arise, and a machine whose license lives at `CONFIGPATH`
carried the built-in figure through to Data collection — where it drives the sampling decision and
the License-Key gate. Measured on **Senzing SDK 4.4.0** (`4.4.0.26242`), 2026-09-01: a machine whose
license reports `recordLimit: 0` (no cap) reads `500` at Step 5a and `0` here.

**Checkpoint:** write step 8a to `config/bootcamp_progress.json`.

## Step 9: Test Database Connection

Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`
to get the current V4 initialization and connection test pattern, then use that MCP-generated
initialization code to verify the database connection works.

⛔ **The check MUST create and use an `SzEngine` (or `SzDiagnostic`) — not only `SzProduct`.** A
version query proves the library loaded; it does not prove the engine can initialize, because the
libraries and their support data can be present independently (see the `SENZ2027` note in Step 8).
So a configuration whose SUPPORTPATH is wrong can satisfy a version probe and fail at the first real
engine call, several steps later, where the cause is no longer obvious. Exercising an engine class
here is what moves that failure back to the step designed to catch it.

This constrains **which class the generated check touches**, not where the code comes from: keep
using `generate_scaffold(workflow='initialize')` (INV-080). Do not hand-write it.

⛔ **The response is a LISTING and nothing in it marks which snippet does this — pick by shape
(INV-267).**
On server 1.33.0 (verified 2026-08-23) `generate_scaffold(language='python', workflow='initialize')`
returned **14** snippets with `content` absent — only `file_path`, `raw_url`, `size_bytes` and
`line_count` — and no field flagging any of them as engine-creating. So:

- **Pick the snippet whose body CALLS A METHOD ON the engine, not merely one that creates it.** For
  Python that is `initialization/engine_priming.py`: it builds the factory, calls
  `create_engine()`, then calls `sz_engine.prime_engine()`. Compare
  `initialization/abstract_factory.py`, which calls `create_engine()` alongside
  `create_configmanager()`, `create_diagnostic()` and `create_product()` and then never uses any of
  them — that satisfies "creates an engine" and **not** the ⛔ above, which requires the check to
  *use* one.
- ⛔ **A count or a position in the listing is NOT the selector (INV-267)**, and neither is the
  filename. The snippet count moves as the server indexes more (Module 3's Step 4 documents the same hazard for
  `full_pipeline`, where it went 18 → 22 and a whole group appeared). Match on the **shape** — does
  the body invoke an engine method? — and fetch a candidate's `raw_url` to check rather than
  inferring from its name.
- Every language's set has the same pair, so apply the shape test in whichever language was chosen
  rather than transliterating the Python filenames (INV-090).

Never generate direct SQL against `database/G2C.db`; all access goes through Senzing SDK
methods (per ground-rules).

**Checkpoint:** write step 9 to `config/bootcamp_progress.json`.

**Success indicator:** ✅ SDK installed + DB configured + test passes + **an `SzEngine`/`SzDiagnostic`
call succeeds** (not merely a version query).

## Success Criteria

- ✅ Senzing SDK installed natively.
- ✅ SDK imports/references work in the chosen language.
- ✅ Engine initializes without errors, proven by an `SzEngine`/`SzDiagnostic` call rather than a version query (Step 9).
- ✅ Database connection works.
- ✅ Project directory structure created.

## Agent Behavior

- Always check for an existing installation first: if the SDK is present and V4.0+, do NOT
  reinstall. Skip only the installation and continue on Step 1's existing-install path: Step 3's
  Phase 3 and its environment script still run before verification (INV-339).
- Do NOT offer alternatives: install the SDK natively (or via Docker where the routing rules
  require it).
- Use the `sdk_guide` MCP tool for current platform-specific instructions.
- Use `search_docs` with `category='anti_patterns'` before recommending approaches.
- **NEVER guess engine configuration values:** take `CONFIGPATH`, `RESOURCEPATH`, `SUPPORTPATH` and
  the connection-string form from
  `sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>')`, and build
  the document from that response's `environment.default_paths` — **not** by pasting its
  `engine_config` field, whose braces are doubled and which does not parse (Step 8 states both
  corrections it needs, and its failure modes). Do not guess the paths
  (INV-080: config options come from the MCP tools, never from speculation). ⛔ **`platform` is not
  optional here** — Step 8 states this rule and what a platform-less response looks like, at the
  step that makes the call (INV-183).
- Recommend SQLite for evaluation, PostgreSQL for production.
- Always use `database/G2C.db` for SQLite (never `/tmp/sqlite`).
- Verify installation before proceeding to the next module.

## Troubleshooting

- Installation fails? Use `explain_error_code` for SENZ errors.
<!-- MCP-NEGATIVE-SCAN: not-a-tool-claim — "the datastore has no default configuration" is a fact
     about the Bootcamper's environment, not about an MCP tool's content, so it needs no marker. The
     tool claims in this bullet are POSITIVE (explain_error_code returns the cause and the seeding
     sequence) and are cited inline. Triaged 2026-08-13 from `coverage_reports.py unmarked`. -->
- **`SENZ7221 EAS_ERR_NO_CONFIG_REGISTERED_FOR_DATA_ID`? The datastore has no default configuration —
  seed one per Step 8a.** Call `explain_error_code('SENZ7221')` first as always (INV-080) and
  **follow what it returns**: its first cause is the never-seeded datastore and its first resolution
  step is the seeding sequence, the same one Step 8a takes from `sdk_guide(topic='configure')`
  (verified on MCP server 1.32.2, 2026-07-30). Its third step — check that
  `SENZING_ENGINE_CONFIGURATION_JSON`'s `SQL.CONNECTION` points at the datastore you actually seeded
  — is a real second possibility, not a distraction. This is the expected symptom on a freshly
  schema-created datastore whose config was never seeded, and it can appear several steps after the
  omission.
- **`Unable to get settings`, or an empty `SENZING_ENGINE_CONFIGURATION_JSON`? This is the env
  script's path resolution, not Senzing — or a script sourced before Step 8.** That message
  carries **no SENZ code** because it is not an engine error: it is the null-check in Senzing's
  own official snippets, which print `Unable to get settings.` and throw `IllegalArgumentException` / `ArgumentException` when
  `SENZING_ENGINE_CONFIGURATION_JSON` is unset. So do not send it through `explain_error_code` — there
  is no code to explain, and hunting through the engine config wastes the time. **First check whether
  the script exists at all** — on the existing-install path it is the artifact most likely to be
  missing (INV-339), and asking whether an absent file was sourced sends the reader looking for the wrong
  fault. If `src/scripts/senzing-env.sh` (on Windows, `src\scripts\senzing-env.ps1`) is not there,
  that **is** the finding: write it now per Step 3's environment-script work, with the values from
  `sdk_guide(topic='install', platform=…, language=…)`. On Windows, a project made before the `.ps1`
  that has only the old `senzing-env.bat` counts as not there: write the `.ps1` per
  [the Windows script](#env-script-windows), have the Bootcamper dot-source it with
  `. .\src\scripts\senzing-env.ps1`, and do not tell them to run the `.bat`, which sets nothing in a
  PowerShell window (unverified on Windows PowerShell 5.1 here, INV-163). Only if it does exist, check
  that it was **sourced** (not executed; dot-sourced on Windows) in this shell, and whether it was
  **sourced before Step 8 wrote
  `config/engine_config.json`**: the script then printed a "not written yet" notice and left the
  variable unset, so re-source it now. Then check that it resolved its own path
  under the shell in use — see [the env script's path resolution](#env-script-path-resolution). Under
  zsh, a `${BASH_SOURCE[0]}`-based script computes the wrong root and exports nothing.
  (Snippet guard verified via `search_docs`; MCP server 1.32.1, 2026-07-28.)
- Platform not supported? Use `search_docs` for alternative installation methods.
- Database errors? Confirm path requirements against the file placement rules in ground-rules
  (the Kiro `FILE_STORAGE_POLICY.md` reference is a later porting phase).
- Permission issues? Ensure you have admin/sudo access for installation.
- Missing dependencies? A Kiro preflight script (`preflight.py`) is a later porting phase; for
  now, verify prerequisites directly and use `search_docs` for platform requirements.

## Module completion and transition

Once the SDK is installed and verified, run the standard **Module Completion** process in
`../bootcamp-onboarding/module-completion.md` (update progress, append the Module 2 recap section
to `docs/bootcamp_recap.md`, and present the end-of-module summary), then ask the single
transition question.

The next module in your selected sequence continues the bootcamp — when it is System verification, it verifies the full setup end-to-end with synthetic records; the separate Truth Set visualization module, when selected, then visualizes the Senzing Truth Set:

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)* On module completion set `current_step` to
`null`.
