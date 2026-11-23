#!/usr/bin/env python3
"""Run every context check in one command. Usage: check_context.py [ROOT]

Run me when: I changed any context file, and before every pull request.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKS = [
    ["build_indexes.py", "--check"],
    ["check_plan.py"],
    ["check_links.py"],
    ["scan_secrets.py"],
    ["secret_guard.py", "--tracked"],
]


def main(argv: list[str]) -> int:
    failed = []
    for script, *flags in CHECKS:
        # secret_guard.py takes the root as an option, not as a positional argument.
        extra = ["--root", *argv] if script == "secret_guard.py" and argv else argv
        code = subprocess.run([sys.executable, str(HERE / script), *flags, *extra]).returncode
        print(f"{'ok  ' if code == 0 else 'FAIL'} {script}")
        if code:
            failed.append(script)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
