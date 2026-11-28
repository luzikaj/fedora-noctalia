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
# Physical keyboard (Logitech G413 TKL: Fn right of Alt Gr, no PrtSc/ScrLk), each key labelled with what it types on dvorak_r_pl
# (right-handed Dvorak). Keep in sync with system_files/etc/xdg/umbriel/config.toml.
# key = (label, Mod-action or "", width in units, group)
_ = ""
MAIN = [
    [("`", _, 1, _), ("1", _, 1, _), ("2", _, 1, _), ("3", _, 1, _), ("4", _, 1, _),
     ("j", "float↔tile", 1, "win"), ("l", "width", 1, "win"), ("m", "narrower", 1, "win"),
     ("f", "wider", 1, "win"), ("p", "center", 1, "win"), ("/", "tabs", 1, "win"),
     ("[", "notifs", 1, "app"), ("]", "clipboard", 1, "app"), ("⌫", "close", 2, "win")],
    [("Tab", _, 1.5, _), ("5", _, 1, _), ("6", _, 1, _), ("q", _, 1, _), (".", "windows", 1, "app"),
     ("o", "col ←", 1, "move"), ("r", "win ↓", 1, "move"), ("s", "win ↑", 1, "move"),
     ("u", "col →", 1, "move"), ("y", "fullscreen", 1, "win"), ("b", "maximize", 1, "win"),
     (";", "stack ←", 1, "move"), ("=", "unstack →", 1, "move"), ("\\", "fullscreen", 1.5, "win")],
    [("Caps", _, 1.75, _), ("7", _, 1, _), ("8", _, 1, _), ("z", "WS → mon", 1, "ws"),
     ("a", "read aloud", 1, "voice"), ("e", "focus ←", 1, "focus"), ("h", "focus ↓", 1, "focus"),
     ("t", "focus ↑", 1, "focus"), ("d", "focus →", 1, "focus"), ("c", "dictate", 1, "voice"),
     ("k", "floating", 1, "win"), ("-", "overview", 1, "app"), ("⏎", "terminal", 2.25, "app")],
    [("Shift", _, 2.25, _), ("9", _, 1, _), ("0", _, 1, _), ("x", "stop voice", 1, "voice"),
     (",", _, 1, _), ("i", "stop dict.", 1, "voice"), ("n", "WS ↑", 1, "ws"), ("w", "WS ↓", 1, "ws"),
     ("v", "send ↑", 1, "ws"), ("g", "send ↓", 1, "ws"), ("'", "launcher", 1, "app"),
     ("Shift", "tap: sticky", 2.75, "keyd")],
    [("Ctrl", _, 1.25, _), ("Win", _, 1.25, _), ("Alt", _, 1.25, _), ("Space", _, 6.25, _),
     ("Alt Gr", "hold: Mod", 1.25, "keyd"), ("Fn", _, 1.25, _), ("Menu", _, 1.25, _),
     ("Ctrl", "tap: sticky", 1.25, "keyd")],
]
FROW = [("F7", "keys→app", "app"), ("F8", "power", "app"), ("F9", "shot win", "shot"), ("F10", "shot area", "shot"),
        ("F11", "audio", "sound"), ("F12", "shot screen", "shot")]
NAV = [
    [("Ins", "shortcuts", "app"), ("Home", "other mon", "ws"), ("PgUp", "last WS", "ws")],
    [("Del", "lock", "app"), ("End", "send→mon", "ws"), ("PgDn", "settings", "app")],
]
ARROWS = [("↑", "vol +", "sound"), ("←", "mute", "sound"), ("↓", "vol −", "sound"), ("→", "play", "sound")]

LEGEND = [("focus", "focus"), ("move", "move"), ("ws", "workspaces · monitors"), ("win", "window · size"),
          ("app", "shell · apps"), ("sound", "sound"), ("voice", "voice"), ("shot", "screenshots"),
          ("keyd", "keyd modifiers")]
TIPS = [
    ("Mod", "hold Right Alt, then one key (never Shift)"),
    ("Polish", "tap Right Alt, then a c e l n o s z x  →  ą ć ę ł ń ó ś ż ź"),
    ("Sticky", "tap Right Ctrl / Right Shift, then the key (1 s)"),
    ("Rescue", "Backspace + Escape + Enter together stops keyd"),
    ("Games", "Mod+F7 passes all keys to a game / VM, again to undo"),
]
SYSTEM = [
    ("sudo bootc upgrade", "update (applies on reboot)"),
    ("bootc status", "current / staged image"),
    ("sudo bootc rollback", "boot previous image"),
    ("flatpak install flathub <app>", "add GUI apps"),
    ("umbriel config validate", "check compositor config"),
]

ACCENT = {
    "focus": "#8fb4ff", "move": "#c39bff", "ws": "#7fe0c4", "win": "#ffb4d8",
    "app": "#e9e4ff", "sound": "#ffd38a", "voice": "#9fe7ff", "shot": "#ffa98a",
    "keyd": "#b8f28a",
}
FONT = "Inter"
MONO = "DejaVu Sans Mono"

# ---------------------------------------------------------------- layout ----
U = 160          # key unit (px at 4K)
GAP = 12
KH = 140         # key height
PX, PY = 260, 360            # panel origin
PW, PH = 3060, 1440


