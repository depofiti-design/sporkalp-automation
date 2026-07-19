# -*- coding: utf-8 -*-
"""Spor'un Kalbi — Instagram otomasyon modülü.
Aynı Pillow görselini Instagram'a post atar.
"""
import os
import json
from instagrapi import Client

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
    env = _load_env()
    username = env["INSTAGRAM_USERNAME"]
    password = env["INSTAGRAM_PASSWORD"]

    cl = Client()
    cl.delay_range = [2, 5]

    # Kaydedilmiş session varsa önce onu dene
    if os.path.exists(_SESSION):
        try:
            cl.load_settings(_SESSION)
            cl.login(username, password)
            return cl
        except Exception:
            pass

    # Cookie tabanlı giriş (HttpOnly sessionid varsa)
    if "INSTAGRAM_SESSIONID" in env:
        try:
            cl.login_by_sessionid(env["INSTAGRAM_SESSIONID"])
            os.makedirs(os.path.dirname(_SESSION), exist_ok=True)
            cl.dump_settings(_SESSION)
            return cl
        except Exception:
            pass

    # Kullanıcı adı/şifre ile giriş
    cl.login(username, password)
    os.makedirs(os.path.dirname(_SESSION), exist_ok=True)
    cl.dump_settings(_SESSION)
    return cl


def send_photo(photo_path, caption=""):
    cl = _get_client()
    cl.photo_upload(photo_path, caption=caption)
    print(f"[IG PAYLAŞILDI] {os.path.basename(photo_path)}")


if __name__ == "__main__":
    # Bağlantı testi
    cl = _get_client()
    print(f"Giriş başarılı: @{cl.username}")
