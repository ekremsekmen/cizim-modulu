# -*- coding: utf-8 -*-
"""
AVAN PROJE UÇLARI

Trafik hesabı, avan hesapları, proje kapağı ve bunların PDF / CAD
çıktıları.  Uygulama projesinden bağımsızdır.
"""

import asyncio
import json
import logging
import os
import threading
from datetime import date

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from uclar.uc_ortak import (
    hata_iletisi,
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
    baglantiyi_izle,
)
from cizim import katlar
from cizim import pafta
from tasarim import alanlar
from motor.avan import avan_hesabi
from motor.avan import avan_sabitleri
from motor.avan import kapak
from motor.avan import tablolar
from motor.avan import trafik
from ciktilar import kapak_cikti
from uclar import avan_cizimi
from uclar import avan_secici
from uclar import cizim_uclari
from ciktilar import pdf_cikti

try:
    from ciktilar import dxf_cikti
    from cizim import elektrik

    _DXF_HATA = None
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("CAD çıktısı kapalı:  %s", _e)
    dxf_cikti, elektrik, _DXF_HATA = None, None, _e

#  Paftanın PDF'i ( pypdf ister ):  yoksa paket PDF'siz iner, DXF etkilenmez
try:
    from ciktilar import pafta_pdf
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("Paftanın PDF'i kapalı:  %s", _e)
    pafta_pdf = None
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
    "md_yukseklik",
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
    #  avan çizimi ( uclar/avan_cizim_uclari.py ):  hesaba girmez, seçiciye gider
    "kuyu_derinligi",
    "tavan_dosemesi",
    #  trafik hesabının kapısı ( ekran köprüden koyar ):  avan çiziminin beyanı
    "kapi_genisligi",
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
    "kuyu_derinligi": "Kuyu derinliği",
    "tavan_dosemesi": "Tavan döşemesi kalınlığı",
    "kapi_genisligi": "Kapı genişliği",
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
    "md_yukseklik": "Makine dairesi iç yüksekliği",
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
    #  Kot tablosu doluysa kat düzeni ondan ( _kat_duzeni ):  elle yazılmış N / bodrum / h
    #  okunmaz — okunamayan eski bir yazım hesabı durdurmasın
    if not _bos_mu(ham.get(alanlar.DURAK_KOTLARI)):
        ham = {k: v for k, v in ham.items() if k not in KAT_DUZENI_ALANLARI}
    #  Red metni kutunun EKRANDAKİ adını söyler ( "hizli1" değil "⑤ Daire sayısı" ).
    g = _temiz(ham, TRAFIK_SAYISAL, etiket=trafik.girdi_etiketleri(ham.get("bina_tipi")))
    g["ek_nufus"] = _ek_nufus_oku(ham.get("ek_nufus"))
    #  Kişi sayısı YAZILMIŞ asansör tanımlıdır.  Okunabilir P aranıyordu:
    #  "8 kişi" yazılan asansör listeden sessizce düşüyor, trafik bir asansör
    #  eksik hesaplanıyordu.  Artık okunamayan P, sebebiyle reddedilir.
    #  SÜTUNUN EKRANDAKİ NUMARASI ( sira ) taşınır ( 21 Eki ):  boş sütun atılınca
    #  hesabın iletileri "ASANSÖR-1" derken ekranda 2. sütundu.
    #  Kot tablosu doluyken BÜTÜN asansörler tablonun tamamını kullanır ( kullanıcı kararı
    #  16 Kas ):  sütunun kendi durak sayısı / kat yüksekliği / bodrumu okunmaz
    tablo = not _bos_mu(ham.get(alanlar.DURAK_KOTLARI))
    liste = [
        dict(
            _temiz(
                {k: v for k, v in a.items() if not (tablo and k in ASANSOR_KAT_ALANLARI)},
                ASANSOR_SAYISAL,
                f"ASANSÖR-{i}: ",
                etiket=trafik.ASANSOR_ETIKET,
            ),
            sira=i,
        )
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
    _kat_duzeni(g, ham)
    return g


#  Trafiğin kot tablosundan türeyen girdileri ( katlar.kat_duzeni )
KAT_DUZENI_ALANLARI = ("N", "bodrum", "h")
#  Trafik sütununun ( asansörün ) kendi kat düzeni:  tablo doluyken okunmaz
ASANSOR_KAT_ALANLARI = ("durak", "h", "bodrum")


#  Trafik sütununun ( asansörün ) hizmet aralığı:  tablodaki en alt / en üst durağın sırası
HIZMET_ARALIGI = ("alt_durak", "ust_durak")


def _sira_oku(ham, ad):
    """Durak sırası ( 1'den ):  boş → None;  okunamayan → None + _RED."""
    if _bos_mu(ham):
        return None
    try:
        return int(str(ham).strip())
    except ValueError:
        _RED.append(f"{ad}:  durağın sırası yazılır ( {str(ham).strip()[:20]!r} girildi )")
        return None


def _kat_duzeni(g, ham):
    """BİNANIN KOT TABLOSU DOLUYSA trafiğin kat düzeni ONDAN ( katlar.kat_duzeni ):  N,
    bodrum ve h tablodan türer ve elle yazılanın YERİNE geçer — avan hesabı ve çizim aynı
    kotları kullanır, üçü aynı binayı hesaplar.  Tablo boşsa elle girilenler geçerlidir
    ( kotsuz hızlı tahmin ).  Motor değişmez:  aynı sayıları alır.

    HİZMET ARALIĞI ( 17 Kas ):  her sütun ( asansör ) tablonun hangi duraklarına hizmet
    ettiğini söyler ( alt_durak · ust_durak;  boş:  tablonun ucu ) — bodruma inmeyen
    asansör.  Ortak düzen aralıkların ZARFINDAN ( en alttaki alt, en üstteki üst:  motor
    ortak N'yi "en yüksek durağa çıkan asansör"e göre ister );  aralığı zarftan farklı
    sütuna kendi durak sayısı, bodrumu ve kat yüksekliği verilir ( motorun sütun alanları ).

    Türetilenler g["kat_duzeni"]'nde de durur ( yanıt:  ekran kutuları "kotlardan" diye
    gösterir;  "asansorler":  sütun sırasıyla her asansörün düzeni )."""
    kotlar = ham.get(alanlar.DURAK_KOTLARI)
    araliklar = []
    for a in g["asansorler"]:
        alt, ust = (a.pop(k, None) for k in HIZMET_ARALIGI)
        ad = f"ASANSÖR-{a.get('sira', len(araliklar) + 1)}: hizmet aralığı"
        araliklar.append((_sira_oku(alt, ad), _sira_oku(ust, ad)))
    if _bos_mu(kotlar):
        return
    giris = ham.get(alanlar.GIRIS_DURAGI)
    duzenler = []
    for a, (alt, ust) in zip(g["asansorler"], araliklar):
        d, iletiler = katlar.kat_duzeni(kotlar, giris, alt, ust)
        if iletiler:
            _RED.append((f"ASANSÖR-{a['sira']}: " if "sira" in a and (alt or ust) else "") + iletiler[0])
            return
        duzenler.append(d)
    if duzenler:
        zarf, iletiler = katlar.kat_duzeni(
            kotlar, giris, min(d["alt"] for d in duzenler), max(d["ust"] for d in duzenler)
        )
    else:
        zarf, iletiler = katlar.kat_duzeni(kotlar, giris)
    if iletiler:
        _RED.append(iletiler[0])
        return
    g.update({k: zarf[k] for k in KAT_DUZENI_ALANLARI})
    #  Sütunun kendi düzeni:  yalnız zarftan farklıysa ve birden çok sütun varsa ( tek tipte
    #  ortak düzen zaten o asansörünküdür;  motor tek yolda sütunun durak sayısını N + 1 ister )
    if len(duzenler) > 1:
        for a, d in zip(g["asansorler"], duzenler):
            if (d["alt"], d["ust"]) != (zarf["alt"], zarf["ust"]):
                a.update(durak=d["N"] + 1, bodrum=d["bodrum"], h=d["h"])
    g["kat_duzeni"] = {
        **zarf,
        "asansorler": [
            {"sira": a.get("sira", i), **d} for i, (a, d) in enumerate(zip(g["asansorler"], duzenler), 1)
        ],
    }


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


def avan_girdisi(veri):
    """Avan isteğinin okunmuş girdisi ve okuma hatası ( belirsiz / okunamayan yazım ):
    ( girdi , hata ya da None ) — avan çizimleri de aynı kapıdan okur
    ( uclar/avan_cizim_uclari.py )."""
    g = _avan_girdi(veri)
    return g, _belirsiz_hata() or None


def _trafik_koprusu(ham):
    """
    Avan tarafına gönderilen trafik özeti — dışarıdan gelen veriye güvenmeden
    yalnız beklenen alanları, sayıya çevirerek alır.
    """
    if not isinstance(ham, dict):
        return {}
    liste = []
    for a in _sozluk_listesi(ham.get("asansorler"))[:4]:
        bir = {
            "P": _sayi(a.get("P")),
            "V": _sayi(a.get("V")),
            "toplam_seyahat": _sayi(a.get("toplam_seyahat")),
        }
        #  Asansörün kendi kat düzeni ( hizmet aralığı — çoklu trafikte;  17 Kas ):  avan kartın
        #  durak sayısını binanın ortak düzeniyle değil BUNUNLA karşılaştırır
        for k in ("N", "bodrum"):
            if not _bos_mu(a.get(k)):
                bir[k] = _sayi(a.get(k))
        liste.append(bir)
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


def _kopruye_kapi(kopru, s):
    """Köprünün asansörlerine trafik hesabının KAPISI ( genişlik, tip ) ve trafik sütunu:
    avan çizimi kapıyı buradan alır ( kullanıcı kararı 14 Kas ), kapı önerisi o sütuna yazılır.
    Tek tipte bütün asansörler aynı kapıdır ( sutun None:  hepsi )."""
    o = s.get("ozet") or {}
    for j, a in enumerate(kopru.get("asansorler") or []):
        if kopru.get("tip") == "tek":
            a.update(kapi_genisligi=o.get("kapi_genisligi"), kapi_tipi=o.get("kapi_tipi"), sutun=None)
        else:
            t = (s.get("asansorler") or [])[j]
            no = t.get("no")
            a.update(
                kapi_genisligi=t.get("kapi_genisligi"),
                kapi_tipi=t.get("kapi_tipi"),
                sutun=no - 1 if isinstance(no, int) else None,
            )
    return kopru


def _kopruye_kat(kopru, duzen):
    """Köprünün asansörlerine HİZMET ARALIĞI ( "kat":  o asansörün kat düzeni — alt, ust,
    durak, seyir … ):  ekran asansörün kartına binanın kot tablosunun o aralığını verir
    ( avan hesabı ve çizim yalnız hizmet ettiği durakları görür ).  Tek tipte bütün
    asansörler aynı aralıktadır;  çokluda sütunundan ( sıra = sutun + 1 )."""
    sutunlar = {d["sira"]: d for d in duzen.get("asansorler") or []}
    ilk = next(iter(sutunlar.values()), None)
    for a in kopru.get("asansorler") or []:
        d = ilk if a.get("sutun") is None else sutunlar.get(a["sutun"] + 1)
        if d:
            a["kat"] = {k: d[k] for k in ("alt", "ust", "durak", "seyir", "giris", "N", "bodrum")}
    return kopru


def _asansor_adi(a):
    """Avan asansörünün adı ( hesap sayfasının başlığı gibi:  "1 NOLU ASANSÖR  ·  İnsan" )."""
    return "  ·  ".join(t for t in (a.get("baslik"), a.get("tanim")) if t)


def _avan_sonuc(veri):
    """Avan hesabı  —  ( sonuç , hata_yanıtı ).

    Ekran, PDF ve CAD aynı yoldan geçer:  ekran neyi reddediyorsa çıktı da
    reddeder.  Üç ret kaynağı vardır — okunamayan yazım ( API ), kullanılamayan
    değer ( motor, bkz. motor.avan.avan_hesabi.girdi_hatalari ) ve hiç asansörü
    olmayan hesap.
    """
    g = _avan_girdi(veri)
    hata = _belirsiz_hata()
    s = None if hata else avan_hesabi.hesapla(g)
    hata = hata or s.get("hata")
    #  HİÇ ASANSÖR YOK:  asansörler trafik hesabından gelir ( avan_koprusu ).  24 Eki:
    #  trafik isteği düşünce ekran asansörsüz avan gönderiyordu, paket 0 asansörlü
    #  avan hesabıyla ( yalnız topraklama ) sessizce iniyordu.
    if not hata and not s.get("asansorler"):
        hata = (
            "HESAP HATASI: Avan hesabında asansör yok — asansör adedi, kapasite ve "
            "hız trafik hesabından gelir.  Trafik hesabı yapılmadan avan hesabı "
            "hazırlanmaz."
        )
    if hata:
        return None, JSONResponse({"hata": hata}, status_code=200)
    #  Kot tablosunun türetilenleri ( ekran:  kuyu yüksekliği, seyir, kat adları )
    s["kotlar"] = avan_cizimi.kot_bilgisi(g)
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
        #  Ofis standardı formu ( gruplar · etiketler ) — uygulamanınkiyle aynı biçim
        "sabit_sema": avan_sabitleri.sema(),
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
        s["avan_koprusu"] = _kopruye_kapi(trafik.trafik_ozeti(s), s)
        #  Kat düzeni kot tablosundansa ( _kat_duzeni ):  ekran N / bodrum / h kutularını
        #  "kotlardan" diye gösterir
        if g.get("kat_duzeni"):
            s["kat_duzeni"] = g["kat_duzeni"]
            _kopruye_kat(s["avan_koprusu"], g["kat_duzeni"])
        #  Kapağın boş bırakılan asansör alanları hesaptan dolar ( ekranda
        #  gri yer tutucu olarak görünür, çıktıya o basılır ).
        s["kapak_bilgileri"] = kapak.trafikten(s)
        #  Hükmü motor kurar, ekran basar ( açılış listesi )
        s["proje_hukmu"] = trafik.proje_hukmu(s)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"hata": hata_iletisi("HESAP HATASI", e, ": ")}, status_code=200)


