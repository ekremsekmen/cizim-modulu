# -*- coding: utf-8 -*-
"""
DÜŞEY KESİT PARÇALARI  ( yan ve ön görünüşte ortak çizim )

Her parçanın plandaki kutusu ( x0, y0, x1, y1 ) ve kotları ( z0, z1 ) bilinir;
bakış yönü yatay ekseni seçer:

  YAN ( A-A ):  u = y       kuyu derinliği;  ön duvar ( kat kapıları ) solda
  ÖN  ( B-B ):  u = G − x   kuyunun arkasından kat kapılarına bakış;
                            plandaki SOL duvar sağda görünür

Kasnaklar dönme düzlemlerine göre ya daire ya dikdörtgen görünür:  kabin
kasnakları ve tahrik kasnağı x–z düzleminde döner ( ön kesitte daire ),
karşı ağırlık kasnağı, regülatör ve gergi kasnağı y–z düzleminde ( yan
kesitte daire ).
"""
from cizim import donanim as CDN
from cizim import geometri as CGE
from cizim import makine as CMK
from cizim import kabin_ustu as CKU
from cizim import baglantilar as CB


class Bakis:
    """kesit:  ( eksen, kot, yön ) — kesit düzlemi ve bakış yönü.  Düzlemin
    arkasında ( bakanın gerisinde ) kalan parçalar çizilmez:  A-A kabin
    ekseninden karşı ağırlığa bakar ( referans proje de öbür yanı ayrı bir kesitte
    gösterir ), B-B kabinin arkasından kat kapılarına."""

    def __init__(self, tur, G, kesit=None):
        assert tur in ("yan", "on")
        self.tur, self.G, self.kesit = tur, G, kesit

    def gorunur(self, k):
        if not self.kesit:
            return True
        eksen, c, yon = self.kesit
        lo, hi = (k[0], k[2]) if eksen == "x" else (k[1], k[3])
        return lo < c if yon < 0 else hi > c

    def u(self, x, y):
        return y if self.tur == "yan" else self.G - x

    def aralik(self, k):
        return (k[1], k[3]) if self.tur == "yan" else (self.G - k[2], self.G - k[0])

    def kutu(self, e, katman, k, z0, z1, ad=None, tip="dikdortgen"):
        if not self.gorunur(k):
            return None
        u0, u1 = self.aralik(k)
        el = CGE._dik(katman, u0, min(z0, z1), u1 - u0, abs(z1 - z0), tip=tip)
        if ad:
            CGE._ad(el, ad)
        e.append(el)
        return el

    def halat(self, e, x, y, z0, z1, ad="halat"):
        u = self.u(x, y)
        e.append(CGE._ad(CGE._cizgi("HALAT", u, z0, u, z1), ad))


def uzaklik(B, k):
    """Plandaki kutunun bakana uzaklığı ( büyük olan uzakta;  makine.gorunus ile aynı )."""
    yon = B.kesit[2] if B.kesit else 1.0
    eks = 0 if B.tur == "yan" else 1
    return yon * (k[eks] + k[eks + 2]) / 2.0


