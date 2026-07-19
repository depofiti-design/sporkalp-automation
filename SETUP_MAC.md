# İçerik Motoru — macOS Kurulum Talimatı (Claude Code için)

> **Bu dosyayı Mac'teki Claude Code'a ver, "bu talimatı uygula" de.**
> Hedef: macOS (Apple Silicon veya Intel). Adımları sırayla uygula, her adımı doğrula; hata olursa dur ve bildir.

Bu paket; markandan bağımsız bir içerik motorudur: Python + Pillow ile dikey görseller, FFmpeg ile **müzik ritmine senkron** dairesel-yüzde Shorts videoları üretir ve isteğe bağlı YouTube'a yükler. Kendi logon/müziğin/verinle çalışır.

---

## 1. Sistem Araçları (Homebrew ile)

Homebrew yoksa önce kur:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Sonra:
```bash
brew install python@3.12 ffmpeg
```
Doğrula:
```bash
python3 --version     # 3.12.x
ffmpeg -version | head -1
ffprobe -version | head -1
```
> YouTube yüklemesi yapılmayacaksa Node.js gerekmez. (Bu paket Node kullanmaz.)

---

## 2. Python Paketleri (sanal ortam önerilir)

```bash
cd <bu-paketin-klasörü>          # içinde config.py olan klasör
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
Doğrula:
```bash
python -c "import PIL, numpy, librosa; print('paketler OK')"
```

---

## 3. Kendi Varlıklarını Ekle (`assets/` klasörü)

| Dosya | Nereye | Zorunlu mu |
|-------|--------|------------|
| Kalın başlık fontu (.ttf) | `assets/fonts/display.ttf` | Önerilir (yoksa sistem fontuna düşer) |
| Logo (PNG, şeffaf) | `assets/logo.png` | Opsiyonel (yoksa sadece yazı) |
| Müzik (.wav) | `assets/music/track.wav` | **Video için zorunlu** |
| Bayraklar (opsiyonel) | `assets/flags/<iso>.png` | Sadece bayrak kullanırsan |

> Müzik elinde mp3/m4a ise wav'a çevir:
> ```bash
> ffmpeg -i girdi.mp3 -ar 44100 -ac 2 assets/music/track.wav
> ```
> Kısa müziği videoya uzatmak için döngüle:
> ```bash
> ffmpeg -stream_loop -1 -i girdi.mp3 -t 37 -af loudnorm assets/music/track.wav
> ```

---

## 4. Markanı Ayarla — `config.py`

`config.py` dosyasını aç, şunları kendine göre değiştir:
- `BRAND_NAME`, `FOOTER_LINE1`, `FOOTER_LINE2`
- Renkler: `PRIMARY`, `ACCENT`, `GOLD`, `BG_TOP/BG_BOT`, `FG`
- Gerekirse `WIDTH/HEIGHT` (varsayılan 1080×1920 dikey)

---

## 5. İlk Video (test)

```bash
source venv/bin/activate
python gauge_video.py
```
`out/gauge_video.mp4` oluşmalı (35.5 sn, müzikle, ritme senkron). Oluştuysa **motor çalışıyor.**

Kendi verinle:
```python
# kendi_uret.py
from gauge_video import render
render(
    data=[("Ürün A", None, 78), ("Ürün B", None, 61), ("Ürün C", None, 45)],
    title="EN ÇOK SATANLAR",
    out_name="haftalik.mp4",
)
```
```bash
python kendi_uret.py
```

---

## 6. (Opsiyonel) YouTube Yükleme

1. https://console.cloud.google.com → proje aç → **YouTube Data API v3** etkinleştir
2. OAuth consent screen (External) → kendi Gmail'ini "Test users"a ekle
3. Credentials → OAuth client ID → **Desktop app** → JSON indir → `client_secret.json` olarak bu klasöre koy
4. İlk giriş ve test:
```bash
python youtube_upload.py connect
python youtube_upload.py out/gauge_video.mp4 "Başlığım" "Açıklama metni"
# Zamanlı (UTC): 
python youtube_upload.py out/video.mp4 "Başlık" "Açıklama" 2026-07-01T18:00:00Z
```
> Kota: ~6 yükleme/gün.

---

## Sorun Giderme
- **Font görünmüyor / kutu çıkıyor** → `assets/fonts/display.ttf` ekle (Türkçe karakter destekleyen kalın bir .ttf).
- **FFmpeg yok** → `brew install ffmpeg`.
- **Müzik yok hatası** → `assets/music/track.wav` ekledin mi? `config.MUSIC` doğru mu?
- **librosa/numba kurulum hatası (Apple Silicon)** → `pip install --upgrade pip` sonra tekrar; gerekiyorsa `brew install llvm`.
- **OAuth access_denied** → consent screen'de kendi Gmail'ini test kullanıcısı yaptın mı?

## Kapanış Kontrol
- [ ] `python3`, `ffmpeg` çalışıyor
- [ ] `pip install -r requirements.txt` tamam
- [ ] `assets/music/track.wav` ve (varsa) `assets/fonts/display.ttf` yerinde
- [ ] `python gauge_video.py` → `out/gauge_video.mp4` oluştu
