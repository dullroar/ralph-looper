#!/usr/bin/env python3
"""Check a TSV record file against simple rules.

Run me when: a gate must check recorded results (decisions, pins, receipts, baselines) in a TSV file.

Usage:
  check_records.py FILE [--min-rows N] [--columns a,b,c] [--match COL=REGEX]... [--require COL=VALUE]...

FILE is UTF-8 TSV with a header row. Lines that start with '#' are comments.
Blank lines are ignored.
--columns   each named column exists and no cell in it is empty.
--match     every cell in COL matches REGEX (re.fullmatch).
--require   every cell in COL equals VALUE.
Exit 0 if all checks pass, 1 if a record fails, 2 for a bad invocation
or a missing or unreadable file.
"""
from __future__ import annotations

import argparse
import re
import sys


class UsageError(Exception):
    """A bad invocation or an unreadable file. Exit code 2."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def _pair(text: str, flag: str) -> tuple[str, str]:
    col, sep, value = text.partition("=")
    if not sep or not col:
        raise UsageError(f"{flag} needs COL=VALUE, got {text!r}")
    return col, value


def _read(path: str) -> tuple[list[str], list[tuple[int, list[str]]]]:
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"cannot read {path}: {exc}") from exc
    header: list[str] | None = None
    rows: list[tuple[int, list[str]]] = []
    for number, line in enumerate(lines, start=1):
        if line.startswith("#") or not line.strip():
            continue
        cells = line.split("\t")
        if header is None:
            header = [c.strip() for c in cells]
        else:
            rows.append((number, cells))
    if header is None:
        raise UsageError(f"{path}: no header row")
    return header, rows


def check(argv: list[str]) -> tuple[int, list[str]]:
    parser = _Parser(prog="check_records.py", add_help=True)
    parser.add_argument("file")
    parser.add_argument("--min-rows", type=int, default=0)
    parser.add_argument("--columns", default="")
    parser.add_argument("--match", action="append", default=[])
    parser.add_argument("--require", action="append", default=[])
    args = parser.parse_args(argv)
    if args.min_rows < 0:
        raise UsageError("--min-rows must not be negative")

    matches = []
    for text in args.match:
        col, pattern = _pair(text, "--match")
        try:
            matches.append((col, re.compile(pattern)))
        except re.error as exc:
            raise UsageError(f"--match {col}: bad regex {pattern!r}: {exc}") from exc
    requires = [_pair(text, "--require") for text in args.require]
    columns = [c.strip() for c in args.columns.split(",") if c.strip()]

    header, rows = _read(args.file)
    index = {name: i for i, name in enumerate(header)}
    failures: list[str] = []

    if len(rows) < args.min_rows:
        failures.append(f"{args.file}: {len(rows)} rows, need at least {args.min_rows}")

    named = set(columns) | {c for c, _ in matches} | {c for c, _ in requires}
    for name in sorted(named - set(index)):
        failures.append(f"{args.file}: missing column {name!r}")

    for number, cells in rows:
        if len(cells) != len(header):
            failures.append(f"{args.file}:{number}: {len(cells)} cells, header has {len(header)}")

        def cell(name: str) -> str:
            i = index[name]
            return cells[i] if i < len(cells) else ""

        for name in columns:
            if name in index and not cell(name).strip():
                failures.append(f"{args.file}:{number}: column {name!r} is empty")
        for name, regex in matches:
            if name in index and not regex.fullmatch(cell(name)):
                failures.append(
                    f"{args.file}:{number}: column {name!r} value {cell(name)!r} "
                    f"does not match {regex.pattern!r}"
                )
        for name, value in requires:
            if name in index and cell(name) != value:
                failures.append(
                    f"{args.file}:{number}: column {name!r} value {cell(name)!r} is not {value!r}"
                )
    return (1 if failures else 0), failures


def main(argv: list[str]) -> int:
    try:
        code, failures = check(argv)
    except UsageError as exc:
        print(f"check_records: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:  # --help
        return 0 if exc.code in (0, None) else 2
    except Exception as exc:  # never exit 0 on an exception
        print(f"check_records: internal error: {exc}", file=sys.stderr)
        return 2
    for line in failures:
        print(line)
    if code == 0:
        print("ok check_records")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
