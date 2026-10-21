"""Yazı – çizgi kesişmeleri:  bir yazının ( etiket ya da ölçü yazısı ) görünen
kutusundan geçen çizgileri bulur ( girdi taraması — araclar/tarama.py ).

Yazının görünen kutusu:  büyük harf 0,72 em, en harflerin gerçek eninden
( eleman.yazi_eni );  yeri çizimin kendi yazı yerleştiricisinden
( geometri ) bağımsız bulunur — ikinci göz.
"""

import math

from cizim import eleman


def yazi_kutusu(el):
    """( metin, x0, y0, x1, y1 ) — görünen kutu:  büyük harf 0,72 em, en gerçek."""
    if el["tip"] == "yazi":
        h = el["yukseklik"]
        w = eleman.yazi_eni(el["metin"], h)
        a, b = {"sol": (0.0, w), "sag": (-w, 0.0)}.get(el.get("hiza"), (-w / 2.0, w / 2.0))
        c = 0.36 * h
        if abs(abs(el.get("aci", 0)) - 90) < 1e-6:
            ys = (el["y"] + a, el["y"] + b) if el["aci"] > 0 else (el["y"] - b, el["y"] - a)
            return (el["metin"], el["x"] - c, ys[0], el["x"] + c, ys[1])
        return (el["metin"], el["x"] + a, el["y"] - c, el["x"] + b, el["y"] + c)
    y = el["yazi"]
    h = y.get("h", eleman.OLCU_YAZI)
    w, c = eleman.yazi_eni(el["metin"], h) / 2.0, 0.36 * h
    if y.get("aci"):
        w, c = c, w
    return (el["metin"], y["x"] - w, y["y"] - c, y["x"] + w, y["y"] + c)


def parcalar(e, k=1.0):
    """( katman, ad, x1, y1, x2, y2, kaynak_id )"""
    out = []
    for i, el in enumerate(e):
        t, kat = el["tip"], el["katman"]
        if t == "dikdortgen" and "bicim" in el:
            #  Biçimi olan parçada çizilen biçimdir;  dikdörtgen yalnız mantık
            #  zarfıdır ( svg._bicim zarfı çizmez ).  21 Eki:  ağırlık konsolunun
            #  görünmeyen zarfı perde yazısına "binen" sayılıyordu.
            for p in el["bicim"]:
                n = p["noktalar"]
                for j in range(0 if p.get("kapali", True) else 1, len(n)):
                    out.append((kat, el.get("ad", ""), *n[j - 1], *n[j], i))
        elif t in ("dikdortgen", "tarama", "tarama_tugla"):
            x, y, g, d = el["x"], el["y"], el["g"], el["d"]
            for s in ((x, y, x + g, y), (x + g, y, x + g, y + d), (x + g, y + d, x, y + d), (x, y + d, x, y)):
                out.append((kat, el.get("ad", ""), *s, i))
        elif t in ("cizgi", "eksen", "ok"):
            out.append(
                (
                    kat if t != "eksen" else "EKSEN",
                    el.get("ad", ""),
                    el["x1"],
                    el["y1"],
                    el["x2"],
                    el["y2"],
                    i,
                )
            )
        elif t == "daire":
            n = 24
            for j in range(n):
                a1, a2 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
                out.append(
                    (
                        kat,
                        el.get("ad", ""),
                        el["x"] + el["r"] * math.cos(a1),
                        el["y"] + el["r"] * math.sin(a1),
                        el["x"] + el["r"] * math.cos(a2),
                        el["y"] + el["r"] * math.sin(a2),
                        i,
                    )
                )
        elif t == "olcu":
            a, b, kot = el["a"], el["b"], el["kot"]
            s = 17.5 * k
            if el["yon"] == "yatay":
                p, q = (a[0], kot), (b[0], kot)
            else:
                p, q = (kot, a[1]), (kot, b[1])
            out.append(("OLCU", "çizgi", *p, *q, i))
            for x, y in (p, q):
                out.append(("OLCU", "tik", x - s, y - s, x + s, y + s, i))
    return out


def _kesisir(s, kutu, pay):
    """Doğru parçası kutunun ( pay kadar küçültülmüş ) içinden geçiyor mu ( Liang–Barsky )."""
    x0, y0, x1, y1 = kutu[0] + pay, kutu[1] + pay, kutu[2] - pay, kutu[3] - pay
    if x0 >= x1 or y0 >= y1:
        return False
    ax, ay, bx, by = s
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


def kesismeler(e, k=1.0):
    seg = parcalar(e, k)
    out = []
    for i, el in enumerate(e):
        if el["tip"] == "yazi" or (el["tip"] == "olcu" and el.get("yazi")):
            kb = yazi_kutusu(el)
            for kat, ad, *s, j in seg:
                if j == i and ad == "çizgi":
                    continue
                if _kesisir(s, kb[1:], 2.0 * k):
                    out.append((kb[0], el["tip"], kat, ad or ("kendi tiki" if j == i else "")))
            # taramalı duvarın içi — kenar denetimiyle aynı payla ( 2·k:  21 Eki,
            # duvara 1 mm giren yazı kutusu — kâğıtta 0,05 mm — bulgu sayılıyordu )
            p = 2.0 * k
            for el2 in e:
                if el2["tip"] in ("tarama", "tarama_tugla"):
                    x, y, g, d = el2["x"], el2["y"], el2["g"], el2["d"]
                    if kb[1] + p < x + g and x < kb[3] - p and kb[2] + p < y + d and y < kb[4] - p:
                        out.append((kb[0], el["tip"], "TARAMA-İÇİ", el2.get("ad", "")))
    return out
