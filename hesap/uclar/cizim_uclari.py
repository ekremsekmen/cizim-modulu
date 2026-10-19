# -*- coding: utf-8 -*-
"""
ÇİZİM UÇLARI  —  hesap programı ile çizim modülünün bağlantısı

Uygulama projesinin girdisi TEK YERDEN gelir:  ekrandaki form.  Hesap o
girdiyle yapılır;  çizim modülü aynı girdiden ( ve hesabın sonucundan )
cizim/kopru.py ile kendi girdisini kurar.  Hesapta olan bir ölçü çizimde
ikinci kez sorulmaz;  hesabın bilmediği ölçüler ( kuyu derinliği, durak
adedi, kabinin ve kapının kuyudaki yeri … ) formun "Çizim" grubundadır.

Çizim modülü bu klasörün bir üstündedir ( cizim/ ).
"""

import functools
import hashlib
import json
import logging
import os
import tempfile
import threading
from collections import OrderedDict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from temel import sayi_mi
from uclar.uc_ortak import hata_iletisi, hata_kaydi


from cizim import cizimler
from cizim import geometri
from cizim import istek_onbellegi
from cizim import izli
from cizim import kopru
from cizim import olcu_kaynagi
from cizim import pafta
from cizim import sabitler
from cizim import sorun
from cizim import sorunlu
from motor.uygulama import mukavemet_girdi
from cizim import svg
from uclar import uygulama_istegi
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from motor.uygulama import uygulama_sabitleri
from uclar.uc_ortak import _belirsiz_hata, _proje_kimligi
from uclar.uc_ortak import _sayi_oku

log = logging.getLogger(__name__)
router = APIRouter()


def girdiler(veri, asansorler, ortak, sonuc, proje_adi):
    """Her asansörün çizim girdisi:  [ ( g , hatalar ) ].

    Girdi hesap motorunun kurduğu gibi kurulur ( motor/uygulama/uygulama_hesabi.hesapla:
    varsayılanlar + girilenler, sonra tamamlama ):  çizim hesabın kullandığı
    sayıyı görür."""

    liste = []
    for i in range(len(asansorler)):
        g, hata = asansor_girdisi(asansorler, ortak, sonuc, proje_adi, i)
        liste.append((g if not hata else None, hata))
    return liste


def asansor_girdisi(asansorler, ortak, sonuc, proje_adi, i):
    """i. asansörün çizim girdisi ve sorunları:  ( g , hatalar ).  g, sorun
    olsa da geometri kurulabiliyorsa döner ( ekran sorunlu çizimi gösterir —
    cizim/sorunlu.py );  None ise girdi çizime hiç çevrilemedi ( köprünün
    hatası:  eksik / geçersiz alan )."""
    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    A = uygulama_girdisi.tamamla({**uygulama_girdisi.varsayilanlar(), **ortak, **asansorler[i], **pg})
    s = sonuc["asansorler"][i] if sonuc and i < len(sonuc.get("asansorler") or []) else None
    g, hata = kopru.cizim_girdisi(A, s, proje_adi, i + 1)
    if g is not None:
        hata = _cizim_hatalari(g, A)
    return g, hata


def _cizim_hatalari(g, A):
    """Çizimlerin doğrulaması ( hepsi ) ve hesapla tutarlılık — ekranın
    "Çizimler kurulamadı" listesi.  Aynı hata birçok çizimde tekrarlanır
    ( hepsi kuyu planının doğrulamasından geçer );  bir kez söylenir
    ( parçaları birleşir — cizim/sorun.py )."""
    tek = sorun.birlestir(h for ad in pafta.sira(g) for h in cizimler.CIZIMLER[ad][0](g))
    return tek or kopru.tutarlilik(g, A)


def _elemanlar(g, ad):
    """Ekrandaki çizimin eleman listesi ( çerçevesiyle ) — SVG'si ve ölçü
    kaynağı çözümlemesi AYNI listeyi okur:  ölçülerin sırası birebir tutar."""
    _dogrula, ciz, baslik = cizimler.CIZIMLER[ad]
    olcek = cizimler.OLCEKLER.get(ad, 20)
    baslik = cizimler.plan_basligi(g, ad, baslik)
    seritler = (
        f"{g['proje']['ad']}  ·  {g['proje']['asansor']}" if g["proje"]["ad"] else g["proje"]["asansor"],
    )
    e = geometri.cerceveli(ciz(g), baslik, olcek, seritler=seritler, olcekli=ad not in cizimler.OLCEKSIZ)
    return e, baslik, olcek


def _svg(g, ad, onek=""):
    """onek verilirse SVG ekran içindir:  ölçüler tıklanır, desen kimlikleri
    önekli ( sayfadaki öteki çizimlerle çakışmasın ), renkler DXF'inki —
    AutoCAD'in koyu model alanı gibi ( svg.CAD;  kullanıcı kararı 13 Eki )."""
    e, baslik, olcek = _elemanlar(g, ad)
    return {
        "ad": ad,
        "baslik": baslik,
        "olcek": olcek,
        #  Tablo ( veri tablosu ):  başlığında ve ekranın listesinde ölçek yazmaz
        "olceksiz": ad in cizimler.OLCEKSIZ,
        "svg": svg.yaz(
            e,
            geometri.sinir(e, 120 * olcek / 20.0),
            "",
            olcek,
            onek=onek,
            etkilesimli=bool(onek),
            r=svg.CAD if onek else svg.KAGIT,
        ),
    }


