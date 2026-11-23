#!/usr/bin/env python3
"""Tests for scripts/check_records.py. Run: python3 tests/test_check_records.py"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_records.py"

GOOD = "# a comment\nrepo\tcommit\tstate\nalpha\t" + "a" * 40 + "\tpass\n# another\nbeta\t" + "b" * 40 + "\tpass\n"


class CheckRecordsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text: str) -> str:
        path = Path(self.tmp.name) / "r.tsv"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def run_check(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
        )

    def test_pass_all_options(self) -> None:
        r = self.run_check(
            self.write(GOOD), "--min-rows", "2", "--columns", "repo,commit,state",
            "--match", "commit=[0-9a-f]{40}", "--match", "state=pass|fail",
            "--require", "state=pass",
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_comment_lines_not_counted(self) -> None:
        r = self.run_check(self.write(GOOD), "--min-rows", "3")
        self.assertEqual(r.returncode, 1)
        self.assertIn("2 rows", r.stdout)

    def test_min_rows_fail(self) -> None:
        r = self.run_check(self.write(GOOD), "--min-rows", "5")
        self.assertEqual(r.returncode, 1)

    def test_missing_column(self) -> None:
        r = self.run_check(self.write(GOOD), "--columns", "repo,nope")
        self.assertEqual(r.returncode, 1)
        self.assertIn("nope", r.stdout)

    def test_empty_cell(self) -> None:
        r = self.run_check(self.write("repo\tstate\nalpha\t\n"), "--columns", "state")
        self.assertEqual(r.returncode, 1)
        self.assertIn(":2:", r.stdout)

    def test_match_fail_gives_row(self) -> None:
        text = "repo\tcommit\nalpha\tabc\n"
        r = self.run_check(self.write(text), "--match", "commit=[0-9a-f]{40}")
        self.assertEqual(r.returncode, 1)
        self.assertIn(":2:", r.stdout)

    def test_match_is_fullmatch(self) -> None:
        r = self.run_check(self.write("s\npassed\n"), "--match", "s=pass|fail")
        self.assertEqual(r.returncode, 1)

    def test_require_fail(self) -> None:
        r = self.run_check(self.write("s\npass\nfail\n"), "--require", "s=pass")
        self.assertEqual(r.returncode, 1)
        self.assertIn(":3:", r.stdout)

    def test_short_row(self) -> None:
        r = self.run_check(self.write("a\tb\nx\n"))
        self.assertEqual(r.returncode, 1)

    def test_missing_file(self) -> None:
        r = self.run_check(str(Path(self.tmp.name) / "absent.tsv"))
        self.assertEqual(r.returncode, 2)

    def test_empty_file(self) -> None:
        r = self.run_check(self.write(""))
        self.assertEqual(r.returncode, 2)

    def test_header_only_with_min_rows(self) -> None:
        r = self.run_check(self.write("a\tb\n"), "--min-rows", "1")
        self.assertEqual(r.returncode, 1)

    def test_bad_regex(self) -> None:
        r = self.run_check(self.write(GOOD), "--match", "commit=[unclosed")
        self.assertEqual(r.returncode, 2)

    def test_bad_pair(self) -> None:
        r = self.run_check(self.write(GOOD), "--require", "novalue")
        self.assertEqual(r.returncode, 2)

    def test_bad_option(self) -> None:
        r = self.run_check(self.write(GOOD), "--min-rows", "x")
        self.assertEqual(r.returncode, 2)

    def test_no_file_argument(self) -> None:
        r = self.run_check()
        self.assertEqual(r.returncode, 2)

    def test_not_utf8(self) -> None:
        path = Path(self.tmp.name) / "bin.tsv"
        path.write_bytes(b"a\n\xff\xfe\n")
        r = self.run_check(str(path))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
