---
id: b05-markdown-links
status: pending
depends_on: [b03-self-ci]
touches:
  - src/deterministic_controls/checks/markdown_links.py
  - src/deterministic_controls/catalog/markdown.local-links.toml
  - tests/test_markdown_links.py
  - tests/fixtures/markdown_links/**
  - plans/bootstrap/steps/b05-markdown-links.md
lane: none
agent: local
fallback: claude
gate: python3 -m unittest discover -s tests -p 'test_markdown_links.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Port `markdown.local-links` with the edge-case fixtures

Read `plans/bootstrap/plan.md` first. The source is `scripts/check_links.py` of this repository. Keep that script. The library check must give the same pass or fail result on the same input, and it must be read-only.

## Change

- `checks/markdown_links.py`: a function `entry(context)`. Check each relative link and image target in tracked Markdown files: the file must exist, and a `#heading` anchor must match a heading of the target file. Match `scripts/check_links.py` for what it skips (web links, `mailto:`, and the like). Stable rule IDs: `markdown.local-links.missing-file`, `.missing-anchor`.
- `catalog/markdown.local-links.toml`: id `markdown.local-links`, status `advisory`, severity `error`, `module = "deterministic_controls.checks.markdown_links"`, `entry = "entry"`.
- Look at `checks/plans.py` and `catalog/plans.schema.toml` for the pattern. Use the `Finding` type of `core/`.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md` (Markdown fixtures end in `.fixture`; a test copies the tree and removes the suffix). `tests/fixtures/markdown_links/` has a good repository and bad fixtures. Cover these edge cases, each as its own fixture: Unicode in names and headings, percent-encoded paths, duplicate headings, reference links, fenced code that holds link-like text (not a link), file names with spaces, absolute paths, and links into `plans/archive`. For each case, first read what `scripts/check_links.py` does, then make the library do the same. If the old script is wrong in a case, keep the same pass or fail result and write the difference under "Resume notes" for the review. `tests/test_markdown_links.py` proves for each bad fixture the rule ID, the path and the exit code `1`. The good fixture passes. A compatibility test runs `scripts/check_links.py` on each fixture and compares the pass or fail result.

## Do not change

- Files outside `touches`. The `gate` command. `scripts/check_links.py`.

## Already done by earlier steps

- b01 to b03: the package, the CLI, the catalog loader, the plan checks and the CI job.

## Done when

- The gate passes. Each bad fixture fails for its own rule. The good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
