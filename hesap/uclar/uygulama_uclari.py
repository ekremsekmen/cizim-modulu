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

from uclar import cizim_uclari
from uclar.uc_ortak import (
    hata_kaydi,
    _BELIRSIZ,
    _RED,
    _belirsiz_hata,
    _dosya_adi,
    _indir,
    _paket_ekleri,
    _proje_kimligi,
    _sabitler_coz,
    _sayi,
    _sayi_oku,
    _uretilemedi,
    belirsiz_sayi_mi,
)
from motor.ortak.adimlar import evet_mi
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_sabitleri
from motor.uygulama import tablolar_gorunum
from motor.uygulama import uygulama_hesabi
from motor.uygulama import mukavemet_girdi
from tasarim import gorunum
from ciktilar import kapak_cikti
from ciktilar import pdf_cikti
from cizim import kopru

try:
    from ciktilar import dxf_cikti

    _DXF_HATA = None
except Exception as _e:  # noqa: BLE001
    logging.getLogger(__name__).warning("CAD çıktısı kapalı:  %s", _e)
    dxf_cikti, _DXF_HATA = None, _e
_BASLATICI = "baslat.command" if os.name != "nt" else "baslat.bat"

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/uygulama/alanlar")
def uygulama_alanlari():
    """Formun kendini üretmesi için girdi sözleşmesi.

    Mukavemet alanları + elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN
    alanları.  Ortak girdiler burada BİR KEZ geçer ( bkz. uygulama_girdi ).
    """
    veri = uygulama_girdisi.arayuz_alanlari()
    veri["ortak_kopru"] = [
        {"mukavemet": ad, "anahtar": a, "avan": av} for ad, a, av in uygulama_girdisi.ORTAK_KOPRU
    ]
    #  UYGULAMANIN KENDİ OFİS STANDARDI  —  avanınkinden ayrıdır.
    #  Ekran bu listeden kurulur;  avanın MMO/697 kuvvet sabitleri burada
    #  YOKTUR, uygulamanın mukavemet kabulleri ( σem · k1 · paylar ) ise
    #  yalnız burada vardır.
    veri["sabitler"] = {
        "varsayilan": uygulama_sabitleri.VARSAYILAN,
        "metin": list(uygulama_sabitleri.METIN),
        "gruplar": [
            {"baslik": b, "aciklama": a, "alanlar": list(al)} for b, a, al in uygulama_sabitleri.GRUPLAR
        ],
        "etiket": {k: list(v) for k, v in uygulama_sabitleri.ETIKET.items()},
    }
    #  Tablolar sekmesi:  uygulamanın kendi tabloları  ( ray · NPU · halat ·
    #  ω · kabin alanı … ).  Bunlar bugüne kadar yalnız motorun içindeydi,
    #  ekranda görünmüyordu — uygulama yapan mühendis kullandığı ray
    #  tablosuna bakamıyordu.
    veri["tablolar"] = tablolar_gorunum.arayuz_tablolari()
    veri["asansor_azami"] = uygulama_hesabi.ASANSOR_AZAMI
    return veri


def _mukavemet_girdi(veri: dict):
    """Arayüzden gelen ham metinleri sözleşmenin beklediği türlere çevirir.

    Seçim alanları LİSTEDEKİ değere eşlenir:  arayüz her şeyi metin olarak
    yollar, oysa seçeneklerin çoğu sayıdır ( 800 · 1,6 · 370 ).  Eşleme
    burada yapılmazsa motorun doğrulaması "geçersiz seçim" der.
    """
    _BELIRSIZ.clear()
    _RED.clear()
    girdiler = (veri or {}).get("girdiler")
    return _girdi_coz(girdiler, veri, _uygulanmayan((girdiler or {}) if isinstance(girdiler, dict) else {}))


def _uygulanmayan(ham):
    """Ham girdideki makine yerleşimine göre hesaba girmeyen alanlar.

    Kutu gönderilmemişse sözleşmenin varsayılanı ( makine dairesiz ) geçerlidir.
    """
    mk_yok = evet_mi(ham["mk_yok"]) if "mk_yok" in ham else uygulama_girdisi.EK_ALAN["mk_yok"][5]
    return uygulama_girdisi.uygulanmayan_alanlar(mk_yok)


