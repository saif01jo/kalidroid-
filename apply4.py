#!/usr/bin/env python3
"""v4: diagnostic instrumentation. Records app/service start breadcrumbs and any
uncaught exception into files/console.log, which the app's "Export diagnostic
log" already includes. Logcat is encrypted on some OEM devices, so this is the only
way to see the real reason a Start attempt dies."""
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


# 1. Install the crash recorder as early as possible in the process.
patch("smali/com/excp/podroid/PodroidApplication.smali",
      ".method public final onCreate()V\n    .locals 4\n\n    .line 1\n",
      ".method public final onCreate()V\n    .locals 4\n\n"
      "    invoke-static {p0}, Lorg/kalidroid/diag/CrashLog;->install(Landroid/content/Context;)V\n\n"
      "    .line 1\n")

# 2. Breadcrumb: every asset extraction attempt (runs only on a fresh data dir).
patch("smali/com/excp/podroid/PodroidApplication.smali",
      ".method public final d(Ljava/lang/String;Ljava/io/File;Z)V\n    .locals 5\n\n    .line 1\n",
      ".method public final d(Ljava/lang/String;Ljava/io/File;Z)V\n    .locals 5\n\n"
      "    invoke-static {p1}, Lorg/kalidroid/diag/CrashLog;->note(Ljava/lang/String;)V\n\n"
      "    .line 1\n")

# 3. Breadcrumb: the service actually received a command (tells us whether the
#    crash is on the activity side or inside the service).
patch("smali/com/excp/podroid/service/PodroidService.smali",
      ".method public final onStartCommand(Landroid/content/Intent;II)I\n    .locals 6\n\n    .line 1\n",
      ".method public final onStartCommand(Landroid/content/Intent;II)I\n    .locals 6\n\n"
      "    invoke-static {p1}, Lorg/kalidroid/diag/CrashLog;->noteStart(Landroid/content/Intent;)V\n\n"
      "    .line 1\n")

# 4. Version bump -> 1.2.9-kalidroid.4 (37)
patch("apktool.yml", "versionCode: '36'", "versionCode: '37'")
patch("apktool.yml", "versionName: 1.2.9-kalidroid.3", "versionName: 1.2.9-kalidroid.4")
patch("smali/v82.smali", '"KaliDroid 1.2.9-kalidroid.3"', '"KaliDroid 1.2.9-kalidroid.4"')
patch("smali/et.smali", '"v1.2.9-kalidroid.3 ', '"v1.2.9-kalidroid.4 ')
patch("smali/nx1.smali", "Version:      1.2.9-kalidroid.3 (36)",
      "Version:      1.2.9-kalidroid.4 (37)")
patch("smali/bt.smali", '"KaliDroid/1.2.9-kalidroid.3"', '"KaliDroid/1.2.9-kalidroid.4"')

if fail:
    sys.exit("aborted: see FAIL lines")
print("\nv4 instrumentation applied")