def kasnak(e, B, kutu, z, cap, duzlem, ad):
    """duzlem:  "x" ( x–z düzleminde döner ) ya da "y"."""
    if not B.gorunur(kutu):
        return
    daire = (duzlem == "x") == (B.tur == "on")
    if daire:
        u = B.u((kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0)
        e.append(CGE._ad(CGE._daire("KASNAK", u, z, cap / 2.0), ad))
    else:
        B.kutu(e, "KASNAK", kutu, z - cap / 2.0, z + cap / 2.0, ad)


def kasnak_capraz(e, B, merkez, u, R, z, ad, adim=24):
    """Düşey düzlemi planda u doğrultusunda olan kasnak ( çapraz — arka_aski ):
    bakışa göre elips ( jant çemberinin izdüşümü, çizgi parçalarıyla )."""
    import math
    pts = []
    for i in range(adim + 1):
        t = 2.0 * math.pi * i / adim
        x, y = merkez[0] + R * math.cos(t) * u[0], merkez[1] + R * math.cos(t) * u[1]
        pts.append((B.u(x, y), z + R * math.sin(t)))
    for a, b in zip(pts, pts[1:]):
        e.append(CGE._ad(CGE._cizgi("KASNAK", a[0], a[1], b[0], b[1]), ad))


def ray(e, B, r, S, ad):
    """Ray gövdesi tabandan üst ucuna, üstünde ek lamaları."""
    B.kutu(e, "RAY", r["kutu"], r["alt"], r["ust"], ad)
    for z in r["ekler"]:
        B.kutu(e, "RAY", r["kutu"], z - S["ek_lama_boyu"] / 2.0, z + S["ek_lama_boyu"] / 2.0,
               "ray_eki")


def konsollar(e, B, parcalar, kotlar, S, ad):
    """Her konsol kotunda konsolun plandaki parçaları ( plaka, kol, ara kiriş )."""
    for z in kotlar:
        for p in parcalar:
            B.kutu(e, "KONSOL", p, z - S["konsol_yukseklik"], z, ad)


def tamponlar(e, B, kutular, taban, baba, boy, ezilme, S, ad):
    tb, tc = S["tampon_taban"], S["tampon_capi"]
    for k in kutular:
        cx, cy = (k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0
        B.kutu(e, "TAMPON", (cx - tb / 2.0, cy - tb / 2.0, cx + tb / 2.0, cy + tb / 2.0),
               taban, taban + baba, ad + "_kaidesi")
        B.kutu(e, "TAMPON", (cx - tc / 2.0, cy - tc / 2.0, cx + tc / 2.0, cy + tc / 2.0),
               taban + baba, taban + baba + boy - ezilme, ad + "_tamponu")


def kot_isareti(e, u, z, metin, K, yon=1.0):
    """▽ kot işareti:  ucu döşemede, yazı yanında  ( referans proje / LiftDesigner )."""
    w, h = 40 * K, 55 * K
    for a, b in (((u - w, z + h), (u + w, z + h)), ((u - w, z + h), (u, z)), ((u, z), (u + w, z + h))):
        e.append(CGE._cizgi("KUYU-IC", a[0], a[1], b[0], b[1]))
    e.append(CGE._ad(CGE._yazi(u + yon * (w + 20 * K), z + h + 25 * K, metin, 40 * K,
                               hiza="sol" if yon > 0 else "sag"), "kot"))


def kutu_(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def plan_parcalari(KD, g):
    """Plandan:  kapı parçaları, konsol grupları, patenler, kasnaklar."""
    taban = KD["taban"]
    kb = KD["kabin"]
    kx = (kb[0] + kb[2]) / 2.0
    sol = g["agirlik"]["yeri"] == "Sol"
    def ad(a):
        return [kutu_(el) for el in taban if el.get("ad") == a]

    konsol = [kutu_(el) for el in taban if el["katman"] == "KONSOL" and el["tip"] == "dikdortgen"]
    arka = g["agirlik"]["yeri"] == "Arka"

    def agirlik_tarafi(k):
        #  Arkadaki ağırlığın konsolları kabinin arkasında ( 1:1 askı )
        if arka:
            return (k[1] + k[3]) / 2.0 > kb[3]
        return ((k[0] + k[2]) / 2.0 < kx) == sol

    return {
        "kasa": ad("kapi_kasasi"), "esik": ad("kat_esigi"), "kanat": ad("kat_kanadi"),
        "bosluk": ad("kapi_boslugu"), "kabin_esik": ad("kabin_esigi"),
        "kabin_kanat": ad("kabin_kanadi"),
        "konsol_agirlik": [k for k in konsol if agirlik_tarafi(k)],
        "konsol_kabin": [k for k in konsol if not agirlik_tarafi(k)],
        "paten": [kutu_(el) for el in taban if el["katman"] == "PATEN"],
        "sase_dikme": [kutu_(el) for el in taban if el.get("ad") == "sase_dikme"],
        "kabin_kasnak": [kutu_(el) for el in taban if el.get("ad") == "kabin_kasnak"],
        #  1:1 askıda karşı ağırlıkta kasnak yok:  halat çerçevenin ortasına bağlanır
        "agirlik_kasnak": next((kutu_(el) for el in taban if el.get("ad") == "agirlik_kasnak"), None),
    }


def donanim(e, B, g, Y, P, kabin_z, ag_alt, K=1.0, kabin_ezilme=0.0):
    """Raylar, karşı ağırlık, kuyu tepesi, kuyu dibi, halatlar ( iki bakışta ortak )."""
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    taban = Y["taban"]
    #  Raylar, konsollar ve karşı ağırlık BAKANA UZAKLIKLARINA GÖRE çizilir
    #  ( uzaktaki önce ):  A-A'da ağırlık tarafındaki kabin rayı ve ara kiriş
    #  karşı ağırlığın önündedir;  önce hepsi, sonra ağırlık çizildiğinde ray
    #  ağırlık boyunca kayboluyordu.  gruplar:  ( plandaki kutu, elemanlar )
    gruplar = []
    for r in M["raylar"]:
        el = []
        ray(el, B, r, S, r["tur"] + "_rayi")
        gruplar.append((r["kutu"], el))
    ag_raylari = [r for r in M["raylar"] if r["tur"] == "agirlik"]
    kabin_raylari = [r for r in M["raylar"] if r["tur"] == "kabin"]
    uzak = max(kabin_raylari, key=lambda r: r["ust"])
    for parcalar, kotlar, ad in ((P["konsol_agirlik"], ag_raylari[0]["konsollar"], "agirlik_konsolu"),
                                 (P["konsol_kabin"], uzak["konsollar"], "kabin_konsolu")):
        for p in parcalar:
            el = []
            konsollar(el, B, [p], kotlar, S, ad)
            gruplar.append((p, el))
    #  Kuyu dibi:  tamponlar ( ikisi de serbest ) ve gergi düzeni
    KD = Y["KD"]
    for kutular, baba, boy, ezilme, ad in (
            (KD["kabin_tamponlari"], dy["kabin_tampon_baba"], dy["kabin_tampon_boyu"], kabin_ezilme, "kabin"),
            (KD["agirlik_tamponlari"], dy["agirlik_tampon_baba"], dy["agirlik_tampon_boyu"], 0.0, "agirlik")):
        for k in kutular:
            el = []
            tamponlar(el, B, [k], taban, baba, boy, ezilme, S, ad)
            gruplar.append((k, el))
    gr = M["gergi"]
    gp = gr["plan"]
    rgx = (gp[0] + gp[2]) / 2.0
    kol = (gp[0], gr["kol"][0], gp[2], gr["kol"][1])
    el = []
    B.kutu(el, "KONSOL", kol, gr["kol"][2], gr["kol"][3], "gergi_kolu")
    gruplar.append((kol, el))
    ge = S["gergi_agirlik_yakin"] - S["gergi_agirlik_uzak"]          # < 0:  ağırlığın eni
    agr = (rgx + ge / 2.0, gr["agirlik"][0], rgx - ge / 2.0, gr["agirlik"][1])
    el = []
    B.kutu(el, "MAKINE", agr, gr["agirlik"][2], gr["agirlik"][3], "gergi_agirligi")
    gruplar.append((agr, el))
    el = []
    kasnak(el, B, gp, gr["merkez"], gr["cap"], "y", "gergi_kasnagi")
    gruplar.append((gp, el))
    #  Karşı ağırlık:  çerçeve, dolgu, kasnak ve yazı bir grup;  patenler ayrı
    AK = CDN.agirlik_kotlari(M, ag_alt)
    blok = M["agirlik"]["kutu"]
    cer = S["agirlik_cerceve"]
    el = []
    B.kutu(el, "AGIRLIK", blok, AK["alt"], AK["ust"], "agirlik")
    B.kutu(el, "AGIRLIK", (blok[0] + cer, blok[1] + cer, blok[2] - cer, blok[3] - cer),
           AK["alt"] + S["agirlik_kiris"], AK["ust"] - S["agirlik_kiris"], "agirlik_dolgu")
    if P["agirlik_kasnak"]:
        kasnak(el, B, P["agirlik_kasnak"], AK["kasnak_merkez"], g["agirlik"]["kasnak_capi"],
               "x" if g["agirlik"]["yeri"] == "Arka" else "y", "agirlik_kasnagi")
    um = sum(B.aralik(blok)) / 2.0
    if B.gorunur(blok):
        el.append(CGE._ad(CGE._yazi(um, (AK["alt"] + AK["kasnak_merkez"]) / 2.0 - 200,
                                    "KARŞI AĞIRLIK", 40 * K, aci=90), "agirlik_yazi"))
    gruplar.append((blok, el))
    for r in ag_raylari:
        k = r["kutu"]
        if k[3] <= blok[1]:
            pk = (k[0], blok[1] - S["paten_en"], k[2], blok[1])
        else:
            pk = (k[0], blok[3], k[2], blok[3] + S["paten_en"])
        el = []
        B.kutu(el, "PATEN", pk, AK["ust_paten_alt"], AK["ust_paten"], "agirlik_paten")
        B.kutu(el, "PATEN", pk, AK["alt_paten"], AK["alt_paten_ust"], "agirlik_paten")
        gruplar.append((pk, el))
    for _, el in sorted(gruplar, key=lambda ge: uzaklik(B, ge[0]), reverse=True):
        e += el
    kt = CDN.kabin_kotlari(dy, S, kabin_z, g.get("aski"))
    e += CMK.gorunus(CB.kasnak_tasiyicilari(g, S, kt["kasnak_merkez"]),
                     B, CGE._dik, CGE._daire, CGE._cizgi)
    capraz = (M.get("KU") or {}).get("capraz")
    if capraz:
        #  Arkadaki ağırlıkla 2:1:  kabin üstündeki çapraz kasnaklar ( elips )
        for m, kutu in zip(capraz["kasnaklar"], capraz["kutular"]):
            if B.gorunur(kutu):
                kasnak_capraz(e, B, m, capraz["u"], capraz["Rk"], kt["kasnak_merkez"], "kabin_kasnagi")
    if "sase" not in M:
        return AK, kt
    #  Kuyu tepesinde ya da makine dairesinde:  makine şasesi, bağlantılar,
    #  makine ( makine.py:  parça parça, izdüşümüyle ), regülatör, ( odada )
    #  kumanda panosu
    for ad in ("agirlik_baglanti", "kabin_baglanti"):          # 1:1 askıda yok
        p = M[ad]
        if p:
            B.kutu(e, "BAGLANTI", p[:4], p[4], p[5], ad)
    e += CMK.gorunus(M["sase_parcalari"] + M["makine"], B, CGE._dik, CGE._daire, CGE._cizgi)
    #  Makine dairesinde halatın tahrik kasnağındaki sarım açısı ( LiftDesigner
    #  "kasnak düzenlemesi" gibi ) — kasnağın daire göründüğü ön kesitte
    #  Kasnak, ekseni bakış yönündeyse daire görünür:  yan ağırlıkta B-B'de,
    #  arkadaki ağırlıkta ( halat düzlemi derinlik boyunca ) A-A'da
    duz_ = (M.get("KU") or {}).get("duzlem")
    daire_bakis = "yan" if duz_ is not None and duz_.yon == "y" else "on"
    if "MD" in M and B.tur == daire_bakis and B.gorunur(M["kasnak"][:4]):
        ks = M["kasnak"]
        e.append(CGE._ad(CGE._yazi(B.u((ks[0] + ks[2]) / 2.0, 0), ks[4] + g["makine"]["tahrik_kasnak_capi"] / 2.0
                                   + 180 * K, f"SARIM AÇISI {M['sarim_acisi']:.0f}°", 40 * K), "sarim_acisi"))
    if M["mrl"]:
        e += CMK.gorunus(M["halat_konsolu"], B, CGE._dik, CGE._daire, CGE._cizgi)
    rg = M["regulator"]
    B.kutu(e, "MAKINE", rg[:4], rg[4], rg[5], "regulator")
    if M.get("pano"):
        p = M["pano"]
        B.kutu(e, "PANO", p[:4], p[4], p[5], "kumanda_panosu")
    rk = M["regulator_kasnak"]
    kasnak(e, B, rk[:4], rk[4], gr["cap"], "y", "regulator_kasnagi")
    #  Halatlar
    KU = M["KU"]
    zk = kt["kasnak_merkez"]
    zt = M["kasnak"][4]
    if KU.get("dogrudan"):
        _halatlar_1_1(e, B, g, M, KU, kt, AK, zt)
        _regulator_halati(e, B, M, gr, rk, rgx)
        return AK, kt
    if KU.get("capraz"):
        _halatlar_capraz(e, B, M, KU, kt, AK, zt)
        _regulator_halati(e, B, M, gr, rk, rgx)
        return AK, kt
    (xl, y0), (xr, _) = KU["halatlar"]
    yakin, uzak_x = KU["yakin"], KU["uzak"]
    zkb = M["kabin_baglanti"][4]
    zab = M["agirlik_baglanti"][4]
    za = AK["kasnak_merkez"]
    dx, dy_ = KU["ag_dusus"]
    tx1, ty1 = KU["ag_teget"]
    tx2, ty2 = KU["ag_teget2"]
    #  Ağırlık tarafı:  saptırma kasnağı varsa ( makine dairesi ) tahrik
    #  kasnağından ona ortak teğet, ondan ağırlık kasnağına dik iner.
    if M.get("agirlik_yolu"):
        ad_, ay_, az_ = M["agirlik_dusus"]
        agirlik = list(M["agirlik_yolu"]) + [((ad_, ay_, az_), (tx1, ty1, za))]
    else:
        agirlik = [((dx, dy_, zt), (tx1, ty1, za))]         # tahrik kasnağı → ağırlık kasnağı
    for (x0_, y0_, z0), (x1_, y1_, z1) in [
            ((yakin, y0, zk), (yakin, y0, zt)),                 # kabin → tahrik kasnağı
            ((uzak_x, y0, zk), (uzak_x, y0, zkb))] + agirlik + [   # kabin → kabin bağlantısı
            ((tx2, ty2, za), (tx2, ty2, zab))]:                 # ağırlık kasnağı → bağlantı
        if B.gorunur((x0_, y0_, x0_, y0_)):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(x0_, y0_), z0, B.u(x1_, y1_), z1), "aski_halati"))
    if B.tur == "on":
        #  Kabinin altında iki kasnak arası
        r = g["aski"]["kasnak_capi"] / 2.0
        us = sorted(B.u((k[0] + k[2]) / 2.0, 0) for k in P["kabin_kasnak"])
        e.append(CGE._ad(CGE._cizgi("HALAT", us[0], zk - r, us[-1], zk - r), "aski_halati"))
    _regulator_halati(e, B, M, gr, rk, rgx)
    return AK, kt