@router.post("/api/uygulama/cizimler")
def api_cizimler(veri: dict = Body(...)):
    """Aktif asansörün çizimleri ( SVG ) — ekrandaki önizleme için.

    Asıl çıktı "Projeyi paketle" ile inen paftadır ( DXF / DWG );  SVG aynı
    eleman listesinden çıkar ( cizim/svg.py · cizim/dxf.py )."""

    #  Yerleşimler bu istekte bir kez kurulur ( cizim/istek_onbellegi.py )
    with istek_onbellegi.etkin():
        return cizimler_yaniti(veri)


def cizimler_yaniti(veri):
    """Çizimlerin yanıtı ( önbelleği etkinleştiren api_cizimler çağırır;  test
    önbelleksizini karşılaştırır )."""
    try:
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"aktif": False, "hata": [belirsiz]})
        try:
            i = int(veri.get("asansor") or 0)
        except (TypeError, ValueError):
            i = 0
        i = min(max(i, 0), len(asansorler) - 1)
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        g, hata = asansor_girdisi(
            asansorler, ortak, s if s.get("aktif") else None, _proje_kimligi(veri)["proje_adi"], i
        )
        if g is None:
            return JSONResponse({"aktif": False, "hata": hata})
        cizimler_, kurulamayan = _ekran_cizimleri(g, hata)
        #  Projenin aktif olması en az bir hesabın yapıldığını söyler;
        #  bu çizimdeki kuvvetlerin durumu seçili asansöre aittir.
        if not hata:
            return JSONResponse(
                {"aktif": True, "hesap": bool(s["asansorler"][i].get("aktif")), "cizimler": cizimler_}
            )
        #  SORUNLU ÇİZİM:  "aktif" bugünkü anlamında kalır ( çizim uygun değil —
        #  testler ve ön yüzün denetimi reddi buradan okur );  ekran çizimleri
        #  yine alır.  kurulamayan:  sorunlu girdiyle kurulamayan çizimlerin başlıkları.
        #  sorunlar:  hata'nın yapılı hâli ( metin, ilgili parçalar, görüldüğü
        #  çizim — cizim/sorun.py );  ekran parçaları çizimde işaretler.
        return JSONResponse(
            {
                "aktif": False,
                "hata": hata,
                "sorunlar": [sorun.yapili(h) for h in hata],
                "hesap": bool(s["asansorler"][i].get("aktif")),
                "cizimler": cizimler_,
                "kurulamayan": kurulamayan,
            }
        )
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("ÇİZİM HATASI", e, ": ")]})


def _ekran_cizimleri(g, hata):
    """Ekranın çizimleri ( SVG ) ve kurulamayanların başlıkları.  Sorun varsa
    çizimler sorunlu çizim kipinde kurulur ( yerleşimler denetim hatasında
    durmaz — cizim/sorunlu.py );  yine de kurulamayan çizim atlanır, adı
    söylenir.  Sorun yoksa kip kapalıdır ve kurulamayan çizim bugünkü gibi
    isteğin hatasıdır ( uygun girdide çizim kurulamaması programın hatası )."""
    liste, kurulamayan = [], []
    with sorunlu.kip(bool(hata)):
        for n, ad in enumerate(pafta.sira(g)):
            if not hata:
                liste.append(_svg(g, ad, onek=f"c{n}-"))
                continue
            try:
                liste.append(_svg(g, ad, onek=f"c{n}-"))
            except Exception:  # sorunlu girdi:  çizim atlanır, adı söylenir
                log.debug("sorunlu girdiyle kurulamayan çizim:  %s", ad, exc_info=True)
                kurulamayan.append(cizimler.CIZIMLER[ad][2].partition("  (")[0])
    return liste, kurulamayan


# ══════════════════════════════════════════════════════════════════════
#  ÖLÇÜYE TIKLAMA  —  ölçünün kaynağı ve ölçüden değiştirme
# ══════════════════════════════════════════════════════════════════════
#  Ekranda bir ölçüye tıklanınca hangi girdiden geldiği söylenir;  yeni değer
#  yazılırsa O GİRDİ değiştirilir ( çizim elle değişmez — hesap ile çizim aynı
#  sayıyı kullanmaya devam eder ).  Kaynak çizim bir kez, girdileri izli
#  sayıya sarılarak kurulup türevden bulunur ( cizim/izli.py,
#  olcu_kaynagi.turevden );  değiştirme çizim yeniden kurularak doğrulanır.

#  Oynatma adımı:  1 mm'ye denk gelen değişim;  başka birimlerde değerin binde
#  biri ( eski yolda kaynak bulmak, değiştirirken girdinin bağlılığını denemek ).
_ADIM = {"mm": 1.0, "m": 0.001, "cm": 0.1, "°": 0.1, "adet": 1.0}
_ONBELLEK, _KILIT, _ONBELLEK_AZAMI = OrderedDict(), threading.Lock(), 8
#  Süren çözümlemeler:  aynı çizimin çözümlemesi bitmeden ikinci istek gelirse
#  ( tıklama ve hemen ardından değiştirme ) ikinci kez, paralel yapılmaz —
#  ikinci istek birincinin bitmesini bekler, sonucu önbellekten alır.
_SURENLER = {}


