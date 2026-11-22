---
id: 02-verify-rollout
status: done
depends_on: [01-prepare-launcher]
touches:
  - plans/ralphify-repositories/steps/02-verify-rollout.md
lane: none
gate: python3 plans/ralphify-repositories/rollout.py verify && python3 scripts/check_context.py && git diff --check
evidence: gate passed 2026-11-22 (driver-verified)
claimed_by: codex cli-default
claimed_at: "2026-11-22T22:41:58Z"
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

## Publication

All ten rollout pull requests merged into their existing default branches on 2026-11-22 UTC. The table above records the original Ralph verification commits. The merge commits below record publication.

| Repository | Pull request | Merge commit |
| --- | --- | --- |
| compliance_poc | [#10](https://github.com/dullroar/compliance_poc/pull/10) | `3e103af249ab105ce3429d9d8bb2ac6c958c1091` |
| duckdb-fs | [#3](https://github.com/dullroar/duckdb-fs/pull/3) | `124a71d6966227e2314ce47a04a2e2d01aa91d10` |
| ffmpeg_mcp | [#2](https://github.com/dullroar/ffmpeg_mcp/pull/2) | `621326f8c483917c8d1ee908a4fdb06f94942968` |
| gpx_parser | [#2](https://github.com/dullroar/gpx_parser/pull/2) | `14899eba71f53d460d6fe7ec7f420bcdcd43d497` |
| lmdb-fs | [#3](https://github.com/dullroar/lmdb-fs/pull/3) | `d2d34150ba3cf7844f2af801d9159ce5480a0823` |
| metadata_driven_gx | [#2](https://github.com/dullroar/metadata_driven_gx/pull/2) | `c1b76ee38f14ec279fc8aeba3282c38eb335f490` |
| metadata_mcp | [#2](https://github.com/dullroar/metadata_mcp/pull/2) | `89fafb01edbb6930fa7b250dbb87d3f0f030288b` |
| pandoc_mcp | [#2](https://github.com/dullroar/pandoc_mcp/pull/2) | `1873896b9cbd4b07a113b7b07d6363cb5e458a78` |
| sample_parse | [#2](https://github.com/dullroar/sample_parse/pull/2) | `e3f043db056c74ff3e4b43aefa87dc80e7313580` |
| vips_mcp | [#2](https://github.com/dullroar/vips_mcp/pull/2) | `be6f9c394568abe515417d30517a77aad397da60` |

The hosted FUSE runs exposed a teardown permission difference. DuckDB commit `e0286fcb63d5fee0a685b3334b85179e49fb1921` and LMDB commit `d35caa20a7359ee92836968441efb4badc61756a` bounded teardown and let the mount-test container unmount. The LMDB write-denial check also verifies the kernel's read-only filesystem error. Both updated heads passed their full local Docker gates and their GitHub Docker jobs, including real mounts.
