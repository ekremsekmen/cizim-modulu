# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN HESAPLAMA PROGRAMI
=================================
Yerel sunucu + tarayıcı arayüzü.  Çalıştırmak için:

    python3 main.py

Tarayıcı kendiliğinden açılır (http://127.0.0.1:8780).
Program tümüyle bilgisayarınızda çalışır, internet gerektirmez.
"""

import json
import hashlib
import logging
import os
import re
import sys
import threading
import webbrowser

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yollar

yollar.kur()

#  CAD çıktısı ezdxf + pdfminer.six ister.  Bunlar kurulu değilse PROGRAM
#  YİNE AÇILIR — yalnız CAD düğmeleri anlaşılır bir hata verir.
#  ( Kitaplık denetimi artık uç dosyalarında:  uclar/avan_uclari.py · uclar/uygulama_uclari.py )
_BASLATICI = "baslat.bat" if os.name == "nt" else "baslat.command"

SURUM = "3.0"
KOK = os.path.dirname(os.path.abspath(__file__))
#  8780:  hesap programının kendisi 8760'ta açık olabilir;  bu program onun
#  çizimli kopyasıdır, aynı porta düşüp ötekinin penceresine yönlenmesin.
PORT = int(os.environ.get("AVAN_PORT", "8780"))

#  KAYIT:  uçların beklenmeyen hataları izleriyle ( uclar/uc_ortak.hata_kaydi ),
#  çizimin yedek değere düştüğü yerler ayrıntı düzeyinde.  Düzey ortamdan:
#  AVAN_KAYIT=DEBUG | INFO | WARNING ( varsayılan ) | ERROR.
logging.basicConfig(
    level=os.environ.get("AVAN_KAYIT", "WARNING").upper(),
    format="%(asctime)s  %(levelname)-7s  %(name)s:  %(message)s",
)

app = FastAPI(title="Asansör Proje Programı", version=SURUM, docs_url=None, redoc_url=None)


# ------------------------------------------------------------------ yardımcı
#  BELİRSİZ SAYI  —  "1.200" bin iki yüz mü, bir nokta iki mi?
#  Program ondalık ayracı olarak hem virgülü hem noktayı kabul ediyor; bu da
#  TEK ayraçlı ve ardından TAM ÜÇ RAKAM gelen yazımları belirsiz bırakır:
#  Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki.  Program bunu
#  tahmin ETMEZ — reddeder ve kullanıcıya nasıl yazması gerektiğini söyler.
#  Sessizce 1,2 okumak 1.200 daireli bir binada asansör adedini 41'den 2'ye
#  düşürüyordu.
#  Tam sayı kısmı SIFIRLA BAŞLAMAMALI: "0,075" ( = %7,5 ) belirsiz değildir,
#  çünkü binlik ayracı sıfırdan sonra gelmez.  Belirsiz olan "1.200" gibi
#  1-3 basamaklı, sıfırla başlamayan bir sayıdan sonra tam üç rakam gelmesidir.
BELIRSIZ_SAYI = re.compile(r"^[+-]?[1-9]\d{0,2}[.,]\d{3}$")


from uclar import avan_uclari
from uclar import cizim_uclari
from uclar import uygulama_uclari
from uclar.uc_ortak import _BELIRSIZ, _RED, _sayi, belirsiz_sayi_mi  # noqa: F401

#  UÇLAR İKİ PAKETTE:  avan projesi ve uygulama projesi ayrı dosyalarda
#  ( bkz. uclar/avan_uclari.py · uclar/uygulama_uclari.py ).  Ortak yardımcılar uclar/uc_ortak.py.
app.include_router(avan_uclari.router)
app.include_router(uygulama_uclari.router)
app.include_router(cizim_uclari.router)


@app.get("/", response_class=HTMLResponse)
def anasayfa():
    with open(os.path.join(KOK, "static", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read().replace("?v=SURUM", "?v=" + _statik_damga()))


def _statik_damga():
    """Betik ve biçem dosyalarının içeriğinden türetilen önbellek damgası.

    Elle yazılan bir sürüm etiketi ( "?v=3.0" ) unutulabiliyordu:  JS
    değiştiğinde etiket aynı kaldığı için tarayıcı ESKİ betiği önbellekten
    çalıştırıyor, YENİ index.html ile birleşince ekran sessizce bozuluyordu.
    İçerikten türetilen damga unutulamaz — dosya değişince damga da değişir.
    """
    h = hashlib.sha1()
    for ad in ("ortak.js", "avan.js", "uygulama.js", "style.css"):
        try:
            with open(os.path.join(KOK, "static", ad), "rb") as f:
                h.update(f.read())
        except OSError:
            h.update(ad.encode())
    return h.hexdigest()[:12]


@app.get("/api/saglik")
def saglik():
    return {"durum": "calisiyor", "surum": SURUM}


app.mount("/static", StaticFiles(directory=os.path.join(KOK, "static")), name="static")


# ------------------------------------------------------------------ başlat
def _bos_port(ilk, deneme=20):
    """İlk boş portu bulur — program zaten açıksa ikinci kopya çakışmasın."""
    import socket

    for p in range(ilk, ilk + deneme):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return None


def _zaten_calisiyor(port):
    """Bu portta bizim programımız mı çalışıyor?"""
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/saglik", timeout=2) as c:
            return json.loads(c.read()).get("durum") == "calisiyor"
    except Exception:  # noqa: BLE001
        return False


def calistir():
    import uvicorn

    port = PORT
    if _zaten_calisiyor(port):
        url = f"http://127.0.0.1:{port}"
        print(f"\n  Program zaten açık  →  {url}\n  Tarayıcı yönlendiriliyor…\n")
        webbrowser.open(url)
        return
    if _bos_port(port, 1) is None:
        yeni = _bos_port(port + 1)
        if yeni is None:
            print(
                f"\n  {port} ve sonraki portlar dolu. Başka bir program bu portları "
                "kullanıyor olabilir.\n  Bilgisayarı yeniden başlatıp tekrar deneyin.\n"
            )
            return
        print(f"\n  {port} portu başka bir program tarafından kullanılıyor — {yeni} portuna geçildi.")
        port = yeni

    url = f"http://127.0.0.1:{port}"
    print("\n" + "═" * 62)
    print(f"  ASANSÖR AVAN HESAPLAMA PROGRAMI   ·   sürüm {SURUM}")
    print("═" * 62)
    print(f"  Program çalışıyor :  {url}")
    print("  Tarayıcı kendiliğinden açılmazsa bu adresi yapıştırın.")
    print("  Kapatmak için bu pencerede  Ctrl + C  tuşlayın.")
    print("═" * 62 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        print("\n  Program kapatıldı.\n")


if __name__ == "__main__":
    calistir()