def _regulator_halati(e, B, M, gr, rk, rgx):
    """Regülatör halatı:  tepedeki kasnaktan gergi kasnağına ( iki kol )."""
    R = gr["cap"] / 2.0
    ry_ = M["regulator_y"]
    for yy in (ry_ - R, ry_ + R):
        if B.gorunur((rgx, yy, rgx, yy)):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(rgx, yy), rk[4], B.u(rgx, yy), gr["merkez"]),
                             "regulator_halati"))


def _halatlar_capraz(e, B, M, KU, kt, AK, zt):
    """Arkadaki ağırlıkla 2:1 ( arka_aski ):  kabin bağlantısından ( H ) ön
    kasnağa, iki kasnağın altından ( jantların alt noktası ) arka kasnağa,
    oradan ( P ) tahrik kasnağına;  tahrik kasnağından ( W ) ağırlık kasnağına,
    öbür teğetinden ( Hw ) ağırlığın bağlantısına."""
    A = KU["capraz"]
    zk, Rk = kt["kasnak_merkez"], A["Rk"]
    zkb, zab = M["kabin_baglanti"][4], M["agirlik_baglanti"][4]
    za = AK["kasnak_merkez"]
    (px, py), (hx, hy) = A["P"], A["H"]
    (wx, wy), (bx, by) = A["W"], A["Hw"]
    if M.get("agirlik_yolu"):
        ad_, ay_, az_ = M["agirlik_dusus"]
        agirlik = list(M["agirlik_yolu"]) + [((ad_, ay_, az_), (wx, wy, za))]
    else:
        agirlik = [((wx, wy, zt), (wx, wy, za))]

    def gorunur(x, y):
        return B.gorunur((x - 1.0, y - 1.0, x + 1.0, y + 1.0))
    (ax_, ay2), (ox_, oy_) = A["kasnaklar"]
    for (x0_, y0_, z0), (x1_, y1_, z1) in [((px, py, zk), (px, py, zt)),
                                            ((hx, hy, zk), (hx, hy, zkb))] + agirlik + [
            ((bx, by, za), (bx, by, zab)), ((ax_, ay2, zk - Rk), (ox_, oy_, zk - Rk))]:
        if gorunur(x0_, y0_) or gorunur(x1_, y1_):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(x0_, y0_), z0, B.u(x1_, y1_), z1), "aski_halati"))


