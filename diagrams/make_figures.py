#!/usr/bin/env python3
"""Generate publication-quality vector figures (SVG) + high-DPI PNG (via
rsvg-convert) for the audio-TRNG IDP presentation.

One shared palette and typographic scale are used across every figure so the
set reads like figures from a single paper.

Run:  uv run python diagrams/make_figures.py
SVGs are always written; PNG export needs rsvg-convert (gracefully skipped
with a hint when it is not installed, e.g. on a fresh Windows box).
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PNG_WARNED = False  # print the missing-rsvg hint only once

# ----------------------------------------------------------------------------
# Palette (muted, print-safe; one accent family per semantic role)
# ----------------------------------------------------------------------------
INK   = "#152230"   # primary text
MUTED = "#5b6b7a"   # secondary text
HAIR  = "#c7d1da"   # hairlines / fills
WHITE = "#ffffff"

BLUE,  BLUE_F,  BLUE_D  = "#3d6fa3", "#e7eff8", "#204a70"   # physical source / audio
TEAL,  TEAL_F,  TEAL_D  = "#2f8f7f", "#dcefeb", "#1b6257"   # method / extraction
AMBER, AMBER_F, AMBER_D = "#c08a2b", "#fbefd6", "#8a5e14"   # gate / discipline
PLUM,  PLUM_F,  PLUM_D  = "#7a4b8f", "#ece3f4", "#57306a"   # output / crypto
RED,   RED_F,   RED_D   = "#b23a48", "#f8e1e3", "#8a2732"   # reject / caution
GREY_F = "#eef2f5"

SANS = "DejaVu Sans, Liberation Sans, sans-serif"
MONO = "DejaVu Sans Mono, monospace"

FLOOR = "#f7f9fb"   # subtle panel wash


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    """Tiny SVG builder. Coordinates are in pixels, origin top-left."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.el: list[str] = []

    # -- primitives ----------------------------------------------------------
    def raw(self, s: str):
        self.el.append(s)
        return self

    def text(self, x, y, s, size=13, fill=INK, anchor="start", weight="normal",
             family=SANS, italic=False, opacity=1.0, ls=0.0):
        st = ' font-style="italic"' if italic else ""
        lsp = f' letter-spacing="{ls}"' if ls else ""
        self.el.append(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"'
            f'{st}{lsp} opacity="{opacity}">{esc(s)}</text>')
        return self

    def rect(self, x, y, w, h, fill="none", stroke=None, r=10, sw=1.6,
             opacity=1.0, dash=None):
        s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" '
             f'fill="{fill}" opacity="{opacity}"')
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            s += f' stroke-dasharray="{dash}"'
        return self.raw(s + "/>")

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.6, dash=None, cap="round"):
        s = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}" stroke-linecap="{cap}"')
        if dash:
            s += f' stroke-dasharray="{dash}"'
        return self.raw(s + "/>")

    def path(self, d, fill="none", stroke=INK, sw=1.6, dash=None,
             cap="round", join="round"):
        s = (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
             f'stroke-linecap="{cap}" stroke-linejoin="{join}"')
        if dash:
            s += f' stroke-dasharray="{dash}"'
        return self.raw(s + "/>")

    def poly(self, pts, fill, stroke=None, sw=1.4, opacity=1.0):
        p = " ".join(f"{x},{y}" for x, y in pts)
        s = f'<polygon points="{p}" fill="{fill}" opacity="{opacity}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        return self.raw(s + "/>")

    # -- composites ----------------------------------------------------------
    def arrow(self, x1, y1, x2, y2, color=INK, sw=1.8, head=10.0):
        """Line with a solid triangular head at (x2, y2)."""
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, stroke=color, sw=sw)
        px, py = -math.sin(ang), math.cos(ang)
        hw = head * 0.52
        self.poly([(x2, y2),
                   (bx + hw * px, by + hw * py),
                   (bx - hw * px, by - hw * py)], fill=color)
        return self

    def elbow_arrow(self, x1, y1, x2, y2, color=INK, sw=1.8, head=10.0):
        """Right-angle connector: horizontal then vertical, arrow at end."""
        mx = x2
        self.line(x1, y1, mx, y1, stroke=color, sw=sw)
        self.arrow(mx, y1, x2, y2, color=color, sw=sw, head=head)
        return self

    def chip(self, x, y, bits, cw=22, ch=26, size=13, tint=TEAL_F, on_1=True):
        """Draw a bit string as a row of cells (1s tinted)."""
        for i, b in enumerate(bits):
            cx = x + i * cw
            fill = tint if (on_1 and b == "1") else WHITE
            self.rect(cx, y, cw, ch, fill=fill, stroke=HAIR, r=3, sw=1.1)
            self.text(cx + cw / 2, y + ch * 0.66, b, size=size, anchor="middle",
                      family=MONO, fill=INK)
        return self

    def badge(self, x, y, label, fill, stroke, text_fill=WHITE, h=22, size=11.5,
              pad=11, weight="bold"):
        w = pad * 2 + len(label) * size * 0.60
        self.rect(x, y, w, h, fill=fill, stroke=stroke, r=h / 2, sw=1.2)
        self.text(x + w / 2, y + h * 0.7, label, size=size, anchor="middle",
                  fill=text_fill, weight=weight)
        return w

    def caption(self, label, desc, num=None):
        y = self.h - 22
        if num:
            self.text(28, y, num, size=12, fill=MUTED, weight="bold")
        self.text(58 if num else 28, y, f"{label}  ", size=12, fill=INK, weight="bold")
        self.text((58 if num else 28) + 7.0 * len(label) + 10, y, desc,
                  size=12, fill=MUTED)
        return self

    # -- output --------------------------------------------------------------
    def figure(self) -> str:
        defs = (
            '<defs>'
            '<linearGradient id="wash" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{WHITE}"/>'
            f'<stop offset="1" stop-color="{FLOOR}"/>'
            '</linearGradient>'
            '<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.55"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/>'
            '</linearGradient>'
            '</defs>')
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">')
        return (head + defs +
                f'<rect width="{self.w}" height="{self.h}" fill="{WHITE}"/>' +
                "".join(self.el) + "</svg>")


