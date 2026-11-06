"""
PARÇANIN GİRDİLERİ — ekranda bir parçaya tıklanınca onu belirleyen girdiler
( tuvalin parça kutusu ).

Ölçü kutusunun yöntemi ( cizim_uclari._cozumle ):  çizim BİR KEZ izli kurulur
( cizim/izli.py ) ve parçanın her koordinatı hangi girdiye hangi eğimle bağlı
olduğunu taşır — girdi elle etiketlenmez.  Parça, ekrandaki ÖRNEĞİDİR ( SVG'nin
data-parca'sı "ad-n" — geometri.parca_ornekleri, svg._parca_isaretleri ):  iki
kabin rayından tıklananınki.  Sorunlu çizimde de çözülür — ekran onu sorunlu
çizim kipinde kurar ( cizim/sorunlu.py ) ve kırmızı parçanın girdisi asıl
aranandır.

Kategori seçimleri ( ray profili, askı oranı ) türevle bulunmaz:  her birini
oynatıp çizimi yeniden kurmak tıklamada saniyeler sürer ( ölçü kutusu bunu
yalnız kaynaksız ölçüde yapar — cizim_uclari._kategori_kaynaklari ).  Listede
yoklar;  yanıt bunu söyler ( NOT ), ekran kendisi yazmaz.
"""

import hashlib
import json
import logging
import threading
from collections import OrderedDict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from cizim import cizimler
from cizim import geometri
from cizim import izli
from cizim import kopru
from cizim import olcu_kaynagi
from cizim import pafta
from cizim import parca_adlari
from cizim import sabitler
from cizim import sorun
from cizim import sorunlu
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_sabitleri
from tasarim.alanlar import DURAK_KOTLARI
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar.uc_ortak import hata_iletisi, hata_kaydi

log = logging.getLogger(__name__)
router = APIRouter()

NOT = (
    "Seçim kutularının ( ray profili, askı oranı … ) etkisi bu listede yok — yalnız sayıyla değişen girdiler."
)

#  Aynı girdiyle ikinci tıklama önbellekten ( çizimin bütün parçaları bir kurulumda çözülür )
_ONBELLEK, _KILIT, _ONBELLEK_AZAMI = OrderedDict(), threading.Lock(), 8
_SURENLER = {}


def _terimler(el):
    """Elemanın koordinatları  ( boyut terimleri , yer terimleri ) — çizginin boyu
    uçlarının farkıdır:  boyuna bağlı girdi parçanın ÖLÇÜSÜNÜ, yalnız uçlarına
    bağlı olan YERİNİ değiştirir."""
    if el["tip"] == "cizgi":
        return (el["x2"] - el["x1"], el["y2"] - el["y1"]), (el["x1"], el["y1"])
    if el["tip"] == "daire":
        return (el["r"],), (el["x"], el["y"])
    return (el["g"], el["d"]), (el["x"], el["y"])


def _cozumle(ham, i, proje, ad):
    """Çizimin parça örnekleri ve her birinin kaynakları:
    { ornekler:  [ ( ad , { kimlik:  { egim , boyut } } ) ] ( ekrandaki sırayla ) ,
      adaylar:  { kimlik:  aday } }.  Kurulamazsa None."""
    sira = i + 1
    A = uygulama_girdisi.tamamla(dict(ham))
    g, _hata = kopru.cizim_girdisi(A, None, proje, sira)
    if g is None or not pafta.cizilir(g, ad):
        return None
    with sorunlu.kip(True):
        #  Çizimin okuduğu ofis sabitleri aday olur ( cizim_uclari.adaylar )
        with sabitler.okunanlar() as okunan:
            cizimler.CIZIMLER[ad][1](g)
        adaylar = cizim_uclari.adaylar(ham, A, g, okunan)
        aday = {a["kimlik"]: a for a in adaylar}
        with izli.izleme():
            gi = cizim_uclari.izli_cizim_girdisi(ham, proje, sira, g, adaylar)
            if gi is None:
                return None
            ornekler = []
            for pad, liste in geometri.parca_ornekleri(cizimler.CIZIMLER[ad][1](gi)):
                kaynak = {}
                for el in liste:
                    boyut, yer = _terimler(el)
                    for terimler, olcu in ((boyut, True), (yer, False)):
                        for x in terimler:
                            for k, eg in izli.turev(x).items():
                                if k not in aday or abs(eg * aday[k].get("adim", 1.0)) <= olcu_kaynagi.ESIK:
                                    continue
                                o = kaynak.setdefault(k, {"egim": 0.0, "boyut": False})
                                o["egim"] = max(o["egim"], abs(eg))
                                o["boyut"] = o["boyut"] or olcu
                ornekler.append((pad, kaynak))
    return {"ornekler": ornekler, "adaylar": aday}


