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
import threading

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from cizim import asamalar
from cizim import elektrik
from cizim import istek_onbellegi
from cizim import pafta
from uclar import cizim_uclari
from uclar import uc_ortak
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

#  PAKETİN AŞAMALARI ( 20 Kas — arayüz taslağı B1 ):  önce hesap ( bütün asansörler ve çizim
#  girdileri ), sonra paketin ortak adımları ( uc_ortak.PAKET_ASAMALARI )
PAKET_ASAMALARI = {"hesap": ("Hesap yapılıyor", "Hesap yapıldı"), **uc_ortak.PAKET_ASAMALARI}


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
        #  Projenin genel hükmü ( açılış listesi ):  motor kurar, ekran basar
        s["proje_hukmu"] = uygulama_hesabi.proje_hukmu(s)
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
async def indir_uygulama_dwg_ucu(istek: Request, veri: dict = Body(...)):
    """Uygulama projesi paftası — ofis tip proje formatına yerleştirilmiş CAD ( indir_uygulama_dwg ).

    AKIŞ ( 20 Kas — arayüz taslağı B1:  paket 1 asansörde 2,7, 4 asansörde 10,4 sn sürüyor, ekranda
    yalnız dönen işaret vardı ):  istek uc_ortak.AKIS_TURU'nü isterse paketin adımları satır satır,
    sonda dosya ( uc_ortak.akis_sonucu ).  Kullanıcı vazgeçince ( bağlantı kapandı ) iş bir sonraki
    adımda durur;  eskiden paket sonuna kadar kuruluyordu.  İstemiyorsa eskisi gibi ZIP."""
    if not uc_ortak.akis_isteniyor(istek):
        return await run_in_threadpool(indir_uygulama_dwg, veri)
    birakildi = threading.Event()
    ilerleme = asamalar.Ilerleme(PAKET_ASAMALARI, iptal=birakildi.is_set)
    return uc_ortak.akisli_yanit(
        istek, lambda: uc_ortak.akis_sonucu(indir_uygulama_dwg(veri)), ilerleme, birakildi
    )


def indir_uygulama_dwg(veri):
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
        #  KÂĞIT ENİ ( 19 Kas ):  paftanın dizileceği rulo — 600 / 900 mm, boşsa 600;  başka
        #  değer reddedilir ( hesaptan önce:  boşuna beklenmesin )
        try:
            kagit = pafta.kagit_eni(veri.get("kagit"))
        except ValueError as e:
            return JSONResponse({"aktif": False, "hata": f"KÂĞIT ENİ:  {e}"}, status_code=200)
        _p = _proje_kimligi(veri)
        #  Adımlar ( akışlı istekte ekranda;  yoksa bildirim hiçbir şey yapmaz — asamalar )
        dwg = bool(dxf_cikti.donusturucu())
        asamalar.planla(["hesap"] + uc_ortak.paket_plani(True, dwg, pafta_pdf is not None))
        adet = len(veri.get("asansorler") or []) if isinstance(veri.get("asansorler"), list) else 0
        asamalar.asama("hesap", f"{adet} asansör" if adet > 1 else "")
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
        eksik += cizim_uclari.grup_sorunlari([g for g, _h in cizim])
        if eksik:
            return JSONResponse(
                {"aktif": False, "hata": "ÇİZİMLER KURULAMADI:\n· " + "\n· ".join(eksik)}, status_code=200
            )
        asamalar.asama("sayfalar")
        paftalar = []
        #  KAPAK.  Uygulama projesinin kapağı MMO'nun ayrı kitabındadır;  ama
        #  paket bir teslim dosyasıdır ve kapaksız gitmesi için sebep yok.
        #  Asansör tabloları ( her asansöre bir tablo ) projeden dolar, yazılan
        #  değer ezer;  yazılmayan kişisel alanlar boş kalır.  HER PAKETTE ( 18 Kas —
        #  yayın öncesi denetim ):  eskiden yalnız bir kapak alanı doluysa giriyordu;
        #  başlığı ve kapağı boş projede paket kapaksız iniyor, ofis şablonunun antet
        #  hücreleri kendi örnek değerleriyle ( "300 KG (4 KİŞİ)", "0,1/2 DURAK",
        #  "2,67 KW" … ) DXF'te ve PDF şeridinde kalıyordu.
        kapak = veri.get("kapak_sayfasi") if isinstance(veri.get("kapak_sayfasi"), dict) else {}
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
        son_islem, pdf_islem = uc_ortak.asamali_islemler(
            cizim_uclari.paftaya_ekle([g for g, _h in cizim]),
            pafta_pdf.paket_pdfleri(paftalar, [g for g, _h in cizim], elektrikler) if pafta_pdf else None,
            dwg,
        )
        paket, sebep, tasti = dxf_cikti.proje_paketi(
            paftalar,
            os.path.splitext(ad)[0],
            list(_paket_ekleri(veri, "uygulama")),
            son_islem=son_islem,
            pdf_islem=pdf_islem,
            elektrikler=elektrikler,
            kagit=kagit,
        )
        yanit = _indir(paket, ad, "application/zip")
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)
