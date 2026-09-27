# -*- coding: utf-8 -*-
"""
DÜŞEY KESİTLER  ( kuyunun derinliği boyunca, kabin ekseninden )

  KUYU DİBİ DÜŞEY KESİTİ   kabin tam ezilmiş tamponunun üstünde
  KUYU ÜSTÜ DÜŞEY KESİTİ   kabin en üst konumunda:  karşı ağırlık tam ezilmiş
                           tamponunun üstünde + 0,035 · v²  ( m.5.2.5.6.1 )
  KUYU DÜŞEY KESİTİ        tam boy, 1/50:  bütün duraklar, kat kapıları ve kotlar;
                           kabin en alt durakta  ( ELEport "Cabin at Bottom Floor",
                           LiftDesigner "Dikey 1:50" gibi — LiftDesigner da tam
                           boy gerçek ölçekte çizer, ELEport ara katları kırar )

Yatay eksen kuyu derinliğidir ( 0 = ön duvarın iç yüzü );  plan çizimleriyle
aynı koordinat — kabin, ray, tampon ve sığınma alanı plandaki yerlerinden
okunur.  Düşey eksen döşeme kotudur ( 0 = en alt / en üst durak ).

KABİNİN DÜŞEY ÖLÇÜLERİ ELEport kabininden ( sabitler.py ).  Hesap
programının sığınma satırları bu kabinle değil ofisin paylarıyla hesaplanır
( üst paten bir satırda 2.700, bir başkasında 2.900 );  o paylar bu modele
göre düzeltilene kadar çizimin açıklıkları hesap paftasındakilerle birebir
tutmaz.

STANDARDIN DENETLEDİĞİ AÇIKLIKLAR
  kuyu dibi   m.5.2.5.8.1  sığınma yüksekliği ( Çizelge 4 )
              m.5.2.5.8.2 a  kabinin en alt kısımları ≥ 0,50 m;  etek ≥ 0,10;
                             şase, paten, fren bloğu ( raya yakın ) ≥ 0,10
  kuyu üstü   m.5.2.5.7.1  sığınma yüksekliği ( Çizelge 3 )
              m.5.2.5.7.2 b  paten ≥ 0,10  ( 0,40 m yatay uzaklık içindeki tavan parçalarına )
              m.5.2.5.7.2 c  korkuluğun üstü ≥ 0,30 kabin izdüşümünde, dışında ≥ 0,10
              m.5.2.5.6.2   kabin ve karşı ağırlık en üst konumdayken raylar en az
                            0,10 m daha kılavuzluk eder  ( konum:  m.5.2.5.6.1 Çizelge 2 )
  "Kuyu tavanının en alt kısmı" kirişler ve tavanın altındaki parçalar dahildir
  ( m.5.2.5.7.2 ):  makine dairesizde makine şasesi, halat bağlantıları ve
  regülatör — yerleri donanim.py'de.
  duraklar    m.5.2.3.1     ardışık iki kat kapısı eşiği arası 11 m'yi aşarsa ara
                            acil kapı gerekir — bu çizim acil kapı çizmez, durur
"""
from cizim import donanim as CDN
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kabin_ustu as CKU
from cizim import kesit_parcalari as CKP
from cizim import kuyu_dibi as CKD
from cizim import sabitler as CS

