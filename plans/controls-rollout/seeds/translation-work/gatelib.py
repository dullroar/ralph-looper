#!/usr/bin/env python3
"""Gate helper of plan v4-es-1. No step may change it: it is in no `touches` list.

Run me when: a gate or a `run` command of plan v4-es-1 calls it.
Usage: python3 plans/v4-es-1/gatelib.py COMMAND [ARGS]
Commands (exit 0 = pass, 1 = fail, 2 = bad use):
  keys FILE KEY...          each KEY is a line `KEY: value` with a real value (no placeholder)
  cap FILE                  line `usd-cap: N` with 0 < N <= 100 (the program cap of the Batch API)
  stop                      loop/STOP exists in the main checkout and is not tracked
  untracked                 the private review files and runtime folders are not tracked
  guard                     stop, untracked, secret guard, indexes, context checks
  tests [FILE...]           with files: those unit tests. Without: the tool suite against the recorded baseline
  verify [FILE...]          tools/verify.py --fast (with --files when files are given)
  release [--no-gates]      tools/verify.py --release; with --no-gates exit 3 counts as a pass
  packets build|rebuild|verify [DIR]   build the jury packets in .probe/, record or compare the manifest digest
  requests | ingest         jury batch input and jury ingest, built in .probe/ from a rebuilt packet set
  approved-si RECORD FILE   each source issue named in RECORD is `approved` in FILE
  english-check             apply the upstream patches to a scratch English clone and run its build check
  upstream-sha RECORD       the accepted commit of RECORD exists in the English repository
  record-source RECORD      pin the accepted commit in translation/source.json and write the impact report
  source-check RECORD       translation/source.json and the impact report agree with RECORD
  triage FILE ID...         each ID is on a line of FILE that holds a verdict word
  controls                  the pinned controls run (exit 0 or 1; 2 or 3 is a failure)
  published RECORD          the release tag exists on the public remote of RECORD
  verify-release RECORD     the published release assets have the hashes of the r01 record
Scratch work stays in .probe/ (the step deletes it). The tool reads no secret.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PLAN = Path("plans/v4-es-1")
PLACEHOLDER = re.compile(r"SET-BY-JIM|TODO|FIXME|<[^>]*>|^\s*$")
PRIVATE = ["review/packets", "review/repo-bundle.zip", "review/canaries.key.json", "review/units.index.jsonl",
           "translation/work"]
RELEASE_TAG = "v4-es.1"


def out(msg):
    print(msg)


def fail(msg):
    print("gatelib: " + msg, file=sys.stderr)
    return 1


def git(*args, cwd=None, check=False):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def main_checkout():
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(common).parent


def env():
    e = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    venv = main_checkout() / ".venv" / "bin"
    if venv.is_dir():
        e["PATH"] = str(venv) + os.pathsep + e.get("PATH", "")
    return e


def run(cmd, **kw):
    return subprocess.run(cmd, env=env(), text=True, **kw)


def read_keys(path):
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z0-9-]+): ?(.*)$", line)
        if m:
            values.setdefault(m.group(1), []).append(m.group(2).strip())
    return values


def cmd_keys(args):
    if len(args) < 2 or not Path(args[0]).is_file():
        return fail("keys: file missing or no key given: %s" % (args[:1],))
    values, bad = read_keys(args[0]), []
    for key in args[1:]:
        vals = values.get(key)
        if not vals or any(PLACEHOLDER.search(v) for v in vals):
            bad.append(key)
    return fail("%s: missing or placeholder key(s): %s" % (args[0], ", ".join(bad))) if bad else 0


def cmd_cap(args):
    vals = read_keys(args[0]).get("usd-cap", []) if args and Path(args[0]).is_file() else []
    if len(vals) != 1 or not re.fullmatch(r"[0-9]+(\.[0-9]+)?", vals[0]):
        return fail("usd-cap is not set to a number in %s (Jim must set it)" % (args[:1],))
    if not 0 < float(vals[0]) <= 100:
        return fail("usd-cap must be above 0 and at most 100")
    return 0


def cmd_stop(_):
    stop = main_checkout() / "loop" / "STOP"
    if not stop.is_file():
        return fail("loop/STOP is missing in the main checkout. The old loop must stay stopped.")
    if git("ls-files", "--", "loop/STOP").stdout.strip():
        return fail("loop/STOP is tracked")
    return 0


def cmd_untracked(_):
    tracked = git("ls-files", "--", *PRIVATE, "loop/driver.out*").stdout.split()
    return fail("private files are tracked: %s" % tracked[:5]) if tracked else 0


def cmd_guard(_):
    for step in (cmd_stop, cmd_untracked):
        if step([]):
            return 1
    for cmd in (["python3", "scripts/secret_guard.py", "--tracked"], ["python3", "scripts/build_indexes.py", "--check"],
                ["python3", "scripts/check_context.py"]):
        if run(cmd).returncode:
            return fail("failed: " + " ".join(cmd))
    return 0


def cmd_tests(args):
    if args:
        return run(["python3", "-m", "unittest", *args]).returncode
    proc = run(["python3", "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"],
               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chk = run(["python3", "plans/adopt-ralph/no_new_failures.py", "plans/adopt-ralph/tools-test-baseline.txt"],
              input=proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("\n".join(chk.stdout.splitlines()[-12:]))
    return chk.returncode


def cmd_verify(args):
    cmd = ["python3", "-I", "tools/verify.py", "--fast"] + (["--files", *args] if args else [])
    return run(cmd).returncode


def cmd_release(args):
    gates = "--no-gates" not in args
    code = run(["python3", "-I", "tools/verify.py", "--release"] + ([] if gates else ["--no-gates"])).returncode
    if not (code == 0 or (code == 3 and not gates)):
        return fail("verify --release exit %d" % code)
    if gates:  # the r01 record: the hashes of the release assets, for step r03
        assets = sorted(p for p in Path("translation/work/verify/release-a").rglob("*") if p.suffix in (".pdf", ".epub"))
        if not assets:
            return fail("the release build made no PDF or EPUB")
        rec = record_path("r01-release-gates.md")
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text("# Release gates record (written by gatelib.py release)\n\nresult: pass\n" + "".join(
            "asset: %s %s\n" % (p.name, sha256(p)) for p in assets), encoding="utf-8")
    return 0


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_packets(dest):
    """Build the packets into `dest` (inside .probe/) and return (manifest digest, packet count, leak lines)."""
    shutil.rmtree(dest, ignore_errors=True)
    proc = run(["python3", "-I", "tools/jury_packet.py", "--build", "--bundle", "--code", "--out", str(dest)],
               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    leaks = [ln for ln in proc.stdout.splitlines() if ln.startswith("LEAK:")]
    manifest = Path(dest) / "packets" / "manifest.json"
    if proc.returncode or not manifest.is_file():
        raise SystemExit("gatelib: jury_packet.py failed:\n" + proc.stdout[-1500:])
    return sha256(manifest), len(json.loads(manifest.read_text(encoding="utf-8"))["packets"]), leaks


def record_path(name):
    return PLAN / "records" / name


def cmd_packets(args):
    mode = args[0] if args else ""
    rec = record_path("j01-packets.md")
    if mode == "verify":
        d = Path(args[1] if len(args) > 1 else "review")
        have, want = sha256(d / "packets" / "manifest.json"), read_keys(rec).get("manifest-sha256", [""])[0]
        return 0 if have == want else fail("manifest digest %s differs from the j01 record %s" % (have[:12], want[:12]))
    probe = Path(".probe/review")
    try:
        digest, count, leaks = build_packets(probe)
        if mode == "build":
            again, _, _ = build_packets(Path(".probe/review-2"))
            if again != digest:
                return fail("two builds of the packets differ: the build is not deterministic")
            if leaks:
                return fail("private data in the packets: %s" % leaks[:3])
            rec.parent.mkdir(parents=True, exist_ok=True)
            rec.write_text("# Packets record (written by gatelib.py packets build)\n\nmanifest-sha256: %s\npackets: %d\n"
                           "leak-count: 0\nbuilds-equal: yes\n" % (digest, count), encoding="utf-8")
            return 0
        if mode == "rebuild":
            want = read_keys(rec).get("manifest-sha256", [""])[0]
            return 0 if digest == want else fail("rebuilt manifest digest differs from the j01 record")
        return fail("packets: use build, rebuild or verify")
    finally:
        shutil.rmtree(".probe/review-2", ignore_errors=True)
        if mode == "build":
            shutil.rmtree(".probe", ignore_errors=True)


def cmd_requests(_):
    if cmd_packets(["rebuild"]):
        return 1
    inp = Path(".probe/jury-input.jsonl")
    if run(["python3", "-I", "tools/jury_requests.py", "build", "--packets", ".probe/review/packets",
            "--out", str(inp)]).returncode:
        return fail("jury_requests.py build failed")
    rows = [json.loads(x) for x in inp.read_text(encoding="utf-8").splitlines() if x.strip()]
    lenses = {r["segment_id"].rsplit(".", 1)[-1] for r in rows}
    dry = run(["python3", "-I", "tools/batch.py", "build", "--input", str(inp), "--model", "dry-run-model",
               "--out", ".probe/requests.jsonl", "--prompt-file", "translation/prompts/batch-jury.md", "--dry-run"])
    if dry.returncode or len(lenses) != 13:
        return fail("batch.py dry run failed or lens count is %d (need 13)" % len(lenses))
    record_path("j02-batch-requests.md").write_text(
        "# Jury batch input record (written by gatelib.py requests)\n\nrows: %d\nlenses: %d\ninput-sha256: %s\n"
        "dry-run: ok\n" % (len(rows), len(lenses), sha256(inp)), encoding="utf-8")
    shutil.rmtree(".probe", ignore_errors=True)
    return 0


def cmd_ingest(_):
    if cmd_packets(["rebuild"]):
        return 1
    shutil.copytree("review/inbox", ".probe/review/inbox", dirs_exist_ok=True)
    if run(["python3", "-I", "tools/jury_ingest.py", "--review", ".probe/review"]).returncode:
        return fail("jury_ingest.py failed")
    for pattern in ("report-*.md", "findings-*.jsonl"):
        for f in Path(".probe/review").glob(pattern):
            shutil.copy(f, Path("review") / f.name)
    shutil.rmtree(".probe", ignore_errors=True)
    return 0


def cmd_approved_si(args):
    ids = [i.strip() for i in read_keys(args[0]).get("approved-source-issues", [""])[0].split(",")]
    ids = [i for i in ids if i and i != "none"]
    rows = Path(args[1]).read_text(encoding="utf-8").splitlines()
    bad = [i for i in ids if not any(r.startswith("| %s " % i) and r.rstrip().endswith("| approved |") for r in rows)]
    return fail("not marked approved in %s: %s" % (args[1], bad)) if bad else 0


def source_info():
    return json.loads(Path("translation/source.json").read_text(encoding="utf-8"))


def english_copy(tmp, name, commit):
    dest = Path(tmp) / name
    git("clone", "-q", "--no-checkout", source_info()["english_clone_path"], str(dest), check=True)
    git("checkout", "-q", commit, cwd=dest, check=True)
    return dest


def cmd_english_check(_):
    info = source_info()
    patches = [Path("translation/part3/upstream-package.patch")] + sorted(Path("translation/part3/source-issues").glob("*.patch"))
    with tempfile.TemporaryDirectory() as tmp:
        en = english_copy(tmp, "en", info["english_commit"])
        for p in patches:
            if not p.is_file() or git("apply", str(p.resolve()), cwd=en).returncode:
                return fail("patch does not apply to the pinned English commit: %s" % p)
        if run(["python3", "lessons/book/build.py", "--check"], cwd=en).returncode:
            return fail("English build check fails with the patches")
    return 0


def cmd_upstream_sha(args):
    sha = read_keys(args[0]).get("accepted-sha", [""])[0]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return fail("accepted-sha is not a full commit hash")
    with tempfile.TemporaryDirectory() as tmp:
        git("init", "-q", tmp, check=True)
        got = subprocess.run(["git", "fetch", "-q", "--depth", "1", source_info()["english_repo"], sha], cwd=tmp,
                             env=env(), capture_output=True, text=True)
    return 0 if got.returncode == 0 else fail("the accepted commit is not in the English repository")


def cmd_record_source(args):
    sha = read_keys(args[0])["accepted-sha"][0]
    info = source_info()
    old = info["english_commit"]
    with tempfile.TemporaryDirectory() as tmp:
        en_old, en_new = english_copy(tmp, "old", old), english_copy(tmp, "new", sha)
        info["previous_english_commit"] = old
        info["english_commit"] = sha
        Path("translation/source.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return run(["python3", "-I", "tools/impact.py", "--old", str(en_old), "--new", str(en_new),
                    "--release", "v4-es.1", "--write"]).returncode


def cmd_source_check(args):
    sha = read_keys(args[0]).get("accepted-sha", [""])[0]
    report = Path("translation/reports/impact-v4-es.1.json")
    if source_info().get("english_commit") != sha or not report.is_file():
        return fail("source.json does not hold the accepted commit, or the impact report is missing")
    return 0 if "units" in json.loads(report.read_text(encoding="utf-8")) else fail("impact report has no units")


def cmd_triage(args):
    lines = Path(args[0]).read_text(encoding="utf-8").splitlines()
    verdict = re.compile(r"\b(agree|library-defect|translation-defect|no-local-tool)\b")
    bad = [i for i in args[1:] if not any(i in ln and verdict.search(ln) for ln in lines)]
    return fail("no verdict line for: %s" % ", ".join(bad)) if bad else 0


def cmd_controls(_):
    code = run(["python3", "-m", "deterministic_controls", "check", "--root", ".", "--profile", "ci"]).returncode
    return 0 if code in (0, 1) else fail("the controls could not run (exit %d). Put the pinned library on PYTHONPATH." % code)


def remote_of(rec):
    return read_keys(rec)["repo-url"][0].rstrip("/")


def cmd_published(args):
    url, tag = remote_of(args[0]), RELEASE_TAG
    got = subprocess.run(["git", "ls-remote", "--tags", url, "refs/tags/" + tag], env=env(), capture_output=True, text=True)
    return 0 if got.returncode == 0 and tag in got.stdout else fail("no public tag %s at %s" % (tag, url))


def cmd_verify_release(args):
    m = re.match(r"https://github\.com/([^/]+/[^/]+)$", remote_of(args[0]))
    want = dict(v.split()[:2] for v in read_keys(record_path("r01-release-gates.md")).get("asset", []))
    if not m or not want:
        return fail("repo-url is not a GitHub URL or the r01 record has no asset lines")
    api = "https://api.github.com/repos/%s/releases/tags/%s" % (m.group(1), RELEASE_TAG)
    release = json.load(urllib.request.urlopen(api, timeout=60))
    have = {}
    for a in release.get("assets", []):
        have[a["name"]] = hashlib.sha256(urllib.request.urlopen(a["browser_download_url"], timeout=600).read()).hexdigest()
    bad = [n for n, h in want.items() if have.get(n) != h]
    return fail("asset missing or hash differs: %s" % bad) if bad else 0


COMMANDS = {"keys": cmd_keys, "cap": cmd_cap, "stop": cmd_stop, "untracked": cmd_untracked, "guard": cmd_guard,
            "tests": cmd_tests, "verify": cmd_verify, "release": cmd_release, "packets": cmd_packets,
            "requests": cmd_requests, "ingest": cmd_ingest, "approved-si": cmd_approved_si,
            "english-check": cmd_english_check, "upstream-sha": cmd_upstream_sha, "record-source": cmd_record_source,
            "source-check": cmd_source_check, "triage": cmd_triage, "controls": cmd_controls,
            "published": cmd_published, "verify-release": cmd_verify_release}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    return COMMANDS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
