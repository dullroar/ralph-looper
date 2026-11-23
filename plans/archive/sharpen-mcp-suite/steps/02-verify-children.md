---
id: 02-verify-children
status: done
depends_on: [01-preflight]
touches:
  - plans/sharpen-mcp-suite/steps/02-verify-children.md
lane: none
gate: python3 plans/sharpen-mcp-suite/fanout.py verify && python3 scripts/check_context.py && git diff --check
evidence: gate passed 2026-11-23 (driver-verified)
claimed_by: codex cli-default
claimed_at: "2026-11-23T13:45:58Z"
---

# Verify the four child plan results

Run this step after operator dispatch succeeds. Run the read-only verifier, which checks the committed step states, the original gates, and the final Docker gate log for each recorded head. Independently review the per-tool test outcomes, removal of passthroughs, and real README examples and consuming-agent snippet. Record the four final plan SHAs, Docker results, backend versions, planned exceptions or open blockers, and UTC date below. Leave the gate intact.

## Results

Verified on 2026-11-23 UTC. The parent gate exited 0. The verifier matched
each final plan commit and Docker log checksum to the dispatch record. It
checked all five completed steps in each child against the original gates
and dependencies. The parent index, plan, link, secret, and whitespace
checks passed.

| Repository | Final plan commit | Recorded Docker result | Docker backend versions |
| --- | --- | --- | --- |
| `ffmpeg_mcp` | `5a92724ed463badf68f58dff7e358903e6d62302` | 22 tests passed | FFmpeg and ffprobe `5.1.9-0+deb12u1`, Python `3.12.16`, MCP `1.30.0`, Pydantic `2.14.4` |
| `gpx_mcp` | `1b954e093cead1ae2118c60e83b8c6aacd18c669` | 19 tests passed | gpxpy `1.6.2`, defusedxml `0.7.1`, GeographicLib `2.1`, Python `3.12.16`, MCP `1.26.0` |
| `metadata_mcp` | `ee55fa7b11503400fc403c5da8436e5a3c88fdb2` | 24 unit tests and the MCP stdio smoke test passed | ExifTool `12.76`, Pandoc `3.1.3`, Mutagen `1.48.1`, MCP `1.30.0` |
| `vips_mcp` | `7295d32a3f1dc8d5e6d69217ba0aae5f0f39cce4` | 18 tests passed | libvips `8.14.1` (`8.14.1-3+deb12u3`), pyvips `3.2.0`, Python `3.12.16`, MCP `1.30.0` |

Reviewed the test assertions, final Docker logs, and guides at these commits.
Each catalog method appears in the test sources and the tool reference.
Each README contains three valid JSON tool requests and the exact fenced
consuming-project `AGENTS.md` snippet from its final step.

- `ffmpeg_mcp` exposes 18 bounded tools. The tests reject
  `ffmpeg_passthrough` and check decoded properties for core and expanded
  workflows. The child ran the README requests over host and Docker stdio.
  They produced an MPEG program stream with MPEG-2 video and MP2 audio,
  a FLAC excerpt within 25 ms of 0.8 seconds, and a 480 × 180 PNG contact
  sheet. The older architecture notes still contain the retired passthrough
  premise. The current tool reference records the migration.
- `gpx_mcp` exposes 12 bounded tools. Its runtime requirements and imports
  use gpxpy with the standard library XML adapter. The legacy GPX parser
  is outside the runtime. The exact discovery test excludes raw backend
  calls. Stdio tests cover route and track measurements, segment rules,
  missing values, and CSV output. The child ran the README inspection,
  route aggregate, and summary CSV requests on both launchers. Format
  conversion, GIS export, and extension metrics remain outside the catalog.
  The MCP dependency emitted a `lifespan` warning during passing tests.
- `metadata_mcp` exposes 20 bounded tools. Exact discovery and closed-schema
  checks cover the typed replacements for raw metadata calls. The smoke test
  exercises the three README workflows. It scans folder copyright, reads
  Markdown attributes, and previews and applies a PNG edit. It verifies
  field provenance, preserves
  conflicting notices as present, and checks each separate scan status.
  Native read-back confirms the PNG notice, dimensions, and unchanged pixels.
  DOCX coverage remains incomplete in Docker because ExifTool lacks
  Archive::Zip. Text writes are limited to the supported Markdown or HTML
  copyright layouts. The child documents these limits and tests the error
  or incomplete states.
- `vips_mcp` exposes 24 bounded tools. The tests reject `vips_passthrough`
  and extra native arguments. They check decoded geometry, pixels, ICC
  handling, page selection, TIFF tags, and Deep Zoom layout. The child ran
  the README requests over host and Docker stdio. They produced a 240 × 120
  resize, ordered JPEG preview paths without writes, and a 120 × 120
  thumbnail. The backend notes defer optional codecs and document or
  vector rendering. Host evidence covers Linux.

All four child Docker gates passed. The documented backend limits leave
no open blocker for the parent verification.
