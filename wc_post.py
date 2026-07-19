# -*- coding: utf-8 -*-
"""Dünya Kupası özel otomasyon — günde 10 post, 30 dakikada bir."""
import datetime, os, time, html, re
import requests, feedparser
from email.utils import parsedate_to_datetime
import config as C
from post_template import render_post
from telegram_post import send_photo

WC_LOG = os.path.join(C.BASE, "out", "_wc_post_log.csv")
WC_SEEN = os.path.join(C.BASE, "out", "_wc_seen_links.txt")
DAILY_CAP = 10

# WC'ye özel RSS kaynakları
WC_RSS_SOURCES = [
    ("https://www.aspor.com.tr/rss/dunya-kupasi.xml", "A Spor"),
    ("https://www.aspor.com.tr/rss/milli-takim.xml", "A Spor"),
    ("https://www.fotomac.com.tr/rss/dunya-kupasi.xml", "Fotomaç"),
    ("https://www.hurriyet.com.tr/rss/spor", "Hürriyet"),
    ("https://www.haberturk.com/rss/spor.xml", "Haberturk"),
]

_WC_KEYWORDS = [
    "dünya kupası", "world cup", "fifa", "milli takım", "a milli",
    "grup maçı", "2026 dünya", "dünya kupası 2026", "yarı final",
    "çeyrek final", "son 16", "fransa", "ispanya", "arjantin", "brezilya",
    "almanya", "portekiz", "ingiltere", "hollanda",
]

_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _extract_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    if "links" in entry:
        for lnk in entry.links:
            if lnk.get("type", "").startswith("image"):
                return lnk.get("href")
    summary = entry.get("summary", "") or ""
    m = _IMG_RE.search(summary)
    if m:
        return html.unescape(m.group(1))
    return None


def _clean(raw):
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = html.unescape(text).strip()
    sentences = [s for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return " ".join(sentences[:3])[:220]


def _today_count():
    if not os.path.exists(WC_LOG):
        return 0
    today = datetime.date.today().isoformat()
    with open(WC_LOG, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip().startswith(today))


def _load_seen():
    if not os.path.exists(WC_SEEN):
        return set()
    with open(WC_SEEN, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def _mark_seen(link):
    os.makedirs(os.path.dirname(WC_SEEN), exist_ok=True)
    with open(WC_SEEN, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def _log():
    os.makedirs(os.path.dirname(WC_LOG), exist_ok=True)
    with open(WC_LOG, "a", encoding="utf-8") as f:
        f.write(datetime.datetime.now().isoformat() + "\n")


def _parse_pub(entry):
    for field in ("published", "updated"):
        val = entry.get(field, "")
        if not val:
            continue
        try:
            return parsedate_to_datetime(val).replace(tzinfo=None)
        except Exception:
            pass
    return None


def fetch_wc_news(max_age_hours=48):
    seen = _load_seen()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=max_age_hours)
    items = []
    for url, source_name in WC_RSS_SOURCES:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            feed = feedparser.parse(r.content)
        except Exception:
            continue
        for entry in feed.entries:
            link = entry.get("link")
            if not link or link in seen:
                continue
            pub = _parse_pub(entry)
            if pub and pub < cutoff:
                continue
            title = entry.get("title", "").strip()
            summary = _clean(entry.get("summary", "") or "")
            image = _extract_image(entry)
            if not title or not image:
                continue
            text = f"{title} {summary}".lower()
            if not any(kw in text for kw in _WC_KEYWORDS):
                continue
            items.append({
                "title": title, "link": link, "summary": summary,
                "image": image, "source": source_name,
            })
    return items


def run():
    if _today_count() >= DAILY_CAP:
        print("Dünya Kupası günlük 10 post hedefi tamamlandı.")
        return

    items = fetch_wc_news()
    if not items:
        print("Yeni Dünya Kupası haberi bulunamadı.")
        return

    item = items[0]
    _mark_seen(item["link"])

    out_path = render_post(
        photo_path=item["image"],
        category="son_dakika",
        headline=item["title"].upper(),
        subheadline="",
        caption=item["summary"],
        source=item["source"],
        out_name=f"wc_{int(time.time())}.jpg",
    )

    caption = ""
    if item.get("source"):
        caption += f"Kaynak: {item['source']}\n"
    if item.get("link"):
        caption += f'<a href="{item["link"]}">Haberin devamı</a>\n'
    caption += C.CHANNEL_HANDLE

    send_photo(out_path, caption=caption)
    _log()
    print(f"[WC PAYLAŞILDI] {item['title']}")


if __name__ == "__main__":
    run()
