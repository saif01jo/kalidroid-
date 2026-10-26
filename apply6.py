#!/usr/bin/env python3
"""v6: release cleanup + new launcher icon.

1. Removes the diagnostic crash recorder installed by apply4.py. It writes
   breadcrumbs into files/console.log, which is also the VM console log, so it
   should not be in a release build. (CrashLog.smali stays in the repo and
   apply4.py can be re-applied when debugging a device with encrypted logcat.)
2. Sets the icon background colour to the tile colour used by gen_icon.py.
3. Bumps the version to 1.2.9-kalidroid.6 (39).

The icon mipmaps themselves are written by gen_icon.py (run it after this
script); it needs res/ to already exist.
"""
import os
import sys

ROOT = "/tmp/opencode/podroid/work/"
fail = False


def patch(rel, old, new, want=1):
    global fail
    path = ROOT + rel
    text = open(path, encoding="utf-8").read()
    got = text.count(old)
    if got != want:
        print(f"FAIL {got:>2}x (want {want})  {rel}  {old[:60]!r}")
        fail = True
        return
    open(path, "w", encoding="utf-8").write(text.replace(old, new))
    print(f"ok   {got:>2}x  {rel}  {old.splitlines()[0][:60]}")


# 1. drop the diagnostic hooks (exact reverse of apply4.py)
patch("smali/com/excp/podroid/PodroidApplication.smali",
      "    invoke-static {p0}, Lorg/kalidroid/diag/CrashLog;->install(Landroid/content/Context;)V\n\n",
      "")
patch("smali/com/excp/podroid/PodroidApplication.smali",
      "    invoke-static {p1}, Lorg/kalidroid/diag/CrashLog;->note(Ljava/lang/String;)V\n\n",
      "")
patch("smali/com/excp/podroid/service/PodroidService.smali",
      "    invoke-static {p1}, Lorg/kalidroid/diag/CrashLog;->noteStart(Landroid/content/Intent;)V\n\n",
      "")

diag = ROOT + "smali/org/kalidroid/diag/CrashLog.smali"
if os.path.exists(diag):
    os.remove(diag)
    print("ok    1x  smali/org/kalidroid/diag/CrashLog.smali removed")
else:
    print("skip     smali/org/kalidroid/diag/CrashLog.smali already absent")

# 2. icon tile colour (matches TILE_RGB in gen_icon.py)
patch("res/values/colors.xml", "<color name=\"ic_launcher_background\">#ff0a0a0a</color>",
      "<color name=\"ic_launcher_background\">#ff0c0d11</color>")

# 3. version bump -> 1.2.9-kalidroid.6 (39)
patch("apktool.yml", "versionCode: '38'", "versionCode: '39'")
patch("apktool.yml", "versionName: 1.2.9-kalidroid.5", "versionName: 1.2.9-kalidroid.6")
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.5"', '"KaliDroid 1.2.9-kalidroid.6"')
patch("smali/et.smali", '"v1.2.9-kalidroid.5 ', '"v1.2.9-kalidroid.6 ')
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.5 (38)",
      "Version:      1.2.9-kalidroid.6 (39)")
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.5"', '"KaliDroid/1.2.9-kalidroid.6"')

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv6 release cleanup applied")