@functools.lru_cache(maxsize=1)
def _sozlesme():
    """Formun alanları ( anahtar → alan ), proje geneli olanlar, yerleşime göre gizliler."""

    v = uygulama_istegi.alanlar()
    alan = {f["anahtar"]: f for gr in v["gruplar"] for f in gr["alanlar"]}
    return alan, frozenset(v["proje_geneli"]), v["yerlesime_gore_gizli"]


def _istek(veri):
    """Aktif asansörün tamamlanmamış girdisi — girdiler()'in kurduğunun aynısı."""

    asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    belirsiz = _belirsiz_hata()
    if belirsiz:
        raise ValueError(belirsiz)
    try:
        i = int(veri.get("asansor") or 0)
    except (TypeError, ValueError):
        i = 0
    i = min(max(i, 0), len(asansorler) - 1)
    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    return (
        {**uygulama_girdisi.varsayilanlar(), **ortak, **asansorler[i], **pg},
        i,
        _proje_kimligi(veri)["proje_adi"],
    )


def _kurucu(ham, ad, proje_adi, sira):
    """kur( degisiklik , serbest ) → çizimin ölçüleri ( ya da None ).

    degisiklik:  { ( yer , anahtar ) : değer } — yer girdi · ofis.
    serbest:  True ya da anahtar kümesi — girilmiş türetilen alanlar ( kaide,
    askı kaçıklığı … ) bırakılır, çizimden yeniden türetilir.  Çizimin girdisi
    değişmediyse tabanın listesi döner ( çözümleme o girdiyi atlar ).  Hesabın
    sonucu verilmez:  ölçüler ona bağlı değildir ( yalnız yük kutuları )."""

    taban = {}
    secimler = {k for k, f in _sozlesme()[0].items() if f["tur"] == "secim"}

    def kur(degisiklik, serbest=False, denetle=False):
        h = dict(ham)
        if degisiklik:
            ofis = dict(h.get("_ofis") or {})
            for (yer, k), v in degisiklik.items():
                {"girdi": h, "ofis": ofis}[yer][k] = v
            h["_ofis"] = ofis
        if "g" in taban and not any(k in secimler for (_y, k) in degisiklik or {}):
            _regulatoru_tut(h, taban["g"], degisiklik or {})
        if serbest:
            birak = kopru.CIZIMDEN if serbest is True else serbest
            for k in birak:
                if ("girdi", k) not in (degisiklik or {}) and h.get(k) is not None:
                    h[k] = None
        try:
            A = uygulama_girdisi.tamamla(h)
            g, _hata = kopru.cizim_girdisi(A, None, proje_adi, sira)
            #  Çizimin kendi denetimi ( CZ.CIZIMLER[ad][0] ) tabanda ve kesikli
            #  değişimlerde ( seçim, tam sayı — düzen değişebilir ):  1 mm
            #  oynatmada ölçünün değişimi denetimden bağımsızdır ( kurulamayan
            #  girdi zaten hata verir ).  Değiştirilen değer uygulanmadan önce
            #  bütün çizimlerin denetiminden geçer ( _yeni_hatalar ).
            if g is None or (("g" not in taban or denetle) and cizimler.CIZIMLER[ad][0](g)):
                return None
            if "g" in taban and g == taban["g"]:
                return taban["e"]
            #  Çerçevesiz:  çerçeve yalnız sona eleman ekler, ölçülerin sırası
            #  ekrandakiyle aynıdır ( test ) — başlığı kurmak kesitin bütün
            #  denetimini yeniden yapıyordu.
            with geometri.yalniz_olculer():
                e = olcu_kaynagi.olculer(cizimler.CIZIMLER[ad][1](g))
        except Exception:
            log.debug("yedek değer kullanılıyor ( kurulamayan girdi )", exc_info=True)
            return None
        if "g" not in taban:
            taban.update(g=g, e=e, A=A)
        return e

    return kur, taban


def _regulatoru_tut(h, g, degisiklik):
    """Regülatörün BOŞ bırakılmış yeri ( kaçıklık, "karşı ağırlığın karşısı" )
    tabandaki çizimde bulunduğu yerde tutulur.  Program onu kuralla arar
    ( kopru._regulator_yeri:  varsayılan xs'in işaretine göre ±280, gergi
    çarpıyorsa başka yer ) — 1 mm oynatmada arama başka bir yere atlayınca
    kuyu dibinin ölçü zinciri değişiyordu:  880'lik ölçü "askı kaçıklığına
    bağlı, eğimi −180" görünüyor, değiştirmek xs'e 0,05 mm yazıyordu ( 1022 );
    her oynatmada arama baştan yapıldığı için de bir çizimin çözümlemesi 6 – 8
    saniye sürüyordu.  Seçim kutuları oynatılırken düzen yeniden kurulur,
    tutulmaz ( ağırlığın yanı değişince regülatörün yanı da kurala göre değişir )."""
    kd = g.get("kuyu_dibi") or {}
    if (
        ("girdi", "regulator_kaciklik") not in degisiklik
        and h.get("regulator_kaciklik") is None
        and sayi_mi(kd.get("regulator_kaciklik"))
    ):
        h["regulator_kaciklik"] = kd["regulator_kaciklik"]
    if (
        ("girdi", "regulator_yani") not in degisiklik
        and h.get("regulator_yani") in (None, "Karşı ağırlığın karşısı")
        and kd.get("regulator_yan")
    ):
        h["regulator_yani"] = kd["regulator_yan"]


