# -*- coding: utf-8 -*-
"""
KUYU DÜŞEY KESİTLERİ  ( tam boy, 1/50 )

  A-A  YAN KESİT   kuyu derinliği boyunca;  ön duvar ( kat kapıları ) solda.
                   Kabin EN ALT durakta, karşı ağırlık yukarıda
                   ( ELEport "Cabin at Bottom Floor" ).
  B-B  ÖN KESİT    kuyu genişliği boyunca, kuyunun arkasından kat kapılarına
                   bakış ( plandaki sol duvar sağda görünür ).  Kabin EN ÜST
                   durakta, karşı ağırlık aşağıda ( ELEport "Cabin at Top
                   Floor", LiftDesigner "Dikey 1:50" ).

İkisi de gerçek ölçekte, bütün duraklarla ( LiftDesigner gibi;  ELEport ara
katları kırar ).  Çizilenler:

  · kuyu duvarları, kuyu dibi ve tavan döşemesi, kat döşemeleri, kat kapıları
    ( yanda kesit, önde görünüş ), kotlar ve durak adları
  · kabin ve karşı ağırlık raylarının tamamı:  üst uçları, konsolları
    ( konsollar arası:  hesap programının girdisi ), ek yerleri
  · kabin ( şase, patenler, fren blokları, 2:1 kasnakları ) ve karşı ağırlık
    ( çerçeve, kasnak, patenler )
  · makine dairesizde kuyu tepesi:  makine şasesi, makine, tahrik kasnağı,
    halat bağlantıları, hız regülatörü;  kuyu dibinde tamponlar ve gergi düzeni
  · askı halatları ( 2:1 ) ve regülatör halatı

Kotlar donanim.py'de, planla aynı yerlerden;  açıklık denetimleri dusey.py'de
( bu kesitler de aynı yerleşimle durur ).
"""
from cizim import dusey as CDU
from cizim import geometri as CGE
from cizim import kesit_parcalari as CKP

OLCEK = 50


def yerlesim(g, cizim_sabitleri=None):
    Y = CDU.yerlesim(g, cizim_sabitleri)
    if Y["hata"]:
        return Y
    if not Y["M"]["mrl"]:
        Y["hata"].append("Tam boy düşey kesitler bugün yalnız makine dairesiz ( kuyu üstü ) "
                         "düzeni çizer;  makine daireli kesit için makine dairesinin yüksekliği "
                         "ve döşeme kalınlığı gerekir.")
    return Y


def dogrula(g):
    hata = CDU.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _duvar(e, u, z, w, h, ad=None):
    e.append(CGE._dik("TARAMA", u, z, w, h, tip="tarama"))
    el = CGE._dik("KUYU-DUVAR", u, z, w, h)
    if ad:
        CGE._ad(el, ad)
    e.append(el)


def _zincir(e, kot, noktalar, metinler=None):
    metinler = metinler or {}
    for i, (a, b) in enumerate(zip(noktalar, noktalar[1:])):
        if b - a > 1e-6:
            e.append(CGE._olcu("dusey", (0, a), (0, b), kot, metinler.get(i)))


def _kat_seviyeleri(e, g, S, kotlar, u_duvar, K, yon):
    """Kot işaretleri ve durak adları ( duvarın dışında )."""
    for i, z in enumerate(kotlar):
        CKP.kot_isareti(e, u_duvar + yon * 200 * K, z, CDU._kot(z), K, yon)
        e.append(CGE._ad(CGE._yazi(u_duvar + yon * 120 * K, z + 1100, f"{i + 1}. DURAK", 45 * K,
                                   hiza="sol" if yon > 0 else "sag"), "durak_adi"))


def _olculer_sol(e, Y, u0, K, kotlar, tavan, g):
    """Kuyu dibi + kat yükseklikleri + son kat · seyir · kuyu yüksekliği."""
    H = kotlar[-1]
    s0, s1, s2 = (u0 - (250 * i) * K for i in range(3))
    zincir = [Y["taban"]] + kotlar + [tavan]
    _zincir(e, s0, zincir, {0: f"KUYU DİBİ {-Y['taban']:g}",
                            len(zincir) - 2: f"SON KAT {tavan - H:g}"})
    e.append(CGE._olcu("dusey", (0, 0.0), (0, H), s1, f"SEYİR {H:g}"))
    e.append(CGE._olcu("dusey", (0, Y["taban"]), (0, tavan), s2,
                       f"KUYU YÜKSEKLİĞİ {tavan - Y['taban']:g}"))


