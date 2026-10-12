# -*- coding: utf-8 -*-
"""
KUYU DİBİ PLANI  ( kuyu tabanından yatay kesit )

Kuyu planının duvarlarını, raylarını ve konsollarını AYNEN kullanır:  yerleşim
ikinci kez hesaplanmaz, plan() elemanlarından okunur.  Kabin ve karşı ağırlık
bu kesitte yoktur ve ÇİZİLMEZ:  kesit, en alt duraktaki kabinin en alt
noktasının altından geçer ( düşey kesitlerdeki E-E ).  Kat kapısı yalnız
KESİK çizgiyle, merdivenin ve sığınma alanının yerini göstermek için
çizilir ( ofisin "View of Pit" planındaki gibi ).  Üstüne kuyu dibinde
olanlar gelir:

  · kabin ve karşı ağırlık tamponları                 m.5.8.1.1
  · karşı ağırlık perdesi                             m.5.2.5.5.1
  · regülatör gergi kasnağı
  · SIĞINMA ALANI                                     m.5.2.5.8.1 · Çizelge 4
  · MERDİVEN  ( kuyu dibi 2,5 m'yi aşmıyorsa )         m.5.2.2.4 · Ek F
  · kuyu tabanına yük aktaran noktalar ( LiftDesigner "View of Pit" gibi ):
    her rayın ve tamponun ortasına ok, çerçeveli kutuda adı ve değeri —
    FKR ( bir kabin rayı ) · FAR ( bir ağırlık rayı ) · Fkt ( kabin tamponu;
    iki tamponda her birine düşen Fkt1 ) · Fat / Fat1.  Adlar ve değerler
    hesap programının 9. bölümünden ( m.5.2.1.8 );  `kuyu_dibi.kuvvetler`
    girilmemişse kutuda yalnız ad yazar.  Kutu, noktanın çevresinde parçaya,
    ölçüye, yazıya ve başka bir kutuya binmeyen ilk yere konur.
  · RAY KONSOLUNA YATAY YÜKLER:  hesabın 7. ve 8. bölümlerindeki paten
    kuvvetlerinin bütün yük durumlarındaki EN BÜYÜĞÜ ( Fx ray ağzına yandan,
    Fy ağız doğrultusunda — EN 81-50 m.5.10.5 );  tek bir noktaya değil her
    konsola gelir, tablo ve ray şemasıyla ( referans proje "Building Forces" gibi )
"""

from temel import eleman_kutusu, kutu_merkezi, ortusur, sayi_mi
from cizim import eleman
from cizim import uslup
from cizim import geometri
from cizim import girdi
from cizim import sabitler
from cizim import parca_kotlari
from cizim import arka_aski
from cizim import hareketli

#  TS EN 81-20 Çizelge 4 — kuyu dibi sığınma alanının yatay ölçüleri ( mm ).
#  Adlar hesap programının "Kuyu dibi sığınma hacmi tipi" seçenekleriyle aynı.
SIGINMA = {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0), "Yatarak": (700.0, 1000.0)}
#  ve yüksekliği ( mm ) — dusey açıklığı bununla ölçer
SIGINMA_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0}
#  m.5.2.2.4:  kuyu dibi 2,50 m'yi aşarsa erişim kapısı gerekir;  aşmıyorsa
#  kuyu içinde merdiven yeterlidir.
MERDIVEN_AZAMI_DERINLIK = 2500.0
#  Ek F.5 b:  saklanan merdiven ile kat girişinin kenarı arası en çok 800 mm.
MERDIVEN_KAPI_AZAMI = 800.0
#  m.5.2.5.5.1 e:  ağırlık rayları ile kuyu duvarı arasındaki boşluk bundan
#  büyükse o bölge de perdeyle korunur ( mm ).
PERDE_BOSLUGU_AZAMI = 300.0
GERGI_PARCA = {"kol": "kolu", "agirlik": "ağırlığı"}
TAMPON_ADETLERI = (1, 2)
#  Hesap programının 9. bölümündeki adlar ( ozet:  FKR · FAR · Fkt · Fat, N )
KUVVETLER = ("FKR", "FAR", "Fkt", "Fat", "Fx_kabin", "Fy_kabin", "Fx_agirlik", "Fy_agirlik")
YANLAR = ("Sağ", "Sol")

_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "EKSEN")


def _birlesim(kutular):
    return (
        min(k[0] for k in kutular),
        min(k[1] for k in kutular),
        max(k[2] for k in kutular),
        max(k[3] for k in kutular),
    )


def raylari_topla(taban, ad):
    """Aynı adlı ray parçalarını ( flanş + gövde ) raylara toplar."""
    parcalar = [eleman_kutusu(el) for el in taban if el.get("ad") == ad and el["tip"] == "dikdortgen"]
    raylar = []
    for p in parcalar:
        for r in raylar:
            if ortusur(p, _birlesim(r), 1.0):
                r.append(p)
                break
        else:
            raylar.append([p])
    return sorted((_birlesim(r) for r in raylar), key=lambda k: (k[0], k[1]))