def _halatlar_1_1(e, B, g, M, KU, kt, AK, zt):
    """1:1 askıda halatlar:  kabin şasesinin üst kirişinin ortasındaki
    bağlantıdan tahrik kasnağına;  kasnağın öbür teğetinden ( saptırma varsa
    ondan ) karşı ağırlığın ortasındaki bağlantıya.  Kabin bağlantısı üst
    kirişin üstünde, halat soketlerinin boyunda ( donanim.kabin_kotlari )."""
    hx, hy = KU["kabin_nokta"]
    ax, ay = KU["ag_nokta"]
    a = g["aski"]
    #  Kabin bağlantısı:  halat demetinin izi, üst kirişten soketlerin tepesine
    dk = CMK.halat_deligi(hx, hy, a["halat_adedi"], a["halat_capi"], 0.0, KU["duzlem"].eksen)
    B.kutu(e, "BAGLANTI", dk, kt["sase_ust"], kt["baglanti_ust"], "kabin_halat_baglantisi")
    if M.get("agirlik_yolu"):
        ad_, ay_, az_ = M["agirlik_dusus"]
        agirlik = list(M["agirlik_yolu"]) + [((ad_, ay_, az_), (ax, ay, AK["ust"]))]
    else:
        dx, dy_ = KU["ag_dusus"]
        agirlik = [((dx, dy_, zt), (ax, ay, AK["ust"]))]
    #  Halat düzlemi kesit düzleminin İÇİNDE olabilir ( arkadaki ağırlıkta 1:1
    #  askı kabin ekseninde, A-A de oradan geçer ):  düzlemdeki halat kesilir ve
    #  çizilir — nokta 1 mm'lik kutuyla sorulur.
    def gorunur(x, y):
        return B.gorunur((x - 1.0, y - 1.0, x + 1.0, y + 1.0))
    for (x0_, y0_, z0), (x1_, y1_, z1) in [((hx, hy, kt["baglanti_ust"]), (hx, hy, zt))] + agirlik:
        if gorunur(x0_, y0_) or gorunur(x1_, y1_):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(x0_, y0_), z0, B.u(x1_, y1_), z1), "aski_halati"))


