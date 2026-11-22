#!/usr/bin/env python3
"""Read and pick plan steps. Standard library only.

Commands:
  pick_step.py ready PLAN_DIR [--max N] [--active ID,ID]
      Print one JSON line for each ready step to start now (at most N). A step is ready when
      its status is `pending` and every `depends_on` step is `done`. Steps in --active (already
      running or being resumed) count as busy: a new step must not touch the same files.
  pick_step.py summary PLAN_DIR
      Print counts. Exit 0 = all done, 10 = work remains, 11 = blocked and nothing can run.
  pick_step.py field FILE KEY       Print one front-matter value (a list prints one item a line).
  pick_step.py set FILE KEY VALUE   Set one scalar front-matter key.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path


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


def cmd_ready(plan_dir: Path, args: list[str]) -> int:
    limit, active = 1, []
    if "--max" in args:
        limit = int(args[args.index("--max") + 1])
    if "--active" in args:
        active = [a for a in args[args.index("--active") + 1].split(",") if a]
    steps = load(plan_dir)
    chosen: list[str] = []
    busy = [steps[a] for a in active if a in steps]
    for sid, meta in steps.items():
        if len(chosen) + len(active) >= limit and limit > 0:
            break
        if sid in active or meta.get("status") != "pending" or sid.startswith("00-"):
            continue
        if not all(done(steps, d) for d in as_list(meta.get("depends_on"))):
            continue
        if any(clash(meta, b) for b in busy):
            continue
        chosen.append(sid)
        busy.append(meta)
        print(json.dumps({"id": sid, "file": meta["_file"], "tier": meta.get("tier", ""),
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
        m.get("status") in ("pending", "in_progress") and all(done(steps, d) for d in as_list(m.get("depends_on")))
        for m in steps.values())
    return 10 if runnable else 11


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
    if cmd == "field" and len(argv) == 3:
        return cmd_field(target, argv[2])
    if cmd == "set" and len(argv) == 4:
        return cmd_set(target, argv[2], argv[3])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
