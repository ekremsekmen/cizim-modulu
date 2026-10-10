# -*- coding: utf-8 -*-
"""ÇİZİMLERİN ALTIN ÇIKTISI — düzenleme ( refactor ) kalkanı.

Seçilmiş düzenlerin TAM paftası ( her çizimin bütün elemanları ve SVG'si )
dondurulur;  test_altin_cizim.py her koşuda yeniden üretip karşılaştırır.
Hesabın altın çıktısı ( hesap/testler/altin_uret.py ) gibi:  belirli
değerleri değil, kimsenin denetlemediği her şeyi ( bir çizginin kayması, bir
yazının yer değiştirmesi, bir elemanın düşmesi ) kilitler.

Girdiler programın yolundan geçer:  formun isteği → hesap → köprü → pafta
( api uçlarının yaptığı gibi ).  Çizilmeyen düzenin hata listesi dondurulur.

    .venv/bin/python -m testler.altin_cizim     → dosyayı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR.  Düzenleme sırasında
çalıştırılmaz;  yalnız kasıtlı bir çizim değişikliğinden sonra, farklar
incelenip onaylandığında çalıştırılır.
"""

import gzip
import hashlib
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _yol in (KOK, os.path.join(KOK, "hesap"), os.path.join(KOK, "ornekler"), os.path.join(KOK, "testler")):
    if _yol not in sys.path:
        sys.path.append(_yol)

from api import cizim as UC_CIZIM  # noqa: E402
from api import uygulama as UC_UYG  # noqa: E402
from cizim import geometri as CGE  # noqa: E402
from cizim import pafta as CPF  # noqa: E402
from cizim import svg as CSV  # noqa: E402
from engine.uygulama import hesap as E_UYG  # noqa: E402

import gercek_projeler as GP  # noqa: E402
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER  # noqa: E402

DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "altin_cizim.json.gz")
#  Kayan noktada işlem sırası değişince ( düzenlemede olağan ) son basamaklar
#  oynar;  karşılaştırma bu basamağa yuvarlanmış değerlerle yapılır.
BASAMAK = 6

#  Standart kabinler ( test_yerlesim_saglamligi.KABIN ile aynı:  kuyu kabinden
#  950 geniş, 450 derin )
KABIN = {
    320: (900, 1000, 800),
    450: (1000, 1250, 800),
    630: (1100, 1400, 800),
    800: (1350, 1400, 900),
    1000: (1100, 2100, 900),
    1275: (2000, 1400, 1100),
    1600: (1400, 2400, 1100),
}


def _standart(Q, yer="Sağ", mrl=True, **ek):
    """Formdan girilmiş bir standart asansör ( kapı ağırlığın tersine açılır )."""
    kg, kd, dw = KABIN[Q]
    kanat = " 3 Kanat" if dw >= 1300 else ""
    ek.setdefault(
        "kat_kapisi_tipi",
        {"Sol": f"Teleskopik{kanat} Sağ", "Sağ": f"Teleskopik{kanat} Sol"}.get(yer, "Teleskopik Sol"),
    )
    a = dict(
        beyan_yuku=Q,
        kabin_genisligi=kg,
        kabin_derinligi=kd,
        kapi_genisligi=dw,
        kuyu_genisligi=kg + 950,
        kuyu_derinligi=kd + 450,
        agirlik_yeri=yer,
        **ek,
    )
    pg = {"mk_yok": mrl}
    if not mrl:
        pg.update(mk_uzunluk=max(3800, kd + 2000), mk_genislik=max(2600, kg + 1200))
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def _arka(Q, mrl=True):
    """Arkadaki ağırlıkla 2:1 ( kabin üstünde çapraz kasnaklar ):  kuyu kabinden
    700 derin;  makine dairesizde makine bina yapısında, son kat 5.000."""
    ek = {"aski_duzeni": "Kabin üstü"}
    if mrl:
        ek.update(makine_raya_biniyor="Bina yapısına", son_kat_yuksekligi=5000)
    v = _standart(Q, "Arka", mrl, **ek)
    v["asansorler"][0]["kuyu_derinligi"] = KABIN[Q][1] + 700
    return v


def _ornek(md):
    return {
        "asansorler": [dict(ASANSOR_MD if md else ASANSOR)],
        "proje_geneli": dict(ORTAK_MD if md else ORTAK),
        "sabitler": dict(SABITLER),
        "asansor": 0,
    }


