# -*- coding: utf-8 -*-
"""Spor'un Kalbi — uçtan uca otomasyon: RSS'den haber çek, kurumsal şablonla görsel üret,
Telegram kanalına gönder. Zamanlanmış görev (cron) bu scripti günde N kez çalıştırır.

Kullanım:
    python auto_post.py            # otomatik tempo modu: günlük 15-20 hedefine göre eksik varsa tamamlar
    python auto_post.py --count 3  # tempo mantığını atla, sabit 3 haber paylaş
    python auto_post.py --dry-run  # görseli üretir, Telegram'a ATMAZ (out/ klasörüne kaydeder)

Tempo mantığı (GitHub Actions'ın tetikleme sıklığı öngörülemez olduğu için):
    Her gün için 15-20 arası rastgele bir hedef seçilir. Her çalıştırmada, kalan hedef
    kalan tahmini çalıştırma sayısına orantılı dağıtılır; gerekiyorsa aynı çalıştırmada
    art arda (rastgele aralıklarla) birden fazla post atılır. Ertesi gün hedef sıfırdan
    seçilir, önceki günün açığı taşınmaz (spam'i önlemek için).
"""
import argparse
import datetime
import os
import random
import sys
import time

import config as C
from news_fetch import fetch_news
from post_template import render_post
from telegram_post import send_photo as tg_send_photo
try:
    from instagram_post import send_photo as ig_send_photo
    # GEÇİCİ OLARAK KAPALI: Instagram hesabı şüpheli giriş denemeleri nedeniyle
    # güvenlik incelemesine takıldı (BadPassword / login_required hataları).
    # Hesap manuel olarak temizlenip taze bir INSTAGRAM_SESSIONID alınana kadar
    # tekrar denemek durumu kötüleştirebilir — bilerek kapatıldı.
    _IG_ENABLED = os.environ.get("IG_POSTING_ENABLED", "0") == "1"
except Exception:
    _IG_ENABLED = False

POST_LOG = os.path.join(C.BASE, "out", "_post_log.csv")
TARGET_FILE = os.path.join(C.BASE, "out", "_daily_target.txt")
TR_OFFSET = datetime.timedelta(hours=3)   # Türkiye UTC+3 (DST yok, 2016'dan beri sabit)
DAILY_START_HOUR = 8
DAILY_END_HOUR = 22        # dahil — 08:00-22:59 penceresi (Türkiye saati)


def _tr_now():
    """GitHub Actions runner'ları UTC çalışır — datetime.now() Türkiye saatiyle
    karıştırılırsa pencere 3 saat kayar. Her yerde bunun yerine bu fonksiyon kullanılmalı."""
    return (datetime.datetime.now(datetime.timezone.utc) + TR_OFFSET).replace(tzinfo=None)
# GitHub Actions'ın schedule cron'u sık sık geciktirdiği için (gözlemlenen: ~20dk yerine
# ortalama ~90-120dk'da bir tetikleniyor), tek bir çalıştırmanın birden fazla post atabilmesi
# gerekiyor — yoksa günlük hedefe asla ulaşılamıyor.
EFFECTIVE_RUN_INTERVAL_MIN = 90
MAX_POSTS_PER_RUN = 4
DAILY_TARGET_RANGE = (15, 20)   # günlük hedef bu aralıkta rastgele seçilir
IG_JITTER_SEC = (30, 300)       # Telegram'dan sonra IG'ye rastgele gecikmeyle post (bot izini kırar)
INTER_POST_GAP_SEC = (60, 240)  # aynı çalıştırmada birden fazla post varsa aralarındaki rastgele bekleme


def _log_post():
    os.makedirs(os.path.dirname(POST_LOG), exist_ok=True)
    with open(POST_LOG, "a", encoding="utf-8") as f:
        f.write(_tr_now().isoformat() + "\n")


def _today_post_count():
    if not os.path.exists(POST_LOG):
        return 0
    today = _tr_now().date().isoformat()
    with open(POST_LOG, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip().startswith(today))


def _daily_target():
    """Her gün için 15-20 arası rastgele bir hedef seçer ve dosyada saklar (gün boyu sabit kalır)."""
    today = _tr_now().date().isoformat()
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            saved = f.read().strip()
        if saved.startswith(today):
            return int(saved.split(",")[1])
    target = random.randint(*DAILY_TARGET_RANGE)
    os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(f"{today},{target}")
    return target


def _pace_decision():
    """Günlük hedefe göre bu çalıştırmada kaç post atılacağına karar verir.
    Zamanlayıcı ne sıklıkla tetiklenirse tetiklensin (GitHub Actions'ın gerçek
    aralığı öngörülemez), kalan hedef kalan tahmini çalıştırma sayısına orantılı
    dağıtılır; birden fazla post gerekiyorsa aynı çalıştırmada art arda (rastgele
    aralıklarla) atılır — böylece hedefe her koşulda ulaşılır."""
    now = _tr_now()
    if now.hour < DAILY_START_HOUR or now.hour > DAILY_END_HOUR:
        return 0

    target = _daily_target()
    already = _today_post_count()
    deficit = target - already
    if deficit <= 0:
        return 0

    end_of_window = now.replace(hour=DAILY_END_HOUR, minute=59, second=59, microsecond=0)
    minutes_left = max(EFFECTIVE_RUN_INTERVAL_MIN, (end_of_window - now).total_seconds() / 60)
    runs_left = max(1.0, minutes_left / EFFECTIVE_RUN_INTERVAL_MIN)

    expected_this_run = deficit / runs_left
    count = round(expected_this_run + random.uniform(-0.4, 0.4))
    if count <= 0 and random.random() < min(1.0, expected_this_run):
        count = 1
    return max(0, min(count, deficit, MAX_POSTS_PER_RUN))


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
        if idx > 0 and not dry_run:
            time.sleep(random.randint(*INTER_POST_GAP_SEC))
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
                jitter = random.randint(*IG_JITTER_SEC)
                time.sleep(jitter)   # Telegram ile aynı anda atmamak için rastgele gecikme (bot izini kırar)
                ig_caption = f"{item['title']}\n\n{item.get('summary','')}\n\n#sporkalp #spor #futbol #superlig #transfer"
                ig_send_photo(out_path, caption=ig_caption)
                print(f"[IG PAYLAŞILDI] {item['title']}")
            except Exception as e:
                print(f"[IG HATA] {item['title']} -> {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=None,
                    help="Sabit sayıda haber paylaş (verilmezse otomatik telafi mantığı kullanılır)")
    p.add_argument("--dry-run", action="store_true", help="Telegram'a atmadan sadece görsel üret")
    args = p.parse_args()
    count = args.count if args.count is not None else _pace_decision()
    if count == 0:
        print("Bu çalıştırmada post atlanıyor (hedef tamamlandı, pencere dışı ya da rastgele atlama).")
    else:
        run(count, args.dry_run)