@router.post("/api/avan")
def api_avan(veri: dict = Body(...)):
    try:
        s, yanit = _avan_sonuc(veri)
        if yanit is not None:
            return yanit
        s["kapak_bilgileri"] = kapak.avandan(s)
        #  Hükmü motor kurar, ekran basar ( açılış listesi, adım şeridi )
        s["proje_hukmu"] = avan_hesabi.proje_hukmu(s)
        #  Paketi durduran eksik hesaplar ( 18 Kas ):  ekran "Projeyi indir"i bununla kapatır,
        #  paket ucu aynı listeyle reddeder
        s["teslim_eksikleri"] = avan_hesabi.teslim_eksikleri(s)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"hata": hata_iletisi("HESAP HATASI", e, ": ")}, status_code=200)


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
async def indir_proje_dwg_ucu(istek: Request, veri: dict = Body(...)):
    """/api/indir/proje-dwg ( 17 Kas — yayın öncesi denetim ):  paket çizimi istenen her asansörün
    seçicisini koşar ( önbellekte yoksa — avan_secici._Onbellek );  KULLANICI VAZGEÇİNCE ( bağlantı
    kapandı ) arama durur.  Eskiden paketin araması iptalsizdi:  indirme bırakılsa ya da vekil
    sunucu zaman aşımıyla kesse de sunucu asansör başına dakikalarca aramayı sürdürüyordu.
    Paket iş parçacığında kurulur;  bağlantı burada izlenir ( avan_cizim_uclari gibi )."""
    birakildi = threading.Event()
    izleyici = asyncio.create_task(baglantiyi_izle(istek, birakildi))
    try:
        return await run_in_threadpool(indir_proje_dwg, veri, birakildi.is_set)
    finally:
        birakildi.set()
        izleyici.cancel()


