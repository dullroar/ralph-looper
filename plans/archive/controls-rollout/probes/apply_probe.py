#!/usr/bin/env python3
"""Apply one bypass probe to a working tree. Used by make_probe.sh and self_test.sh.

Run me when: you change a probe, or make_probe.sh reports that a probe does not apply.

Usage: apply_probe.py ROOT PROBE
Environment:
  PROBE_JOB         id of the workflow job that the workflow probes change (default: controls)
  PROBE_ALT_COMMIT  commit for the swap-pin probe (default: the pinned commit with one digit changed)

The script changes files only. It never runs Git. It prints one line for each changed file:
"<action> <relative path>". Exit 0 if the probe applied, 1 if the target is missing.
Secrets are built at run time from random bytes. No secret is stored in this file.
"""
from __future__ import annotations

import os
import re
import secrets
import sys
from pathlib import Path

PROBES = [
    "secret-key", "env-file", "allow-blanket",
    "remove-controls-job", "rename-check", "continue-on-error", "if-false", "path-filter",
    "remove-check-id", "swap-pin", "delete-fixture", "blanket-ignore",
]


class ProbeError(Exception):
    pass


def workflows(root: Path) -> list[Path]:
    return sorted((root / ".github" / "workflows").glob("*.y*ml"))


def job_span(lines: list[str], job: str) -> tuple[int, int]:
    """Return (start, end) line indexes of the job block. end is exclusive."""
    head = re.compile(rf"^  {re.escape(job)}:\s*(#.*)?$")
    for i, line in enumerate(lines):
        if head.match(line):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if re.match(r"^\S", lines[j]) or re.match(r"^  \S", lines[j]):
                    end = j
                    break
            return i, end
    raise ProbeError("job not found")


def find_job(root: Path, job: str) -> tuple[Path, list[str], int, int]:
    for wf in workflows(root):
        lines = wf.read_text(encoding="utf-8").splitlines(keepends=True)
        try:
            start, end = job_span(lines, job)
        except ProbeError:
            continue
        return wf, lines, start, end
    raise ProbeError(f"no workflow in .github/workflows has a job with id '{job}' (set PROBE_JOB)")


def save(root: Path, path: Path, text: str, action: str = "modify") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"{action} {path.relative_to(root).as_posix()}")


def probe_secret_key(root: Path) -> None:
    token = "sk-ant-" + secrets.token_hex(24)
    save(root, root / "probe" / "synthetic_key.txt", f"api_key = {token}\n", "add")


def probe_env_file(root: Path) -> None:
    save(root, root / ".env", f"SERVICE_PASSWORD={secrets.token_urlsafe(24)}\n", "add")


def probe_allow_blanket(root: Path) -> None:
    path = root / ".secret-guard-allow"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old and not old.endswith("\n"):
        old += "\n"
    save(root, path, old + "*  **  probe: blanket exception\n", "modify" if old else "add")


def edit_job(root: Path, edit) -> None:
    job = os.environ.get("PROBE_JOB", "controls")
    wf, lines, start, end = find_job(root, job)
    new = edit(lines, start, end, job)
    save(root, wf, "".join(new))


def probe_remove_job(root: Path) -> None:
    edit_job(root, lambda ls, s, e, j: ls[:s] + ls[e:])


def probe_rename(root: Path) -> None:
    def edit(ls, s, e, job):
        ls = list(ls)
        ls[s] = ls[s].replace(f"{job}:", f"{job}-renamed:", 1)
        for k in range(s + 1, e):
            if re.match(r"^    name:\s*", ls[k]):
                ls[k] = re.sub(r"(name:\s*)(.+)", r"\1\2-renamed", ls[k].rstrip("\n")) + "\n"
        return ls
    edit_job(root, edit)


def probe_insert(line: str):
    def run(root: Path) -> None:
        edit_job(root, lambda ls, s, e, j: ls[:s + 1] + [line + "\n"] + ls[s + 1:])
    return run


def probe_path_filter(root: Path) -> None:
    pattern = "    paths:\n      - 'docs/**'\n"
    for wf in workflows(root):
        text = wf.read_text(encoding="utf-8")
        new, n = re.subn(r"^(  pull_request:[ \t]*\n)", r"\1" + pattern, text, count=1, flags=re.M)
        if n == 0:
            new, n = re.subn(r"^on:[ \t]*\[[^\]]*\][ \t]*\n",
                             "on:\n  pull_request:\n" + pattern + "  push:\n", text, count=1, flags=re.M)
        if n:
            save(root, wf, new)
            return
    raise ProbeError("no workflow has an 'on: pull_request' block")


ID = r"[a-z][a-z0-9]*\.[a-z][a-z0-9-]*"


def probe_remove_check_id(root: Path) -> None:
    path = root / "controls.toml"
    if not path.exists():
        raise ProbeError("controls.toml not found")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        for m in re.finditer(rf"\"({ID})\"", line):
            if m.group(1).startswith("security."):
                continue
            if line.lstrip().startswith("["):
                j = i + 1
                while j < len(lines) and not lines[j].lstrip().startswith("["):
                    j += 1
                del lines[i:j]
            else:
                rest = re.sub(rf"\s*\"{re.escape(m.group(1))}\"\s*,?", " ", line, count=1)
                if rest.strip() == "":
                    del lines[i]
                else:
                    lines[i] = rest
            save(root, path, "".join(lines))
            return
    raise ProbeError("controls.toml has no check ID that this probe can remove")


def probe_swap_pin(root: Path) -> None:
    path = root / "scripts" / "controls-requirements.txt"
    if not path.exists():
        raise ProbeError("scripts/controls-requirements.txt not found")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"@([0-9a-f]{40})\b", text)
    if not m:
        raise ProbeError("no 40-digit commit pin in scripts/controls-requirements.txt")
    alt = os.environ.get("PROBE_ALT_COMMIT") or (("0" if m.group(1)[0] != "0" else "1") + m.group(1)[1:])
    if not re.fullmatch(r"[0-9a-f]{40}", alt) or alt == m.group(1):
        raise ProbeError("PROBE_ALT_COMMIT must be a different 40-digit commit")
    save(root, path, text.replace(m.group(1), alt, 1))


def probe_delete_fixture(root: Path) -> None:
    base = root / "tests" / "fixtures"
    files = sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
    if not files:
        raise ProbeError("tests/fixtures has no file")
    target = next((p for p in files if "bad" in p.as_posix().lower()), files[0])
    target.unlink()
    print(f"delete {target.relative_to(root).as_posix()}")


def probe_blanket_ignore(root: Path) -> None:
    path = root / "controls.toml"
    if not path.exists():
        raise ProbeError("controls.toml not found")
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    save(root, path, text + '\n[ignore]\npaths = ["**"]\n')


HANDLERS = {
    "secret-key": probe_secret_key,
    "env-file": probe_env_file,
    "allow-blanket": probe_allow_blanket,
    "remove-controls-job": probe_remove_job,
    "rename-check": probe_rename,
    "continue-on-error": probe_insert("    continue-on-error: true"),
    "if-false": probe_insert("    if: false"),
    "path-filter": probe_path_filter,
    "remove-check-id": probe_remove_check_id,
    "swap-pin": probe_swap_pin,
    "delete-fixture": probe_delete_fixture,
    "blanket-ignore": probe_blanket_ignore,
}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[2] not in HANDLERS:
        print(__doc__)
        print("Probes: " + " ".join(PROBES), file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve()
    try:
        HANDLERS[argv[2]](root)
    except ProbeError as err:
        print(f"probe {argv[2]}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