def _adaylar(ham, A, g, okunan):
    """Oynatılacak girdiler:  formun sayı ve seçim kutuları ( yerleşime göre
    gizliler hariç ) ve ofis standardının çizim sabitleri ( tek katalog —
    yalnız çizimin okudukları:  okunan )."""
    alan, _pg, gizli = _sozlesme()
    sakli = set(gizli["mrl" if kopru.mrl_mi(A) else "daireli"])
    ad = []
    for k, f in alan.items():
        if k in sakli or f["tur"] not in ("sayi", "secim"):
            continue
        v = ham.get(k)
        if f["tur"] == "secim":
            ad.append(
                {
                    "kimlik": ("girdi", k),
                    "tur": "secim",
                    "deger": f["varsayilan"] if v is None else v,
                    "secenekler": f["secenekler"],
                }
            )
            continue
        if v is None:
            #  Boş kutu:  kuralla dolan çizim alanı ( etkin değeri çizimde ),
            #  varsayılanlı çizim alanı ( duvar 150 … ) ya da hesabın doldurduğu /
            #  çizimden türettiği değer.
            v = (
                kopru.etkin_deger(g, k)
                if k in kopru.KURALLI
                else kopru.varsayilan_deger(A, k)
                if k in kopru.ALAN
                else A.get(k)
            )
        if not sayi_mi(v):
            continue
        adim = _ADIM.get(f["birim"]) or max(abs(float(v)) * 1e-3, 1e-3)
        ad.append(
            {
                "kimlik": ("girdi", k),
                "tur": "tam" if f["birim"] == "adet" else "sayi",
                "deger": float(v),
                "adim": adim,
            }
        )
    S = sabitler.sabitler(kopru.cizim_sabitleri(ham))
    for o, c in kopru.OFIS_SABITLERI.items():
        if c in okunan:
            ad.append({"kimlik": ("ofis", o), "tur": "ofis", "adim": 1.0, "deger": float(S[c])})
    return ad


