#!/usr/bin/env python3
"""Tests for lib/fanout.py with disposable Git repositories and the fake agent.

Run me when: I changed lib/fanout.py. Costs no tokens. Needs git, flock, timeout, python3.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FANOUT = ROOT / "lib" / "fanout.py"
CHILD = "child"

WRAPPER = """#!/usr/bin/env bash
# Fake agent wrapper: simulate a usage limit or a failed gate for one named repository.
name="$(basename "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")"
if [ "$name" = "${FANOUT_LIMIT_REPO:-}" ] && [ ! -e "$FANOUT_MARKER" ]; then
  cat > /dev/null; touch "$FANOUT_MARKER"; echo "usage limit reached" >&2; exit 1
fi
if [ "$name" = "${FANOUT_FAIL_REPO:-}" ]; then
  cat > /dev/null; echo '{"result":"no work"}'; exit 0
fi
exec bash "$FAKE_AGENT"
"""


def step(sid, deps=""):
    return (f"---\nid: {sid}\nstatus: pending\ndepends_on: [{deps}]\ntouches:\n  - {sid}.out\n"
            f"lane: none\ngate: test -f {sid}.out\nevidence: \"\"\n---\n\n# {sid}\n")


def write_plan(directory):
    (directory / "steps").mkdir(parents=True, exist_ok=True)
    (directory / "goal.md").write_text("# Goal\n")
    (directory / "plan.md").write_text('---\ngist: "Read me when: test"\n---\n\n# Plan\n')
    (directory / "steps" / "01-a.md").write_text(step("01-a"))
    (directory / "steps" / "02-b.md").write_text(step("02-b", "01-a"))


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


class FanoutTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fanout-test-")
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name).resolve()
        self.repos = self.tmp / "repos"
        self.work = self.tmp / "work"
        self.repos.mkdir()
        self.work.mkdir()
        self.plan_dir = self.tmp / "parent" / "plans" / "parent-plan"
        write_plan(self.plan_dir / "seeds" / CHILD)
        (self.plan_dir / "waves").mkdir(parents=True)
        self.bases = {}
        for name in ("alpha", "beta"):
            self.make_repo(name)
        wrapper = self.tmp / "agent.sh"
        wrapper.write_text(WRAPPER)
        self.marker = self.tmp / "limit-marker"
        self.env = {
            "PATH": os.environ["PATH"], "HOME": str(self.tmp), "LANG": "C.UTF-8",
            "REPOS_ROOT": str(self.repos), "RALPH_WORK": str(self.work),
            "AGENT_CMD": f"bash {wrapper}", "FAKE_AGENT": str(HERE / "fake-agent.sh"),
            "FANOUT_MARKER": str(self.marker), "MAX_ATTEMPTS": "1", "SLEEP_SECS": "0",
            "SECRET_PARENT_VALUE": "do-not-pass",
        }

    def make_repo(self, name, branch="main"):
        repo = self.repos / name
        repo.mkdir()
        git(repo, "init", "-q", "-b", branch)
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fanout Fixture")
        (repo / "README.md").write_text(f"# {name}\n")
        scripts = repo / "scripts"
        scripts.mkdir()
        for script in ("check_plan.py", "ctx_common.py"):
            shutil.copy(ROOT / "scripts" / script, scripts / script)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        self.bases[name] = git(repo, "rev-parse", "HEAD")
        return repo

    def wave(self, rows, name="w1"):
        text = "# test wave\nrepo\tbase\tchild_plan\tmode\tsource\trun\n"
        text += "".join("\t".join(row) + "\n" for row in rows)
        (self.plan_dir / "waves" / f"{name}.tsv").write_text(text)

    def seed_wave(self):
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "yes"),
                   ("beta", "main", CHILD, "seed", f"seeds/{CHILD}", "yes")])

    def fanout(self, command, *extra, wave="w1", **env):
        args = [sys.executable, str(FANOUT), command, "--plan-dir", str(self.plan_dir), "--wave", wave]
        if command == "run":
            args += ["--agent", "claude", "--jobs", "2"]
            for key in ("AGENT_CMD", "FAKE_AGENT", "FANOUT_MARKER", "MAX_ATTEMPTS", "SLEEP_SECS",
                        *(k for k in env if k.startswith("FANOUT_"))):
                args += ["--child-env", key]
        proc = subprocess.run([*args, *extra], env={**self.env, **env}, capture_output=True,
                              text=True, timeout=300)
        return proc.returncode, proc.stdout + proc.stderr

    def record(self, name, wave="w1"):
        path = self.work / "fanout" / "parent-plan" / wave / "targets" / f"{name}.json"
        return json.loads(path.read_text())

    def assert_base_untouched(self, name, branch="main"):
        repo = self.repos / name
        self.assertEqual(git(repo, "rev-parse", f"refs/heads/{branch}"), self.bases[name])
        self.assertEqual(git(repo, "symbolic-ref", "HEAD"), f"refs/heads/{branch}")
        self.assertEqual(git(repo, "status", "--porcelain"), "")

    # ---- run, limit, resume, verify ----

    def test_run_limit_resume_and_verify(self):
        self.seed_wave()
        code, out = self.fanout("run", FANOUT_LIMIT_REPO="beta")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.record("alpha")["status"], "done", out)
        self.assertEqual(self.record("beta")["exit_code"], 75, out)
        self.assertEqual(self.record("beta")["status"], "limit")
        self.assertTrue(self.marker.exists())
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("beta: FAIL", out)
        alpha = self.record("alpha")

        code, out = self.fanout("run", FANOUT_LIMIT_REPO="beta")
        self.assertEqual(code, 0, out)
        self.assertIn("alpha: reused", out)
        self.assertEqual(self.record("alpha"), alpha)
        self.assertEqual(self.record("beta")["status"], "done")
        code, out = self.fanout("verify")
        self.assertEqual(code, 0, out)
        self.assertIn("2/2 targets pass", out)
        code, out = self.fanout("status")
        self.assertEqual(code, 0, out)
        self.assertIn("alpha: done", out)
        for name in ("alpha", "beta"):
            self.assert_base_untouched(name)
        self.assertNotIn("do-not-pass", (self.work / "fanout").joinpath(
            "parent-plan", "w1", "logs", "alpha.out").read_text())

        # A changed plan ref fails verify.
        repo = self.repos / "alpha"
        good = git(repo, "rev-parse", f"refs/heads/plan/{CHILD}")
        git(repo, "update-ref", f"refs/heads/plan/{CHILD}", alpha["seed_commit"])
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("differs from the recorded plan SHA", out)
        git(repo, "update-ref", f"refs/heads/plan/{CHILD}", good)

        # A child step whose gate differs from the seed fails verify, even when the record matches.
        plan_tree = self.work / "alpha" / CHILD / "worktrees" / "_plan"
        path = plan_tree / "plans" / CHILD / "steps" / "02-b.md"
        path.write_text(path.read_text().replace("gate: test -f 02-b.out", "gate: true"))
        git(plan_tree, "commit", "-q", "-am", "weaken gate")
        record_path = self.work / "fanout" / "parent-plan" / "w1" / "targets" / "alpha.json"
        data = json.loads(record_path.read_text())
        data["final_sha"] = git(repo, "rev-parse", f"refs/heads/plan/{CHILD}")
        record_path.write_text(json.dumps(data))
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("gate text differs from the seed", out)

    def test_amend_accepts_only_recorded_operator_gate_changes(self):
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "yes")])
        code, out = self.fanout("run")
        self.assertEqual(code, 0, out)
        repo = self.repos / "alpha"
        seed = self.record("alpha")["seed_commit"]
        plan_tree = self.work / "alpha" / CHILD / "worktrees" / "_plan"
        step_file = plan_tree / "plans" / CHILD / "steps" / "02-b.md"
        record_path = self.work / "fanout" / "parent-plan" / "w1" / "targets" / "alpha.json"

        def commit(message, old, new, path=step_file):
            path.write_text(path.read_text().replace(old, new) if old else new)
            git(plan_tree, "add", "-A")
            git(plan_tree, "commit", "-q", "-m", message)
            sha = git(repo, "rev-parse", f"refs/heads/plan/{CHILD}")
            data = json.loads(record_path.read_text())
            data["final_sha"] = sha
            record_path.write_text(json.dumps(data))
            return sha

        # An operator changes a gate. Before it is recorded, verify fails.
        amend_sha = commit("operator: stricter gate", "gate: test -f 02-b.out", "gate: test -s 02-b.out || test -f 02-b.out")
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("gate text differs", out)

        # Bad amendments are refused: no reason, a commit outside the plan branch history, the seed itself.
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", amend_sha, "--reason", " ")
        self.assertEqual(code, 1, out)
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", self.bases["alpha"], "--reason", "x")
        self.assertEqual(code, 1, out)
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", seed, "--reason", "x")
        self.assertEqual(code, 1, out)

        # Recorded, verify passes and reports the amendment and its reason. A repeat is a no-op.
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", amend_sha, "--reason", "re-pin after review")
        self.assertEqual(code, 0, out)
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", amend_sha, "--reason", "again")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.record("alpha")["amendments"]), 1)
        code, out = self.fanout("verify")
        self.assertEqual(code, 0, out)
        self.assertIn("operator amendments: 1", out)
        self.assertIn("re-pin after review", out)

        # A later, unrecorded gate change (for example by an agent) still fails.
        commit("agent weakens gate", "gate: test -s 02-b.out || test -f 02-b.out", "gate: true")
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("gate text differs", out)

        # An amendment that changes files outside plans/<child>/ is refused.
        outside = commit("touch product", None, "x\n", path=plan_tree / "product.txt")
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", outside, "--reason", "x")
        self.assertEqual(code, 1, out)
        self.assertIn("may change only", out)

    def test_amendment_does_not_launder_an_earlier_gate_change(self):
        # An unrecorded gate change, followed by an operator amendment that does not touch that gate,
        # must still fail: the amendment accepts only the gate changes that it makes itself.
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "yes")])
        code, out = self.fanout("run")
        self.assertEqual(code, 0, out)
        repo = self.repos / "alpha"
        plan_tree = self.work / "alpha" / CHILD / "worktrees" / "_plan"
        steps = plan_tree / "plans" / CHILD / "steps"
        record_path = self.work / "fanout" / "parent-plan" / "w1" / "targets" / "alpha.json"
        first = steps / "01-a.md"
        first.write_text(first.read_text().replace("gate: test -f 01-a.out", "gate: true"))
        git(plan_tree, "commit", "-q", "-am", "agent weakens 01-a")
        second = steps / "02-b.md"
        second.write_text(second.read_text() + "\nOperator note.\n")
        git(plan_tree, "commit", "-q", "-am", "operator note on 02-b")
        sha = git(repo, "rev-parse", f"refs/heads/plan/{CHILD}")
        data = json.loads(record_path.read_text())
        data["final_sha"] = sha
        record_path.write_text(json.dumps(data))
        code, out = self.fanout("amend", "--repo", "alpha", "--commit", sha, "--reason", "note only")
        self.assertEqual(code, 0, out)
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("step 01-a gate text differs", out)

    def test_failed_gate_leaves_target_incomplete(self):
        self.seed_wave()
        code, out = self.fanout("run", FANOUT_FAIL_REPO="beta")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.record("alpha")["status"], "done", out)
        self.assertEqual(self.record("beta")["status"], "blocked", out)
        self.assertEqual(self.record("beta")["exit_code"], 11)
        code, out = self.fanout("verify")
        self.assertEqual(code, 1, out)
        self.assertIn("alpha: verified done", out)
        self.assertIn("beta: FAIL", out)

    def test_held_driver_lock_is_not_relaunched(self):
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "yes")])
        lock = self.work / "alpha" / CHILD / ".lock"
        lock.parent.mkdir(parents=True)
        code, out = self.fanout("provision")
        self.assertEqual(code, 1, out)  # an unrecorded runtime directory is refused
        self.assertIn("no recorded provenance", out)
        shutil.rmtree(self.work / "alpha")
        code, out = self.fanout("provision")
        self.assertEqual(code, 0, out)
        lock.parent.mkdir(parents=True)
        holder = subprocess.Popen(["flock", str(lock), "sleep", "30"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.terminate)
        for _ in range(50):
            if subprocess.run(["flock", "-n", str(lock), "true"]).returncode:
                break
            subprocess.run(["sleep", "0.1"])
        code, out = self.fanout("run")
        self.assertEqual(code, 1, out)
        self.assertIn("driver lock is held", out)
        self.assertIsNone(subprocess.run(["git", "-C", str(self.repos / "alpha"), "rev-parse", "--verify",
                                          "--quiet", f"refs/heads/plan/{CHILD}"],
                                         capture_output=True).stdout.strip() or None)

    # ---- ready and provision refusals ----

    def test_ready_is_read_only_and_passes(self):
        self.seed_wave()
        refs = git(self.repos / "alpha", "for-each-ref")
        code, out = self.fanout("ready")
        self.assertEqual(code, 0, out)
        self.assertIn("alpha: ready seed child on main", out)
        self.assertEqual(git(self.repos / "alpha", "for-each-ref"), refs)
        self.assertFalse((self.work / "fanout").exists())

    def test_ready_rejects_a_seed_that_fails_the_target_checker(self):
        bad = self.plan_dir / "seeds" / CHILD / "steps" / "01-a.md"
        bad.write_text(bad.read_text().replace("gate: test -f 01-a.out\n", ""))
        self.seed_wave()
        code, out = self.fanout("ready")
        self.assertEqual(code, 1, out)
        self.assertIn("fails the target plan checker", out)

    def test_ready_and_provision_reject_unknown_dirty_foreign_and_substituted(self):
        cases = {
            "unknown": (lambda: None, "missing or substituted checkout"),
            "dirty": (lambda: (self.repos / "dirty" / "new.txt").write_text("x\n"), "uncommitted changes"),
            "foreign": (lambda: git(self.repos / "foreign", "branch", f"rollout/{CHILD}"),
                        "no recorded provenance"),
            "linked": (lambda: (self.repos / "linked").symlink_to(self.repos / "alpha"),
                       "missing or substituted checkout"),
        }
        for name in ("dirty", "foreign"):
            self.make_repo(name)
        for name, (prepare, message) in cases.items():
            prepare()
            self.wave([(name, "main", CHILD, "seed", f"seeds/{CHILD}", "yes")], name=name)
            for command in ("ready", "provision"):
                with self.subTest(case=name, command=command):
                    code, out = self.fanout(command, wave=name)
                    self.assertEqual(code, 1, out)
                    self.assertIn(message, out)
        self.assertEqual(git(self.repos / "alpha", "branch", "--list", f"rollout/{CHILD}"), "")

    def test_provision_rejects_advanced_base_and_changed_seed(self):
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "no")])
        code, out = self.fanout("provision")
        self.assertEqual(code, 0, out)
        seed = self.record("alpha")["seed_commit"]
        self.assertEqual(git(self.repos / "alpha", "rev-parse", f"refs/heads/rollout/{CHILD}"), seed)
        self.assert_base_untouched("alpha")
        code, out = self.fanout("provision")
        self.assertEqual(code, 0, out)  # idempotent

        goal = self.plan_dir / "seeds" / CHILD / "goal.md"
        goal.write_text("# Changed goal\n")
        code, out = self.fanout("provision")
        self.assertEqual(code, 1, out)
        self.assertIn("seed differs", out)
        code, out = self.fanout("ready")
        self.assertEqual(code, 1, out)
        goal.write_text("# Goal\n")

        repo = self.repos / "alpha"
        (repo / "README.md").write_text("advanced\n")
        git(repo, "commit", "-q", "-am", "advance base")
        code, out = self.fanout("provision")
        self.assertEqual(code, 1, out)
        self.assertIn("base branch advanced", out)

    # ---- published and pinned ----

    def test_published_after_fast_forward_of_the_remote_base(self):
        remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        repo = self.repos / "alpha"
        git(repo, "remote", "add", "origin", str(remote))
        git(repo, "push", "-q", "origin", "main")
        self.wave([("alpha", "main", CHILD, "seed", f"seeds/{CHILD}", "yes")])
        code, out = self.fanout("run")
        self.assertEqual(code, 0, out)
        code, out = self.fanout("published")
        self.assertEqual(code, 1, out)
        self.assertIn("is not on origin/main", out)
        final = self.record("alpha")["final_sha"]
        # Simulate the merge on the remote: a fast-forward of main to the result (no force).
        git(repo, "push", "-q", "origin", f"{final}:refs/heads/main")
        code, out = self.fanout("published")
        self.assertEqual(code, 0, out)
        self.assertIn(f"alpha: published {final}", out)
        self.assert_base_untouched("alpha")

    def test_pinned_mode_and_provision_only_target(self):
        repo = self.make_repo("gamma")
        write_plan(repo / "plans" / CHILD)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "commit child plan")
        pin = git(repo, "rev-parse", "HEAD")
        self.bases["gamma"] = pin
        self.wave([("gamma", "main", CHILD, "pinned", pin, "yes"),
                   ("beta", "main", CHILD, "seed", f"seeds/{CHILD}", "no")])
        code, out = self.fanout("ready")
        self.assertEqual(code, 0, out)
        code, out = self.fanout("run")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.record("gamma")["seed_commit"], pin)
        self.assertEqual(self.record("beta")["status"], "provisioned")
        code, out = self.fanout("verify")
        self.assertEqual(code, 0, out)
        self.assertIn("gamma: verified done", out)
        self.assertIn("beta: verified seeded", out)
        self.assert_base_untouched("gamma")
        self.assert_base_untouched("beta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
