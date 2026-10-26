#!/usr/bin/env python3
"""Apply the KaliDroid rebrand to the decoded APK tree."""
import sys

ROOT = "/tmp/opencode/podroid/work/"

# (file, old, new, expected_count or None)
EDITS = [
    # ---- install identity -------------------------------------------------
    ("AndroidManifest.xml", 'package="com.excp.podroid.kali"',
     'package="org.kalidroid.app"', 1),
    ("AndroidManifest.xml",
     "com.excp.podroid.kali.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION",
     "org.kalidroid.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION", 2),
    ("AndroidManifest.xml", "com.excp.podroid.kali.fileprovider",
     "org.kalidroid.app.fileprovider", 1),
    ("AndroidManifest.xml", "com.excp.podroid.kali.control",
     "org.kalidroid.app.control", 1),
    ("AndroidManifest.xml", "com.excp.podroid.kali.androidx-startup",
     "org.kalidroid.app.androidx-startup", 1),
    ("AndroidManifest.xml", "com.excp.podroid.action.START_VM",
     "org.kalidroid.app.action.START_VM", 2),
    ("AndroidManifest.xml", "com.excp.podroid.action.STOP_VM",
     "org.kalidroid.app.action.STOP_VM", 1),

    # ---- user-visible text ------------------------------------------------
    ("res/values/strings.xml", '<string name="app_name">Podroid</string>',
     '<string name="app_name">KaliDroid</string>', 1),
    # every remaining package reference in UI text / adb instructions
    ("res/values/strings.xml", "com.excp.podroid", "org.kalidroid.app", None),
    ("res/values/strings.xml", "Podroid terminal", "KaliDroid terminal", 1),
    ("res/values/strings.xml", "Podroid Diagnostic Log",
     "KaliDroid Diagnostic Log", 1),
    ("res/values/strings.xml", "Podroid needs these", "KaliDroid needs these", 1),
    ("res/values/strings.xml", "Podroid's own forwards",
     "KaliDroid's own forwards", 1),

    # ---- update check -> placeholder fork repo ---------------------------
    ("smali/fu.smali",
     "https://api.github.com/repos/ExTV/Podroid/releases/latest",
     "https://api.github.com/repos/CHANGE_ME/kalidroid/releases/latest", 1),

    # ---- help / bug-report link ------------------------------------------
    ("smali/os1.smali", "https://extv.github.io/Podroid/guide/",
     "https://github.com/CHANGE_ME/kalidroid", 2),

    # ---- about + version display -----------------------------------------
    ("smali/v82.smali", '"Podroid 1.2.9"',
     '"KaliDroid 1.2.9-kalidroid.1 (unofficial Kali fork)"', 1),
    ("smali/et.smali", 'const-string v9, "v1.2.9 ',
     'const-string v9, "v1.2.9-kalidroid.1 ', 1),
    ("smali/nx1.smali", "Version:      1.2.9 (33)",
     "Version:      1.2.9-kalidroid.1 (34)", 1),
    ("smali/nx1.smali", "App ID:       com.excp.podroid.kali",
     "App ID:       org.kalidroid.app", 1),

    # ---- notification channel + user agent -------------------------------
    ("smali/com/excp/podroid/service/PodroidService.smali",
     '"Podroid Service"', '"KaliDroid Service"', 1),
    ("smali/com/excp/podroid/service/PodroidService.smali",
     'const-string v3, "Podroid"', 'const-string v3, "KaliDroid"', 1),
    ("smali/bt.smali", '"Podroid/1.2.9"',
     '"KaliDroid/1.2.9-kalidroid.1"', 1),

    # ---- android version --------------------------------------------------
    ("apktool.yml", "versionCode: '33'", "versionCode: '34'", 1),
    ("apktool.yml", "versionName: 1.2.9", "versionName: 1.2.9-kalidroid.1", 1),
]

fail = False
for rel, old, new, want in EDITS:
    path = ROOT + rel
    with open(path, encoding="utf-8") as f:
        text = f.read()
    got = text.count(old)
    ok = got > 0 if want is None else got == want
    print(("ok  " if ok else "FAIL") + f" {got:>2}x  {rel}  {old[:58]}")
    if not ok:
        fail = True
        continue
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(old, new))

if fail:
    sys.exit("aborted: unexpected match count, nothing written for those entries")
print("\nall edits applied")
