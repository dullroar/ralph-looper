#!/usr/bin/env bash
# Create a bypass probe branch in a temporary clone and print the push command for the operator.
#
# Run me when: the operator tests that a producer cannot get around a required check (step 34).
#
# Usage: make_probe.sh [--hooks] <repo> <probe>
#   <repo>   OWNER/NAME (cloned from GitHub), a clone URL or a local Git path
#   <probe>  secret-key env-file allow-blanket remove-controls-job rename-check continue-on-error
#            if-false path-filter remove-check-id swap-pin delete-fixture blanket-ignore
#   --hooks  also test the local hooks: install them in the clone, try the commit and try a push
#            to a local bare repository. Needs scripts/install_hooks.sh in the repository.
# Environment: PROBE_TMP (parent for the clone), PROBE_JOB, PROBE_ALT_COMMIT (see apply_probe.py),
#              REPOS_ROOT (the clone must not be under it).
#
# The clone is always new and always outside $REPOS_ROOT. The script never pushes. It makes the
# probe commit with hooks off, so that the commit exists. The operator pushes it and reads the CI result.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
hooks=0
if [ "${1:-}" = "--hooks" ]; then hooks=1; shift; fi
if [ $# -ne 2 ]; then sed -n '2,16p' "${BASH_SOURCE[0]}" >&2; exit 2; fi
repo=$1
probe=$2

case "$probe" in
  secret-key|env-file|allow-blanket|remove-controls-job|rename-check|continue-on-error|if-false|path-filter|remove-check-id|swap-pin|delete-fixture|blanket-ignore) ;;
  *) echo "make_probe: unknown probe '$probe'" >&2; exit 2 ;;
esac

if [ -d "$repo" ]; then src=$(cd "$repo" && pwd)
elif [[ "$repo" == *://* || "$repo" == git@* ]]; then src=$repo
elif [[ "$repo" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]; then src="https://github.com/$repo.git"
else echo "make_probe: cannot read <repo> '$repo'" >&2; exit 2; fi

parent=$(mktemp -d "${PROBE_TMP:-${TMPDIR:-/tmp}}/probe.XXXXXX")
parent=$(cd "$parent" && pwd -P)
if [ -n "${REPOS_ROOT:-}" ]; then
  root_real=$(cd "$REPOS_ROOT" && pwd -P)
  case "$parent/" in
    "$root_real"/*) echo "make_probe: the clone must be outside REPOS_ROOT" >&2; exit 2 ;;
  esac
fi

clone="$parent/clone"
git clone --quiet --no-hardlinks "$src" "$clone"
branch="probe/$probe-$(date -u +%Y%m%d%H%M%S)"
git -C "$clone" checkout --quiet -b "$branch"

changes=$(python3 -I "$here/apply_probe.py" "$clone" "$probe")
echo "$changes"
git -C "$clone" add -A

gitc=(git -C "$clone" -c user.name=probe -c user.email=probe@example.invalid -c core.hooksPath=/dev/null)

if [ "$hooks" -eq 1 ]; then
  if [ ! -f "$clone/scripts/install_hooks.sh" ]; then
    echo "make_probe: --hooks needs scripts/install_hooks.sh in the repository" >&2; exit 2
  fi
  (cd "$clone" && bash scripts/install_hooks.sh >/dev/null)
  if git -C "$clone" -c user.name=probe -c user.email=probe@example.invalid commit --quiet -m "probe: $probe" >/dev/null 2>&1; then
    echo "pre-commit: NOT BLOCKED"
    precommit=open
  else
    echo "pre-commit: BLOCKED"
    precommit=blocked
  fi
  "${gitc[@]}" commit --quiet --no-verify -m "probe: $probe" 2>/dev/null || true
  git init --quiet --bare "$parent/sink.git"
  git -C "$clone" remote add probe-sink "$parent/sink.git"
  if git -C "$clone" -c user.name=probe -c user.email=probe@example.invalid push --quiet probe-sink "$branch" >/dev/null 2>&1; then
    echo "pre-push: NOT BLOCKED"
  else
    echo "pre-push: BLOCKED"
  fi
  git -C "$clone" remote remove probe-sink
  : "$precommit"
else
  "${gitc[@]}" commit --quiet --no-verify -m "probe: $probe"
fi

echo "probe: $probe"
echo "clone: $clone"
echo "branch: $branch"
echo "Operator: push the branch and watch CI. Close the pull request and delete the branch after the test."
echo "  git -C \"$clone\" push origin \"$branch\""