def save(svg: SVG, name: str, scale: float = 2.0):
    sfile = HERE / f"{name}.svg"
    sfile.write_text(svg.figure(), encoding="utf-8")
    png = HERE / f"{name}.png"
    try:
        subprocess.run(["rsvg-convert", "-z", str(scale), str(sfile), "-o", str(png)],
                       check=True)
        print(f"  wrote {name}.svg + {name}.png")
    except FileNotFoundError:
        global _PNG_WARNED
        if not _PNG_WARNED:
            print("  note: 'rsvg-convert' not found - PNG export skipped, "
                  "SVGs written instead.\n"
                  "        install librsvg to get PNGs "
                  "(pacman -S librsvg / winget install GNOME.GtkForWindows_librsvg)")
            _PNG_WARNED = True
        print(f"  wrote {name}.svg")


def panel(x, y, w, h, title, accent, tag=None):
    """Section panel: wash card + accent title bar + optional corner tag."""
    s = SVG(0, 0)  # placeholder, not used; real panels drawn inline below
    return s


# ============================================================================
# Figure 1 — End-to-end system architecture
# ============================================================================
def fig1() -> SVG:
    W, H = 1680, 800
    s = SVG(W, H)
    s.text(40, 58, "End-to-end system architecture", size=27, weight="bold")
    s.text(40, 86, "A true random number generator whose entropy is drawn only "
                   "from physical processes in bird-chirp audio — no cryptographic conditioning.",
           size=14.5, fill=MUTED)
    s.line(40, 106, W - 40, 106, stroke=HAIR, sw=1.2)

    top = 132

    # --- Panel A: physical source -----------------------------------------
    ax, aw = 40, 470
    s.rect(ax, top, aw, 470, fill="#fbfdff", stroke=HAIR, r=14, sw=1.4)
    s.rect(ax, top, aw, 44, fill=BLUE, r=14, sw=0)
    s.rect(ax, top + 30, aw, 14, fill=BLUE, r=0, sw=0)
    s.text(ax + 18, top + 29, "1 · PHYSICAL ENTROPY SOURCE", size=14,
           fill=WHITE, weight="bold", ls=1.2)

    items = [
        ("Bird-chirp field recordings", "xeno-canto · field MP3s · native sample rate"),
        ("ADC quantisation noise", "lowest bits of each 16-bit sample"),
        ("Environmental / acoustic noise", "uncorrelated per-channel noise floor"),
        ("Non-stationary vocal content", "song / silence / tonal transitions"),
    ]
    y = top + 66
    for t, d in items:
        s.rect(ax + 18, y, aw - 36, 82, fill=BLUE_F, stroke=BLUE, r=10, sw=1.3)
        s.text(ax + 34, y + 33, t, size=14.5, fill=BLUE_D, weight="bold")
        s.text(ax + 34, y + 57, d, size=12, fill=MUTED)
        y += 96
    s.text(ax + 18, top + 446, "Entropy is microscopic & unpredictable —",
           size=12, fill=MUTED, italic=True)
    s.text(ax + 18, top + 464, "never algorithmic.", size=12, fill=MUTED, italic=True)

    # --- Panel B: method --------------------------------------------------
    bx, bw = 546, 780
    s.rect(bx, top, bw, 470, fill="#fbfefd", stroke=HAIR, r=14, sw=1.4)
    s.rect(bx, top, bw, 44, fill=TEAL, r=14, sw=0)
    s.rect(bx, top + 30, bw, 14, fill=TEAL, r=0, sw=0)
    s.text(bx + 18, top + 29, "2 · UNCONDITIONED EXTRACTION METHOD", size=14,
           fill=WHITE, weight="bold", ls=1.2)

    steps = [
        ("trim silence", "remove lead-in zeros & tails (no entropy, but biasing)"),
        ("stereo common-mode rejection", "L ⊕ R cancels shared tone & decoder artefacts"),
        ("mixed physical extractor", "(y & 1) ⊕ (Δy & 1) ⊕ ((y >> 2) & 1)  per sample"),
        ("source-health gate  ·  SP 800-90B style", "discard low-entropy frames — never transform data"),
    ]
    y = top + 66
    for i, (t, d) in enumerate(steps):
        h = 72
        s.rect(bx + 24, y, bw - 48, h, fill=TEAL_F, stroke=TEAL, r=10, sw=1.4)
        s.text(bx + 44, y + 31, t, size=14.5, fill=TEAL_D, weight="bold")
        s.text(bx + 44, y + 54, d, size=12.5, fill=MUTED)
        if i < len(steps) - 1:
            s.arrow(bx + bw / 2, y + h, bx + bw / 2, y + h + 16,
                    color=TEAL, sw=1.8, head=9)
        y += h + 16
    # "no hashing" stamp (below the flow, centred)
    stamp_w = 232
    stx = bx + (bw - stamp_w) / 2
    s.rect(stx, top + 424, stamp_w, 30, fill=WHITE, stroke=TEAL, r=15, sw=1.4)
    s.text(stx + stamp_w / 2, top + 444, "NO SHA / AES CONDITIONING", size=12,
           anchor="middle", fill=TEAL_D, weight="bold", ls=0.6)

    # --- Panel C: outputs --------------------------------------------------
    cx, cw = 1366, 274
    s.rect(cx, top, cw, 470, fill="#fdfbff", stroke=HAIR, r=14, sw=1.4)
    s.rect(cx, top, cw, 44, fill=PLUM, r=14, sw=0)
    s.rect(cx, top + 30, cw, 14, fill=PLUM, r=0, sw=0)
    s.text(cx + 18, top + 29, "3 · OUTPUTS & APPLICATION", size=14,
           fill=WHITE, weight="bold", ls=1.1)

    outs = ["raw bit stream", "uint32 stream", "grayscale key image",
            "image keystream (XOR)"]
    y = top + 70
    for o in outs:
        s.rect(cx + 18, y, cw - 36, 40, fill=PLUM_F, stroke=PLUM, r=8, sw=1.2)
        s.text(cx + 32, y + 26, o, size=13.5, fill=PLUM_D, weight="bold")
        y += 50
    s.arrow(cx + cw / 2, y + 6, cx + cw / 2, y + 34, color=PLUM, sw=1.8)
    s.rect(cx + 18, y + 38, cw - 36, 82, fill=WHITE, stroke=PLUM, r=10, sw=1.5)
    s.text(cx + cw / 2, y + 68, "encrypt / decrypt", size=14, anchor="middle",
           fill=PLUM_D, weight="bold")
    s.text(cx + cw / 2, y + 90, "cipher = plain ⊕ keystream", size=12,
           anchor="middle", fill=MUTED, family=MONO)
    s.text(cx + cw / 2, y + 110, "byte-identical round-trip", size=11.5,
           anchor="middle", fill=MUTED, italic=True)

    # --- connectors A→B→C --------------------------------------------------
    s.arrow(ax + aw + 2, top + 235, bx - 6, top + 235, color=INK, sw=2.0, head=12)
    s.arrow(bx + bw + 2, top + 235, cx - 6, top + 235, color=INK, sw=2.0, head=12)

    # --- validation band ---------------------------------------------------
    vy = top + 502
    s.rect(40, vy, W - 80, 96, fill=FLOOR, stroke=HAIR, r=14, sw=1.4)
    s.text(60, vy + 34, "VALIDATION — performed on the RAW, unconditioned bits",
           size=14, weight="bold", fill=INK)
    notes = [
        ("SP 800-90B", "min-entropy estimate"),
        ("SP 800-22", "monobit · runs · autocorrelation"),
        ("uniformity", "byte histogram, |z| < 3"),
        ("benchmark", "throughput vs PRNG / CSPRNG"),
    ]
    x = 64
    for t, d in notes:
        s.rect(x, vy + 50, 372, 34, fill=WHITE, stroke=HAIR, r=8, sw=1.2)
        s.text(x + 12, vy + 72, t, size=12.5, weight="bold", fill=BLUE_D)
        s.text(x + 12 + 10.5 * len(t) + 8, vy + 72, "— " + d, size=12, fill=MUTED)
        x += 384

    s.caption("Figure 1", "Entropy source → method-level extraction → outputs and "
              "image-encryption application.", num="Fig 1")
    return s


