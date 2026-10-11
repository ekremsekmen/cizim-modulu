# -*- coding: utf-8 -*-
"""
GİRİŞ GÖRÜNÜŞÜ  —  kat kapısı durak tarafından ( LiftDesigner "Giriş" gibi )

En alt durağın kapısı, kuyunun ön duvarına durak tarafından bakılarak:  duvardaki
kaba boşluk, kasa, kanatlar, eşik, kat göstergesi, kat butonu ve yuvası, kapı
ekseni, döşemenin kotu.  Ölçüler kuyunun iç yüzlerine bağlanır ( iç yüzler kesik
çizgiyle gösterilir — görünüşte duvarın gerisindedir ).

Eksenler:  x planınki ( kuyunun sol iç yüzünden;  durakta duran kişinin sağı +x ),
z durak döşemesinden yukarı.

Ölçüler LiftDesigner'ın "Giriş" görünüşünden ( kullanıcı kararı 1 Eki;
cizim/sabitler.py KAPI VE KATLAR ):  kaba boşluk kapıdan 2 × 140 geniş, 240
yüksek;  kasa dikmeleri 120, üstü kapının 220 üstünde;  eşik plakası 50;
gösterge 500 × 124, ortası kapının 100 üstünde;  buton kutusu 90 × 240, ortası
döşemeden 1.200 ve kapının kenarından 240, duvardaki yuvası 160 × 290.
Kanatlar kapı tipinin sayısında ( 2 kanatlıda ortada birleşir — LiftDesigner;
3 kanatlı teleskopik, 4 kanatlı merkezi );  elle açılan kapıda tek.

ÇİZİM KABULÜ:  kat butonu kapının açıldığı yanın KARŞISINDADIR ( kanatlar
"Sağ"a açılıyorsa solda, öbürlerinde sağda — LiftDesigner'ın örneklerinde
sağda ).
Çizilmeyenler ( kullanıcı kararı:  anlamları belli değil ):  LiftDesigner'ın
kapının yanındaki kesikli 100 mm'lik dikdörtgeni, döşemeden 2.500'deki çizgisi,
kasanın ve eşiğin bağlantı noktaları.
"""

from cizim import eleman
from cizim import dusey
from cizim import geometri
from cizim import girdi
from cizim import kesit_parcalari
from cizim import sabitler


def dogrula(g):
    return girdi.dogrula(g)


