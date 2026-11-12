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

from cizim import istek_onbellegi
from motor.avan import tablolar
from motor.ortak.adimlar import evet_mi
from temel import sayi_mi
from uclar import avan_secici, avan_uclari, cizim_uclari
from uclar.uc_ortak import hata_iletisi, hata_kaydi

log = logging.getLogger(__name__)
router = APIRouter()

#  Avan kartındaki mimari alanlar ( kotlar metindir — uygulamanın kot kutuları gibi okunur )
KART = ("kuyu_genisligi", "kuyu_derinligi", *avan_secici.KOTLAR)


def mimari(a, ortak):
    """Avan asansörü ( okunmuş kart ) + ortak panel → seçicinin girdisi."""
    yuk = a.get("Q_elle") if sayi_mi(a.get("Q_elle")) else tablolar.tablo7_yuk(a.get("kapasite"))
    m = {"beyan_yuku": yuk, "beyan_hizi": a.get("V"), "mk_yok": evet_mi(ortak.get("mk_yok"))}
    m.update({k: a.get(k) for k in KART})
    if not m["mk_yok"]:
        m.update({k: ortak.get(k) for k in avan_secici.MIMARI_GENEL})
    return m


def secim(veri):
    """İsteğin asansörü için seçicinin sonucu ( avan_secici.sec ) ya da
    { durum:  "hata" , hata } — avan girdisi okunamadıysa / asansör yoksa."""
    g = avan_uclari._avan_girdi(veri)
    hata = avan_uclari._belirsiz_hata()
    if hata:
        return {"durum": "hata", "hata": hata}
    try:
        i = int((veri if isinstance(veri, dict) else {}).get("asansor") or 0)
    except (TypeError, ValueError):
        i = 0
    asansorler = g["asansorler"]
    if not 0 <= i < len(asansorler) or asansorler[i] is None:
        return {
            "durum": "hata",
            "hata": "Avan hesabında bu asansör yok — kapasite ve hız trafik hesabından gelir.",
        }
    return avan_secici.sec(mimari(asansorler[i], g["ortak"]))


@router.post("/api/avan/cizimler")
def api_avan_cizimler(veri: dict = Body(...)):
    """Avan asansörünün çizimleri.  Yanıt seçicinin sonucudur ( durum:  uygun ·
    gereken · sigmaz · paket_yok · eksik · hata );  "uygun"da ayrıca cizim —
    uygulamanın çizim yanıtı ( cizimler:  SVG listesi )."""
    try:
        #  Seçicinin her sınaması kendi önbelleğiyle koşar ( care_uclari._durum );  dışına
        #  ortak bir önbellek sarılmaz — adaylar ayrı girdilerdir.
        r = secim(veri)
        if r["durum"] == "uygun":
            with istek_onbellegi.etkin():
                c = json.loads(cizim_uclari.cizimler_yaniti(r["istek"]).body)
            #  Ürün bölümleri avanın işi değil:  ekranda "hesapta uygun değil" işareti yok
            c.pop("hesap_parcalari", None)
            r["cizim"] = c
        #  "gereken"in isteği mimarın bugünkü ölçüleriyle değildir:  ekrana gitmez
        if r["durum"] != "uygun":
            r.pop("istek", None)
        return JSONResponse(json.loads(json.dumps(r, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"durum": "hata", "hata": hata_iletisi("ÇİZİM HATASI", e, ": ")})
