#!/usr/bin/env python3
"""Render the "noctalia-night" cheat-sheet wallpaper.

Keep KEYS / EXTRAS / SYSTEM in sync with system_files/etc/xdg/umbriel/config.toml.

Needs: python3 with Pillow + numpy, rsvg-convert, fonts Inter + DejaVu Sans Mono.
Usage (from repo root):
    python3 artwork/make-cheatsheet.py system_files/usr/share/backgrounds/fedora-noctalia
"""
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 3840, 2160
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# ---------------------------------------------------------------- content ---
# Right half of the keyboard, labelled with the Dvorak symbol each key types.
# (label, action, width in key units, accent group)
ROWS = [
    (0.0, [("6", "WS 1", 1, "ws"), ("7", "WS 2", 1, "ws"), ("8", "WS 3", 1, "ws"),
           ("9", "WS 4", 1, "ws"), ("0", "WS 5", 1, "ws"), ("[", "tabs", 1, "win"),
           ("]", "next tab", 1, "win"), ("⌫", "close", 1.6, "app")]),
    (0.5, [("F", "col ←", 1, "move"), ("G", "win ↓", 1, "move"), ("C", "win ↑", 1, "move"),
           ("R", "col →", 1, "move"), ("L", "fullscreen", 1, "win"), ("/", "width", 1, "size"),
           ("=", "wider", 1, "size"), ("\\", "this sheet", 1.1, "app")]),
    (0.75, [("D", "focus ←", 1, "focus"), ("H", "focus ↓", 1, "focus"), ("T", "focus ↑", 1, "focus"),
            ("N", "focus →", 1, "focus"), ("S", "overview", 1, "app"), ("-", "narrower", 1, "size"),
            ("⏎", "terminal", 1.85, "app")]),
    (1.25, [("B", "send →", 1, "ws"), ("M", "maximize", 1, "win"), ("W", "stack ←", 1, "win"),
            ("V", "stack →", 1, "win"), ("Z", "float", 1, "win")]),
]
EDIT = [  # editing block 2x3
    [("Ins", "clipboard", "app"), ("Home", "control", "app"), ("PgUp", "WS prev", "ws")],
    [("Del", "power", "app"), ("End", "settings", "app"), ("PgDn", "WS next", "ws")],
]
EXTRAS = [
    ("Mod", "tap: launcher"),
    ("Mod  Space", "launcher"),
    ("Mod  B  then 6…0", "send window to WS 1…5"),
    ("Mod  B  then PgUp/PgDn", "send to prev/next WS"),
    ("Print", "region screenshot"),
    ("Mod  Pause", "keys go to app / back"),
]
SYSTEM = [
    ("sudo bootc upgrade", "fetch update (applies on reboot)"),
    ("bootc status", "current / staged image"),
    ("sudo bootc rollback", "boot previous image"),
    ("flatpak install flathub <app>", "add GUI apps"),
    ("umbriel config validate", "check compositor config"),
    ("noctalia config validate", "check shell config"),
]

ACCENT = {
    "focus": "#8fb4ff", "move": "#c39bff", "ws": "#7fe0c4",
    "win": "#ffb4d8", "size": "#ffd38a", "app": "#e9e4ff",
}
FONT = "Inter"
MONO = "DejaVu Sans Mono"

# ---------------------------------------------------------------- layout ----
U = 168          # key unit (px at 4K)
GAP = 14
KH = 150         # key height
PX, PY = 1400, 470          # panel origin
PW, PH = 2330, 1520


def key(x, y, w, label, action, group):
    col = ACCENT[group]
    big = 64 if len(label) <= 2 else 40
    return f'''
  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{KH}" rx="22" fill="#1b1838" fill-opacity="0.78"
          stroke="{col}" stroke-opacity="0.45" stroke-width="2.5"/>
    <rect x="{x + 18}" y="{y + KH - 14}" width="{w - 36}" height="4" rx="2" fill="{col}" fill-opacity="0.75"/>
    <text x="{x + 22}" y="{y + 70}" font-family="{FONT}" font-weight="700" font-size="{big}" fill="#f3f0ff">{escape(label)}</text>
    <text x="{x + 22}" y="{y + 118}" font-family="{FONT}" font-weight="500" font-size="27" fill="{col}">{escape(action)}</text>
  </g>'''


