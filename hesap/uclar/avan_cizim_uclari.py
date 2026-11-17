# -*- coding: utf-8 -*-
"""
AVAN PROJESİNİN ÇİZİMLERİ  —  /api/avan/cizimler  ( 12 Kas 2026 )

Avan ekranı avan hesabının girdisini gönderir ( /api/avan ile aynı gövde ) ve
hangi asansörü istediğini söyler.  Asansörün MİMARİSİ avan kartındadır:

    kapasite ( ya da Q elle ) · hız        trafik hesabından
    kuyu genişliği · kuyu derinliği        mm
    durak kotları · kuyu dibi · kuyu tavanı ( · makine dairesi zemini )   kot
    makine dairesi var mı, ölçüleri        ortak panel

Seçici ( uclar/avan_secici ) bu kuyuya doğrulanmış asansörü bulur;  çizimler
uygulamanın çizim yolundan çıkar ( cizim_uclari.cizimler_yaniti ) — iki proje
aynı çizimi çizer.  Asansör bulunamadıysa çizim yoktur:  mimardan istenecek
ölçüler ya da sebep döner.
"""

import asyncio
import json
import logging
import threading
import zlib

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from cizim import avan_kipi, hesap_isareti, istek_onbellegi
from uclar import avan_cizimi, avan_secici, avan_uclari, cizim_uclari
from uclar.uc_ortak import hata_iletisi, hata_kaydi

log = logging.getLogger(__name__)
router = APIRouter()


def secim(veri):
    """İsteğin asansörü için seçicinin sonucu ( avan_cizimi.secim ) ya da
    { durum:  "hata" , hata } — avan girdisi okunamadıysa / asansör yoksa."""
    g, hata = avan_uclari.avan_girdisi(veri)
    if hata:
        return {"durum": "hata", "hata": hata}
    try:
        i = int((veri if isinstance(veri, dict) else {}).get("asansor") or 0)
    except (TypeError, ValueError):
        i = 0
    return avan_cizimi.secim(g, i)


@router.post("/api/avan/cizimler")
async def api_avan_cizimler_ucu(istek: Request, veri: dict = Body(...)):
    """/api/avan/cizimler ( 16 Kas ):  seçici korumalı ve önbellekli çalışır ( avan_secici.korumali );
    EKRAN İSTEĞİ BIRAKINCA ( girdi değişti — tarayıcı isteği iptal eder, bağlantı kapanır ) arama
    durur.  Eskiden bırakılan istek sunucuda sonuna kadar hesaplanıyordu:  süre sınırı kalkınca
    ( bütçe sınama sayısıdır ) yazarken biriken aramalar sunucuyu kilitleyebilirdi.  Arama iş
    parçacığında koşar;  bağlantı burada izlenir.

    AKIŞ ( 17 Kas ):  istek Accept'te AKIS_TURU'nü isterse yanıt satır satır gelir — aramanın
    aşamaları ( avan_secici.Ilerleme ), en sonda sonuç ( _akis ).  Yoksa eskisi gibi tek JSON."""
    if AKIS_TURU in istek.headers.get("accept", ""):
        return _akis(istek, veri)
    birakildi = threading.Event()

    async def izle():
        while not birakildi.is_set():
            if await istek.is_disconnected():
                birakildi.set()
                return
            await asyncio.sleep(BAGLANTI_ARALIGI)

    def ara():
        with avan_secici.korumali(birakildi.is_set):
            return api_avan_cizimler(veri)

    izleyici = asyncio.create_task(izle())
    try:
        return await run_in_threadpool(ara)
    finally:
        birakildi.set()
        izleyici.cancel()


#  Bağlantının kapanıp kapanmadığına bakma aralığı ( sn;  bir sınama ~0,1 – 1 sn )
BAGLANTI_ARALIGI = 0.25

#  AKIŞLI YANIT:  her satır bir JSON — { ilerleme:  { asamalar , sinama , gecen } } … , sonda
#  { sonuc:  /api/avan/cizimler'in yanıtı }.  Satırlar en çok ILERLEME_ARALIGI'nda bir, yalnız
#  yeni bir şey varsa.
AKIS_TURU = "application/x-ndjson"
ILERLEME_ARALIGI = 0.2


