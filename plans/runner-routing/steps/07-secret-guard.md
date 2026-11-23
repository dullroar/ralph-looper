---
id: 07-secret-guard
status: done
depends_on: [01-baseline-records]
touches:
  - scripts/secret_guard.py
  - scripts/install_hooks.sh
  - scripts/check_context.py
  - scripts/AGENTS.md
  - tests/test_secret_guard.py
  - .secret-guard-allow
  - .github/workflows/context.yml
  - plans/runner-routing/steps/07-secret-guard.md
lane: none
gate: python3 tests/test_secret_guard.py && python3 scripts/secret_guard.py --tracked && python3 scripts/secret_guard.py --history && bash scripts/install_hooks.sh --self-test && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-23T22:26:26Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Build a deterministic secret guard for commits, pushes, CI and the driver

Secrets must never be tracked, committed or pushed in any repository. This is the owner's hard rule. The current `scripts/scan_secrets.py` reads only Markdown in the context folders, with six patterns. It does not see a `.env` file, a key in a Python file or a committed `id_rsa`. No hook and no CI job checks commits or pushes. Build one guard that does, with no model and no network. Every later step of every plan depends on it.

## Change

- `scripts/secret_guard.py`: standard-library Python. Start with a comment block that has a `Run me when:` line.

  ```text
  secret_guard.py --staged              # pre-commit: the staged blobs
  secret_guard.py --range A..B          # pre-push, the driver, CI on a pull request: every added line in every commit of the range
  secret_guard.py --tracked             # CI and audits: every tracked file at HEAD
  secret_guard.py --history             # one-time audit: every added line in all history (git log --all -p)
  secret_guard.py --paths FILE...       # the given files
  ```

  Options: `--root DIR` (default: the Git top level), `--format text|json`.

