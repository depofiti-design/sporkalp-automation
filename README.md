# İçerik Motoru (Content Engine Kit)

Markandan bağımsız, çapraz platform bir içerik üretim motoru. Müzik ritmine **senkron** dikey video (Shorts) ve markalı görseller üretir; isteğe bağlı YouTube'a yükler.

## Hızlı Başlangıç
1. `SETUP_MAC.md`'i izle (veya Windows'ta Python 3.12 + FFmpeg kur).
2. `assets/` içine kendi font/logo/müziğini koy.
3. `config.py`'da markanı ayarla.
4. `python gauge_video.py` → ilk videon `out/` içinde.

## Dosyalar
| Dosya | Görevi |
|-------|--------|
| `config.py` | **Tek ayar noktası** — renkler, yollar, marka, video boyutu |
| `engine.py` | Çizim/animasyon yardımcıları (font, arka plan, metin, daire, beat) |
| `gauge_video.py` | Beat-senkron dairesel-yüzde Shorts videosu (kendi verinle) |
| `youtube_upload.py` | YouTube'a anında/zamanlı yükleme (kendi Google hesabınla) |
| `requirements.txt` | Python paketleri |
| `assets/` | Senin font/logo/müzik/bayrak dosyaların |
| `out/` | Üretilen videolar/görseller |

## Gereksinimler
- Python 3.12, FFmpeg
- Python paketleri: Pillow, numpy, librosa, (YouTube için) google-api-python-client + google-auth-oauthlib

## Notlar
- YouTube kimliği taşınamaz: kendi Google Cloud projeni açıp `client_secret.json` indir.
- Müzik telif: kendi sahip olduğun veya royalty-free müzik kullan.
- Bu paket örnek/iskelet veri ile gelir; içeriği sen oluşturursun.