# ============================================================================
# Figure 2 — Signal-processing pipeline (sample level)
# ============================================================================
def _waveform(s, x0, x1, y0, color, n=260, sw=1.25):
    def amp(t):
        if t < 0.15:
            return 1.6 + 1.1 * math.sin(t * 90)
        if t < 0.74:
            u = (t - 0.15) / 0.59
            env = 46 * abs(math.sin(u * math.pi * 3.6)) ** 0.7
            return 3.5 + env * (0.62 + 0.38 * math.sin(u * 41))
        u = (t - 0.74) / 0.26
        return max(0.9, 34 * math.exp(-6.5 * u) * (0.5 + 0.5 * abs(math.sin(u * 55))))
    import math as _m
    pts = [(x0 + i / (n - 1) * (x1 - x0), amp(i / (n - 1))) for i in range(n)]
    s.line(x0, y0, x1, y0, stroke=HAIR, sw=1.0)
    for x, a in pts:
        s.line(x, y0 - a, x, y0 + a, stroke=color, sw=sw)


def fig2() -> SVG:
    W, H = 1800, 780
    s = SVG(W, H)
    s.text(54, 56, "Signal-processing pipeline", size=26, weight="bold")
    s.text(54, 84, "From a bird-chirp recording to a clean, unconditioned bit stream. "
                   "Every stage is deterministic DSP except the source itself.",
           size=14, fill=MUTED)
    s.line(54, 104, W - 54, 104, stroke=HAIR, sw=1.2)

    # --- Row 1: the acoustic signal, with structure annotated -----------------
    s.rect(54, 132, W - 108, 214, fill=FLOOR, stroke=HAIR, r=14, sw=1.3)
    y0 = 240
    _waveform(s, 84, W - 84, y0, BLUE, n=300, sw=1.15)
    # region brackets
    xs = [84, 84 + 0.15 * (W - 168), 84 + 0.74 * (W - 168), W - 84]
    labs = [("lead-in silence", "trimmed", BLUE_D),
            ("bird vocalization (wide-band, non-stationary)", "", BLUE_D),
            ("tail", "trimmed", BLUE_D)]
    seg = [(xs[0], xs[1], labs[0]), (xs[1], xs[2], labs[1]), (xs[2], xs[3], labs[2])]
    for a, b, (t, u, c) in seg:
        s.line(a, 168, b, 168, stroke=BLUE, sw=1.6)
        s.line(a, 160, a, 176, stroke=BLUE, sw=1.6)
        s.line(b, 160, b, 176, stroke=BLUE, sw=1.6)
        s.text((a + b) / 2, 158, t, size=12, anchor="middle", fill=c, weight="bold")
        if u:
            s.text((a + b) / 2, 320, u, size=11, anchor="middle", fill=MUTED, italic=True)
    s.text(W - 84, 320, "time →", size=11, anchor="end", fill=MUTED)
    s.arrow(W - 108, 346, W - 108, 384, color=INK, sw=1.8)
    s.text(W - 120, 372, "digitise @ native rate", size=11.5, anchor="end", fill=MUTED)

    # --- Row 2: discrete chain ------------------------------------------------
    n = 6
    bw, gap = 252, 36
    x0 = 54
    ytop, bh = 430, 118
    steps = [
        ("load", "native sample rate", "44.1 kHz, stereo"),
        ("trim silence", "lead-in zeros & tails", "remove biasing runs"),
        ("stereo  L ⊕ R", "common-mode rejection", "cancel shared tone"),
        ("mixed extractor", "3 complementary views", "(y&1)⊕(Δy&1)⊕((y>>2)&1)"),
        ("health gate", "SP 800-90B style", "discard, never transform"),
        ("pack → bytes", "uint32 / key image", "raw, unconditioned"),
    ]
    for i, (t, sub, det) in enumerate(steps):
        x = x0 + i * (bw + gap)
        accent = [BLUE, BLUE, TEAL, TEAL, AMBER, PLUM][i]
        fillc = [BLUE_F, BLUE_F, TEAL_F, TEAL_F, AMBER_F, PLUM_F][i]
        s.rect(x, ytop, bw, bh, fill=fillc, stroke=accent, r=12, sw=1.5)
        s.text(x + 16, ytop + 30, t, size=15, fill=accent if False else INK,
               weight="bold")
        s.text(x + 16, ytop + 54, sub, size=12.5, fill=MUTED)
        s.text(x + 16, ytop + 78, det, size=11, fill=MUTED, family=MONO)
        # number chip
        s.rect(x + bw - 34, ytop + 12, 22, 22, fill=WHITE, stroke=accent,
               r=11, sw=1.2)
        s.text(x + bw - 23, ytop + 28, str(i + 1), size=12, anchor="middle",
               fill=accent, weight="bold")
        if i < n - 1:
            s.arrow(x + bw + 3, ytop + bh / 2, x + bw + gap - 3, ytop + bh / 2,
                    color=INK, sw=1.8, head=9)

    # bit-level detail strip below the chain
    dy = ytop + bh + 26
    # glyph for step 3
    gx = x0 + 2 * (bw + gap) + 16
    s.line(gx, dy, gx + 26, dy, stroke=TEAL, sw=1.6)
    s.line(gx, dy + 16, gx + 26, dy + 16, stroke=TEAL, sw=1.6)
    s.text(gx + 34, dy + 14, "L,R identical ⟶ cancel", size=10.5, fill=MUTED)
    # gate glyph
    gx = x0 + 4 * (bw + gap) + 16
    for k in range(6):
        col = TEAL if k != 3 else RED
        s.rect(gx + k * 15, dy + 2, 11, 14, fill=WHITE if k == 3 else TEAL_F,
               stroke=col, r=2, sw=1.2)
    s.text(gx + 100, dy + 14, "keep / drop frames", size=10.5, fill=MUTED)

    s.caption("Figure 2", "Acoustic structure → DSP stages → bit-level operations. "
              "The health gate removes — never rewrites — weak audio.", num="Fig 2")
    return s