def _konsol_zinciri(e, kot, r, tavan, ad, aralik):
    noktalar = [r["alt"]] + r["konsollar"] + [r["ust"], tavan]
    orta = len(r["konsollar"]) // 2
    _zincir(e, kot, noktalar, {0: f"İLK KONSOL {r['konsollar'][0] - r['alt']:g}",
                               orta: f"{ad} KONSOL ARASI {aralik:g}"})


def yan_kesit(g, cizim_sabitleri=None):
    """A-A:  kabin en alt durakta."""
    Y = yerlesim(g, cizim_sabitleri)
    S, M, KD, dy = Y["S"], Y["M"], Y["KD"], g["dusey"]
    k = g["kuyu"]
    G, D, don, dar = k["genislik"], k["derinlik"], k["duvar_on"], k["duvar_arka"]
    K = OLCEK / 20.0
    B = CKP.Bakis("yan", G)
    P = CKP.plan_parcalari(Y["KD"], g)
    kotlar = Y["kotlar"]
    H = kotlar[-1]
    tavan = H + dy["son_kat"]
    taban = Y["taban"]
    kapi_h = g["kapi"]["yukseklik"]
    bosluk_h = kapi_h + S["kapi_ust_payi"]
    e = []
    #  Ön duvar kapı boşluklarıyla, arka duvar, kuyu dibi ve tavan döşemesi
    z = taban - don
    for zk in kotlar:
        _duvar(e, -don, z, don, zk - z)
        z = zk + bosluk_h
    _duvar(e, -don, z, don, tavan + don - z)
    _duvar(e, D, taban - don, dar, tavan + don - (taban - don))
    _duvar(e, 0, taban - don, D, don)
    _duvar(e, 0, tavan, D, don)
    #  Kuyu tavanının en alt kısmı ( kiriş payı )
    e.append(CGE._dik("TARAMA", 0, Y["tavan_alti"] + H, D, S["tavan_kirisi"], tip="tarama"))
    e.append(CGE._ad(CGE._dik("KUYU-DUVAR", 0, Y["tavan_alti"] + H, D, S["tavan_kirisi"]),
                     "tavan_kirisi"))
    #  Katlar:  döşeme, kat kapısı ( kasa, eşik, kanatlar )
    L = 240 * K
    for zk in kotlar:
        _duvar(e, -don - L, zk - S["kat_doseme_kalinlik"], L, S["kat_doseme_kalinlik"], "kat_dosemesi")
        for kk in P["kasa"]:
            e.append(CGE._ad(CGE._dik("KAPI", kk[1], zk - S["esik_kalinlik"], kk[3] - kk[1],
                                      kapi_h + S["esik_kalinlik"]), "kapi_kasasi"))
        for kk in P["esik"]:
            e.append(CGE._ad(CGE._dik("KAPI", kk[1], zk - S["esik_kalinlik"], kk[3] - kk[1],
                                      S["esik_kalinlik"]), "kat_esigi"))
        for kk in P["kanat"]:
            e.append(CGE._ad(CGE._dik("KAPI", kk[1], zk, kk[3] - kk[1], kapi_h), "kat_kapisi"))
    _kat_seviyeleri(e, g, S, kotlar, -don - L, K, -1.0)
    CKP.kot_isareti(e, -don - L + 200 * K * -1.0, taban, CDU._kot(taban), K, -1.0)
    AK, kt = CKP.donanim(e, B, g, Y, P, 0.0, M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"] + H, K)
    kb = KD["kabin"]
    ky = [(kz[1] + kz[3]) / 2.0 for kz in P["kabin_kasnak"]]
    CDU._kabin(e, kt, (kb[1], kb[3]), g["kabin_ray"]["kapi_arasi"], S, ky[:1], g["aski"]["kasnak_capi"])
    #  Ölçüler
    _olculer_sol(e, Y, -don - L - 700 * K, K, kotlar, tavan, g)
    uzak = max((r for r in M["raylar"] if r["tur"] == "kabin"), key=lambda r: r["ust"])
    r0 = D + dar + 150 * K
    _konsol_zinciri(e, r0, uzak, tavan, "KABİN RAYI", dy["kabin_konsol_arasi"])
    sa = M["sase"]
    _zincir(e, r0 + 250 * K, [sa[4], sa[5], M["kapak"][5], tavan],
            {0: f"ŞASE {sa[5] - sa[4]:g}", 1: f"MAKİNE {M['kapak'][5] - sa[5]:g}"})
    e.append(CGE._olcu("dusey", (0, 0.0), (0, kapi_h), -don - 120 * K, f"KAPI {kapi_h:g}"))
    e.append(CGE._olcu("yatay", (0, taban), (D, taban), taban - don - 250 * K, f"KUYU DERİNLİĞİ {D:g}"))
    CGE._yazilari_yerlestir(e, CGE.OLCU_YAZI * K)
    return e


def on_kesit(g, cizim_sabitleri=None):
    """B-B:  kabin en üst durakta;  kuyunun arkasından kat kapılarına bakış."""
    Y = yerlesim(g, cizim_sabitleri)
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    k = g["kuyu"]
    G, D, ds, dg, don = k["genislik"], k["derinlik"], k["duvar_sol"], k["duvar_sag"], k["duvar_on"]
    K = OLCEK / 20.0
    B = CKP.Bakis("on", G)
    P = CKP.plan_parcalari(Y["KD"], g)
    kotlar = Y["kotlar"]
    H = kotlar[-1]
    tavan = H + dy["son_kat"]
    taban = Y["taban"]
    kapi_h = g["kapi"]["yukseklik"]
    e = []
    #  Yan duvarlar ( görünüşte plandaki sağ duvar solda ), kuyu dibi, tavan
    _duvar(e, -dg, taban - don, dg, tavan + don - (taban - don))
    _duvar(e, G, taban - don, ds, tavan + don - (taban - don))
    _duvar(e, 0, taban - don, G, don)
    _duvar(e, 0, tavan, G, don)
    e.append(CGE._dik("TARAMA", 0, Y["tavan_alti"] + H, G, S["tavan_kirisi"], tip="tarama"))
    e.append(CGE._ad(CGE._dik("KUYU-DUVAR", 0, Y["tavan_alti"] + H, G, S["tavan_kirisi"]),
                     "tavan_kirisi"))
    #  Kat kapıları ön duvarda ( görünüş ):  kasa, boşluk, kanat ayrımı, durak numarası
    bos = P["bosluk"][0]
    kasa_x0 = min(kk[0] for kk in P["kasa"])
    kasa_x1 = max(kk[2] for kk in P["kasa"])
    ayrim = sorted(kk[2] for kk in P["kanat"])[0] if len(P["kanat"]) > 1 else None
    for i, zk in enumerate(kotlar):
        B.kutu(e, "KAPI", (kasa_x0, -1, kasa_x1, 0), zk, zk + kapi_h + S["kapi_ust_payi"], "kapi_kasasi")
        B.kutu(e, "KAPI", bos, zk, zk + kapi_h, "kat_kapisi")
        if ayrim is not None:
            u = B.u(ayrim, 0)
            e.append(CGE._cizgi("KAPI", u, zk, u, zk + kapi_h))
        e.append(CGE._ad(CGE._yazi(B.u((bos[0] + bos[2]) / 2.0, 0), zk + kapi_h * 0.6, f"{i + 1}",
                                   90 * K), "durak_no"))
    _kat_seviyeleri(e, g, S, kotlar, -dg, K, -1.0)
    CKP.kot_isareti(e, -dg - 200 * K, taban, CDU._kot(taban), K, -1.0)
    AK, kt = CKP.donanim(e, B, g, Y, P, H, M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"], K)
    CKP.kabin_on(e, B, g, Y, P, kt)
    #  Ölçüler
    _olculer_sol(e, Y, -dg - 700 * K, K, kotlar, tavan, g)
    ag = min((r for r in M["raylar"] if r["tur"] == "agirlik"), key=lambda r: r["ust"])
    r0 = G + ds + 150 * K
    _konsol_zinciri(e, r0, ag, tavan, "AĞIRLIK RAYI", dy["agirlik_konsol_arasi"])
    _zincir(e, r0 + 250 * K, [M["agirlik"]["tampon_ustu"], AK["alt"], AK["ust"]],
            {0: f"ÇARPMA ARASI {dy['agirlik_carpma_arasi']:g}",
             1: f"KARŞI AĞIRLIK {AK['ust'] - AK['alt']:g}"})
    e.append(CGE._olcu("yatay", (0, taban), (G, taban), taban - don - 250 * K,
                       f"KUYU GENİŞLİĞİ {G:g}"))
    CGE._yazilari_yerlestir(e, CGE.OLCU_YAZI * K)
    return e
