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
import os
import tempfile
import threading
from collections import OrderedDict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse


from cizim import cizimler as CZ
from cizim import geometri as CGE
from cizim import kopru as CK
from cizim import olcu_kaynagi as CO
from cizim import pafta as CPF
from cizim import sabitler as CS
from cizim import svg as CSV

router = APIRouter()


def girdiler(veri, asansorler, ortak, sonuc, proje_adi):
    """Her asansörün çizim girdisi:  [ ( g , hatalar ) ].

    Girdi hesap motorunun kurduğu gibi kurulur ( engine/uygulama/hesap.hesapla:
    varsayılanlar + girilenler, sonra tamamlama ):  çizim hesabın kullandığı
    sayıyı görür."""
    from engine.uygulama import girdi as E_UGR

    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    liste = []
    for i, a in enumerate(asansorler):
        A = E_UGR.tamamla({**E_UGR.varsayilanlar(), **ortak, **a, **pg})
        s = sonuc["asansorler"][i] if sonuc and i < len(sonuc.get("asansorler") or []) else None
        g, hata = CK.cizim_girdisi(A, s, proje_adi, i + 1)
        if g is not None:
            hata = _cizim_hatalari(g, A)
        liste.append((g if not hata else None, hata))
    return liste


def _cizim_hatalari(g, A):
    """Çizimlerin doğrulaması ( hepsi ) ve hesapla tutarlılık — ekranın
    "Çizimler kurulamadı" listesi.  Aynı hata birçok çizimde tekrarlanır
    ( hepsi kuyu planının doğrulamasından geçer );  bir kez söylenir."""
    gorulen, tek = set(), []
    for ad in CPF.sira(g):
        for h in CZ.CIZIMLER[ad][0](g):
            if h not in gorulen:
                gorulen.add(h)
                tek.append(h)
    return tek or CK.tutarlilik(g, A)


def _elemanlar(g, ad):
    """Ekrandaki çizimin eleman listesi ( çerçevesiyle ) — SVG'si ve ölçü
    kaynağı çözümlemesi AYNI listeyi okur:  ölçülerin sırası birebir tutar."""
    _dogrula, ciz, baslik = CZ.CIZIMLER[ad]
    olcek = CZ.OLCEKLER.get(ad, 20)
    baslik = CZ.plan_basligi(g, ad, baslik)
    seritler = (
        f"{g['proje']['ad']}  ·  {g['proje']['asansor']}" if g["proje"]["ad"] else g["proje"]["asansor"],
    )
    return CGE.cerceveli(ciz(g), baslik, olcek, seritler=seritler), baslik, olcek


def _svg(g, ad, onek=""):
    """onek verilirse SVG ekran içindir:  ölçüler tıklanır, desen kimlikleri
    önekli ( sayfadaki öteki çizimlerle çakışmasın )."""
    e, baslik, olcek = _elemanlar(g, ad)
    return {
        "ad": ad,
        "baslik": baslik,
        "olcek": olcek,
        "svg": CSV.yaz(e, CGE.sinir(e, 120 * olcek / 20.0), "", olcek, onek=onek, etkilesimli=bool(onek)),
    }


@router.post("/api/uygulama/cizimler")
def api_cizimler(veri: dict = Body(...)):
    """Aktif asansörün çizimleri ( SVG ) — ekrandaki önizleme için.

    Asıl çıktı "Projeyi paketle" ile inen paftadır ( DXF / DWG );  SVG aynı
    eleman listesinden çıkar ( cizim/svg.py · cizim/dxf.py )."""
    from api import uygulama as UYG
    from api.ortak import _belirsiz_hata, _proje_kimligi
    from engine.uygulama import hesap as E_UYG

    try:
        asansorler, ortak = UYG._asansor_girdileri(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"aktif": False, "hata": [belirsiz]})
        try:
            i = int(veri.get("asansor") or 0)
        except (TypeError, ValueError):
            i = 0
        i = min(max(i, 0), len(asansorler) - 1)
        s = E_UYG.hesapla_coklu(asansorler, ortak)
        g, hata = girdiler(
            veri, asansorler, ortak, s if s.get("aktif") else None, _proje_kimligi(veri)["proje_adi"]
        )[i]
        if hata:
            return JSONResponse({"aktif": False, "hata": hata})
        #  Projenin aktif olması en az bir hesabın yapıldığını söyler;
        #  bu çizimdeki kuvvetlerin durumu seçili asansöre aittir.
        return JSONResponse(
            {
                "aktif": True,
                "hesap": bool(s["asansorler"][i].get("aktif")),
                "cizimler": [_svg(g, ad, onek=f"c{n}-") for n, ad in enumerate(CPF.sira(g))],
            }
        )
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"aktif": False, "hata": [f"ÇİZİM HATASI: {e}"]})