def _cozumleme(veri, ad):
    """Çizimin bütün ölçülerinin kaynakları — aynı girdiyle ikinci tıklama ve
    değiştirme önbellekten."""
    ham, i, proje = _istek(veri)
    anahtar = hashlib.sha1(
        json.dumps([ham, i, ad, proje], sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    with _KILIT:
        if anahtar in _ONBELLEK:
            _ONBELLEK.move_to_end(anahtar)
            return _ONBELLEK[anahtar]
        suren = _SURENLER.setdefault(anahtar, threading.Lock())
    with suren:
        with _KILIT:
            if anahtar in _ONBELLEK:  # beklerken bitti
                _ONBELLEK.move_to_end(anahtar)
                return _ONBELLEK[anahtar]
        try:
            r = _cozumle(ham, i, proje, ad)
            if r is not None:
                with _KILIT:
                    _ONBELLEK[anahtar] = r
                    while len(_ONBELLEK) > _ONBELLEK_AZAMI:
                        _ONBELLEK.popitem(last=False)
            return r
        finally:
            with _KILIT:
                _SURENLER.pop(anahtar, None)


def izli_cizim_girdisi(ham, proje, sira, g_taban, adaylar):
    """Çizimin girdisi ( g ), sayıları kaynaklarını taşıyarak ( cizim/izli.py ) —
    izli.izleme() içinde çağrılır;  çizim de o blokta kurulmalı ( sabitler
    izlenir ).  Sayı kutuları ve uzunluk seçimleri ( kapı genişliği ) sarılır;
    boş kalıp hesabın doldurduğu alanlara kendi kutusuna eğim eklenir
    ( izli.oz — çizim alanlarınınki köprüde ).  Regülatör tabandaki yerinde
    tutulur ( _regulatoru_tut — sayı oynatmada olduğu gibi ).  Kategori
    seçimleri ( askı oranı 2 → "2.0:1" yazardı ) sarılmaz.  Kurulamazsa None."""
    alan = _sozlesme()[0]
    sar = [
        a["kimlik"][1]
        for a in adaylar
        if a["kimlik"][0] == "girdi"
        and (
            a["tur"] == "sayi" or (a["tur"] == "secim" and alan[a["kimlik"][1]]["birim"] in ("mm", "m", "cm"))
        )
    ]
    h = dict(ham)
    _regulatoru_tut(h, g_taban, {})
    for k in sar:
        h[k] = izli.girdi(h.get(k), ("girdi", k))
    A = uygulama_girdisi.tamamla(h)
    for k in sar:
        if h.get(k) is None:
            A[k] = izli.oz(A.get(k), ("girdi", k))
    g, _hata = kopru.cizim_girdisi(A, None, proje, sira)
    return g


def _izli_olculer(ham, ad, proje, sira, g_taban, adaylar):
    """Çizimin ölçüleri, uzunlukları kaynaklarını taşıyarak — çizim BİR KEZ
    kurulur ( izli_cizim_girdisi ).  Kurulamazsa None."""
    try:
        with izli.izleme():
            g = izli_cizim_girdisi(ham, proje, sira, g_taban, adaylar)
            if g is None:
                return None
            with geometri.yalniz_olculer():
                return olcu_kaynagi.olculer(cizimler.CIZIMLER[ad][1](g))
    except Exception:
        log.warning("izli kurulum yapılamadı ( %s )", ad, exc_info=True)
        return None


def _cozumle(ham, i, proje, ad):
    """Çizimin ölçüleri ve her birinin kaynakları:  taban düz kurulur ( ekranla
    aynı ölçüler ), kaynaklar izli kurulumun türevinden ( olcu_kaynagi.turevden ).
    İzli kurulum tutmazsa ( olmamalı — testte denetlenir ) eski yol:  her
    girdi oynatılıp çizim yeniden kurulur ( olcu_kaynagi.cozumle )."""
    kur, bilgi = _kurucu(ham, ad, proje, i + 1)
    with sabitler.okunanlar() as okunan:
        taban = kur({})
    if taban is None:
        return None
    adaylar = _adaylar(ham, bilgi["A"], bilgi["g"], okunan)
    e = _izli_olculer(ham, ad, proje, i + 1, bilgi["g"], adaylar)
    kategori = False  # kategori seçimleri oynatıldı mı ( _kategori_kaynaklari )
    if e is not None and [o["metin"] for o in e] == [o["metin"] for o in taban]:
        kaynak = olcu_kaynagi.turevden(e, adaylar)
    else:
        log.warning("ölçü kaynağı izli kurulumla bulunamadı ( %s ):  oynatarak", ad)
        taban, kaynak = olcu_kaynagi.cozumle(kur, adaylar)
        kategori = True
    return {
        "ham": ham,
        "kur": kur,
        "taban": taban,
        "kaynak": kaynak,
        "adaylar": {a["kimlik"]: a for a in adaylar},
        "kategori": kategori,
        "kilit": threading.Lock(),
    }


def _kategori_kaynaklari(r, i):
    """Ölçünün türevle kaynağı da kuralı da yoksa kaynağı bir KATEGORİ
    seçimidir ( ray profili → "RAY 62", yan yatak NPU'su → makine şasesi,
    sığınma tipi → kuyu dibindeki alanın ölçüleri ):  türev onu bulamaz.  O
    zaman — bir kez, çizimin bütün kaynaksız ölçüleri için — yalnız seçim ve
    tam sayı kutuları oynatılır ( olcu_kaynagi.cozumle;  ~1 – 3 sn ).  Başka
    kaynağı olan ölçüde kategori seçimi söylenmez."""
    if r["kaynak"][i] or r["taban"][i].get("kural") or r["kategori"]:
        return
    with r["kilit"]:
        if r["kategori"]:
            return
        secimler = [a for a in r["adaylar"].values() if a["tur"] in ("secim", "tam")]
        _t, fd = olcu_kaynagi.cozumle(r["kur"], secimler)
        for j, ks in enumerate(fd or []):
            if not r["kaynak"][j] and not r["taban"][j].get("kural"):
                r["kaynak"][j] = ks
        r["kategori"] = True


def _dogrudan(k, deger, u):
    return abs(abs(k["egim"] or 0) - 1.0) < 1e-9 and abs(deger - u) < 0.5


def _kaynaklar(r, i):
    """Ekrana:  her kaynak adıyla, yeriyle ( asansör · proje · ofis · ürün ) ve
    değiştirilip değiştirilemeyeceğiyle.  Sıra:  ölçünün kendisi olan girdi
    ( değeri ölçüye eşit, eğimi 1 ) önce, sonra değiştirilebilenler, sonra
    yalnız gösterilenler."""

    _kategori_kaynaklari(r, i)
    alan, pg, _gizli = _sozlesme()
    u = r["taban"][i]["uzunluk"]
    liste = []
    for k in r["kaynak"][i]:
        yer, anahtar = k["kimlik"]
        aday = r["adaylar"][k["kimlik"]]
        b = {
            "anahtar": anahtar,
            "tur": k["tur"],
            "deger": aday["deger"],
            "egim": k["egim"],
            "dogrusal": k["dogrusal"],
            "bagli": k["bagli"],
        }
        if yer == "girdi":
            f = alan[anahtar]
            b.update(etiket=f["etiket"], birim=f["birim"], yer="proje" if anahtar in pg else "asansor")
            if k["tur"] == "secim":
                #  Yalnız uzunluk seçimleri ölçüden seçilir ( kapı genişliği );
                #  askı oranı gibi kategoriler sayı olsa da yalnız gösterilir.
                sayili = k["egim"] is not None and f["birim"] in ("mm", "m", "cm")
                b.update(secenekler=list(f["secenekler"]) if sayili else None, degistirilir=sayili)
            else:
                b["degistirilir"] = k["tur"] == "sayi"
        else:
            b.update(
                etiket=uygulama_sabitleri.ETIKET.get(anahtar, (anahtar,))[0],
                birim="mm",
                yer="ofis",
                degistirilir=False,
            )
        b["dogrudan"] = yer == "girdi" and k["tur"] != "tam" and _dogrudan(k, aday["deger"], u)
        liste.append(b)
    sira = {"asansor": 0, "proje": 0, "ofis": 1}
    #  Eşitlikte kuralla dolan alanın KENDİSİ önce:  "DUVAR 200"ün kaynağı hem
    #  o duvarın kutusu hem ortak "kuyu duvarı kalınlığı" ( ikisi de değeri eşit,
    #  eğimi 1 );  önce duvarın kendisi gelir — ortak kutu değişseydi dört duvar
    #  birden değişirdi ( 2 Eki ).
    liste.sort(
        key=lambda b: (
            not b["dogrudan"],
            not b["degistirilir"],
            sira[b["yer"]],
            -abs(b["egim"] or 0),
            b["anahtar"] not in kopru.KURALLI,
        )
    )
    return liste


def _olcu_bul(veri, r):
    """İstekteki ölçü ( sırası ve ekranda görülen yazısı ) — çizim o arada
    değiştiyse yanlış ölçü değiştirilmesin."""
    try:
        i = int(veri.get("olcu"))
    except (TypeError, ValueError):
        return None, "Ölçü belirtilmedi."
    if not 0 <= i < len(r["taban"]):
        return None, "Ölçü bulunamadı — çizimler yenileniyor, yeniden tıklayın."
    if veri.get("metin") is not None and veri["metin"] != r["taban"][i]["metin"]:
        return None, "Çizim değişmiş — yeniden tıklayın."
    return i, None


@router.post("/api/uygulama/olcu")
def api_olcu(veri: dict = Body(...)):
    """Tıklanan ölçünün kaynakları."""
    try:
        ad = veri.get("cizim")
        if ad not in cizimler.CIZIMLER:
            return JSONResponse({"aktif": False, "hata": ["Bilinmeyen çizim."]})
        r = _cozumleme(veri, ad)
        if r is None:
            return JSONResponse({"aktif": False, "hata": [_cozumlenemedi(veri)]})
        i, hata = _olcu_bul(veri, r)
        if hata:
            return JSONResponse({"aktif": False, "hata": [hata]})
        o = r["taban"][i]
        return JSONResponse(
            {
                "aktif": True,
                "metin": o["metin"],
                "deger": o["uzunluk"],
                "kural": o.get("kural"),
                "kaynaklar": _kaynaklar(r, i),
            }
        )
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("ÖLÇÜ HATASI", e, ": ")]})


