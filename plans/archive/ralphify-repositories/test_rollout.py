#!/usr/bin/env python3
"""Offline launcher and runner checks using disposable repositories and a fake agent."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import rollout


RUNNER = rollout.HERE.parents[2] / "ralph-looper"
ALLOWLIST = {"gpx_parser": "master", "metadata_mcp": "main"}

FAKE_AGENT = """\
import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys

assert "GITHUB_TOKEN" not in os.environ
assert "RUN_LIVE_OPENAI_TESTS" not in os.environ
mode, marker = sys.argv[1:]
sys.stdin.read()
step = os.environ["RALPH_STEP"]
base = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
name = Path("plans/ralphify/goal.md").read_text().split()[2]
target = Path("plans/ralphify/steps") / (step + ".md")
inputs = Path("plans/ralphify/template-inputs")
if step == "01-adopt-context":
    for source in inputs.rglob("*.txt"):
        dest = Path(str(source.relative_to(inputs)).removesuffix(".txt"))
        if dest.as_posix() not in {"Dockerfile", ".gitignore"}:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
    resume = Path(marker)
    if mode == "handoff" and name == "metadata_mcp" and not resume.exists():
        resume.write_text(base)
        print('{"is_error":true,"result":"usage limit reached"}')
        sys.exit(1)
    if mode == "handoff" and name == "metadata_mcp":
        assert resume.read_text() == base
        assert Path("plans/AGENTS.md").is_file()
elif step == "02-build-and-test":
    Path("Dockerfile").write_text("FROM scratch\\n")
    Path(".dockerignore").write_text(".git\\n")
    gate = "exit 42\\n" if mode == "fail" and name == "metadata_mcp" else "echo fake Docker gate\\n"
    Path("scripts/test_docker.sh").write_text(gate)
