#!/usr/bin/env python3
"""Seed, run, and verify the allowlisted Ralph migration on a Bash host."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import csv
import datetime
import fcntl
from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).resolve().parent
PLAN_PATH = "plans/ralphify"
SEED_REF = "refs/heads/rollout/ralphify"
PLAN_REF = "refs/heads/plan/ralphify"
TEMPLATE_REV = "126277f5b34027bc3766b4ae0804746f90dce959"
RUNNER_REV = "0a1c8b6fdbe79e5e182206ce99e10bad007d1aba"
STEPS = {
    "01-adopt-context": (
        "python3 scripts/build_indexes.py --check && python3 scripts/check_context.py"
        " && git diff --check"
    ),
    "02-build-and-test": (
        "bash scripts/test_docker.sh && python3 scripts/check_context.py && git diff --check"
    ),
    "03-verify-integration": (
        "python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check"
    ),
}
LINKS = ("https://github.com/dullroar/repo-template", "https://github.com/dullroar/ralph-looper")
SCAFFOLD = (
    ".github/workflows/context.yml", ".gitignore", "AGENTS.md", "CLAUDE.md", "Dockerfile",
    "docs/README.md", "memory/AGENTS.md", "plans/AGENTS.md",
    "plans/for-each-plan/goal.md", "plans/for-each-plan/plan.md",
    "plans/for-each-plan/steps/00-step-template.md", "scripts/AGENTS.md",
    "scripts/build_indexes.py", "scripts/check_context.py", "scripts/check_links.py",
    "scripts/check_plan.py", "scripts/ctx_common.py", "scripts/scan_secrets.py",
)
REQUIRED_RESULT_FILES = (
    "AGENTS.md", "CLAUDE.md", "README.md", "Dockerfile", ".dockerignore",
    ".github/workflows/context.yml", "docs/README.md", "memory/AGENTS.md",
    "plans/AGENTS.md", "plans/for-each-plan/goal.md", "plans/for-each-plan/plan.md",
    "plans/for-each-plan/steps/00-step-template.md", "scripts/AGENTS.md",
    "scripts/build_indexes.py", "scripts/check_context.py", "scripts/test_docker.sh",
)
RUNTIME_ENV = (
    "PATH", "HOME", "USERPROFILE", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR", "DOCKER_HOST",
    "DOCKER_CONTEXT", "SSL_CERT_FILE", "SSL_CERT_DIR",
)
CHILD_OVERRIDES = ("AGENT_CMD", "STEP_TIMEOUT_MIN", "GATE_TIMEOUT_MIN", "MAX_USD", "MAX_ATTEMPTS")
FUSE_REPOS = {"duckdb-fs", "lmdb-fs"}
# The owner approved one offline test correction after the Docker gate stopped.
# Keep the original stop and requeue commits in history.
COMPLIANCE_REPAIR_HISTORY = (
    "c1111e14bab4addbd5c4f747d709597ce6379d7f",
    "6dc07712efc662d1521c83f15b1d6cff209a1ad0",
    "61016ab3f6dc2265c52e9f4de8d32e02e8f77a9a",
)


class RolloutError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise RolloutError(message)


def git(repo, *args, allow_missing=False):
    # Explicit paths select the repo even when the caller runs inside a Git hook.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], env=env, capture_output=True, check=False
    )
    if allow_missing and proc.returncode == 1:
        return None
    require(proc.returncode == 0, f"{repo.name}: git {args[0]} failed\n{proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git_text(repo, *args, **kwargs):
    output = git(repo, *args, **kwargs)
    return output.decode().strip() if output is not None else None


def ref(repo, name):
    return git_text(repo, "rev-parse", "--verify", "--quiet", name, allow_missing=True)


def sections(path):
    parts = re.split(r"^## ([^\n]+)\n", path.read_text(), flags=re.MULTILINE)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def targets():
    with (HERE / "targets.tsv").open(newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    require(rows and all(
        set(row) == {"repo", "base"}
        and re.fullmatch(r"[a-z][a-z0-9_-]*", row["repo"] or "")
        and row["base"] in {"main", "master"} for row in rows
    ), "Invalid target allowlist")
    allowlist = {row["repo"]: row["base"] for row in rows}
    require(len(allowlist) == len(rows), "Duplicate target in allowlist")
    return allowlist


def canonical_path(value, label):
    path = Path(value)
    require(path.is_absolute() and path == path.resolve(), f"{label} must be an absolute, canonical path")
    return path


def external_path(path, forbidden):
    require(not any(path.is_relative_to(root) or root.is_relative_to(path) for root in forbidden),
            f"{path} overlaps a repository or another runtime directory")
    ancestor = next(parent for parent in (path, *path.parents) if parent.is_dir())
    probe = subprocess.run(
        ["git", "-C", str(ancestor), "rev-parse", "--is-inside-work-tree", "--is-inside-git-dir"],
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
        capture_output=True, text=True, check=False,
    )
    require("true" not in probe.stdout.splitlines(), f"{path} must be outside Git checkouts")


def env_path(name):
    value = os.environ.get(name)
    require(value, f"Set and export {name}")
    return canonical_path(value, name)


def git_identity(repo):
    require(repo.is_dir() and repo.resolve() == repo, f"Missing or substituted checkout: {repo}")
    top = git_text(repo, "rev-parse", "--show-toplevel")
    require(Path(top) == repo, f"{repo}: expected a checkout at this path")
    return git_text(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")


def atomic_json(path, data):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        draft = Path(stream.name)
        try:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(draft, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            draft.unlink(missing_ok=True)


@contextlib.contextmanager
def locked(path):
    with path.open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RolloutError(f"Run already active: {path}") from exc
        yield stream.fileno()
        # A child may still hold this file description after its supervisor exits.
        # Close our copy instead of unlocking the description explicitly.


def pinned_file(repo, revision, path):
    return git(repo, "show", f"{revision}:{path}")


def load_inputs(template, runner):
    git_identity(template)
    git_identity(runner.parent)
    require(runner.name == "ralph-looper" and os.access(runner, os.X_OK)
            and not any(char.isspace() for char in str(runner)), "Invalid Bash runner path")
    runner_paths = ("ralph-looper", "lib/agents.sh", "lib/pick_step.py", "lib/PROMPT.md", "lib/usage.py")
    for path in runner_paths:
        file = runner.parent / path
        require(file.resolve() == file and file.read_bytes() == pinned_file(runner.parent, RUNNER_REV, path),
                f"Runner file differs from the pinned revision: {path}")
    return {path: pinned_file(template, TEMPLATE_REV, path) for path in SCAFFOLD}


def seed_files(name, base, repo, base_sha, inputs):
    contract = sections(HERE / "child-plan.md")
    brief = sections(HERE / "targets.md")[name]
    seed_dir = HERE / "seeds"
    seed = {}
    for path in ("goal.md", "plan.md", "spec.md"):
        seed[path] = (seed_dir / f"{path}.in").read_text().replace("@REPO@", name).replace(
            "@BASE@", base
        ).replace("@TEMPLATE_REV@", TEMPLATE_REV).encode()
    for path, data in inputs.items():
        seed[f"template-inputs/{path}.txt"] = data

    context = [
        "AGENTS.md", "CLAUDE.md", "docs/README.md", "memory/README.md", "memory/AGENTS.md",
        "plans/AGENTS.md", "plans/TEMPLATE/**", "plans/for-each-plan/**",
        "plans/archive/legacy-template/**", ".github/workflows/context.yml",
        "scripts/README.md", "scripts/AGENTS.md", "scripts/build_indexes.py",
        "scripts/build_context_indexes.py", "scripts/check_context.py", "scripts/check_links.py",
        "scripts/check_plan.py", "scripts/ctx_common.py", "scripts/scan_context_secrets.py",
        "scripts/scan_secrets.py",
    ]
    tracked = git_text(repo, "ls-tree", "-r", "--name-only", base_sha).splitlines()
    if name == "duckdb-fs":
        context.append("README.md")
    for path in tracked:
        if not path.endswith(".md") or path.startswith(("plans/TEMPLATE/", "plans/archive/")):
            continue
        data = pinned_file(repo, base_sha, path)
        if any(item in data for item in (b"plans/TEMPLATE", b"memory/README.md", b"scripts/README.md")):
            context.append(path)

    docker = ["Dockerfile", ".dockerignore", "README.md", "scripts/test_docker.sh",
              "scripts/AGENTS.md", ".github/workflows/context.yml"]
    if name in {"ffmpeg_mcp", "gpx_parser", "metadata_mcp", "pandoc_mcp", "vips_mcp", "metadata_driven_gx"}:
        docker.append("tests/**")
    if name == "metadata_driven_gx":
        docker.append("configs/demo_weather.yaml")
    previous = []
    for index, ((step, gate), paths) in enumerate(zip(STEPS.items(), (context, docker, [])), 1):
        file = f"steps/{step}.md"
        touched = dict.fromkeys([*paths, f"{PLAN_PATH}/{file}"])
        allowed = "\n".join(f"  - {path}" for path in touched)
        body = contract[f"{step} (R{index})"]
        if index == 1:
            body += f"\n\nUse `{base}` as the workflow base branch. Copy the pinned inputs from "
            body += "`plans/ralphify/template-inputs/`. Remove the final `.txt` suffix on copy."
            if name == "duckdb-fs":
                body += "\n\nFix the standalone README link to the GX repo in this step."
        if index >= 2:
            body += f"\n\n## Repository gate\n\n{brief}"
        if index == 3:
            body += "\n\n" + (seed_dir / "verification.md.in").read_text().strip()
        seed[file] = (
            f"---\nid: {step}\nstatus: pending\ndepends_on: [{', '.join(previous)}]\n"
            f"touches:\n{allowed}\nlane: none\nrequirements: [R{index}]\ngate: {gate}\n"
            f'evidence: ""\n---\n\n# {step}\n\n{body}\n'
        ).encode()
        previous = [step]
    return {f"{PLAN_PATH}/{path}": data for path, data in seed.items()}


def worktrees(repo):
    entries = git_text(repo, "worktree", "list", "--porcelain").split("\n\n")
    return {block.splitlines()[0][9:]: block.splitlines() for block in entries}


def seed_matches(repo, sha, base_sha, files):
    changed = set(git_text(repo, "diff", "--name-only", base_sha, sha).splitlines())
    return (
        git_text(repo, "rev-list", "--parents", "-n", "1", sha) == f"{sha} {base_sha}"
        and changed == files.keys()
        and all(pinned_file(repo, sha, path) == data for path, data in files.items())
    )


def preflight(root, state, work, allowlist, manifest):
    known = manifest.get("targets", {})
    require(not set(known) - allowlist.keys(), "State contains an unknown target")
    identities = set()
    for name, base in allowlist.items():
        repo = root / name
        identity = git_identity(repo)
        require(identity not in identities, f"{name}: duplicate Git common directory")
        require(Path(identity).resolve() == repo / ".git",
                f"{name}: canonical target checkout must own its Git directory")
        identities.add(identity)
        require(not git_text(repo, "status", "--porcelain", "--untracked-files=all"),
                f"{name}: target checkout has uncommitted changes")
        sha = ref(repo, f"refs/heads/{base}")
        require(sha, f"{name}: missing base branch {base}")
        require(not git_text(repo, "ls-tree", sha, "--", PLAN_PATH),
                f"{name}: base already contains the rollout plan directory")
        seed_dir = state / "seeds" / name
        runtime = work / name / "ralphify"
        require(not state.is_relative_to(runtime) and not runtime.is_relative_to(state),
                f"{name}: child runtime overlaps rollout state")
        require(seed_dir.resolve() == seed_dir and runtime.resolve() == runtime,
                f"{name}: substituted worktree or runtime path")
        row = known.get(name)
        if row is None:
            require(not ref(repo, SEED_REF) and not ref(repo, PLAN_REF)
                    and not seed_dir.exists() and not runtime.exists()
                    and not git_text(repo, "branch", "--list", "step/ralphify/*"),
                    f"{name}: an existing rollout branch or worktree has no recorded provenance")
            continue
        require(row["repo"] == str(repo) and row["identity"] == identity
                and row["base"] == base and row["base_sha"] == sha
                and row["seed_dir"] == str(seed_dir) and row["runtime"] == str(runtime),
                f"{name}: recorded checkout, worktree, or base has changed")
        seed_sha = ref(repo, SEED_REF)
        if row["seed_sha"] is not None:
            require(seed_sha == row["seed_sha"], f"{name}: seed branch has changed")
        if seed_dir.exists():
            require(git_identity(seed_dir) == identity
                    and git_text(seed_dir, "symbolic-ref", "HEAD") == SEED_REF
                    and str(seed_dir) in worktrees(repo), f"{name}: unexpected seed worktree")
        plan_sha = ref(repo, PLAN_REF)
        require(not plan_sha or (
            row["seed_sha"] is not None and is_ancestor(repo, row["seed_sha"], plan_sha)
        ), f"{name}: unexpected child plan branch")
        if row["status"] in {"preparing", "seeded"}:
            require(not plan_sha and not runtime.exists(), f"{name}: unexpected child run before dispatch")
        require(not row.get("final_sha") or row["final_sha"] == plan_sha,
                f"{name}: completed plan branch has changed")


def is_ancestor(repo, ancestor, commit):
    return git(repo, "merge-base", "--is-ancestor", ancestor, commit, allow_missing=True) is not None


def seed_target(row, files, runner, env):
    repo = Path(row["repo"])
    tree = Path(row["seed_dir"])
    base_sha = row["base_sha"]
    seed_sha = ref(repo, SEED_REF)
    if not tree.exists():
        # A successful worktree add updates the registration and creates the branch together.
        require(seed_sha is None and str(tree) not in worktrees(repo),
                f"{repo.name}: seed worktree is missing or registered elsewhere")
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "add", "-b", "rollout/ralphify", str(tree), base_sha)
        seed_sha = base_sha
    require(git_identity(tree) == row["identity"] and git_text(tree, "symbolic-ref", "HEAD") == SEED_REF,
            f"{repo.name}: seed worktree identity changed")

    if seed_sha == base_sha:
        staged = set(git_text(tree, "diff", "--cached", "--name-only", base_sha).splitlines())
        untracked = set(git_text(tree, "ls-files", "--others", "--exclude-standard").splitlines())
        require(not git_text(tree, "diff", "--name-only") and (staged | untracked) <= files.keys(),
                f"{repo.name}: unexpected edits in unfinished seed")
        for path, data in files.items():
            dest = tree / path
            require(dest.resolve() == dest, f"{repo.name}: substituted seed path {path}")
            if dest.exists():
                partial = dest.read_bytes()
                require(partial == data, f"{repo.name}: divergent unfinished seed file {path}")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=tree.parent, delete=False) as stream:
                    draft = Path(stream.name)
                    try:
                        stream.write(data)
                        stream.flush()
                        os.replace(draft, dest)
                    finally:
                        draft.unlink(missing_ok=True)
        validate_seed(tree, runner, env)
        git(tree, "add", "--", *files)
        git(tree, "commit", "-m", "Seed Ralph migration plan", "--", *files)
        seed_sha = ref(repo, SEED_REF)
    require(seed_matches(repo, seed_sha, base_sha, files), f"{repo.name}: seed commit is unfamiliar")
    require(not git_text(tree, "status", "--porcelain", "--untracked-files=all"),
            f"{repo.name}: seed worktree is dirty")
    row["seed_sha"] = seed_sha
    if row["status"] == "preparing":
        row["status"] = "seeded"


def validate_seed(tree, runner, env):
    context = subprocess.run(
        [sys.executable, "-B", "scripts/check_context.py"],
        cwd=tree, env=env, capture_output=True, text=True, check=False,
    )
    if context.returncode:
        # This exact standalone failure predates the seed and is a step 01 repair.
        known = {"BROKEN README.md: ../metadata_driven_gx", "ok   build_context_indexes.py",
                 "ok   check_plan.py", "FAIL check_links.py", "ok   scan_context_secrets.py",
                 "plans/ralphify: 01-adopt-context=ready, 02-build-and-test=waiting,"
                 " 03-verify-integration=waiting"}
        require(tree.name == "duckdb-fs" and context.returncode == 1 and not context.stderr.strip()
                and set(context.stdout.splitlines()) == known,
                f"{tree.name}: seed failed the current context gate\n{context.stdout}{context.stderr}")
    command = [
        sys.executable, "-I", str(runner.parent / "lib/pick_step.py"), "ready",
        str(tree / PLAN_PATH), "--max", "3",
    ]
    ready = subprocess.check_output(command, cwd=tree, env=env, text=True)
    require([json.loads(line)["id"] for line in ready.splitlines()] == [next(iter(STEPS))],
            f"{tree.name}: runner did not select the first child step")
    require({file.stem for file in (tree / PLAN_PATH / "steps").glob("*.md")} == STEPS.keys(),
            f"{tree.name}: child seed has missing or unexpected steps")


def child_environment(work):
    env = {key: os.environ[key] for key in RUNTIME_ENV if key in os.environ}
    env.update(RALPH_WORK=str(work), GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    for key in CHILD_OVERRIDES:
        if value := os.environ.get(f"RALPH_CHILD_{key}"):
            env[key] = value
    return env


def validate_driver_state(row):
    repo = Path(row["repo"])
    worktrees_by_path = worktrees(repo)
    root = Path(row["runtime"]) / "worktrees"
    plan_sha = ref(repo, PLAN_REF)
    if (root / "_plan").exists():
        entry = worktrees_by_path.get(str(root / "_plan"), [])
        require(f"branch {PLAN_REF}" in entry and git_identity(root / "_plan") == row["identity"],
                f"{repo.name}: unexpected driver plan worktree")
    expected = {"_plan", *STEPS}
    paths = {item.name for item in root.iterdir()} if root.is_dir() else set()
    require(paths <= expected, f"{repo.name}: unexpected entry in driver worktrees")
    steps = git_text(repo, "for-each-ref", "--format=%(refname)", "refs/heads/step/ralphify").splitlines()
    for name in steps:
        step = name.removeprefix("refs/heads/step/ralphify/")
        require(step in STEPS, f"{repo.name}: unexpected driver branch {name}")
        sha = ref(repo, name)
        require(is_ancestor(repo, row["seed_sha"], sha), f"{repo.name}: foreign driver branch {name}")
        entry = worktrees_by_path.get(str(root / step), [])
        if not entry:
            require(plan_sha and is_ancestor(repo, sha, plan_sha),
                    f"{repo.name}: unmerged driver branch has no worktree: {name}")
        else:
            require(f"branch {name}" in entry and git_identity(root / step) == row["identity"],
                    f"{repo.name}: unexpected driver step worktree {step}")
    for path in paths - {"_plan"}:
        require(f"refs/heads/step/ralphify/{path}" in steps,
                f"{repo.name}: unexpected driver step directory {path}")


def front_matter(data):
    lines = data.splitlines()
    require(lines and lines[0] == "---" and "---" in lines[1:], "Invalid child step front matter")
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        if key := re.match(r"^(\w+):\s*(.*)$", line):
            name, value = key.groups()
            require(name not in fields, f"Duplicate child step field: {name}")
            fields[name] = value.strip('"\'')
    return fields, "\n".join(lines[end + 1:])


def verification_notes(body, repo_name):
    if "\n## Results\n" not in body:
        raise RolloutError(f"{repo_name}: missing committed verification results")
    content = body.split("\n## Results\n", 1)[1].split("\n## ", 1)[0]
    fields = ("Base commit", "Commands", "Docker build", "Tests", "Skips", "FUSE", "UTC date")
    expected = "|".join(fields)
    entries = re.findall(rf"^- ({expected}):[ \t]+([^\n]+(?:\n[ \t]+[^\n]+)*)$", content, re.MULTILINE)
    notes = {field: " ".join(part.strip() for part in value.splitlines()) for field, value in entries}
    require(len(entries) == len(fields) and set(notes) == set(fields)
            and all(value.strip() and "PENDING" not in value for value in notes.values()),
            f"{repo_name}: incomplete committed verification notes")
    base = re.match(r"^(?P<tick>`?)(?P<sha>[0-9a-f]{64}|[0-9a-f]{40})(?P=tick)(?=$|[\s.,])",
                    notes["Base commit"])
    def passed(field):
        return re.match(r"^PASS\b[. :–—-]*\s+\S", notes[field])

    require(base
            and "scripts/test_docker.sh" in notes["Commands"]
            and passed("Docker build") and passed("Tests")
            and (passed("FUSE") if repo_name in FUSE_REPOS else notes["FUSE"].rstrip(".") == "n/a"),
            f"{repo_name}: committed verification notes do not show the required results")
    notes["Base commit"] = base["sha"]
    notes["UTC date"] = notes["UTC date"].rstrip(".")
    datetime.date.fromisoformat(notes["UTC date"])
    return notes


def has_contract_link(contract, url):
    target = re.escape(url) + r"/?"
    if re.search(r"\[[^\]\n]+\]\(" + target + r"\)", contract):
        return True
    references = re.findall(r"^\[([^\]\n]+)\]:[ \t]+" + target + r"[ \t]*$", contract, re.MULTILINE)
    return any(re.search(r"\[[^\]\n]+\]\[" + re.escape(label) + r"\]", contract, re.IGNORECASE)
               for label in references)


def inspect_result(row, repo_name, sha):
    repo = Path(row["repo"])
    require(sha and is_ancestor(repo, row["seed_sha"], sha),
            f"{repo_name}: final branch does not descend from the seed")
    tracked = set(git_text(repo, "ls-tree", "-r", "--name-only", sha).splitlines())
    require(set(REQUIRED_RESULT_FILES) <= tracked,
            f"{repo_name}: missing required files: {', '.join(sorted(set(REQUIRED_RESULT_FILES) - tracked))}")
    contract = pinned_file(repo, sha, "AGENTS.md").decode()
    for link in LINKS:
        require(has_contract_link(contract, link),
                f"{repo_name}: missing AGENTS.md link to {link}")

    expected_steps = {f"{PLAN_PATH}/steps/{step}.md" for step in STEPS}
    require({path for path in tracked if path.startswith(f"{PLAN_PATH}/steps/") and path.endswith(".md")}
            == expected_steps, f"{repo_name}: unexpected set of committed steps")
    history = git_text(repo, "rev-list", "--first-parent", "--reverse", f"{row['seed_sha']}..{sha}")
    merges = history.splitlines()
    repair = None
    if repo_name == "compliance_poc" and tuple(merges[1:4]) == COMPLIANCE_REPAIR_HISTORY:
        repair = merges[3]
        changed = git(repo, "diff", "--name-only", "--no-renames", "-z", merges[0], repair)
        require(changed == b"tests/test_openai_cost_estimator.py\0",
                f"{repo_name}: approved recovery changed unexpected files")
        merges = [merges[0], *merges[4:]]
    require(len(merges) == len(STEPS), f"{repo_name}: missing or unexpected driver merges")
    base = row["seed_sha"]
    for (step, gate), merge in zip(STEPS.items(), merges):
        if repair and step == "02-build-and-test":
            base = repair
        path = f"{PLAN_PATH}/steps/{step}.md"
        actual, body = front_matter(pinned_file(repo, sha, path).decode())
        source = pinned_file(repo, row["seed_sha"], path).decode()
        original, _ = front_matter(source)
        require(actual.get("id") == step and actual.get("status") == "done"
                and actual.get("gate") == original.get("gate") == gate
                and actual.get("depends_on") == original.get("depends_on")
                and re.fullmatch(r"gate passed \d{4}-\d{2}-\d{2} \(driver-verified\)",
                                 actual.get("evidence", "")),
                f"{repo_name}: {step} has no valid driver result")
        parents = git_text(repo, "rev-list", "--parents", "-n", "1", merge).split()
        require(len(parents) == 3 and parents[1] == base
                and git_text(repo, "show", "-s", "--format=%s", merge) == f"plan(ralphify): merge {step}",
                f"{repo_name}: {step} is missing its expected driver merge")
        scope = source.split("\nlane:", 1)[0].split("\ntouches:\n", 1)[1]
        patterns = [line.removeprefix("  - ") for line in scope.splitlines()]
        changed = git(repo, "diff", "--name-only", "--no-renames", "-z", base, merge).decode()
        outside = [path for path in changed.split("\0") if path and
                   not any(fnmatchcase(path, pattern) for pattern in patterns)]
        require(not outside, f"{repo_name}: {step} changed files outside touches: {', '.join(outside)}")
        if step == "03-verify-integration":
            last = verification_notes(body, repo_name)
            require(last["Base commit"] == base,
                    f"{repo_name}: verification notes identify a different integration base")
        base = merge
    log = Path(row["runtime"]) / "logs" / "gate-03-verify-integration.out"
    require(log.is_file() and log.resolve() == log, f"{repo_name}: missing final driver gate log")
    data = log.read_bytes()
    require(data.strip(), f"{repo_name}: final driver gate log is empty")
    return {"path": str(log), "sha256": hashlib.sha256(data).hexdigest(), "notes": last}


def verify_target(name, row):
    repo = Path(row["repo"])
    sha = row.get("final_sha")
    require(row["status"] == "done" and row.get("exit_code") == 0 and sha,
            f"{name}: no recorded completed run")
    require(ref(repo, PLAN_REF) == sha and ref(repo, SEED_REF) == row["seed_sha"],
            f"{name}: recorded seed or plan SHA no longer matches")
    require(inspect_result(row, name, sha) == row["evidence"],
            f"{name}: final Docker gate evidence has changed")
    return sha


def run_target(name, row, state, runner, agent, env):
    runtime = Path(row["runtime"])
    start = time.monotonic()
    result = dict(row, exit_code=None, final_sha=None, evidence=None)
    result.pop("error", None)
    result.pop("failed_logs", None)
    with locked(state / f"{name}.lock") as fd:
        validate_driver_state(row)
        # Write intent before starting the child, so a restart can prove provenance.
        intent = dict(result, status="running", elapsed_seconds=0)
        atomic_json(state / f"{name}.json", intent)
        status_log = state / f"{name}.out"
        with status_log.open("ab") as log:
            completed = subprocess.run(
                [str(runner), "--repo", row["seed_dir"], "--plan", "ralphify",
                 "--jobs", "1", "--on-limit", "handoff", "--agent", agent],
                env=env, stdout=log, stderr=subprocess.STDOUT, pass_fds=(fd,), check=False,
            )
        result.update(exit_code=completed.returncode, status="stopped",
                      elapsed_seconds=round(time.monotonic() - start, 2))
        if completed.returncode == 0:
            try:
                sha = ref(Path(row["repo"]), PLAN_REF)
                result.update(evidence=inspect_result(row, name, sha), final_sha=sha, status="done")
            except (RolloutError, OSError, ValueError) as exc:
                result["error"] = str(exc)
        if result["status"] != "done":
            result["failed_logs"] = [
                str(path) for path in sorted((runtime / "logs").glob("gate-*.out"))
            ]
        atomic_json(state / f"{name}.json", result)
    return result


def load_rows(state, manifest, allowlist):
    require(set(manifest) == {"repos_root", "ralph_work", "runner", "template_repo", "targets"},
            "Invalid rollout manifest")
    require(not set(manifest["targets"]) - allowlist.keys(), "State contains an unknown target")
    for name, row in manifest["targets"].items():
        result = state / f"{name}.json"
        if not result.is_file():
            continue
        data = json.loads(result.read_text())
        keys = ("repo", "identity", "base", "base_sha", "seed_dir", "seed_sha", "runtime")
        require(all(row[key] == data[key] for key in keys), f"{name}: mismatched child run record")
        row.update(data)


def run(args, allowlist):
    root = canonical_path(args.repos_root, "--repos-root")
    template = canonical_path(args.template_repo, "--template-repo")
    runner = canonical_path(args.runner, "--runner")
    state, work = env_path("ROLLOUT_STATE"), env_path("RALPH_WORK")
    require(root.is_dir(), "Repos root does not exist")
    external_path(work, (root, template, runner.parent))
    external_path(state, (root, template, runner.parent))
    require(1 <= args.jobs <= len(allowlist), f"--jobs must be between 1 and {len(allowlist)}")
    require(not ({"ralph-looper", "repo-template"} & allowlist.keys()), "Tool repos cannot be rollout targets")
    inputs = load_inputs(template, runner)
    env = child_environment(work)
    state.mkdir(parents=True, mode=0o700, exist_ok=True)
    with locked(state / "rollout.lock"):
        manifest_path = state / "manifest.json"
        settings = {"repos_root": str(root), "ralph_work": str(work),
                    "runner": str(runner), "template_repo": str(template)}
        manifest = dict(settings, targets={})
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            require(all(manifest.get(key) == value for key, value in settings.items()),
                    "Rollout paths differ from the recorded run")
            load_rows(state, manifest, allowlist)
        preflight(root, state, work, allowlist, manifest)
        rows = manifest["targets"]
        for name, base in allowlist.items():
            repo = root / name
            if name not in rows:
                require(not (state / f"{name}.json").exists(), f"{name}: unexpected run record")
                rows[name] = {
                    "repo": str(repo), "identity": git_identity(repo), "base": base,
                    "base_sha": ref(repo, f"refs/heads/{base}"), "status": "preparing",
                    "seed_dir": str(state / "seeds" / name), "seed_sha": None,
                    "runtime": str(work / name / "ralphify"),
                }
                atomic_json(manifest_path, manifest)
            row = rows[name]
            if row["status"] == "preparing":
                require(ref(repo, f"refs/heads/{base}") == row["base_sha"],
                        f"{name}: base changed during provisioning")
                files = seed_files(name, base, repo, row["base_sha"], inputs)
                seed_target(row, files, runner, env)
                atomic_json(manifest_path, manifest)

        errors = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {}
            for name, row in rows.items():
                if row["status"] == "done":
                    try:
                        print(f"{name}: reused {verify_target(name, row)}", flush=True)
                    except (RolloutError, OSError, ValueError) as exc:
                        print(f"{name}: {exc}", file=sys.stderr)
                        errors += 1
                    continue
                futures[pool.submit(run_target, name, row, state, runner, args.agent, env)] = name
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                except (RolloutError, OSError, ValueError) as exc:
                    print(f"{name}: {exc}", file=sys.stderr)
                    errors += 1
                    continue
                if result["status"] == "done":
                    print(f"{name}: verified {result['final_sha']}", flush=True)
                else:
                    errors += 1
                    print(f"{name}: exit {result['exit_code']}, {result.get('error', 'incomplete')}"
                          f"\n  driver: {result['runtime']}/driver.out"
                          f"\n  launcher: {state / (name + '.out')}", file=sys.stderr)
                    for path in result.get("failed_logs", []):
                        print(f"  step gate: {path}", file=sys.stderr)
        return int(errors != 0)


def verify(allowlist):
    state = env_path("ROLLOUT_STATE")
    manifest = json.loads((state / "manifest.json").read_text())
    load_rows(state, manifest, allowlist)
    root = canonical_path(manifest["repos_root"], "recorded repo root")
    work = canonical_path(manifest["ralph_work"], "recorded Ralph work root")
    external_path(state, (root,))
    rows = manifest["targets"]
    require(set(rows) == allowlist.keys(), "Run record is missing one or more allowlisted targets")
    errors = 0
    for name, base in allowlist.items():
        row = rows[name]
        repo = root / name
        try:
            require(row["repo"] == str(repo) and row["identity"] == git_identity(repo)
                    and row["runtime"] == str(work / name / "ralphify") and row["base"] == base
                    and row["base_sha"] == ref(repo, f"refs/heads/{base}"),
                    f"{name}: recorded checkout, runtime, or base has changed")
            print(f"{name}: verified {verify_target(name, row)}")
        except (RolloutError, OSError, ValueError) as exc:
            print(f"{name}: {exc}", file=sys.stderr)
            errors += 1
    return int(errors != 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    start = commands.add_parser(
        "run", help="seed and run the allowed child repositories",
        epilog="Explicit child overrides: RALPH_CHILD_" + ", RALPH_CHILD_".join(CHILD_OVERRIDES),
    )
    for option in ("repos-root", "template-repo", "runner"):
        start.add_argument(f"--{option}", required=True)
    start.add_argument("--agent", choices=("claude", "codex", "copilot"), required=True)
    start.add_argument("--jobs", type=int, default=1)
    commands.add_parser("verify", help="verify committed outcomes from the recorded rollout")
    args = parser.parse_args()
    try:
        allowlist = targets()
        return run(args, allowlist) if args.action == "run" else verify(allowlist)
    except (RolloutError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"rollout: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
