# -*- coding: utf-8 -*-
"""
AVAN PROJE UÇLARI

Trafik hesabı, avan hesapları, proje kapağı ve bunların PDF / CAD
çıktıları.  Uygulama projesinden bağımsızdır.
"""

import json
import logging
import os
from datetime import date

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from uclar.uc_ortak import (
    hata_kaydi,
    _BELIRSIZ,
    _RED,
    _belirsiz_hata,
    _bos_mu,
    _dosya_adi,
    _indir,
    _paket_ekleri,
    _proje_kimligi,
    _sabitler_coz,
    _sayi,
    _sozluk_listesi,
    _temiz,
    _uretilemedi,
    belirsiz_sayi_mi,
)
from motor.avan import avan_hesabi
from motor.avan import kapak
from motor.avan import tablolar
from motor.avan import trafik
from ciktilar import kapak_cikti
from ciktilar import pdf_cikti

try:
    from ciktilar import dxf_cikti

    _DXF_HATA = None
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("CAD çıktısı kapalı:  %s", _e)
    dxf_cikti, _DXF_HATA = None, _e
_BASLATICI = "baslat.command" if os.name != "nt" else "baslat.bat"

log = logging.getLogger(__name__)
router = APIRouter()

TRAFIK_SAYISAL = (
    "bina_yuksekligi",
    "yapi_yuksekligi",
    "N",
    "hizli1",
    "hizli2",
    "h",
    "P",
    "kapi_genisligi",
    "bodrum",
    "manuel_k",
    "manuel_V",
    "manuel_ta",
    "manuel_tk",
    "manuel_tg",
    "manuel_tp",
    "manuel_adet",
)

ASANSOR_SAYISAL = (
    "P",
    "kapi_genisligi",
    "V",
    "durak",
    "h",
    "bodrum",
    "manuel_ta",
    "manuel_tk",
    "manuel_tg",
    "manuel_tp",
)

AVAN_ORTAK_SAYISAL = (
    "U",
    "kappa",
    "eps_max",
    "temel_a",
    "temel_b",
    "beta",
    "serit_L",
    "cubuk_sayisi",
    "mk_uzunluk",
    "mk_genislik",
)

AVAN_AS_SAYISAL = (
    "i_palanga",
    "q_denge",
    "kapasite",
    "Q_elle",
    "V",
    "eta",
    "Hk",
    "kuyu_genisligi",
    "kabin_boyu",
    "kabin_genisligi",
    "Gk_elle",
    "gr",
    "Fmk",
    "Fsh",
    "Nsc",
    "S1",
    "L1",
    "S2",
    "L2",
    "zincir_birim_kutle",
)

#  Red metninde görünen adlar:  "Q_elle" değil "Q elle — anma yükü".  Motorun
#  kendi tablolarından okunur ( tek kaynak );  yalnız motorun denetlemediği
#  birkaç ortak alanın adı burada yazılıdır.
AVAN_AS_ETIKET = {
    "kapasite": "Kapasite",
    **{k: ad for k, ad, _poz in avan_hesabi.ZORUNLU_ALANLAR},
    **{k: ad for k, ad, _aralik, _birim in avan_hesabi.ASANSOR_SINIRLARI},
}
AVAN_ORTAK_ETIKET = {
    **{k: ad for k, (ad, _birim) in avan_hesabi.OFIS_ETIKET.items()},
    "temel_a": "Temel uzunluğu",
    "temel_b": "Temel genişliği",
    "serit_L": "L — topraklama şeridi boyu",
    "mk_uzunluk": "Makine dairesi uzunluğu",
    "mk_genislik": "Makine dairesi genişliği",
}

#  Ofis standardında METİN olan sabitler ( kablo tipi … ) — sayıya çevrilmez.
AVAN_METIN_SABITLER = tuple(
    k
    for k, v in {**avan_hesabi.SABIT_B_VARSAYILAN, **avan_hesabi.OFIS_VARSAYILAN}.items()
    if isinstance(v, str)
)


def _ek_nufus_oku(ham):
    """Ek nüfus satırlarını okur.  Bozuk satırlar `_BELIRSIZ` üzerinden bildirilir."""
    satirlar = []
    for i, s in enumerate(_sozluk_listesi(ham), 1):
        kalem, ham_miktar = s.get("kalem"), s.get("miktar")
        if not kalem and (ham_miktar in (None, "")):
            continue  # tümüyle boş satır — yok say
        if belirsiz_sayi_mi(ham_miktar):
            _BELIRSIZ.append(f"ek nüfus {i}. satır miktarı = {str(ham_miktar).strip()}")
            continue
        miktar = _sayi(ham_miktar)
        if not kalem:
            _RED.append(f"ek nüfus {i}. satırında Tablo-1 kalemi seçilmemiş")
            continue
        if miktar is None:
            _RED.append(f"ek nüfus {i}. satır miktarı sayı değil ( {str(ham_miktar).strip()[:20]!r} )")
            continue
        if miktar < 0:
            _RED.append(f"ek nüfus {i}. satır miktarı negatif ( {miktar} ) — nüfus eksiltilemez")
            continue
        satirlar.append({"aciklama": s.get("aciklama"), "miktar": miktar, "kalem": kalem})
    return satirlar