else:
    notes = {
        "Base commit": base,
        "Commands": "bash scripts/test_docker.sh",
        "Docker build": "PASS fixture image",
        "Tests": "PASS fixture assertion",
        "Skips": "none",
        "FUSE": "n/a",
        "UTC date": datetime.date.today().isoformat(),
    }
    text = target.read_text()
    for key, value in notes.items():
        text = text.replace(f"- {key}: PENDING", f"- {key}: {value}")
    target.write_text(text)
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-qm", f"fake: {step}"], check=True)
print('{"result":"fixture"}')
"""


def write(repo, path, text):
    dest = repo / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


def init_repo(path, branch):
    path.mkdir()
    rollout.git(path, "init", "-q", "-b", branch)
    rollout.git(path, "config", "user.email", "fixture@example.invalid")
    rollout.git(path, "config", "user.name", "Rollout Fixture")


def commit(repo, message):
    rollout.git(repo, "add", "-A")
    rollout.git(repo, "commit", "-qm", message)
    return rollout.ref(repo, "HEAD")


class LauncherTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="ralph-rollout-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repos = self.root / "repos"
        self.repos.mkdir()
        self.state = self.root / "state"
        self.work = self.root / "work"
        self.template = self.root / "template"
        self.runner = self.root / "runner" / "ralph-looper"
        init_repo(self.runner.parent, "main")
        for path in ("ralph-looper", "lib/agents.sh", "lib/pick_step.py", "lib/PROMPT.md", "lib/usage.py"):
            dest = self.runner.parent / path
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes((RUNNER.parent / path).read_bytes())
            dest.chmod((RUNNER.parent / path).stat().st_mode & 0o777)
        runner_pin = commit(self.runner.parent, "fixture uses the actual runner")

        init_repo(self.template, "main")
        for path in rollout.SCAFFOLD:
            write(self.template, path, f"Fixture for {path}\n")
        write(self.template, "AGENTS.md", "Read [repo-template](https://github.com/dullroar/repo-template)"
              " and [ralph-looper](https://github.com/dullroar/ralph-looper) before structure changes.\n")
        write(self.template, "scripts/build_indexes.py", "print('fixture indexes checked')\n")
        # Use the actual Ralph context plan checker to validate the child seeds.
        for path in ("scripts/check_plan.py", "scripts/ctx_common.py"):
            write(self.template, path, (RUNNER.parent / path).read_text())
        write(self.template, "scripts/check_context.py",
              "import check_plan\nraise SystemExit(check_plan.main([]))\n")
        template_pin = commit(self.template, "pin fixture scaffold")
        pins = patch.multiple(rollout, TEMPLATE_REV=template_pin, RUNNER_REV=runner_pin)
        pins.start()
        self.addCleanup(pins.stop)

        self.bases = {}
        for name, branch in {**ALLOWLIST, "unrelated": "main"}.items():
            repo = self.repos / name
            init_repo(repo, branch)
            write(repo, "README.md", f"# {name}\n")
            write(repo, "scripts/check_context.py", "print('legacy context checked')\n")
            self.bases[name] = commit(repo, "base")
        self.fake = self.root / "fake_agent.py"
        self.fake.write_text(FAKE_AGENT)
        self.marker = self.root / "resume-marker"
        overrides = patch.dict(os.environ, {
            "RALPH_WORK": str(self.work),
            "ROLLOUT_STATE": str(self.state),
            "AGENT_CMD": "exit 94",
            "GATE_TIMEOUT_MIN": "invalid-parent-value",
            "GITHUB_TOKEN": "fixture-only",
            "RUN_LIVE_OPENAI_TESTS": "1",
        })
        overrides.start()
        self.addCleanup(overrides.stop)

    def run_rollout(self, mode):
        args = argparse.Namespace(repos_root=str(self.repos), template_repo=str(self.template),
                                  runner=str(self.runner), jobs=2, agent="claude")
        command = shlex.join([sys.executable, str(self.fake), mode, str(self.marker)])
        output, errors = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {"RALPH_CHILD_AGENT_CMD": command, "RALPH_CHILD_MAX_ATTEMPTS": "1"}):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = rollout.run(args, ALLOWLIST)
        return code, output.getvalue(), errors.getvalue()

    def result(self, name):
        path = self.state / (name + ".json")
        return json.loads(path.read_text())

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return rollout.verify(ALLOWLIST)

    def assert_base_untouched(self, name):
        repo = self.repos / name
        self.assertEqual(rollout.ref(repo, "HEAD"), self.bases[name])
        self.assertEqual(rollout.git_text(repo, "status", "--porcelain"), "")

    def test_resume_after_handoff_and_reject_stale_evidence(self):
        with self.assertRaises(FileNotFoundError):
            self.verify()
        code, output, error = self.run_rollout("handoff")
        self.assertEqual(code, 1, output + error)
        self.assertIn("metadata_mcp: exit 75", error)
        self.assertEqual(self.result("metadata_mcp")["exit_code"], 75)
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.verify(), 1)
        success = self.result("gpx_parser")
        self.assertEqual(success["status"], "done", error)

        code, output, error = self.run_rollout("handoff")
        self.assertEqual(code, 0, output + error)
        self.assertIn("gpx_parser: reused", output)
        self.assertEqual(self.result("gpx_parser"), success)
        self.assertEqual(self.verify(), 0)
        for name in (*ALLOWLIST, "unrelated"):
            self.assert_base_untouched(name)
        unrelated = self.repos / "unrelated"
        self.assertIsNone(rollout.ref(unrelated, rollout.SEED_REF))
        self.assertIsNone(rollout.ref(unrelated, rollout.PLAN_REF))
        self.assertFalse((self.work / "unrelated").exists())

        # Verify detects overwritten logs and plan branches independently.
        log = Path(success["evidence"]["path"])
        original = log.read_bytes()
        log.write_text("replacement evidence\n")
        self.assertEqual(self.verify(), 1)
        log.write_bytes(original)
        self.assertEqual(self.verify(), 0)
        repo = self.repos / "gpx_parser"
        rollout.git(repo, "update-ref", rollout.PLAN_REF, self.bases["gpx_parser"])
        self.assertEqual(self.verify(), 1)

    def test_failed_gate_leaves_child_incomplete(self):
        code, output, error = self.run_rollout("fail")
        self.assertEqual(code, 1, output + error)
        self.assertIn("metadata_mcp: exit 11", error)
        self.assertIn("gate-02-build-and-test.out", error)
        self.assertEqual(self.result("gpx_parser")["status"], "done")
        self.assertEqual(self.result("metadata_mcp")["status"], "stopped")
        self.assertEqual(self.verify(), 1)

    def test_preflight_rejects_dirty_and_unknown_targets(self):
        repo = self.repos / "metadata_mcp"
        dirty = repo / "untracked.txt"
        dirty.write_text("uncommitted\n")
        with self.assertRaisesRegex(rollout.RolloutError, "uncommitted changes"):
            self.run_rollout("pass")
        self.assertIsNone(rollout.ref(self.repos / "gpx_parser", rollout.SEED_REF))
        dirty.unlink()
        with self.assertRaisesRegex(rollout.RolloutError, "unknown target"):
            rollout.preflight(self.repos, self.state, self.work, ALLOWLIST, {"targets": {"unrelated": {}}})
        with self.assertRaisesRegex(rollout.RolloutError, "substituted checkout"):
            (self.repos / "substitute").symlink_to(repo, target_is_directory=True)
            rollout.preflight(self.repos, self.state, self.work, {"substitute": "main"}, {})

    def test_pinned_inputs_and_base_drift(self):
        patched = self.runner.parent / "lib/agents.sh"
        patched.write_text(patched.read_text() + "\n# drift\n")
        with self.assertRaisesRegex(rollout.RolloutError, "differs from the pinned revision"):
            self.run_rollout("pass")
        repo = self.repos / "gpx_parser"
        base_sha = self.bases["gpx_parser"]
        row = {
            "repo": str(repo), "identity": rollout.git_identity(repo), "base": "master",
            "base_sha": base_sha, "seed_dir": str(self.state / "seeds" / "gpx_parser"),
            "runtime": str(self.work / "gpx_parser" / "ralphify"), "seed_sha": None,
        }
        write(repo, "README.md", "new base\n")
        commit(repo, "advance base")
        with self.assertRaisesRegex(rollout.RolloutError, "base has changed"):
            rollout.preflight(self.repos, self.state, self.work, ALLOWLIST, {"targets": {"gpx_parser": row}})

    def test_preflight_rejects_foreign_git_directory_and_seed_ref(self):
        repo = self.repos / "gpx_parser"
        substitute = self.repos / "substitute"
        rollout.git(repo, "worktree", "add", "-b", "main", str(substitute), "HEAD")
        with self.assertRaisesRegex(rollout.RolloutError, "must own"):
            rollout.preflight(self.repos, self.state, self.work, {"substitute": "main"}, {})
        rollout.git(repo, "branch", "rollout/ralphify")
        with self.assertRaisesRegex(rollout.RolloutError, "no recorded provenance"):
            self.run_rollout("pass")
        self.assertIsNone(rollout.ref(self.repos / "metadata_mcp", rollout.SEED_REF))

    def test_child_lease_survives_supervisor_exit(self):
        lock = self.root / "lease"
        with rollout.locked(lock) as fd:
            process = subprocess.Popen(["sleep", "5"], pass_fds=(fd,))
        try:
            with self.assertRaisesRegex(rollout.RolloutError, "already active"):
                with rollout.locked(lock):
                    self.fail("held lease allowed another launch")
        finally:
            process.terminate()
            process.wait(timeout=5)
        with rollout.locked(lock):
            pass


class EvidenceTest(unittest.TestCase):
    def test_accepts_markdown_that_retains_the_required_evidence(self):
        sha = "a" * 40
        report = f"""