def yerlesim(g, cizim_sabitleri=None):
    """Görünüşün parçaları ( x, z kutuları ) — çizim ve ölçüler bunu okur."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    kp = g["kapi"]
    x0, DW, HH = kp["sol_pay"], kp["genislik"], kp["yukseklik"]
    x1 = x0 + DW
    xc = (x0 + x1) / 2.0
    bx0, bx1, bh = girdi.kaba_bosluk(g, S)
    tip = str(kp.get("tip") or "")
    n = girdi.kapi_tipi(tip)["kanat"]
    buton_sol = tip.endswith("Sağ")
    bx = x0 - S["buton_kapi_payi"] if buton_sol else x1 + S["buton_kapi_payi"]
    bz = S["buton_yukseklik"]
    return {
        "S": S,
        "x0": x0,
        "x1": x1,
        "xc": xc,
        "HH": HH,
        "bosluk": (bx0, 0.0, bx1, bh),
        "kasa": (x0 - S["kasa_yan"], 0.0, x1 + S["kasa_yan"], HH + S["kasa_ust"]),
        "esik": (bx0, -S["esik_kalinlik"], bx1, 0.0),
        #  Kanatlar kapı tipinin sayısında ( girdi.kapi_tipi:  2 · 3 · 4;  elle açılanda tek )
        "kanatlar": [(x0 + i * DW / n, x0 + (i + 1) * DW / n) for i in range(n)],
        "gosterge": (
            xc - S["gosterge_en"] / 2.0,
            HH + S["gosterge_yukseklik"] - S["gosterge_boy"] / 2.0,
            xc + S["gosterge_en"] / 2.0,
            HH + S["gosterge_yukseklik"] + S["gosterge_boy"] / 2.0,
        ),
        "buton_sol": buton_sol,
        "bx": bx,
        "bz": bz,
        "buton": (
            bx - S["buton_kutu_en"] / 2.0,
            bz - S["buton_kutu_boy"] / 2.0,
            bx + S["buton_kutu_en"] / 2.0,
            bz + S["buton_kutu_boy"] / 2.0,
        ),
        "yuva": (
            bx - S["buton_yuva_en"] / 2.0,
            bz - S["buton_yuva_boy"] / 2.0,
            bx + S["buton_yuva_en"] / 2.0,
            bz + S["buton_yuva_boy"] / 2.0,
        ),
    }


def _kutu(katman, k, ad, tip="dikdortgen"):
    return eleman.ad(eleman.dikdortgen(katman, k[0], k[1], k[2] - k[0], k[3] - k[1], tip=tip), ad)


def ciz(g, cizim_sabitleri=None):
    """Giriş görünüşünün elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    S, HH, x0, x1, xc = Y["S"], Y["HH"], Y["x0"], Y["x1"], Y["xc"]
    G = g["kuyu"]["genislik"]
    bo, ka, es, go, bu, yu = (Y[k] for k in ("bosluk", "kasa", "esik", "gosterge", "buton", "yuva"))
    e = []
    #  Kuyunun iç yüzleri ( duvarın gerisinde — kesik ) ve durak döşemesi
    ust = bo[3] + 600
    for x in (0.0, G):
        e.append(eleman.ad(eleman.cizgi("GIZLI", x, -300, x, ust), "kuyu_ic_yuzu"))
    sol, sag = min(0.0, bo[0], yu[0]) - 300, max(G, bo[2], yu[2]) + 300
    e.append(eleman.ad(eleman.cizgi("KUYU-DUVAR", sol, 0.0, bo[0], 0.0), "durak_dosemesi"))
    e.append(eleman.ad(eleman.cizgi("KUYU-DUVAR", bo[2], 0.0, sag, 0.0), "durak_dosemesi"))
    #  Duvardaki kaba boşluk, kasa ( iki dikme ve başlık ), eşik plakası
    e.append(_kutu("BINA", bo, "kaba_bosluk"))
    for k in ((ka[0], 0.0, x0, ka[3]), (x1, 0.0, ka[2], ka[3]), (x0, HH, x1, ka[3])):
        e.append(_kutu("KAPI", k, "kapi_kasasi"))
    e.append(_kutu("KAPI", es, "kat_esigi"))
    #  Kanatlar ( LiftDesigner:  kasadan ve eşikten 5 mm )
    for a, b in Y["kanatlar"]:
        e.append(_kutu("KAPI", (a, 5.0, b, HH - 5.0), "kat_kanadi"))
    #  Kat göstergesi, kat butonu ( kutu + buton ) ve duvardaki yuvası ( kesik )
    e.append(_kutu("PANO", go, "kat_gostergesi"))
    e.append(_kutu("GIZLI", yu, "buton_yuvasi"))
    e.append(_kutu("PANO", bu, "kat_butonu"))
    d = min(S["buton_kutu_en"], S["buton_kutu_boy"]) * 0.35
    e.append(
        _kutu("PANO", (Y["bx"] - d / 2.0, Y["bz"] - d / 2.0, Y["bx"] + d / 2.0, Y["bz"] + d / 2.0), "buton")
    )
    #  Kapı ekseni ve döşemenin kotu
    e.append(eleman.ad(eleman.cizgi("EKSEN", xc, -300, xc, ust, tip="eksen"), "kapi_ekseni"))
    kesit_parcalari.kot_isareti(e, xc + 150, 0.0, dusey._kot(0.0), 1.0)

    O = eleman.olcu
    #  Alt:  kuyunun iç yüzlerinden kaba boşluğa ( LiftDesigner 470 · 1.180 · 350 ),
    #  kapının net genişliği
    alt1, alt2 = es[1] - 250, es[1] - 470
    e.append(O("yatay", (x0, 0), (x1, 0), alt1, f"KAPI {x1 - x0:g}"))
    e += [
        O("yatay", (a, 0), (b, 0), alt2, None)
        for a, b in ((0.0, bo[0]), (bo[0], bo[2]), (bo[2], G))
        if b - a > 1e-6
    ]
    #  Kat butonu ( kendi yanında, yuvaya yakın ):  yuvanın yeri ve boyu
    #  ( döşemeden ), butonun ortası;  dışında kaba boşluğun yüksekliği ( sol )
    #  ve kapı · kasa başlığı · eşik ( sağ ) — buton hangi yandaysa o yanın
    #  zinciri butonun ölçülerinin dışına kayar.
    yon = -1.0 if Y["buton_sol"] else 1.0
    bk = (yu[0] if Y["buton_sol"] else yu[2]) + yon * 120
    bk2 = bk + yon * 200
    e += [O("dusey", (0, a), (0, b), bk, m) for a, b, m in ((0.0, yu[1], None), (yu[1], yu[3], None))]
    e.append(O("dusey", (0, 0.0), (0, Y["bz"]), bk2, f"BUTON {Y['bz']:g}"))
    s_sol = min(bo[0], bk2 if Y["buton_sol"] else bo[0]) - 250
    s_sag = max(bo[2], bk2 if not Y["buton_sol"] else bo[2]) + 250
    e.append(O("dusey", (0, 0.0), (0, bo[3]), s_sol, f"KAPI BOŞLUĞU {bo[3]:g}"))
    e += [
        O("dusey", (0, a), (0, b), s_sag, m)
        for a, b, m in ((es[1], 0.0, None), (0.0, HH, f"KAPI {HH:g}"), (HH, ka[3], None))
    ]
    #  Gösterge:  kapının üstünden ortasına ( kasanın dışında, boşluğun yanında )
    e.append(O("dusey", (0, HH), (0, (go[1] + go[3]) / 2.0), bo[0] - 110, None))
    kapi_kenari = x0 if Y["buton_sol"] else x1
    ust1 = bo[3] + 250
    e.append(O("yatay", (min(kapi_kenari, Y["bx"]), 0), (max(kapi_kenari, Y["bx"]), 0), ust1, None))
    e.append(O("yatay", (yu[0], 0), (yu[2], 0), ust1 + 220, None))
    #  Ölçü yazıları ( SVG ve DXF aynı yeri kullanır )
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri._yazilari_yerlestir(e)
    return e
