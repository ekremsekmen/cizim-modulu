# -*- coding: utf-8 -*-
"""
DÜŞEY KESİTLER  ( kuyunun derinliği boyunca, kabin ekseninden )

  KUYU DİBİ DÜŞEY KESİTİ   kabin tam ezilmiş tamponunun üstünde
  KUYU ÜSTÜ DÜŞEY KESİTİ   kabin en üst konumunda:  karşı ağırlık tam ezilmiş
                           tamponunun üstünde + 0,035 · v²  ( m.5.2.5.6.1 )

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
              m.5.2.5.7.2 b  paten ve halat bağlantısı ≥ 0,10
              m.5.2.5.7.2 c  korkuluğun üstü ≥ 0,30
              m.5.2.5.6.1   raylar patene en az 0,10 m daha kılavuzluk eder
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kabin_ustu as CKU
from cizim import kuyu_dibi as CKD
from cizim import sabitler as CS

#  Çizelge 3 / Çizelge 4 — sığınma alanının YÜKSEKLİĞİ ( mm )
SIGINMA_UST_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0}
SIGINMA_DIP_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0}
DIP_EN_ALT = 500.0          # m.5.2.5.8.2 a
DIP_ETEK = 100.0            # m.5.2.5.8.2 a 1)
DIP_RAYA_YAKIN = 100.0      # m.5.2.5.8.2 a 2) · Şekil 7  ( XH ≤ 0,15 m )
UST_PATEN = 100.0           # m.5.2.5.7.2 b
UST_KORKULUK = 300.0        # m.5.2.5.7.2 c 1)
RAY_UZANTISI = 100.0        # m.5.2.5.6.1  ( 0,1 + 0,035·v²;  0,035·v² konumda )
ETEK_BOYU = 750.0           # m.5.4.5.1:  kabin eteğinin düşey kısmı en az 0,75 m
DUSEY_ALANLAR = ("kabin_ic_yukseklik", "kabin_paten_arasi", "son_kat", "beyan_hizi",
                 "durak_adedi", "kat_yuksekligi", "kabin_tampon_baba", "kabin_tampon_boyu",
                 "kabin_carpma_arasi", "kabin_tampon_ezilme", "agirlik_tampon_baba",
                 "agirlik_tampon_boyu", "agirlik_carpma_arasi", "agirlik_tampon_ezilme")


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def kabin_kotlari(dy, S, z):
    """Döşemesi z kotundaki kabinin parça kotları ( ELEport kabini )."""
    tavan = z + dy["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"]
    sase_alt = z - S["sase_alt_derinlik"]
    sase_ust = sase_alt + dy["kabin_paten_arasi"]
    return {"doseme": z, "taban_alti": z - S["kabin_taban_kalinlik"],
            "etek_alti": z - ETEK_BOYU, "fren_alti": z - S["kabin_taban_kalinlik"]
            - S["fren_blogu_yukseklik"], "sase_alt": sase_alt, "sase_ust": sase_ust,
            "alt_paten": sase_alt - S["paten_yukseklik"], "ust_paten": sase_ust + S["paten_yukseklik"],
            "ic_ust": z + dy["kabin_ic_yukseklik"], "tavan": tavan,
            "kasnak_merkez": z - S["kabin_kasnak_derinlik"]}


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    dy = g.get("dusey") or {}
    hata = [f"dusey.{a}: sıfırdan büyük bir sayı olmalı ( {dy.get(a)!r} )."
            for a in DUSEY_ALANLAR if not (_sayi(dy.get(a)) and dy[a] > 0)]
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
    yukselme = dy["agirlik_carpma_arasi"] + dy["agirlik_tampon_ezilme"] + b35
    ust = kabin_kotlari(dy, S, yukselme)
    tavan_alti = dy["son_kat"] - S["tavan_kirisi"]
    ray_ustu = tavan_alti
    korkuluk = max((k["yukseklik"] for k in KU["kenarlar"].values() if k["gerekli"]), default=0.0)
    ust_aciklik = {
        "siginma": (tavan_alti - ust["tavan"], SIGINMA_UST_YUKSEKLIK[ku["siginma_tipi"]],
                    "m.5.2.5.7.1 · Çizelge 3"),
        "paten": (tavan_alti - ust["ust_paten"], UST_PATEN, "m.5.2.5.7.2 b"),
        "ray": (ray_ustu - ust["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.1"),
    }
    if korkuluk:
        ust_aciklik["korkuluk"] = (tavan_alti - (ust["tavan"] + korkuluk), UST_KORKULUK,
                                   "m.5.2.5.7.2 c")
    for ad, (deger, asgari, madde) in list(dip_aciklik.items()) + list(ust_aciklik.items()):
        if deger < asgari - 1e-9:
            hata.append(f"{AD[ad]}:  {deger:g} mm < {asgari:g} mm  ( TS EN 81-20 {madde} ).")
    return {"hata": hata, "S": S, "KD": KD, "KU": KU, "dip": dip, "ust": ust, "taban": taban,
            "tavan_alti": tavan_alti, "ray_ustu": ray_ustu, "yukselme": yukselme,
            "korkuluk": korkuluk, "dip_aciklik": dip_aciklik, "ust_aciklik": ust_aciklik,
            "kasnaklar": kasnaklar, "kasnak_capi": kasnak_capi}


AD = {"siginma": "Sığınma yüksekliği", "en_alt": "Kuyu tabanı – kabinin en alt kısmı",
      "etek": "Kuyu tabanı – kabin eteği", "sase": "Kuyu tabanı – şase / paten / fren bloğu",
      "paten": "Üst paten – kuyu tavanı", "ray": "Üst paten – rayın üst ucu",
      "korkuluk": "Korkuluk – kuyu tavanı"}
#  Paftadaki kısa adlar ( uzun ad ölçüye sığmayıp dışarı taşıyordu )
KISA = {"siginma": "SIĞINMA", "en_alt": "EN ALT", "etek": "ETEK", "sase": "ŞASE",
        "paten": "PATEN", "ray": "RAY", "korkuluk": "KORKULUK"}


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
    e.append(CGE._yazi(-don - 300, z + 60, _kot(z), 40))


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
    #  Kılavuz ray:  kuyu tabanından yukarı ( kesitte flanş eni kadar )
    e.append(CGE._ad(CGE._dik("RAY", ry - 45, Y["taban"], 90, z_ust - Y["taban"]), "kabin_rayi"))
    #  Tamponlar:  kabin ( tam ezilmiş ) ve karşı ağırlık ( serbest )
    tb, tc = S["tampon_taban"], S["tampon_capi"]
    for merkez, baba, boy, ezilme, ad in (
            (ry, dy["kabin_tampon_baba"], dy["kabin_tampon_boyu"], dy["kabin_tampon_ezilme"], "kabin"),
            (CKD._merkez(KD["agirlik_tamponlari"][0])[1], dy["agirlik_tampon_baba"],
             dy["agirlik_tampon_boyu"], 0.0, "agirlik")):
        e.append(CGE._ad(CGE._dik("TAMPON", merkez - tb / 2.0, Y["taban"], tb, baba), ad + "_kaidesi"))
        e.append(CGE._ad(CGE._dik("TAMPON", merkez - tc / 2.0, Y["taban"] + baba, tc, boy - ezilme),
                         ad + "_tamponu"))
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
    e.append(CGE._ad(CGE._dik("RAY", ry - 45, z_alt, 90, Y["ray_ustu"] - z_alt), "kabin_rayi"))
    _kabin(e, ust, (kb[1], kb[3]), ry, S)
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
    A = Y["ust_aciklik"]
    olculer = [(ust["tavan"], Y["tavan_alti"], "siginma") + A["siginma"][:2],
               (ust["ust_paten"], Y["tavan_alti"], "paten") + A["paten"][:2]]
    if "korkuluk" in A:
        olculer.append((ust["tavan"] + Y["korkuluk"], Y["tavan_alti"], "korkuluk") + A["korkuluk"][:2])
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
