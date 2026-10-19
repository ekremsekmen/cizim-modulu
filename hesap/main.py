# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN HESAPLAMA PROGRAMI
=================================
Yerel sunucu + tarayıcı arayüzü.  Çalıştırmak için:

    python3 main.py

Tarayıcı kendiliğinden açılır (http://127.0.0.1:8780).
Program tümüyle bilgisayarınızda çalışır, internet gerektirmez.

WEB SUNUCUSUNDA ( yayın ):

    python3 hesap/main.py --sunucu

Tarayıcı açılmaz, port aranmaz;  adres, port ve işçi sayısı ortamdan
( bkz. sunucu_ayari ).  Sağlık denetimi için:  GET /api/saglik
"""

import json
import logging
import os
import re
import sys
import threading
import webbrowser

from fastapi import FastAPI, Request
from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES, GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yollar

yollar.kur()

from cizim import uslup

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
#  YANIT SIKIŞTIRMA:  çizim yanıtı ( 11 SVG ) 834 KB, gzip'le 53 KB — her ölçü
#  değişikliğinde iner;  yavaş bağlantıda saniyeler.  Düzey 6:  4,5 ms ( 9'da
#  11 ms, 2 KB küçük ).  PDF zaten sıkışık ( ZIP Starlette'in dışladıkları
#  arasında ).
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=6,
    exclude_content_types=DEFAULT_EXCLUDED_CONTENT_TYPES + ("application/pdf",),
)

#  İSTEK BOYUTU SINIRI:  formun en büyük isteği ( paket:  dört asansör, kapak,
#  proje dosyası ) onlarca KB'tır;  dosya yükleyen uç yok ( "Proje aç"
#  tarayıcıda okur ).  5 MB'lık bir asansör adı çizim işçisini 3,9 sn tutuyordu
#  ( 17 Eki ).  Başlığa güvenilmez ( parça parça gelen gövde ):  baytlar sayılır.
ISTEK_AZAMI = 1024 * 1024


class IstekBoyutu:
    def __init__(self, uygulama, azami=ISTEK_AZAMI):
        self.uygulama, self.azami = uygulama, azami

    async def __call__(self, kapsam, al, gonder):
        if kapsam["type"] != "http" or kapsam["method"] not in ("POST", "PUT", "PATCH"):
            return await self.uygulama(kapsam, al, gonder)
        boy = dict(kapsam["headers"]).get(b"content-length")
        if boy is not None and boy.isdigit() and int(boy) > self.azami:
            return await self._reddet(gonder)
        govde, parcalar = 0, []
        while True:
            m = await al()
            if m["type"] != "http.request":
                parcalar.append(m)
                break
            govde += len(m.get("body", b""))
            if govde > self.azami:
                return await self._reddet(gonder)
            parcalar.append(m)
            if not m.get("more_body"):
                break

        async def tekrar():
            return parcalar.pop(0) if parcalar else await al()

        return await self.uygulama(kapsam, tekrar, gonder)

    async def _reddet(self, gonder):
        ileti = json.dumps(
            {
                "aktif": False,
                "hata": [
                    f"İstek çok büyük ( en çok {self.azami // 1024 // 1024} MB ) — girdileri kontrol edin."
                ],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        await gonder(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(ileti)).encode()),
                ],
            }
        )
        await gonder({"type": "http.response.body", "body": ileti})


app.add_middleware(IstekBoyutu)


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
from uclar import care_uclari
from uclar import cizim_uclari
from uclar import uygulama_uclari
from uclar.uc_ortak import _BELIRSIZ, _RED, _sayi, belirsiz_sayi_mi  # noqa: F401

#  UÇLAR İKİ PAKETTE:  avan projesi ve uygulama projesi ayrı dosyalarda
#  ( bkz. uclar/avan_uclari.py · uclar/uygulama_uclari.py ).  Ortak yardımcılar uclar/uc_ortak.py.
app.include_router(avan_uclari.router)
app.include_router(uygulama_uclari.router)
app.include_router(cizim_uclari.router)
app.include_router(care_uclari.router)


@app.get("/api/saglik")
def saglik():
    return {"durum": "calisiyor", "surum": SURUM}


#  ÇİZİM YAZI TİPİ ( cizim/yazi, OFL ):  SVG'deki yazılar "CizimYazi"yı ister;
#  ekran onu buradan yükler ( on-yuz/src/styles.css ).  Çizim yazının enini bu
#  yazı tipinin enleriyle hesaplar — her bilgisayarda aynı yazı tipi, aynı en.
app.mount("/yazi", StaticFiles(directory=uslup.YAZI_KLASORU), name="yazi")


# ------------------------------------------------------------------ ön yüz
#  ÖN YÜZ ( on-yuz/, React ) — derlenmiş dosyalar on-yuz/dist'te ( npm run
#  build;  depoda değil ).  Derleme yoksa program yine açılır ve nasıl
#  derleneceğini söyler.
ON_YUZ = os.path.join(os.path.dirname(KOK), "on-yuz", "dist")
#  Vite dosya adına içerik özeti koyar ( index-BfWyniNr.js ):  değişen dosyanın
#  adı da değişir, tarayıcı bir yıl önbellekte tutabilir.  index.html her
#  seferinde sorulur — yeni derlemenin adlarını o taşır.
_OZETLI = "public, max-age=31536000, immutable"


@app.get("/yeni", include_in_schema=False)
@app.get("/yeni/{yol:path}", include_in_schema=False)
def eski_yeni_adresi(istek: Request, yol: str = ""):
    """Geçiş dönemi adresi ( /yeni ):  yer imleri kırılmasın ( sorgusuyla:  ?cizim=… )."""
    sorgu = istek.url.query
    return RedirectResponse("/" + yol + (f"?{sorgu}" if sorgu else ""), status_code=301)


@app.get("/{yol:path}", include_in_schema=False)
def on_yuz(yol: str = ""):
    #  Bilinmeyen bir API adresi sayfa değil 404'tür ( yanlış yazılmış uç
    #  HTML döndürüp istemciyi "JSON değil" hatasına sokmasın )
    if yol == "api" or yol.startswith("api/"):
        return JSONResponse({"hata": "Bulunamadı"}, status_code=404)
    kok = os.path.realpath(ON_YUZ)
    giris = os.path.join(kok, "index.html")
    if not os.path.isfile(giris):
        return HTMLResponse(
            "<!doctype html><meta charset='utf-8'><title>Ön yüz derlenmemiş</title>"
            "<p style='font:15px system-ui;margin:48px'>Ön yüz derlenmemiş.  "
            "<code>on-yuz</code> klasöründe <code>npm ci</code> ve <code>npm run build</code> "
            "çalıştırın.</p>",
            status_code=503,
        )
    dosya = os.path.realpath(os.path.join(kok, yol))
    if yol and dosya.startswith(kok + os.sep) and os.path.isfile(dosya):
        ozetli = os.path.dirname(dosya) == os.path.join(kok, "assets")
        return FileResponse(dosya, headers={"Cache-Control": _OZETLI if ozetli else "no-cache"})
    #  Uzantılı bir ad istenip bulunamadıysa ( eski derlemenin betiği ) 404:
    #  yerine index.html dönmek tarayıcıda "yanlış MIME türü" hatası olurdu.
    if "." in os.path.basename(yol):
        return HTMLResponse("Bulunamadı", status_code=404)
    #  Uygulamanın kendi adresleri ( /uygulama/abc ):  yönlendirmeyi React yapar
    return FileResponse(giris, headers={"Cache-Control": "no-cache"})


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


def sunucu_ayari(ortam=None):
    """Web sunucusunda çalışma ayarı — ortam değişkenlerinden.

    AVAN_HOST        dinlenen adres.  Varsayılan 0.0.0.0 ( bütün ağ arayüzleri:
                     kapsayıcı ve barındırma servisi );  önünde aynı makinede
                     ters vekil ( nginx, Caddy ) varsa 127.0.0.1
    PORT             barındırma servislerinin verdiği port ( Render, Railway,
                     Fly … ister );  yoksa AVAN_PORT, o da yoksa 8780
    WEB_CONCURRENCY  işçi süreç sayısı ( uvicorn'un kendi değişkeni ).  Çizim
                     ve PDF işlemciyi tutar:  bir işçi aynı anda yalnız bir
                     ağır isteği hesaplar.  Varsayılan 1
    AVAN_SUNUCU      1:  programın kendi hatasında Python metni yerine genel
                     ileti ( uc_ortak.hata_iletisi ).  sunucu() kendisi koyar.
    """
    ortam = os.environ if ortam is None else ortam
    return {
        "host": ortam.get("AVAN_HOST") or "0.0.0.0",
        "port": int(ortam.get("PORT") or ortam.get("AVAN_PORT") or 8780),
        "workers": int(ortam.get("WEB_CONCURRENCY") or 1),
    }


def sunucu():
    """Web sunucusu:  tarayıcı açmaz, port aramaz ( port doluysa durur ).

    Uygulama "main:app" adıyla verilir:  uvicorn birden çok işçiyi ancak
    içe aktarma yolundan kurabilir.  Erişim kaydı açık ( INFO ).
    """
    import uvicorn

    a = sunucu_ayari()
    #  Web'de programın kendi hatasının Python metni kullanıcıya gitmez
    #  ( uc_ortak.hata_iletisi );  işçi süreçler ortamı devralır.  Program
    #  doğrudan uvicorn'la başlatılırsa barındırma ayarına AVAN_SUNUCU=1 yazılır.
    os.environ["AVAN_SUNUCU"] = "1"
    print(f"  ASANSÖR PROJE PROGRAMI  ·  sürüm {SURUM}  ·  sunucu  {a['host']}:{a['port']}", flush=True)
    uvicorn.run("main:app", host=a["host"], port=a["port"], workers=a["workers"], log_level="info")


if __name__ == "__main__":
    if "--sunucu" in sys.argv[1:]:
        sunucu()
    else:
        calistir()
