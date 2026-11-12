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

import json
import logging

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from cizim import avan_kipi, hesap_isareti, istek_onbellegi
from uclar import avan_cizimi, avan_uclari, cizim_uclari
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
def api_avan_cizimler(veri: dict = Body(...)):
    """Avan asansörünün çizimleri.  Yanıt seçicinin sonucudur ( durum:  uygun ·
    gereken · sigmaz · paket_yok · eksik · hata );  "uygun"da ayrıca cizim —
    uygulamanın çizim yanıtı ( cizimler:  SVG listesi )."""
    try:
        #  Seçicinin her sınaması kendi önbelleğiyle koşar ( care_uclari.girdi_durumu );  dışına
        #  ortak bir önbellek sarılmaz — adaylar ayrı girdilerdir.
        r = secim(veri)
        if r["durum"] == "uygun":
            #  Avan kipi ( cizim/avan_kipi.py ):  ürün yazıları ve hesap işareti yok
            with avan_kipi.etkin(), istek_onbellegi.etkin():
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
        return JSONResponse(json.loads(json.dumps(r, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"durum": "hata", "hata": hata_iletisi("ÇİZİM HATASI", e, ": ")})
