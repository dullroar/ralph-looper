# Child plan contract

Use this file and the corresponding entry in [targets.md](./targets.md) to render each `plans/ralphify/` seed. Embed the relevant instructions in the child files so that no child needs a sibling checkout or this parent worktree to resume. Each seed contains `goal.md`, `plan.md`, `spec.md`, and the three steps below. Use `gist: "Read me when: ..."` in `plan.md`. The initial target checker still requires `spec.md` with requirement headings `R1`, `R2`, and `R3`, and a matching `requirements` field on each step. The runner requires `goal.md`, `plan.md`, and `steps/`. Keep `spec.md` as the requirement record through the rollout.

Use the step filename stem as `id`. Set initial `status: pending`, `lane: none`, and empty evidence. List exact `depends_on`, `touches`, and `gate` fields. Include the step's own file in `touches`. Every child gets the same three-step dependency chain. Render `touches` from the allowed changes below and the repo-specific scope. Run the protected gates as written. If the base requires a larger change or a gate fails for reasons outside the repo, record the blocker for that target.

## Prepare the seed

- Record the clean base ref and commit. Create a linked seed worktree and commit only the seed files on `rollout/ralphify`. Run the repository's existing `python3 scripts/check_context.py` on the seed before starting Ralph. Include current rules and any baseline check issues in the seed. For `duckdb-fs`, allow only the known `BROKEN README.md: ../metadata_driven_gx` baseline result, with the other checks passing. Step 01 fixes that link and requires a clean context result.
- Give the child agent the pinned template source. Vendor the needed generic scaffold into the seed as inputs, or stage a read-only snapshot outside the target Git tree and record how to recover it at the same revision. The finished repo must own its checks and run without the snapshot or the template checkout.
- Confirm `ralph-looper` sees all three steps in the seed. Keep the same plan name in each repository. The launcher gives the ten children different repository and worktree identities.

## 01-adopt-context (R1)

Depends on no step. Carry forward the project description, existing local rules, and context ownership. Keep `CLAUDE.md` as a pointer to the root contract. Put this rule in `AGENTS.md`, with links to both upstream repositories:

> Before changing this repository's structure, read `repo-template` and `ralph-looper`. Account for their layout, plan format, generated indexes, worktree rules, and validation commands in the change.

Adopt `docs/README.md`, `memory/AGENTS.md`, `plans/AGENTS.md`, `scripts/AGENTS.md`, and `plans/for-each-plan/`. Preserve any existing docs and archive references. Move the old `plans/TEMPLATE/` out of the active plan namespace and repair references. Keep archived plans readable without rewriting their evidence. Adapt and reuse existing checker logic where it preserves coverage. Provide `scripts/build_indexes.py` and `scripts/check_context.py`. Preserve compatibility for documented checker commands and repository-specific checks. Add or adapt `.github/workflows/context.yml` for the actual base branch and preserve existing workflows. Regenerate indexes. Resolve any local links that would fail from a standalone checkout.

Touches the agent contracts, the relevant index and checker files, current plan templates, references to the old layout, `.github/workflows/context.yml`, and this step file. Review the exact layout diff and test that broken links, stale indexes, malformed active plans, and the existing secret scan still fail their checks. Gate: `python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && git diff --check`.

## 02-build-and-test (R2)

Depends on `01-adopt-context`. Add a project Dockerfile, an appropriate `.dockerignore`, and `scripts/test_docker.sh`. Use project dependencies and current lockfiles. Run project tests as a normal container user where supported. Use synthetic fixtures, a temporary output directory, and no developer credentials. Put any new operational or test artifacts under the repo's existing conventions. Document build, test, and any device or platform requirements in `README.md`. Keep existing host usage working. Arrange for CI to call the same entry point wherever the runner supports that gate.

The Docker test script builds the image from the current step worktree and runs the repo-specific gates inside it. For context checks, use a complete source snapshot or an appropriate read-only checkout that works with linked Git worktrees. A linked worktree's `.git` pointer alone does not provide its Git metadata in the container. Keep the image usable without a sibling checkout, host venv, or mutable shared volume. Use repo- and run-specific names for any image tags, container names, and writable paths. Build dependencies can use package registries. The default test runtime uses local fixtures and an isolated container network. The FUSE mount gate is required for the two FUSE lanes, with the host requirements in their repo briefs.

Touches `Dockerfile`, `.dockerignore`, `README.md`, `scripts/test_docker.sh`, generated indexes, any necessary workflow updates, focused test/support paths from the repo brief, and this step file. Gate: `bash scripts/test_docker.sh && python3 scripts/check_context.py && git diff --check`.

## 03-verify-integration (R3)

Depends on `02-build-and-test`. Update only the step file. Rerun the context and Docker gate from the integrated worktree as the driver would. Check the template and runner links in `AGENTS.md` and the structural-change rule. Verify README commands and the existing entry points. Record the worktree base commit, exact commands, build result, test counts or concrete smoke assertions, expected opt-in skips, real FUSE result where required, and UTC date. Keep logs outside Git. Gate: `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.

The driver writes its own `evidence` field. Put detailed test evidence in the body of the verification step and commit it. The parent verifies the final child commit and result. A green build alone cannot satisfy R2 or R3.
