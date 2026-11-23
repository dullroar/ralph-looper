---
gist: "Read me when: you build or change the deterministic-controls library before release v0.1.0: the CLI, the manifest, the result contract, the checks or the adoption tools."
---

# Plan: bootstrap the deterministic-controls library (v0.1.0)

This file is the high-level plan. The detail is in `steps/`. Every step is self-contained. Read this file for the shared decisions.

## Approach

The repository starts as a copy of `repo-template`. It has the template scripts in `scripts/` (`check_context.py`, `check_plan.py`, `check_links.py`, `build_indexes.py`, `scan_secrets.py`, `ctx_common.py`). The library ports these checks one by one. Each port keeps the template script, so a compatibility test can run both on the same fixtures. The old scripts go away only in the last step that needs them.

The first vertical slice is the plan checks (`b02`). It proves the CLI, the result contract, the CI job and a failing bad fixture. The other checks follow the same pattern.

The secret guard comes first (`b00`). The template has no secret guard, and a missed secret cannot be undone by a later fix. The reference copy is in `plans/bootstrap/reference/`. It is a copy of the guard of the runner at the time of the seed.

## Decisions

- Package `deterministic_controls`, source layout `src/`. Python 3.11 or later. Standard library only at run time. Test with `unittest`.
- CLI: `python3 -m deterministic_controls {list,check,explain,version,adopt}`. `check --root DIR --profile quick|ci|full [--format text|json] [--report FILE]`.
- Exit codes: `0` pass, `1` defects found, `2` bad configuration or invocation, `3` internal failure. All nonzero codes fail CI. A crash never gives `0`.
- Result JSON fields: `schema_version`, `tool_version`, `repository_revision`, `control_revision`, `config_digest`, `profile`, `status`. For each check: `check_id`, `status` (`passed`, `failed`, `skipped` with a reason, `error`), `duration_ms` and findings. A finding has `rule_id`, `severity`, `path`, `line`, `message`, `evidence`.
- Manifest `controls.toml` with `schema_version = 1`: profile, enabled check IDs, parameters. No commands. Unknown keys and unknown IDs are errors. A missing manifest is a configuration error (exit `2`) with a clear message.
- Catalog: one file for each check, `src/deterministic_controls/catalog/<check-id>.toml`. Keys: `id`, `summary`, `version`, `status` (`experimental`, `advisory`, `required`, `deprecated`), `severity` (default), `parameters`, `module`, `entry` and the optional boolean `mandatory`. A mandatory check runs in every profile and cannot be disabled in the manifest (exit `2`). With one file for each check, parallel steps never edit a shared file. `list` reads these files. It does not import a check module to list it. `check` imports `module` from the package and calls `entry(context)` only for an enabled check.
- Check modules: `checks/plans.py` (`plans.schema`, `plans.graph`), `checks/index_freshness.py`, `checks/markdown_links.py`, `checks/secrets.py`, `checks/personal_data.py`, `checks/forbidden_artifacts.py`. Step `b01` defines the `context` object and the `Finding` type in `core/`. Later steps use them without change.
- Severity is separate from policy. A policy maps severities to failure. A mandatory check that is missing or skipped fails.
- Checks are read-only. A fixer needs a separate `--fix` flag. It does not exist in `v0.1.0`.
- Fixture rule. The template checks scan every Markdown file of this repository, including fixtures. A bad fixture would fail them. So store each Markdown fixture file with the extra suffix `.fixture` (for example `README.md.fixture`). The test copies the fixture tree to a temporary directory and removes the suffix before it runs a check. Build fixtures that hold a secret, a personal path or a forbidden tracked file at run time in a temporary directory. Never store them as files.
- Each test file adds `<repo>/src` to `sys.path` at its top, so `python3 -m unittest discover -s tests` works without an install.
- The install line for consumers is `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@<commit>"`. The commit does not exist before the release. This plan does not use it. Step `b08` writes it into a template with the placeholder `<commit>`.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| [b00-secret-guard](./steps/b00-secret-guard.md) | cloud agent, light | Install the secret guard, the hooks and the CI job. Refresh the generated indexes. | none |
| [b01-contract](./steps/b01-contract.md) | cloud agent | Package skeleton, CLI, manifest and result schema, catalog loader, exit codes, contract tests. | b00 |
| [b02-plans-slice](./steps/b02-plans-slice.md) | cloud agent | Port `plans.schema` and `plans.graph`, with fixtures. | b01 |
| [b03-self-ci](./steps/b03-self-ci.md) | cloud agent | CI workflow, an example consumer fixture, proof that a bad plan fails in both places. | b02 |
| [b04-index-freshness](./steps/b04-index-freshness.md) | local, fallback claude | Port `context.index-freshness`, without writes. | b03 |
| [b05-markdown-links](./steps/b05-markdown-links.md) | local, fallback claude | Port `markdown.local-links` with the edge-case fixtures. | b03 |
| [b06-secrets](./steps/b06-secrets.md) | cloud agent | Port `security.secrets` and `security.personal-data`. | b03 |
| [b07-forbidden-artifacts](./steps/b07-forbidden-artifacts.md) | local, fallback claude | New `repo.forbidden-artifacts`. | b03 |
| [b08-adoption-tools](./steps/b08-adoption-tools.md) | cloud agent | `adopt audit`, `plan`, `apply`, receipt, shim and workflow templates. | b03 |
| [b09-test-the-tests](./steps/b09-test-the-tests.md) | cloud agent | Mutation, metamorphic and fail-closed tests, performance, fault matrix. Dogfood the shim. | b04, b05, b06, b07, b08 |
| [b10-release-prep](./steps/b10-release-prep.md) | cloud agent | Docs, changelog, release check script, version `0.1.0`. | b08, b09 |
| [b11-verify](./steps/b11-verify.md) | cloud agent, light | Run everything from a clean clone and record evidence. | b10 |

## Parallelism

- `b00` to `b03` run one after the other. They build the base that all later steps share.
- `b04`, `b05`, `b06`, `b07` and `b08` run together after `b03`. Each touches only its own module, catalog file, test file, fixture directory and step file. `loop.yaml` sets `jobs: 4`.
- `b09` waits for the four checks and for `b08`, because it uses the shim writer of `b08`. `b10` waits for `b09`. `b11` runs last.

## Risks

- **A secret is committed.** `b00` installs the guard first. Synthetic secrets in tests are built at run time. Do not add an exception to pass a step. A new exception needs a reason and a fingerprint, and the owner reviews it.
- **A weak secret rule.** `b06` uses a cloud agent, not the local model. `security.secrets` is `required` in every profile and cannot be turned off.
- **A port changes behavior.** Each port has a compatibility test that runs the template script and the library on the same fixtures.
- **The local model fails a step.** The three local steps have a cloud fallback. The driver switches after a failed attempt.
- **No network for the wheel build.** `b10` and `b11` build a wheel. If the build tool is not available offline, record that under "Resume notes" and stop. Do not change the gate.
- **A check turns a pass into a false pass.** `b09` adds mutation and fail-closed tests. A mutation must turn a pass into the expected failure.