def _trafik_girdi(veri: dict):
    """
    Trafik girdisini tek biçime getirir:  bina alanları + `asansorler` listesi.

    Yöntemi ( tek / çoklu ) ARTIK KULLANICI SEÇMEZ, veri belirler — bkz.
    motor.traffic.hesapla().  Eski `mod` alanı ve düz `P / kapi_genisligi /
    kapi_tipi` girdileri geriye dönük uyumluluk için hâlâ kabul edilir:
    liste boşsa düz alanlardan TEK asansörlük bir liste kurulur.
    """
    _BELIRSIZ.clear()
    _RED.clear()
    veri = veri if isinstance(veri, dict) else {}
    ham = veri.get("girdiler")
    ham = ham if isinstance(ham, dict) else {}
    #  Red metni kutunun EKRANDAKİ adını söyler ( "hizli1" değil "⑤ Daire sayısı" ).
    g = _temiz(ham, TRAFIK_SAYISAL, etiket=trafik.girdi_etiketleri(ham.get("bina_tipi")))
    g["ek_nufus"] = _ek_nufus_oku(ham.get("ek_nufus"))
    #  Kişi sayısı YAZILMIŞ asansör tanımlıdır.  Okunabilir P aranıyordu:
    #  "8 kişi" yazılan asansör listeden sessizce düşüyor, trafik bir asansör
    #  eksik hesaplanıyordu.  Artık okunamayan P, sebebiyle reddedilir.
    liste = [
        _temiz(a, ASANSOR_SAYISAL, f"ASANSÖR-{i}: ", etiket=trafik.ASANSOR_ETIKET)
        for i, a in enumerate(_sozluk_listesi(ham.get("asansorler")), 1)
        if not _bos_mu(a.get("P"))
    ][:4]
    if not liste and g.get("P") is not None:
        bir = {
            k: g.get(k) for k in ("P", "kapi_genisligi", "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp")
        }
        bir["kapi_tipi"] = ham.get("kapi_tipi")
        liste = [bir]
    g["asansorler"] = liste
    return g


def _avan_girdi(veri: dict):
    _BELIRSIZ.clear()
    _RED.clear()
    veri = veri if isinstance(veri, dict) else {}
    v = veri.get("girdiler")
    v = v if isinstance(v, dict) else {}
    ortak_ham = v.get("ortak")
    ortak = _temiz(
        ortak_ham if isinstance(ortak_ham, dict) else {}, AVAN_ORTAK_SAYISAL, etiket=AVAN_ORTAK_ETIKET
    )
    asansorler = []
    for sira, a in enumerate(_sozluk_listesi(v.get("asansorler"))[:4], 1):
        #  Kapasitesi ya da anma yükü YAZILMAMIŞ kolon tanımsızdır ve okunmaz:
        #  içinde kalmış bir değer projeyi durdurmamalı.  Yazılmışsa okunur —
        #  "abc" yazılmış anma yükü eskiden kolonu sessizce tanımsız yapıyordu.
        if not a.get("aktif", True) or (_bos_mu(a.get("kapasite")) and _bos_mu(a.get("Q_elle"))):
            asansorler.append(None)
            continue
        asansorler.append(_temiz(a, AVAN_AS_SAYISAL, f"{sira} NOLU ASANSÖR: ", AVAN_AS_ETIKET))
    sb = _sabitler_coz(
        v.get("sabitler"), AVAN_METIN_SABITLER, lambda k: f"Ofis standardı · {AVAN_ORTAK_ETIKET.get(k, k)}"
    )
    return {
        "ortak": ortak,
        "asansorler": asansorler,
        "sabitler": sb,
        "trafik": _trafik_koprusu(v.get("trafik")),
    }


