#!/usr/bin/env python3
"""Fan out child plans from a parent plan to other repositories. Standard library only.

Run me when: a parent plan sends one wave of child plans to repositories under $REPOS_ROOT.
The operator runs this tool. Agents do not run `provision` or `run`.

Commands (each takes --plan-dir DIR --wave NAME):
  ready      Read only. Check each target of the wave before provisioning.
  provision  Create rollout/<child_plan> in a linked worktree and commit the seed.
  run        Provision if needed, then run the driver for each run=yes target.
  status     Read only. Print the recorded state of each target.
  verify     Read only. Check the child plan branches with Git plumbing.
  published  Fetch each target remote, then check that the result is on origin/<base>.
  amend      Record a reviewed operator commit on plan/<child_plan> (--repo, --commit, --reason).
             The commit may change only plans/<child_plan>/. verify then accepts the gates that
             the amendment changed, and prints every amendment. Any other gate change still fails.
  followup   Record one reviewed operator commit on top of a completed run (--repo, --commit,
             --reason). Its parent must be the final commit or the previous follow-up, and it may
             not change plans/<child_plan>/. verify then accepts it as the new branch head.

Wave manifest: DIR/waves/<wave>.tsv (UTF-8, header row, `#` comments) with the columns
repo, base, child_plan, mode (seed|pinned), source, run (yes|no). See docs/fanout.md.

Environment: REPOS_ROOT (parent of the canonical checkouts) and RALPH_WORK (runtime root,
outside all checkouts). State: $RALPH_WORK/fanout/<parent-plan>/<wave>/.
This tool never pushes, never forces and never changes a remote.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import csv
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pick_step import parse as parse_front_matter  # noqa: E402

COLUMNS = ("repo", "base", "child_plan", "mode", "source", "run")
RUNTIME_ENV = (
    "PATH", "HOME", "USERPROFILE", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR", "DOCKER_HOST",
    "DOCKER_CONTEXT", "SSL_CERT_FILE", "SSL_CERT_DIR",
)
AGENTS = ("claude", "codex", "copilot", "local")
EVIDENCE = re.compile(r"gate passed \d{4}-\d{2}-\d{2} \(driver-verified\)")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
SHA = re.compile(r"[0-9a-f]{40}")


class FanoutError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise FanoutError(message)


# ---- Git helpers ----

def git_env():
    # Explicit paths select the repository even when the caller runs inside a Git hook.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k in (
        "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    return env


def git(repo, *args, allow_fail=False):
    proc = subprocess.run(["git", "-C", str(repo), *args], env=git_env(),
                          capture_output=True, check=False)
    if allow_fail and proc.returncode != 0:
        return None
    require(proc.returncode == 0,
            f"{Path(repo).name}: git {args[0]} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git_text(repo, *args, **kwargs):
    out = git(repo, *args, **kwargs)
    return out.decode().strip() if out is not None else None


def ref(repo, name):
    return git_text(repo, "rev-parse", "--verify", "--quiet", f"{name}^{{commit}}", allow_fail=True)


def is_ancestor(repo, ancestor, commit):
    return git(repo, "merge-base", "--is-ancestor", ancestor, commit, allow_fail=True) is not None


def blob(repo, commit, path):
    return git(repo, "cat-file", "blob", f"{commit}:{path}", allow_fail=True)


def ls_tree(repo, commit, path):
    out = git_text(repo, "ls-tree", "-r", "--name-only", commit, "--", path, allow_fail=True)
    return [line for line in (out or "").splitlines() if line]


def worktree_paths(repo):
    out = git_text(repo, "worktree", "list", "--porcelain")
    return {line[9:] for line in out.splitlines() if line.startswith("worktree ")}


# ---- paths, state and locks ----

def canonical(value, label):
    require(value, f"Set and export {label}")
    path = Path(value)
    require(path.is_absolute() and path == path.resolve(), f"{label} must be an absolute, canonical path")
    return path


def outside_checkouts(path):
    ancestor = next(p for p in (path, *path.parents) if p.is_dir())
    probe = subprocess.run(["git", "-C", str(ancestor), "rev-parse", "--is-inside-work-tree",
                            "--is-inside-git-dir"], env=git_env(), capture_output=True,
                           text=True, check=False)
    require("true" not in probe.stdout.split(), f"{path} must be outside Git checkouts")


def atomic_json(path, data):
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, encoding="utf-8") as f:
        draft = Path(f.name)
        try:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
            os.replace(draft, path)
        finally:
            draft.unlink(missing_ok=True)


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with path.open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise FanoutError(f"another fan-out holds the wave lock: {path}") from exc
        yield


def lock_held(path):
    """True if another process (for example a running driver) holds a lock on this file."""
    if not path.exists():
        return False
    with path.open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(stream, fcntl.LOCK_UN)
    return False


class Wave:
    def __init__(self, plan_dir, wave):
        self.plan_dir = canonical(str(Path(plan_dir).resolve()) if plan_dir else "", "--plan-dir")
        require(self.plan_dir.is_dir(), f"no plan directory: {self.plan_dir}")
        require(NAME.fullmatch(wave or ""), "invalid --wave name")
        self.name = wave
        self.parent = self.plan_dir.name
        self.root = canonical(os.environ.get("REPOS_ROOT", ""), "REPOS_ROOT")
        require(self.root.is_dir(), "REPOS_ROOT does not exist")
        self.work = canonical(os.environ.get("RALPH_WORK", ""), "RALPH_WORK")
        require(not (self.work.is_relative_to(self.root) or self.root.is_relative_to(self.work)),
                "RALPH_WORK and REPOS_ROOT must not overlap")
        outside_checkouts(self.work)
        self.state = self.work / "fanout" / self.parent / wave
        self.rows = load_manifest(self.plan_dir / "waves" / f"{wave}.tsv", self.plan_dir)

    def record_path(self, row):
        return self.state / "targets" / f"{row['repo']}.json"

    def record(self, row):
        path = self.record_path(row)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("repo", "base", "child_plan", "mode", "source", "run"):
            require(data.get(key) == row[key], f"{row['repo']}: manifest row differs from the record ({key})")
        return data

    def save(self, rec):
        atomic_json(self.state / "targets" / f"{rec['repo']}.json", rec)

    def worktree(self, row):
        return self.state / "worktrees" / row["repo"]

    def runtime(self, row):
        # The driver uses $RALPH_WORK/<basename of the checkout>/<plan>. The worktree has the repo name.
        return self.work / row["repo"] / row["child_plan"]


def load_manifest(path, plan_dir):
    require(path.is_file(), f"no wave manifest: {path}")
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    reader = csv.reader(lines, delimiter="\t")
    header = next(reader, None)
    require(header is not None and tuple(h.strip() for h in header) == COLUMNS,
            f"wave header must be: {' '.join(COLUMNS)}")
    rows, seen = [], set()
    for number, cells in enumerate(reader, 2):
        require(len(cells) == len(COLUMNS), f"wave row {number}: expected {len(COLUMNS)} columns")
        row = dict(zip(COLUMNS, (c.strip() for c in cells)))
        require(NAME.fullmatch(row["repo"]) and row["repo"] not in (".", "..", "fanout"),
                f"wave row {number}: invalid repo name")
        require(row["repo"] not in seen, f"wave row {number}: duplicate repo {row['repo']}")
        seen.add(row["repo"])
        require(NAME.fullmatch(row["child_plan"]), f"wave row {number}: invalid child_plan")
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", row["base"]) and ".." not in row["base"],
                f"wave row {number}: invalid base branch")
        require(row["mode"] in ("seed", "pinned"), f"wave row {number}: mode must be seed or pinned")
        require(row["run"] in ("yes", "no"), f"wave row {number}: run must be yes or no")
        if row["mode"] == "pinned":
            require(SHA.fullmatch(row["source"]), f"wave row {number}: pinned source must be a full SHA")
        else:
            src = (plan_dir / row["source"]).resolve()
            require(not Path(row["source"]).is_absolute() and src.is_relative_to(plan_dir)
                    and src.is_dir(), f"wave row {number}: seed source must be a directory in the plan")
        rows.append(row)
    require(rows, "wave has no targets")
    return rows


# ---- seed ----

def seed_files(wave, row):
    """Map of repository path -> bytes for a seed row."""
    src = (wave.plan_dir / row["source"]).resolve()
    files = {}
    for path in sorted(src.rglob("*")):
        require(not path.is_symlink(), f"{row['repo']}: seed contains a link: {path.name}")
        if path.is_file():
            files[f"plans/{row['child_plan']}/{path.relative_to(src).as_posix()}"] = path.read_bytes()
    require(any(re.fullmatch(rf"plans/{re.escape(row['child_plan'])}/steps/[^/]+\.md", p) for p in files),
            f"{row['repo']}: seed has no steps/*.md")
    return files


def digest(files):
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(path.encode() + b"\0" + hashlib.sha256(files[path]).hexdigest().encode() + b"\n")
    return h.hexdigest()


def pinned_files(repo, row):
    prefix = f"plans/{row['child_plan']}/"
    return {path: blob(repo, row["source"], path) for path in ls_tree(repo, row["source"], prefix)}


def seed_commit_matches(repo, sha, base_sha, files):
    changed = set(git_text(repo, "diff", "--name-only", "--no-renames", base_sha, sha).splitlines())
    return (git_text(repo, "rev-list", "--parents", "-n", "1", sha) == f"{sha} {base_sha}"
            and changed == set(files) and all(blob(repo, sha, p) == d for p, d in files.items()))


# ---- target checks (shared by ready, provision and run) ----

def identity(repo):
    require(repo.is_dir() and not repo.is_symlink() and repo.resolve() == repo,
            f"{repo.name}: missing or substituted checkout")
    top = git_text(repo, "rev-parse", "--show-toplevel", allow_fail=True)
    require(top and Path(top) == repo, f"{repo.name}: not the top of a checkout")
    common = git_text(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    require(Path(common).resolve() == repo / ".git", f"{repo.name}: the canonical checkout must own its Git directory")
    return common


def check_target(wave, row, rec, seen):
    """Check one target. Return (repo, base_sha, files). Read only."""
    name, child = row["repo"], row["child_plan"]
    repo = wave.root / name
    ident = identity(repo)
    require(ident not in seen, f"{name}: duplicate Git common directory")
    seen.add(ident)
    require(not git_text(repo, "status", "--porcelain", "--untracked-files=all"),
            f"{name}: checkout has uncommitted changes")
    base_sha = ref(repo, f"refs/heads/{row['base']}")
    require(base_sha, f"{name}: missing base branch {row['base']}")
    if row["mode"] == "seed":
        files = seed_files(wave, row)
    else:
        require(git(repo, "cat-file", "-e", f"{row['source']}^{{commit}}", allow_fail=True) is not None,
                f"{name}: pinned commit is not in the repository")
        files = pinned_files(repo, row)
        require(any(p.startswith(f"plans/{child}/steps/") for p in files),
                f"{name}: pinned commit has no plans/{child}/steps")
    rollout, plan = ref(repo, f"refs/heads/rollout/{child}"), ref(repo, f"refs/heads/plan/{child}")
    tree = wave.worktree(row)
    if rec is None:
        if row["mode"] == "seed":
            require(not ls_tree(repo, base_sha, f"plans/{child}"),
                    f"{name}: base already contains plans/{child}")
        require(not rollout and not plan and not git_text(repo, "branch", "--list", f"step/{child}/*"),
                f"{name}: an existing branch for {child} has no recorded provenance (foreign branch)")
        require(not tree.exists() and not wave.runtime(row).exists(),
                f"{name}: an existing worktree or runtime has no recorded provenance")
        return repo, base_sha, files
    require(rec["path"] == str(repo) and rec["identity"] == ident, f"{name}: recorded checkout has changed")
    require(rec["seed_digest"] == digest(files), f"{name}: seed differs from the provisioned seed")
    if rec.get("status") != "done":
        require(rec["base_sha"] == base_sha, f"{name}: base branch advanced after provisioning")
    if rec.get("seed_commit"):
        require(rollout == rec["seed_commit"], f"{name}: rollout/{child} differs from the recorded seed commit")
    else:
        start = rec["base_sha"] if row["mode"] == "seed" else row["source"]
        require(rollout in (None, start), f"{name}: rollout/{child} is foreign")
    require(not plan or (rec.get("seed_commit") and is_ancestor(repo, rec["seed_commit"], plan)),
            f"{name}: plan/{child} does not descend from the seed commit")
    require(tree.resolve() == tree or not tree.exists(), f"{name}: substituted worktree path")
    if tree.exists():
        require(str(tree) in worktree_paths(repo)
                and git_text(tree, "rev-parse", "--path-format=absolute", "--git-common-dir") == ident
                and git_text(tree, "symbolic-ref", "HEAD") == f"refs/heads/rollout/{child}",
                f"{name}: unexpected worktree at the recorded path")
    return repo, base_sha, files


def snapshot_check(wave, repo, commit, files, row, runner):
    """Copy `commit` and the seed into a temporary tree. Run the plan checker and the picker."""
    child = row["child_plan"]
    with tempfile.TemporaryDirectory(prefix="fanout-ready-") as tmp:
        snap = Path(tmp) / row["repo"]
        snap.mkdir()
        archive = git(repo, "archive", "--format=tar", commit)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(snap, filter="data")
        for path, data in files.items():
            dest = snap / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        subprocess.run(["git", "init", "-q", str(snap)], env=git_env(), capture_output=True, check=True)
        env = dict(git_env(), PYTHONDONTWRITEBYTECODE="1")
        if (snap / "scripts/check_plan.py").is_file():
            proc = subprocess.run([sys.executable, "-B", "scripts/check_plan.py", str(snap)], cwd=snap,
                                  env=env, capture_output=True, text=True, check=False)
            require(proc.returncode == 0, f"{row['repo']}: seed fails the target plan checker\n"
                    f"{proc.stdout}{proc.stderr}".rstrip())
        pick = runner.parent / "lib" / "pick_step.py"
        plan_dir = snap / "plans" / child
        summary = subprocess.run([sys.executable, "-I", str(pick), "summary", str(plan_dir)],
                                 env=env, capture_output=True, text=True, check=False)
        ready = subprocess.run([sys.executable, "-I", str(pick), "ready", str(plan_dir), "--max", "1"],
                               env=env, capture_output=True, text=True, check=False)
        require(summary.returncode in (0, 10) and (summary.returncode == 0 or ready.stdout.strip()),
                f"{row['repo']}: the driver cannot list a ready child step")
        return summary.stdout.strip()


# ---- provision ----

def provision_target(wave, row, seen):
    name, child = row["repo"], row["child_plan"]
    rec = wave.record(row)
    repo, base_sha, files = check_target(wave, row, rec, seen)
    if rec and rec.get("seed_commit"):
        return rec
    tree = wave.worktree(row)
    if rec is None:
        rec = {**row, "path": str(repo), "identity": git_text(repo, "rev-parse", "--path-format=absolute",
                                                               "--git-common-dir"),
               "base_sha": base_sha, "seed_digest": digest(files), "seed_commit": None,
               "worktree": str(tree), "runtime": str(wave.runtime(row)), "status": "provisioning"}
        wave.save(rec)  # write intent before the first change, so a restart can prove provenance
    start = base_sha if row["mode"] == "seed" else row["source"]
    if not tree.exists():
        require(ref(repo, f"refs/heads/rollout/{child}") is None and str(tree) not in worktree_paths(repo),
                f"{name}: worktree is missing or registered elsewhere")
        tree.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        git(repo, "worktree", "add", "-q", "-b", f"rollout/{child}", str(tree), start)
    require(git_text(tree, "symbolic-ref", "HEAD") == f"refs/heads/rollout/{child}",
            f"{name}: worktree is not on rollout/{child}")
    if row["mode"] == "seed":
        head = ref(tree, "HEAD")
        if head == base_sha:
            staged = set(git_text(tree, "diff", "--cached", "--name-only", base_sha).splitlines())
            untracked = set(git_text(tree, "ls-files", "--others", "--exclude-standard").splitlines())
            require(not git_text(tree, "diff", "--name-only") and (staged | untracked) <= set(files),
                    f"{name}: unexpected edits in the unfinished seed")
            for path, data in files.items():
                dest = tree / path
                require(dest.parent.resolve().is_relative_to(tree), f"{name}: substituted seed path {path}")
                if dest.exists():
                    require(dest.read_bytes() == data, f"{name}: divergent unfinished seed file {path}")
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            git(tree, "add", "--", *files)
            git(tree, "commit", "-q", "-m", f"fanout({wave.parent}/{wave.name}): seed plan {child}",
                "--", *files)
        seed = ref(tree, "HEAD")
        require(seed_commit_matches(repo, seed, base_sha, files), f"{name}: seed commit is unfamiliar")
    else:
        seed = ref(tree, "HEAD")
        require(seed == row["source"], f"{name}: worktree is not at the pinned commit")
    require(not git_text(tree, "status", "--porcelain", "--untracked-files=all"), f"{name}: worktree is dirty")
    rec.update(seed_commit=seed, status="provisioned")
    wave.save(rec)
    return rec


def provision_all(wave):
    seen, records, errors = set(), {}, 0
    for row in wave.rows:
        try:
            records[row["repo"]] = provision_target(wave, row, seen)
            print(f"{row['repo']}: provisioned {records[row['repo']]['seed_commit']}", flush=True)
        except (FanoutError, OSError, ValueError) as exc:
            print(f"{row['repo']}: {exc}", file=sys.stderr, flush=True)
            errors += 1
    return records, errors


# ---- verify ----

def gate_digest(runtime):
    logs = Path(runtime) / "logs"
    h = hashlib.sha256()
    for path in sorted(logs.glob("gate-*.out")) if logs.is_dir() else []:
        h.update(path.name.encode() + b"\0" + hashlib.sha256(path.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


def amended_gate(repo, rec, path, seed_gate):
    """Return the gate a step must have: the seed gate, as changed by recorded operator amendments.

    An amendment changes the expected gate only for the steps whose gate it changed itself. Any other
    later change of a gate (for example by an agent) still fails verify.
    """
    gate = seed_gate
    for amendment in rec.get("amendments", []):
        commit = amendment["commit"]
        before = parse_front_matter((blob(repo, f"{commit}^", path) or b"").decode()).get("gate")
        after = parse_front_matter((blob(repo, commit, path) or b"").decode()).get("gate")
        if after != before:
            gate = after
    return gate


def check_amendments(repo, rec, plan_sha):
    name = rec["repo"]
    previous = rec["seed_commit"]
    for amendment in rec.get("amendments", []):
        commit = amendment["commit"]
        require(is_ancestor(repo, previous, commit) and commit != previous,
                f"{name}: amendment {commit[:12]} does not follow the seed or the previous amendment")
        require(is_ancestor(repo, commit, plan_sha), f"{name}: amendment {commit[:12]} is not on the plan branch")
        previous = commit


def amendment_note(rec):
    note = ""
    for key, label in (("amendments", "operator amendments"), ("followups", "operator follow-ups")):
        items = rec.get(key, [])
        if items:
            note += f" ({label}: {len(items)}: " + "; ".join(f"{a['commit'][:12]} {a['reason']}" for a in items) + ")"
    return note


def expected_head(repo, rec):
    """Return the commit that plan/<child> must point to: the final commit, or the last recorded follow-up.

    Each follow-up is one commit whose parent is the final commit or the previous follow-up.
    """
    head = rec["final_sha"]
    for item in rec.get("followups", []):
        commit = item["commit"]
        parent = git_text(repo, "rev-parse", "--verify", "--quiet", f"{commit}^", allow_fail=True)
        require(parent == head, f"{rec['repo']}: follow-up {commit[:12]} is not a single commit on top of {head[:12]}")
        head = commit
    return head


def check_result(wave, row, rec, plan_sha):
    """Check a child plan commit with Git plumbing. Raise FanoutError if it is not a valid result."""
    name, child = row["repo"], row["child_plan"]
    repo = Path(rec["path"])
    seed = rec["seed_commit"]
    require(plan_sha and is_ancestor(repo, seed, plan_sha), f"{name}: plan/{child} does not descend from the seed")
    check_amendments(repo, rec, plan_sha)
    prefix = f"plans/{child}/steps/"
    original = {p for p in ls_tree(repo, seed, prefix) if p.endswith(".md")}
    actual = {p for p in ls_tree(repo, plan_sha, prefix) if p.endswith(".md")}
    require(original and original == actual, f"{name}: the set of child steps differs from the seed")
    for path in sorted(original):
        step = Path(path).stem
        if step.startswith("00-"):
            continue
        old = parse_front_matter((blob(repo, seed, path) or b"").decode())
        new = parse_front_matter((blob(repo, plan_sha, path) or b"").decode())
        require(new.get("status") == "done", f"{name}: step {step} is not done")
        require(EVIDENCE.match(str(new.get("evidence", ""))), f"{name}: step {step} has no driver evidence")
        expected = amended_gate(repo, rec, path, old.get("gate"))
        require(old.get("gate") and new.get("gate") == expected,
                f"{name}: step {step} gate text differs from the seed and from every recorded operator amendment")


def verify_target(wave, row):
    name, child = row["repo"], row["child_plan"]
    rec = wave.record(row)
    require(rec and rec.get("seed_commit"), f"{name}: not provisioned")
    repo = Path(rec["path"])
    require(repo == wave.root / name and identity(repo) == rec["identity"], f"{name}: recorded checkout has changed")
    if row["run"] == "no":
        rollout = ref(repo, f"refs/heads/rollout/{child}")
        require(rollout and is_ancestor(repo, rec["seed_commit"], rollout),
                f"{name}: seed commit is not on rollout/{child}")
        return f"seeded {rec['seed_commit']}"
    require(rec.get("status") == "done" and rec.get("exit_code") == 0 and rec.get("final_sha"),
            f"{name}: no recorded completed run (status {rec.get('status')})")
    plan_sha = ref(repo, f"refs/heads/plan/{child}")
    require(plan_sha == expected_head(repo, rec),
            f"{name}: plan/{child} differs from the recorded plan SHA and its recorded follow-ups")
    check_result(wave, row, rec, rec["final_sha"])
    require(gate_digest(rec["runtime"]) == rec.get("gate_digest"), f"{name}: gate logs have changed")
    return f"done {plan_sha}{amendment_note(rec)}"


# ---- run ----

def child_environment(wave, keys):
    env = {k: os.environ[k] for k in RUNTIME_ENV if k in os.environ}
    for key in keys:
        env[key] = os.environ[key]
    env.update(RALPH_WORK=str(wave.work), GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    return env


def run_target(wave, row, rec, runner, agent, env):
    name = row["repo"]
    runtime = Path(rec["runtime"])
    if lock_held(runtime / ".lock"):
        return dict(rec, note="driver lock is held: not relaunched")
    start = time.monotonic()
    rec = {k: v for k, v in rec.items() if k not in ("error", "note")}
    rec.update(status="running", exit_code=None, final_sha=None, gate_digest=None)
    wave.save(rec)
    log_path = wave.state / "logs" / f"{name}.out"
    log_path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with log_path.open("ab") as log:
        proc = subprocess.run([str(runner), "--repo", rec["worktree"], "--plan", row["child_plan"],
                               "--agent", agent, "--on-limit", "handoff"],
                              env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    code = proc.returncode
    rec.update(exit_code=code, elapsed_seconds=round(time.monotonic() - start, 2),
               final_sha=ref(rec["path"], f"refs/heads/plan/{row['child_plan']}"),
               gate_digest=gate_digest(runtime),
               status={0: "done", 75: "limit", 11: "blocked", 3: "locked"}.get(code, "stopped"))
    if code == 0:
        try:
            check_result(wave, row, rec, rec["final_sha"])
        except FanoutError as exc:
            rec.update(status="stopped", error=str(exc))
    wave.save(rec)
    return rec


def cmd_run(wave, args):
    runner = Path(args.runner).resolve() if args.runner else HERE.parent / "ralph-looper"
    require(runner.is_file() and os.access(runner, os.X_OK), f"runner is not executable: {runner}")
    for key in args.child_env:
        require(re.fullmatch(r"[A-Z_][A-Z0-9_]*", key) and key in os.environ,
                f"--child-env {key}: invalid name or not set")
    env = child_environment(wave, args.child_env)
    require(args.jobs >= 1, "--jobs must be 1 or more")
    with locked(wave.state / "wave.lock"):
        records, errors = provision_all(wave)
        todo = []
        for row in wave.rows:
            rec = records.get(row["repo"])
            if rec is None or row["run"] == "no":
                continue
            if rec.get("status") == "done":
                try:
                    print(f"{row['repo']}: reused {verify_target(wave, row)}", flush=True)
                except (FanoutError, OSError, ValueError) as exc:
                    print(f"{row['repo']}: {exc}", file=sys.stderr, flush=True)
                    errors += 1
                continue
            todo.append((row, rec))
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_target, wave, row, rec, runner, args.agent, env): row
                       for row, rec in todo}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]["repo"]
                try:
                    rec = future.result()
                except (FanoutError, OSError, ValueError) as exc:
                    print(f"{name}: {exc}", file=sys.stderr, flush=True)
                    errors += 1
                    continue
                if rec.get("status") == "done":
                    print(f"{name}: done {rec['final_sha']}", flush=True)
                    continue
                errors += 1
                print(f"{name}: {rec.get('note') or 'exit ' + str(rec.get('exit_code'))} "
                      f"status={rec.get('status')} {rec.get('error', '')}".rstrip()
                      + f"\n  log: {wave.state / 'logs' / (name + '.out')}", file=sys.stderr, flush=True)
    return int(errors != 0)


# ---- read-only commands ----

def cmd_ready(wave, args):
    runner = Path(args.runner).resolve() if args.runner else HERE.parent / "ralph-looper"
    seen, errors = set(), 0
    for row in wave.rows:
        try:
            rec = wave.record(row)
            repo, base_sha, files = check_target(wave, row, rec, seen)
            commit = base_sha if row["mode"] == "seed" else row["source"]
            summary = snapshot_check(wave, repo, commit, files, row, runner)
            print(f"{row['repo']}: ready {row['mode']} {row['child_plan']} on {row['base']} {summary}")
        except (FanoutError, OSError, ValueError) as exc:
            print(f"{row['repo']}: {exc}", file=sys.stderr)
            errors += 1
    return int(errors != 0)


def cmd_provision(wave, args):
    with locked(wave.state / "wave.lock"):
        return int(provision_all(wave)[1] != 0)


def cmd_status(wave, args):
    for row in wave.rows:
        try:
            rec = wave.record(row)
        except (FanoutError, ValueError) as exc:
            print(f"{row['repo']}: {exc}")
            continue
        if rec is None:
            print(f"{row['repo']}: not provisioned")
            continue
        print(f"{row['repo']}: {rec.get('status')} child={row['child_plan']} run={row['run']} "
              f"seed={rec.get('seed_commit') or '-'} exit={rec.get('exit_code', '-')} "
              f"plan={rec.get('final_sha') or '-'} elapsed={rec.get('elapsed_seconds', '-')}"
              + (f" error={rec['error']}" if rec.get("error") else ""))
    return 0


def cmd_verify(wave, args):
    errors = 0
    for row in wave.rows:
        try:
            print(f"{row['repo']}: verified {verify_target(wave, row)}")
        except (FanoutError, OSError, ValueError) as exc:
            print(f"{row['repo']}: FAIL {exc}", file=sys.stderr)
            errors += 1
    print(f"verify: {len(wave.rows) - errors}/{len(wave.rows)} targets pass")
    return int(errors != 0)


def cmd_published(wave, args):
    errors = 0
    for row in wave.rows:
        try:
            rec = wave.record(row)
            require(rec and rec.get("seed_commit"), f"{row['repo']}: not provisioned")
            repo = Path(rec["path"])
            commit = rec.get("final_sha") if row["run"] == "yes" else rec["seed_commit"]
            require(commit and (row["run"] == "no" or rec.get("status") == "done"),
                    f"{row['repo']}: no completed result to check")
            git(repo, "fetch", "--quiet", "--no-tags", "origin")
            remote = ref(repo, f"refs/remotes/origin/{row['base']}")
            require(remote and is_ancestor(repo, commit, remote),
                    f"{row['repo']}: {commit[:12]} is not on origin/{row['base']}")
            print(f"{row['repo']}: published {commit}")
        except (FanoutError, OSError, ValueError) as exc:
            print(f"{row['repo']}: FAIL {exc}", file=sys.stderr)
            errors += 1
    return int(errors != 0)


def cmd_amend(wave, args):
    """Record a reviewed operator commit on plan/<child_plan>. Only plan files may change in it."""
    rows = [row for row in wave.rows if row["repo"] == args.repo]
    require(rows, f"{args.repo}: not in the wave manifest")
    row = rows[0]
    reason = (args.reason or "").strip()
    require(reason and "\n" not in reason and len(reason) <= 300, "--reason must be one line of 1 to 300 characters")
    with locked(wave.state / "wave.lock"):
        rec = wave.record(row)
        require(rec and rec.get("seed_commit"), f"{row['repo']}: not provisioned")
        repo = Path(rec["path"])
        commit = git_text(repo, "rev-parse", "--verify", "--quiet", f"{args.commit}^{{commit}}", allow_fail=True)
        require(commit, f"{row['repo']}: unknown commit {args.commit}")
        amendments = rec.get("amendments", [])
        if any(a["commit"] == commit for a in amendments):
            print(f"{row['repo']}: amendment {commit[:12]} is already recorded")
            return 0
        previous = amendments[-1]["commit"] if amendments else rec["seed_commit"]
        require(commit != previous and is_ancestor(repo, previous, commit),
                f"{row['repo']}: {commit[:12]} does not follow the seed or the previous amendment")
        plan = ref(repo, f"refs/heads/plan/{row['child_plan']}")
        require(plan and is_ancestor(repo, commit, plan), f"{row['repo']}: {commit[:12]} is not on plan/{row['child_plan']}")
        files = [f for f in git_text(repo, "diff", "--name-only", f"{commit}^", commit).splitlines() if f]
        prefix = f"plans/{row['child_plan']}/"
        outside = [f for f in files if not f.startswith(prefix)]
        require(files and not outside, f"{row['repo']}: an amendment may change only {prefix}: {outside or 'no files'}")
        amendments.append({"commit": commit, "reason": reason, "files": files,
                           "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        rec["amendments"] = amendments
        wave.save(rec)
    print(f"{row['repo']}: recorded amendment {commit[:12]}: {reason}")
    return 0


def cmd_followup(wave, args):
    """Record one reviewed operator commit on top of a completed run. It may not change plans/<child_plan>/."""
    rows = [row for row in wave.rows if row["repo"] == args.repo]
    require(rows, f"{args.repo}: not in the wave manifest")
    row = rows[0]
    reason = (args.reason or "").strip()
    require(reason and "\n" not in reason and len(reason) <= 300, "--reason must be one line of 1 to 300 characters")
    with locked(wave.state / "wave.lock"):
        rec = wave.record(row)
        require(rec and rec.get("status") == "done" and rec.get("final_sha"),
                f"{row['repo']}: a follow-up needs a completed run")
        repo = Path(rec["path"])
        commit = git_text(repo, "rev-parse", "--verify", "--quiet", f"{args.commit}^{{commit}}", allow_fail=True)
        require(commit, f"{row['repo']}: unknown commit {args.commit}")
        followups = rec.get("followups", [])
        if any(f["commit"] == commit for f in followups):
            print(f"{row['repo']}: follow-up {commit[:12]} is already recorded")
            return 0
        head = expected_head(repo, rec)
        parents = git_text(repo, "rev-list", "--parents", "-n", "1", commit).split()[1:]
        require(parents == [head], f"{row['repo']}: {commit[:12]} must be one commit whose parent is {head[:12]}")
        plan = ref(repo, f"refs/heads/plan/{row['child_plan']}")
        require(plan and is_ancestor(repo, commit, plan), f"{row['repo']}: {commit[:12]} is not on plan/{row['child_plan']}")
        files = [f for f in git_text(repo, "diff", "--name-only", head, commit).splitlines() if f]
        prefix = f"plans/{row['child_plan']}/"
        inside = [f for f in files if f.startswith(prefix)]
        require(files and not inside, f"{row['repo']}: a follow-up may not change {prefix}: {inside or 'no files'}")
        followups.append({"commit": commit, "reason": reason, "files": files,
                          "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        rec["followups"] = followups
        wave.save(rec)
    print(f"{row['repo']}: recorded follow-up {commit[:12]}: {reason}")
    return 0


COMMANDS = {
    "ready": (cmd_ready, "read only: check each target before provisioning"),
    "provision": (cmd_provision, "create rollout/<child_plan> worktrees and commit the seeds"),
    "run": (cmd_run, "provision if needed, then run the driver for each run=yes target"),
    "status": (cmd_status, "read only: print the recorded state of each target"),
    "verify": (cmd_verify, "read only: check the child plan branches with Git plumbing"),
    "published": (cmd_published, "fetch, then check that each result is on origin/<base>"),
    "amend": (cmd_amend, "record a reviewed operator commit on plan/<child_plan> (plan files only)"),
    "followup": (cmd_followup, "record a reviewed operator commit after a completed run (no plan files)"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fanout.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    for name, (_, text) in COMMANDS.items():
        cmd = sub.add_parser(name, help=text, description=text)
        cmd.add_argument("--plan-dir", required=True, help="the parent plan directory")
        cmd.add_argument("--wave", required=True, help="the wave name (waves/<wave>.tsv)")
        if name in ("ready", "run"):
            cmd.add_argument("--runner", help="driver path (default: the driver next to this tool)")
        if name in ("amend", "followup"):
            cmd.add_argument("--repo", required=True, help="the target repository (a manifest row)")
            cmd.add_argument("--commit", required=True, help="the operator commit on plan/<child_plan>")
            cmd.add_argument("--reason", required=True, help="one line: why the operator changed the plan")
        if name == "run":
            cmd.add_argument("--agent", required=True, choices=AGENTS)
            cmd.add_argument("--jobs", type=int, default=1, help="targets to run at the same time")
            cmd.add_argument("--child-env", action="append", default=[], metavar="KEY",
                             help="pass this environment variable to the children (repeat)")
    args = parser.parse_args(argv)
    try:
        wave = Wave(args.plan_dir, args.wave)
        return COMMANDS[args.command][0](wave, args)
    except (FanoutError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"fanout: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
