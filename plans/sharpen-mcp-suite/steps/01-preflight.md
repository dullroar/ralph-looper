---
id: 01-preflight
status: pending
depends_on: []
touches:
  - plans/sharpen-mcp-suite/steps/01-preflight.md
lane: none
gate: python3 plans/sharpen-mcp-suite/fanout.py ready && python3 scripts/check_context.py && git diff --check
evidence: ""
---

# Preflight the committed MCP plans

Use the environment documented in the plan. Verify the four canonical repositories, their pinned child-plan commits, and the Bash driver. Confirm Docker can build and start the intended test images on the operator host. Check resource capacity for four independent children. Record the checkout provenance, pins, and command results. Keep personal paths and logs out of Git. If a pin is missing, have the operator fetch the corresponding default branch and retry. Do not start a child from this agent step.

## Resume notes

Pending.