def _cozumlenemedi(veri):
    """Ölçü çözümlenemeyince sebep:  çizim ekranda sorunlu kurulmuş olabilir
    ( cizim/sorunlu.py ) — o zaman "kurulamıyor" yanıltır.  Sorunlu çizimde
    ölçünün kaynağı ( türev ) henüz çözülmüyor:  sorunun çaresiyle aynı
    altyapı, sonraki adımın işi."""
    try:
        ham, i, proje = _istek(veri)
        g, _hata = kopru.cizim_girdisi(uygulama_girdisi.tamamla(dict(ham)), None, proje, i + 1)
    except Exception:  # sebep bulunamazsa eski ileti
        log.debug("ölçü:  çizim girdisi kurulamadı", exc_info=True)
        g = None
    if g is not None:
        return "Çizimde sorun var — ölçünün kaynağı sorunlar giderilince gösterilir."
    return "Çizim bu girdilerle kurulamıyor."


def _yuvarla(x):
    """Kutuya yazılacak sayı:  kayan nokta kırıntısı atılır ( 2199.9999999 → 2200 )."""
    x = round(float(x), 6)
    return int(round(x)) if abs(x - round(x)) < 1e-6 else x


@router.post("/api/uygulama/olcu_degistir")
def api_olcu_degistir(veri: dict = Body(...)):
    """Ölçüyü hedef değere getirecek girdi değişikliği — çizim yeniden kurularak
    doğrulanır.  Formun kutularına yazılacak değerleri döndürür;  hesabı ve
    çizimi form kendi akışıyla yeniler."""

    try:
        ad = veri.get("cizim")
        if ad not in cizimler.CIZIMLER:
            return JSONResponse({"aktif": False, "hata": ["Bilinmeyen çizim."]})
        r = _cozumleme(veri, ad)
        if r is None:
            return JSONResponse({"aktif": False, "hata": [_cozumlenemedi(veri)]})
        i, hata = _olcu_bul(veri, r)
        if hata:
            return JSONResponse({"aktif": False, "hata": [hata]})
        anahtar = veri.get("anahtar")
        _kategori_kaynaklari(r, i)
        k = next((x for x in r["kaynak"][i] if x["kimlik"] == ("girdi", anahtar)), None)
        bilgi = next(
            (b for b in _kaynaklar(r, i) if b["anahtar"] == anahtar and b["yer"] in ("asansor", "proje")),
            None,
        )
        if k is None or not bilgi or not bilgi["degistirilir"]:
            return JSONResponse({"aktif": False, "hata": ["Bu ölçü bu girdiyle değiştirilemez."]})
        aday = r["adaylar"][k["kimlik"]]
        #  Ana formla aynı okuma ve belirsiz yazım denetimi.  Tarayıcı
        #  metni korur: "2.200" burada sessizce 2,2 mm'ye dönüşmez.
        hedef = _sayi_oku(veri.get("hedef"), "Yeni ölçü")
        if hedef is None:
            return JSONResponse({"aktif": False, "hata": [_belirsiz_hata() or "Yeni ölçü bir sayı olmalı."]})
        if hedef < 0:
            return JSONResponse({"aktif": False, "hata": ["Yeni ölçü sıfırdan küçük olamaz."]})
        if k["tur"] == "secim":
            return JSONResponse(_secimle(r, i, anahtar, hedef, bilgi))
        #  Türev girdinin tek başına değişip değişemeyeceğini söylemez:  çizim
        #  kurulamıyorsa ( kaide girilmişken kuyu dibi — zincir ) bırakılması
        #  gereken türetilen alan aranır
        bagli = k["bagli"] or r["kur"]({k["kimlik"]: aday["deger"] + aday["adim"]}) is None
        serbest = _en_az_serbest(r, k, aday) if bagli else False
        if bilgi["dogrudan"] and not serbest:
            #  Ölçü girdinin kendisi ( değeri eşit, eğimi 1 ):  yeni değer hedeftir.
            #  Çizimde yeniden aranmaz — "ø 240" gibi bazı ölçüler geometri
            #  değişince başka parçalara bölünür, ölçü artık ayrı görünmez.
            s = {"deger": hedef, "olcu": hedef, "dogrulandi": True}
        else:
            s = olcu_kaynagi.coz(
                r["kur"],
                r["taban"],
                i,
                k["kimlik"],
                aday["deger"],
                k["egim"],
                hedef,
                serbest=serbest,
                dogrusal=k["dogrusal"],
            )
            if not s["dogrulandi"] and not s.get("bolundu"):
                #  Hedef doğrulanamadı ve ölçü iki parçaya bölünmüş de değil:
                #  bulunan değer ölçüyü hedefe getirmiyor ( çoğu zaman ölçü hiç
                #  değişmiyordu:  bir eşikte sıçrıyor, yalnız bir yönde değişiyor
                #  ya da sığınma alanı gibi adımla kayıyor ) — kutuya yazılmaz
                #  ( eskiden kabin genişliği 1.360 → 1.359,9995 ya da 58.430 ).
                return JSONResponse(
                    {
                        "aktif": False,
                        "hata": [
                            f"Bu ölçü «{bilgi['etiket']}» değiştirilerek {_yuvarla(hedef)} mm "
                            "yapılamıyor:  ölçü bu girdiyle düzgün değişmiyor ( bir eşikte "
                            "sıçrıyor ya da bu yönde değişmiyor ).  Başka bir girdiyle deneyin "
                            "ya da girdiyi formdan değiştirin."
                        ],
                    }
                )
        x = _yuvarla(s["deger"])
        degisiklik = [{"anahtar": anahtar, "etiket": bilgi["etiket"], "eski": aday["deger"], "deger": x}]
        if serbest:
            degisiklik += _bagli_degerler(r, anahtar, x, serbest)
        degisiklik += _tutarlilik_duzeltmeleri(r, degisiklik)
        #  FORMUN KURALI ÖLÇÜDE DE GEÇERLİ:  kutu "çizim kuruldu" deyip formun
        #  reddedeceği değeri yazıyordu ( kuyu dibi 99.999.999 → form "en çok
        #  20.000" der, hesap durur ).  Değişiklik kutuya yazılmadan reddedilir.
        red = _kural_disi(degisiklik)
        if red:
            return JSONResponse(
                {"aktif": False, "hata": [f"{red}  —  bu ölçü {_tr_sayi(hedef)} mm yapılamaz."]}
            )
        return JSONResponse(
            {
                "aktif": True,
                "degisiklikler": degisiklik,
                "hedef": hedef,
                "olcu": s["olcu"],
                "dogrulandi": s["dogrulandi"],
                "bolundu": bool(s.get("bolundu")),
                "uyarilar": _yeni_hatalar(r, degisiklik),
            }
        )
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("ÖLÇÜ HATASI", e, ": ")]})