# ══════════════════════════════════════════════════════════════════════
#  ÖLÇÜYE TIKLAMA  —  ölçünün kaynağı ve ölçüden değiştirme
# ══════════════════════════════════════════════════════════════════════
#  Ekranda bir ölçüye tıklanınca hangi girdiden geldiği söylenir;  yeni değer
#  yazılırsa O GİRDİ değiştirilir ( çizim elle değişmez — hesap ile çizim aynı
#  sayıyı kullanmaya devam eder ).  Kaynak her girdi çok az oynatılıp çizim
#  yeniden kurularak bulunur ( cizim/olcu_kaynagi.py ).

#  Oynatma adımı:  1 mm'ye denk gelen değişim;  başka birimlerde değerin binde biri.
_ADIM = {"mm": 1.0, "m": 0.001, "cm": 0.1, "°": 0.1, "adet": 1.0}
_ONBELLEK, _KILIT, _ONBELLEK_AZAMI = OrderedDict(), threading.Lock(), 8
#  Süren çözümlemeler:  ekran, fare çizimin üstüne gelince çözümlemeyi önceden
#  ister;  o bitmeden ölçüye tıklanınca aynı çözümleme ikinci kez, paralel
#  yapılıyordu ( ikisi de yarı hızda — tıklama iki kat bekliyordu ).  Şimdi
#  ikinci istek birincinin bitmesini bekler, sonucu önbellekten alır.
_SURENLER = {}


@functools.lru_cache(maxsize=1)
def _sozlesme():
    """Formun alanları ( anahtar → alan ), proje geneli olanlar, yerleşime göre gizliler."""
    from api import uygulama as UYG

    v = UYG.uygulama_alanlari()
    alan = {f["anahtar"]: f for gr in v["gruplar"] for f in gr["alanlar"]}
    return alan, frozenset(v["proje_geneli"]), v["yerlesime_gore_gizli"]


def _istek(veri):
    """Aktif asansörün tamamlanmamış girdisi — girdiler()'in kurduğunun aynısı."""
    from api import uygulama as UYG
    from api.ortak import _belirsiz_hata, _proje_kimligi
    from engine.uygulama import girdi as E_UGR

    asansorler, ortak = UYG._asansor_girdileri(veri)
    belirsiz = _belirsiz_hata()
    if belirsiz:
        raise ValueError(belirsiz)
    try:
        i = int(veri.get("asansor") or 0)
    except (TypeError, ValueError):
        i = 0
    i = min(max(i, 0), len(asansorler) - 1)
    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    return ({**E_UGR.varsayilanlar(), **ortak, **asansorler[i], **pg}, i, _proje_kimligi(veri)["proje_adi"])


def _kurucu(ham, ad, proje_adi, sira):
    """kur( degisiklik , serbest ) → çizimin ölçüleri ( ya da None ).

    degisiklik:  { ( yer , anahtar ) : değer } — yer girdi · ofis.
    serbest:  True ya da anahtar kümesi — girilmiş türetilen alanlar ( kaide,
    askı kaçıklığı … ) bırakılır, çizimden yeniden türetilir.  Çizimin girdisi
    değişmediyse tabanın listesi döner ( çözümleme o girdiyi atlar ).  Hesabın
    sonucu verilmez:  ölçüler ona bağlı değildir ( yalnız yük kutuları )."""
    from engine.uygulama import girdi as E_UGR

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
            birak = CK.CIZIMDEN if serbest is True else serbest
            for k in birak:
                if ("girdi", k) not in (degisiklik or {}) and h.get(k) is not None:
                    h[k] = None
        try:
            A = E_UGR.tamamla(h)
            g, _hata = CK.cizim_girdisi(A, None, proje_adi, sira)
            #  Çizimin kendi denetimi ( CZ.CIZIMLER[ad][0] ) tabanda ve kesikli
            #  değişimlerde ( seçim, tam sayı — düzen değişebilir ):  1 mm
            #  oynatmada ölçünün değişimi denetimden bağımsızdır ( kurulamayan
            #  girdi zaten hata verir ).  Değiştirilen değer uygulanmadan önce
            #  bütün çizimlerin denetiminden geçer ( _yeni_hatalar ).
            if g is None or (("g" not in taban or denetle) and CZ.CIZIMLER[ad][0](g)):
                return None
            if "g" in taban and g == taban["g"]:
                return taban["e"]
            #  Çerçevesiz:  çerçeve yalnız sona eleman ekler, ölçülerin sırası
            #  ekrandakiyle aynıdır ( test ) — başlığı kurmak kesitin bütün
            #  denetimini yeniden yapıyordu.
            with CGE.yalniz_olculer():
                e = CO.olculer(CZ.CIZIMLER[ad][1](g))
        except Exception:  # noqa: BLE001 — kurulamayan girdi
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
        and CK._sayi(kd.get("regulator_kaciklik"))
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
    sakli = set(gizli["mrl" if CK._mrl(A) else "daireli"])
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
                CK.etkin_deger(g, k)
                if k in CK.KURALLI
                else CK._varsayilan(A, k)
                if k in CK.ALAN
                else A.get(k)
            )
        if not CK._sayi(v):
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
    S = CS.sabitler(CK.cizim_sabitleri(ham))
    for o, c in CK.OFIS_SABITLERI.items():
        if c in okunan:
            ad.append({"kimlik": ("ofis", o), "tur": "ofis", "adim": 1.0, "deger": float(S[c])})
    return ad