def _girdi_coz(v, veri, atla=frozenset()):
    """Tek asansörün ham alanlarını türlerine çevirir.

    ``atla``:  makine yerleşimine göre hesaba girmeyen ( ekranda gizli )
    alanlar.  OKUNMAZLAR — içlerinde kalmış "4.000" ya da "-3" projeyi
    durdurmaz, çünkü kullanıcı gizli alanı göremez ve düzeltemez.

    _BELIRSIZ / _RED KASITLI OLARAK TEMİZLENMEZ:  çoklu projede her asansör
    ayrı çağrılır ve belirsiz girdiler hepsinden TOPLANMALIDIR — temizlik
    çağıranın işidir ( bkz. _asansor_girdileri ).
    """
    v = v if isinstance(v, dict) else {}
    g = {}
    #  Elektrik hesaplarının ek alanları  ( kuyu genişliği · kesitler ·
    #  temel ölçüleri · makine dairesi ).  Onay kutusu mantıksal, geri kalanı
    #  serbest sayıdır;  boş bırakılabilir — hesap eksikliği kendisi bildirir.
    for anahtar, _et, _b2, tur2, _s2, _v2 in uygulama_girdisi.EK_ALANLAR:
        if anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar]
        g[anahtar] = evet_mi(ham) if tur2 == "onay" else _sayi_oku(ham, _et)
    #  Çizim alanları:  sayılar okunur ( okunamayan yazım reddedilir ),
    #  seçimler olduğu gibi;  boş alan None — köprü kuralını uygular.
    for anahtar, _et, _b3, tur3, _s3, _v3, _gel, _bil in kopru.ALANLAR:
        if anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar]
        g[anahtar] = _sayi_oku(ham, _et) if tur3 == "sayi" else (ham if str(ham).strip() != "" else None)
    for anahtar, etiket, _b, tur, secenekler, _var in mukavemet_girdi.ALANLAR:
        if tur == "hesap" or anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar]
        if secenekler is None:
            #  Serbest sayı:  okunamayan yazım boş SAYILMAZ, sebebiyle
            #  reddedilir ( boş kabin kütlesi gibi tablodan doldurulan bir
            #  alanda "abc" eskiden tablo değerine dönüşürdü ).
            g[anahtar] = _sayi_oku(ham, etiket) if tur == "sayi" else ham
            continue
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{etiket} = {str(ham).strip()}")
        #  Seçenek listesi:  önce birebir, sonra sayısal eşleşme aranır
        if ham in secenekler:
            g[anahtar] = ham
            continue
        sayi = _sayi(ham)
        esles = next(
            (
                o
                for o in secenekler
                if isinstance(o, (int, float))
                and not isinstance(o, bool)
                and sayi is not None
                and abs(o - sayi) < 1e-9
            ),
            None,
        )
        g[anahtar] = esles if esles is not None else (ham if str(ham).strip() != "" else None)
    #  Ofis standardı ( Sabitler sekmesi ) — elektrik ve topraklama hesapları
    #  buradan besleniyor;  avan tarafındaki ile aynı biçimde alınır.
    g["_ofis"] = _sabitler_coz(
        (veri or {}).get("sabitler"),
        uygulama_sabitleri.METIN,
        lambda k: uygulama_sabitleri.ETIKET.get(k, (k,))[0],
    )
    return g


#  Makine dairesinin çizim ölçüleri de binaya aittir.
PROJE_GENELI_ALANLAR = uygulama_girdisi.PROJE_GENELI_ALANLAR + kopru.PROJE_GENELI
#  FORMDA KUTUSU OLAN alanlar okunur ( tasarım şeması ).  Çizimden ya da
#  hesaptan gelen alan istekte olsa da okunmaz — eski proje dosyalarında
#  saptırma kasnağı çapı, kaide, ray sayısı yazılı olabilir.
_FORMDA = frozenset(gorunum.anahtarlar(formda=True))