def build_svg():
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
    # panel
    parts.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="48" fill="#0d0b20" '
                 f'fill-opacity="0.62" stroke="#a796f0" stroke-opacity="0.22" stroke-width="2"/>')
    parts.append(f'<text x="{PX + 70}" y="{PY + 110}" font-family="{FONT}" font-weight="700" '
                 f'font-size="58" fill="#f3f0ff">Mod = hold Right Alt</text>')
    parts.append(f'<text x="{PX + 760}" y="{PY + 110}" font-family="{FONT}" font-weight="400" '
                 f'font-size="36" fill="#b8addf">+ one key · keys show their Dvorak letter</text>')

    # keyboard
    kx0, ky0 = PX + 70, PY + 170
    for r, (offset, keys) in enumerate(ROWS):
        x = kx0 + offset * U
        y = ky0 + r * (KH + GAP)
        for label, action, w, grp in keys:
            kw = w * U - GAP
            parts.append(key(x, y, kw, label, action, grp))
            x += w * U
    # space bar
    sy = ky0 + 4 * (KH + GAP)
    parts.append(key(kx0 + 0.25 * U, sy, 4.6 * U - GAP, "Space", "launcher", "app"))

    # editing block
    ex0 = kx0 + 9.15 * U
    for r, row in enumerate(EDIT):
        for c, (label, action, grp) in enumerate(row):
            parts.append(key(ex0 + c * U, ky0 + r * (KH + GAP), U - GAP, label, action, grp))

    # legend
    lx, ly = ex0, ky0 + 2 * (KH + GAP) + 60
    for i, (grp, name) in enumerate([("focus", "focus"), ("move", "move"), ("ws", "workspaces"),
                                     ("win", "window"), ("size", "size"), ("app", "apps & shell")]):
        yy = ly + i * 52
        parts.append(f'<rect x="{lx}" y="{yy - 24}" width="34" height="8" rx="4" fill="{ACCENT[grp]}"/>')
        parts.append(f'<text x="{lx + 54}" y="{yy - 10}" font-family="{FONT}" font-size="30" '
                     f'fill="#cfc6f2">{escape(name)}</text>')

    # bottom columns
    by = sy + KH + 110

    def column(x, title, rows, keyw, mono_key):
        out = [f'<text x="{x}" y="{by}" font-family="{FONT}" font-weight="700" font-size="40" '
               f'fill="#f3f0ff">{escape(title)}</text>']
        for i, (k, v) in enumerate(rows):
            yy = by + 70 + i * 56
            out.append(f'<text x="{x}" y="{yy}" font-family="{MONO if mono_key else FONT}" '
                       f'font-weight="{400 if mono_key else 600}" font-size="{30 if mono_key else 32}" '
                       f'fill="#e9e4ff">{escape(k)}</text>')
            out.append(f'<text x="{x + keyw}" y="{yy}" font-family="{FONT}" font-size="30" '
                       f'fill="#a99fd3">{escape(v)}</text>')
        return out

    parts += column(kx0, "More keys", EXTRAS, 470, False)
    parts += column(kx0 + 1130, "System", SYSTEM, 590, True)
    parts.append('</svg>')
    return "\n".join(parts)


def background(tmp: Path):
    """Night sky with moon and a smaller moth on the left."""
    shapes = Path(__file__).with_name("noctalia-night-shapes.svg").read_text()
    # shrink and move the moth out of the panel's way
    shapes = shapes.replace('translate(1250,1230) rotate(-14) scale(1.15)',
                            'translate(690,1330) rotate(-14) scale(0.72)')
    shapes = shapes.replace('M1650,980 C2050,760 2400,690 2700,660', 'M960,1120 C1100,980 1250,880 1380,820')
    # moon above the panel's top-right corner
    shapes = shapes.replace('cx="2930" cy="610"', 'cx="3480" cy="245"')
    shapes = shapes.replace('cx="3000" cy="565"', 'cx="3550" cy="200"')
    svg = tmp / "shapes.svg"
    svg.write_text(shapes)
    png = tmp / "shapes.png"
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), svg, "-o", png], check=True)
    rng = np.random.default_rng(45)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip((x / W * 0.45 + y / H * 0.75) / 1.2, 0, 1)[..., None]
    img = np.array([10, 12, 30], np.float32) * (1 - t) + np.array([34, 16, 52], np.float32) * t

    def radial(cx, cy, r, col, a):
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
        return (np.exp(-d ** 2) * a)[..., None] * np.array(col, np.float32)

    img += radial(3480, 245, 1100, [70, 45, 130], 0.55)
    img += radial(700, 1900, 1300, [20, 30, 80], 0.45)
    n = 1400
    for px, py, v in zip(rng.integers(0, W, n), rng.integers(0, H, n), rng.power(6, n) * 200):
        img[py, px] += v
    s = np.asarray(Image.open(png).convert("RGBA"), np.float32)
    a = s[..., 3:] / 255
    return img * (1 - a) + s[..., :3] * a, rng


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        img, rng = background(tmp)
        (tmp / "sheet.svg").write_text(build_svg(), encoding="utf-8")
        subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), tmp / "sheet.svg",
                        "-o", tmp / "sheet.png"], check=True)
        s = np.asarray(Image.open(tmp / "sheet.png").convert("RGBA"), np.float32)
        a = s[..., 3:] / 255
        img = img * (1 - a) + s[..., :3] * a
        img += rng.normal(0, 1.4, img.shape).astype(np.float32)
        out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        for w, h in ((3840, 2160), (2560, 1440), (1920, 1080)):
            out.resize((w, h), Image.LANCZOS).save(
                OUT / f"noctalia-night-cheatsheet-{w}x{h}.jpg", quality=94, subsampling=0, optimize=True)


if __name__ == "__main__":
    main()