def _cozumleme(veri, ad):
    """Çizimin bütün ölçülerinin kaynakları — aynı girdiyle ikinci tıklama
    önbellekten ( bir çizimin çözümlemesi bir saniye kadar sürer )."""
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


def _cozumle(ham, i, proje, ad):
    kur, bilgi = _kurucu(ham, ad, proje, i + 1)
    with CS.okunanlar() as okunan:
        if kur({}) is None:
            return None
    adaylar = _adaylar(ham, bilgi["A"], bilgi["g"], okunan)
    taban, kaynak = CO.cozumle(kur, adaylar)
    return {
        "ham": ham,
        "kur": kur,
        "taban": taban,
        "kaynak": kaynak,
        "adaylar": {a["kimlik"]: a for a in adaylar},
    }


def _dogrudan(k, deger, u):
    return abs(abs(k["egim"] or 0) - 1.0) < 1e-9 and abs(deger - u) < 0.5


def _kaynaklar(r, i):
    """Ekrana:  her kaynak adıyla, yeriyle ( asansör · proje · ofis · ürün ) ve
    değiştirilip değiştirilemeyeceğiyle.  Sıra:  ölçünün kendisi olan girdi
    ( değeri ölçüye eşit, eğimi 1 ) önce, sonra değiştirilebilenler, sonra
    yalnız gösterilenler."""
    from engine.uygulama import sabitler as E_US

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
                etiket=E_US.ETIKET.get(anahtar, (anahtar,))[0], birim="mm", yer="ofis", degistirilir=False
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
            b["anahtar"] not in CK.KURALLI,
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
        if ad not in CZ.CIZIMLER:
            return JSONResponse({"aktif": False, "hata": ["Bilinmeyen çizim."]})
        r = _cozumleme(veri, ad)
        if r is None:
            return JSONResponse({"aktif": False, "hata": ["Çizim bu girdilerle kurulamıyor."]})
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
        return JSONResponse({"aktif": False, "hata": [f"ÖLÇÜ HATASI: {e}"]})


def _yuvarla(x):
    """Kutuya yazılacak sayı:  kayan nokta kırıntısı atılır ( 2199.9999999 → 2200 )."""
    x = round(float(x), 6)
    return int(round(x)) if abs(x - round(x)) < 1e-6 else x