# ============================================================================
# Figure 3 — Entropy-extraction worked example (one sample)
# ============================================================================
def fig3() -> SVG:
    W, H = 1500, 720
    s = SVG(W, H)
    s.text(54, 56, "Entropy extraction, sample by sample", size=26, weight="bold")
    s.text(54, 84, "One 16-bit sample: the top bits carry the chirp's shape; the low bits "
                   "carry ADC & environmental noise.", size=14, fill=MUTED)
    s.line(54, 104, W - 54, 104, stroke=HAIR, sw=1.2)

    sample = "0011010100101101"
    cw, ch = 46, 52
    x0, y0 = 90, 150
    s.text(x0, y0 - 16, "16-bit sample  y  =  0b" + sample, size=14.5,
           weight="bold", family=MONO, fill=INK)
    for i, b in enumerate(sample):
        x = x0 + i * cw
        signal_bit = i < 7
        fill = BLUE_F if signal_bit else TEAL_F
        s.rect(x, y0, cw - 6, ch, fill=fill, stroke=HAIR, r=5, sw=1.2)
        s.text(x + (cw - 6) / 2, y0 + 34, b, size=17, anchor="middle",
               family=MONO, fill=INK)
    s.text(x0 + 3 * cw, y0 + ch + 22, "signal-shaped bits", size=11.5,
           anchor="middle", fill=BLUE_D, weight="bold")
    s.text(x0 + 11.5 * cw, y0 + ch + 22, "noise-rich bits (entropy)", size=11.5,
           anchor="middle", fill=TEAL_D, weight="bold")
    s.line(x0 + 7 * cw - 3, y0 - 6, x0 + 7 * cw - 3, y0 + ch + 8,
           stroke=HAIR, sw=1.2, dash="4 4")

    # three views
    vy = 300
    s.text(90, vy, "Three complementary physical views", size=15, weight="bold")
    views = [
        ("a = y & 1", "raw LSB", ["1"], TEAL),
        ("b = Δy & 1", "LSB of first difference", ["0"], TEAL),
        ("c = (y >> 2) & 1", "shifted bit-plane LSB", ["1"], TEAL),
    ]
    rowy = vy + 24
    for i, (name, desc, bits, col) in enumerate(views):
        y = rowy + i * 58
        s.text(90, y + 24, name, size=13.5, family=MONO, fill=INK, weight="bold")
        s.text(250, y + 24, desc, size=12, fill=MUTED)
        s.rect(430, y + 2, 40, 34, fill=TEAL_F if bits[0] == "1" else WHITE,
               stroke=HAIR, r=5, sw=1.2)
        s.text(450, y + 26, bits[0], size=16, anchor="middle", family=MONO)
        s.arrow(486, y + 19, 520, y + 19, color=MUTED, sw=1.4, head=7)
    # bias note
    s.text(560, rowy + 44, "Each view alone is biased by the tone /", size=12,
           fill=MUTED, italic=True)
    s.text(560, rowy + 64, "decoder; their XOR cancels it.", size=12,
           fill=MUTED, italic=True)

    # XOR gate
    gx, gy = 620, 402
    s.path(f"M {gx} {gy} C {gx+44} {gy-14} {gx+86} {gy+4} {gx+96} {gy+38} "
           f"C {gx+104} {gy+68} {gx+52} {gy+76} {gx} {gy+76} Z",
           fill=WHITE, stroke=PLUM, sw=1.8)
    s.line(gx - 34, gy + 18, gx + 6, gy + 18, stroke=TEAL, sw=1.8)
    s.line(gx - 34, gy + 40, gx + 4, gy + 40, stroke=TEAL, sw=1.8)
    s.line(gx + 4, gy + 40, gx + 46, gy + 58, stroke=TEAL, sw=1.8)
    s.line(gx - 34, gy + 62, gx + 8, gy + 62, stroke=TEAL, sw=1.8)
    s.text(gx + 30, gy + 46, "XOR", size=13, anchor="middle", fill=PLUM_D,
           weight="bold")
    s.arrow(gx + 104, gy + 38, gx + 168, gy + 38, color=PLUM, sw=1.8)
    s.rect(gx + 170, gy + 14, 66, 48, fill=PLUM_F, stroke=PLUM, r=8, sw=1.6)
    s.text(gx + 203, gy + 45, "1 bit", size=13, anchor="middle",
           fill=PLUM_D, weight="bold")
    s.text(gx + 250, gy + 45, "≈ uniform", size=12, fill=MUTED, italic=True)

    # result strip
    res_y = 560
    s.rect(90, res_y, W - 180, 84, fill=FLOOR, stroke=HAIR, r=12, sw=1.3)
    s.text(112, res_y + 34, "Output bit per sample", size=13.5, weight="bold",
           fill=INK)
    s.text(112, res_y + 60, "= (y & 1) ⊕ (Δy & 1) ⊕ ((y >> 2) & 1)", size=13.5,
           family=MONO, fill=TEAL_D)
    s.text(W - 112, res_y + 34, "No hashing · no whitening", size=13,
           anchor="end", fill=PLUM_D, weight="bold")
    s.text(W - 112, res_y + 60, "every bit traceable to a measurement", size=12,
           anchor="end", fill=MUTED, italic=True)

    s.caption("Figure 3", "Mixing three biased views yields a near-uniform physical bit.",
              num="Fig 3")
    return s


