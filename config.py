# -*- coding: utf-8 -*-
"""TEK DÜZENLEME NOKTASI — markanı, renklerini, yollarını buradan ayarla.
Çapraz platform (macOS / Windows / Linux). Yol yazma; her şey bu klasöre göreceli."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
def _p(*a): return os.path.join(BASE, *a)

# ---- ÇIKTI ----
OUT_DIR = _p("out")

# ---- VARLIKLAR (assets/ içine kendi dosyalarını koy) ----
# Kalın başlık fontu (.ttf/.otf). assets/fonts/ içine at, adını buraya yaz.
FONT_BOLD = _p("assets", "fonts", "display.ttf")
# Logo (PNG, tercihen şeffaf). assets/logo.png
LOGO = _p("assets", "logo.png")
# Müzik (.wav). assets/music/track.wav
MUSIC = _p("assets", "music", "track.wav")
# Bayraklar (opsiyonel): assets/flags/<iso>.png  (ör. tr.png)
FLAGS_DIR = _p("assets", "flags")

# ---- MARKA RENKLERİ (RGB) ----
BG_TOP    = (8, 18, 14)      # arka plan üst
BG_BOT    = (16, 32, 25)     # arka plan alt
PRIMARY   = (27, 229, 125)   # ana vurgu
ACCENT    = (212, 255, 63)   # ikincil vurgu
GOLD      = (236, 193, 90)
FG        = (234, 246, 239)  # metin
RING_COLORS = [PRIMARY, ACCENT, GOLD, (52, 211, 153), (125, 255, 176), (255, 140, 90)]

# ---- METİNLER ----
BRAND_NAME   = "MARKAN"           # üst başlıkta görünür
FOOTER_LINE1 = "ALT YAZI · BURAYI DEĞİŞTİR"
FOOTER_LINE2 = "siteniz.com"

# ---- VIDEO ----
WIDTH, HEIGHT, FPS = 1080, 1920, 30   # dikey Shorts
DURATION = 35.5                        # saniye

# ---- SPOR'UN KALBİ — TELEGRAM KANAL KİMLİĞİ ----
CHANNEL_NAME     = "SPOR'UN KALBİ"
CHANNEL_HANDLE   = "@sporkalp"            # her postta sabit watermark
CHANNEL_LOGO     = _p("assets", "channel_logo.png")  # 512x512 şeffaf PNG koy

POST_WIDTH, POST_HEIGHT = 1080, 1350      # Telegram'da kırpılmadan iyi görünen oran (4:5)

# Haber tipine göre sabit kategori paleti — her gönderi bu tablodan birini kullanır,
# stil rastgele değişmez (kurumsal tutarlılık).
# "bg"/"badge_fg" rozetin (kategori etiketinin) rengi — fotoğraf üstündeki başlık metni
# DAİMA HEADLINE_FG (beyaz) olur, kontrast için değişmez. "accent" alt başlık vurgu rengidir,
# her zaman koyu foto üzerinde net görünecek canlı bir renk olmalı.
HEADLINE_FG = (255, 255, 255)

CATEGORIES = {
    "son_dakika":      {"label": "SON DAKİKA",            "bg": (225, 6, 0),   "badge_fg": (255, 255, 255), "accent": (255, 199, 0), "default_bg": _p("assets", "templates", "son_dakika.jpg")},
    "transfer":        {"label": "TRANSFER",               "bg": (11, 61, 145), "badge_fg": (255, 255, 255), "accent": (212, 175, 55), "default_bg": _p("assets", "templates", "transfer.jpg")},
    "skor":            {"label": "MAÇ SONUCU",             "bg": (27, 138, 61), "badge_fg": (255, 255, 255), "accent": (255, 255, 255), "default_bg": _p("assets", "templates", "skor.jpg")},
    "gunun_programi":  {"label": "GÜNÜN KARŞILAŞMALARI",   "bg": (88, 28, 168), "badge_fg": (255, 255, 255), "accent": (255, 255, 255), "default_bg": _p("assets", "templates", "gunun_programi.jpg")},
    "olumsuz":         {"label": "SAKATLIK",               "bg": (26, 26, 26), "badge_fg": (255, 255, 255), "accent": (225, 6, 0), "default_bg": _p("assets", "templates", "olumsuz.jpg")},
    "canli":           {"label": "CANLI",                  "bg": (255, 199, 0), "badge_fg": (26, 26, 26), "accent": (255, 199, 0), "default_bg": _p("assets", "templates", "canli.jpg")},
    "gundem":          {"label": "SPOR GÜNDEMİ",            "bg": (0, 121, 140), "badge_fg": (255, 255, 255), "accent": (255, 199, 0), "default_bg": _p("assets", "templates", "skor.jpg")},
}

POST_FONT_BOLD = _p("assets", "fonts", "display.ttf")   # kalın başlık fontu — assets/fonts/ içine koy
POST_FONT_REGULAR = _p("assets", "fonts", "regular.ttf")

# ---- HABER KAYNAKLARI (RSS) ----
# (url, kaynak_adi) — her döngüde HTTP durumu kontrol edilir, çöken kaynak otomatik atlanır.
RSS_SOURCES = [
    # Kulüp özelinde
    ("https://www.aspor.com.tr/rss/galatasaray.xml", "A Spor"),
    ("https://www.aspor.com.tr/rss/fenerbahce.xml", "A Spor"),
    ("https://www.aspor.com.tr/rss/besiktas.xml", "A Spor"),
    ("https://www.aspor.com.tr/rss/trabzonspor.xml", "A Spor"),
    # Süper Lig & Avrupa
    ("https://www.fotomac.com.tr/rss/superlig.xml", "Fotomaç"),
    ("https://www.fotomac.com.tr/rss/avrupadanfutbol.xml", "Fotomaç"),
    # Genel spor
    ("https://www.sozcu.com.tr/feeds-rss-category-spor", "Sözcü"),
    # ("https://www.cumhuriyet.com.tr/rss/11", "Cumhuriyet"),  # spor dışı haberler de geliyor
    ("https://www.aa.com.tr/tr/rss/default?cat=spor", "Anadolu Ajansı"),
    # Ek çeşitli kaynaklar
    ("https://www.hurriyet.com.tr/rss/spor", "Hürriyet"),
    ("https://www.sabah.com.tr/rss/spor.xml", "Sabah"),
    ("https://www.haberturk.com/rss/spor.xml", "Haberturk"),
    ("https://www.takvim.com.tr/rss/spor.xml", "Takvim"),
    ("https://www.posta.com.tr/rss/spor.xml", "Posta"),
    # Dünya Kupası & milli takım
    ("https://www.aspor.com.tr/rss/milli-takim.xml", "A Spor"),
    ("https://www.aspor.com.tr/rss/dunya-kupasi.xml", "A Spor"),
    ("https://www.fotomac.com.tr/rss/dunya-kupasi.xml", "Fotomaç"),
]

SEEN_LOG = _p("out", "_seen_links.txt")   # aynı haberin tekrar paylaşılmaması için

# ---- YOUTUBE (opsiyonel) ----
CLIENT_SECRET = _p("client_secret.json")   # kendi Google Cloud OAuth dosyan
TOKEN         = _p("token.json")           # ilk girişte otomatik oluşur
CATEGORY_ID   = "17"                        # 17 = Spor; 24 = Eğlence vb.