@router.post("/api/uygulama/olcu_degistir")
def api_olcu_degistir(veri: dict = Body(...)):
    """Ölçüyü hedef değere getirecek girdi değişikliği — çizim yeniden kurularak
    doğrulanır.  Formun kutularına yazılacak değerleri döndürür;  hesabı ve
    çizimi form kendi akışıyla yeniler."""
    from api.ortak import _belirsiz_hata, _sayi_oku

    try:
        ad = veri.get("cizim")
        if ad not in CZ.CIZIMLER:
            return JSONResponse({"aktif": False, "hata": ["Bilinmeyen çizim."]})
        r = _cozumleme(veri, ad)
        if r is None:
            return JSONResponse({"aktif": False, "hata": ["Çizim bu girdilerle kurulamıyor."]})
        i, hata = _olcu_bul(veri, r)
        if hata:
            return JSONResponse({"aktif": False, "hata": [hata]})
        anahtar = veri.get("anahtar")
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
        serbest = _en_az_serbest(r, k, aday) if k["bagli"] else False
        if bilgi["dogrudan"] and not serbest:
            #  Ölçü girdinin kendisi ( değeri eşit, eğimi 1 ):  yeni değer hedeftir.
            #  Çizimde yeniden aranmaz — "ø 240" gibi bazı ölçüler geometri
            #  değişince başka parçalara bölünür, ölçü artık ayrı görünmez.
            s = {"deger": hedef, "olcu": hedef, "dogrulandi": True}
        else:
            s = CO.coz(
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
        return JSONResponse({"aktif": False, "hata": [f"ÖLÇÜ HATASI: {e}"]})


def _en_az_serbest(r, k, aday):
    """Girdiyle birlikte bırakılması gereken EN AZ türetilen alan:  kaide
    girilmişken kuyu dibi değişirse yalnız kaide ( zincir ) — D2, Ds, α gibi
    geometriyle ilgisi olmayanlar girildiği gibi kalır."""
    girilmis = [c for c in CK.CIZIMDEN if r["ham"].get(c) is not None and c != k["kimlik"][1]]
    x = aday["deger"] + aday["adim"]
    for c in girilmis:
        if r["kur"]({k["kimlik"]: x}, serbest={c}) is not None:
            return {c}
    return set(girilmis) or True


def _bagli_degerler(r, anahtar, x, serbest):
    """Bırakılan türetilen alanların yeni değerleri — kutuya yazılır ( girilmiş
    kalırlar ):  kuyu dibi 1.500 → 1.600 olunca kaide 306 → 406."""
    from engine.uygulama import girdi as E_UGR

    alan = _sozlesme()[0]
    h = dict(r["ham"])
    h[anahtar] = x
    birak = CK.CIZIMDEN if serbest is True else serbest
    for c in birak:
        h[c] = None
    A = E_UGR.tamamla(h)
    return [
        {"anahtar": c, "etiket": alan[c]["etiket"], "eski": r["ham"][c], "deger": _yuvarla(A[c])}
        for c in birak
        if r["ham"].get(c) is not None and CK._sayi(A.get(c)) and abs(A[c] - r["ham"][c]) > 1e-9
    ]


def _yeni_hatalar(r, degisiklik):
    """Yeni değerlerle çizim kurulamayacaksa sebepleri — ekran uygulamadan
    önce sorar ( "Yine de uygula" ):  kuyu genişleyince korkuluk gerekir,
    korkuluk tavana sığmaz …"""
    from engine.uygulama import girdi as E_UGR

    h = dict(r["ham"])
    h.update({d["anahtar"]: d["deger"] for d in degisiklik})
    try:
        A = E_UGR.tamamla(h)
        g, hata = CK.cizim_girdisi(A)
        return hata if g is None else _cizim_hatalari(g, A)
    except Exception as e:  # noqa: BLE001
        return [f"ÇİZİM HATASI: {e}"]


def _tutarlilik_duzeltmeleri(r, degisiklik):
    """Yeni değerle hesabın girdisi ile çizim ayrı şey söyleyecekse ( L = DBGW,
    girilmiş D2 · Ds · α ) o girdiler de çizimdeki değere getirilir:  DBGW
    değişince yan yatak boyu da değişir — kullanıcı ikinci bir uyarıyla
    karşılaşmasın."""
    from engine.uygulama import girdi as E_UGR

    alan = _sozlesme()[0]
    h = dict(r["ham"])
    h.update({d["anahtar"]: d["deger"] for d in degisiklik})
    try:
        A = E_UGR.tamamla(h)
        g, _hata = CK.cizim_girdisi(A)
        duz = CK.tutarlilik_duzeltmeleri(g, A) if g is not None else {}
    except Exception:  # noqa: BLE001 — çizim kendi hatasını söyler
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
            or (CK._sayi(x) and CK._sayi(_sayiya(hedef)) and abs(x - _sayiya(hedef)) < 1e-9)
        ),
        None,
    )
    if v is None:
        return {"aktif": False, "hata": ["Seçeneklerden biri seçilmeli."]}
    e = r["kur"]({("girdi", anahtar): v}, denetle=True)
    j = CO.eslestir(r["taban"], e)[i] if e is not None else None
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
            d, _bilgi = CPF.birlestir(yol, gler)
            cikti = os.path.join(t, "pafta.dxf")
            d.saveas(cikti)
            with open(cikti, "rb") as f:
                return f.read()

    return islem