# ============================================================================
# Figure 4 — Source-health gate (discard-only)
# ============================================================================
def fig4() -> SVG:
    W, H = 1500, 720
    s = SVG(W, H)
    s.text(54, 56, "Source-health gate: discard, never transform", size=26,
           weight="bold")
    s.text(54, 84, "NIST SP 800-90B style health testing of whole audio frames — "
                   "low-entropy segments are refused, not rewritten.", size=14, fill=MUTED)
    s.line(54, 104, W - 54, 104, stroke=HAIR, sw=1.2)

    # block strip
    zs = [0.3, -0.6, 0.9, -0.4, 0.7, -1.1, 0.2, 0.5, 2.4, 3.1, 2.7, 1.9, 2.2,
          -0.3, 0.8, -0.7, 0.4, 1.0, -0.5, 0.6, 0.1, -0.9]
    x0, bw, bh, by = 90, 54, 62, 170
    s.text(90, by - 14, "audio frames (block = 16 384 bits, 2 048 bytes each)",
           size=12, fill=MUTED)
    zlim = 1.0
    for i, z in enumerate(zs):
        x = x0 + i * (bw + 6)
        keep = abs(z) <= zlim
        fill = TEAL_F if keep else RED_F
        col = TEAL if keep else RED
        s.rect(x, by, bw, bh, fill=fill, stroke=col, r=8, sw=1.5)
        s.text(x + bw / 2, by + 26, f"z={z:+.1f}", size=10.5, anchor="middle",
               fill=col, family=MONO, weight="bold")
        s.text(x + bw / 2, by + 46, "keep" if keep else "drop", size=10.5,
               anchor="middle", fill=col)
    s.text(x0, by + bh + 24, "field / ambience — uniform", size=12, fill=TEAL_D,
           weight="bold")
    s.text(x0 + 7 * (bw + 6), by + bh + 24, "tonal passage — non-uniform", size=12,
           fill=RED_D, weight="bold")
    s.text(x0 + 14 * (bw + 6), by + bh + 24, "field / ambience — uniform", size=12,
           fill=TEAL_D, weight="bold")

    # output stream = concatenation
    oy = 300
    s.text(x0, oy + 18, "output = only the kept frames, concatenated", size=13.5,
           weight="bold", fill=INK)
    keepxs = [i for i, z in enumerate(zs) if abs(z) <= zlim]
    x = x0
    for k, i in enumerate(keepxs):
        s.rect(x, oy + 30, 26, 34, fill=TEAL_F, stroke=TEAL, r=4, sw=1.2)
        x += 28
        if x > W - 120:
            break
    s.text(x + 12, oy + 52, "→  uniform raw bit stream", size=13, fill=TEAL_D,
           weight="bold")

    # right panel: rule card
    px, pw = 90, 620
    py = 400
    s.rect(px, py, pw, 232, fill=FLOOR, stroke=HAIR, r=12, sw=1.3)
    s.text(px + 20, py + 32, "Gate rule", size=14, weight="bold", fill=INK)
    rules = [
        "per block, compute byte-histogram uniformity statistic  z",
        "|z| ≤ zlim  →  keep the block          |z| > zlim  →  discard",
        "discarding cannot increase entropy consumption",
        "the gate never rewrites, whitens or expands data",
        "report the kept fraction (source-yield diagnostic)",
    ]
    for i, r in enumerate(rules):
        yy = py + 62 + i * 32
        s.rect(px + 22, yy - 7, 7, 7, fill=AMBER, r=2, sw=0)
        s.text(px + 42, yy, r, size=12.5, fill=MUTED)

    # right panel: accept region sketch
    hx, hw = 760, W - 760 - 90
    s.rect(hx, py, hw, 232, fill="#fdfbff", stroke=HAIR, r=12, sw=1.3)
    s.text(hx + 20, py + 32, "Distribution of block statistics", size=14,
           weight="bold", fill=PLUM_D)
    base = py + 186
    s.line(hx + 30, base, hx + hw - 30, base, stroke=MUTED, sw=1.4)
    s.line(hx + 30, base, hx + 30, py + 62, stroke=MUTED, sw=1.4)
    # accept band
    s.rect(hx + 30, py + 62, hw - 60, 124, fill=TEAL_F, r=0, sw=0, opacity=0.55)
    # density bars
    heights = [6, 12, 22, 34, 52, 74, 92, 104, 96, 78, 58, 40, 26, 16, 9]
    nb = len(heights)
    for i, hgt in enumerate(heights):
        bx = hx + 34 + i * ((hw - 68) / nb)
        wbar = (hw - 68) / nb - 5
        inside = 4 <= i <= 10
        s.rect(bx, base - hgt * 1.15, wbar, hgt * 1.15,
               fill=TEAL if inside else RED, r=3, sw=0, opacity=0.85)
    for t in (-1, 1):
        tx = hx + 30 + (hw - 60) * (0.5 + t * 0.24)
        s.line(tx, py + 62, tx, base, stroke=AMBER, sw=1.6, dash="5 4")
        s.text(tx, py + 56, f"z={t:+d}", size=11, anchor="middle", fill=AMBER_D,
               weight="bold")
    s.text(hx + hw / 2, base + 22, "block statistic  z", size=12, anchor="middle",
           fill=MUTED)

    s.caption("Figure 4", "Low-entropy frames are discarded; the surviving frames "
              "form a uniform stream with no rewriting.", num="Fig 4")
    return s


