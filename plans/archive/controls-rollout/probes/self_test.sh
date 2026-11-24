#!/usr/bin/env bash
# Test the bypass probes in a disposable local repository. No network.
#
# Run me when: you change make_probe.sh or apply_probe.py, and before step 34.
#
# For each probe, the test makes the probe from a local repository and checks that the expected
# file change is in the probe commit. For the two secret probes it also checks that the pre-commit
# and the pre-push hooks block the push. It checks that the clone is outside REPOS_ROOT.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$here/../../.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/probe-selftest.XXXXXX")
trap 'rm -rf "$work"' EXIT
fail=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=1; }

src="$work/src"
mkdir -p "$src/.github/workflows" "$src/scripts" "$src/tests/fixtures/bad" "$src/tests/fixtures/good"
cp "$repo_root/scripts/secret_guard.py" "$repo_root/scripts/install_hooks.sh" "$src/scripts/"
cat > "$src/.github/workflows/context.yml" <<'EOF'
name: context
on:
  pull_request:
  push:
permissions:
  contents: read
jobs:
  context:
    runs-on: ubuntu-latest
    steps:
      - run: echo context
  controls:
    name: controls
    runs-on: ubuntu-latest
    steps:
      - run: echo controls
EOF
cat > "$src/controls.toml" <<'EOF'
schema_version = 1
profile = "ci"
checks = [
  "markdown.local-links",
  "security.secrets",
]
EOF
printf 'deterministic-controls @ git+https://example.invalid/controls.git@%s\n' \
  "3a2e9f3d95136958c54f73c831e84b971fc9a054" > "$src/scripts/controls-requirements.txt"
echo "broken" > "$src/tests/fixtures/bad/case.md"
echo "fine" > "$src/tests/fixtures/good/case.md"
git init --quiet "$src"
git -C "$src" add -A
git -C "$src" -c user.name=t -c user.email=t@example.invalid -c core.hooksPath=/dev/null commit --quiet -m base
base_head=$(git -C "$src" rev-parse HEAD)

# make <probe> [extra args]: set $clone and $out. The probe commit is HEAD of the clone.
make() {
  local probe=$1; shift
  out=$(PROBE_TMP="$work" PROBE_JOB=controls bash "$here/make_probe.sh" "$@" "$src" "$probe")
  clone=$(printf '%s\n' "$out" | sed -n 's/^clone: //p')
  [ -n "$clone" ] || { bad "$probe: no clone path in output"; return 1; }
}
at() { git -C "$clone" show "HEAD:$1" 2>/dev/null; }
changed() { git -C "$clone" diff --name-status HEAD~1 HEAD; }

for probe in secret-key env-file allow-blanket remove-controls-job rename-check continue-on-error \
             if-false path-filter remove-check-id swap-pin delete-fixture blanket-ignore; do
  if ! make "$probe"; then continue; fi
  if [ "$(git -C "$clone" rev-parse HEAD~1)" != "$base_head" ]; then bad "$probe: not one commit on the base"; continue; fi
  case "$probe" in
    secret-key)          at probe/synthetic_key.txt | grep -q '^api_key = sk-ant-[0-9a-f]\{48\}$' ;;
    env-file)            at .env | grep -q '^SERVICE_PASSWORD=.' ;;
    allow-blanket)       at .secret-guard-allow | grep -q '^\*  \*\*  ' ;;
    remove-controls-job) ! at .github/workflows/context.yml | grep -q '^  controls:' && at .github/workflows/context.yml | grep -q '^  context:' ;;
    rename-check)        at .github/workflows/context.yml | grep -q '^  controls-renamed:' && ! at .github/workflows/context.yml | grep -q '^  controls:' ;;
    continue-on-error)   at .github/workflows/context.yml | grep -A1 '^  controls:' | grep -q '^    continue-on-error: true$' ;;
    if-false)            at .github/workflows/context.yml | grep -A1 '^  controls:' | grep -q '^    if: false$' ;;
    path-filter)         at .github/workflows/context.yml | grep -A2 '^  pull_request:' | grep -q "^    paths:" ;;
    remove-check-id)     ! at controls.toml | grep -q 'markdown.local-links' && at controls.toml | grep -q 'security.secrets' ;;
    swap-pin)            ! at scripts/controls-requirements.txt | grep -q '3a2e9f3d95136958c54f73c831e84b971fc9a054' && at scripts/controls-requirements.txt | grep -q '@[0-9a-f]\{40\}$' ;;
    delete-fixture)      changed | grep -q '^D	tests/fixtures/bad/case.md$' ;;
    blanket-ignore)      at controls.toml | grep -q '^paths = \["\*\*"\]$' ;;
  esac && ok "$probe" || bad "$probe: expected change not found"
done

# The workflow probes must leave the other job alone.
make rename-check && { at .github/workflows/context.yml | grep -q '^  context:' && ok "rename-check keeps the other job" || bad "rename-check changed the other job"; }

# The path-filter probe also handles the inline form of "on".
inline="$work/inline"
mkdir -p "$inline/.github/workflows"
printf 'name: x\non: [push, pull_request]\njobs:\n  controls:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo\n' > "$inline/.github/workflows/x.yml"
python3 -I "$here/apply_probe.py" "$inline" path-filter >/dev/null
grep -q "paths:" "$inline/.github/workflows/x.yml" && ok "path-filter inline form" || bad "path-filter inline form"

# Hooks: the secret probes must be blocked by the pre-commit and the pre-push hook.
for probe in secret-key env-file; do
  make "$probe" --hooks || continue
  if printf '%s\n' "$out" | grep -q '^pre-commit: BLOCKED$' && printf '%s\n' "$out" | grep -q '^pre-push: BLOCKED$'; then
    ok "$probe blocked by both hooks"
  else
    bad "$probe: hooks did not block ($(printf '%s' "$out" | grep -E '^pre-(commit|push):' | tr '\n' ' '))"
  fi
done

# Refuse a clone under REPOS_ROOT.
if REPOS_ROOT="$work" PROBE_TMP="$work" bash "$here/make_probe.sh" "$src" env-file >/dev/null 2>&1; then
  bad "clone under REPOS_ROOT was allowed"
else
  ok "clone under REPOS_ROOT is refused"
fi

# Refuse an unknown probe. The source repository must stay unchanged.
if bash "$here/make_probe.sh" "$src" no-such-probe >/dev/null 2>&1; then bad "unknown probe was accepted"; else ok "unknown probe is refused"; fi
[ "$(git -C "$src" rev-parse HEAD)" = "$base_head" ] && [ -z "$(git -C "$src" status --porcelain)" ] && ok "source repository unchanged" || bad "source repository changed"

if [ "$fail" -ne 0 ]; then echo "probes self-test: FAILED"; exit 1; fi
echo "probes self-test: ok"
