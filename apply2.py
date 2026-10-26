#!/usr/bin/env python3
"""v2: fix action-intent mismatch (my regression), point links at the real repo."""
import glob
import sys

ROOT = "/tmp/opencode/podroid/work/"
fail = False


def patch(rel, old, new, want=None):
    global fail
    path = ROOT + rel
    text = open(path, encoding="utf-8").read()
    got = text.count(old)
    ok = got > 0 if want is None else got == want
    print(("ok  " if ok else "FAIL") + f" {got:>2}x  {rel}  {old[:55]}")
    if not ok:
        fail = True
        return
    open(path, "w", encoding="utf-8").write(text.replace(old, new))


# 1. Action strings must agree with the manifest in BOTH directions.
#    MainActivity compares incoming intents, VmControlReceiver dispatches on them,
#    tt/PodroidService send them.
total = 0
for path in sorted(glob.glob(ROOT + "smali/**/*.smali", recursive=True)):
    text = open(path, encoding="utf-8").read()
    n = text.count("com.excp.podroid.action.")
    if n:
        open(path, "w", encoding="utf-8").write(
            text.replace("com.excp.podroid.action.", "org.kalidroid.app.action.")
        )
        print(f"ok   {n:>2}x  {path[len(ROOT):]}")
        total += n
print(f"     -> {total} action literals aligned")
if total != 12:
    fail = True

# 2. Real repo everywhere.
patch("smali/fu.smali",
      "https://api.github.com/repos/CHANGE_ME/kalidroid/releases/latest",
      "https://api.github.com/repos/saif01jo/kalidroid-/releases/latest", 1)
patch("smali/os1.smali", "https://github.com/CHANGE_ME/kalidroid",
      "https://github.com/saif01jo/kalidroid-", 2)

# 3. Version surfaces -> 1.2.9-kalidroid.2 / 35. Plain chars only.
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.1 (unofficial Kali fork)"',
      '"KaliDroid 1.2.9-kalidroid.2"', 1)
patch("smali/et.smali", 'const-string v9, "v1.2.9-kalidroid.1 ',
      'const-string v9, "v1.2.9-kalidroid.2 ', 1)
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.1 (34)",
      "Version:      1.2.9-kalidroid.2 (35)", 1)
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.1"',
      '"KaliDroid/1.2.9-kalidroid.2"', 1)
patch("apktool.yml", "versionCode: '34'", "versionCode: '35'", 1)
patch("apktool.yml", "versionName: 1.2.9-kalidroid.1",
      "versionName: 1.2.9-kalidroid.2", 1)

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv2 edits applied")
