#!/usr/bin/env python3
"""Dispatch and verify the four pinned MCP Ralph plans."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLAN = "sharpen-mcp"
REF = f"refs/heads/plan/{PLAN}"
TARGETS = {"ffmpeg_mcp", "gpx_mcp", "metadata_mcp", "vips_mcp"}
STEPS = (
    "01-backend-evidence", "02-tool-boundary", "03-core-workflows",
    "04-expanded-workflows", "05-docs-and-final-gate",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def environment_path(name):
    value = Path(os.environ[name])
    require(value.is_absolute() and value == value.resolve(), f"{name} must be an absolute canonical path")
    return value


def paths():
    root = environment_path("REPOS_ROOT")
    work = environment_path("RALPH_WORK")
    runner_repo = environment_path("RALPH_REPO")
    require(not (work.is_relative_to(root) or root.is_relative_to(work)
                 or work.is_relative_to(runner_repo) or runner_repo.is_relative_to(work)),
            "Use an external Ralph runtime directory")
    runner = runner_repo / "ralph-looper"
    require(runner.is_file() and os.access(runner, os.X_OK) and not any(c.isspace() for c in str(runner)),
            "Use an executable Bash runner at a path without whitespace")
    parser = runpy.run_path(str(runner_repo / "lib/pick_step.py"))["parse"]
    rows = [line.split("\t") for line in (HERE / "targets.tsv").read_text().splitlines()]
    require(len(rows) == len(TARGETS) and {name for name, _ in rows} == TARGETS,
            "Unexpected target manifest")
    repos = []
    for name, pin in rows:
        repo = root / name
        require(re.fullmatch(r"[0-9a-f]{40}", pin) and repo == repo.resolve(),
                f"{name}: invalid repository or plan pin")
        require(Path(git(repo, "rev-parse", "--show-toplevel")) == repo
                and Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")) == repo / ".git",
                f"{name}: expected a separate canonical checkout")
        files = git(repo, "ls-tree", "-r", "--name-only", pin, f"plans/{PLAN}").splitlines()
        expected = {f"plans/{PLAN}/steps/{step}.md" for step in STEPS}
        require(expected == {file for file in files if file.startswith(f"plans/{PLAN}/steps/")}
                and {f"plans/{PLAN}/{name}.md" for name in ("goal", "plan", "catalog", "spec")} <= set(files),
                f"{name}: pinned plan has unexpected files")
        for index, step in enumerate(STEPS):
            meta = step_metadata(parser, repo, pin, step)
            require(meta.get("id") == step and meta.get("status") == "pending" and meta.get("gate")
                    and meta.get("depends_on") == (list(STEPS[index - 1:index]) if index else []),
                    f"{name}: invalid pinned step {step}")
        repos.append((repo, pin))
    return work, runner, parser, repos


def step_metadata(parser, repo, commit, step):
    return parser(git(repo, "show", f"{commit}:plans/{PLAN}/steps/{step}.md"))


def evidence(repo, pin, work, parser):
    sha = git(repo, "rev-parse", "--verify", REF)
    subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", pin, sha], check=True)
    for step in STEPS:
        actual = step_metadata(parser, repo, sha, step)
        original = step_metadata(parser, repo, pin, step)
        require(actual.get("id") == step and actual.get("status") == "done"
                and actual.get("gate") == original.get("gate")
                and actual.get("depends_on") == original.get("depends_on")
                and re.fullmatch(r"gate passed \d{4}-\d{2}-\d{2} \(driver-verified\)",
                                 actual.get("evidence", "")),
                f"{repo.name}: {step} lacks unchanged, driver-verified evidence")
    log = work / repo.name / PLAN / "logs/gate-05-docs-and-final-gate.out"
    output = log.read_bytes()
    require(output.strip(), f"{repo.name}: missing final Docker output")
    return {"pin": pin, "sha": sha, "log_sha256": hashlib.sha256(output).hexdigest()}


def verify(repo, pin, work, parser, path):
    actual = evidence(repo, pin, work, parser)
    require(json.loads(path.read_text()) == actual, f"{repo.name}: stale or unrecorded result")
    return actual["sha"]


def save(path, value):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as file:
        draft = Path(file.name)
        try:
            json.dump(value, file)
            file.flush()
            os.fsync(file.fileno())
            os.replace(draft, path)
        finally:
            draft.unlink(missing_ok=True)


def run_child(repo, pin, work, runner, parser, state, agent, lease):
    result = state / f"{repo.name}.json"
    if result.exists():
        return f"{repo.name}: reused {verify(repo, pin, work, parser, result)}"
    seed = state / "seeds" / repo.name
    require(seed.resolve() == seed, f"{repo.name}: substituted seed path")
    if seed.exists():
        require(git(seed, "rev-parse", "HEAD") == pin
                and Path(git(seed, "rev-parse", "--path-format=absolute", "--git-common-dir")) == repo / ".git"
                and not git(seed, "status", "--porcelain"), f"{repo.name}: unexpected seed worktree")
    else:
        existing = git(repo, "for-each-ref", "--format=%(refname)", REF, f"refs/heads/step/{PLAN}")
        require(not existing and not (work / repo.name / PLAN).exists(),
                f"{repo.name}: unknown prior child branch or runtime")
        seed.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "add", "--detach", str(seed), pin)
    env_keys = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR",
                "DOCKER_HOST", "DOCKER_CONTEXT", "SSL_CERT_FILE", "SSL_CERT_DIR")
    env = {key: os.environ[key] for key in env_keys if key in os.environ}
    env.update(RALPH_WORK=str(work), GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    if override := os.environ.get("MCP_CHILD_AGENT_CMD"):
        env["AGENT_CMD"] = override
    print(f"{repo.name}: starting or resuming", flush=True)
    with (state / f"{repo.name}.out").open("ab") as log:
        child = subprocess.run(
            [str(runner), "--repo", str(seed), "--plan", PLAN, "--agent", agent,
             "--jobs", "1", "--on-limit", "handoff"], check=False, env=env, pass_fds=(lease,),
            stdout=log, stderr=subprocess.STDOUT,
        )
    require(child.returncode == 0, f"{repo.name}: Ralph exit {child.returncode}. See {repo.name}.out")
    data = evidence(repo, pin, work, parser)
    save(result, data)
    return f"{repo.name}: verified {data['sha']}"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("ready", "run", "verify"))
    cli.add_argument("--agent", choices=("codex", "claude", "copilot"))
    cli.add_argument("--jobs", type=int, default=4)
    args = cli.parse_args()
    work, runner, parser, repos = paths()
    state = work / "ralph-looper/sharpen-mcp-suite/children"
    require(state == state.resolve(), "Substituted child state directory")
    if args.action == "ready":
        subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], check=True)
        for repo, pin in repos:
            print(f"{repo.name}: ready at {pin}")
        return 0
    if args.action == "verify":
        for repo, pin in repos:
            sha = verify(repo, pin, work, parser, state / f"{repo.name}.json")
            print(f"{repo.name}: verified {sha}")
        return 0

    require(args.agent and 1 <= args.jobs <= len(repos), "Specify an agent and use one to four jobs")
    state.mkdir(parents=True, mode=0o700, exist_ok=True)
    errors = 0
    with (state / "dispatch.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(run_child, repo, pin, work, runner, parser, state, args.agent, lock.fileno())
                for repo, pin in repos
            ]
            for future in futures:
                try:
                    print(future.result(), flush=True)
                except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                    print(exc, file=sys.stderr, flush=True)
                    errors += 1
    return int(errors != 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"MCP fan-out: {exc}", file=sys.stderr)
        sys.exit(1)
