# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ UÇLARI

Mukavemet + elektrik + topraklama hesabı ve çıktıları.  Avandan bağımsızdır;
elektrik hesapları avan MOTORUNU çağırır ( motor/uygulama/uygulama_hesabi.py ), ama
uçlar ayrıdır.
"""

import json
import logging
import os

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from cizim import elektrik
from cizim import istek_onbellegi
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar.uc_ortak import (
    hata_iletisi,
    hata_kaydi,
    _dosya_adi,
    _indir,
    _paket_ekleri,
    _proje_kimligi,
    _uretilemedi,
)
from motor.uygulama import uygulama_kapagi
from motor.uygulama import uygulama_hesabi
from ciktilar import kapak_cikti
from ciktilar import pdf_cikti

try:
    from ciktilar import dxf_cikti

    _DXF_HATA = None
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("CAD çıktısı kapalı:  %s", _e)
    dxf_cikti, _DXF_HATA = None, _e

#  Paftanın PDF'i ( pypdf ister ):  yoksa paket PDF'siz iner, DXF etkilenmez
try:
    from ciktilar import pafta_pdf
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("Paftanın PDF'i kapalı:  %s", _e)
    pafta_pdf = None
_BASLATICI = "baslat.command" if os.name != "nt" else "baslat.bat"

log = logging.getLogger(__name__)
router = APIRouter()

#  Uygulama paketinin kapağının büyük başlığı ( kapak_cikti'nin varsayılanı avanınkidir )
BASLIK = "ASANSÖR UYGULAMA PROJESİ"


@router.get("/api/uygulama/alanlar")
def uygulama_alanlari():
    """Formun kendini üretmesi için girdi sözleşmesi ( uygulama_istegi.alanlar )."""
    return uygulama_istegi.alanlar()


def _coklu_sonuc(veri):
    """Çoklu uygulama hesabı.  ( sonuc , hata_yaniti )"""
    try:
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    except uygulama_istegi.GecersizGirdi as e:
        return None, JSONResponse({"aktif": False, "hata": e.hatalar}, status_code=200)
    #  Hesap çizimden gelen girdiler için yerleşim kurar:  bu istekte bir kez
    with istek_onbellegi.etkin():
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    if not s.get("aktif"):
        return None, JSONResponse(
            {"aktif": False, "hata": s.get("hata") or ["HESAP HATASI"]}, status_code=200
        )
    return s, None


@router.post("/api/uygulama/coklu")
def api_uygulama_coklu(veri: dict = Body(...)):
    """1 - 4 asansörlük uygulama projesi."""
    try:
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        for a in s.get("asansorler") or []:
            a.pop("ara", None)  # ara değerler testler içindir, arayüze gerekmez
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse(
            {"aktif": False, "hata": [hata_iletisi("HESAP HATASI", e, ": ")]}, status_code=200
        )


@router.post("/api/indir/uygulama-pdf")
def indir_uygulama_pdf(veri: dict = Body(...)):
    try:
        _p = _proje_kimligi(veri)
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        return _indir(
            pdf_cikti.uygulama_pdf(s, _p),
            _dosya_adi(_p, "Uygulama Projesi Hesaplari", "pdf"),
            "application/pdf",
        )
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)


@router.post("/api/indir/uygulama-dwg")
def indir_uygulama_dwg(veri: dict = Body(...)):
    """Uygulama projesi paftası — ofis tip proje formatına yerleştirilmiş CAD."""
    if dxf_cikti is None:
        return JSONResponse(
            {
                "hata": "HESAP HATASI: CAD çıktısı için gereken kitaplıklar kurulu değil "
                f"( {_DXF_HATA} ).  Programı kapatıp {_BASLATICI} dosyasını "
                "yeniden çalıştırın; eksik kitaplıklar kendiliğinden kurulur."
            },
            status_code=200,
        )
    #  Hesap, çizimler ve paftalar aynı yerleşimleri kurar:  bu istekte bir kez
    with istek_onbellegi.etkin():
        return _uygulama_paketi(veri)


def _uygulama_paketi(veri):
    try:
        _p = _proje_kimligi(veri)
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        #  ÇİZİMLER:  her asansörün kuyu kesitleri ve planları hesap
        #  sayfalarının sağına dizilir.  Bir asansörün çizimi kurulamıyorsa
        #  paket ÇİZİMSİZ inmez — eksik bir proje teslim edilmesin, sebep
        #  söylenir ( girdi formun "Çizim" grubunda ya da hesapta düzeltilir ).
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
        cizim = cizim_uclari.girdiler(veri, asansorler, ortak, s, _p["proje_adi"])
        eksik = [f"{i}. asansör — {h}" for i, (_g, hata) in enumerate(cizim, 1) for h in hata]
        if eksik:
            return JSONResponse(
                {"aktif": False, "hata": "ÇİZİMLER KURULAMADI:\n· " + "\n· ".join(eksik)}, status_code=200
            )
        paftalar = []
        #  KAPAK.  Uygulama projesinin kapağı MMO'nun ayrı kitabındadır;  ama
        #  paket bir teslim dosyasıdır ve kapaksız gitmesi için sebep yok —
        #  kapak alanları doldurulmuşsa pakete de girer.  Asansör tabloları
        #  ( her asansöre bir tablo ) projeden dolar, yazılan değer ezer.
        kapak = veri.get("kapak_sayfasi")
        if isinstance(kapak, dict) and any(str(x).strip() for x in kapak.values()):
            #  Büyük başlık belgenin adıdır ( avan kapağında ASANSÖR AVAN PROJESİ ):
            #  projenin adı dosya adında ve çizimlerin antetinde kalır.
            kapak = {**kapak, "project_title": BASLIK}
            turetilen = uygulama_kapagi.uygulamadan(s, [g for g, _h in cizim])
            paftalar.append(
                ("Kapak", kapak_cikti.pdf_baytlari(kapak, uygulama_kapagi.kapak_tablolari(kapak, turetilen)))
            )
        paftalar.append(("Uygulama Projesi", pdf_cikti.uygulama_pdf(s)))
        ad = _dosya_adi(_p, "Uygulama Projesi", "zip")
        #  ELEKTRİK PROJESİ:  her asansörün hesabından ( paftada sol altta )
        elektrikler = elektrik.pafta_sayfalari(
            [(x.get("elektrik"), x.get("tanim")) for x in s["asansorler"] if x.get("aktif")]
        )
        #  Pakete PROJE DOSYASI da girer:  teslim paketi ile geri dönüş
        #  noktası aynı arşivde dursun.
        paket, sebep, tasti = dxf_cikti.proje_paketi(
            paftalar,
            os.path.splitext(ad)[0],
            list(_paket_ekleri(veri, "uygulama")),
            son_islem=cizim_uclari.paftaya_ekle([g for g, _h in cizim]),
            pdf_islem=(
                pafta_pdf.paket_pdfleri(paftalar, [g for g, _h in cizim], elektrikler) if pafta_pdf else None
            ),
            elektrikler=elektrikler,
        )
        yanit = _indir(paket, ad, "application/zip")
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)