def _trafik_koprusu(ham):
    """
    Avan tarafına gönderilen trafik özeti — dışarıdan gelen veriye güvenmeden
    yalnız beklenen alanları, sayıya çevirerek alır.
    """
    if not isinstance(ham, dict):
        return {}
    liste = []
    for a in _sozluk_listesi(ham.get("asansorler"))[:4]:
        liste.append(
            {"P": _sayi(a.get("P")), "V": _sayi(a.get("V")), "toplam_seyahat": _sayi(a.get("toplam_seyahat"))}
        )
    if not liste:
        return {}
    return {
        "tip": ham.get("tip") if ham.get("tip") in ("tek", "coklu") else None,
        "N": _sayi(ham.get("N")),
        "bodrum": _sayi(ham.get("bodrum")),
        "h": _sayi(ham.get("h")),
        "adet": _sayi(ham.get("adet")),
        "asansorler": liste,
    }


def _avan_sonuc(veri):
    """Avan hesabı  —  ( sonuç , hata_yanıtı ).

    Ekran, PDF ve CAD aynı yoldan geçer:  ekran neyi reddediyorsa çıktı da
    reddeder.  İki ret kaynağı vardır — okunamayan yazım ( API ) ve
    kullanılamayan değer ( motor, bkz. motor.avan.avan_hesabi.girdi_hatalari ).
    """
    g = _avan_girdi(veri)
    hata = _belirsiz_hata()
    s = None if hata else avan_hesabi.hesapla(g)
    hata = hata or s.get("hata")
    if hata:
        return None, JSONResponse({"hata": hata}, status_code=200)
    return s, None


# ------------------------------------------------------------------ uçlar
@router.get("/api/secenekler")
def secenekler():
    return {
        "bina_tipleri": tablolar.BINA_TIPLERI,
        #  ⑤ / ⑥ kutularının bina tipine göre etiketi —  red metni de aynı adı söyler.
        "hizli_etiketleri": {bt: trafik.hizli_etiketleri(bt) for bt in ("", *tablolar.BINA_TIPLERI)},
        #  Kapakta hesaptan dolan alanlar ( motor/avan/kapak.py ).
        "kapak_turetilen": list(kapak.ALANLAR),
        "kapi_genislikleri": tablolar.KAPI_GENISLIKLERI,
        "kapi_tipleri": tablolar.KAPI_TIPLERI,
        "kapasiteler": tablolar.GECERLI_KAPASITELER,
        "hizlar": tablolar.GECERLI_HIZLAR,
        "nufus_kalemleri": list(tablolar.TABLO_1.keys()),
        "tablo_1": tablolar.TABLO_1,
        "kesitler": sorted(tablolar.KABLO_IZ.keys()),
        "makine_tipleri": tablolar.MAKINE_TIPLERI,
        "aski_oranlari": tablolar.ASKI_ORANLARI,
        "sabit_b": avan_hesabi.SABIT_B_VARSAYILAN,
        "sabit_b_yedek": list(avan_hesabi.SABIT_B_YEDEK),
        "ofis_varsayilan": avan_hesabi.OFIS_VARSAYILAN,
        "ofis_asansor_alanlari": list(avan_hesabi.OFIS_ASANSOR_ALANLARI),
        "ofis_ortak_alanlari": list(avan_hesabi.OFIS_ORTAK_ALANLARI),
        "motor_kademeleri": list(tablolar.MOTOR_KADEMELERI),
        "sabit_a": avan_hesabi.SABIT_A,
        "bugun": date.today().strftime("%d.%m.%Y"),
        "tablo_10": tablolar.TABLO_10,
        "tablo_9": tablolar.TABLO_9,
        "tablo_7": tablolar.TABLO_7,
        "tablo_4": {str(k): v for k, v in tablolar.TABLO_4.items()},
        "tablo_8": {str(k): v for k, v in tablolar.TABLO_8.items()},
        "tablo_11": tablolar.TABLO_11,
        "kablo_iz": {str(k): v for k, v in tablolar.KABLO_IZ.items()},
        "ayd_sutun_aciklama": tablolar.AYD_SUTUN_ACIKLAMA,
    }


# ------------------------------------------------- uygulama projesi: mukavemet
@router.post("/api/trafik")
def api_trafik(veri: dict = Body(...)):
    try:
        g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = trafik.hesapla(g)
        #  Avan sekmesi bu özeti geri gönderir; kapasite / hız / kuyu yüksekliği
        #  tutarsızlığı orada uyarı olarak görünür.
        s["avan_koprusu"] = trafik.trafik_ozeti(s)
        #  Kapağın boş bırakılan asansör alanları hesaptan dolar ( ekranda
        #  gri yer tutucu olarak görünür, çıktıya o basılır ).
        s["kapak_bilgileri"] = kapak.trafikten(s)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)


@router.post("/api/avan")
def api_avan(veri: dict = Body(...)):
    try:
        s, yanit = _avan_sonuc(veri)
        if yanit is not None:
            return yanit
        s["kapak_bilgileri"] = kapak.avandan(s)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)


