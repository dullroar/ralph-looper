#!/usr/bin/env bash
# Record the commit of a deterministic-controls release tag in pins.tsv (next to this file).
# Run me when: a step or the operator must pin a new release of the shared controls library.
# Usage: pin.sh TAG   (CONTROLS_URL overrides the repository URL; used by tests)
set -euo pipefail
tag="${1:?usage: pin.sh TAG}"
url="${CONTROLS_URL:-https://github.com/dullroar/deterministic-controls}"
out="$(cd "$(dirname "$0")" && pwd)/pins.tsv"
sha="$(git ls-remote "$url" "refs/tags/$tag^{}" | cut -f1)"
[ -n "$sha" ] || sha="$(git ls-remote "$url" "refs/tags/$tag" | cut -f1)"
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { echo "pin.sh: tag $tag not found at $url" >&2; exit 1; }
[ -f "$out" ] || printf 'name\ttag\tcommit\n' > "$out"
awk -F'\t' -v t="$tag" '!($1 == "deterministic-controls" && $2 == t)' "$out" > "$out.tmp"
printf 'deterministic-controls\t%s\t%s\n' "$tag" "$sha" >> "$out.tmp"
mv "$out.tmp" "$out"
echo "pinned deterministic-controls $tag $sha"
