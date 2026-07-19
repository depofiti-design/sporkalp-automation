# -*- coding: utf-8 -*-
"""Çapraz platform çizim/animasyon yardımcıları. macOS / Windows / Linux."""
import os, sys, math, platform
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import config as C

# ---------- FONT (çapraz platform) ----------
_FALLBACKS = {
    "Darwin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial.ttf",
               "/Library/Fonts/Arial Bold.ttf"],
    "Windows": [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"],
    "Linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
}
def _font_path():
    if os.path.exists(C.FONT_BOLD): return C.FONT_BOLD
    for p in _FALLBACKS.get(platform.system(), []):
        if os.path.exists(p): return p
    return None

def F(size):
    """kalın başlık fontu (config.FONT_BOLD, yoksa sistem yedeği, yoksa PIL default)."""
    fp = _font_path()
    if fp:
        try: return ImageFont.truetype(fp, max(8, int(size)))
        except Exception: pass
    return ImageFont.load_default()

FA = F  # gövde için de aynı font (istersen ayrı tanımla)

# ---------- ARKA PLAN ----------
def gradient_bg(w=None, h=None):
    w = w or C.WIDTH; h = h or C.HEIGHT
    img = Image.new("RGB", (w, h)); px = img.load()
    for y in range(h):
        t = y / h
        px_row = (int(C.BG_TOP[0]+(C.BG_BOT[0]-C.BG_TOP[0])*t),
                  int(C.BG_TOP[1]+(C.BG_BOT[1]-C.BG_TOP[1])*t),
                  int(C.BG_TOP[2]+(C.BG_BOT[2]-C.BG_TOP[2])*t))
        for x in range(w): px[x, y] = px_row
    return img.convert("RGBA")

# ---------- METİN / GLOW ----------
def glow(img, cx, cy, rx, ry, color, blur=60, alpha=90):
    L = Image.new("RGBA", img.size, (0,0,0,0))
    ImageDraw.Draw(L).ellipse((cx-rx, cy-ry, cx+rx, cy+ry), fill=tuple(color)+(alpha,))
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(blur)))

def ctext(img, d, cx, y, text, fnt, fill, glow_col=None, gb=8):
    bb = d.textbbox((0,0), text, font=fnt); w = bb[2]-bb[0]; x = cx-w/2
    if glow_col:
        gl = Image.new("RGBA", img.size, (0,0,0,0))
        ImageDraw.Draw(gl).text((x,y), text, font=fnt, fill=glow_col)
        img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(gb)))
    d.text((x,y), text, font=fnt, fill=fill); return w

def fit(d, text, maxw, start, floor=20):
    s = start
    while s > floor:
        f = F(s)
        if d.textbbox((0,0), text, font=f)[2] <= maxw: return f
        s -= 2
    return F(floor)

def pill(d, cx, cy, text, fnt, fg=None, bg=(10,40,28,235), outline=None, padx=30, pady=14):
    fg = fg or C.FG; outline = outline or C.PRIMARY
    w = d.textbbox((0,0), text, font=fnt)[2]
    d.rounded_rectangle((cx-w//2-padx, cy-pady, cx+w//2+padx, cy+fnt.size+pady),
                        radius=(fnt.size+2*pady)//2, fill=bg, outline=outline, width=3)
    d.text((cx-w//2, cy), text, font=fnt, fill=fg)

# ---------- GÖRSEL → DAİRE (logo/bayrak/foto) ----------
def circle_image(path, size, ring=None, rw=5):
    im = Image.open(path).convert("RGBA")
    w, h = im.size; s = min(w, h)
    im = im.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((size,size), Image.LANCZOS)
    m = Image.new("L",(size,size),0); ImageDraw.Draw(m).ellipse((0,0,size,size), fill=255)
    pad = (rw+4) if ring else 0
    out = Image.new("RGBA",(size+2*pad,size+2*pad),(0,0,0,0))
    if ring:
        ImageDraw.Draw(out).ellipse((pad-rw,pad-rw,pad+size+rw,pad+size+rw), outline=tuple(ring), width=rw)
    out.paste(im,(pad,pad),m); return out

def flag(iso, size, ring=None, rw=5):
    return circle_image(os.path.join(C.FLAGS_DIR, iso+".png"), size, ring, rw)

def logo_img(sz):
    return Image.open(C.LOGO).convert("RGBA").resize((sz,sz), Image.LANCZOS)

# ---------- ORTAK ÇERÇEVE ----------
def header(img, d, sz=120):
    cx = C.WIDTH//2
    if os.path.exists(C.LOGO):
        glow(img, cx, 60+sz//2, sz//2+14, sz//2+14, C.PRIMARY, 28, 70)
        img.alpha_composite(logo_img(sz), (cx-sz//2, 50))
        ty = 50+sz+4
    else:
        ty = 70
    ctext(img, d, cx, ty, C.BRAND_NAME, F(54), C.PRIMARY, tuple(C.PRIMARY)+(150,), 10)

def footer(img, d, y=None):
    y = y or (C.HEIGHT-150); cx = C.WIDTH//2
    ctext(img, d, cx, y,   C.FOOTER_LINE1, FA(30), C.GOLD)
    ctext(img, d, cx, y+42, C.FOOTER_LINE2, F(54), C.PRIMARY, tuple(C.PRIMARY)+(150,), 10)

# ---------- BEAT (müzik senkron) ----------
def get_beats(music_path, dur):
    import numpy as np, librosa
    y, sr = librosa.load(music_path, sr=22050, mono=True, duration=dur+1)
    tempo, bf = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    bt = [float(t) for t in librosa.frames_to_time(bf, sr=sr) if t <= dur]
    if bt and bt[0] > 0.2: bt = [0.0]+bt
    if len(bt) < 4:
        step = 60.0/float(np.atleast_1d(tempo)[0] or 120)
        bt = list(np.arange(0.3, dur, step))
    return np.array(bt)

def smoothstep(x): x = max(0.,min(1.,x)); return x*x*(3-2*x)
def back_ease(p):
    c1 = 1.45; c3 = c1+1
    return 1 + c3*((p-1)**3) + c1*((p-1)**2)
