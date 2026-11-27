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

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from cizim import asamalar, avan_kipi, hesap_isareti, istek_onbellegi
from uclar import avan_cizimi, avan_secici, avan_uclari, cizim_uclari, uc_ortak
from uclar.uc_ortak import baglantiyi_izle, hata_iletisi, hata_kaydi

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

    AKIŞ ( 17 Kas ):  istek Accept'te uc_ortak.AKIS_TURU'nü isterse yanıt satır satır gelir —
    aramanın aşamaları ( avan_secici.ASAMALAR ), en sonda sonuç ( uc_ortak.akisli_yanit ).  Yoksa
    eskisi gibi tek JSON."""
    birakildi = threading.Event()
    if uc_ortak.akis_isteniyor(istek):
        ilerleme = asamalar.Ilerleme(avan_secici.ASAMALAR)

        def ara_akisli():
            with avan_secici.korumali(birakildi.is_set):
                return avan_cizimler_sonucu(veri)

        return uc_ortak.akisli_yanit(istek, ara_akisli, ilerleme, birakildi)

    def ara():
        with avan_secici.korumali(birakildi.is_set):
            return api_avan_cizimler(veri)

    izleyici = asyncio.create_task(baglantiyi_izle(istek, birakildi))
    try:
        return await run_in_threadpool(ara)
    finally:
        birakildi.set()
        izleyici.cancel()


@router.post("/api/avan/aranacaklar")
def api_avan_aranacaklar(veri: dict = Body(...)):
    """Paketin şimdi arama yapacağı asansörler ( avan_cizimi.aranacaklar — arama yapmaz, anında ):
    { aranacaklar:  [ sıra ] }.  Avan girdisi okunamıyorsa boş ( paket kendi hatasını söyler )."""
    try:
        g, hata = avan_uclari.avan_girdisi(veri)
        return {"aranacaklar": [] if hata else avan_cizimi.aranacaklar(g)}
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return {"aranacaklar": []}


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
            asamalar.asama("cizim")
            #  Avan kipi ( cizim/avan_kipi.py ):  ürün yazıları ve hesap işareti yok
            with avan_kipi.etkin(r.get("avan")), istek_onbellegi.etkin():
                r["cizim"] = json.loads(cizim_uclari.cizimler_yaniti(r["istek"]).body)
        #  Bölümlerin ekrandaki adları ( kimlik değil )
        ad = hesap_isareti.KISA_AD
        r["acik_bolum_adlari"] = [ad.get(b, b) for b in r.get("acik_bolumler") or []]

        def adli(nedenler):
            return [
                f"{ad.get(n[6:], n[6:])}:  hesabı uygun değil" if n.startswith("bölüm:") else n
                for n in nedenler
            ]

        if r.get("nedenler"):
            r["nedenler"] = adli(r["nedenler"])
        #  Denenip kullanılmayan yerleşimin sorunları ( avan_secici.sec — "denenen" )
        for x in r.get("denenen") or []:
            x["nedenler"] = adli(x["nedenler"])
        #  "gereken"in isteği mimarın bugünkü ölçüleriyle değildir:  ekrana gitmez
        if r["durum"] != "uygun":
            r.pop("istek", None)
        return json.loads(json.dumps(r, default=str))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return {"durum": "hata", "hata": hata_iletisi("ÇİZİM HATASI", e, ": ")}