#  Çizelge 3 / Çizelge 4 — sığınma alanının YÜKSEKLİĞİ ( mm )
SIGINMA_UST_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0}
SIGINMA_DIP_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0}
DIP_EN_ALT = 500.0          # m.5.2.5.8.2 a
DIP_ETEK = 100.0            # m.5.2.5.8.2 a 1)
DIP_RAYA_YAKIN = 100.0      # m.5.2.5.8.2 a 2) · Şekil 7  ( XH ≤ 0,15 m )
UST_PATEN = 100.0           # m.5.2.5.7.2 b
UST_KORKULUK = 300.0        # m.5.2.5.7.2 c 1)  kabin izdüşümünde
UST_KORKULUK_DIS = 100.0    # m.5.2.5.7.2 c 1)  korkuluğun dışında
YATAY_UZAKLIK = 400.0       # m.5.2.5.7.2 b / c 1)  "0,40 m yatay uzaklık içinde"
RAY_UZANTISI = 100.0        # m.5.2.5.6.2  ( en üst konum m.5.2.5.6.1:  + 0,035·v² )
ETEK_BOYU = CDN.ETEK_BOYU   # m.5.4.5.1:  kabin eteğinin düşey kısmı en az 0,75 m
ESIK_ARASI = 11000.0        # m.5.2.3.1:  ardışık kat kapısı eşikleri arası
DUSEY_ALANLAR = ("kabin_ic_yukseklik", "kabin_paten_arasi", "son_kat", "beyan_hizi",
                 "kabin_tampon_baba", "kabin_tampon_boyu",
                 "kabin_carpma_arasi", "kabin_tampon_ezilme", "agirlik_tampon_baba",
                 "agirlik_tampon_boyu", "agirlik_carpma_arasi", "agirlik_tampon_ezilme")


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def durak_kotlari(g):
    """Durakların döşeme kotları ( en alt durak ±0 ) ve girdi hataları.

    kat_yuksekligi tek sayıysa bütün katlar o yükseklikte;  liste ise alttan
    üste ardışık iki durak arası ( durak_adedi − 1 tane ).  ELEport'ta
    hepsi 2.900;  LiftDesigner örneğinde 3.400, 3.400, 3.000 … karışık.
    """
    dy, kp = g.get("dusey") or {}, g.get("kapi") or {}
    n, kh = dy.get("durak_adedi"), dy.get("kat_yuksekligi")
    if not (_sayi(n) and n == int(n) and n >= 2):
        return [], [f"dusey.durak_adedi:  2 ya da daha büyük bir tam sayı olmalı ( {n!r} )."]
    n = int(n)
    araliklar = [kh] * (n - 1) if _sayi(kh) else kh
    if not (isinstance(araliklar, (list, tuple)) and len(araliklar) == n - 1
            and all(_sayi(h) and h > 0 for h in araliklar)):
        return [], [f"dusey.kat_yuksekligi:  sıfırdan büyük bir sayı ya da {n - 1} "
                    f"sayılık bir liste olmalı ( {kh!r} )."]
    hata = []
    kapi_h = kp.get("yukseklik") or 0
    for i, h in enumerate(araliklar):
        ad = f"{i + 1}. – {i + 2}. durak arası {h:g} mm"
        if h <= kapi_h:
            hata.append(f"{ad}:  kat kapısı yüksekliğinden ( {kapi_h:g} ) büyük olmalı — "
                        f"kapı üstteki durağın döşemesine giriyor.")
        if h > ESIK_ARASI:
            hata.append(f"{ad} > {ESIK_ARASI:g} mm:  ara acil kapı gerekir "
                        f"( TS EN 81-20 m.5.2.3.1 );  bu çizim acil kapı çizmez.")
    kotlar = [0.0]
    for h in araliklar:
        kotlar.append(kotlar[-1] + h)
    return kotlar, hata


def _korkuluk_cizgileri(KU):
    """Gerekli korkulukların plandaki çizgileri ( ince kutu )."""
    x0, y0, x1, y1 = KU["tavan"]
    cizgi = {"Sol": lambda i: (x0 + i, y0, x0 + i, y1), "Sağ": lambda i: (x1 - i, y0, x1 - i, y1),
             "Ön": lambda i: (x0, y0 + i, x1, y0 + i), "Arka": lambda i: (x0, y1 - i, x1, y1 - i)}
    return [cizgi[ad](k["iceri"]) for ad, k in KU["kenarlar"].items() if k["gerekli"]]


