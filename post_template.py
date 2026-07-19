# -*- coding: utf-8 -*-
"""Spor'un Kalbi — kurumsal haber post şablonu.
Her gönderi aynı yerleşimi kullanır: foto + kategori şeridi + başlık + @sporkalp watermark.
Stil sabittir; sadece metin/foto/kategori değişir (kurumsal tutarlılık).

Kullanım:
    from post_template import render_post
    render_post(
        photo_path="indirilen_haber_fotosu.jpg",
        category="olumsuz",
        headline="SİNGO ŞOKU!",
        subheadline="3 AY YOK!",
        caption="Fildişi Sahili'nin Almanya ile oynadığı maçta sakatlanan Singo'nun 3 ay sahalardan uzak kalması bekleniyor.",
        source="Milliyet",
        out_name="post_001.jpg",
    )
"""
import os
import time
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import config as C
import engine as E


def _load_photo(photo_path_or_url, w, h):
    if photo_path_or_url.startswith("http"):
        last_err = None
        r = None
        for attempt in range(1, 4):
            try:
                r = requests.get(
                    photo_path_or_url, timeout=20,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                r.raise_for_status()
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_err = e
                r = None
                if attempt < 3:
                    time.sleep(2 * attempt)
        if r is None:
            raise last_err
        tmp = os.path.join(C.OUT_DIR, "_tmp_src.jpg")
        os.makedirs(C.OUT_DIR, exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(r.content)
        photo_path_or_url = tmp
    im = Image.open(photo_path_or_url).convert("RGB")
    im = ImageOps.fit(im, (w, h), Image.LANCZOS)
    return im


def _wrap_lines(d, text, max_w, start_size, floor=36, max_lines=2):
    """Metni en büyük boyuttan başlayıp, max_lines içine sığana kadar küçülterek satırlara böler."""
    size = start_size
    while size >= floor:
        f = E.F(size)
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textbbox((0, 0), test, font=f)[2] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines and all(d.textbbox((0, 0), ln, font=f)[2] <= max_w for ln in lines):
            return f, lines
        size -= 4
    f = E.F(floor)
    lines = lines[:max_lines]
    if lines:
        last = lines[-1]
        while d.textbbox((0, 0), last + "…", font=f)[2] > max_w and len(last) > 1:
            last = last[:-1]
        lines[-1] = last + "…"
    return f, lines


def _wrap_body(d, text, max_w, font, max_lines=3):
    """Sol hizalı çok satırlı metin — kelime ortasında kesmez, taşan kısmı '…' ile bitirir."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if d.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    if len(lines) <= max_lines:
        return lines

    lines = lines[:max_lines]
    last = lines[-1]
    while d.textbbox((0, 0), last + "…", font=font)[2] > max_w and " " in last:
        last = last.rsplit(" ", 1)[0]
    lines[-1] = last + "…"
    return lines


def _draw_centered_lines(d, img, cx, y, lines, font, fill, line_gap=6, shadow=(0, 0, 0, 160)):
    for line in lines:
        w = d.textbbox((0, 0), line, font=font)[2]
        d.text((cx - w // 2 + 4, y + 4), line, font=font, fill=shadow)
        d.text((cx - w // 2, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def _bottom_gradient(w, h, fade_h, color=(0, 0, 0)):
    grad = Image.new("L", (1, fade_h), 0)
    for y in range(fade_h):
        grad.putpixel((0, y), int(255 * (y / fade_h) ** 1.4))
    grad = grad.resize((w, fade_h))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    solid = Image.new("RGBA", (w, fade_h), color + (0,))
    solid.putalpha(grad)
    layer.alpha_composite(solid, (0, h - fade_h))
    return layer


def render_post(photo_path=None, category="son_dakika", headline="", subheadline="", caption="", source="",
                 out_name="post.jpg"):
    cat = C.CATEGORIES[category]
    W, H = C.POST_WIDTH, C.POST_HEIGHT

    photo_path = photo_path or cat["default_bg"]
    img = _load_photo(photo_path, W, H).convert("RGBA")
    img.alpha_composite(_bottom_gradient(W, H, int(H * 0.62)))

    d = ImageDraw.Draw(img)

    # ---- kategori şeridi (üst sol, sabit konum) ----
    badge_pad_x, badge_pad_y = 28, 14
    bf = E.F(34)
    bw = d.textbbox((0, 0), cat["label"], font=bf)[2]
    bx0, by0 = 40, 40
    d.rounded_rectangle(
        (bx0, by0, bx0 + bw + 2 * badge_pad_x, by0 + bf.size + 2 * badge_pad_y),
        radius=10, fill=cat["bg"],
    )
    d.text((bx0 + badge_pad_x, by0 + badge_pad_y - 2), cat["label"], font=bf, fill=cat["badge_fg"])

    # ---- kanal logosu (üst sağ, sabit konum/boyut — kurumsal kimlik) ----
    logo_sz = 84
    if os.path.exists(C.CHANNEL_LOGO):
        logo = Image.open(C.CHANNEL_LOGO).convert("RGBA").resize((logo_sz, logo_sz), Image.LANCZOS)
        img.alpha_composite(logo, (W - logo_sz - 40, 40))

    # ---- başlık (alt blok, foto üstünde, en fazla 2 satır — kenardan taşmaz) ----
    max_w = W - 90
    cx = W // 2
    headline_font, headline_lines = _wrap_lines(d, headline, max_w, 88, floor=40, max_lines=2)
    hy = H - (340 if len(headline_lines) > 1 else 300)
    cap_y = _draw_centered_lines(d, img, cx, hy, headline_lines, headline_font, C.HEADLINE_FG)
    cap_y += 6

    if subheadline:
        sub_font, sub_lines = _wrap_lines(d, subheadline, max_w, 76, floor=34, max_lines=1)
        cap_y = _draw_centered_lines(d, img, cx, cap_y, sub_lines, sub_font, cat["accent"])
        cap_y += 18
    else:
        cap_y += 18

    # ---- açıklama satırı (kelime ortasında kesilmez, taşarsa '…' ile biter) ----
    if caption:
        cf = E.F(28)
        lines = _wrap_body(d, caption, max_w, cf, max_lines=3)
        for i, line in enumerate(lines):
            d.text((45, cap_y + i * (cf.size + 8)), line, font=cf, fill=(235, 235, 235))
        cap_y += len(lines) * (cf.size + 8)

    # ---- kaynak + kanal handle (alt şerit, sabit konum — kurumsal imza) ----
    foot_y = H - 56
    foot_font = E.F(24)
    left = f"{source}" if source else ""
    d.text((45, foot_y), left, font=foot_font, fill=(190, 190, 190))
    handle_w = d.textbbox((0, 0), C.CHANNEL_HANDLE, font=foot_font)[2]
    d.text((W - handle_w - 45, foot_y), C.CHANNEL_HANDLE, font=foot_font, fill=(255, 255, 255))

    os.makedirs(C.OUT_DIR, exist_ok=True)
    out_path = os.path.join(C.OUT_DIR, out_name)
    img.convert("RGB").save(out_path, quality=94)
    return out_path


if __name__ == "__main__":
    # Hızlı görsel test (assets/ ve gerçek foto olmadan da çalışır, düz renkli arka planla).
    test_bg = os.path.join(C.OUT_DIR, "_test_bg.jpg")
    os.makedirs(C.OUT_DIR, exist_ok=True)
    Image.new("RGB", (C.POST_WIDTH, C.POST_HEIGHT), (40, 40, 60)).save(test_bg)
    out = render_post(
        photo_path=test_bg,
        category="olumsuz",
        headline="SİNGO ŞOKU!",
        subheadline="3 AY YOK!",
        caption="Fildişi Sahili'nin Almanya ile oynadığı maçta sakatlanan Wilfried Singo'nun 3 ay sahalardan uzak kalması bekleniyor.",
        source="Milliyet",
        out_name="test_post.jpg",
    )
    print("OK ->", out)
