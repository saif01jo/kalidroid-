#!/usr/bin/env python3
"""Regenerate changes.diff: text changes between the pristine decode of the
uploaded base APK (base_dec/) and the final apktool tree (work/).

Binary artefacts (icons, assets) are listed in NOTICE.txt instead; including
them here would only produce "Binary files differ" noise.

usage: mkdiff.py <base_dec> <work> > changes.diff
"""
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {"assets", "original", "unknown", "build", "kotlin"}
SKIP_PREFIX = ("res/mipmap", "res/drawable")
TEXT_EXT = {".xml", ".yml", ".smali", ".txt", ".json", ".html", ".css", ".js"}


def wanted(rel: Path) -> bool:
    rel_s = rel.as_posix()
    if any(part in SKIP_DIRS for part in rel.parts):
        return False
    if rel_s.startswith(SKIP_PREFIX):
        return False
    return rel.suffix in TEXT_EXT


def main() -> int:
    base, work = Path(sys.argv[1]), Path(sys.argv[2])
    files = set()
    for root in (base, work):
        for p in root.rglob("*"):
            if p.is_file() and wanted(p.relative_to(root)):
                files.add(p.relative_to(root))
    out = []
    for rel in sorted(files, key=lambda p: p.as_posix()):
        a, b = base / rel, work / rel
        if not b.exists():
            out.append(f"--- a/{rel}\n+++ /dev/null\n")
            continue
        if not a.exists():
            out.append(f"--- /dev/null\n+++ b/{rel}\n")
            continue
        d = subprocess.run(
            ["diff", "-u", "--label", f"a/{rel}", "--label", f"b/{rel}", str(a), str(b)],
            capture_output=True, text=True, errors="replace")
        if d.returncode == 1:
            out.append(d.stdout)
    sys.stdout.write("".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