def _avan_reddi(a):
    """Avan hesabıyla paket inmiyorsa sebebi ( JSON yanıt ) ya da None.  Engelleyici uyarılı tasarım
    ( kabin kuyuya sığmıyor … — ekran avan PDF'ini de kapatır, 20 Eki ) ve EKSİK HESAP ( 18 Kas —
    avan_hesabi.teslim_eksikleri:  çizim, hesap sayfası ve elektrik projesi birbiriyle çelişirdi );
    seçici koşmadan — aranacak bir şey yok."""
    if a.get("engelleyici"):
        return JSONResponse({"hata": a["engelleyici"]}, status_code=200)
    eksik = avan_hesabi.teslim_eksikleri(a)
    if eksik:
        ileti = "HESAP HATASI: Avan hesapları tamamlanmadı, proje paketi inmez  —  " + "  ·  ".join(eksik)
        return JSONResponse({"hata": ileti}, status_code=200)
    return None


def _paket_cizimleri(veri, avan_ham, iptal):
    """Paketin avan çizimleri ( avan_cizimi.paket_cizimleri ):  ( gler , cizimsiz ).  Seçici korumalı
    ve önbellekli ( avan_secici.korumali ):  ekranda bulunan asansör yeniden aranmaz;  güvenlik
    süresinde bitmeyen arama "çizimi yok" notuna sebebiyle girer."""
    okunan, _hata = avan_girdisi({"girdiler": avan_ham})
    #  Paftadaki ad hesap sayfasının başlığı gibi:  "1 NOLU ASANSÖR  ·  İnsan"
    adlar = [
        "  ·  ".join(t for t in (f"{i} NOLU ASANSÖR", str((k or {}).get("tanim") or "").strip()) if t)
        for i, k in enumerate(okunan["asansorler"], 1)
    ]
    with avan_secici.korumali(iptal):
        return avan_cizimi.paket_cizimleri(okunan, _proje_kimligi(veri)["proje_adi"], adlar)


