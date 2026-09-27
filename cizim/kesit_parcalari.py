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


class Bakis:
    """kesit:  ( eksen, kot, yön ) — kesit düzlemi ve bakış yönü.  Düzlemin
    arkasında ( bakanın gerisinde ) kalan parçalar çizilmez:  A-A kabin
    ekseninden karşı ağırlığa bakar ( ELEport da öbür yanı ayrı bir kesitte
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
    """▽ kot işareti:  ucu döşemede, yazı yanında  ( ELEport / LiftDesigner )."""
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
    kapi = [kutu_(el) for el in taban if el["katman"] == "KAPI" and el["tip"] == "dikdortgen"]
    konsol = [kutu_(el) for el in taban if el["katman"] == "KONSOL" and el["tip"] == "dikdortgen"]

    def agirlik_tarafi(k):
        return ((k[0] + k[2]) / 2.0 < kx) == sol

    return {
        "kasa": [k for k in kapi if k[1] < 0 and k[3] <= 0 and k[1] > -g["kuyu"]["duvar_on"]],
        "esik": [k for k in kapi if k[1] == 0],
        "kanat": [k for k in kapi if k[1] > 0],
        "bosluk": [k for k in kapi if k[1] <= -g["kuyu"]["duvar_on"]],
        "konsol_agirlik": [k for k in konsol if agirlik_tarafi(k)],
        "konsol_kabin": [k for k in konsol if not agirlik_tarafi(k)],
        "paten": [kutu_(el) for el in taban if el["katman"] == "PATEN"],
        "sase_dikme": [kutu_(el) for el in taban if el.get("ad") == "sase_dikme"],
        "kabin_kasnak": [kutu_(el) for el in taban if el.get("ad") == "kabin_kasnak"],
        "agirlik_kasnak": next(kutu_(el) for el in taban if el.get("ad") == "agirlik_kasnak"),
    }


def donanim(e, B, g, Y, P, kabin_z, ag_alt, K=1.0, kabin_ezilme=0.0):
    """Raylar, karşı ağırlık, kuyu tepesi, kuyu dibi, halatlar ( iki bakışta ortak )."""
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    taban = Y["taban"]
    #  Raylar ve konsollar
    for r in M["raylar"]:
        ray(e, B, r, S, r["tur"] + "_rayi")
    ag_raylari = [r for r in M["raylar"] if r["tur"] == "agirlik"]
    kabin_raylari = [r for r in M["raylar"] if r["tur"] == "kabin"]
    uzak = max(kabin_raylari, key=lambda r: r["ust"])
    konsollar(e, B, P["konsol_agirlik"], ag_raylari[0]["konsollar"], S, "agirlik_konsolu")
    konsollar(e, B, P["konsol_kabin"], uzak["konsollar"], S, "kabin_konsolu")
    #  Kuyu dibi:  tamponlar ( ikisi de serbest ) ve gergi düzeni
    KD = Y["KD"]
    tamponlar(e, B, KD["kabin_tamponlari"], taban, dy["kabin_tampon_baba"],
                  dy["kabin_tampon_boyu"], kabin_ezilme, S, "kabin")
    tamponlar(e, B, KD["agirlik_tamponlari"], taban, dy["agirlik_tampon_baba"],
                  dy["agirlik_tampon_boyu"], 0.0, S, "agirlik")
    gr = M["gergi"]
    gp = gr["plan"]
    rgx = (gp[0] + gp[2]) / 2.0
    B.kutu(e, "KONSOL", (gp[0], gr["kol"][0], gp[2], gr["kol"][1]), gr["kol"][2], gr["kol"][3],
           "gergi_kolu")
    ge = S["gergi_agirlik_yakin"] - S["gergi_agirlik_uzak"]          # < 0:  ağırlığın eni
    B.kutu(e, "MAKINE", (rgx + ge / 2.0, gr["agirlik"][0], rgx - ge / 2.0, gr["agirlik"][1]),
           gr["agirlik"][2], gr["agirlik"][3], "gergi_agirligi")
    kasnak(e, B, gp, gr["merkez"], gr["cap"], "y", "gergi_kasnagi")
    #  Karşı ağırlık
    AK = CDN.agirlik_kotlari(M, ag_alt)
    blok = M["agirlik"]["kutu"]
    cer = S["agirlik_cerceve"]
    B.kutu(e, "AGIRLIK", blok, AK["alt"], AK["ust"], "agirlik")
    B.kutu(e, "AGIRLIK", (blok[0] + cer, blok[1] + cer, blok[2] - cer, blok[3] - cer),
           AK["alt"] + S["agirlik_kiris"], AK["ust"] - S["agirlik_kiris"], "agirlik_dolgu")
    for r in ag_raylari:
        k = r["kutu"]
        if k[3] <= blok[1]:
            pk = (k[0], blok[1] - S["paten_en"], k[2], blok[1])
        else:
            pk = (k[0], blok[3], k[2], blok[3] + S["paten_en"])
        B.kutu(e, "PATEN", pk, AK["ust"], AK["ust_paten"], "agirlik_paten")
        B.kutu(e, "PATEN", pk, AK["alt_paten"], AK["alt"], "agirlik_paten")
    kasnak(e, B, P["agirlik_kasnak"], AK["kasnak_merkez"], g["agirlik"]["kasnak_capi"], "y",
               "agirlik_kasnagi")
    um = sum(B.aralik(blok)) / 2.0
    if B.gorunur(blok):
        e.append(CGE._ad(CGE._yazi(um, (AK["alt"] + AK["kasnak_merkez"]) / 2.0 - 200,
                                   "KARŞI AĞIRLIK", 40 * K, aci=90), "agirlik_yazi"))
    kt = CDN.kabin_kotlari(dy, S, kabin_z)
    if "sase" not in M:
        return AK, kt
    #  Kuyu tepesinde ya da makine dairesinde:  makine şasesi ( kaidesi ),
    #  bağlantılar, makine, regülatör, ( odada ) kumanda panosu
    sa = M["sase"]
    B.kutu(e, "KONSOL", sa[:4], sa[4], sa[5], "makine_sasesi")
    for ad in ("agirlik_baglanti", "kabin_baglanti"):
        p = M[ad]
        B.kutu(e, "BAGLANTI", p[:4], p[4], p[5], ad)
    gv = M["govde"]
    zt = M["kasnak"][4]
    if B.tur == "on":
        if B.gorunur(gv[:4]):
            u = B.u((gv[0] + gv[2]) / 2.0, 0)
            e.append(CGE._ad(CGE._daire("MAKINE", u, zt, (gv[2] - gv[0]) / 2.0), "makine"))
    else:
        B.kutu(e, "MAKINE", gv[:4], gv[4], gv[5], "makine")
    kp = M["kapak"]
    B.kutu(e, "MAKINE", kp[:4], kp[4], kp[5], "makine_kapagi")
    D1 = g["makine"]["tahrik_kasnak_capi"]
    kasnak(e, B, M["kasnak"][:4], zt, D1, "x", "tahrik_kasnagi")
    rg = M["regulator"]
    B.kutu(e, "MAKINE", rg[:4], rg[4], rg[5], "regulator")
    if "pano" in M:
        p = M["pano"]
        B.kutu(e, "PANO", p[:4], p[4], p[5], "kumanda_panosu")
    rk = M["regulator_kasnak"]
    kasnak(e, B, rk[:4], rk[4], gr["cap"], "y", "regulator_kasnagi")
    #  Halatlar
    KU = M["KU"]
    zk = kt["kasnak_merkez"]
    (xl, y0), (xr, _) = KU["halatlar"]
    yakin, uzak_x = KU["yakin"], KU["uzak"]
    zkb = M["kabin_baglanti"][4]
    zab = M["agirlik_baglanti"][4]
    za = AK["kasnak_merkez"]
    dx, dy_ = KU["ag_dusus"]
    tx1, ty1 = KU["ag_teget"]
    tx2, ty2 = KU["ag_teget2"]
    for (x0_, y0_, z0), (x1_, y1_, z1) in (
            ((yakin, y0, zk), (yakin, y0, zt)),                 # kabin → tahrik kasnağı
            ((uzak_x, y0, zk), (uzak_x, y0, zkb)),              # kabin → kabin bağlantısı
            ((dx, dy_, zt), (tx1, ty1, za)),                    # tahrik kasnağı → ağırlık kasnağı
            ((tx2, ty2, za), (tx2, ty2, zab))):                 # ağırlık kasnağı → bağlantı
        if B.gorunur((x0_, y0_, x0_, y0_)):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(x0_, y0_), z0, B.u(x1_, y1_), z1), "aski_halati"))
    if B.tur == "on":
        #  Kabinin altında iki kasnak arası
        r = g["aski"]["kasnak_capi"] / 2.0
        us = sorted(B.u((k[0] + k[2]) / 2.0, 0) for k in P["kabin_kasnak"])
        e.append(CGE._ad(CGE._cizgi("HALAT", us[0], zk - r, us[-1], zk - r), "aski_halati"))
    #  Regülatör halatı:  tepedeki kasnaktan gergi kasnağına ( iki kol )
    R = gr["cap"] / 2.0
    ry_ = M["regulator_y"]
    for yy in (ry_ - R, ry_ + R):
        if B.gorunur((rgx, yy, rgx, yy)):
            e.append(CGE._ad(CGE._cizgi("HALAT", B.u(rgx, yy), rk[4], B.u(rgx, yy), gr["merkez"]),
                             "regulator_halati"))
    return AK, kt


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
    for z in (kt["sase_alt"], kt["sase_ust"] - 10):
        B.kutu(e, "SASE", (sx0, kb[1], sx1, kb[3]), z, z + 10, "sase_kirisi")
    for p in P["paten"]:
        B.kutu(e, "PATEN", p, kt["sase_ust"], kt["ust_paten"], "ust_paten")
        B.kutu(e, "PATEN", p, kt["alt_paten"], kt["sase_alt"], "alt_paten")
        B.kutu(e, "SASE", p, kt["fren_alti"], kt["fren_alti"] + S["fren_blogu_yukseklik"], "fren")
    for k in P["kabin_kasnak"]:
        kasnak(e, B, k, kt["kasnak_merkez"], g["aski"]["kasnak_capi"], "x", "kabin_kasnagi")
