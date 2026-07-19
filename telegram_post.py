# -*- coding: utf-8 -*-
"""Spor'un Kalbi — Telegram kanalına gönderi atma.
.env içindeki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHANNEL_ID kullanılır.

Kullanım:
    from telegram_post import send_photo
    send_photo("out/post_001.jpg", caption="Açıklama metni")
"""
import os
import time
import requests

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def _load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


_ENV = _load_env()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or _ENV.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID") or _ENV.get("TELEGRAM_CHANNEL_ID")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_photo(photo_path, caption="", channel_id=None, retries=3):
    if not BOT_TOKEN:
        raise RuntimeError(".env içinde TELEGRAM_BOT_TOKEN bulunamadı.")
    chat_id = channel_id or CHANNEL_ID
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with open(photo_path, "rb") as f:
                r = requests.post(
                    f"{API}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=60,
                )
            r.raise_for_status()
            result = r.json()
            if not result.get("ok"):
                raise RuntimeError(f"Telegram hatası: {result}")
            return result
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_err = e
            if attempt < retries:
                time.sleep(3 * attempt)
    raise last_err


def get_me():
    r = requests.get(f"{API}/getMe", timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print(get_me())
