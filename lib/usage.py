#!/usr/bin/env python3
"""Read the raw output of one agent run. Append a record to the ledger. Print a usage block.

Usage: usage.py --agent claude|codex|copilot|other --out FILE --ledger FILE --rc N --seconds N
                [--step ID] [--tier T] [--model M] [--effort E] [--head-before SHA] [--cwd DIR]

Prints the usage block (never the prompt) to stdout. The last line is `outcome: recorded|limit`.
Cost: claude gives USD. copilot gives AI credits (USD is an estimate). codex gives tokens only.
Ported from the loop driver of an earlier project; it handles the real JSON of each CLI.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import re
import subprocess
import time


def git(cwd: str, *a: str) -> str:
    try:
        return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--rc", type=int, default=0)
    ap.add_argument("--seconds", type=int, default=0)
    ap.add_argument("--step", default="")
    ap.add_argument("--tier", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--effort", default="")
    ap.add_argument("--head-before", default="")
    ap.add_argument("--cwd", default=".")
    a = ap.parse_args()
    agent, rc = a.agent, a.rc

    rec: dict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "step": a.step, "agent": agent,
                 "exit_code": rc, "seconds": a.seconds, "tier": a.tier, "model_requested": a.model,
                 "effort_requested": a.effort, "cost_usd": None, "cost_est_usd": None, "ai_credits": None,
                 "tok_fresh_in": None, "tok_cache_read": None, "tok_cache_write": None, "tok_out": None,
                 "tok_reasoning": None, "api_calls": None}
    reported: dict[str, int] = {}
    thread_id, result = "", ""
    errors: list[str] = []
    usage: dict = {}
    quota_error = False
    out = pathlib.Path(a.out)
    raw = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""

    if agent == "claude":
        try:
            data = json.loads(raw)
        except ValueError:
            data = {}
        if isinstance(data, dict):
            rec["cost_usd"] = data.get("total_cost_usd", data.get("cost_usd"))
            usage = data.get("usage") or {}
            for name, u in (data.get("modelUsage") or {}).items():
                reported[name] = int((u or {}).get("outputTokens") or 0)
            rec.update(tok_fresh_in=(usage.get("input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0),
                       tok_cache_read=usage.get("cache_read_input_tokens"),
                       tok_cache_write=usage.get("cache_creation_input_tokens"),
                       tok_out=usage.get("output_tokens"), api_calls=data.get("num_turns"))
            result = str(data.get("result") or "")
            errors.append(result)
    else:
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            et = event.get("type")
            if agent == "copilot":
                d = event.get("data") or {}
                if et in ("model.call_start", "model.call_final_result") and d.get("model"):
                    reported[d["model"]] = reported.get(d["model"], 0) + 1
                if et == "assistant.message" and not d.get("toolRequests"):
                    result = str(d.get("content") or "")
                elif et == "assistant.usage":
                    for key, field in (("input_tokens", "inputTokens"), ("output_tokens", "outputTokens")):
                        if isinstance(d.get(field), int):
                            usage[key] = usage.get(key, 0) + d[field]
                elif et == "session.usage_checkpoint":
                    snap = d.get("accountingSnapshot") or {}
                    mm = snap.get("modelMetrics") or {}
                    if mm:
                        t = dict.fromkeys(("in", "read", "write", "out", "reason", "calls"), 0)
                        reported = {}
                        for name, m in mm.items():
                            u = (m or {}).get("usage") or {}
                            t["in"] += u.get("inputTokens") or 0
                            t["read"] += u.get("cacheReadTokens") or 0
                            t["write"] += u.get("cacheWriteTokens") or 0
                            t["out"] += u.get("outputTokens") or 0
                            t["reason"] += u.get("reasoningTokens") or 0
                            t["calls"] += ((m or {}).get("requests") or {}).get("count") or 0
                            reported[name] = u.get("outputTokens") or 0
                        rec.update(tok_fresh_in=max(t["in"] - t["read"] - t["write"], 0), tok_cache_read=t["read"],
                                   tok_cache_write=t["write"], tok_out=t["out"], tok_reasoning=t["reason"],
                                   api_calls=t["calls"])
                        nano = snap.get("totalNanoAiu")
                        if isinstance(nano, (int, float)):
                            rec["ai_credits"] = round(nano / 1e9, 4)
                            rec["cost_est_usd"] = round(nano / 1e9 * 0.01, 4)  # 1 credit = $0.01 (estimate)
                        for entry in d.get("promptCacheBreakState") or []:
                            for mdl in (entry.get("models") or {}).values():
                                if mdl.get("reasoning_effort"):
                                    rec["effort_reported"] = mdl["reasoning_effort"]
                elif et == "session.error":
                    errors.append(str(d.get("message") or ""))
                    quota_error |= d.get("errorType") == "quota"
            elif et == "thread.started":
                thread_id = str(event.get("thread_id") or "")
            elif et == "turn.completed":
                usage = event.get("usage") or {}
                cached = usage.get("cached_input_tokens") or 0
                rec.update(tok_fresh_in=max((usage.get("input_tokens") or 0) - cached, 0), tok_cache_read=cached,
                           tok_cache_write=usage.get("cache_write_input_tokens"), tok_out=usage.get("output_tokens"),
                           tok_reasoning=usage.get("reasoning_output_tokens"))
            elif et == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "agent_message":
                    result = str(item.get("text") or "")
            elif et in ("error", "turn.failed"):
                errors.append(str(event.get("error") or event.get("message") or ""))

    if agent == "codex" and thread_id:  # codex --json never names the model; its session file does
        home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
        for f in glob.glob(os.path.join(home, "sessions", "**", f"rollout-*{thread_id}.jsonl"), recursive=True):
            text = pathlib.Path(f).read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'"model":"([^"]+)"', text):
                reported[m.group(1)] = reported.get(m.group(1), 0) + 1
            eff = re.findall(r'"effort":"([^"]+)"', text)
            if eff:
                rec["effort_reported"] = eff[-1]

    primary = max(reported, key=reported.get) if reported else ""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    rec["model_reported"] = primary
    rec["models_all"] = sorted(reported)
    rec["model_mismatch"] = bool(a.model) and (not primary or norm(a.model) not in norm(primary))

    errfile = pathlib.Path(str(out) + ".err")
    if rc and errfile.exists():
        errors.append(errfile.read_text(encoding="utf-8", errors="replace").strip())
    error_text = "\n".join(filter(None, errors))
    rec["result_tail"] = ((error_text if rc or quota_error else "") or result)[-300:]

    head_after = git(a.cwd, "rev-parse", "HEAD")
    if head_after and a.head_before and head_after != a.head_before:
        rec["commit"] = head_after[:12]
        stat = git(a.cwd, "diff", "--shortstat", a.head_before, head_after)
        for key, pat in (("files_changed", r"(\d+) files? changed"), ("lines_added", r"(\d+) insertions?"),
                         ("lines_deleted", r"(\d+) deletions?")):
            mm_ = re.search(pat, stat)
            rec[key] = int(mm_.group(1)) if mm_ else 0
    rec["usage_limited"] = quota_error or (rc != 0 and bool(re.search(
        r"\bhit your\b[^\n]{0,100}\blimit\b|\busage[_ ]limit[_ ]reached\b|rate limit|quota", error_text, re.I)))

    with open(a.ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    spent = 0.0
    spent_est = 0.0
    for line in open(a.ledger, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        spent += float(r.get("cost_usd") or 0)
        spent_est += float(r.get("cost_usd") or r.get("cost_est_usd") or 0)

    def v(x):
        return "n/a" if x is None else x

    print(f"--- usage: step={a.step or '-'} agent={agent} ---")
    print(f"model: requested={a.model or 'cli-default'} reported={primary or 'NOT-REPORTED'}"
          + (f" also={','.join(m for m in sorted(reported) if m != primary)}" if len(reported) > 1 else "")
          + ("  MISMATCH" if rec["model_mismatch"] else ""))
    print(f"effort: requested={a.effort or 'default'} reported={rec.get('effort_reported', 'n/a')}  tier={a.tier or '-'}")
    print(f"time: {a.seconds}s  exit_code: {rc}  api_calls: {v(rec['api_calls'])}")
    print(f"tokens: fresh_in={v(rec['tok_fresh_in'])} cache_read={v(rec['tok_cache_read'])} "
          f"cache_write={v(rec['tok_cache_write'])} out={v(rec['tok_out'])} reasoning={v(rec['tok_reasoning'])}")
    print(f"cost: usd={v(rec['cost_usd'])} est_usd={v(rec['cost_est_usd'])} ai_credits={v(rec['ai_credits'])}")
    print(f"cumulative: usd={spent:.4f} usd_incl_estimates={spent_est:.4f}")
    if "commit" in rec:
        print(f"git: commit={rec['commit']} files={rec['files_changed']} +{rec['lines_added']} -{rec['lines_deleted']}")
    print(f"usage_limited: {str(rec['usage_limited']).lower()}")
    print("outcome: " + ("limit" if rec["usage_limited"] else "recorded"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
