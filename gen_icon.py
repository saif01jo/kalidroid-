#!/usr/bin/env python3
"""KaliDroid launcher icon generator.

The Kali dragon emblem (blue orb, white dragon) on a dark navy tile: vertical
gradient, blue bloom behind the orb, dragon glow, specular highlight, drop
shadow, vignette and a thin rim light along the tile edge.

Writes every mipmap density used by the app:

    ic_launcher.png             legacy square (adaptive fallback < API 26)
    ic_launcher_round.png       legacy round
    ic_launcher_foreground.png  adaptive foreground (full-bleed tile)
    ic_launcher_monochrome.png  themed-icon layer (white dragon only)

and, with --master, a 4096x4096 PNG for the repository/social preview.

usage: gen_icon.py <res_dir> [--preview DIR] [--master PATH] [--size N]

Requires Pillow (pip install pillow). Artwork: icon/kali-emblem.png (Kali dragon, vendored from the
Kali GNU/Linux kali-defaults package; not covered by the GPL).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
DEFAULT_EMBLEM = HERE / "icon" / "kali-emblem.png"

TILE_TOP = (13, 18, 32)        # tile gradient, top (navy)
TILE_BOTTOM = (4, 6, 11)        # tile gradient, bottom
BLOOM_RGB = (52, 130, 255)      # blue bloom behind the orb
GLYPH_RGB = (247, 251, 255)    # dragon white
RIM_RGB = (120, 170, 255)      # tile edge light (blue)

LEGACY_FRAC = 0.95             # emblem width / tile width (legacy square)
ROUND_FRAC = 0.88              # a circle clips the wings, so keep it smaller
FG_FRAC = 0.63                 # adaptive layer: 0.95 of the 72dp visible circle
MONO_FRAC = 0.62
CORNER = 0.225                 # rounded-square radius / size
SS = 2                         # supersampling factor

# Position of the blue disc inside the emblem artwork (fractions of its width
# and height). The disc -- not the bounding box -- is what has to look centred,
# because the dragon's wings sweep out to the left edge of the artwork.
DISC_CX, DISC_CY, DISC_R = 0.6443, 0.4071, 0.3020

# the adaptive layer is 108dp but only its central 72dp circle is visible
FG_ZOOM = 72.0 / 108.0

LEGACY_SIZES = {"ldpi": 36, "mdpi": 48, "hdpi": 72, "xhdpi": 96,
                "xxhdpi": 144, "xxxhdpi": 192}
FG_SIZES = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324,
            "xxxhdpi": 432}


def load_emblem(path: Path) -> Image.Image:
    """Open the original Kali dragon emblem (1881x1415 RGBA)."""
    im = Image.open(path).convert("RGBA")
    bbox = im.split()[-1].getbbox()
    if bbox:
        im = im.crop(bbox)
    return im


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgradient(size: int, top, bottom) -> Image.Image:
    col = Image.new("RGB", (1, 256))
    px = col.load()
    for y in range(256):
        px[0, y] = lerp(top, bottom, y / 255.0)
    return col.resize((size, size), Image.BILINEAR)


def radial(size: int, inner, outer, alpha_gain: float = 1.0) -> Image.Image:
    s = 256
    g = Image.radial_gradient("L").resize((s, s), Image.BILINEAR)
    img = Image.composite(Image.new("RGB", (s, s), inner),
                          Image.new("RGB", (s, s), outer), g)
    img = img.convert("RGBA")
    img.putalpha(ImageChops.invert(g).point(lambda v: int(v * alpha_gain)))
    return img.resize((size, size), Image.BICUBIC)


def rounded_mask(size: int, radius_frac: float = CORNER, ss: int = 4) -> Image.Image:
    m = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size * ss - 1, size * ss - 1),
                                        radius=int(size * radius_frac) * ss, fill=255)
    return m.resize((size, size), Image.LANCZOS)


def emblem_box(emblem: Image.Image, n: int, frac: float):
    """Top-left corner and size of the emblem inside an n-px tile, placed so
    that the blue (now emerald) disc sits at the centre of the tile."""
    w = max(1, int(n * frac))
    h = max(1, round(w * emblem.size[1] / emblem.size[0]))
    x = int(n * 0.5 - DISC_CX * w)
    y = int(n * 0.5 - DISC_CY * h)
    return x, y, w, h


def edge_feather(n: int, shape: str, inset: float = 0.004,
                 blur: float = 0.075, radius: float = 0.5) -> Image.Image:
    """Alpha mask that fades the artwork out as it reaches the tile edge, so
    the dragon's wings and tail dissolve instead of being sliced by the mask.
    `n` is the drawing resolution, `radius` a fraction of n (0.5 for the icon,
    1/3 for the adaptive layer)."""
    pad = int(n * inset)
    m = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(m)
    if shape == "circle":
        c = n / 2
        r = n * radius - pad
        d.ellipse((c - r, c - r, c + r, c + r), fill=255)
    else:
        d.rounded_rectangle((pad, pad, n - 1 - pad, n - 1 - pad),
                            radius=max(1, int(n * CORNER) - pad), fill=255)
    return m.filter(ImageFilter.GaussianBlur(n * blur / 2))


def dragon_mask(em: Image.Image) -> Image.Image:
    r, g, b, _ = em.split()
    return ImageChops.darker(ImageChops.darker(r, g), b).point(
        lambda v: max(0, min(255, int((v - 90) * 255 / 120))))


def draw_tile(emblem: Image.Image, size: int, frac: float, shape: str = "square",
              feather_radius: float = 0.5, zoom: float = 1.0,
              rim: bool = True) -> Image.Image:
    n = size * SS
    tile = vgradient(n, TILE_TOP, TILE_BOTTOM).convert("RGBA")

    # emerald bloom behind the orb
    b = radial(int(n * 0.62 * zoom), BLOOM_RGB, (8, 14, 26), 0.55)
    tile.alpha_composite(b, ((n - b.size[0]) // 2, (n - b.size[1]) // 2))

    # vignette so the corners fall away
    v = Image.radial_gradient("L").resize((n, n), Image.BILINEAR)
    vig = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    vig.putalpha(v.point(lambda x: int(x * 0.52)))
    tile = Image.alpha_composite(tile, vig)

    x, y, w, h = emblem_box(emblem, n, frac)
    em = emblem.resize((w, h), Image.LANCZOS)
    keep = ImageChops.multiply(em.split()[-1], edge_feather(n, shape, radius=feather_radius))
    em.putalpha(keep)

    # drop shadow under the whole emblem
    sh = keep.filter(ImageFilter.GaussianBlur(n * 0.018)).point(lambda v: int(v * 0.55))
    tile.paste(Image.new("RGBA", em.size, (0, 0, 0, 255)),
               (x + int(n * 0.006), y + int(n * 0.012)), sh)

    # emerald glow around the dragon itself
    dm = dragon_mask(em)
    glow = Image.new("L", (n, n), 0)
    glow.paste(dm, (x, y))
    glow = glow.filter(ImageFilter.GaussianBlur(n * 0.012)).point(lambda v: int(v * 0.85))
    g = Image.new("RGBA", (n, n), BLOOM_RGB + (0,))
    g.putalpha(glow)
    tile = Image.alpha_composite(tile, g)

    tile.alpha_composite(em, (x, y))

    # specular highlight on the orb, clipped to the emblem's opaque pixels
    cx = x + em.size[0] * DISC_CX
    cy = y + em.size[1] * DISC_CY
    r = em.size[0] * DISC_R
    hl = radial(int(2.0 * r), (255, 255, 255), (200, 255, 220), 0.34)
    lay = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    lay.alpha_composite(hl, (int(cx - 0.26 * r - hl.size[0] / 2),
                             int(cy - 0.32 * r - hl.size[1] / 2)))
    opaque = Image.new("L", (n, n), 0)
    opaque.paste(keep, (x, y))
    lay.putalpha(ImageChops.multiply(lay.split()[-1], opaque))
    tile = Image.alpha_composite(tile, lay)

    if rim:
        rimimg = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        inset = max(1, int(n * 0.006))
        ImageDraw.Draw(rimimg).rounded_rectangle(
            (inset, inset, n - 1 - inset, n - 1 - inset),
            radius=max(1, int(n * CORNER) - inset),
            outline=RIM_RGB + (70,), width=max(1, int(n * 0.004)))
        tile = Image.alpha_composite(tile, rimimg)

    return tile.resize((size, size), Image.LANCZOS)


def compose(emblem: Image.Image, size: int, shape: str, frac: float) -> Image.Image:
    tile = draw_tile(emblem, size, frac, shape)
    if shape == "circle":
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
    else:
        mask = rounded_mask(size)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(tile, (0, 0), mask)
    return out


def foreground(emblem: Image.Image, size: int, frac: float) -> Image.Image:
    """Full-bleed tile; the artwork is faded out inside the 72dp visible
    circle so the launcher mask never slices the wings."""
    return draw_tile(emblem, size, frac, "circle", feather_radius=1.0 / 3.0,
                     zoom=FG_ZOOM, rim=False)


def monochrome(emblem: Image.Image, size: int, frac: float) -> Image.Image:
    r, g, b, _ = emblem.split()
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    mask = mn.point(lambda v: max(0, min(255, int((v - 90) * 255 / 120))))
    w = max(1, int(size * frac))
    h = max(1, round(w * emblem.size[1] / emblem.size[0]))
    m = mask.resize((w, h), Image.LANCZOS).filter(ImageFilter.MaxFilter(3))
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(m, ((size - w) // 2, (size - h) // 2))
    out = Image.new("RGBA", (size, size), GLYPH_RGB + (0,))
    out.putalpha(canvas)
    return out


def previews(emblem: Image.Image, pdir: Path) -> None:
    pdir.mkdir(parents=True, exist_ok=True)
    for s in (432, 192, 96, 48):
        compose(emblem, s, "square", LEGACY_FRAC).save(pdir / f"icon-{s}.png")
    compose(emblem, 192, "circle", ROUND_FRAC).save(pdir / "icon-round-192.png")
    foreground(emblem, 432, FG_FRAC).save(pdir / "layer-432.png")

    sheet = Image.new("RGB", (760, 250), (240, 240, 244))
    x = 24
    for s in (192, 96, 48):
        im = Image.open(pdir / f"icon-{s}.png").convert("RGBA")
        sheet.paste(im, (x, 30), im)
        x += s + 34
    sheet.save(pdir / "sheet.png")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = {}
    for i, a in enumerate(sys.argv):
        if a.startswith("--") and i + 1 < len(sys.argv):
            opts[a] = sys.argv[i + 1]

    res = Path(args[0]) if args else Path("res")
    emblem = load_emblem(Path(opts.get("--emblem", DEFAULT_EMBLEM)))

    for name, px in LEGACY_SIZES.items():
        d = res / f"mipmap-{name}"
        d.mkdir(parents=True, exist_ok=True)
        compose(emblem, px, "square", LEGACY_FRAC).save(d / "ic_launcher.png")
        compose(emblem, px, "circle", ROUND_FRAC).save(d / "ic_launcher_round.png")

    for name, px in FG_SIZES.items():
        d = res / f"mipmap-{name}"
        d.mkdir(parents=True, exist_ok=True)
        foreground(emblem, px, FG_FRAC).save(d / "ic_launcher_foreground.png")
        monochrome(emblem, px, MONO_FRAC).save(d / "ic_launcher_monochrome.png")

    if "--master" in opts:
        dest = Path(opts["--master"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        px = int(opts.get("--size", 4096))
        master = draw_tile(emblem, px, LEGACY_FRAC, "square", rim=True)
        master = master.filter(ImageFilter.GaussianBlur(px / 4096 * 0.8))
        master.save(dest)
        print("master:", dest, master.size)

    if "--preview" in opts:
        previews(emblem, Path(opts["--preview"]))
        print("preview:", opts["--preview"])

    print("icons written to", res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
