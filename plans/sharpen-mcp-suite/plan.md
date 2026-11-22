---
gist: "Read me when: you want to run or resume the four bounded MCP tool catalogs from one Ralph parent plan."
---

# Run four bounded MCP catalogs

The [target manifest](./targets.tsv) pins the commits that introduce each child plan. Each target implements its own native capability matrix, bounded tool schema, real Docker fixtures and consuming-agent guide. The libvips catalog is the coverage model. The metadata field support and rights audit receive dedicated acceptance checks. The GPX plan uses gpxpy and has no runtime dependency on the older parser.

## Steps

| Step | Goal | Depends on |
| --- | --- | --- |
| [01-preflight](./steps/01-preflight.md) | Check the four committed child plans and the runner. | None |
| Operator dispatch | Run the independent child plans through the existing Bash driver. | 01 |
| [02-verify-children](./steps/02-verify-children.md) | Verify and record the child results. | 01 and completed dispatch |

## Run

Use a Bash host with working Docker, a supported agent CLI and enough capacity for the selected concurrency. Fetch the four target repositories so their pinned commits from the manifest are available locally. Set `REPOS_ROOT` to their common checkout parent, `RALPH_REPO` to the Bash runner checkout, and `RALPH_WORK` to an absolute directory outside the repositories. Export all three. Set `MCP_RALPH_AGENT` explicitly.

```bash
runner="$RALPH_REPO/ralph-looper"
"$runner" --repo "$RALPH_REPO" --plan sharpen-mcp-suite \
  --agent "$MCP_RALPH_AGENT" --jobs 1 --max-iterations 1 --on-limit handoff
```

The iteration cap can return exit 10 after step 01 passes. Check that step 01 is done on `plan/sharpen-mcp-suite` before dispatching.

```bash
plan="$RALPH_WORK/ralph-looper/sharpen-mcp-suite/worktrees/_plan/plans/sharpen-mcp-suite"
python3 "$plan/fanout.py" run --agent "$MCP_RALPH_AGENT" --jobs 4
```

The launcher creates detached, pinned seed worktrees outside the repositories and calls the existing Ralph driver against each one. Each driver manages a single step at a time. There are no dependencies between the four targets. Lower the rollout concurrency if Docker or model capacity requires it. All four target runs use separate Git directories, worktrees, Docker resources and logs. Child status and evidence remain in the child Git branches and in Ralph's external runtime directories. Use the same environment and command to resume. Finished children are revalidated and reused. A blocked or stopped child exits independently and does not stop the other runs. Keep stopped worktrees intact. Clear an operator pause only when intended, and review a blocked gate before requeueing it.

After the dispatcher exits zero:

```bash
"$runner" --repo "$RALPH_REPO" --plan sharpen-mcp-suite \
  --agent "$MCP_RALPH_AGENT" --jobs 1 --on-limit handoff
```

Review the completed local child branches through each repository's normal publishing process.
