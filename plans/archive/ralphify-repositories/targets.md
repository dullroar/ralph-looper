# Repository-specific Docker gates

## Dependency review

The ten repos already have `AGENTS.md`, `CLAUDE.md`, `docs/`, `memory/`, `plans/`, `scripts/`, and the older context checkers. None has a tracked Dockerfile. Inspection found no Git submodules or sibling requirements in the tracked code and dependency manifests checked. Keep each repo's tests independent and verify that property from a standalone Docker build context.

- `duckdb-fs` documents a demo that reads `../metadata_driven_gx/environments/demo_weather/output`. Its tests use `tests/fixtures/demo_weather_output/`, a pinned copy of the twelve extractor CSVs. Use that local fixture for the Docker gates. A standalone Git snapshot reproduced one broken Markdown link, `../metadata_driven_gx` in `README.md`. The other nine standalone context checks passed. Fix the `duckdb-fs` link in step 01 with a repository URL or a local fixture link. Keep the producer/consumer demo as an optional example with an explicit input mount. Preserve summary/detail schema compatibility in both lanes. A future coordinated schema change would need a separate plan.
- `duckdb-fs` links to `lmdb-fs` for design lineage. Each has its own filesystem implementation, tests, and fixtures.
- `metadata_mcp` and `pandoc_mcp` both use the Pandoc executable and `pypandoc`. Install the executable and Python packages in each image. Each server runs from its own checkout.
- Template files and the runner executable are common read-only inputs. Docker, `/dev/fuse`, and agent quotas are shared host resources. Keep write paths and mount points separate.

## compliance_poc

Use the existing Python dependencies and `requirements-mcp.lock`. Preserve evaluator contracts, MCP transport checks, provider accounting, and protected suites. Run `python3 -m unittest discover -s tests -v` in Docker with live provider and local-model flags off. Check that the offline MCP stdio tests run. Preserve live opt-in instructions and repository spending rules. No credentials, provider API calls, or Ollama service are needed for the migration gate. Limit repo-specific edits to test environment and packaging support needed to reproduce the offline checks.

## duckdb-fs

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `DUCKDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify actual reads through the mounted filesystem using the committed GX fixture. Gate on a passing test with no mount-test skip. Keep the core test run device-free. Give the mount run its own disposable mountpoint and remove it on exit. Document `/dev/fuse` and the minimum container permissions that the tested host needs. Preserve the host CLI and output schema.

## ffmpeg_mcp

Install the repo's Python requirements and FFmpeg with `ffprobe`. Add a deterministic stdio test under `tests/`. Use the MCP client to initialize and list tools, then probe or convert a tiny synthetic input and assert a property of the result with `ffprobe`. Use temporary files. Document the stdio container command with stdin open and the test entry point. Preserve existing tool names and arguments.

## gpx_parser

Keep the stdlib-only package footprint and single-file CLI. Add an isolated CLI test under `tests/` using synthetic GPX. Exercise explicit-file and directory input. Assert CSV columns, rows, and representative distance or elevation values. Use a temporary working directory because the CLI writes `gpx_summary.csv` to the current directory. Preserve the existing sample output.

## lmdb-fs

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `LMDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify reads through the real mount over its generated test corpus and require a passing test with no mount-test skip. Apply the same device-free core test and disposable mount rules as `duckdb-fs`. Preserve the `tools/` entry points and host mount instructions.

## metadata_driven_gx

Install from `requirements.txt`. Run `python end_to_end.py --config-file configs/demo_weather.yaml` using the committed demo inputs and suites in a disposable copy in the container. Check the expected summary and detail CSVs and compare stable row counts, columns, and outcomes with the committed sample. Ignore only fields known to vary across runs, such as timestamps. Scope config or test support changes to the local demo. Preserve Databricks documentation, keep its runtime out of the Docker gate, and leave GX output contracts intact for consumers.

## metadata_mcp

Install ExifTool, Pandoc, and the existing Python requirements. Run `python3 -m unittest discover -s tests -v` and exercise the real binaries through a small stdio smoke if existing tests mock them. Verify a Pandoc semantic attribute and an ExifTool field from synthetic files. Keep real native commands on the required path and record any skips. Add test files under `tests/` as needed. Keep existing host entry points and metadata behavior.

## pandoc_mcp

Install Pandoc and the existing Python requirements. Add a stdio test under `tests/` that initializes, lists tools and formats, and converts an inline fixture to a different format. Assert actual converted content. Keep the documented stdio host entry point and any optional format requirements. Use local files for file conversion tests.

## sample_parse

Install the existing `.[dev]` extra and run `python -m pytest tests/` in Docker. Preserve `LEARNTHIS.md`, packaging, and the example entry point. Keep Docker-only adjustments to test and packaging support.

## vips_mcp

Install the libvips CLI and the existing Python requirements. Add a stdio test under `tests/` that initializes and uses a real image operation on a synthetic local image. Verify output dimensions or format using the native CLI. Document the stdio container command with stdin open. Preserve existing tool names and arguments.
