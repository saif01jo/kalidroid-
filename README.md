# KaliDroid

Unofficial Kali Linux build of [Podroid](https://github.com/ExTV/Podroid).
**This is a modified fork, not the official app.** Not affiliated with or
supported by the Podroid author.

| | |
|---|---|
| Package | `org.kalidroid.app` |
| Version | 1.2.9-kalidroid.7 (40) |
| Guest | Kali Linux (squashfs rootfs, ARM64) |
| Guest login | `root` / `kalidroid` |
| Min Android | 8.0 (API 26) |
| Arch | arm64-v8a only |

## Status

Experimental. The APK is a rebrand of a binary release (it is not built from
upstream sources), so it is behind upstream and may have bugs the official app
does not.

Confirmed booting on an Android 16 (API 36) arm64 device with QEMU backend. Builds.
## Install

1. Download the APK from [Releases](../../releases).
2. Uninstall any KaliDroid build signed with a different key first — Android
   refuses to update across signing keys. (The official Podroid has a different
   application id, so it can stay installed.)
3. Open the app and grant the permissions it asks for.
4. First start extracts the ~450 MB rootfs to app storage. Make sure you have
   at least 2 GB free and keep the app in the foreground for that first boot.

If you use the **AVF (pKVM)** backend, Android requires a one-time grant per
install (the app shows the exact command, or use Shizuku):

```
adb shell pm grant org.kalidroid.app android.permission.MANAGE_VIRTUAL_MACHINE
adb shell pm grant org.kalidroid.app android.permission.USE_CUSTOM_VIRTUAL_MACHINE
```

Without the grant the app falls back to the QEMU backend automatically.

## Guest login

The terminal greets you with:

```
Welcome to KaliDroid (Kali GNU/Linux Rolling)
Kernel ... on aarch64 (hvc0)

  Default login:  root  /  kalidroid
  Change root password:    passwd
  Create a regular user:   adduser <name>
                           (then: usermod -aG sudo <name>)

kalidroid login:
```

Log in as `root` with password `kalidroid` (SSH on port 9922 uses the same
password). Change it with `passwd` — it is the same well-known default as
upstream Podroid's `root` / `podroid`, so change it before exposing the VM to
your network.

## Differences from Podroid

- Kali Linux guest instead of Alpine.
- Guest hostname `kalidroid`, KaliDroid login banner, default root password
  `kalidroid` (upstream: `podroid`).
- New application id (`org.kalidroid.app`) so it can coexist with the official
  app and does not overwrite it.
- The in-app update check points at **this** repository's releases, so it can
  never offer you an official Alpine build.
- Help/bug-report links point here.
- Launcher name, notification channel and About text say KaliDroid.
- Kali-inspired launcher icon: the Kali dragon emblem on a dark navy tile
  (regenerate with `gen_icon.py`; source artwork in `icon/`).

Everything else — the VM engine, QEMU/AVF backends, terminal, port forwarding,
USB passthrough — is upstream Podroid code. Guest-side helper names
(`podroid-getty`, `podroid-backup`, the `podroid-*.service` units,
`/var/backups/podroid`, `Download/Podroid/backups`) are intentionally left
unchanged, because the app talks to them by name.

## Known issues

All three start-up crashes of the early builds are fixed in
`1.2.9-kalidroid.5`:

1. **`foregroundServiceType` dropped by apktool.** The service declares
   `specialUse` (`0x40000000`); apktool 2.7 rebuilt it as `0` and Android 14+
   threw `MissingForegroundServiceTypeException`. `patch_fgs.py` restores the
   value in the compiled manifest after every build.
2. **Renamed broadcast actions broke R8 switches.** R8 compiles the
   `when (action)` blocks into `switch (action.hashCode())` with the hash baked
   in (`com.excp.podroid.action.START` = `0x48aa4b9c`). Renaming the literals
   made every branch miss, so `startForeground()` was never called and Android
   killed the process with
   `ForegroundServiceDidNotStartInTimeException`. The action strings are
   internal identifiers and are **not** rebranded.
3. **Compressed assets.** `AssetManager.openFd()` only works on stored assets;
   apktool compressed the squashfs, so the app could not read the expected size
   and re-extracted the 450 MB rootfs on every launch. The big assets are now
   stored (`doNotCompress` in `apktool.yml`).

Other notes:

- First boot is slow (extracts the ~450 MB rootfs once) and needs ~2 GB free.
  Keep the app in the foreground until the console appears.
- The signing key is not the upstream key. Uninstall any KaliDroid build signed
  with a different key before installing.

## How this build was made

The APK is a patched rebuild of the upstream release, not compiled from source:

- [`changes.diff`](changes.diff) — every modification against a fresh decode of
  the base APK
- [`apply.py`](apply.py), [`apply2.py`](apply2.py), [`apply3.py`](apply3.py),
  [`apply4.py`](apply4.py), [`apply5.py`](apply5.py), [`apply6.py`](apply6.py),
  [`apply7.py`](apply7.py) — the scripts that apply them, in that order (later
  scripts deliberately undo earlier ones)
- [`gen_icon.py`](gen_icon.py) + [`icon/`](icon/) — generates the Kali dragon
  launcher icon at every density (needs Pillow)
- [`CrashLog.smali`](CrashLog.smali) — diagnostic crash/breadcrumb recorder that
  writes to `files/console.log` (installed by `apply4.py`, removed again by
  `apply6.py` for release; optional, useful on devices whose logcat is
  encrypted)
- [`patch_fgs.py`](patch_fgs.py) — post-build step that restores
  `foregroundServiceType=specialUse` in the compiled manifest (apktool 2.7 with
  an API-33 framework drops it, which crashes the app on Android 14+)
- [`mkdiff.py`](mkdiff.py) — regenerates `changes.diff`
- [`NOTICE.txt`](NOTICE.txt) — full change log, the guest-image rebuild steps
  (including the `unsquashfs` setuid pitfall), signing details, rebuild recipe

## License

Podroid is licensed under the **GNU GPL v2**. This fork is distributed under the
same license. The corresponding source is the upstream Podroid source plus the
modifications in `changes.diff`, which are applied to a decoded copy of the
upstream APK (see `NOTICE.txt` for the exact steps).

If you redistribute an APK built from this repository you must also make the
source available and keep the GPLv2 text and the original copyright notices.

The Kali dragon logo is a trademark of **Offensive Security** and is not part of
the GPL grant. This is an unofficial fork; the mark is used only to show that the
guest system is Kali Linux, and the project is not endorsed by Offensive
Security.

## Reporting bugs

Please use this repository's [Issues](../../issues), not the upstream tracker —
the upstream author cannot support builds with a Kali guest.
