#!/usr/bin/env python3
"""Summarize usage ledgers by route and model: cost, time, tokens and first-attempt gate pass rate.

Usage: report.py [--ledger FILE]... [--work DIR] [--by plan|repo] [--format md|tsv|json] [--strict]

Without --ledger, the tool reads every `ledger.jsonl` under --work (default $RALPH_WORK, else ~/repo-work).
A run line has `route`, `attempt` and `gate`. A gate line ({kind: gate}) gives the gate result of
one attempt. The tool joins them by (ledger, step, attempt). Old lines without these fields count as
attempts with an unknown gate. A malformed line is counted and reported. With --strict it is an error.
The output has no prompts, no paths and no user names.
Exit codes: 0 ok, 2 unreadable input (or a malformed line with --strict).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys


def read_ledger(path: pathlib.Path, bad: list[int]) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            bad[0] += 1
            continue
        if not isinstance(r, dict):
            bad[0] += 1
            continue
        rows.append(r)
    return rows


def group_key(r: dict, by: str, ledger: pathlib.Path) -> tuple:
    extra = ""
    if by == "plan":
        extra = ledger.parent.name
    elif by == "repo":
        extra = ledger.parent.parent.name
    model = r.get("model_reported") or r.get("model_requested") or "-"
    return (extra, r.get("route") or r.get("agent") or "unknown", model)


def summarize(ledgers: list[pathlib.Path], by: str) -> tuple[list[dict], int]:
    bad = [0]
    groups: dict[tuple, dict] = {}
    for ledger in ledgers:
        rows = read_ledger(ledger, bad)
        gates: dict[tuple, str] = {}
        for r in rows:
            if r.get("kind") == "gate":
                gates[(r.get("step"), r.get("attempt"))] = r.get("gate", "none")
        for r in rows:
            if r.get("kind") == "gate":
                continue
            g = groups.setdefault(group_key(r, by, ledger), {
                "steps": set(), "attempts": 0, "first": 0, "first_pass": 0, "secs": [], "tok_in": 0,
                "tok_out": 0, "usd": 0.0, "usd_reported": 0})
            g["steps"].add((str(ledger), r.get("step")))
            g["attempts"] += 1
            gate = gates.get((r.get("step"), r.get("attempt")), r.get("gate") or "none")
            if r.get("attempt") == 1 and gate in ("pass", "fail"):
                g["first"] += 1
                g["first_pass"] += gate == "pass"
            g["secs"].append(r.get("seconds") or 0)
            g["tok_in"] += (r.get("tok_fresh_in") or 0) + (r.get("tok_cache_read") or 0)
            g["tok_out"] += r.get("tok_out") or 0
            cost = r.get("cost_usd")
            if cost is None:
                cost = r.get("cost_est_usd")
            if cost is not None:
                g["usd"] += float(cost)
                g["usd_reported"] += 1
    out = []
    for (extra, route, model), g in sorted(groups.items()):
        out.append({
            **({by: extra} if by else {}), "route": route, "model": model, "steps": len(g["steps"]),
            "attempts": g["attempts"], "first_attempts_with_gate": g["first"],
            "first_pass_rate": round(g["first_pass"] / g["first"], 3) if g["first"] else None,
            "seconds_total": sum(g["secs"]), "seconds_median": statistics.median(g["secs"]) if g["secs"] else 0,
            "tokens_in": g["tok_in"], "tokens_out": g["tok_out"],
            "usd": round(g["usd"], 4) if g["usd_reported"] else None})
    return out, bad[0]


def fmt(v, key: str) -> str:
    if v is None:
        return "not reported" if key == "usd" else "n/a"
    if key == "first_pass_rate":
        return f"{v * 100:.0f}%"
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize usage ledgers by route and model.")
    ap.add_argument("--ledger", action="append", default=[], help="a ledger file (repeatable)")
    ap.add_argument("--work", default="", help="directory with ledgers (default $RALPH_WORK, else ~/repo-work)")
    ap.add_argument("--by", choices=("plan", "repo"), default="")
    ap.add_argument("--format", choices=("md", "tsv", "json"), default="md")
    ap.add_argument("--strict", action="store_true", help="a malformed line is an error")
    a = ap.parse_args()
    if a.ledger:
        ledgers = [pathlib.Path(p) for p in a.ledger]
    else:
        root = pathlib.Path(a.work or os.environ.get("RALPH_WORK") or os.path.expanduser("~/repo-work"))
        if not root.is_dir():
            print("report: work directory not found", file=sys.stderr)
            return 2
        ledgers = sorted(root.rglob("ledger.jsonl"))
    try:
        rows, bad = summarize(ledgers, a.by)
    except (OSError, UnicodeDecodeError):
        print("report: cannot read a ledger", file=sys.stderr)
        return 2
    if bad and a.strict:
        print(f"report: {bad} malformed line(s)", file=sys.stderr)
        return 2
    cols = ([a.by] if a.by else []) + ["route", "model", "steps", "attempts", "first_pass_rate", "seconds_total",
                                       "seconds_median", "tokens_in", "tokens_out", "usd"]
    if a.format == "json":
        print(json.dumps({"rows": rows, "malformed_lines": bad}, indent=2))
    else:
        cells = [[fmt(r.get(c), c) for c in cols] for r in rows]
        if a.format == "tsv":
            print("\t".join(cols))
            for c in cells:
                print("\t".join(c))
        else:
            print("| " + " | ".join(cols) + " |")
            print("| " + " | ".join("---" for _ in cols) + " |")
            for c in cells:
                print("| " + " | ".join(c) + " |")
        if bad:
            print(f"\nmalformed lines skipped: {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