@functools.lru_cache(maxsize=1)
def _form_kurallari():
    return mukavemet_girdi.form_kurallari()


def _tr_sayi(x):
    """Ekrandaki yazım:  binlik nokta, ondalık virgül ( on-yuz sayiYaz gibi )."""
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")


def _kural_disi(degisiklik):
    """Değişikliklerden formun kuralını çiğneyen ilki:  ileti ( yoksa None ).
    İletiler ön yüzünküyle aynı ( on-yuz/src/lib/denetim.ts alanHatasi )."""
    kurallar = _form_kurallari()
    for d in degisiklik:
        k, n = kurallar.get(d["anahtar"]), d.get("deger")
        if not k or not isinstance(n, (int, float)) or isinstance(n, bool):
            continue
        ileti = None
        if k["tam_sayi"] and not float(n).is_integer():
            ileti = "tam sayı olmalı"
        elif k["en_az"] is not None and (n < k["en_az"] if k["en_az_dahil"] else n <= k["en_az"]):
            ileti = (
                f"en az {_tr_sayi(k['en_az'])}"
                if k["en_az_dahil"]
                else f"{_tr_sayi(k['en_az'])} üstünde olmalı"
            )
        elif k["en_cok"] is not None and n > k["en_cok"]:
            ileti = f"en çok {_tr_sayi(k['en_cok'])}"
        if ileti:
            return f"{d['etiket']} {_tr_sayi(n)} olurdu:  {ileti}"
    return None