@router.post("/api/indir/trafik-pdf")
def indir_trafik_pdf(veri: dict = Body(...)):
    try:
        g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = trafik.hesapla(g)
        ek = "Trafik Hesabi" if s.get("yol") == "tek" else "Coklu Asansor Trafik"
        _p = _proje_kimligi(veri)
        return _indir(pdf_cikti.trafik_pdf(s, _p), _dosya_adi(_p, ek, "pdf"), "application/pdf")
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)


@router.post("/api/indir/avan-pdf")
def indir_avan_pdf(veri: dict = Body(...)):
    try:
        s, yanit = _avan_sonuc(veri)
        if yanit is not None:
            return yanit
        _p = _proje_kimligi(veri)
        return _indir(pdf_cikti.avan_pdf(s, _p), _dosya_adi(_p, "Avan Hesaplari", "pdf"), "application/pdf")
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)


@router.post("/api/indir/proje-dwg")
def indir_proje_dwg(veri: dict = Body(...)):
    """
    BÜTÜN PROJE  —  tek CAD dosyası.

    Kapak, ofis TİP PROJE FORMATININ antet hücresine; trafik paftası ve avan
    hesapları formatın büyük çerçevesine A4 boyutunda dizilir ( şablon yoksa
    yan yana serbest bir şerit ).  Geometri programın KENDİ PDF'lerinden
    okunur, bu yüzden CAD çıktısı paftanın birebir aynısıdır
    ( bkz. ciktilar/dxf_cikti ).
    """
    if dxf_cikti is None:
        return JSONResponse(
            {
                "hata": "HESAP HATASI: CAD çıktısı için gereken kitaplıklar kurulu değil "
                f"( {_DXF_HATA} ).  Programı kapatıp {_BASLATICI} dosyasını "
                "yeniden çalıştırın; eksik kitaplıklar kendiliğinden kurulur."
            },
            status_code=200,
        )
    try:
        paftalar = []
        kapak_verisi = veri.get("kapak") if isinstance(veri.get("kapak"), dict) else None
        if kapak_verisi:
            paftalar.append(("Kapak", kapak_cikti.pdf_baytlari(kapak_verisi)))

        #  Trafik ve avan girdileri ayrı ayrı temizlenir; ikisi de belirsiz
        #  sayı denetiminden geçer — ekran neyi reddediyorsa CAD çıktısı da
        #  reddeder, yarım bir proje dosyası teslim edilmez.
        ham = veri.get("girdiler") if isinstance(veri.get("girdiler"), dict) else {}
        trafik_ham = ham.get("trafik")
        if isinstance(trafik_ham, dict):
            g = _trafik_girdi({"girdiler": trafik_ham})
            belirsiz = _belirsiz_hata()
            if belirsiz:
                return JSONResponse({"hata": belirsiz}, status_code=200)
            paftalar.append(("Trafik", pdf_cikti.trafik_pdf(trafik.hesapla(g))))

        avan_ham = ham.get("avan")
        if isinstance(avan_ham, dict):
            a, yanit = _avan_sonuc({"girdiler": avan_ham})
            if yanit is not None:
                return yanit
            paftalar.append(("Avan", pdf_cikti.avan_pdf(a)))

        if not paftalar:
            return JSONResponse(
                {
                    "hata": "HESAP HATASI: Projede hiç sayfa yok — önce kapağı doldurun "
                    "ya da trafik / avan hesabını yapın."
                },
                status_code=200,
            )

        ad = _dosya_adi(_proje_kimligi(veri), "Avan Projesi", "zip")
        #  Pakete PROJE DOSYASI da girer:  teslim paketi ile geri dönüş
        #  noktası aynı arşivde dursun.
        kok = os.path.splitext(ad)[0]
        ekler = list(_paket_ekleri(veri, "avan"))
        paket, sebep, tasti = dxf_cikti.proje_paketi(paftalar, kok, ekler)
        yanit = _indir(paket, ad, "application/zip")
        #  Kullanıcının BİLMESİ GEREKENLER başlıkta taşınır:
        #    DXF   → DWG üretilemedi, pakette yalnız DXF var ( sebebi OKUBENI'de )
        #    TASMA → paftalar formatın çerçevesine sığmadı, taşan sayfalar var
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)


@router.post("/api/indir/kapak-pdf")
def indir_kapak_pdf(veri: dict = Body(...)):
    """Hesap motorundan bağımsız, tek sayfalık avan proje kapağı."""
    try:
        return _indir(
            kapak_cikti.pdf_baytlari(veri.get("kapak")),
            _dosya_adi(_proje_kimligi(veri), "Kapak", "pdf"),
            "application/pdf",
        )
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)