def _akis(istek, veri):
    """Akışlı yanıt.  SIKIŞTIRMA BURADA ( main'deki GZipMiddleware bu türü dışlar ):  çizim yanıtı
    834 KB, gzip'le ~53 KB — ama ara katman küçük satırları biriktirir, aşamalar geç gelirdi.  Her
    satır gzip akışına yazılıp hemen boşaltılır ( Z_SYNC_FLUSH ):  tarayıcı satırı geldiği anda
    açar, sonuç yine sıkışık iner.

    BAĞLANTI KAPANINCA ( ekran isteği bıraktı ) arama durur:  StreamingResponse kopmayı kendisi
    dinler ( ASGI 2.3 — uvicorn ) ve üreteci iptal eder, finally aramayı bırakır.  Burada AYRICA
    is_disconnected yoklanmaz:  akış sürerken ikinci bir dinleyici bağlantıyı bozuyordu ( tarayıcı
    sonucu alıp isteği yine de "kesildi" sayıyordu — 17 Kas, uçtan uca testte yakalandı )."""
    gz = "gzip" in istek.headers.get("accept-encoding", "")
    ilerleme = avan_secici.Ilerleme()
    birakildi = threading.Event()

    def ara():
        with avan_secici.korumali(birakildi.is_set), avan_secici.ilerleme(ilerleme):
            return avan_cizimler_sonucu(veri)

    async def satirlar():
        sikistir = zlib.compressobj(6, zlib.DEFLATED, 31) if gz else None

        def bayt(nesne, son=False):
            b = (json.dumps(nesne, ensure_ascii=False, default=str) + "\n").encode("utf-8")
            if sikistir is None:
                return b
            return sikistir.compress(b) + sikistir.flush(zlib.Z_FINISH if son else zlib.Z_SYNC_FLUSH)

        arama = asyncio.ensure_future(run_in_threadpool(ara))
        gonderilen = -1
        try:
            while True:
                await asyncio.wait({arama}, timeout=ILERLEME_ARALIGI)
                if arama.done():
                    break
                surum, durum = ilerleme.durum()
                if surum != gonderilen:
                    gonderilen = surum
                    yield bayt({"ilerleme": durum})
            yield bayt({"sonuc": arama.result()}, son=True)
        finally:
            #  Bağlantı kapandıysa Starlette üreteci iptal eder ( buraya gelinir ):  arama durur
            birakildi.set()

    basliklar = {"Cache-Control": "no-store", "X-Accel-Buffering": "no"}
    if gz:
        basliklar.update({"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
    return StreamingResponse(satirlar(), media_type=AKIS_TURU, headers=basliklar)


def api_avan_cizimler(veri):
    """Avan asansörünün çizimleri, JSON yanıtı ( avan_cizimler_sonucu )."""
    return JSONResponse(avan_cizimler_sonucu(veri))


def avan_cizimler_sonucu(veri):
    """Avan asansörünün çizimleri.  Yanıt seçicinin sonucudur ( durum:  uygun ·
    gereken · sigmaz · paket_yok · eksik · hata · tamamlanmadi );  "uygun"da ayrıca cizim —
    uygulamanın çizim yanıtı ( cizimler:  SVG listesi ).  tamamlanmadi:  korumalı aramada
    ( api_avan_cizimler_ucu ) güvenlik süresi doldu ya da istek bırakıldı — sonuç bilinmiyor."""
    try:
        #  Seçicinin her sınaması kendi önbelleğiyle koşar ( care_uclari.girdi_durumu );  dışına
        #  ortak bir önbellek sarılmaz — adaylar ayrı girdilerdir.
        r = secim(veri)
        if r["durum"] == "uygun":
            avan_secici.asama("cizim")
            #  Avan kipi ( cizim/avan_kipi.py ):  ürün yazıları ve hesap işareti yok
            with avan_kipi.etkin(r.get("avan")), istek_onbellegi.etkin():
                r["cizim"] = json.loads(cizim_uclari.cizimler_yaniti(r["istek"]).body)
        #  Bölümlerin ekrandaki adları ( kimlik değil )
        ad = hesap_isareti.KISA_AD
        r["acik_bolum_adlari"] = [ad.get(b, b) for b in r.get("acik_bolumler") or []]
        if r.get("nedenler"):
            r["nedenler"] = [
                f"{ad.get(n[6:], n[6:])}:  hesabı uygun değil" if n.startswith("bölüm:") else n
                for n in r["nedenler"]
            ]
        #  "gereken"in isteği mimarın bugünkü ölçüleriyle değildir:  ekrana gitmez
        if r["durum"] != "uygun":
            r.pop("istek", None)
        return json.loads(json.dumps(r, default=str))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return {"durum": "hata", "hata": hata_iletisi("ÇİZİM HATASI", e, ": ")}
