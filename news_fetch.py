# -*- coding: utf-8 -*-
"""Spor'un Kalbi — RSS'den haber çekme, kategori sınıflandırma, tekrar engelleme.

Kullanım:
    from news_fetch import fetch_news
    items = fetch_news(limit=15)
    # her item: {"title","link","summary","image","source","category","pub_date"}
"""
import os
import re
import html
import datetime
import feedparser
import requests
from email.utils import parsedate_to_datetime
import config as C

_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

# Kategori anahtar kelimeleri — başlık/özet içinde aranır, sırayla ilk eşleşen kazanır.
_KEYWORDS = [
    ("son_dakika", ["son dakika"]),
    ("olumsuz", ["sakat", "kırmızı kart", "men cezası", "ceza aldı", "ameliyat", "ceza verildi"]),
    ("transfer", ["transfer", "imza attı", "imzaladı", "anlaştı", "kiralık", "bonservis", "kanca"]),
    ("skor", ["kazandı", "mağlup", "berabere", "yenildi", "yendi", "galibiyet", "maç sonucu"]),
]


def _classify(title, summary):
    text = f"{title} {summary}".lower()
    for cat, words in _KEYWORDS:
        if any(w in text for w in words):
            return cat
    return "gundem"


def _is_valid_image_url(url):
    if not url or not url.startswith("http"):
        return False
    # Posta gibi bozuk URL birleşimi varsa reddet
    if url.count("http") > 1 or url.count(".jpg") > 1:
        return False
    return True


def _extract_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    if "links" in entry:
        for link in entry.links:
            if link.get("type", "").startswith("image"):
                return link.get("href")
    summary = entry.get("summary", "") or entry.get("description", "")
    m = _IMG_RE.search(summary)
    if m:
        return html.unescape(m.group(1))
    if "image" in entry:
        img = entry.image
        return img.get("href") if isinstance(img, dict) else str(img)
    return None


_CTA_PATTERNS = [
    r"devamı\s*için\s*tıklayınız\.?",
    r"devamını\s*oku(yun)?\.?",
    r"haberin\s*devamı.*",
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_TRUNC_MARK = re.compile(r"\.\.\.|…")


def _drop_truncated_tail(text):
    """Yayıncı kaynağın '...' ile kestiği yarım cümleyi tamamen at, son tam cümleye kadar tut."""
    m = _TRUNC_MARK.search(text)
    if not m:
        return text
    head = text[:m.start()]
    enders = list(re.finditer(r"[.!?]", head))
    return head[:enders[-1].end()] if enders else ""


def _limit_sentences(text, max_sentences=3, max_chars=220):
    sentences = [s for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    out, total = [], 0
    for s in sentences:
        if len(out) >= max_sentences or total + len(s) > max_chars:
            break
        out.append(s)
        total += len(s)
    return " ".join(out).strip()


def _clean_summary(raw):
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = html.unescape(text).strip()
    for pat in _CTA_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
    text = _drop_truncated_tail(text)
    return _limit_sentences(text, max_sentences=3, max_chars=220)


def _load_seen():
    if not os.path.exists(C.SEEN_LOG):
        return set()
    with open(C.SEEN_LOG, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def _mark_seen(links):
    os.makedirs(os.path.dirname(C.SEEN_LOG), exist_ok=True)
    with open(C.SEEN_LOG, "a", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")


def _parse_pub_date(entry):
    for field in ("published", "updated"):
        val = entry.get(field, "")
        if not val:
            continue
        try:
            return parsedate_to_datetime(val).replace(tzinfo=None)
        except Exception:
            pass
    return None


def fetch_news(limit=15, mark_as_seen=True, max_age_hours=48):
    seen = _load_seen()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=max_age_hours)

    # Her kaynaktan en fazla 3 haber al — çeşitliliği zorla
    per_source = max(3, limit // max(len(C.RSS_SOURCES), 1))
    buckets = []

    for url, source_name in C.RSS_SOURCES:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            feed = feedparser.parse(r.content)
        except Exception:
            continue
        count = 0
        for entry in feed.entries:
            if count >= per_source:
                break
            link = entry.get("link")
            if not link or link in seen:
                continue
            pub = _parse_pub_date(entry)
            if pub and pub < cutoff:
                continue
            title = entry.get("title", "").strip()
            summary = _clean_summary(entry.get("summary", "") or entry.get("description", ""))
            image = _extract_image(entry)
            if not title or not image or not _is_valid_image_url(image):
                continue
            buckets.append({
                "title": title,
                "link": link,
                "summary": summary,
                "image": image,
                "source": source_name,
                "category": _classify(title, summary),
                "pub_date": entry.get("published", ""),
            })
            count += 1

    # Kaynak sırasına göre round-robin karıştır
    import random
    random.shuffle(buckets)
    collected = buckets[:limit]
    if mark_as_seen:
        _mark_seen([item["link"] for item in collected])
    return collected


if __name__ == "__main__":
    for item in fetch_news(limit=15, mark_as_seen=False):
        print(f"[{item['category']:12}] {item['source']:15} {item['title']}")
        print(f"             img: {item['image']}")
