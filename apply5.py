#!/usr/bin/env python3
"""v5: revert the broadcast-action rename (it broke R8 hashCode() switches) and
store the big assets uncompressed so AssetManager.openFd() works.

Why the revert: R8 compiles `when (action)` into a switch on String.hashCode()
with the hash baked in as an integer constant. Renaming the string literal made
every branch miss, so PodroidService.onStartCommand() returned without calling
startForeground() -> Android threw ForegroundServiceDidNotStartInTimeException
and killed the process. Action names are internal, so they stay as upstream.
"""
import glob
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
    print(f"ok   {got:>2}x  {rel}  {old[:60]}")


# 1. Action strings back to the values the compiled hash constants expect.
total = 0
for path in sorted(glob.glob(ROOT + "smali/**/*.smali", recursive=True)):
    text = open(path, encoding="utf-8").read()
    n = text.count("org.kalidroid.app.action.")
    if n:
        open(path, "w", encoding="utf-8").write(
            text.replace("org.kalidroid.app.action.", "com.excp.podroid.action.")
        )
        print(f"ok   {n:>2}x  {path[len(ROOT):]}")
        total += n
print(f"     -> {total} action literals reverted")
if total != 12:
    fail = True

patch("AndroidManifest.xml", "org.kalidroid.app.action.", "com.excp.podroid.action.", 3)
patch("res/values/strings.xml", "org.kalidroid.app.action.", "com.excp.podroid.action.", 1)

# 2. Store the kernel/initrd/rootfs uncompressed. AssetManager.openFd() only
#    works on STORED assets; it is how the app learns the expected size and
#    skips re-extraction. Compressed (apktool default) made it re-copy the
#    450 MB rootfs on every single app launch.
patch("apktool.yml",
      "doNotCompress:\n- resources.arsc\n- assets/dexopt/baseline.prof\n"
      "- assets/dexopt/baseline.profm\n- png\n",
      "doNotCompress:\n- resources.arsc\n- assets/dexopt/baseline.prof\n"
      "- assets/dexopt/baseline.profm\n- png\n- squashfs\n- img\n"
      "- assets/vmlinuz-virt\n")

# 3. Version bump -> 1.2.9-kalidroid.5 (38)
patch("apktool.yml", "versionCode: '37'", "versionCode: '38'")
patch("apktool.yml", "versionName: 1.2.9-kalidroid.4", "versionName: 1.2.9-kalidroid.5")
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.4"', '"KaliDroid 1.2.9-kalidroid.5"')
patch("smali/et.smali", '"v1.2.9-kalidroid.4 ', '"v1.2.9-kalidroid.5 ')
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.4 (37)",
      "Version:      1.2.9-kalidroid.5 (38)")
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.4"', '"KaliDroid/1.2.9-kalidroid.5"')

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv5 edits applied")
