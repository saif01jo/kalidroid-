#!/usr/bin/env python3
"""Patch android:foregroundServiceType in a compiled (binary AXML) manifest.

apktool 2.7 decodes the API-34 flag 0x40000000 ("specialUse") as "" and rebuilds
it as 0, and its API-33 framework cannot express the name either. Everything else
in the manifest round-trips fine, so we set the single int back to 0x40000000.

usage: patch_fgs.py <in.apk> <out.apk>
"""
import struct
import sys
import zipfile

ATTR = "foregroundServiceType"
WANT = 0x40000000
TARGET = "AndroidManifest.xml"


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def read_strings(b, off):
    """Return list of strings from a ResStringPool chunk at `off`."""
    assert u16(b, off) == 0x0001, "not a string pool"
    header_size = u16(b, off + 2)
    count = u32(b, off + 8)
    flags = u32(b, off + 16)
    strings_start = u32(b, off + 20)
    utf8 = bool(flags & 0x100)
    base = off + strings_start
    out = []
    for i in range(count):
        p = base + u32(b, off + header_size + 4 * i)
        if utf8:
            n = b[p]
            p += 2 if n & 0x80 else 1  # skip char-length (+ second byte)
            n = b[p]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | b[p + 1]
                p += 2
            else:
                p += 1
            out.append(b[p:p + n].decode("utf-8", "replace"))
        else:
            n = u16(b, p)
            p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | u16(b, p)
                p += 2
            out.append(b[p:p + 2 * n].decode("utf-16-le", "replace"))
    return out


def patch(data):
    assert u16(data, 0) == 0x0003, "not a binary XML document"
    total = u32(data, 4)
    strings = None
    pos = 8
    hits = []
    while pos < total:
        ctype = u16(data, pos)
        csize = u32(data, pos + 4)
        if csize == 0:
            break
        if ctype == 0x0001:
            strings = read_strings(data, pos)
        elif ctype == 0x0102:  # start element
            ext = pos + 16
            name = strings[u32(data, ext + 4)] if strings else "?"
            attr_start = u16(data, ext + 8)
            attr_size = u16(data, ext + 10)
            attr_count = u16(data, ext + 12)
            for i in range(attr_count):
                a = ext + attr_start + i * attr_size
                aname = strings[u32(data, a + 4)] if strings else "?"
                if aname == ATTR and name == "service":
                    hits.append(a)
        pos += csize
    if len(hits) != 1:
        raise SystemExit(f"expected exactly 1 service/{ATTR}, found {len(hits)}")
    a = hits[0]
    if u16(data, a + 12) != 8:
        raise SystemExit("unexpected typed-value size")
    dtype, value = data[a + 15], u32(data, a + 16)
    print(f"  found {ATTR}: dataType=0x{dtype:02x} value=0x{value:08x}")
    if value not in (0, WANT):
        raise SystemExit(f"unexpected current value 0x{value:08x}")
    struct.pack_into("<I", data, a + 16, WANT)
    print(f"  patched {ATTR}: value=0x{WANT:08x}")
    return bytes(data)


def main(src, dst):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            raw = zin.read(info.filename)
            if info.filename == TARGET:
                print(f"patching {info.filename} ({len(raw)} bytes)")
                raw = patch(bytearray(raw))
            zout.writestr(info, raw)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
