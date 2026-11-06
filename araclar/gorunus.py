# -*- coding: utf-8 -*-
"""GÖRÜNÜŞLER ARASI TUTARLILIK — aynı parça her görünüşte aynı yerde mi
( 6 Kas çizim denetimi:  cikti/devir/CIZIM_DENETIMI_PLANI.md, 0. adım ).

Aynı adlı ( parca_adlari ile Türkçeye çevrilmiş — "kabin_ray" ve "kabin_rayi"
aynı parça ) her parçanın:
  · planlardaki ( kuyu planı, kuyu dibi, kabin üstü, kuyu üstü ) yeri ile A-A
    ( bakış ekseni u = y ) ve B-B ( u = G − x, arkadan bakış ) kesitlerindeki
    yeri — kesitteki her örnek planda o adlı parçaların birleşiminin içinde;
  · sabit parçaların ( raylar, tamponlar, regülatör, makine ) A-A ile B-B'deki
    kotları — kabin ve ağırlık iki kesitte ayrı konumda ( en alt / en üst durak ).
Parçanın ZARFI karşılaştırılır:  dikdörtgenin x, y, g, d — biçimi, daireleri ve
çizgileri değil ( kesitte gergi kolunun ucundaki pim kolun zarfından 6 mm taşar,
planda yalnız zarfı çizilir ).

Bilerek farklı olan:  B-B'de kat eşiği kanat ceplerinin altından da sürer
( kuyu_kesiti._on_katlar ), planda cep ayrı parçadır — ESDEGER.

26 Eki:  32 altın düzende ağırlık ve tamponlar 96 / 96;  6 Kas:  bütün adlı
parçalar, altın ve tarama ( araclar/tarama — sorun olarak ).
"""

import collections

from cizim import parca_adlari

PLANLAR = ("kuyu_plani", "kuyu_dibi", "kabin_ustu", "kuyu_ustu")
KESITLER = ("kuyu_kesiti_yan", "kuyu_kesiti_on")
SABIT = frozenset(
    (
        "Kabin rayı",
        "Karşı ağırlık rayı",
        "Kabin tamponu",
        "Karşı ağırlık tamponu",
        "Ağırlık tamponu kaidesi",
        "Regülatör",
        "Makine",
        "Tahrik kasnağı",
    )
)
#  Kesitteki parça planda bu adların birleşimiyle karşılaştırılır
ESDEGER = {("kuyu_kesiti_on", "Kat eşiği"): ("Kat eşiği", "Kanat cebi")}
#  Kıl payı ( mm, çizim birimi )
TOL = 2.0


def _adi(ad):
    return parca_adlari.ADLAR.get(ad, ad)


ZARFLAR = ("dikdortgen", "tarama", "tarama_tugla")


def parcalar(e, daireler=False):
    """{ Türkçe ad : [ zarf ( x0, y0, x1, y1 ) ] } — adlı kutular;  daireler:  adlı
    dairelerin sınırı da ( kesitte gearless makine eksen yönünden daire, öbüründe
    kutu — kotları karşılaştırılırken )."""
    out = collections.defaultdict(list)
    for el in e:
        ad = el.get("ad")
        if not ad or el.get("katman") in ("YAZI", "OLCU", "EKSEN"):
            continue
        if el["tip"] in ZARFLAR:
            out[_adi(ad)].append((el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"]))
        elif daireler and el["tip"] == "daire":
            x, y, r = el["x"], el["y"], el["r"]
            out[_adi(ad)].append((x - r, y - r, x + r, y + r))
    return out


def _birlesik(araliklar):
    """Bitişik / iç içe aralıklar tek aralık:  [ ( alt , üst ) ]."""
    out = []
    for a, b in sorted(araliklar):
        if out and a <= out[-1][1] + TOL:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _icinde(a, kume):
    return any(lo - TOL <= a[0] and a[1] <= hi + TOL for lo, hi in kume)


def kuyu_genisligi(cizimler):
    """G:  kuyu planının SW ölçüsü ( iç yüzler arası ) — yoksa None."""
    for o in cizimler.get("kuyu_plani", ()):
        if o["tip"] == "olcu" and str(o.get("metin", "")).startswith("SW"):
            return o["uzunluk"]
    return None


def sorunlar(cizimler, G=None):
    """[ ileti ] — cizimler:  { çizim adı : elemanlar };  G kuyu genişliği
    ( verilmezse kuyu planının SW ölçüsü )."""
    G = G if G is not None else kuyu_genisligi(cizimler)
    if G is None:
        return []
    plan = collections.defaultdict(list)
    for p in PLANLAR:
        for ad, ks in parcalar(cizimler.get(p, ())).items():
            plan[ad] += ks
    out = []
    cevir = {"kuyu_kesiti_yan": lambda k: (k[1], k[3]), "kuyu_kesiti_on": lambda k: (G - k[2], G - k[0])}
    for kesit in KESITLER:
        for ad, ks in parcalar(cizimler.get(kesit, ())).items():
            adlar = ESDEGER.get((kesit, ad), (ad,))
            if not any(a in plan for a in adlar):
                continue
            kume = _birlesik([cevir[kesit](k) for a in adlar for k in plan.get(a, ())])
            for k in ks:
                if not _icinde((k[0], k[2]), kume):
                    out.append(f"{kesit}: {ad} kesitte {k[0]:.0f} … {k[2]:.0f}, planda {kume[:3]}")
    a, b = (parcalar(cizimler.get(k, ()), daireler=True) for k in KESITLER)
    for ad in sorted(SABIT & set(a) & set(b)):
        kume = _birlesik([(k[1], k[3]) for k in b[ad]])
        for k in a[ad]:
            if not _icinde((k[1], k[3]), kume):
                out.append(f"A-A ↔ B-B: {ad} kotu {k[1]:.0f} … {k[3]:.0f}, B-B'de {kume[:3]}")
    return out
