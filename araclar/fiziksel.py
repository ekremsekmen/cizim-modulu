# -*- coding: utf-8 -*-
"""FİZİKSEL TUTARLILIK — çizilen bir çizimin elemanlarında gerçekte olamayacak
durumlar ( girdi taraması — araclar/tarama.py;  17 Eki ):

  R1  beton parçaya giriyor:  kesilen betonun ( tarama ) bir parçanın biçimiyle
      ortak alanı var ( kaide ayak plakası oda duvarında )
  R2  kesitte kuyu boşluğunda beton ( oda duvarı tabliyenin altına, kuyunun
      içine iniyordu )
  R3  düşey duvarın altı boşta:  altında beton yok, lento da değil ( altında kapı
      yok )
  R4  kuyu planında kabin, karşı ağırlık ve raylar birbirine biniyor

Eskiden tarama yalnız yazıya, zincire, NaN'a bakıyordu:  yukarıdaki üç hata
( PR #26 ) çizilmiş paftada duruyordu.  Biçimi olan parçada ( parcalar ) zarfa
değil biçimin kapalı çokgenlerine bakılır."""

import math

from cizim import geometri
from cizim import kuyu_kesiti

PARCA = (
    set(geometri.PARCA_KATMANLARI)
    | {"KAPI", "AGIRLIK", "KASNAK", "KABIN", "PATEN", "BAGLANTI", "PANO", "CIVATA"}
) - {"DELIK"}
#  Bu kadar ortak alan çakışma sayılmaz ( mm² — çizgi kalınlığı, yuvarlama )
ESIK = 25.0
KESITLER = ("kuyu_kesiti_yan", "kuyu_kesiti_on")
#  Lento:  altındaki kapının üstünden bu kadar yukarıda biten duvar ( kat kapısı
#  boşluğunun üstü )
LENTO_ARALIGI = 3500.0


def alan(p):
    """Çokgenin alanı."""
    return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2.0


def kirp(p, k):
    """Çokgeni ( x0, y0, x1, y1 ) kutusuna kırpar ( Sutherland–Hodgman )."""
    x0, y0, x1, y1 = k
    for ic, kes in (
        (lambda q: q[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
        (lambda q: q[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
        (lambda q: q[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
        (lambda q: q[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1)),
    ):
        out = []
        for i in range(len(p)):
            a, b = p[i - 1], p[i]
            if ic(b):
                if not ic(a):
                    out.append(kes(a, b))
                out.append(b)
            elif ic(a):
                out.append(kes(a, b))
        p = out
        if not p:
            return []
    return p


def ortak_alan(p, k):
    """Çokgenin kutuyla ortak alanı."""
    q = kirp([tuple(a) for a in p], k)
    return alan(q) if len(q) > 2 else 0.0


def kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _kose(k):
    return [(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])]


def bicimler(el):
    """Elemanın görünen biçiminin kapalı çokgenleri:  parçanın biçimi varsa
    onun kapalı çokgenleri, yoksa dikdörtgeni;  daire 24 köşeyle."""
    if el["tip"] == "daire":
        return [
            [
                (
                    el["x"] + el["r"] * math.cos(t * math.pi / 12),
                    el["y"] + el["r"] * math.sin(t * math.pi / 12),
                )
                for t in range(24)
            ]
        ]
    if el["tip"] != "dikdortgen":
        return []
    if "bicim" in el:
        return [p["noktalar"] for p in el["bicim"] if p.get("kapali", True) and len(p["noktalar"]) > 2]
    return [_kose(kutu(el))]


def _ad(el):
    return el.get("ad") or el["katman"]


def _yuvarla(k):
    return tuple(round(v) for v in k)


def _altinda(b, k):
    """b'nin üstü k'nin altına değiyor ve yatayda örtüşüyor mu."""
    return abs(b[3] - k[1]) < 1.0 and min(b[2], k[2]) - max(b[0], k[0]) > 1.0


def sorunlar(g, c, e):
    """c çiziminin ( elemanları e ) fiziksel sorunları:  [ ileti ]."""
    out = []
    beton = [kutu(el) for el in e if el["tip"] == "tarama" and el["katman"] == "TARAMA"]
    for el in e:
        if el["katman"] in PARCA and el["tip"] in ("dikdortgen", "daire"):
            enb = max((ortak_alan(p, k) for p in bicimler(el) for k in beton), default=0.0)
            if enb > ESIK:
                out.append(f"{c}: R1 beton parçaya giriyor  {_ad(el)}  ( {enb:.0f} mm² )")
    if c in KESITLER and beton:
        D = g["kuyu"]["derinlik"] if c == "kuyu_kesiti_yan" else g["kuyu"]["genislik"]
        dip = min(k[1] for k in beton)
        taban = min(k[3] for k in beton if abs(k[1] - dip) < 1.0)
        bos = (0.0, taban, D, kuyu_kesiti.yerlesim(g)["M"]["tavan"])
        for k in beton:
            a = ortak_alan(_kose(k), bos)
            if a > ESIK:
                out.append(f"{c}: R2 kuyu boşluğunda beton  {_yuvarla(k)}  ( {a:.0f} mm² )")
        kapilar = [kutu(el) for el in e if el["katman"] == "KAPI" and el["tip"] == "dikdortgen"]
        for k in beton:
            if k[3] - k[1] <= k[2] - k[0] or abs(k[1] - dip) < 1.0:
                continue  # yatay beton ( döşeme ) ya da kuyunun tabanı
            if any(_altinda(b, k) for b in beton if b is not k):
                continue
            if any(
                k[1] - LENTO_ARALIGI < b[3] <= k[1] + 1.0 and min(b[2], k[2]) - max(b[0], k[0]) > -200.0
                for b in kapilar
            ):
                continue  # lento
            out.append(f"{c}: R3 duvarın altı boşta  {_yuvarla(k)}")
    if c == "kuyu_plani":
        ana = [el for el in e if el["katman"] in ("KABIN", "AGIRLIK", "RAY") and el["tip"] == "dikdortgen"]
        for i, a in enumerate(ana):
            for b in ana[i + 1 :]:
                if a["katman"] == b["katman"]:
                    continue
                enb = max((ortak_alan(p, kutu(b)) for p in bicimler(a)), default=0.0)
                if enb > ESIK:
                    out.append(f"{c}: R4 {_ad(a)} / {_ad(b)} biniyor ( {enb:.0f} mm² )")
    return out
