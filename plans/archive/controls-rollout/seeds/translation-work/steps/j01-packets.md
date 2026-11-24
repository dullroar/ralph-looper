---
id: j01-packets
status: pending
depends_on: []
touches:
  - plans/v4-es-1/records/j01-packets.md
  - plans/v4-es-1/steps/j01-packets.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py packets build
gate: python3 plans/v4-es-1/gatelib.py keys plans/v4-es-1/records/j01-packets.md manifest-sha256 packets leak-count builds-equal && grep -q '^leak-count: 0$' plans/v4-es-1/records/j01-packets.md && grep -q '^builds-equal: yes$' plans/v4-es-1/records/j01-packets.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: build the Jury packets for the release candidate and record their digest

No model work. The `run` command builds the packets (prose and code, with the bundle and the canaries) twice into `.probe/`, checks that both builds have the same manifest digest, and checks that `jury_packet.py` reports no `LEAK:` line. It writes the digest to `plans/v4-es-1/records/j01-packets.md` and deletes `.probe/`. The packets, the bundle and the canary key stay untracked.

Later steps rebuild the packets from the same commit and compare the digest. A step that changes translated content after this step makes the digest different. Then the operator runs `gatelib.py packets build` again and records the new digest in the same commit as the content change.

## Do not change

- Files outside `touches`. The `gate`. `tools/jury_packet.py`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
