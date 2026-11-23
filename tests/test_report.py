#!/usr/bin/env python3
"""Run me when: I changed lib/report.py or the ledger fields in lib/usage.py.
Tests the route report with ledger fixtures. Needs only python3."""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
REPORT = HERE / "lib" / "report.py"


def run(*args):
    return subprocess.run([sys.executable, "-I", str(REPORT), *args], capture_output=True, text=True)


def run_line(step, route, attempt, gate="none", secs=10, usd=0.5, model="m1", **extra):
    r = {"step": step, "agent": route, "route": route, "attempt": attempt, "gate": gate, "seconds": secs,
         "model_reported": model, "tok_fresh_in": 10, "tok_cache_read": 90, "tok_out": 5, "cost_usd": usd}
    r.update(extra)
    return json.dumps(r)


def gate_line(step, route, attempt, gate):
    return json.dumps({"kind": "gate", "step": step, "route": route, "attempt": attempt, "gate": gate})


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    led = d / "plan-a" / "ledger.jsonl"
    led.parent.mkdir()
    old = json.dumps({"step": "00-old", "agent": "claude", "seconds": 7, "model_reported": "m1", "cost_usd": 0.1})
    lines = [
        old,
        run_line("01-a", "claude", 1), gate_line("01-a", "claude", 1, "pass"),
        run_line("02-b", "claude", 1), gate_line("02-b", "claude", 1, "fail"),
        run_line("02-b", "claude", 2), gate_line("02-b", "claude", 2, "pass"),
        run_line("03-c", "codex", 1, usd=None, model="m2"), gate_line("03-c", "codex", 1, "pass"),
        run_line("04-s", "script", 1, usd=0.0, model="-"), gate_line("04-s", "script", 1, "pass"),
        "{not json",
    ]
    led.write_text("\n".join(lines) + "\n")

    r = run("--ledger", str(led), "--format", "json")
    check(r.returncode == 0, "json run failed: " + r.stderr)
    data = json.loads(r.stdout)
    check(data["malformed_lines"] == 1, "malformed line not counted")
    rows = {(x["route"], x["model"]): x for x in data["rows"]}
    c = rows[("claude", "m1")]
    check(c["steps"] == 3 and c["attempts"] == 4, f"claude steps/attempts wrong: {c}")
    check(c["first_attempts_with_gate"] == 2 and c["first_pass_rate"] == 0.5, f"first-pass rate wrong: {c}")
    check(c["seconds_total"] == 37, f"seconds total wrong: {c}")
    check(c["tokens_in"] == 300 and c["tokens_out"] == 15, f"tokens wrong: {c}")
    check(abs(c["usd"] - 1.6) < 1e-9, f"usd wrong: {c}")
    x = rows[("codex", "m2")]
    check(x["usd"] is None and x["first_pass_rate"] == 1.0, f"codex row wrong: {x}")

    r = run("--ledger", str(led), "--format", "md")
    check(r.returncode == 0 and "not reported" in r.stdout and "malformed lines skipped: 1" in r.stdout, "md output wrong")
    check(str(d) not in r.stdout, "output shows a path")
    r = run("--ledger", str(led), "--format", "tsv", "--by", "plan")
    check(r.returncode == 0 and r.stdout.splitlines()[0].startswith("plan\troute"), "tsv header wrong")
    check("plan-a" in r.stdout, "--by plan missing")

    r = run("--ledger", str(led), "--strict")
    check(r.returncode == 2, "--strict must exit 2 on a malformed line")
    r = run("--ledger", str(d / "missing.jsonl"))
    check(r.returncode == 2, "missing file must exit 2")

    r = run("--work", str(d), "--format", "json")
    check(r.returncode == 0 and json.loads(r.stdout)["rows"], "--work discovery failed")
    r = run("--work", str(d / "nope"))
    check(r.returncode == 2, "missing work dir must exit 2")

print("PASS")