def _serbest(sira, adaylar, sinir_, engeller):
    """Adaylardan yazıları hiçbir engele binmeyen ilk ölçü sırası ( kuyunun
    içinde kalanlardan );  hepsi biniyorsa ilki."""
    uygun = [k for k in adaylar if 0 < k < sinir_] or list(adaylar[:1])
    for k in uygun:
        olculer = [dict(o) for o in sira(k) if o["uzunluk"] > 1e-6]
        geometri.yazilari_yerlestir(olculer)
        kutular = []
        for o in olculer:
            y_ = o["yazi"]
            w, h = eleman.yazi_eni(o["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
            if y_["aci"]:
                w, h = h, w
            kutular.append((y_["x"] - w, y_["y"] - h, y_["x"] + w, y_["y"] + h))
        if not any(ortusur(a, b) for a in kutular for b in engeller):
            return sira(k)
    return sira(uygun[0])


def _kuvvet_tablosu(kv, x, y):
    """RAY KONSOLUNA YATAY YÜKLER ve altında Fx / Fy yönlerini gösteren ray şeması."""
    satirlar = [
        ("RAY KONSOLUNA YATAY YÜKLER", uslup.NORMAL),
        ("( yük durumlarının en büyüğü )", uslup.NORMAL),
        (f"Kabin rayı:  Fx = {_kn(kv['Fx_kabin'])} kN  ·  Fy = {_kn(kv['Fy_kabin'])} kN", uslup.NORMAL),
        (f"Ağırlık rayı:  Fx = {_kn(kv['Fx_agirlik'])} kN  ·  Fy = {_kn(kv['Fy_agirlik'])} kN", uslup.NORMAL),
    ]
    e = []
    for i, (metin, h) in enumerate(satirlar):
        #  Başlıktan sonra yarım satır boşluk
        yy = y - 90 * i - (55 if i >= 2 else 0)
        e.append(eleman.ad(eleman.yazi(x, yy, metin, h, hiza="sol"), "kuvvet_tablosu"))
    #  Ray şeması ( planda, ölçeksiz ):  taban, ağız;  Fy ağzın doğrultusunda,
    #  Fx ağza yandan ( EN 81-50 m.5.10.5:  "Fx … by a guide shoe to the flange" )
    cx, cy = x + 330, yy - 560
    for kutu in ((cx - 150, cy, 300, 30), (cx - 20, cy + 30, 40, 220)):
        e.append(eleman.ad(eleman.dikdortgen("RAY", *kutu), "kuvvet_semasi"))
    uc = cy + 250
    e.append(eleman.ad(eleman.ok("YUK", cx, uc + 230, cx, uc + 15), "kuvvet_semasi"))
    e.append(eleman.ad(eleman.ok("YUK", cx - 280, cy + 160, cx - 25, cy + 160), "kuvvet_semasi"))
    e.append(eleman.ad(eleman.yazi(cx + 50, uc + 150, "Fy", uslup.NORMAL, hiza="sol"), "kuvvet_semasi"))
    e.append(eleman.ad(eleman.yazi(cx - 160, cy + 215, "Fx", uslup.NORMAL), "kuvvet_semasi"))
    return e


def _kn(v):
    """N → kN, iki ondalık, virgülle:  30683 → "30,68" """
    return f"{v / 1000.0:.2f}".replace(".", ",")


#  Yük kutusunun yazısı ve kutunun yazı çevresindeki payı ( mm, 1/20'de )
YUK_YAZI = uslup.NORMAL
YUK_PAY = 30.0
_YUK_DISI = ("EKSEN", "CERCEVE", "TARAMA", "KUYU-DUVAR", "KUYU-IC", "GIZLI")


def _engeller(e, siginma=True, olcu_cizgisi=True):
    """Yük kutusunun binmemesi gerekenler:  parçalar, yazılar, ölçü çizgileri ve
    yazıları ( eksenler, duvarlar, çerçeve değil ).  siginma / olcu_cizgisi
    False:  sığınma alanının yüzeyi / ölçü çizgisi engel sayılmaz ( yazıları
    sayılır )."""
    kutular, yazilar = [], []
    for el in e:
        if (
            el["katman"] in _YUK_DISI
            or el["tip"] == "tarama"
            or (not siginma and el["katman"] == "SIGINMA" and el["tip"] != "yazi")
        ):
            continue
        if el["tip"] == "olcu":
            a, b, k = el["a"], el["b"], el["kot"]
            if olcu_cizgisi:
                kutular.append(
                    (min(a[0], b[0]), k - 15, max(a[0], b[0]), k + 15)
                    if el["yon"] == "yatay"
                    else (k - 15, min(a[1], b[1]), k + 15, max(a[1], b[1]))
                )
            yazilar.append(geometri.yazi_kutusu(el))
        elif el["tip"] == "yazi":
            yazilar.append(geometri.sinir([el]))
        else:
            kutular.append(geometri.sinir([el]))
    return kutular, yazilar


def _kesisir(p, q, kutu, pay=0.0):
    """p–q doğru parçası kutuyu keser mi ( Liang–Barsky )."""
    x0, y0, x1, y1 = kutu[0] - pay, kutu[1] - pay, kutu[2] + pay, kutu[3] + pay
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for d, a, b in ((dx, p[0] - x0, x1 - p[0]), (dy, p[1] - y0, y1 - p[1])):
        if abs(d) < 1e-12:
            if a < 0 or b < 0:
                return False
            continue
        ta, tb = (-a / d, b / d) if d > 0 else (b / d, -a / d)
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    return True


def _cakisir(p1, q1, p2, q2):
    def yon(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    return (yon(p1, q1, p2) * yon(p1, q1, q2) < 0) and (yon(p2, q2, p1) * yon(p2, q2, q1) < 0)


def _yuk_etiketleri(e, noktalar, G, D):
    """Her yük noktasına ok ve çerçeveli kutu ( LiftDesigner "View of Pit" gibi,
    ama değeriyle ).  Kutu noktanın çevresinde, kuyunun içinde, hiçbir parçaya,
    yazıya, ölçüye ve başka kutuya binmeyen, oku da başka kutuyu / oku
    kesmeyen ilk yere konur:  önce kuyunun ortasına bakan yönler, önce kısa ok.
    En az seçeneği olan nokta ( duvar dibindeki tampon, ray ) önce yerleşir;
    ortadaki nokta sona kalır, onun yeri boldur.  Yer yoksa önce sığınma
    alanının yüzeyine ( yazısına değil ), sonra ölçü çizgisine ( yazısına
    değil ) binmesine izin verilir."""
    #  Sıra:  hiçbir şeye binmeden içeride, sonra kuyunun DIŞINDA ( duvarın
    #  ötesinde;  ok duvarın üstünden noktayı gösterir ) · sığınma alanının
    #  yüzeyine binerek içeride / dışarıda · ölçü çizgisine binerek içeride /
    #  dışarıda.  Yazılar büyüyünce ( 5 Eki ) küçük kuyularda
    #  kutular içeride yer bulamıyor, çizim duruyordu;  ölçü çizgisinin
    #  kutunun içinden geçmesi dışarıdaki kutudan daha kötü okunur.
    duvar = [geometri.sinir([el]) for el in e if el["katman"] == "KUYU-DUVAR" and el["tip"] != "yazi"]
    dis = (
        (
            min(d[0] for d in duvar),
            min(d[1] for d in duvar),
            max(d[2] for d in duvar),
            max(d[3] for d in duvar),
        )
        if duvar
        else None
    )
    hata = None
    for kademe, disari in (
        ({}, False),
        ({}, True),
        ({"siginma": False}, False),
        ({"siginma": False}, True),
        ({"siginma": False, "olcu_cizgisi": False}, False),
        ({"siginma": False, "olcu_cizgisi": False}, True),
    ):
        if disari and dis is None:
            continue
        try:
            return _yuk_yerlesimi(e, noktalar, G, D, *_engeller(e, **kademe), dis=dis if disari else None)
        except ValueError as h:
            hata = h
    raise hata


def _yuk_yerlesimi(e, noktalar, G, D, kutular, yazilar, dis=None):
    #  24 yön:  eksenler, köşegenler ve aralarındaki ( 1 : 2 ve 1 : 3 ) doğrultular;
    #  ok boyları 75'er artar ( 16 yön ve 150'lik adımla sağ aynalı düzende
    #  ağırlık tamponunun kutusu ölçü çizgisine biniyordu )
    yonler = [
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (2, 1),
        (-2, 1),
        (2, -1),
        (-2, -1),
        (1, 2),
        (-1, 2),
        (1, -2),
        (-1, -2),
        (3, 1),
        (-3, 1),
        (3, -1),
        (-3, -1),
        (1, 3),
        (-1, 3),
        (1, -3),
        (-1, -3),
    ]

    def adaylar(p, metin):
        px, py = p
        w, h = eleman.yazi_eni(metin, YUK_YAZI) + 2 * YUK_PAY, YUK_YAZI + 2 * YUK_PAY
        ox, oy = G / 2.0 - px, D / 2.0 - py
        #  Okun başladığı nokta bir yazının payının içindeyse ( yazı noktaya
        #  bitişik ) o yazı paysız sayılır:  yoksa noktadan çıkan her ok onu
        #  "kesiyor" sayılıyor, kutuya aday kalmıyordu ( yazılar büyüyünce, 5 Eki )
        okp = [
            0.0 if (b[0] - 15 <= px <= b[2] + 15 and b[1] - 15 <= py <= b[3] + 15) else 15.0 for b in yazilar
        ]
        sira = sorted(yonler, key=lambda u: -(u[0] * ox + u[1] * oy) / (u[0] ** 2 + u[1] ** 2) ** 0.5)
        for L in (220, 285, 350, 425, 500, 575, 650, 725, 800, 900, 1000, 1100, 1200, 1400) + (
            (1600, 1800, 2000, 2300) if dis else ()
        ):
            for ux, uy in sira:
                n = (ux * ux + uy * uy) ** 0.5
                q = (px + L * ux / n, py + L * uy / n)
                x0 = (q[0] if ux > 0 else q[0] - w) if ux else q[0] - w / 2.0
                y0 = (q[1] - h / 2.0) if ux else (q[1] if uy > 0 else q[1] - h)
                k = (x0, y0, x0 + w, y0 + h)
                if not (20 <= k[0] and k[2] <= G - 20 and 20 <= k[1] and k[3] <= D - 20):
                    #  dis:  kuyunun ( duvarlarıyla ) dışında, ona 900'den yakın
                    if dis is None or not (
                        (
                            k[2] <= dis[0] - 20
                            or k[0] >= dis[2] + 20
                            or k[3] <= dis[1] - 20
                            or k[1] >= dis[3] + 20
                        )
                        and dis[0] - 900 <= k[0]
                        and k[2] <= dis[2] + 900
                        and dis[1] - 900 <= k[1]
                        and k[3] <= dis[3] + 900
                    ):
                        continue
                if any(ortusur(k, b, 20) for b in kutular + yazilar) or any(
                    _kesisir(p, q, b, pay) for b, pay in zip(yazilar, okp)
                ):
                    continue
                yield q, k

    def uyar(p, q, k, konan):
        return not any(ortusur(k, b, 20) for b, _, _ in konan) and not any(
            _kesisir(p, q, b, 15) or _kesisir(a, c, k, 15) or _cakisir(p, q, a, c) for b, a, c in konan
        )

    #  En az seçeneği olan önce;  bir kutu sonrakilere yer bırakmıyorsa bir
    #  öncekinin sıradaki yeri denenir ( geri izleme, sınırlı adım )
    aday = [list(adaylar(*n)) for n in noktalar]
    sira = sorted(range(len(noktalar)), key=lambda i: len(aday[i]))
    konan, adim = [], [0]  # konan:  ( kutu, nokta, ok ucu )

    def yerlestir(j):
        if j == len(sira):
            return True
        p = noktalar[sira[j]][0]
        for q, k in aday[sira[j]]:
            adim[0] += 1
            if adim[0] > (200000 if dis else 20000):
                return False
            if uyar(p, q, k, konan):
                konan.append((k, p, q))
                if yerlestir(j + 1):
                    return True
                konan.pop()
        return False

    if not yerlestir(0):
        eksik = noktalar[sira[len(konan)]][1]
        raise ValueError(f"Kuyu dibi planında {eksik!r} yük kutusuna yer yok.")
    yeni = []
    for i, (k, p, q) in zip(sira, konan):
        metin = noktalar[i][1]
        yeni.append(eleman.ad(eleman.dikdortgen("YUK", k[0], k[1], k[2] - k[0], k[3] - k[1]), "yuk_kutusu"))
        yeni.append(
            eleman.ad(
                eleman.yazi((k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0, metin, YUK_YAZI, katman="YUK"), "yuk"
            )
        )
        yeni.append(eleman.ad(eleman.ok("YUK", q[0], q[1], p[0], p[1]), "yuk_oku"))
    return yeni


def kabin_alti_askisi(g, S, taban):
    """Kabin altı askıda kabinin tabanından aşağı sarkan askı:  iki kabin
    kasnağı ve aralarında yatay giden halat ( kasnakların alt teğetinde ) —
    plan kutuları.  Başka askıda boş liste."""
    if (g.get("aski") or {}).get("duzen") != "Kabin altı":
        return []
    kasnak = [eleman_kutusu(el) for el in taban if el.get("ad") == "kabin_kasnak"]
    if len(kasnak) < 2:
        return kasnak
    return kasnak + [
        (
            min(k[0] for k in kasnak),
            min(k[1] for k in kasnak),
            max(k[2] for k in kasnak),
            max(k[3] for k in kasnak),
        )
    ]


def sarkan_parcalar(g, S, taban, yukseklik):
    """Kabin tam ezilmiş tamponundayken kuyu tabanının `yukseklik` üstüne
    inen kabin parçalarının plan kutuları ( kabinin gövdesi hariç:  alan onun
    altında aranır, yüksekliğini dusey ölçer ).  Alt şase kirişi, patenler,
    fren bloğu … — hareketli.kabin_parcalari.  Eskiden yalnız kabin altı
    kasnakları sayılıyordu:  1275 kg'lık 2000 × 1400 kabinde, kuyu dibi 1400,
    alan alt kirişin altına düşüyor, kirişin altı tabandan 940 iken sığınma
    1.110 ( platformun altı ) ölçülüyordu.  Düşey girdi eksikse boş liste."""

    dy = g.get("dusey") or {}
    gerekli = ("kabin_carpma_arasi", "kabin_tampon_ezilme", "kabin_ic_yukseklik", "kabin_paten_arasi")
    kd = g.get("kuyu_dibi") or {}
    if not (all(sayi_mi(dy.get(k)) for k in gerekli) and sayi_mi(kd.get("derinlik"))):
        return []
    kt = parca_kotlari.kabin_kotlari(
        dy,
        S,
        -(dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"]),
        g.get("aski"),
        arka_aski.arkada_iki_bir(g),
    )
    sinir = -kd["derinlik"] + yukseklik
    return [
        k
        for ad, k, alt, _ in hareketli.kabin_parcalari(g, S, taban, kt)
        if ad != hareketli.KABIN and alt < sinir - 1e-9
    ]


def _perdeyi_uzat(perde, ag_yan, G, D, engeller):
    """Perdeyi iki ucunda, boşluk PERDE_BOSLUGU_AZAMI'yı aşıyorsa duvara ya da
    araya giren ilk engele uzatır.  →  ( perde, korunan bölgeler [ kutu ] ):
    korunan, uzayan parça ile ağırlığın yanındaki duvar arası."""
    x0, y0, x1, y1 = perde
    korunan = []
    if x0 == x1:  # yandaki ağırlık:  perde y boyunca
        kes = [k for k in engeller if k[0] < x0 < k[2]]
        on = max([k[3] for k in kes if k[3] <= y0 + 1e-6] + [0.0])
        arka = min([k[1] for k in kes if k[1] >= y1 - 1e-6] + [D])
        duvar = (x0, G) if ag_yan == "Sağ" else (0.0, x0)
        if y0 - on > PERDE_BOSLUGU_AZAMI:
            korunan.append((duvar[0], on, duvar[1], y0))
            y0 = on
        if arka - y1 > PERDE_BOSLUGU_AZAMI:
            korunan.append((duvar[0], y1, duvar[1], arka))
            y1 = arka
    else:  # arkadaki ağırlık:  perde x boyunca
        kes = [k for k in engeller if k[1] < y0 < k[3]]
        sol = max([k[2] for k in kes if k[2] <= x0 + 1e-6] + [0.0])
        sag = min([k[0] for k in kes if k[0] >= x1 - 1e-6] + [G])
        if x0 - sol > PERDE_BOSLUGU_AZAMI:
            korunan.append((sol, y0, x0, D))
            x0 = sol
        if sag - x1 > PERDE_BOSLUGU_AZAMI:
            korunan.append((x1, y0, sag, D))
            x1 = sag
    return (x0, y0, x1, y1), korunan


def gergi_parcalari(g, S, kasnak):
    """Gerginin ortak plan kutuları; kol rayı, kasnağı ve ağırlığı birleştirir."""
    gx, gy = kutu_merkezi(kasnak)
    ry = g["kabin_ray"]["kapi_arasi"]
    yon = 1.0 if gy >= ry else -1.0
    D = g["kuyu"]["derinlik"]
    #  Ağırlık duvara en az ASGARI_ACIKLIK ( çizimin çakışma payı ) kalmalı:
    #  sığmıyorsa kol öbür yöne döner ( montajcı da böyle yapar )
    a = girdi.ASGARI_ACIKLIK
    if not a <= gy + yon * S["gergi_agirlik_uzak"] <= D - a:
        yon = -yon
    agirlik_y = sorted((gy + yon * S["gergi_agirlik_yakin"], gy + yon * S["gergi_agirlik_uzak"]))
    en = S["gergi_agirlik_eni"]  # duvara dik:  kasnak düzlemine ortalı
    # Yön ters dönse de kolun zarfı kasnak milini ve raydaki mesnedi içerir.
    kol_y = (
        min(ry - S["gergi_kol_ray"], gy, gy + yon * S["gergi_kol_uc"]),
        max(ry + S["gergi_kol_ray"], gy, gy + yon * S["gergi_kol_uc"]),
    )
    return {
        "kol": (kasnak[0], kol_y[0], kasnak[2], kol_y[1]),
        "agirlik": (gx - en / 2.0, agirlik_y[0], gx + en / 2.0, agirlik_y[1]),
    }


def _girdi_hatalari(kd):
    """Kuyu dibi girdisinin eksikleri:  [ ileti ]."""
    hata = []
    for alan, secenek in (("siginma_tipi", tuple(SIGINMA)), ("regulator_yan", YANLAR)):
        if kd.get(alan) not in secenek:
            hata.append(f"kuyu_dibi.{alan}: {secenek} içinden olmalı ( {kd.get(alan)!r} ).")
    for alan in ("kabin_tampon_adedi", "agirlik_tampon_adedi"):
        if kd.get(alan) not in TAMPON_ADETLERI:
            hata.append(f"kuyu_dibi.{alan}: {TAMPON_ADETLERI} içinden olmalı ( {kd.get(alan)!r} ).")
    for alan in ("derinlik", "regulator_kaciklik", "regulator_kasnak_capi"):
        v = kd.get(alan)
        if (
            not isinstance(v, (int, float))
            or isinstance(v, bool)
            or (alan != "regulator_kaciklik" and v <= 0)
        ):
            hata.append(f"kuyu_dibi.{alan}: sayı olmalı ( {v!r} ).")
    kuvvet = kd.get("kuvvetler")
    if kuvvet is not None:
        if not isinstance(kuvvet, dict) or set(kuvvet) != set(KUVVETLER):
            hata.append(f"kuyu_dibi.kuvvetler: {KUVVETLER} girilmeli ( {kuvvet!r} ).")
        else:
            for ad in KUVVETLER:
                v = kuvvet[ad]
                #  Ray kuvveti sıfır olabilir ( ör. yük ekseni ray ekseninde );
                #  kuyu tabanı yükü olamaz
                if (
                    not isinstance(v, (int, float))
                    or isinstance(v, bool)
                    or v < 0
                    or (v == 0 and not ad.startswith(("Fx", "Fy")))
                ):
                    hata.append(f"kuyu_dibi.kuvvetler.{ad}: pozitif sayı ( N ) olmalı ( {v!r} ).")
    for adet, ara in (
        ("kabin_tampon_adedi", "kabin_tampon_arasi"),
        ("agirlik_tampon_adedi", "agirlik_tampon_arasi"),
    ):
        if kd.get(adet) == 2:
            v = kd.get(ara)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                hata.append(f"kuyu_dibi.{ara}: iki tamponda tamponlar arası girilmeli ( {v!r} ).")
    return hata


def yerlesim(g, cizim_sabitleri=None):
    """Kuyu dibinin yerleşimi — çizim de doğrulama da bunu kullanır."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    kd = g.get("kuyu_dibi") or {}
    hata = _girdi_hatalari(kd)
    if hata:
        return {"hata": hata}

    taban = geometri.plan(g, S, kapi_duzeyi=False)
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    kabin = eleman_kutusu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = eleman_kutusu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
    kabin_raylari = raylari_topla(taban, "kabin_ray")
    agirlik_raylari = raylari_topla(taban, "agirlik_ray")
    konsollar = [eleman_kutusu(el) for el in taban if el["katman"] == "KONSOL" and el["tip"] == "dikdortgen"]
    ag_yan = g["agirlik"]["yeri"] if g["agirlik"]["yeri"] in ("Sağ", "Sol") else None
    ry = g["kabin_ray"]["kapi_arasi"]
    kabin_tamponlari, agirlik_tamponlari = _tamponlar(kd, S, (kabin[0] + kabin[2]) / 2.0, ry, blok, ag_yan)
    perde = _perde(ag_yan, blok, kabin, konsollar, kabin_raylari, agirlik_raylari)

    #  ── REGÜLATÖR GERGİ KASNAĞI ──────────────────────────────────────
    #  Seçilen yandaki kabin rayının hizasında, ray ekseninin kaciklik kadar
    #  arkasında;  planda kasnak yandan görünür ( boyu çap, eni sabit ).
    ray = kabin_raylari[-1] if kd["regulator_yan"] == "Sağ" else kabin_raylari[0]
    gx, gy = kutu_merkezi(ray)[0], ry + kd["regulator_kaciklik"]
    dg_, eg = kd["regulator_kasnak_capi"] / 2.0, S["gergi_kasnak_eni"] / 2.0
    gergi = (gx - eg, gy - dg_, gx + eg, gy + dg_)
    gergi_donanim = gergi_parcalari(g, S, gergi)

    #  m.5.2.5.5.1 e:  perdenin ucu ile duvar arasında 0,30 m'den büyük boşluk
    #  kalıyorsa o bölge de korunur — perde o yanda duvara ya da araya giren
    #  ilk sabit parçaya ( konsol, kabin rayı, tampon, gergi, en alt durağın kapı
    #  ünitesi ) uzar.  Perde ile duvar arasında kalan bölge ağırlığın korunan
    #  alanıdır:  merdiven oraya saklanmaz.  ( Eskiden perde ağırlık raylarının
    #  hizasında bitiyordu;  standart düzenlerin çoğunda ucu ile duvar arası
    #  340 – 365 mm kalıyordu. )
    kapi_unitesi = [
        eleman_kutusu(el)
        for el in taban
        if el.get("ad") in ("kapi_kasasi", "kat_esigi", "kanat_cebi") and el["tip"] == "dikdortgen"
    ]
    perde, korunan = _perdeyi_uzat(
        perde,
        ag_yan,
        G,
        D,
        konsollar + kabin_raylari + kabin_tamponlari + kapi_unitesi + [gergi] + list(gergi_donanim.values()),
    )
    sabit = (
        konsollar
        + kabin_raylari
        + agirlik_raylari
        + [blok]
        + kabin_tamponlari
        + agirlik_tamponlari
        + [gergi]
        + list(gergi_donanim.values())
        + korunan
    )
    merdiven = _merdiven(g, kd, S, sabit, hata)
    hata += _cakismalar(
        G,
        D,
        kabin,
        blok,
        konsollar,
        kabin_raylari,
        agirlik_raylari,
        kabin_tamponlari,
        agirlik_tamponlari,
        gergi,
        gergi_donanim,
    )
    tip = kd["siginma_tipi"]
    siginma = _siginma_yeri(
        g, S, taban, tip, kabin, perde, ag_yan, sabit + ([merdiven] if merdiven else []), hata
    )
    return {
        "taban": taban,
        "kabin": kabin,
        "blok": blok,
        "kabin_raylari": kabin_raylari,
        "agirlik_raylari": agirlik_raylari,
        "kabin_tamponlari": kabin_tamponlari,
        "agirlik_tamponlari": agirlik_tamponlari,
        "perde": perde,
        "gergi": gergi,
        "gergi_donanim": gergi_donanim,
        "merdiven": merdiven,
        "siginma": siginma,
        "siginma_tipi": tip,
        "hata": hata,
        "S": S,
        "ag_yan": ag_yan,
    }


def _tamponlar(kd, S, kx, ry, blok, ag_yan):
    """TAMPONLAR:  kabin tamponu kabin ekseninde, ray ekseni üstünde durur
    ( referans proje ve LiftDesigner paftaları ).  İki tamponda ray ekseni
    boyunca simetrik.  Ağırlık tamponu ağırlığın ortasında;  iki tamponda
    ağırlığın boyu doğrultusunda simetrik.  ( kabin tamponları, ağırlık tamponları )"""
    t = S["tampon_taban"] / 2.0

    def _tampon(cx, cy):
        return (cx - t, cy - t, cx + t, cy + t)

    if kd["kabin_tampon_adedi"] == 1:
        kabin_tamponlari = [_tampon(kx, ry)]
    else:
        a = kd["kabin_tampon_arasi"] / 2.0
        kabin_tamponlari = [_tampon(kx - a, ry), _tampon(kx + a, ry)]
    bx, by = kutu_merkezi(blok)
    if kd["agirlik_tampon_adedi"] == 1:
        agirlik_tamponlari = [_tampon(bx, by)]
    else:
        a = kd["agirlik_tampon_arasi"] / 2.0
        agirlik_tamponlari = (
            [_tampon(bx, by - a), _tampon(bx, by + a)]
            if ag_yan
            else [_tampon(bx - a, by), _tampon(bx + a, by)]
        )
    return kabin_tamponlari, agirlik_tamponlari


def _perde(ag_yan, blok, kabin, konsollar, kabin_raylari, agirlik_raylari):
    """KARŞI AĞIRLIK PERDESİ  ( m.5.2.5.5.1 ):  ağırlığın kuyuya bakan yüzünde,
    ağırlık rayları arasının tamamı boyunca ( d:  en az ağırlığın genişliği
    kadar ).  Ağırlık ile ona en yakın parça arasındaki boşluğun ortasından
    geçer.  ( x0, y0, x1, y1 ) çizgisi."""
    ar = _birlesim(agirlik_raylari)
    if ag_yan == "Sol":
        komsu = min([k[0] for k in konsollar + kabin_raylari if k[0] > blok[2]] + [kabin[0]])
        px = (blok[2] + komsu) / 2.0
        return (px, ar[1], px, ar[3])
    if ag_yan == "Sağ":
        komsu = max([k[2] for k in konsollar + kabin_raylari if k[2] < blok[0]] + [kabin[2]])
        px = (blok[0] + komsu) / 2.0
        return (px, ar[1], px, ar[3])
    py = (blok[1] + kabin[3]) / 2.0
    return (ar[0], py, ar[2], py)


def _merdiven(g, kd, S, sabit, hata):
    """MERDİVEN  ( m.5.2.2.4 · Ek F ):  yan duvara yaslı saklanır, kapıya yakın
    yan seçilir;  yan duvar kapıdan 800 mm'den uzaksa ( geniş kuyu ) kapının
    yanında ön duvara yaslanır — Ek F.5 b yalnız kapı kenarına uzaklığı
    sınırlar.  Kuyu dibi 2,5 m'yi aşıyorsa merdiven değil erişim kapısı
    gerekir — çizilmez.  Kutu ya da None."""
    if kd["derinlik"] > MERDIVEN_AZAMI_DERINLIK:
        return None
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    kp = g["kapi"]
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    me, md = S["merdiven_eni"], S["merdiven_derinlik"]
    adaylar = []
    for yan, mx0, kenar in (("Sol", 0.0, x0), ("Sağ", G - md, x1)):
        y = 0.0
        while y + me <= D:
            k = (mx0, y, mx0 + md, y + me)
            if not any(ortusur(k, p) for p in sabit):
                #  Ek F.5 b:  kat girişinin kenarından merdivene
                dx = max(0.0, k[0] - kenar, kenar - k[2])
                uzak = (dx**2 + k[1] ** 2) ** 0.5
                if uzak <= MERDIVEN_KAPI_AZAMI:
                    adaylar.append((uzak, y, yan, k))
                break
            y += 25.0
    if not adaylar:
        #  Ön duvarda, kapı boşluğunun iki yanında ( eni ön duvar boyunca )
        for yon, kenar in ((-1.0, x0), (1.0, x1)):
            x = kenar if yon > 0 else kenar - me
            while 0.0 <= x and x + me <= G:
                k = (x, 0.0, x + me, md)
                uzak = max(0.0, k[0] - kenar, kenar - k[2])
                if uzak > MERDIVEN_KAPI_AZAMI:
                    break
                if not any(ortusur(k, p) for p in sabit):
                    adaylar.append((uzak, 0.0, "Ön", k))
                    break
                x += 25.0 * yon
    if adaylar:
        return min(adaylar)[3]
    hata.append(
        "Kuyu dibi merdiveni kat girişine en çok 800 mm uzakta ( TS EN 81-20 "
        "Ek F.5 b ) ne yan duvara ne kapının yanına yaslanabiliyor — orada tampon, "
        "ray ya da konsol var."
    )
    return None


def _cakismalar(
    G,
    D,
    kabin,
    blok,
    konsollar,
    kabin_raylari,
    agirlik_raylari,
    kabin_tamponlari,
    agirlik_tamponlari,
    gergi,
    gergi_donanim,
):
    """ÇAKIŞMALAR:  tamponlar, gergi ve donanımı kuyunun içinde, raylara ve
    konsollara değmeden;  tamponlar kabinin / ağırlığın altında."""
    hata = []
    for ad, liste in (
        ("kabin tamponu", kabin_tamponlari),
        ("ağırlık tamponu", agirlik_tamponlari),
        ("regülatör gergisi", [gergi]),
    ):
        for k in liste:
            if k[0] < 0 or k[1] < 0 or k[2] > G or k[3] > D:
                hata.append(f"{ad.capitalize()} kuyunun dışına taşıyor.")
            elif any(ortusur(k, p) for p in konsollar + kabin_raylari + agirlik_raylari):
                hata.append(f"{ad.capitalize()} bir ray ya da konsolla çakışıyor.")
    for ad, parca in gergi_donanim.items():
        if parca[0] < 0 or parca[1] < 0 or parca[2] > G or parca[3] > D:
            hata.append(f"Regülatör gergisi {ad} kuyunun dışına taşıyor.")
        elif ad == "agirlik" and min(parca[0], parca[1], G - parca[2], D - parca[3]) < girdi.ASGARI_ACIKLIK:
            #  Eskiden örnekte arka duvara 3 mm kalıyordu:  pratikte değiyordu
            hata.append(
                f"Regülatör gergisinin ağırlığı duvara "
                f"{min(parca[0], parca[1], G - parca[2], D - parca[3]):g} mm ( en az "
                f"{girdi.ASGARI_ACIKLIK:g} — çizimin çakışma payı ) — regülatör kaçıklığını değiştirin."
            )
        # Kol raydaki mesnede bağlanır; ağırlık rayların içine giremez.
        engeller = kabin_tamponlari + agirlik_tamponlari
        if ad == "agirlik":
            engeller += kabin_raylari + agirlik_raylari
        if any(ortusur(parca, p) for p in engeller):
            hata.append(
                f"Regülatör gergisinin {GERGI_PARCA[ad]} tampona ya da raya çarpıyor — "
                "regülatörün yerini ( kaçıklığı ya da yanı ) değiştirin."
            )
    for k in agirlik_tamponlari:
        if not (blok[0] <= kutu_merkezi(k)[0] <= blok[2] and blok[1] <= kutu_merkezi(k)[1] <= blok[3]):
            hata.append("Ağırlık tamponu karşı ağırlığın altına düşmüyor — tamponlar arasını daraltın.")
    for k in kabin_tamponlari:
        if not (kabin[0] <= kutu_merkezi(k)[0] <= kabin[2]):
            hata.append("Kabin tamponu kabinin altına düşmüyor — tamponlar arasını daraltın.")
    if len(kabin_tamponlari) == 2 and ortusur(*kabin_tamponlari):
        hata.append("İki kabin tamponu üst üste biniyor — tamponlar arasını açın.")
    if len(agirlik_tamponlari) == 2 and ortusur(*agirlik_tamponlari):
        hata.append("İki ağırlık tamponu üst üste biniyor — tamponlar arasını açın.")
    return hata


def _siginma_yeri(g, S, taban, tip, kabin, perde, ag_yan, engel, hata):
    """SIĞINMA ALANI  ( Çizelge 4 ):  kabinin izinin altında ( yüksekliği
    kabinin altına göre hesaplanır ), sabit donanıma basmadan, kapıya ve kabin
    eksenine en yakın yere.  Kutu ya da None.

    Kabin altı askıda kasnaklar ve aralarındaki halat kabinin tabanından
    aşağıdadır;  alt şase kirişi, patenler, fren bloğu da alanın yüksekliğine
    inebilir ( sarkan_parcalar ):  alan önce onların altına düşmeyen yerde
    aranır ( yoksa onların altında — yüksekliği düşey kesit denetler ).  Eskiden kasnak
    planda hiç engel sayılmıyordu:  alan kapıya yakın diye kasnağın köşesine
    giriyor, kasnaktan birkaç santim ötede tam yükseklik varken proje
    "sığınma yüksekliği 945 < 1000" diye reddediliyordu.

    Kabinin altında yer yoksa kuyu tabanının başka bir yeri:  m.5.2.5.8.1
    yalnız "kuyu tabanında engelsiz bir alan" ister ( kabinin izinin dışında
    üstünde kabin yoktur ).  Karşı ağırlığın indiği şerit ( perdenin ötesi )
    sayılmaz.  Küçük kabinde ( 900 × 1.000 ) ortadaki tamponun iki yanı
    500'e yetmiyor, proje reddediliyordu."""
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    kx = (kabin[0] + kabin[2]) / 2.0
    alcak = kabin_alti_askisi(g, S, taban) + sarkan_parcalar(g, S, taban, SIGINMA_YUKSEKLIK[tip])
    bolge = (max(0.0, kabin[0]), max(0.0, kabin[1]), min(G, kabin[2]), min(D, kabin[3]))
    if ag_yan == "Sağ":
        agirlik_seridi = (perde[0], 0.0, G, D)
    elif ag_yan == "Sol":
        agirlik_seridi = (0.0, 0.0, perde[0], D)
    else:
        agirlik_seridi = (0.0, perde[1], G, D)
    adaylar = []
    for bolge_, engeller, kenar in (
        (bolge, engel + alcak, False),
        (bolge, engel + alcak, True),
        (bolge, engel, False),
        (bolge, engel, True),
        ((0.0, 0.0, G, D), engel + alcak + [agirlik_seridi], False),
        ((0.0, 0.0, G, D), engel + alcak + [agirlik_seridi], True),
    ):
        adaylar = [
            (round(k[1], 3), abs((k[0] + k[2]) / 2.0 - kx), k)
            for w, h in {SIGINMA[tip], SIGINMA[tip][::-1]}
            for k in geometri.yer_adaylari(bolge_, w, h, engeller, kenar)
        ]
        if adaylar:
            break
    if adaylar:
        return min(adaylar)[2]
    a, b = SIGINMA[tip]
    hata.append(
        f"Kuyu dibinde {tip.lower()} tipi sığınma alanına ( {a:g} × {b:g} mm, "
        "TS EN 81-20 Çizelge 4 ) yer yok — tamponlar, gergi, merdiven ve karşı "
        "ağırlığın şeridi dışında kalmalı."
    )
    return None


def dogrula(g):
    hata = geometri.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    """Kuyu dibi planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    k = g["kuyu"]
    G, D, don = k["genislik"], k["derinlik"], k["duvar_on"]
    e = [el for el in Y["taban"] if el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi"]

    #  Kat kapısı:  yalnız yer göstermek için, kesik ( kabin bu kesitte yok )
    kp = g["kapi"]
    e.append(eleman.ad(eleman.dikdortgen("GIZLI", kp["sol_pay"], -don, kp["genislik"], don), "kapi_izi"))
    e += _donanim(Y, G)

    #  ── YAZILAR ──────────────────────────────────────────────────────
    #  Kuyu tabanına yük aktaran noktalar ( kutuları en sonda, ölçülerden sonra
    #  yerleşir ki onlara da binmesin )
    kv = g["kuyu_dibi"].get("kuvvetler")
    noktalar = _yuk_noktalari(g, Y, kv)
    gr, p = Y["gergi"], Y["perde"]
    e.append(
        eleman.yazi(
            kutu_merkezi(gr)[0] - (80 if gr[0] > G / 2 else -80),
            kutu_merkezi(gr)[1],
            "REGÜLATÖR GERGİSİ",
            uslup.NORMAL,
            aci=90,
        )
    )
    #  Perde yazısı ağırlıkla perde arasındaki boşluğa, tamponun yanına
    #  denk gelmeyen yarıya yazılır — yük okları yerleştikten sonra ( en sonda ),
    #  okların geçtiği yerden kaydırılarak.
    bl = Y["blok"]
    tamp = _birlesim(Y["agirlik_tamponlari"])
    if p[0] == p[2]:
        perde_yazisi = ((p[0] + (bl[2] if Y["ag_yan"] == "Sol" else bl[0])) / 2.0, (tamp[3] + p[3]) / 2.0, 90)
    else:
        perde_yazisi = ((tamp[2] + p[2]) / 2.0, (p[1] + bl[1]) / 2.0, 0)

    e += _olculer(g, Y)
    if Y["siginma"]:
        e += _siginma_olculeri(Y["siginma"], G, D, e)
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e)
    if geometri.olcu_kipi():  # ölçü çözümlemesi:  ölçüler yukarıda bitti
        return e
    e += _yuk_etiketleri(e, noktalar, G, D)
    e.append(_perde_yazisi(e, perde_yazisi, p))
    #  Ray konsoluna yatay yükler:  sağdaki ölçülerin ( ve kuyunun dışına konmuş
    #  yük kutularının ) dışında, kuyunun üst hizasından.  Yük kutularından
    #  SONRA:  dışarıdaki kutu tablonun yerine taşıyordu.
    if kv:
        s1 = G + k["duvar_sag"] + 320
        e += _kuvvet_tablosu(kv, max(s1 + 250, geometri.sinir(e)[2] + 150), D - 20)
    #  Parçaya ( ara kiriş, gergi ... ) binen ölçü yazıları, yük kutuları
    #  konduktan sonra ölçüleri boyunca boş yere kayar ( girdi taraması, 4 Eki ).
    #  Önce kaydırılınca bir düzende yük kutusuna yer kalmıyordu.
    geometri.parcadan_kaydir(e, ek_katman=("YUK",))
    return e


def _donanim(Y, G):
    """Tamponlar ( taban plakası + gövde ), perde, regülatör gergisi ve
    donanımı, merdiven, sığınma alanı."""
    S = Y["S"]
    e = []
    for liste, ad in ((Y["kabin_tamponlari"], "kabin_tamponu"), (Y["agirlik_tamponlari"], "agirlik_tamponu")):
        for kutu in liste:
            cx, cy = kutu_merkezi(kutu)
            e.append(
                eleman.ad(
                    eleman.dikdortgen("TAMPON", kutu[0], kutu[1], kutu[2] - kutu[0], kutu[3] - kutu[1]), ad
                )
            )
            e.append(eleman.ad(eleman.daire("TAMPON", cx, cy, S["tampon_capi"] / 2.0), ad))
    e.append(eleman.ad(eleman.cizgi("PERDE", *Y["perde"]), "perde"))
    gr = Y["gergi"]
    e.append(eleman.ad(eleman.dikdortgen("KASNAK", gr[0], gr[1], gr[2] - gr[0], gr[3] - gr[1]), "gergi"))
    for ad, kutu in Y["gergi_donanim"].items():
        e.append(
            eleman.ad(
                eleman.dikdortgen(
                    "KONSOL" if ad == "kol" else "MAKINE",
                    kutu[0],
                    kutu[1],
                    kutu[2] - kutu[0],
                    kutu[3] - kutu[1],
                ),
                "gergi_" + ad,
            )
        )
    m = Y["merdiven"]
    if m:
        e.append(eleman.ad(eleman.dikdortgen("MERDIVEN", m[0], m[1], m[2] - m[0], m[3] - m[1]), "merdiven"))
        #  Etiket sığıyorsa merdivenin içine:  yanına yazılınca sığınma alanının
        #  ölçüsüne biniyordu
        ic = (
            eleman.yazi_eni("MERDİVEN", uslup.NORMAL) <= m[3] - m[1] - 40 and uslup.NORMAL <= m[2] - m[0] - 20
        )
        e.append(
            eleman.yazi(
                kutu_merkezi(m)[0] + (0 if ic else 110 if m[0] < G / 2 else -110),
                kutu_merkezi(m)[1],
                "MERDİVEN",
                uslup.NORMAL,
                aci=90,
            )
        )
    sg = Y["siginma"]
    if sg:
        e.append(
            eleman.ad(eleman.dikdortgen("SIGINMA", sg[0], sg[1], sg[2] - sg[0], sg[3] - sg[1]), "siginma")
        )
        a, b = SIGINMA[Y["siginma_tipi"]]
        cx, cy = kutu_merkezi(sg)
        e.append(eleman.yazi(cx, cy + 35, "SIĞINMA ALANI", uslup.NORMAL))
        e.append(eleman.yazi(cx, cy - 35, f"{eleman.buyuk(Y['siginma_tipi'])}  {a:g} x {b:g}", uslup.NORMAL))
    return e


def _yuk_noktalari(g, Y, kv):
    """Kuyu tabanına yük aktaran noktalar:  [ ( merkez, yazı ) ]."""
    kd = g["kuyu_dibi"]
    noktalar = []
    for liste, ad, adet in (
        (Y["kabin_tamponlari"], "Fkt", kd["kabin_tampon_adedi"]),
        (Y["agirlik_tamponlari"], "Fat", kd["agirlik_tampon_adedi"]),
        (Y["kabin_raylari"], "FKR", 1),
        (Y["agirlik_raylari"], "FAR", 1),
    ):
        #  İki tamponda her birine düşen:  hesap paftasındaki Fkt1 = Fkt / ncar
        ad_ = ad + ("1" if adet > 1 else "")
        metin = f"{ad_} = {_kn(kv[ad] / adet)} kN" if kv else ad_
        noktalar += [(kutu_merkezi(k), metin) for k in liste]
    return noktalar


def _olculer(g, Y):
    """Üst:  tampon eksenleri ( ağırlık ekseni · kabin ekseni );  sağ:  ray
    ekseni ve regülatör gergisi;  alt:  kat kapısı ve merdivenin kapıya
    uzaklığı."""
    k, kp = g["kuyu"], g["kapi"]
    G, D, don, dg, dar = k["genislik"], k["derinlik"], k["duvar_on"], k["duvar_sag"], k["duvar_arka"]
    ry = g["kabin_ray"]["kapi_arasi"]
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    a0 = -don - 120
    xs = sorted({0.0, G} | {kutu_merkezi(t)[0] for t in Y["kabin_tamponlari"] + Y["agirlik_tamponlari"]})
    e = [eleman.olcu("yatay", (a, 0), (b, 0), u0) for a, b in zip(xs, xs[1:])]
    e.append(eleman.olcu("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    ys = sorted(
        {0.0, D, ry, kutu_merkezi(Y["gergi"])[1]} | {kutu_merkezi(t)[1] for t in Y["agirlik_tamponlari"]}
    )
    e += [eleman.olcu("dusey", (0, a), (0, b), s0) for a, b in zip(ys, ys[1:])]
    e.append(eleman.olcu("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    kapi = (kp["sol_pay"], kp["sol_pay"] + kp["genislik"])
    xs = sorted({0.0, G, *kapi} | ({Y["merdiven"][0], Y["merdiven"][2]} if Y["merdiven"] else set()))
    e += [
        eleman.olcu("yatay", (a, 0), (b, 0), a0, f"KAPI {kp['genislik']:g}" if (a, b) == kapi else None)
        for a, b in zip(xs, xs[1:])
    ]
    return e


def _siginma_olculeri(sg, G, D, e):
    """Sığınma alanının yeri — kuyu duvarlarından.  Ölçü sırası sığınmanın
    üstünde / sağında;  yazısı bir parçaya ( tampon, gergi, merdiven, ray,
    nokta adı ) biniyorsa öbür yanına geçer ( Yatarak sığınmada "1000"
    kabin tamponunun üstüne düşüyordu )."""
    engel = [
        geometri.sinir([el])
        for el in e
        if el["katman"] in geometri.PARCA_KATMANLARI or (el["tip"] == "yazi" and el.get("katman") == "YAZI")
    ]

    def yatay(k):
        return [
            eleman.olcu("yatay", (0, 0), (sg[0], 0), k),
            eleman.olcu("yatay", (sg[0], 0), (sg[2], 0), k),
            eleman.olcu("yatay", (sg[2], 0), (G, 0), k),
        ]

    def dusey(k):
        return [
            eleman.olcu("dusey", (0, 0), (0, sg[1]), k),
            eleman.olcu("dusey", (0, sg[1]), (0, sg[3]), k),
            eleman.olcu("dusey", (0, sg[3]), (0, D), k),
        ]

    return _serbest(yatay, (sg[3] + 90, sg[1] - 90), D, engel) + _serbest(
        dusey, (sg[2] + 90, sg[0] - 90), G, engel
    )


def _perde_yazisi(e, yer, p):
    """KARŞI AĞIRLIK PERDESİ:  tercih edilen yerde;  bir yük okuna ya da kutusuna,
    bir yazıya değiyorsa perde boyunca en yakın boş yere kayar."""
    x, y, aci = yer
    h = uslup.NORMAL
    oklar = [((o["x1"], o["y1"]), (o["x2"], o["y2"])) for o in e if o.get("ad") == "yuk_oku"]
    engel = [
        geometri.sinir([o])
        for o in e
        if o.get("ad") in ("yuk_kutusu", "yuk") or (o["tip"] == "yazi" and o["katman"] == "YAZI")
    ]
    #  Ölçü yazıları da ( eskiden sayılmıyordu — girdi taraması, 4 Eki )
    engel += [geometri.yazi_kutusu(o) for o in e if o["tip"] == "olcu" and o.get("yazi")]
    boy = (p[1], p[3]) if aci else (p[0], p[2])
    orta = y if aci else x
    #  Tam adı sığmıyorsa ( oklar perdeyi sık kesiyor ) kısaltılır
    for metin in ("KARŞI AĞIRLIK PERDESİ", "AĞIRLIK PERDESİ", "PERDE"):
        L = eleman.yazi_eni(metin, h)
        adaylar = sorted(
            (orta + d for d in range(-2000, 2001, 20) if boy[0] + L / 2.0 <= orta + d <= boy[1] - L / 2.0),
            key=lambda c: abs(c - orta),
        )
        for c in adaylar:
            hh = h
            k = (
                (x - hh / 2.0, c - L / 2.0, x + hh / 2.0, c + L / 2.0)
                if aci
                else (c - L / 2.0, y - hh / 2.0, c + L / 2.0, y + hh / 2.0)
            )
            if not any(_kesisir(a, b, k, 15) for a, b in oklar) and not any(ortusur(k, b, 15) for b in engel):
                return eleman.yazi(x, c, metin, h, aci=90) if aci else eleman.yazi(c, y, metin, h)
    metin = "KARŞI AĞIRLIK PERDESİ"
    return eleman.yazi(x, orta, metin, h, aci=90) if aci else eleman.yazi(orta, y, metin, h)
