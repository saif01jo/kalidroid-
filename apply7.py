#!/usr/bin/env python3
"""v7: guest-facing rebrand.

1. The SSH hint in the UI still advertised the old default password.
2. Icon tile colour matches the new artwork (gen_icon.py TOP_RGB #0d1220).
3. Version bump to 1.2.9-kalidroid.7 (40).

The guest-side changes (banner, hostname, root password) live in the squashfs
asset, not in the APK code; see NOTICE.txt for how that image was rebuilt.
"""
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


# 1. default password in the SSH hint (root password is now "kalidroid")
patch("res/values/strings.xml",
      "ssh root@&lt;phone-ip> -p 9922 (password: podroid)",
      "ssh root@&lt;phone-ip> -p 9922 (password: kalidroid)")

# 2. adaptive-icon background colour, matches the generated tile
patch("res/values/colors.xml",
      "<color name=\"ic_launcher_background\">#ff0c0d11</color>",
      "<color name=\"ic_launcher_background\">#ff0d1220</color>")

# 3. version bump -> 1.2.9-kalidroid.7 (40)
patch("apktool.yml", "versionCode: '39'", "versionCode: '40'")
patch("apktool.yml", "versionName: 1.2.9-kalidroid.6", "versionName: 1.2.9-kalidroid.7")
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.6"', '"KaliDroid 1.2.9-kalidroid.7"')
patch("smali/et.smali", '"v1.2.9-kalidroid.6 ', '"v1.2.9-kalidroid.7 ')
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.6 (39)",
      "Version:      1.2.9-kalidroid.7 (40)")
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.6"', '"KaliDroid/1.2.9-kalidroid.7"')

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv7 edits applied")
