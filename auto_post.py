# -*- coding: utf-8 -*-
"""Spor'un Kalbi — uçtan uca otomasyon: RSS'den haber çek, kurumsal şablonla görsel üret,
Telegram kanalına gönder. Zamanlanmış görev (cron) bu scripti günde N kez çalıştırır.

Kullanım:
    python auto_post.py            # otomatik telafi modu: günlük 15 hedefine göre eksik varsa tamamlar
    python auto_post.py --count 3  # telafi mantığını atla, sabit 3 haber paylaş
    python auto_post.py --dry-run  # görseli üretir, Telegram'a ATMAZ (out/ klasörüne kaydeder)

Telafi mantığı (Mac kapalıyken atlanan saatleri kapatır):
    Gün 08:00-22:00 arası 15 eşit zaman dilimine bölünür. Mac kapalıyken kaçırılan
    saatler birikir; bilgisayar tekrar açılıp cron çalıştığında, o günün o ana kadar
    "olması gereken" post sayısına ulaşılana dek eksik haberler tek seferde (en fazla
    CATCH_UP_CAP kadar) art arda paylaşılır. Ertesi gün hedef sıfırdan başlar, önceki
    günün açığı taşınmaz (spam'i önlemek için).
"""
import argparse
import datetime
import os
import sys
import time

import config as C
from news_fetch import fetch_news
from post_template import render_post
from telegram_post import send_photo as tg_send_photo
try:
    from instagram_post import send_photo as ig_send_photo
    _IG_ENABLED = True
except Exception:
    _IG_ENABLED = False

POST_LOG = os.path.join(C.BASE, "out", "_post_log.csv")
DAILY_START_HOUR = 8
DAILY_END_HOUR = 22       # dahil — 8..22 = 15 saat dilimi
DAILY_TARGET = DAILY_END_HOUR - DAILY_START_HOUR + 1
CATCH_UP_CAP = 6           # tek çalıştırmada en fazla bu kadar telafi postu at (spam'i önler)


def _log_post():
    os.makedirs(os.path.dirname(POST_LOG), exist_ok=True)
    with open(POST_LOG, "a", encoding="utf-8") as f:
        f.write(datetime.datetime.now().isoformat() + "\n")


def _today_post_count():
    if not os.path.exists(POST_LOG):
        return 0
    today = datetime.date.today().isoformat()
    with open(POST_LOG, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip().startswith(today))


def _catch_up_count():
    now = datetime.datetime.now()
    if now.hour < DAILY_START_HOUR or now.hour > DAILY_END_HOUR:
        return 0
    expected_so_far = now.hour - DAILY_START_HOUR + 1   # bu saat dahil, o ana kadar olması gereken post sayısı
    expected_so_far = min(expected_so_far, DAILY_TARGET)
    already = _today_post_count()
    deficit = max(0, expected_so_far - already)
    return min(deficit, CATCH_UP_CAP) if deficit > 0 else (0 if already >= DAILY_TARGET else 1)


def build_caption(item):
    # Görselde başlık + özet zaten yazılı — mesaj metninde tekrar etmiyoruz.
    # Sadece kaynak, habere giden link ve kanal imzası.
    parts = []
    if item.get("source"):
        parts.append(f"Kaynak: {item['source']}")
    if item.get("link"):
        parts.append(f'<a href="{item["link"]}">Haberin devamı</a>')
    parts.append(C.CHANNEL_HANDLE)
    return "\n".join(parts)


def run(count, dry_run):
    items = fetch_news(limit=count, mark_as_seen=not dry_run)
    if not items:
        print("Yeni haber bulunamadı (hepsi daha önce paylaşılmış olabilir).")
        return

    for idx, item in enumerate(items):
        try:
            out_path = render_post(
                photo_path=item["image"],
                category=item["category"],
                headline=item["title"].upper(),
                subheadline="",
                caption=item["summary"],
                source=item["source"],
                out_name=f"auto_{int(time.time())}_{idx}.jpg",
            )
        except Exception as e:
            print(f"[ATLANDI] görsel üretilemedi: {item['title']} -> {e}")
            continue

        if dry_run:
            print(f"[DRY-RUN] {out_path}  <- {item['title']}")
            continue

        try:
            tg_send_photo(out_path, caption=build_caption(item))
            _log_post()
            print(f"[PAYLAŞILDI] {item['title']}")
            time.sleep(4)   # Telegram rate limit (30 msg/s kanal limiti)
        except Exception as e:
            print(f"[HATA] Telegram'a gönderilemedi: {item['title']} -> {e}")

        if _IG_ENABLED:
            try:
                ig_caption = f"{item['title']}\n\n{item.get('summary','')}\n\n#sporkalp #spor #futbol #superlig #transfer"
                ig_send_photo(out_path, caption=ig_caption)
                print(f"[IG PAYLAŞILDI] {item['title']}")
                time.sleep(10)  # Instagram rate limit
            except Exception as e:
                print(f"[IG HATA] {item['title']} -> {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=None,
                    help="Sabit sayıda haber paylaş (verilmezse otomatik telafi mantığı kullanılır)")
    p.add_argument("--dry-run", action="store_true", help="Telegram'a atmadan sadece görsel üret")
    args = p.parse_args()
    count = args.count if args.count is not None else _catch_up_count()
    if count == 0:
        print("Bugünün 15 hedefi zaten tamamlanmış veya saat penceresi (08-22) dışında — atlanıyor.")
    else:
        run(count, args.dry_run)
