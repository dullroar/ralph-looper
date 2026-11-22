---
id: 02-verify-rollout
status: pending
depends_on: [01-prepare-launcher]
touches:
  - plans/ralphify-repositories/steps/02-verify-rollout.md
lane: none
gate: python3 plans/ralphify-repositories/rollout.py verify && python3 scripts/check_context.py && git diff --check
evidence: ""
---

# Verify all ten target plan branches

Run this parent step after the operator launch has succeeded. Use the same exported `ROLLOUT_STATE` as the launcher. Run the read-only verifier from your step worktree. Review the result for each entry in the [allowlist](../targets.tsv). Check the Docker gate evidence against the matching [repo brief](../targets.md), including both real FUSE mounts and the offline compliance suite. Record each repo, final plan commit, Docker test result, and UTC date below. Keep raw logs and local paths in the external run state.

If a target is incomplete or its branch changed, record the exact missing or mismatched result. The parent gate must fail until the target is verified. The operator resumes that child plan using its existing state. Preserve completed results and leave branch integration to the repository owner.

## Results

The parent gate verified all ten `plan/ralphify` commits and matched their final driver gate logs to the rollout state. All ten Docker builds passed.

| Repository | Final plan commit | UTC date | Docker test result |
| --- | --- | --- | --- |
| `compliance_poc` | `9ec8d6100306fef7102d5fa70f099e3b07072ec7` | 2026-11-22 | Pass. The offline suite ran 657 tests. It had 649 passes and eight expected opt-in skips. MCP stdio parity and lifecycle checks passed. |
| `duckdb-fs` | `7a4bc4d828ad5000718f158d708867533a9bc283` | 2026-11-22 | Pass. The device-free run passed 23 tests. One real FUSE mount test passed with zero skips and matched the file read from the mount to the committed GX fixture. |
| `ffmpeg_mcp` | `c5a01b66a3a43f1e8b780fbb47f18f8766d54071` | 2026-11-22 | Pass. One MCP stdio test listed seven tools and converted a synthetic WAV file. `ffprobe` confirmed the FLAC format, channel count, sample rate, and sample count. |
| `gpx_parser` | `dc1bc0260e51fbd354e3ac45d997d2b4a9a523e1` | 2026-11-22 | Pass. Two CLI tests checked CSV rows, distances, and elevations for file and directory inputs. |
| `lmdb-fs` | `1d49b23c77c8d08c304f41cc4b6721b9d969c9e0` | 2026-11-22 | Pass. The device-free run passed 29 tests. One real FUSE mount test passed with zero skips. It read a synthetic payload, checked write rejection, and unmounted the filesystem. |
| `metadata_driven_gx` | `c26b9296789938758656afa5e43677127616e30e` | 2026-11-22 | Pass. Six demo suites matched 12 sample CSVs, with 50 summary rows and 34 detail rows. The comparison ignored only `run_date`. |
| `metadata_mcp` | `0af4398833d2b9168dccf4acdad99d41d12c01cd` | 2026-11-22 | Pass. Seventeen unit tests passed. An MCP stdio smoke test checked a Markdown title with Pandoc and an HTML title with ExifTool. |
| `pandoc_mcp` | `0081022db28d79cce4c5bfa0913451acc54513c8` | 2026-11-22 | Pass. One MCP stdio test listed tools and formats and checked the exact HTML output from inline and file inputs. |
| `sample_parse` | `055ee7dbba68730869bfb299668095e95f2cd5d9` | 2026-11-22 | Pass. All 89 tests passed with zero skips. The installed CLI and library also passed smoke checks. |
| `vips_mcp` | `33a4dfca589a510ea664e4f0efbdf225e562f1a4` | 2026-11-22 | Pass. One MCP stdio test resized a synthetic PNG. `vipsheader` confirmed the output dimensions. |
