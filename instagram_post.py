# -*- coding: utf-8 -*-
"""Spor'un Kalbi — Instagram otomasyon modülü.
Aynı Pillow görselini Instagram'a post atar.
"""
import os
import time
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

_ENV = os.path.join(os.path.dirname(__file__), ".env")
_SESSION = os.path.join(os.path.dirname(__file__), "out", "ig_session.json")


def _load_env():
    env = {}
    with open(_ENV, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _get_client():
    """Instagram, her seferinde kullanıcı/şifre ile yeniden giriş yapılmasını
    şüpheli bulur (farklı IP'lerden tekrarlayan login = bot işareti). Bu yüzden
    kayıtlı cihaz/session dosyası varsa SADECE onunla devam edilir; sadece
    session tamamen geçersizse cookie (sessionid) ya da şifre ile giriş denenir."""
    env = _load_env()
    cl = Client()
    cl.delay_range = [2, 5]

    if os.path.exists(_SESSION):
        cl.load_settings(_SESSION)
        try:
            cl.get_timeline_feed()   # session hâlâ geçerli mi? (yeniden login tetiklemez)
            return cl
        except (LoginRequired, Exception):
            cl = Client()
            cl.delay_range = [2, 5]

    if env.get("INSTAGRAM_SESSIONID"):
        try:
            cl.login_by_sessionid(env["INSTAGRAM_SESSIONID"])
            os.makedirs(os.path.dirname(_SESSION), exist_ok=True)
            cl.dump_settings(_SESSION)
            return cl
        except Exception:
            cl = Client()
            cl.delay_range = [2, 5]

    cl.login(env["INSTAGRAM_USERNAME"], env["INSTAGRAM_PASSWORD"])
    os.makedirs(os.path.dirname(_SESSION), exist_ok=True)
    cl.dump_settings(_SESSION)
    return cl


def send_photo(photo_path, caption="", retries=3):
    cl = _get_client()
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            cl.photo_upload(photo_path, caption=caption)
            cl.dump_settings(_SESSION)   # cihaz/oturum durumunu her başarılı postta güncel tut
            print(f"[IG PAYLAŞILDI] {os.path.basename(photo_path)}")
            return
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(5 * attempt)
    raise last_err


if __name__ == "__main__":
    # Bağlantı testi
    cl = _get_client()
    print(f"Giriş başarılı: @{cl.username}")
