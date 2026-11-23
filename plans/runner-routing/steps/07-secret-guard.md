---
id: 07-secret-guard
status: pending
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
claimed_by: ""
claimed_at: ""
evidence: ""
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

(fill in)

## Resume notes

(none)
