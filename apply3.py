#!/usr/bin/env python3
"""v3: restore the foregroundServiceType that apktool dropped (fatal on Android 14+).
Runs on the already-patched tree (apply.py + apply2.py applied)."""
import sys

ROOT = "/tmp/opencode/podroid/work/"
fail = False


def patch(rel, old, new, want=1):
    global fail
    path = ROOT + rel
    text = open(path, encoding="utf-8").read()
    got = text.count(old)
    if got != want:
        print(f"FAIL {got:>2}x (want {want})  {rel}  {old[:60]}")
        fail = True
        return
    open(path, "w", encoding="utf-8").write(text.replace(old, new))
    print(f"ok   {got:>2}x  {rel}  {old[:60]}")


# 1. THE BUG: apktool 2.7 (API-33 framework) cannot decode 0x40000000
#    ("specialUse", added in API 34) and silently rebuilt it as 0. Android 14+
#    then throws MissingForegroundServiceTypeException in startForeground(),
#    killing the process the moment "Start VM" starts PodroidService.
patch("AndroidManifest.xml",
      'android:foregroundServiceType=""',
      'android:foregroundServiceType="specialUse"')

# 2. Version bump so the diagnostic proves which APK is installed.
patch("apktool.yml", "versionCode: '35'", "versionCode: '36'")
patch("apktool.yml", "versionName: 1.2.9-kalidroid.2", "versionName: 1.2.9-kalidroid.3")
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.2"', '"KaliDroid 1.2.9-kalidroid.3"')
patch("smali/et.smali", '"v1.2.9-kalidroid.2 ', '"v1.2.9-kalidroid.3 ')
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.2 (35)",
      "Version:      1.2.9-kalidroid.3 (36)")
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.2"', '"KaliDroid/1.2.9-kalidroid.3"')

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv3 edits applied")