## Results

- Base commit: `{sha}` from
  `git merge-base HEAD plan/ralphify`.
- Commands: PASS.
  `bash scripts/test_docker.sh` passed.
- Docker build: PASS. Built the test image.
- Tests: PASS — 17 tests passed.
- Skips: None.
- FUSE: n/a.
- UTC date: 2026-11-22.
"""
        notes = rollout.verification_notes(report, "metadata_mcp")
        self.assertEqual(notes["Base commit"], sha)
        self.assertEqual(notes["UTC date"], "2026-11-22")
        with self.assertRaisesRegex(rollout.RolloutError, "required results"):
            rollout.verification_notes(report, "duckdb-fs")
        with self.assertRaisesRegex(rollout.RolloutError, "required results"):
            rollout.verification_notes(report.replace("Tests: PASS", "Tests: FAIL"), "metadata_mcp")

    def test_reference_link_requires_a_matching_reference_in_the_contract(self):
        url = "https://github.com/dullroar/repo-template"
        definition = f"[layout]: {url}"
        self.assertFalse(rollout.has_contract_link(definition, url))
        self.assertTrue(rollout.has_contract_link(f"Read [repo-template][layout].\n\n{definition}", url))

    def test_reads_commit_after_an_explanation_and_commands_in_a_fence(self):
        sha = "a" * 40
        report = f"""
## Results

- Base commit: PASS. The merge base was
  `{sha}`.
- Commands: PASS. The gate ran the following command.

  ```bash
  python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check
  ```

- Docker build: PASS. Built the test image.
- Tests: PASS. 649 tests passed.
- Skips: Eight opt-in checks.
- FUSE: n/a
- UTC date: 2026-11-22
"""
        self.assertEqual(rollout.verification_notes(report, "compliance_poc")["Base commit"], sha)
        with self.assertRaisesRegex(rollout.RolloutError, "required results"):
            rollout.verification_notes(report.replace("scripts/test_docker.sh", "true"), "compliance_poc")
        with self.assertRaisesRegex(rollout.RolloutError, "required results"):
            rollout.verification_notes(report.replace(sha, sha + " or " + "b" * 40), "compliance_poc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