def _kapak_verisi(gelen, t, a):
    """Paketin kapağı:  ekranın gönderdiği ( hesaptan türeyen alanlarla — kapak_bilgileri );
    gönderilmemişse ya da boşsa trafik ve avan hesabından ( kapak.trafikten / avandan — ekranın
    kullandığının aynısı ).  Ne kapak ne hesap varsa boş.  18 Kas ( yayın öncesi denetim — uygulama
    paketiyle aynı sınıf ):  kapaksız pakette ofis şablonunun antet hücreleri kendi örnek
    değerleriyle ( "300 KG (4 KİŞİ)", "0,1/2 DURAK", "2,67 KW" … ) kalıyordu."""
    gelen = gelen if isinstance(gelen, dict) else {}
    if any(str(x).strip() for x in gelen.values()):
        return gelen
    return {**(kapak.trafikten(t) if t else {}), **(kapak.avandan(a) if a else {})}


def indir_proje_dwg(veri: dict, iptal=None):
    """
    BÜTÜN PROJE  —  tek CAD dosyası.  iptal:  True dönünce asansör araması durur, paket kurulmaz.

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
        #  KÂĞIT ENİ ( 19 Kas ):  paftanın dizileceği rulo — 600 / 900 mm, boşsa 600;  başka
        #  değer reddedilir ( asansör aramasından önce:  boşuna beklenmesin )
        try:
            kagit = pafta.kagit_eni(veri.get("kagit"))
        except ValueError as e:
            return JSONResponse({"hata": f"KÂĞIT ENİ:  {e}"}, status_code=200)
        paftalar = []
        t = a = None

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
            #  Hesabın kendi reddi de ( N > 30 kat, ts ≤ 0 … ):  eskiden hata
            #  kutulu trafik sayfası teslim paketine giriyordu ( 20 Eki ).
            t = trafik.hesapla(g)
            if t.get("hata"):
                return JSONResponse({"hata": t["hata"]}, status_code=200)
            paftalar.append(("Trafik", pdf_cikti.trafik_pdf(t)))

        avan_ham = ham.get("avan")
        elektrikler = []
        #  ÇİZİMLER ( 12 Kas — uclar/avan_cizimi.py ):  mimarisi girilen asansörlerin
        #  çizimleri hesap sayfalarının sağına;  çizilemeyenlerin adı nota
        gler, cizimsiz = [], []
        if isinstance(avan_ham, dict):
            a, yanit = _avan_sonuc({"girdiler": avan_ham})
            if yanit is None:
                yanit = _avan_reddi(a)
            if yanit is not None:
                return yanit
            paftalar.append(("Avan", pdf_cikti.avan_pdf(a)))
            #  ELEKTRİK PROJESİ:  her asansörün hesabından ( paftada sol altta )
            elektrikler = elektrik.pafta_sayfalari(
                [(x.get("elektrik"), _asansor_adi(x)) for x in a.get("asansorler") or [] if x.get("aktif")]
            )
            gler, cizimsiz = _paket_cizimleri(veri, avan_ham, iptal)
            if iptal is not None and iptal():  # bırakılan indirme:  kimseye gitmez
                return JSONResponse({"hata": "HESAP HATASI: İndirme bırakıldı."}, status_code=200)

        kapak_verisi = _kapak_verisi(veri.get("kapak"), t, a)
        if kapak_verisi:
            paftalar.insert(0, ("Kapak", kapak_cikti.pdf_baytlari(kapak_verisi)))
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
        #  Çizimi çıkmayan asansörler ve sebepleri pakette de yazar ( 14 Kas ):  paketi alan,
        #  ekrandaki notu görmemiş olabilir
        if cizimsiz:
            satirlar = [
                "ÇİZİMİ OLMAYAN ASANSÖRLER",
                "",
                "Bu pakette aşağıdaki asansörlerin çizimi yoktur.  Sebebi giderilince",
                "( programın Çizimler adımı ) paket yeniden indirilir.",
                "",
                *(f"  {ad}:  {sebep}" for ad, sebep in cizimsiz),
                "",
            ]
            ekler.append(("ÇİZİMİ OLMAYAN ASANSÖRLER.txt", "\r\n".join(satirlar).encode("utf-8-sig")))
        paket, sebep, tasti = dxf_cikti.proje_paketi(
            paftalar,
            kok,
            ekler,
            son_islem=cizim_uclari.paftaya_ekle(gler) if gler else None,
            pdf_islem=pafta_pdf.paket_pdfleri(paftalar, gler, elektrikler) if pafta_pdf else None,
            elektrikler=elektrikler,
            kagit=kagit,
        )
        yanit = _indir(paket, ad, "application/zip")
        #  Kullanıcının BİLMESİ GEREKENLER başlıkta taşınır:
        #    DXF   → DWG üretilemedi, pakette yalnız DXF var ( sebebi OKUBENI'de )
        #    TASMA → paftalar formatın çerçevesine sığmadı, taşan sayfalar var
        #    CIZIM → mimarisi girilen asansörlerden çizimi kurulamayan var ( pakette yok )
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else []) + (["CIZIM"] if cizimsiz else [])
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