def _asansor_girdileri(veri):
    """Arayüzden gelen isteği ( 1 - 4 asansör ) çözer.

    Döner:  ( [ asansör girdi sözlükleri ] , ortak )

    GERİYE DÖNÜK:  "asansorler" yoksa eski tek asansörlük "girdiler" alanı
    kullanılır — kayıtlı eski projeler ve eski istekler çalışmaya devam eder.
    """
    _BELIRSIZ.clear()
    _RED.clear()
    veri = veri or {}
    ham = veri.get("asansorler")
    if not isinstance(ham, list) or not ham:
        ham = [veri.get("girdiler")]
    ham = [x for x in ham if isinstance(x, dict)][: uygulama_hesabi.ASANSOR_AZAMI] or [{}]

    #  Proje geneli alanlar:  ayrı gönderilmişse oradan, yoksa İLK asansörün
    #  girdisinden ( eski tek asansörlük istekler bunları orada taşıyor ).
    pg_ham = veri.get("proje_geneli")
    if isinstance(pg_ham, dict):
        #  Ayrı gönderildiyse asansörün İÇİNDEKİ kopyalar okunmaz:  eski bir
        #  proje dosyasından kalmış olabilirler, ekranda görünmezler ve motor
        #  zaten ortaktakini kullanır ( bkz. hesap.hesapla_coklu ).
        ham = [{k: v for k, v in x.items() if k not in PROJE_GENELI_ALANLAR} for x in ham]
    else:
        pg_ham = {k: ham[0][k] for k in PROJE_GENELI_ALANLAR if k in ham[0]}
    #  Makine yerleşimi proje genelidir:  gizli alanlar bütün asansörlerde aynı.
    atla = _uygulanmayan(pg_ham)
    ortak = {
        k: v for k, v in _girdi_coz(pg_ham, veri, atla).items() if k in PROJE_GENELI_ALANLAR or k == "_ofis"
    }
    return [_girdi_coz(x, veri, atla) for x in ham], ortak


def _coklu_sonuc(veri):
    """Çoklu uygulama hesabı.  ( sonuc , hata_yaniti )"""
    asansorler, ortak = _asansor_girdileri(veri)
    belirsiz = _belirsiz_hata()
    if belirsiz:
        return None, JSONResponse({"aktif": False, "hata": [belirsiz]}, status_code=200)
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
        return JSONResponse({"aktif": False, "hata": [f"HESAP HATASI: {e}"]}, status_code=200)


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
    try:
        _p = _proje_kimligi(veri)
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        paftalar = []
        #  KAPAK.  Uygulama projesinin kapağı MMO'nun ayrı kitabındadır;  ama
        #  paket bir teslim dosyasıdır ve kapaksız gitmesi için sebep yok —
        #  kapak alanları doldurulmuşsa pakete de girer.
        kapak = veri.get("kapak_sayfasi")
        if isinstance(kapak, dict) and any(str(x).strip() for x in kapak.values()):
            paftalar.append(("Kapak", kapak_cikti.pdf_bytes(kapak)))
        paftalar.append(("Uygulama Projesi", pdf_cikti.uygulama_pdf(s)))
        #  ÇİZİMLER:  her asansörün kuyu kesitleri ve planları hesap
        #  sayfalarının sağına dizilir.  Bir asansörün çizimi kurulamıyorsa
        #  paket ÇİZİMSİZ inmez — eksik bir proje teslim edilmesin, sebep
        #  söylenir ( girdi formun "Çizim" grubunda ya da hesapta düzeltilir ).
        asansorler, ortak = _asansor_girdileri(veri)
        cizim = cizim_uclari.girdiler(veri, asansorler, ortak, s, _p["proje_adi"])
        eksik = [f"{i}. asansör — {h}" for i, (_g, hata) in enumerate(cizim, 1) for h in hata]
        if eksik:
            return JSONResponse(
                {"aktif": False, "hata": "ÇİZİMLER KURULAMADI:\n· " + "\n· ".join(eksik)}, status_code=200
            )
        ad = _dosya_adi(_p, "Uygulama Projesi", "zip")
        #  Pakete PROJE DOSYASI da girer:  teslim paketi ile geri dönüş
        #  noktası aynı arşivde dursun.
        paket, sebep, tasti = dxf_cikti.proje_paketi(
            paftalar,
            os.path.splitext(ad)[0],
            list(_paket_ekleri(veri, "uygulama")),
            son_islem=cizim_uclari.paftaya_ekle([g for g, _h in cizim]),
        )
        yanit = _indir(paket, ad, "application/zip")
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return _uretilemedi(e)