def _gercek(ad):
    a = dict(GP.PROJELER[ad])
    pg = {k: a.pop(k) for k in list(a) if k in UC_UYG.PROJE_GENELI_ALANLAR}
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def duzenler():
    """( ad , formun isteği ) — makine dairesiz / daireli, ağırlık sağ / sol /
    arka, askı 2:1 kabin altı / kabin üstü / 1:1, kapı tipleri, gerçek projeler
    ve reddedilen düzenler."""
    d = {"örnek makine dairesiz": _ornek(False), "örnek makine daireli": _ornek(True)}
    for ad in GP.PROJELER:
        d[f"gerçek {ad}"] = _gercek(ad)
    for Q in (450, 1000, 1600):
        for yer in ("Sağ", "Sol"):
            for mrl in (True, False):
                d[f"{Q} {yer} {'MRL' if mrl else 'MD'}"] = _standart(Q, yer, mrl)
    for Q in (800, 1275):
        for mrl in (True, False):
            d[f"{Q} Arka 2:1 {'MRL' if mrl else 'MD'}"] = _arka(Q, mrl)
    for Q in (630, 1275):
        d[f"{Q} Sağ MD 1:1"] = _standart(Q, "Sağ", False, aski_orani=1)
    for mrl in (True, False):
        d[f"800 Sağ kabin üstü {'MRL' if mrl else 'MD'}"] = _standart(
            800, "Sağ", mrl, aski_duzeni="Kabin üstü", son_kat_yuksekligi=5000
        )
    for tip in ("Manuel Sağ", "Teleskopik 3 Kanat Sol"):
        d[f"1000 Sağ MRL {tip}"] = _standart(1000, "Sağ", True, kat_kapisi_tipi=tip)
    d["1600 Arka 2:1 MD Otomatik Merkezi 4 Kanat"] = _arka(1600, False)
    d["1600 Arka 2:1 MD Otomatik Merkezi 4 Kanat"]["asansorler"][0]["kat_kapisi_tipi"] = (
        "Otomatik Merkezi 4 Kanat"
    )
    d["1000 Sağ MRL duvar boşluğunda kapı"] = _standart(1000, "Sağ", True, kapi_montaji="Duvar boşluğuna")
    #  Reddedilenler:  kanat cebi ray ara kirişine çarpar;  tavanda çömelme alanı
    #  yok;  ağırlık kabinin arkasına sığmaz
    d["1000 Sağ MRL Otomatik Merkezi ( ret )"] = _standart(
        1000, "Sağ", True, kat_kapisi_tipi="Otomatik Merkezi"
    )
    d["320 Sağ MRL ( ret )"] = _standart(320, "Sağ", True)
    v = _arka(450)
    v["asansorler"][0]["kuyu_derinligi"] = KABIN[450][1] + 450
    d["450 Arka 2:1 MRL dar kuyu ( ret )"] = v
    return d


def _yuvarla(x):
    if isinstance(x, float):
        return round(x, BASAMAK) + 0.0  # −0.0 → 0.0
    if isinstance(x, (list, tuple)):
        return [_yuvarla(v) for v in x]
    if isinstance(x, dict):
        return {k: _yuvarla(v) for k, v in x.items()}
    return x


def pafta(veri):
    """Formun isteğinden paftanın çizimleri:  { "hata": [ … ] } ya da
    { "sira": [ ad ] ( paftadaki sıra ), "cizimler": { ad: { baslik, olcek,
    elemanlar, svg ( sha256 ) } } }."""
    asansorler, ortak = UC_UYG._asansor_girdileri(veri)
    s = E_UYG.hesapla_coklu(asansorler, ortak)
    ((g, hata),) = UC_CIZIM.girdiler(veri, asansorler, ortak, s if s.get("aktif") else None, "ALTIN")
    if g is None:
        return {"hata": list(hata)}
    cizimler = {}
    for ad, baslik, olcek, e in CPF.cizim_listesi(g):
        svg = CSV.yaz(e, CGE.sinir(e), baslik, olcek)
        cizimler[ad] = {
            "baslik": baslik,
            "olcek": olcek,
            "elemanlar": _yuvarla(json.loads(json.dumps(e, default=str))),
            "svg": hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        }
    return {"sira": list(cizimler), "cizimler": cizimler}


def uret():
    return {ad: pafta(v) for ad, v in duzenler().items()}


def yaz(kayit, dosya=DOSYA):
    ham = json.dumps(kayit, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    #  mtime=0:  aynı içerik aynı baytları üretsin ( yeniden üretim diff'i temiz )
    with open(dosya, "wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as z:
            z.write(ham.encode("utf-8"))


def oku(dosya=DOSYA):
    with gzip.open(dosya, "rt", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    k = uret()
    yaz(k)
    cizilen = sum(1 for v in k.values() if "cizimler" in v)
    print(
        f"  {os.path.basename(DOSYA)}:  {len(k)} düzen ( {cizilen} çizildi, "
        f"{len(k) - cizilen} ret )  ·  {os.path.getsize(DOSYA) / 1024:.0f} KB"
    )
