#!/usr/bin/env python3
"""Read and pick plan steps. Standard library only.

Commands:
  pick_step.py ready PLAN_DIR [--max N] [--active ID,ID] [--skip ID,ID]
      Print one JSON line for each ready step to start now (at most N). A step is ready when
      its status is `pending` and every `depends_on` step is `done`. Steps in --active (already
      running or being resumed) count as busy: a new step must not touch the same files.
      Steps in --skip are not started (for example an operator step that waits in this run).
  pick_step.py summary PLAN_DIR
      Print counts. Exit 0 = all done, 10 = work remains, 11 = blocked and nothing can run,
      12 = only operator steps can run (waiting for operator).
  pick_step.py waiting PLAN_DIR     Print the ids of ready operator steps, one a line.
  pick_step.py field FILE KEY       Print one front-matter value (a list prints one item a line).
  pick_step.py set FILE KEY VALUE   Set one scalar front-matter key.
  pick_step.py same SPEC FILE
      Compare the driver-owned keys (gate, touches, agent, fallback, run) of two step files.
      Exit 0 if they are equal. Else print the changed keys and exit 1.
  pick_step.py scope WORKTREE BASE SPEC STEP_FILE
      List the paths changed in WORKTREE since commit BASE (committed, staged, unstaged and
      untracked). A path is allowed if it matches a `touches` entry of SPEC (the same glob rules
      as scripts/check_plan.py), is STEP_FILE, or is a generated index file. Print the allowed
      paths with uncommitted changes (the paths to stage) on stdout, one a line. Print each
      path that is not allowed on stderr and exit 1.
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path


DRIVER_KEYS = ("gate", "touches", "agent", "fallback", "run")
INDEX_FILES = ("memory/AGENTS.md", "plans/AGENTS.md", "scripts/AGENTS.md")


def unquote(v: str) -> str:
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def parse(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict = {}
    key = None
    for raw in text[4:end].split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.*)$", raw)
        if item and key:
            data.setdefault(key, []).append(unquote(item.group(1)))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if not pair:
            continue
        key, value = pair.group(1), pair.group(2).strip()
        if value == "":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [unquote(v) for v in inner.split(",")] if inner else []
        else:
            data[key] = unquote(value)
    return data


def as_list(v) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if str(x)]
    return [str(v)] if v else []


def overlaps(a: str, b: str) -> bool:
    a, b = a.rstrip("/"), b.rstrip("/")
    if a == b or fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    stem = lambda g: re.split(r"[*?\[]", g)[0].rstrip("/")  # noqa: E731
    sa, sb = stem(a), stem(b)
    return bool(sa and sb and (sa == sb or sa.startswith(sb + "/") or sb.startswith(sa + "/")))


def clash(x: dict, y: dict) -> bool:
    if any(overlaps(a, b) for a in as_list(x.get("touches")) for b in as_list(y.get("touches"))):
        return True
    lane = x.get("lane")
    return bool(lane and lane != "none" and lane == y.get("lane"))


def load(plan_dir: Path) -> dict[str, dict]:
    steps = {}
    for p in sorted((plan_dir / "steps").glob("*.md")):
        meta = parse(p.read_text(encoding="utf-8"))
        meta["_file"] = str(p)
        steps[p.stem] = meta
    return steps


def done(steps, sid) -> bool:
    return steps.get(sid, {}).get("status") == "done"


def is_operator(meta: dict) -> bool:
    return meta.get("agent") == "operator"


def ready_now(steps: dict, meta: dict) -> bool:
    return meta.get("status") == "pending" and all(done(steps, d) for d in as_list(meta.get("depends_on")))


def id_list(args: list[str], flag: str) -> list[str]:
    if flag not in args or args.index(flag) + 1 >= len(args):
        return []
    return [a for a in args[args.index(flag) + 1].split(",") if a]


def cmd_ready(plan_dir: Path, args: list[str]) -> int:
    limit = 1
    if "--max" in args:
        limit = int(args[args.index("--max") + 1])
    active, skip = id_list(args, "--active"), id_list(args, "--skip")
    steps = load(plan_dir)
    chosen: list[str] = []
    busy = [steps[a] for a in active if a in steps]
    for sid, meta in steps.items():
        if len(chosen) + len(active) >= limit and limit > 0:
            break
        if sid in active or sid in skip or meta.get("status") != "pending" or sid.startswith("00-"):
            continue
        if not all(done(steps, d) for d in as_list(meta.get("depends_on"))):
            continue
        if any(clash(meta, b) for b in busy):
            continue
        chosen.append(sid)
        busy.append(meta)
        print(json.dumps({"id": sid, "file": meta["_file"], "tier": meta.get("tier", ""),
                          "agent": meta.get("agent", "") if isinstance(meta.get("agent"), str) else "",
                          "touches": as_list(meta.get("touches"))}))
    return 0


def cmd_summary(plan_dir: Path) -> int:
    steps = {k: v for k, v in load(plan_dir).items() if not k.startswith("00-")}
    counts: dict[str, int] = {}
    for m in steps.values():
        counts[m.get("status", "?")] = counts.get(m.get("status", "?"), 0) + 1
    print(json.dumps(counts, sort_keys=True))
    if steps and all(m.get("status") == "done" for m in steps.values()):
        return 0
    runnable = any(
        not is_operator(m) and m.get("status") in ("pending", "in_progress")
        and all(done(steps, d) for d in as_list(m.get("depends_on")))
        for m in steps.values())
    if runnable:
        return 10
    return 12 if any(is_operator(m) and ready_now(steps, m) for m in steps.values()) else 11


def cmd_waiting(plan_dir: Path) -> int:
    steps = {k: v for k, v in load(plan_dir).items() if not k.startswith("00-")}
    for sid, meta in steps.items():
        if is_operator(meta) and ready_now(steps, meta):
            print(sid)
    return 0


def driver_keys(file: Path) -> dict:
    try:
        meta = parse(file.read_text(encoding="utf-8"))
    except OSError:
        meta = {}
    return {k: as_list(meta.get(k)) for k in DRIVER_KEYS}


def cmd_same(spec: Path, file: Path) -> int:
    a, b = driver_keys(spec), driver_keys(file)
    changed = [k for k in DRIVER_KEYS if a[k] != b[k]]
    for k in changed:
        print(k)
    return 1 if changed else 0


def git_paths(wt: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(wt), *args], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def changed_paths(wt: Path, base: str) -> tuple[set[str], set[str]]:
    """Return (all paths changed since BASE, the subset with uncommitted changes)."""
    committed = set(git_paths(wt, "diff", "--name-only", "--no-renames", "-z", base, "HEAD"))
    pending = {e[3:] for e in git_paths(wt, "status", "--porcelain=v1", "-z", "--no-renames",
                                        "--untracked-files=all")}
    return committed | pending, pending


def cmd_scope(wt: Path, base: str, spec: Path, step_file: str) -> int:
    touches = as_list(parse(spec.read_text(encoding="utf-8")).get("touches"))
    bad = 0
    every, pending = changed_paths(wt, base)
    for path in sorted(every):
        ok = "\n" not in path and (path == step_file or path in INDEX_FILES
                                   or any(overlaps(path, t) for t in touches))
        if ok:
            if path in pending:
                print(path)
        else:
            print(f"outside touches: {path!r}" if "\n" in path else f"outside touches: {path}", file=sys.stderr)
            bad += 1
    return 1 if bad else 0


def cmd_field(file: Path, key: str) -> int:
    value = parse(file.read_text(encoding="utf-8")).get(key, "")
    print("\n".join(as_list(value)) if isinstance(value, list) else value)
    return 0


def cmd_set(file: Path, key: str, value: str) -> int:
    text = file.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    if not text.startswith("---\n") or end == -1:
        print("no front matter", file=sys.stderr)
        return 2
    head, rest = text[:end], text[end:]
    line = f"{key}: {json.dumps(value) if re.search(r'[:#\"]', value) or value == '' else value}"
    pat = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    head = pat.sub(lambda _: line, head, count=1) if pat.search(head) else head + "\n" + line
    file.write_text(head + rest, encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, target = argv[0], Path(argv[1])
    if cmd == "ready":
        return cmd_ready(target, argv[2:])
    if cmd == "summary":
        return cmd_summary(target)
    if cmd == "waiting":
        return cmd_waiting(target)
    if cmd == "same" and len(argv) == 3:
        return cmd_same(target, Path(argv[2]))
    if cmd == "scope" and len(argv) == 5:
        return cmd_scope(target, argv[2], Path(argv[3]), argv[4])
    if cmd == "field" and len(argv) == 3:
        return cmd_field(target, argv[2])
    if cmd == "set" and len(argv) == 4:
        return cmd_set(target, argv[2], argv[3])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