# ============================================================================
# Figure 5 — Validation suite and measured results
# ============================================================================
def fig5() -> SVG:
    W, H = 1560, 820
    s = SVG(W, H)
    s.text(54, 56, "Validation on raw, unconditioned bits", size=26, weight="bold")
    s.text(54, 84, "Statistical battery (SP 800-22 style) and entropy estimate — "
                   "reported before any conditioning, as there is none.", size=14, fill=MUTED)
    s.line(54, 104, W - 54, 104, stroke=HAIR, sw=1.2)

    # --- left: test table -----------------------------------------------------
    lx, lw = 54, 660
    s.text(lx, 148, "Test suite", size=15, weight="bold", fill=INK)
    rows = [
        ("monobit (frequency)", "stat = 0.00", "PASS"),
        ("runs", "stat < 3.29", "PASS"),
        ("autocorrelation (lag 1)", "r = +0.001", "PASS"),
        ("byte uniformity", "z = +1.30", "PASS"),
        ("min-entropy", "7.98 / 8.0 bits", "7.98"),
    ]
    y = 172
    for name, stat, tag in rows:
        s.rect(lx, y, lw, 62, fill=FLOOR, stroke=HAIR, r=10, sw=1.2)
        s.text(lx + 18, y + 27, name, size=13.5, fill=INK, weight="bold")
        s.text(lx + 18, y + 48, stat, size=12, fill=MUTED, family=MONO)
        ok = tag == "PASS"
        col = TEAL if ok else BLUE
        s.badge(lx + lw - 92, y + 19, tag, col, col)
        y += 72
    s.text(lx, y + 16, "All tests on the RAW extracted stream.", size=12,
           fill=MUTED, italic=True)

    # --- right: metrics -------------------------------------------------------
    rx, rw = 780, W - 780 - 54

    def metric(y, title, rows2, note):
        s.rect(rx, y, rw, 210, fill="#fbfdff", stroke=HAIR, r=12, sw=1.3)
        s.text(rx + 20, y + 30, title, size=14, weight="bold", fill=BLUE_D)
        bar_x, bar_w = rx + 190, rw - 250
        yy = y + 58
        for lab, val, frac, ideal, unit in rows2:
            s.text(rx + 20, yy + 14, lab, size=12, fill=MUTED)
            s.rect(bar_x, yy, bar_w, 16, fill=GREY_F, r=8, sw=0)
            s.rect(bar_x, yy, max(6, bar_w * frac), 16,
                   fill=TEAL, r=8, sw=0)
            s.line(bar_x + bar_w * ideal, yy - 4, bar_x + bar_w * ideal, yy + 20,
                   stroke=INK, sw=1.4, dash="3 3")
            s.text(rx + rw - 18, yy + 14, val, size=12, anchor="end",
                   fill=INK, family=MONO, weight="bold")
            yy += 42
        s.text(rx + 20, y + 196, note, size=11.5, fill=MUTED, italic=True)

    metric(132, "Generator output  (raw bits)", [
        ("P(1)  → ideal 0.5", "0.5000", 0.50, 0.50, ""),
        ("uniformity z → |z|<3", "+1.30", 0.22, 0.0, ""),
        ("min-entropy → 8.0", "7.98", 0.998, 1.0, "b/byte"),
    ], "dashed marker = ideal reference; 14 MB stream, chirp pool")

    metric(372, "Image-encryption demo  (512×512 grayscale)", [
        ("plain↔cipher corr → 0", "+0.0010", 0.02, 0.0, ""),
        ("cipher uniformity z", "−0.50", 0.17, 0.0, ""),
        ("cipher min-entropy", "7.89", 0.986, 1.0, "b/byte"),
    ], "round-trip byte-identical; wrong key ⇒ pixel change ≈ 99.6 % (target)")

    s.caption("Figure 5", "Reported metrics (from the current pipeline) against "
              "ideal references.", num="Fig 5")
    return s