def _cozumleme(veri, ad):
    """_cozumle önbellekle — aynı çizimin çözümlemesi sürerken gelen ikinci
    istek ikinci kez kurmaz, birincinin sonucunu bekler ( cizim_uclari ile aynı )."""
    ham, i, proje = cizim_uclari.istek(veri)
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
            if anahtar in _ONBELLEK:
                _ONBELLEK.move_to_end(anahtar)
                return _ONBELLEK[anahtar]
        try:
            try:
                r = _cozumle(ham, i, proje, ad)
            except sorun.BILINEN:
                log.debug("parçanın girdileri:  çizim kurulamadı ( %s )", ad, exc_info=True)
                r = None
            if r is not None:
                with _KILIT:
                    _ONBELLEK[anahtar] = r
                    while len(_ONBELLEK) > _ONBELLEK_AZAMI:
                        _ONBELLEK.popitem(last=False)
            return r
        finally:
            with _KILIT:
                _SURENLER.pop(anahtar, None)


def girdiler(r, n):
    """n. parça örneğinin girdileri — ölçü kutusunun kaynak satırlarıyla aynı biçim
    ( cizim_uclari._kaynaklar ):  anahtar, etiket, birim, değer, yer ( asansör ·
    proje · ofis ), değiştirilip değiştirilemeyeceği;  ayrıca etki ( boyut · yer ).
    Sıra:  değiştirilebilen önce, parçanın ölçüsünü verenler önce, asansör / proje
    ofisten önce, büyük eğim önce."""
    alan, pg, _gizli = cizim_uclari.sozlesme()
    liste = []
    for kimlik, o in r["ornekler"][n][1].items():
        yer, anahtar = kimlik
        a = r["adaylar"][kimlik]
        b = {
            "anahtar": anahtar,
            "deger": a["deger"],
            "egim": o["egim"],
            "etki": "boyut" if o["boyut"] else "yer",
        }
        if yer == "kot":
            #  Durağın kotu ( kotla giriş ):  kot tablosunda değişir
            b.update(
                anahtar=DURAK_KOTLARI,
                durak=anahtar,
                etiket=f"{anahtar + 1}. durağın kotu",
                birim="m",
                deger=a["deger"] / 1000.0,
                yer="asansor",
                degistirilir=False,
            )
        elif yer == "girdi":
            f = alan[anahtar]
            b.update(etiket=f["etiket"], birim=f["birim"], yer="proje" if anahtar in pg else "asansor")
            #  Kutu formun kutusudur:  yazılan değer forma gider ( uzunluk seçimi seçeneğiyle )
            b.update(
                degistirilir=True, **({"secenekler": list(f["secenekler"])} if a["tur"] == "secim" else {})
            )
        else:
            b.update(
                etiket=uygulama_sabitleri.ETIKET.get(anahtar, (anahtar,))[0],
                birim="mm",
                yer="ofis",
                degistirilir=False,
            )
        liste.append(b)
    sira = {"asansor": 0, "proje": 0, "ofis": 1}
    liste.sort(
        key=lambda b: (
            not b["degistirilir"],
            b["etki"] != "boyut",
            sira[b["yer"]],
            b.get("durak", -1),
            -b["egim"],
            b["etiket"],
        )
    )
    return liste


def _parca(deger):
    """ "kabin_rayi-12"  →  ( "kabin_rayi" , 12 ) — okunamazsa ( None , None )."""
    if not isinstance(deger, str):
        return None, None
    ad, _ayrac, n = deger.rpartition("-")
    if not ad or not n.isdigit():
        return None, None
    return ad, int(n)


def _hata(ileti):
    return JSONResponse({"aktif": False, "hata": [ileti]})


@router.post("/api/uygulama/parca")
def api_parca(veri: dict = Body(...)):
    """Tıklanan parçayı belirleyen girdiler.  İstek:  projenin girdisi, asansor,
    cizim ve parca ( ekrandaki örnek — data-parca "ad-n" ).  Yanıt:
    { aktif , parca , ad ( ekranda okunan ) , girdiler , not }."""
    try:
        ad = veri.get("cizim")
        if isinstance(ad, str) and ad in cizim_uclari.BIRLESIK:
            return _hata(
                "Tek kuyunun ortak çiziminde parçanın girdileri yok — asansörün kendi çiziminden tıklayın."
            )
        if not isinstance(ad, str) or ad not in cizimler.CIZIMLER:
            return _hata("Bilinmeyen çizim.")
        pad, n = _parca(veri.get("parca"))
        if pad is None:
            return _hata("Parça belirtilmedi.")
        r = _cozumleme(veri, ad)
        if r is None:
            return _hata("Çizim bu girdilerle kurulamıyor.")
        if n >= len(r["ornekler"]):
            #  Ekranın çizimi hesabın sonucuyla kurulur:  yük tablosunun ölçeksiz
            #  ray şeması gibi parçalar yalnız orada ve sondadır.
            return _hata("Bu, hesabın ölçeksiz şeması — bir girdinin ölçüsü değil.")
        if r["ornekler"][n][0] != pad:
            return _hata("Çizim değişmiş — yeniden tıklayın.")
        return JSONResponse(
            {
                "aktif": True,
                "parca": veri["parca"],
                "ad": parca_adlari.ad(pad),
                "girdiler": girdiler(r, n),
                "not": NOT,
            }
        )
    except uygulama_istegi.GecersizGirdi as e:
        return JSONResponse({"aktif": False, "hata": e.hatalar})
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("PARÇA HATASI", e, ": ")]})