kabin_kotlari = CDN.kabin_kotlari


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    dy = g.get("dusey") or {}
    hata = [f"dusey.{a}: sıfırdan büyük bir sayı olmalı ( {dy.get(a)!r} )."
            for a in DUSEY_ALANLAR if not (_sayi(dy.get(a)) and dy[a] > 0)]
    kotlar, durak_hata = durak_kotlari(g)
    hata += durak_hata
    if hata:
        return {"hata": hata}
    KD, KU = CKD.yerlesim(g, S), CKU.yerlesim(g, S)
    if KD["hata"] or KU["hata"]:
        return {"hata": KD["hata"] + KU["hata"]}
    kd, ku = g["kuyu_dibi"], g["kabin_ustu"]
    v = dy["beyan_hizi"]
    b35 = 35.0 * v * v                                   # 0,035 · v² · 1000

    #  ── KUYU DİBİ:  kabin tam ezilmiş tamponunda ──────────────────────
    KY = kd["derinlik"]
    #  Kuyu dibi zinciri kabinin şase altıyla kapanmalı:  kaide + tampon +
    #  çarpma arası + şase altı = kuyu dibi ( ELEport:  764 + 160 + 96 + 480 )
    zincir = dy["kabin_tampon_baba"] + dy["kabin_tampon_boyu"] + dy["kabin_carpma_arasi"] + \
        S["sase_alt_derinlik"]
    if abs(zincir - KY) > 0.5:
        hata.append(
            f"Kuyu dibi {KY:g} mm, ama kaide {dy['kabin_tampon_baba']:g} + tampon "
            f"{dy['kabin_tampon_boyu']:g} + çarpma arası {dy['kabin_carpma_arasi']:g} + kabinin "
            f"şase altı {S['sase_alt_derinlik']:g} = {zincir:g} mm — girdiler kabinle çelişiyor.")
    dip = kabin_kotlari(dy, S, -(dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"]))
    taban = -KY
    #  Kabin kasnaklarının planda sığınma alanının üstüne düşüp düşmediği
    kasnaklar = [_kutu(el) for el in KU["taban"] if el.get("ad") == "kabin_kasnak"]
    kasnak_capi = (g.get("aski") or {}).get("kasnak_capi") or 0
    sg = KD["siginma"]
    ustunde_kasnak = bool(kasnaklar) and any(k[0] < sg[2] and sg[0] < k[2] for k in kasnaklar)
    kasnak_alti = dip["kasnak_merkez"] - kasnak_capi / 2.0
    en_alt = min(dip["taban_alti"], kasnak_alti) if kasnaklar else dip["taban_alti"]
    siginma_ustu = min(dip["taban_alti"], kasnak_alti) if ustunde_kasnak else dip["taban_alti"]
    dip_aciklik = {
        "siginma": (siginma_ustu - taban, SIGINMA_DIP_YUKSEKLIK[kd["siginma_tipi"]],
                    "m.5.2.5.8.1 · Çizelge 4"),
        "en_alt": (en_alt - taban, DIP_EN_ALT, "m.5.2.5.8.2 a"),
        "etek": (dip["etek_alti"] - taban, DIP_ETEK, "m.5.2.5.8.2 a 1"),
        "sase": (min(dip["alt_paten"], dip["fren_alti"]) - taban, DIP_RAYA_YAKIN,
                 "m.5.2.5.8.2 a 2 · Şekil 7"),
    }

    #  ── KUYU ÜSTÜ:  kabin en üst konumunda ────────────────────────────
    #  Karşı ağırlık tam ezilmiş tamponunda + 0,035·v²  ( m.5.2.5.6.1 )
    H = kotlar[-1]
    M = CDN.yerlesim(g, S, H, H + dy["son_kat"], -KY)
    if M["hata"]:
        return {"hata": hata + M["hata"]}
    yukselme = dy["agirlik_carpma_arasi"] + dy["agirlik_tampon_ezilme"] + b35
    ust = kabin_kotlari(dy, S, yukselme)
    tavan_alti = dy["son_kat"] - S["tavan_kirisi"]

    def engel(kutu):
        z, ad = CDN.tavan_engeli(M, kutu)
        return z - H, ad

    def genislet(k, d):
        return (k[0] - d, k[1] - d, k[2] + d, k[3] + d)

    kabin_izi = KU["tavan"]
    ray_ustu = min(r["ust"] for r in M["raylar"] if r["tur"] == "kabin") - H
    korkuluk = max((k["yukseklik"] for k in KU["kenarlar"].values() if k["gerekli"]), default=0.0)
    sg_engel = engel(KU["siginma"])
    patenler = [_kutu(el) for el in KD["taban"] if el["katman"] == "PATEN"]
    pt_engel = min(engel(genislet(p, YATAY_UZAKLIK)) for p in patenler)
    ust_engel = {"siginma": sg_engel, "paten": pt_engel, "ray": (ray_ustu, "ray")}
    ust_aciklik = {
        "siginma": (sg_engel[0] - ust["tavan"], SIGINMA_UST_YUKSEKLIK[ku["siginma_tipi"]],
                    "m.5.2.5.7.1 · Çizelge 3"),
        "paten": (pt_engel[0] - ust["ust_paten"], UST_PATEN, "m.5.2.5.7.2 b"),
        "ray": (ray_ustu - ust["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2"),
    }
    if korkuluk:
        #  Korkuluğun 0,40 m yakınındaki tavan parçaları:  kabin izdüşümündeyse
        #  0,30, dışındaysa 0,10  ( m.5.2.5.7.2 c 1 )
        k_ust = ust["tavan"] + korkuluk
        adaylar = [(tavan_alti, "kuyu tavanı", UST_KORKULUK)]
        for kenar in _korkuluk_cizgileri(KU):
            bolge = genislet(kenar, YATAY_UZAKLIK)
            for ad, p, z in M["parcalar"]:
                if CDN._ortusur(p, bolge):
                    icinde = CDN._ortusur(p, kabin_izi)
                    adaylar.append((z - H, ad, UST_KORKULUK if icinde else UST_KORKULUK_DIS))
        z, ad, asgari = min(adaylar, key=lambda a: a[0] - k_ust - a[2])
        ust_engel["korkuluk"] = (z, ad)
        ust_aciklik["korkuluk"] = (z - k_ust, asgari, "m.5.2.5.7.2 c")
    #  Karşı ağırlık en üst konumunda:  kabin tam ezilmiş tamponunda + 0,035·v²
    ag_alt = (M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"] + H
              + dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"] + b35)
    AK = CDN.agirlik_kotlari(M, ag_alt)
    ag_ray = min(r["ust"] for r in M["raylar"] if r["tur"] == "agirlik")
    ust_aciklik["agirlik_ray"] = (ag_ray - AK["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2")
    if M["mrl"] and CDN._ortusur(M["agirlik"]["kutu"], M["sase"][:4]):
        ag_tepe = max(AK["ust_paten"], AK["kasnak_merkez"] + g["agirlik"]["kasnak_capi"] / 2.0)
        if ag_tepe > M["sase"][4] + 1e-9:
            hata.append(f"Karşı ağırlık en üst konumunda makine şasesine çarpıyor:  tepesi "
                        f"{ag_tepe - H:g} mm, şasenin altı {M['sase'][4] - H:g} mm ( son kattan ).")
    for ad, (deger, asgari, madde) in list(dip_aciklik.items()) + list(ust_aciklik.items()):
        if deger < asgari - 1e-9:
            hata.append(f"{AD[ad]}:  {deger:g} mm < {asgari:g} mm  ( TS EN 81-20 {madde} ).")
    return {"hata": hata, "S": S, "KD": KD, "KU": KU, "M": M, "dip": dip, "ust": ust, "taban": taban,
            "tavan_alti": tavan_alti, "ray_ustu": ray_ustu, "yukselme": yukselme,
            "ust_engel": ust_engel, "agirlik_ust": AK,
            "korkuluk": korkuluk, "dip_aciklik": dip_aciklik, "ust_aciklik": ust_aciklik,
            "kasnaklar": kasnaklar, "kasnak_capi": kasnak_capi, "kotlar": kotlar}


AD = {"siginma": "Sığınma yüksekliği", "en_alt": "Kuyu tabanı – kabinin en alt kısmı",
      "etek": "Kuyu tabanı – kabin eteği", "sase": "Kuyu tabanı – şase / paten / fren bloğu",
      "paten": "Üst paten – kuyu tavanı", "ray": "Üst paten – rayın üst ucu",
      "korkuluk": "Korkuluk – kuyu tavanı",
      "agirlik_ray": "Karşı ağırlık üst pateni – rayın üst ucu"}
#  Paftadaki kısa adlar ( uzun ad ölçüye sığmayıp dışarı taşıyordu )
KISA = {"siginma": "SIĞINMA", "en_alt": "EN ALT", "etek": "ETEK", "sase": "ŞASE",
        "paten": "PATEN", "ray": "RAY", "korkuluk": "KORKULUK", "agirlik_ray": "AĞIRLIK RAYI"}


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _kot(z):
    m = z / 1000.0
    return "±0.00" if abs(m) < 5e-4 else f"{m:+.2f}"


def _kabin(e, kt, kabin_y, ry, S, kasnaklar_y=None, kasnak_capi=0, kr_b=89):
    """Kabinin kesiti:  gövde, taban, etek, şase, patenler, fren bloğu, kasnak."""
    y0, y1 = kabin_y
    D = CGE._dik
    e.append(CGE._ad(D("KABIN", y0, kt["taban_alti"], y1 - y0, kt["tavan"] - kt["taban_alti"]), "kabin"))
    e.append(D("KABIN-IC", y0, kt["doseme"], y1 - y0, kt["ic_ust"] - kt["doseme"]))
    #  Etek:  kabin eşiğinin altında, ön yüzde
    e.append(CGE._ad(D("KABIN", y0, kt["etek_alti"], 30, kt["taban_alti"] - kt["etek_alti"]), "etek"))
    #  Şase:  ray ekseninde dikme, alt ve üst kiriş
    #  Dikme iki ince profil olarak çizilir ( ELEport:  50 + 200 + 50 );
    #  dolu çizilince kabinin kesitini örtüyordu.
    sd = S["sase_dikme_derinlik"]
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(CGE._ad(D("KABIN-IC", x, kt["sase_alt"], 50, kt["sase_ust"] - kt["sase_alt"]), "sase"))
    for z in (kt["sase_alt"], kt["sase_ust"] - 10):
        e.append(D("KABIN-IC", ry - sd / 2.0, z, sd, 10))
    #  Patenler ve fren bloğu
    e.append(CGE._ad(D("PATEN", ry - 35, kt["sase_ust"], 70, S["paten_yukseklik"]), "ust_paten"))
    e.append(CGE._ad(D("PATEN", ry - 35, kt["alt_paten"], 70, S["paten_yukseklik"]), "alt_paten"))
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(CGE._ad(D("SASE", x, kt["fren_alti"], 50, S["fren_blogu_yukseklik"]), "fren"))
    #  Kabin kasnağı ( 2:1 kabin altı ):  kesitte yandan, çapı düşey
    for ky in kasnaklar_y or ():
        e.append(CGE._ad(D("KASNAK", ky - S["kabin_kasnak_genislik"] / 2.0,
                             kt["kasnak_merkez"] - kasnak_capi / 2.0,
                             S["kabin_kasnak_genislik"], kasnak_capi), "kabin_kasnak"))


def _duvarlar(e, g, z0, z1, taban=None, tavan=None):
    k = g["kuyu"]
    D, don, dar = k["derinlik"], k["duvar_on"], k["duvar_arka"]
    for x, w in ((-don, don), (D, dar)):
        e.append(CGE._dik("TARAMA", x, z0, w, z1 - z0, tip="tarama"))
        e.append(CGE._dik("KUYU-DUVAR", x, z0, w, z1 - z0))
    if taban is not None:
        e.append(CGE._dik("TARAMA", -don, taban - don, D + don + dar, don, tip="tarama"))
        e.append(CGE._dik("KUYU-DUVAR", -don, taban - don, D + don + dar, don))
    if tavan is not None:
        e.append(CGE._dik("TARAMA", -don, tavan, D + don + dar, don, tip="tarama"))
        e.append(CGE._dik("KUYU-DUVAR", -don, tavan, D + don + dar, don))


def _kat_kapisi(e, g, z):
    """Ön duvardaki kat kapısı boşluğu ve kat döşemesi."""
    k, kp = g["kuyu"], g["kapi"]
    don = k["duvar_on"]
    e.append(CGE._ad(CGE._dik("KAPI", -don, z, don, kp.get("yukseklik", 2100)), "kat_kapisi"))
    e.append(CGE._cizgi("KUYU-DUVAR", -don - 600, z, -don, z))
    e.append(CGE._ad(CGE._yazi(-don - 300, z + 60, _kot(z), 40), "kot"))


def _kirp(elemanlar, z0, z1, dz=0.0):
    """Tam boy donanım çizimini detay kesitin penceresine kırpar ve kaydırır."""
    cikti = []
    for el in elemanlar:
        el = dict(el)
        if el["tip"] in ("dikdortgen", "tarama"):
            a, b = max(el["y"], z0), min(el["y"] + el["d"], z1)
            if b - a <= 1e-6:
                continue
            el["y"], el["d"] = a + dz, b - a
        elif el["tip"] == "cizgi":
            (x1, y1), (x2, y2) = (el["x1"], el["y1"]), (el["x2"], el["y2"])
            if abs(y2 - y1) < 1e-9:
                if not z0 <= y1 <= z1:
                    continue
            else:
                t0, t1 = sorted(((z0 - y1) / (y2 - y1), (z1 - y1) / (y2 - y1)))
                t0, t1 = max(t0, 0.0), min(t1, 1.0)
                if t1 - t0 <= 1e-9:
                    continue
                x1, y1, x2, y2 = (x1 + (x2 - x1) * t0, el["y1"] + (y2 - el["y1"]) * t0,
                                  x1 + (x2 - x1) * t1, el["y1"] + (y2 - el["y1"]) * t1)
            el.update(x1=x1, y1=y1 + dz, x2=x2, y2=y2 + dz)
        elif el["tip"] in ("daire", "yazi"):
            if not z0 <= el["y"] <= z1:
                continue
            el["y"] += dz
        cikti.append(el)
    return cikti


def _donanim(g, Y, kabin_z, ag_alt, kabin_ezilme=0.0):
    """Raylar, konsollar, tamponlar, gergi, kuyu tepesi, halatlar ( yan bakış,
    tam boy kesitlerle aynı çizim );  detay kesit _kirp ile penceresine alır."""
    B = CKP.Bakis("yan", g["kuyu"]["genislik"])
    P = CKP.plan_parcalari(Y["KD"], g)
    d = []
    CKP.donanim(d, B, g, Y, P, kabin_z, ag_alt, 1.0, kabin_ezilme)
    return d


def _acikliklar(e, olculer, x0):
    """Açıklıklar:  her biri kendi sırasında, değeri ve standardın sınırıyla."""
    for i, (z0, z1, ad, deger, asgari) in enumerate(olculer):
        kot = x0 - 120 - i * 200
        metin = f"{KISA[ad]} {deger:g} ≥ {asgari:g}"
        e.append(CGE._olcu("dusey", (0, z0), (0, z1), kot, metin))


def kuyu_dibi_kesiti(g, cizim_sabitleri=None):
    Y = yerlesim(g, cizim_sabitleri)
    S, dip, KD = Y["S"], Y["dip"], Y["KD"]
    k = g["kuyu"]
    D = k["derinlik"]
    kb = KD["kabin"]
    ry = g["kabin_ray"]["kapi_arasi"]
    dy = g["dusey"]
    z_ust = dip["sase_ust"] + 300
    e = []
    _duvarlar(e, g, Y["taban"], z_ust, taban=Y["taban"])
    _kat_kapisi(e, g, 0.0)
    #  Raylar ve konsollar, tamponlar ( kabininki tam ezilmiş ), gergi düzeni,
    #  halatlar — tam boy kesitlerle aynı çizim, pencereye kırpılmış
    M, H = Y["M"], Y["kotlar"][-1]
    ag_alt = (M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"] + H
              + dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"])
    e += _kirp(_donanim(g, Y, dip["doseme"], ag_alt, dy["kabin_tampon_ezilme"]),
               Y["taban"], z_ust)
    #  Sığınma alanı ( planda yeri, yüksekliği Çizelge 4 )
    sg = KD["siginma"]
    h = SIGINMA_DIP_YUKSEKLIK[g["kuyu_dibi"]["siginma_tipi"]]
    e.append(CGE._ad(CGE._dik("SIGINMA", sg[1], Y["taban"], sg[3] - sg[1], h), "siginma"))
    e.append(CGE._yazi((sg[1] + sg[3]) / 2.0, Y["taban"] + h / 2.0, "SIĞINMA", 36))
    ky = [(kz[1] + kz[3]) / 2.0 for kz in Y["kasnaklar"]]
    _kabin(e, dip, (kb[1], kb[3]), ry, S, ky[:1], Y["kasnak_capi"])
    #  Kotlar ve açıklıklar
    e.append(CGE._yazi(-k["duvar_on"] - 300, Y["taban"] + 60, _kot(Y["taban"]), 40))
    A = Y["dip_aciklik"]
    kasnak_alti = dip["kasnak_merkez"] - Y["kasnak_capi"] / 2.0
    olculer = [(Y["taban"], Y["taban"] + A["siginma"][0], "siginma") + A["siginma"][:2],
               (Y["taban"], Y["taban"] + A["en_alt"][0], "en_alt") + A["en_alt"][:2],
               (Y["taban"], dip["etek_alti"], "etek") + A["etek"][:2],
               (Y["taban"], Y["taban"] + A["sase"][0], "sase") + A["sase"][:2]]
    _acikliklar(e, olculer, -k["duvar_on"] - 700)
    #  Sağ:  kuyu dibi zinciri ( kaide · tampon · çarpma arası · şase altı )
    O = CGE._olcu
    s0, s1 = D + k["duvar_arka"] + 120, D + k["duvar_arka"] + 320
    zs = [Y["taban"], Y["taban"] + dy["kabin_tampon_baba"],
          Y["taban"] + dy["kabin_tampon_baba"] + dy["kabin_tampon_boyu"], 0.0]
    e += [O("dusey", (0, zs[0]), (0, zs[1]), s0, f"KAİDE {dy['kabin_tampon_baba']:g}"),
          O("dusey", (0, zs[1]), (0, zs[2]), s0, f"TAMPON {dy['kabin_tampon_boyu']:g}"),
          O("dusey", (0, zs[2]), (0, zs[3]), s0),
          O("dusey", (0, Y["taban"]), (0, 0.0), s1, f"KUYU DİBİ {g['kuyu_dibi']['derinlik']:g}")]
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e


def kuyu_ustu_kesiti(g, cizim_sabitleri=None):
    Y = yerlesim(g, cizim_sabitleri)
    S, ust, KU = Y["S"], Y["ust"], Y["KU"]
    k = g["kuyu"]
    D = k["derinlik"]
    kb = KU["tavan"]
    ry = g["kabin_ray"]["kapi_arasi"]
    dy = g["dusey"]
    z_alt = -1200.0
    SK = dy["son_kat"]
    e = []
    _duvarlar(e, g, z_alt, SK + k["duvar_on"], tavan=SK)
    _kat_kapisi(e, g, 0.0)
    #  Kuyu tavanının en alt kısmı ( kiriş )
    e.append(CGE._ad(CGE._dik("TARAMA", 0, Y["tavan_alti"], D, S["tavan_kirisi"], tip="tarama"), "tavan_kirisi"))
    e.append(CGE._dik("KUYU-DUVAR", 0, Y["tavan_alti"], D, S["tavan_kirisi"]))
    #  Raylar, makine şasesi, makine, halat bağlantıları, regülatör, halatlar —
    #  tam boy kesitlerle aynı çizim;  karşı ağırlık tam ezilmiş tamponunda
    M, H = Y["M"], Y["kotlar"][-1]
    ag_alt = M["agirlik"]["tampon_ustu"] - dy["agirlik_tampon_ezilme"]
    e += _kirp(_donanim(g, Y, H + Y["yukselme"], ag_alt), H + z_alt, H + SK, -H)
    ky = [(kz[1] + kz[3]) / 2.0 for kz in Y["kasnaklar"]]
    _kabin(e, ust, (kb[1], kb[3]), ry, S, ky[:1], Y["kasnak_capi"])
    #  Tavanda:  etek tahtası ve ( gerekiyorsa ) korkuluk
    e.append(CGE._ad(CGE._dik("KORKULUK", kb[1], ust["tavan"], kb[3] - kb[1], S["etek_tahtasi"]),
                     "etek_tahtasi"))
    if Y["korkuluk"]:
        z = ust["tavan"] + Y["korkuluk"]
        e.append(CGE._ad(CGE._cizgi("KORKULUK", kb[1], z, kb[3], z), "korkuluk"))
        for x in (kb[1], kb[3]):
            e.append(CGE._cizgi("KORKULUK", x, ust["tavan"], x, z))
    #  Sığınma alanı ( kabin tavanında, yüksekliği Çizelge 3 )
    sg = KU["siginma"]
    h = SIGINMA_UST_YUKSEKLIK[g["kabin_ustu"]["siginma_tipi"]]
    e.append(CGE._ad(CGE._dik("SIGINMA", sg[1], ust["tavan"], sg[3] - sg[1], h), "siginma"))
    e.append(CGE._yazi((sg[1] + sg[3]) / 2.0, ust["tavan"] + h / 2.0, "SIĞINMA", 36))
    e.append(CGE._yazi(-k["duvar_on"] - 300, SK + 60, _kot(SK), 40))
    #  Her açıklık kendi engeline:  kuyu tavanı ya da altındaki parça ( şase … )
    A, E = Y["ust_aciklik"], Y["ust_engel"]
    olculer = [(ust["tavan"], E["siginma"][0], "siginma") + A["siginma"][:2],
               (ust["ust_paten"], E["paten"][0], "paten") + A["paten"][:2]]
    if "korkuluk" in A:
        olculer.append((ust["tavan"] + Y["korkuluk"], E["korkuluk"][0], "korkuluk") + A["korkuluk"][:2])
    _acikliklar(e, olculer, -k["duvar_on"] - 700)
    #  Sağ:  kabinin yükselmesi ve son kat
    O = CGE._olcu
    s0, s1 = D + k["duvar_arka"] + 120, D + k["duvar_arka"] + 320
    e += [O("dusey", (0, 0.0), (0, Y["yukselme"]), s0, f"YÜKSELME {Y['yukselme']:g}"),
          O("dusey", (0, Y["yukselme"]), (0, Y["tavan_alti"]), s0),
          O("dusey", (0, Y["tavan_alti"]), (0, SK), s0),
          O("dusey", (0, 0.0), (0, SK), s1, f"SON KAT {SK:g}"),
          O("dusey", (0, ust["ust_paten"]), (0, Y["ray_ustu"]), ry + 150,
            f"RAY {Y['ust_aciklik']['ray'][0]:g} ≥ {RAY_UZANTISI:g}")]
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e