def kabin_on(e, B, g, Y, P, kt):
    """Kabin ön görünüşte ( arkasından ):  gövde, iç, şase, patenler, fren blokları, kasnaklar."""
    S, KD = Y["S"], Y["KD"]
    kb = KD["kabin"]
    B.kutu(e, "KABIN", kb, kt["taban_alti"], kt["tavan"], "kabin")
    py = S["kabin_pano_yan"]
    B.kutu(e, "KABIN-IC", (kb[0] + py, kb[1], kb[2] - py, kb[3]), kt["doseme"], kt["ic_ust"])
    kp = g["kapi"]
    #  Kabin kapısı kabinin önündedir — arkadan bakışta görünmez ( kesik )
    B.kutu(e, "GIZLI", (kp["sol_pay"], kb[1], kp["sol_pay"] + kp["genislik"], kb[1] + 1),
           kt["doseme"], kt["doseme"] + kp["yukseklik"], "kabin_kapisi")
    sx0 = min(k[0] for k in P["sase_dikme"])
    sx1 = max(k[2] for k in P["sase_dikme"])
    for k in P["sase_dikme"]:
        B.kutu(e, "SASE", k, kt["sase_alt"], kt["sase_ust"], "sase")
    sy0 = min(k[1] for k in P["sase_dikme"])
    sy1 = max(k[3] for k in P["sase_dikme"])
    for z in (kt["sase_alt"], kt["sase_ust"] - 10):
        B.kutu(e, "SASE", (sx0, sy0, sx1, sy1), z, z + 10, "sase_kirisi")
    for p in P["paten"]:
        B.kutu(e, "PATEN", p, kt["ust_paten_alt"], kt["ust_paten"], "ust_paten")
        B.kutu(e, "PATEN", p, kt["alt_paten"], kt["alt_paten_ust"], "alt_paten")
        B.kutu(e, "SASE", p, kt["fren_alti"], kt["fren_alti"] + S["fren_blogu_yukseklik"], "fren")
    for k in P["kabin_kasnak"]:
        kasnak(e, B, k, kt["kasnak_merkez"], g["aski"]["kasnak_capi"], "x", "kabin_kasnagi")


def korkuluk(e, B, Y, kt):
    """Küpeşte ve uç dikmeleri, planla aynı konum ve kenara özgü yükseklikte."""
    for kutu, yukseklik in CKU.korkuluklar(Y["KU"]):
        if not B.gorunur(kutu):
            continue
        u0, u1 = B.aralik(kutu)
        z0, z1 = kt["tavan"], kt["tavan"] + yukseklik
        for a, b in (((u0, z0), (u0, z1)), ((u0, z1), (u1, z1)), ((u1, z1), (u1, z0))):
            if a != b:
                e.append(CGE._ad(CGE._cizgi("KORKULUK", *a, *b), "korkuluk"))
