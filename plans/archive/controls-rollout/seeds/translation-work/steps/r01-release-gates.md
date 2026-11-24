---
id: r01-release-gates
status: pending
depends_on: [j10-gate-7, h02-humor-ingest, u01-approve-guides, x01-translation-pack]
touches:
  - plans/v4-es-1/records/r01-release-gates.md
  - plans/v4-es-1/steps/r01-release-gates.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py release
gate: python3 plans/v4-es-1/gatelib.py keys plans/v4-es-1/records/r01-release-gates.md result asset && grep -q '^result: pass$' plans/v4-es-1/records/r01-release-gates.md && python3 plans/v4-es-1/gatelib.py guard && python3 tools/jury_gate.py --stage final && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: all release gates on the final candidate

No model work. The `run` command runs `tools/verify.py --release`: the lock, the inventory, the path invariants, every authored file with its PO file, the line anchors, the negative fixtures, every tool test, the English repo gates, the release builds and the double build with identical hashes. It then writes the SHA-256 of each PDF and EPUB of the build to `plans/v4-es-1/records/r01-release-gates.md` (lines `asset: <name> <hash>`). Step `r03-verify-release` compares the published assets with these lines. The link audit is part of the English gates and of `verify.py`. The gate also checks `loop/STOP` and the private files through `guard`.

If this step fails only because the host has no Docker or no Mermaid CLI, or because of a known failure of `plans/adopt-ralph/tools-test-baseline.txt`, the operator fixes the host or uses `fanout.py amend`. Nobody weakens the gate.

## Do not change

- Files outside `touches`. The `gate`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