# ============================================================================
# Figure 6 — Positioning and literature → gaps → objectives map
# ============================================================================
def fig6() -> SVG:
    W, H = 1680, 900
    s = SVG(W, H)
    s.text(54, 56, "Positioning and research map", size=26, weight="bold")
    s.text(54, 84, "How this approach differs from prior art, and how the survey "
                   "condenses into specific gaps and objectives.", size=14, fill=MUTED)
    s.line(54, 104, W - 54, 104, stroke=HAIR, sw=1.2)

    # --- Row 1: two contrasting pipelines ------------------------------------
    def pipeline(x, w, title, accent, fillc, boxes, note):
        s.rect(x, 128, w, 236, fill=fillc, stroke=accent, r=14, sw=1.5)
        s.text(x + 20, 160, title, size=14.5, weight="bold", fill=accent)
        n = len(boxes)
        bwid = (w - 40 - (n - 1) * 46) / n
        by = 186
        for i, (t, sub) in enumerate(boxes):
            bx = x + 20 + i * (bwid + 46)
            s.rect(bx, by, bwid, 86, fill=WHITE, stroke=accent, r=10, sw=1.4)
            s.text(bx + bwid / 2, by + 38, t, size=12.5, anchor="middle",
                   fill=INK, weight="bold")
            s.text(bx + bwid / 2, by + 62, sub, size=11, anchor="middle",
                   fill=MUTED)
            if i < n - 1:
                s.arrow(bx + bwid + 6, by + 43, bx + bwid + 40, by + 43,
                        color=accent, sw=1.8, head=9)
        s.text(x + 20, 336, note, size=11.5, fill=MUTED, italic=True)

    pipeline(54, 760, "Conventional hardware TRNG / conditioned RNG", RED_D, RED_F, [
        ("physical source", "jitter · memristor · optics"),
        ("cryptographic conditioner", "SHA-256 · AES-CTR"),
        ("output", "random-looking"),
    ], "The conditioner maps any input to uniform output → the physical source "
       "becomes statistically irrelevant and the result is unauditable.")

    pipeline(846, 780, "This work — unconditioned physical extraction", TEAL_D,
             TEAL_F, [
        ("physical source", "bird-chirp audio"),
        ("method-level extraction", "L⊕R · mix · gate"),
        ("output", "raw, traceable"),
    ], "Every bit is attributable to a measurement; there is no hashing or "
       "whitening anywhere in the pipeline.")

    # --- Row 2: themes → gaps → objectives -----------------------------------
    ry = 420
    cols = [
        (54, 500, "Literature themes", BLUE, BLUE_F, [
            "1  Physical & acoustic entropy sources",
            "2  Extraction, conditioning & validation",
            "3  Crypto applications & RNG security",
        ], "59 journal papers · 3 themes"),
        (590, 500, "Research gaps", AMBER, AMBER_F, [
            "G1  no conditioning-free commodity source",
            "G2  common-mode correlation ignored",
            "G3  weak estimation for non-stationary audio",
            "G4  validation usually post-conditioning",
            "G5  chaos keystreams broken by CPA",
            "G6  throughput rarely benchmarked",
        ], "6 gaps, each traced to specific papers"),
        (1126, 500, "Objectives", PLUM, PLUM_F, [
            "O1  source characterisation  ≥7.5 b/byte",
            "O2  SP 800-22 ≥98% on raw bits",
            "O3  throughput ≥20 kbit/s vs PRNG",
            "O4  encryption NPCR≥99.6%, corr≤0.01",
        ], "4 measurable outcomes"),
    ]
    for x, w, title, accent, fillc, items, foot in cols:
        h = 330
        s.rect(x, ry, w, h, fill=WHITE, stroke=HAIR, r=14, sw=1.3)
        s.rect(x, ry, w, 40, fill=accent, r=14, sw=0)
        s.rect(x, ry + 26, w, 14, fill=accent, r=0, sw=0)
        s.text(x + 18, ry + 27, title.upper(), size=13.5, fill=WHITE,
               weight="bold", ls=1.0)
        yy = ry + 72
        for it in items:
            s.rect(x + 20, yy - 8, 8, 8, fill=accent, r=2, sw=0)
            s.text(x + 40, yy, it, size=12.5, fill=INK)
            yy += 40
        s.text(x + 18, ry + h - 18, foot, size=11.5, fill=MUTED, italic=True)
    for a, b in [(554, 590), (1090, 1126)]:
        s.arrow(a + 2, ry + 165, b - 2, ry + 165, color=INK, sw=2.0, head=11)

    s.caption("Figure 6", "Prior-art contrast (top) and the survey → gaps → "
              "objectives logic (bottom).", num="Fig 6")
    return s


def main():
    HERE.mkdir(exist_ok=True)
    figures = [("fig1_system_architecture", fig1),
               ("fig2_signal_pipeline", fig2),
               ("fig3_entropy_extraction", fig3),
               ("fig4_health_gate", fig4),
               ("fig5_validation_results", fig5),
               ("fig6_research_map", fig6)]
    for name, fn in figures:
        print(f"building {name}")
        save(fn(), name, scale=2.0)


if __name__ == "__main__":
    main()