- **What it finds.** Scan every text file, not only Markdown. Treat a file with a NUL byte in the first 8 KiB as binary: check its name, and report it as unscanned content in JSON. Scan the first 5 MiB of a large text file and report the rest as unscanned. Never skip a file without saying so.
  - Private keys: `-----BEGIN ... PRIVATE KEY-----` (RSA, EC, DSA, OPENSSH, ENCRYPTED, PGP `PRIVATE KEY BLOCK`).
  - Provider tokens: Anthropic `sk-ant-`, OpenAI `sk-` and `sk-proj-`, GitHub `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`, AWS `AKIA`/`ASIA` access key IDs and `aws_secret_access_key` assignments, Google `AIza`, Slack `xox[baprs]-` and webhook URLs, Stripe `sk_live_` and `rk_live_`, Hugging Face `hf_`, SendGrid `SG.`, npm `_authToken`, PyPI `pypi-`, Azure `AccountKey=` and `SharedAccessKey=`, JSON Web Tokens (`eyJ...` with three parts). <!-- scan:ignore -->
  - Credentials in URLs: `scheme://user:password@host`. <!-- scan:ignore --> <!-- secret-guard: allow format example, not a credential -->
  - Generic assignments: keys named like `password`, `passwd`, `pwd`, `secret`, `token`, `api_key`, `apikey`, `access_key`, `client_secret`, `private_key` in code, YAML, TOML, JSON, INI, `.env` and shell, when the value has at least 16 characters and a Shannon entropy of at least 3.5 bits for each character.
  - File names that must never be tracked: `.env` and `.env.*` (but not `.env.example`), `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `credentials.json`, `service-account*.json`, `.netrc`, `.pypirc`, `.npmrc` with a token, `.git-credentials`, `.claude/settings.json`, `.claude/settings.local.json`, `review/canaries.key.json`.
  - Placeholders are not findings: values inside `<...>`, `${...}` or `$VAR`, and values that contain `example`, `placeholder`, `changeme`, `dummy`, `xxxx` or `****`.

- **Exceptions.** A line that contains `secret-guard: allow <reason>` is not a finding. The reason is required. A file `.secret-guard-allow` (tracked, reviewed like code) holds one exception for each line: `<sha256 of path + matched text>  <path>  <reason>`. There are no glob or directory exceptions. Print the fingerprint with each finding, so that a reviewer can add an exact exception. Example: `compliance_poc` has an offline test sentinel that looks like an Anthropic key (it ends in `SENTINEL-0000`). It needs one fingerprint line in that repository with the reason "offline test sentinel".
- **Output.** Never print a secret. Print the path, the line, the rule ID, the fingerprint and a redacted match (the first 4 characters, then `…`, then the length). Exit `0` clean, `1` findings, `2` error (not a Git repository, a bad range, an unreadable file). Never exit `0` after an exception.
- `scripts/install_hooks.sh`: install `pre-commit` (`--staged`) and `pre-push` (`--range` for each pushed ref, from stdin; for a new branch, the commits not on any remote branch) in the repository's common Git directory, so that all worktrees use them. If a hook exists and is not ours, keep it: move it to `<hook>.local` and call it after the guard with the same arguments and stdin. The translation repository has such hooks (the locked-code `pre-commit` and the restricted `pre-push`). They must keep working. Running the installer twice changes nothing. `--check` exits nonzero if the hooks are missing or not ours. `--self-test` runs the installer in a disposable repository with an existing `pre-push` hook and proves both hooks run and the chain works. The hooks find `secret_guard.py` in the repository's own `scripts/` and, if it is absent, in `$SECRET_GUARD` (the runner copy).
- `scripts/check_context.py`: add `secret_guard.py --tracked` to the aggregate checks. Keep `scan_secrets.py` (it also finds personal paths and e-mail addresses in context Markdown).
- `.github/workflows/context.yml`: run `secret_guard.py --tracked` on every push and pull request. On a pull request, also run `--range <base SHA>..<head SHA>` with a full fetch (`fetch-depth: 0`), so that a secret added and removed inside the branch is still found. `permissions: contents: read`. No `continue-on-error`. No path filters.
- `.secret-guard-allow`: a header comment that explains the format. No entries unless a finding in this repository needs one.
- `tests/test_secret_guard.py`: build every synthetic secret at run time from parts (for example `"sk-" + "ant-" + "A" * 40`). Never write a literal secret in the test file, or the guard finds its own tests. Cover: each rule, each mode, placeholders, an inline exception with and without a reason, a fingerprint exception, a binary file, a large file, a forbidden file name, a secret added and removed in the same range, redaction (the full secret never appears in output), and exit 2 for a bad range.

## Then audit

Run `secret_guard.py --history --format json` read-only on each of the 13 repositories in `plans/runner-routing/baseline.tsv` and on the English source repository (`learn-programming-the-weird-way`). Use `--root` and do not change those repositories. Record the count for each repository below. For each finding, record the repository, the commit, the rule ID and the fingerprint, never the value. A planning audit on 2026-11-23 found only the `compliance_poc` test sentinel. If a real secret appears, set this step `blocked` with the reason "real secret in history: rotate it, then decide on a history rewrite". Rotating a credential is an operator action. Never rewrite history in a step.

## Do not change

- Files outside `touches`. The gate command. Any other repository.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Results

History audit on 2026-11-23 with `secret_guard.py --history --format json --root <repo>`, read-only. No repository was changed. `diffs` is the number of file diffs that the guard read. Unscanned diffs are binary files. The guard checked their names.

| Repository | Findings | Diffs | Unscanned (binary) |
| --- | --- | --- | --- |
| `ralph-looper` | 0 (1 inline exception in this step file) | 214 | 0 |
| `repo-template` | 0 | 25 | 0 |
| `aprende-a-programar-como-un-bicho-raro` | 0 | 7538 | 108 |
| `compliance_poc` | 5 | 776 | 1 |
| `duckdb-fs` | 0 | 129 | 0 |
| `ffmpeg_mcp` | 0 | 147 | 0 |
| `gpx_parser` | 0 | 125 | 0 |
| `lmdb-fs` | 0 | 195 | 0 |
| `metadata_driven_gx` | 0 | 173 | 0 |
| `metadata_mcp` | 0 | 177 | 7 |
| `pandoc_mcp` | 0 | 101 | 0 |
| `sample_parse` | 0 | 114 | 0 |
| `vips_mcp` | 0 | 148 | 0 |
| `learn-programming-the-weird-way` | 0 | 1887 | 85 |

Findings in `compliance_poc`. All five are offline test values, not credentials. The four key-like values end in `SENTINEL-0000`. The fifth is a test marker that ends in `NOT-APPEAR-9876`. No rotation is necessary.

| Commit | Path | Rule | Fingerprint |
| --- | --- | --- | --- |
| `0bae2a776d6fde0a4a498a3b9844c57d8f822e89` | `tests/test_openai_live_parallel.py` | `openai-key` | `4511cba94ce4981d30bfedfaafd96ead09bd99ed2f6a7c824461d7e9be44ee39` |
| `e35e8f056e51ea9fda0130a823a12c19a2245502` | `tests/test_anthropic_live_parallel.py` | `anthropic-key` | `c7dba1a2c164ddae7f29e7520bf2b5ebedf12441c34aca369924615c4a80af22` |
| `020620a5aec4afe1a0ce7ef5f03ce587e0d651bf` | `tests/test_anthropic_live_accounting.py` | `anthropic-key` | `38b64a76e12ab51a719de02d48eaf84a3d35278e6adf41eb31682f16486145fd` |
| `020620a5aec4afe1a0ce7ef5f03ce587e0d651bf` | `tests/test_openai_live_parity_accounting.py` | `openai-key` | `e5d34469cb44100a292748427369760106a4c184b1a94165e45bbedffe6d6e7a` |
| `052d735f5ddfce9cba67e8df1e5c4267bd88bded` | `tests/test_agent_runner.py` | `generic-secret` | `6641c131657c531de49ba551b67d4bed9931cb5c48e9582b8442a5d4ed2fb03b` |

Notes for later steps:

- `compliance_poc` needs five lines in its own `.secret-guard-allow`, one for each fingerprint above, with the reason "offline test sentinel" (or "offline test marker" for the fifth). The planning audit expected one value. There are two sentinel values in four files, and one marker.
- The first audit run found 22 generic matches in `translation/protected-tokens/tokens.jsonl` of the translation repository. They were language identifiers, for example `"token":"ReadableStreamDefaultController"`. The guard now ignores identifier-like values with at most one digit. The count above is after that change.
- Hooks are not installed in any clone by this step. The operator runs `bash scripts/install_hooks.sh` in each clone after the merge (see `plan.md`).

## Resume notes

(none)
