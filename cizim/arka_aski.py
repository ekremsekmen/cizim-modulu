# -*- coding: utf-8 -*-
"""
ARKADA KARŞI AĞIRLIKLA 2:1 ASKI — kabin üstünde çapraz kasnaklar

Kullanıcı kararı ( 30 Eyl ):  "çapraz, iki taraf dengeli".  Ofisin iki gerçek
projesi ( LiftDesigner ):  12495-18 ( makine dairesiz ) kasnakları çapraz,
1275 ( makine daireli ) derinlik boyunca düz koyar;  düzde karşı ağırlığın
kasnağı ağırlığın ortasından kasnak yarıçapı kadar kaçık kalır.  Çaprazda
ikisi de dengelidir:

  · KARŞI AĞIRLIK KASNAĞI ağırlığın ortasında ( ex , ey );  ağırlık geniş ve
    sığdır, kasnağın düzlemi genişlik boyuncadır ( geometri.plan da öyle
    çizer ).  Bir teğeti ( W ) tahrik kasnağından inen halatı alır, öbür
    teğeti ( Hw ) ağırlığın bağlantısına çıkar.
  · TAHRİK KASNAĞININ düzlemi derinlik boyunca, W'nin hizasında ( x = xk ):
    iki inişi ağırlık ekseninde ( W ) ve D1 önünde ( P ) — referans proje:
    arka duvardan 354 ve 594 ( RDB 240 ).
  · KABİN KASNAKLARI kabinin üstünde, P ile kabin bağlantısını ( H )
    birleştiren düşey düzlemde;  arkadakinin dış teğeti P'de, öndekinin H'de.
    H, P'nin askı merkezine ( C:  kabin ekseni, kabin merkezi + kaçıklık )
    göre aynasıdır:  iki düşey halatın ortası C'dir, askı kabin merkezinde.
    Referans projede düzlem derinliğe 20° açılı, askı kabin merkezinden 18 ·
    49 mm kaçık ( LiftDesigner'ın yuvarlaması ).

Makinenin gövdesi tahrik kasnağından ağırlık kasnağının merkezinden uzağa
( yon yönünde ) uzanır.  Bütün noktalar planda ( mm;  x kuyu genişliği,
y ön duvardan arkaya ).
"""

from temel import sayi_mi
from cizim import izli
from cizim import standart

#  Kabin kasnaklarının birbirine en az açıklığı ( jantlar arası ):  yoksa iki
#  kasnak üst üste biner.  Sıfır değil:  kasnak taşıyıcısının ortası.
KASNAK_ARALIGI_ASGARI = 0.0


def arkada_iki_bir(g):
    """Arkadaki ağırlıkla 2:1 askı mı ( bu modülün düzeni )."""
    return (g.get("agirlik") or {}).get("yeri") == "Arka" and (g.get("aski") or {}).get("duzen") in (
        "Kabin üstü",
        "Kabin altı",
    )


def makine_yonu(g):
    """Makine ağırlık kasnağının hangi yanında ( +1 sağ, −1 sol ):  karşı ağırlık
    kuyunun ortasındadır, iki yan eşittir;  kabin bir yana kaçıksa o yana
    ( referans proje:  kabin sağa 60 kaçık, makine sağda ), değilse sağa."""
    kacik = (g.get("kabin") or {}).get("kaciklik_y") or 0.0
    return -1.0 if kacik < 0 else 1.0


def agirlik_ray_duvari(g, S):
    """Ağırlık ekseni – arka duvar ( girilmemişse ):  tahrik kasnağının kabin
    inişi ( P ) kabin tavanının arka kenarından korkuluk payı ( kabin_ustu:
    parçalara 0,10 m ) kadar içeride — arka kabin kasnağı ve halat korkuluğun
    içinde kalır.  Ofisin iki projesinde de P kabinin arka kenarındadır ( 1275:
    ~50 içeride, 12495-18:  56 dışarıda — orada kasnak kenardan taşar ).
    Ağırlık ekseni = P + D1.  Karşı ağırlık kabine en az 50 mm ( m.5.2.5.5.1 h ),
    duvara eski kuraldan ( derinlik / 2 + 50 ) yakın olamaz."""

    k, kb, ag, mk = g["kuyu"], g["kabin"], g["agirlik"], g["makine"]
    kabin_arka = kb["on_pay"] + kb["derinlik"] + S["kabin_pano_arka"]
    ey = kabin_arka - standart.KORKULUK_PARCA_ASGARI + mk["tahrik_kasnak_capi"]
    ey = max(ey, kabin_arka + 50.0 + ag["derinlik"] / 2.0)
    return max(ag["derinlik"] / 2.0 + 50.0, k["derinlik"] - ey)