def _en_az_serbest(r, k, aday):
    """Girdiyle birlikte bırakılması gereken EN AZ türetilen alan:  kaide
    girilmişken kuyu dibi değişirse yalnız kaide ( zincir ) — D2, Ds, α gibi
    geometriyle ilgisi olmayanlar girildiği gibi kalır."""
    girilmis = [c for c in kopru.CIZIMDEN if r["ham"].get(c) is not None and c != k["kimlik"][1]]
    x = aday["deger"] + aday["adim"]
    for c in girilmis:
        if r["kur"]({k["kimlik"]: x}, serbest={c}) is not None:
            return {c}
    return set(girilmis) or True


def _bagli_degerler(r, anahtar, x, serbest):
    """Bırakılan türetilen alanların yeni değerleri — kutuya yazılır ( girilmiş
    kalırlar ):  kuyu dibi 1.500 → 1.600 olunca kaide 306 → 406."""

    alan = _sozlesme()[0]
    h = dict(r["ham"])
    h[anahtar] = x
    birak = kopru.CIZIMDEN if serbest is True else serbest
    for c in birak:
        h[c] = None
    A = uygulama_girdisi.tamamla(h)
    return [
        {"anahtar": c, "etiket": alan[c]["etiket"], "eski": r["ham"][c], "deger": _yuvarla(A[c])}
        for c in birak
        if r["ham"].get(c) is not None and sayi_mi(A.get(c)) and abs(A[c] - r["ham"][c]) > 1e-9
    ]


def _yeni_hatalar(r, degisiklik):
    """Yeni değerlerle çizim kurulamayacaksa sebepleri — ekran uygulamadan
    önce sorar ( "Yine de uygula" ):  kuyu genişleyince korkuluk gerekir,
    korkuluk tavana sığmaz …"""

    h = dict(r["ham"])
    h.update({d["anahtar"]: d["deger"] for d in degisiklik})
    try:
        A = uygulama_girdisi.tamamla(h)
        g, hata = kopru.cizim_girdisi(A)
        return hata if g is None else _cizim_hatalari(g, A)
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return [hata_iletisi("ÇİZİM HATASI", e, ": ")]


def _tutarlilik_duzeltmeleri(r, degisiklik):
    """Yeni değerle hesabın girdisi ile çizim ayrı şey söyleyecekse ( L = DBGW,
    girilmiş D2 · Ds · α ) o girdiler de çizimdeki değere getirilir:  DBGW
    değişince yan yatak boyu da değişir — kullanıcı ikinci bir uyarıyla
    karşılaşmasın."""

    alan = _sozlesme()[0]
    h = dict(r["ham"])
    h.update({d["anahtar"]: d["deger"] for d in degisiklik})
    try:
        A = uygulama_girdisi.tamamla(h)
        g, _hata = kopru.cizim_girdisi(A)
        duz = kopru.tutarlilik_duzeltmeleri(g, A) if g is not None else {}
    except Exception:
        log.debug("yedek değer kullanılıyor ( çizim kendi hatasını söyler )", exc_info=True)
        return []
    zaten = {d["anahtar"] for d in degisiklik}
    return [
        {"anahtar": k, "etiket": alan[k]["etiket"], "eski": A.get(k), "deger": _yuvarla(v)}
        for k, v in duz.items()
        if k not in zaten and k in alan
    ]


def _secimle(r, i, anahtar, hedef, bilgi):
    """Sayılı seçim kutusu ( halat çapı, kasnak çapı … ):  seçenek seçilir,
    çizim yeniden kurularak ölçü okunur."""
    sec = bilgi.get("secenekler") or []
    v = next(
        (
            x
            for x in sec
            if str(x) == str(hedef)
            or (sayi_mi(x) and sayi_mi(_sayiya(hedef)) and abs(x - _sayiya(hedef)) < 1e-9)
        ),
        None,
    )
    if v is None:
        return {"aktif": False, "hata": ["Seçeneklerden biri seçilmeli."]}
    e = r["kur"]({("girdi", anahtar): v}, denetle=True)
    j = olcu_kaynagi.eslestir(r["taban"], e)[i] if e is not None else None
    degisiklik = [
        {
            "anahtar": anahtar,
            "etiket": bilgi["etiket"],
            "eski": r["adaylar"][("girdi", anahtar)]["deger"],
            "deger": v,
        }
    ]
    degisiklik += _tutarlilik_duzeltmeleri(r, degisiklik)
    return {
        "aktif": True,
        "hedef": v,
        "olcu": e[j]["uzunluk"] if j is not None else None,
        "dogrulandi": j is not None,
        "degisiklikler": degisiklik,
        "uyarilar": _yeni_hatalar(r, degisiklik),
    }


def _sayiya(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def paftaya_ekle(gler):
    """Pakete girecek DXF'e çizimleri ekleyen son işlem ( dxf_export ).
    Hesap sayfalarının sağından başlayarak asansörler sırayla dizilir."""

    def islem(dxf):
        with tempfile.TemporaryDirectory() as t:
            yol = os.path.join(t, "hesap.dxf")
            with open(yol, "wb") as f:
                f.write(dxf)
            d, _bilgi = pafta.birlestir(yol, gler)
            cikti = os.path.join(t, "pafta.dxf")
            d.saveas(cikti)
            with open(cikti, "rb") as f:
                return f.read()

    return islem