def key(x, y, w, label, action, group, h=KH):
    if not group:   # unbound key: dim
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#14122b" fill-opacity="0.55" '
                f'stroke="#6d63a0" stroke-opacity="0.25" stroke-width="2"/>'
                f'<text x="{x + 18}" y="{y + 58}" font-family="{FONT}" font-weight="600" '
                f'font-size="{48 if len(label) == 1 else 28}" fill="#7a71a8">{escape(label)}</text>')
    col = ACCENT[group]
    big = 56 if len(label) == 1 else 32
    return f'''
  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#1b1838" fill-opacity="0.85"
          stroke="{col}" stroke-opacity="0.55" stroke-width="2.5"/>
    <rect x="{x + 16}" y="{y + h - 13}" width="{w - 32}" height="4" rx="2" fill="{col}" fill-opacity="0.8"/>
    <text x="{x + 18}" y="{y + 60}" font-family="{FONT}" font-weight="700" font-size="{big}" fill="#f6f3ff">{escape(label)}</text>
    <text x="{x + 18}" y="{y + h - 32}" font-family="{FONT}" font-weight="500" font-size="23" fill="{col}">{escape(action)}</text>
  </g>'''


def build_svg():
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
    p.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="48" fill="#0d0b20" '
             f'fill-opacity="0.66" stroke="#a796f0" stroke-opacity="0.22" stroke-width="2"/>')
    p.append(f'<text x="{PX + 70}" y="{PY + 100}" font-family="{FONT}" font-weight="700" '
             f'font-size="56" fill="#f3f0ff">Hold Right Alt + one key</text>')
    p.append(f'<text x="{PX + 760}" y="{PY + 100}" font-family="{FONT}" font-size="34" '
             f'fill="#b8addf">keys show what they type on right-handed Dvorak (dvorak_r_pl)</text>')

    kx0 = PX + 70
    fy = PY + 150                       # F-row
    frow_x = kx0 + 8 * U                # F7..F12 above the right hand
    for i, (lab, act, grp) in enumerate(FROW):
        p.append(key(frow_x + i * U, fy, U - GAP, lab, act, grp, h=120))
    ky0 = fy + 120 + 40                  # main block
    for r, row in enumerate(MAIN):
        x = kx0
        y = ky0 + r * (KH + GAP)
        for lab, act, w, grp in row:
            p.append(key(x, y, w * U - GAP, lab, act, grp))
            x += w * U
    nx0 = kx0 + 15 * U + 70             # nav cluster
    for r, row in enumerate(NAV):
        for c, (lab, act, grp) in enumerate(row):
            p.append(key(nx0 + c * U, ky0 + r * (KH + GAP), U - GAP, lab, act, grp))
    ay = ky0 + 3 * (KH + GAP)
    up, left, down, right = ARROWS
    p.append(key(nx0 + U, ay, U - GAP, *up))
    for c, k in enumerate((left, down, right)):
        p.append(key(nx0 + c * U, ay + KH + GAP, U - GAP, *k))

    # legend under the nav cluster? -> bottom band, three columns
    by = ky0 + 5 * (KH + GAP) + 80
    lx = kx0
    for i, (grp, name) in enumerate(LEGEND):
        col, row = divmod(i, 5)
        xx, yy = lx + col * 420, by + row * 50
        p.append(f'<rect x="{xx}" y="{yy - 22}" width="34" height="8" rx="4" fill="{ACCENT[grp]}"/>')
        p.append(f'<text x="{xx + 50}" y="{yy - 8}" font-family="{FONT}" font-size="29" fill="#cfc6f2">{escape(name)}</text>')
    tx = kx0 + 900
    for i, (k, v) in enumerate(TIPS):
        yy = by + i * 50
        p.append(f'<text x="{tx}" y="{yy - 8}" font-family="{FONT}" font-weight="700" font-size="29" fill="#f3f0ff">{escape(k)}</text>')
        p.append(f'<text x="{tx + 130}" y="{yy - 8}" font-family="{FONT}" font-size="29" fill="#b7aee0">{escape(v)}</text>')
    sx = kx0 + 2000
    for i, (k, v) in enumerate(SYSTEM):
        yy = by + i * 50
        p.append(f'<text x="{sx}" y="{yy - 8}" font-family="{MONO}" font-size="26" fill="#e9e4ff">{escape(k)}</text>')
        p.append(f'<text x="{sx + 540}" y="{yy - 8}" font-family="{FONT}" font-size="26" fill="#a99fd3">{escape(v)}</text>')
    p.append('</svg>')
    return "\n".join(p)


def background(tmp: Path):
    """Night sky with moon and a smaller moth on the left."""
    shapes = Path(__file__).with_name("noctalia-night-shapes.svg").read_text()
    # shrink and move the moth out of the panel's way
    # small moth in the bottom-right corner, moon top-right, both clear of the panel
    shapes = shapes.replace('translate(1250,1230) rotate(-14) scale(1.15)',
                            'translate(3620,1990) rotate(-14) scale(0.2)')
    shapes = shapes.replace('M1650,980 C2050,760 2400,690 2700,660', 'M0,0')
    shapes = shapes.replace('cx="2930" cy="610" r="170"', 'cx="3600" cy="190" r="120"')
    shapes = shapes.replace('cx="3000" cy="565" r="150"', 'cx="3650" cy="158" r="106"')
    shapes = shapes.replace('cx="2930" cy="610" r="260"', 'cx="3600" cy="190" r="190"')
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

    img += radial(3600, 190, 900, [70, 45, 130], 0.55)
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