def geometri(g, S, yon=None):
    """Planda askının bütün noktaları.  yon:  makinenin ağırlık kasnağından
    yana yönü ( +1 sağa, −1 sola;  boşsa makine_yonu ).  Döner:  sözlük ( hata
    listesiyle );  girdi eksikse yalnız { hata }."""
    yon = makine_yonu(g) if yon is None else yon
    k, kb, ag = g["kuyu"], g["kabin"], g["agirlik"]
    a, mk = g.get("aski") or {}, g.get("makine") or {}
    hata = []
    for ad, v in (
        ("aski.kasnak_capi", a.get("kasnak_capi")),
        ("agirlik.kasnak_capi", ag.get("kasnak_capi")),
        ("makine.tahrik_kasnak_capi", mk.get("tahrik_kasnak_capi")),
    ):
        if not (sayi_mi(v) and v > 0):
            hata.append(f"{ad}:  arkadaki ağırlıkla 2:1 askıda gerekli ( {v!r} ).")
    if hata:
        return {"hata": hata}
    G, D = k["genislik"], k["derinlik"]
    Rk, Rc, D1 = a["kasnak_capi"] / 2.0, ag["kasnak_capi"] / 2.0, mk["tahrik_kasnak_capi"]

    #  Askı merkezi C:  kabin ekseni, kabinin ( pano dahil ) derinlik ortası
    #  + kaçıklık ( hesabın xs'i girilmişse köprü buraya taşır ).
    cx = G / 2.0 + kb["kaciklik_y"]
    cy = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 + a.get("kasnak_kaciklik", 0)
    #  Karşı ağırlığın ekseni ( geometri.plan:  arkada, kuyu genişliğinin ortası )
    ex, ey = G / 2.0, D - ag["ray_duvar"]
    xk = ex + yon * Rc
    W = (xk, ey)  # tahrik → ağırlık kasnağı
    Hw = (ex - yon * Rc, ey)  # ağırlık kasnağı → bağlantı
    P = (xk, ey - D1)  # tahrik → kabin kasnağı
    H = (2.0 * cx - P[0], 2.0 * cy - P[1])  # kabin kasnağı → bağlantı
    L = izli.hypot(H[0] - P[0], H[1] - P[1])
    if L < 1e-6:
        return {
            "hata": [
                "Arkadaki ağırlıkla 2:1:  tahrik kasnağının kabin inişi askı merkezinin "
                "üstünde — kabin kasnaklarına yer yok."
            ]
        }
    u = ((H[0] - P[0]) / L, (H[1] - P[1]) / L)  # P'den H'ye
    n = (-u[1], u[0])  # kasnak ekseni ( düzleme dik )
    arka = (P[0] + Rk * u[0], P[1] + Rk * u[1])
    on = (H[0] - Rk * u[0], H[1] - Rk * u[1])
    aralik = L - 2.0 * Rk  # kasnak merkezleri arası
    if aralik < 2.0 * Rk + KASNAK_ARALIGI_ASGARI:
        hata.append(
            f"Arkadaki ağırlıkla 2:1:  kabin kasnakları ( ø {2 * Rk:g} ) üst üste biniyor — "
            f"merkezleri arası {aralik:.0f} mm, en az {2 * Rk:g};  kabin askı merkezinden "
            f"tahrik kasnağının inişine uzaklık {L / 2.0:.0f} mm."
        )
    if not (0.0 < H[0] < G and 0.0 < H[1] < D):
        hata.append(
            f"Arkadaki ağırlıkla 2:1:  kabin halatının bağlantısı ( x {H[0]:.0f}, y {H[1]:.0f} ) "
            "kuyunun dışına düşüyor."
        )
    #  Kasnaklar kabinin üstünde:  tahrik kasnağından inen halat kabinin
    #  tavanına iner ( kabin hep onun altındadır ) — kabinin yanından geçmesi
    #  gerekmez;  karşı ağırlığın içinden geçemez.
    blok_on = ey - ag["derinlik"] / 2.0
    if not P[1] < blok_on:
        hata.append(
            f"Arkadaki ağırlıkla 2:1:  tahrik kasnağından kabine inen halat ( y {P[1]:.0f} ) "
            f"karşı ağırlığın içinden geçiyor ( ağırlığın önü {blok_on:.0f} ) — tahrik "
            "kasnağı çapı ağırlığın derinliğinin yarısından büyük olmalı."
        )

    def ayak_izi(merkez):
        """Kasnağın plandaki dört köşesi ( düzlem boyunca çap, ekseni boyunca en )."""
        w = S["kabin_kasnak_genislik"] / 2.0
        return [
            (merkez[0] + su * Rk * u[0] + sn * w * n[0], merkez[1] + su * Rk * u[1] + sn * w * n[1])
            for su, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]

    kasnaklar = [arka, on]
    izler = [ayak_izi(m) for m in kasnaklar]
    return {
        "cx": cx,
        "cy": cy,
        "ex": ex,
        "ey": ey,
        "xk": xk,
        "yon": yon,
        "W": W,
        "Hw": Hw,
        "P": P,
        "H": H,
        "u": u,
        "n": n,
        "kasnaklar": kasnaklar,
        "izler": izler,
        "kutular": [
            (min(p[0] for p in iz), min(p[1] for p in iz), max(p[0] for p in iz), max(p[1] for p in iz))
            for iz in izler
        ],
        "aralik": aralik,
        "aci": izli.degrees(izli.atan2(abs(u[0]), abs(u[1]))),
        "Rk": Rk,
        "Rc": Rc,
        "D1": D1,
        "hata": hata,
    }
