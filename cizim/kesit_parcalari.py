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

from cizim import izli
from cizim import eleman
from cizim import uslup
from cizim import arka_aski
from cizim import makine
from cizim import kabin_ustu
from cizim import baglantilar
from cizim import parca_kotlari
from cizim import parcalar
import math


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

    def derin(self, el, lo, hi):
        """Elemanın bakış eksenindeki ( yan:  x, ön:  y ) aralığı — kabin_arkasi
        kabinin arkasında kalanı onunla bulur.  Kesit düzlemi yoksa ( kasnak
        düzenlemesi ) işaret konmaz."""
        if self.kesit and el is not None:
            el["_derin"] = (min(lo, hi), max(lo, hi))
        return el

    def derin_kutu(self, el, k):
        eks = 0 if self.tur == "yan" else 1
        return self.derin(el, k[eks], k[eks + 2])

    def derin_nokta(self, el, x, y):
        v = x if self.tur == "yan" else y
        return self.derin(el, v, v)

    def aralik(self, k):
        return (k[1], k[3]) if self.tur == "yan" else (self.G - k[2], self.G - k[0])

    def kutu(self, e, katman, k, z0, z1, ad=None, tip="dikdortgen"):
        if not self.gorunur(k):
            return None
        u0, u1 = self.aralik(k)
        el = eleman.dikdortgen(katman, u0, min(z0, z1), u1 - u0, abs(z1 - z0), tip=tip)
        if ad:
            eleman.ad(el, ad)
        self.derin_kutu(el, k)
        e.append(el)
        return el

    def halat(self, e, x, y, z0, z1, ad="halat"):
        u = self.u(x, y)
        e.append(self.derin_nokta(eleman.ad(eleman.cizgi("HALAT", u, z0, u, z1), ad), x, y))

    def halat_cizgisi(self, e, p0, p1, ad):
        """Uçları plan noktası olan halat parçası ( x, y, z ) → ( x, y, z )."""
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        el = eleman.ad(eleman.cizgi("HALAT", self.u(x0, y0), z0, self.u(x1, y1), z1), ad)
        v0, v1 = (x0, x1) if self.tur == "yan" else (y0, y1)
        e.append(self.derin(el, v0, v1))


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
        e.append(B.derin_kutu(eleman.ad(eleman.daire("KASNAK", u, z, cap / 2.0), ad), kutu))
    else:
        B.kutu(e, "KASNAK", kutu, z - cap / 2.0, z + cap / 2.0, ad)


def kasnak_capraz(e, B, merkez, u, R, z, ad, adim=24):
    """Düşey düzlemi planda u doğrultusunda olan kasnak ( çapraz — arka_aski ):
    bakışa göre elips ( jant çemberinin izdüşümü, çizgi parçalarıyla )."""

    pts = []
    for i in range(adim + 1):
        t = 2.0 * math.pi * i / adim
        x, y = merkez[0] + R * izli.cos(t) * u[0], merkez[1] + R * izli.cos(t) * u[1]
        pts.append((B.u(x, y), z + R * izli.sin(t)))
    for a, b in zip(pts, pts[1:]):
        e.append(B.derin_nokta(eleman.ad(eleman.cizgi("KASNAK", a[0], a[1], b[0], b[1]), ad), *merkez))


def ray(e, B, r, S, ad):
    """Ray gövdesi tabandan üst ucuna, üstünde ek lamaları."""
    B.kutu(e, "RAY", r["kutu"], r["alt"], r["ust"], ad)
    for z in r["ekler"]:
        ek = B.kutu(e, "RAY", r["kutu"], z - S["ek_lama_boyu"] / 2.0, z + S["ek_lama_boyu"] / 2.0, "ray_eki")
        if ek is not None:
            ek["_ray"] = ad  # kabin_arkasi:  eki rayıyla birlikte


def konsollar(e, B, kutular, kotlar, S, ad):
    """Her konsol kotunda konsolun plandaki parçaları ( plaka, kol, ara kiriş )."""
    for z in kotlar:
        for p in kutular:
            B.kutu(e, "KONSOL", p, z - S["konsol_yukseklik"], z, ad)


def tamponlar(e, B, kutular, taban, baba, boy, ezilme, S, ad, tip="poliuretan", strok=0.0):
    """Tampon:  kaide ( kutu — beton mu çelik ayak mı bilinmez ), taban sacı,
    tipine göre gövde ( parcalar.tampon_kesiti ), hidrolikte geri dönüş kontağı.
    Zarflar planın kutularıdır ( taban sacı · gövde dairesi );  ezilme o anki
    sıkışma ( kabin en alt durakta 0 ), strok tamponun stroku ( hidroliğin kolu )."""
    tb, tc = S["tampon_taban"], S["tampon_capi"]
    t = parcalar.TAMPON_SAC
    z0 = taban + baba
    for k in kutular:
        cx, cy = (k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0
        sac = (cx - tb / 2.0, cy - tb / 2.0, cx + tb / 2.0, cy + tb / 2.0)
        B.kutu(e, "TAMPON", sac, taban, z0, ad + "_kaidesi")
        B.kutu(e, "TAMPON", sac, z0, z0 + t, ad + "_tamponu")
        govde = B.kutu(
            e,
            "TAMPON",
            (cx - tc / 2.0, cy - tc / 2.0, cx + tc / 2.0, cy + tc / 2.0),
            z0 + t,
            z0 + max(boy - ezilme, t),
            ad + "_tamponu",
        )
        if govde is None:
            continue
        uc = B.u(cx, cy)
        bicim, zg = parcalar.tampon_kesiti(tip, tc, boy, strok, ezilme)
        govde["bicim"] = [dict(p, noktalar=[(uc + r, z0 + t + z) for r, z in p["noktalar"]]) for p in bicim]
        if tip == "hidrolik":
            kx0, ky0, kx1, ky1 = parcalar.tampon_kontagi(tc, tb)
            zk1 = z0 + t + zg
            B.kutu(
                e,
                "TAMPON",
                (cx + kx0, cy + ky0, cx + kx1, cy + ky1),
                max(z0 + t, zk1 - parcalar.TAMPON_KONTAK[1]),
                zk1,
                ad + "_tamponu",
            )


def kot_isareti(e, u, z, metin, K, yon=1.0):
    """▽ kot işareti:  ucu döşemede, yazı yanında  ( referans proje / LiftDesigner )."""
    w, h = 40 * K, 55 * K
    for a, b in (((u - w, z + h), (u + w, z + h)), ((u - w, z + h), (u, z)), ((u, z), (u + w, z + h))):
        e.append(eleman.cizgi("KUYU-IC", a[0], a[1], b[0], b[1]))
    e.append(
        eleman.ad(
            eleman.yazi(
                u + yon * (w + 20 * K),
                z + h + 25 * K,
                metin,
                uslup.NORMAL * K,
                hiza="sol" if yon > 0 else "sag",
            ),
            "kot",
        )
    )


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
        "kasa": ad("kapi_kasasi"),
        "esik": ad("kat_esigi"),
        "kanat": ad("kat_kanadi"),
        "bosluk": ad("kapi_boslugu"),
        "kabin_esik": ad("kabin_esigi"),
        "kabin_kanat": ad("kabin_kanadi"),
        "konsol_agirlik": [k for k in konsol if agirlik_tarafi(k)],
        "konsol_kabin": [k for k in konsol if not agirlik_tarafi(k)],
        "paten": [kutu_(el) for el in taban if el["katman"] == "PATEN" and el.get("ad") != "agirlik_pateni"],
        "sase_dikme": [kutu_(el) for el in taban if el.get("ad") == "sase_dikme"],
        "kabin_kasnak": [kutu_(el) for el in taban if el.get("ad") == "kabin_kasnak"],
        #  1:1 askıda karşı ağırlıkta kasnak yok:  halat çerçevenin ortasına bağlanır
        "agirlik_kasnak": next((kutu_(el) for el in taban if el.get("ad") == "agirlik_kasnak"), None),
    }


def donanimi_ciz(e, B, g, Y, P, kabin_z, ag_alt, K=1.0, kabin_ezilme=0.0):
    """Raylar, karşı ağırlık, kuyu tepesi, kuyu dibi, halatlar ( iki bakışta ortak )."""
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    #  Raylar, konsollar ve karşı ağırlık BAKANA UZAKLIKLARINA GÖRE çizilir
    #  ( uzaktaki önce ):  A-A'da ağırlık tarafındaki kabin rayı ve ara kiriş
    #  karşı ağırlığın önündedir;  önce hepsi, sonra ağırlık çizildiğinde ray
    #  ağırlık boyunca kayboluyordu.  gruplar:  ( plandaki kutu, elemanlar )
    AK = parca_kotlari.agirlik_kotlari(M, ag_alt)
    gruplar = _ray_ve_dip_gruplari(B, g, Y, P, kabin_ezilme) + _agirlik_gruplari(B, g, S, M, P, AK, K)
    for _, el in sorted(gruplar, key=lambda ge: uzaklik(B, ge[0]), reverse=True):
        e += el
    kt = parca_kotlari.kabin_kotlari(dy, S, kabin_z, g.get("aski"), arka_aski.arkada_iki_bir(g))
    e += makine.gorunus(
        baglantilar.kasnak_tasiyicilari(g, S, kt["kasnak_merkez"]),
        B,
        eleman.dikdortgen,
        eleman.daire,
        eleman.cizgi,
    )
    capraz = (M.get("KU") or {}).get("capraz")
    if capraz:
        #  Arkadaki ağırlıkla 2:1:  kabin üstündeki çapraz kasnaklar ( elips )
        for m, kutu in zip(capraz["kasnaklar"], capraz["kutular"]):
            if B.gorunur(kutu):
                kasnak_capraz(e, B, m, capraz["u"], capraz["Rk"], kt["kasnak_merkez"], "kabin_kasnagi")
    if "sase" not in M:
        return AK, kt
    _kuyu_tepesi(e, B, g, M, K)
    #  Halatlar
    gr, rk = M["gergi"], M["regulator_kasnak"]
    rgx = (gr["plan"][0] + gr["plan"][2]) / 2.0
    KU = M["KU"]
    zt = M["kasnak"][4]
    if KU.get("dogrudan"):
        _halatlar_1_1(e, B, g, M, KU, kt, AK, zt)
    elif KU.get("capraz"):
        _halatlar_capraz(e, B, M, KU, kt, AK, zt)
    else:
        _halatlar_yan(e, B, g, M, P, KU, kt, AK, zt)
    _regulator_halati(e, B, M, gr, rk, rgx)
    return AK, kt


def _ray_ve_dip_gruplari(B, g, Y, P, kabin_ezilme):
    """Raylar, konsollar, tamponlar ( ikisi de serbest ) ve gergi düzeni:
    [ ( plandaki kutu, elemanlar ) ]."""
    S, M, dy, taban = Y["S"], Y["M"], g["dusey"], Y["taban"]
    gruplar = []
    for r in M["raylar"]:
        el = []
        ray(el, B, r, S, r["tur"] + "_rayi")
        gruplar.append((r["kutu"], el))
    ag_raylari = [r for r in M["raylar"] if r["tur"] == "agirlik"]
    kabin_raylari = [r for r in M["raylar"] if r["tur"] == "kabin"]
    uzak = max(kabin_raylari, key=lambda r: r["ust"])
    for konsol_kutulari, kotlar, ad in (
        (P["konsol_agirlik"], ag_raylari[0]["konsollar"], "agirlik_konsolu"),
        (P["konsol_kabin"], uzak["konsollar"], "kabin_konsolu"),
    ):
        for p in konsol_kutulari:
            el = []
            konsollar(el, B, [p], kotlar, S, ad)
            gruplar.append((p, el))
    KD = Y["KD"]
    tip = parcalar.tampon_tipi((g.get("veri") or {}).get("tampon"))
    for kutular, baba, boy, ezilme, ad in (
        (KD["kabin_tamponlari"], dy["kabin_tampon_baba"], dy["kabin_tampon_boyu"], kabin_ezilme, "kabin"),
        (KD["agirlik_tamponlari"], dy["agirlik_tampon_baba"], dy["agirlik_tampon_boyu"], 0.0, "agirlik"),
    ):
        strok = dy.get(f"{ad}_tampon_ezilme") or 0.0
        for k in kutular:
            el = []
            tamponlar(el, B, [k], taban, baba, boy, ezilme, S, ad, tip, strok)
            gruplar.append((k, el))
    return gruplar + _gergi_gruplari(B, Y)


#  Kesitte gerginin parçaları:  ad · katman · zarfın plan adı ( kuyu dibi )
_GERGI_PARCALARI = (
    ("plaka", "KONSOL", "gergi_plakasi"),
    ("kontak", "MAKINE", "gergi_kontagi"),
    ("kol", "KONSOL", "gergi_kolu"),
    ("agirlik", "MAKINE", "gergi_agirligi"),
)


def _gergi_gruplari(B, Y):
    """Regülatör gergisi ( R4K tipi kollu — parcalar.gergi_geometrisi ):  [ ( plan
    kutusu, elemanlar ) ].  Kasnağın düzlemi bakışa dikse ( yan ) gerçek biçimi:
    olukları ile raya bağlantı plakası, güvenlik kontağı, eğik kol, mafsal ve
    pim, oluk dibiyle kasnak, koruma kapağı, askılı ağırlık.  Öbür bakışta
    ( ön ) parçalar yandan, kalınlıklarıyla ( zarflar ).  Zarflar kuyu dibinin
    zarflarıdır:  denetim ile çizim aynı kutuyu kullanır."""
    gr, gd = Y["M"]["gergi"], Y["KD"]["gergi_donanim"]
    gp, zc, geo, yon = gr["plan"], gr["merkez"], gr["geo"], gr["yon"]
    gx, gy = (gp[0] + gp[2]) / 2.0, (gp[1] + gp[3]) / 2.0
    duz = B.tur == "yan"

    def nok(p):  # kasnağa göre ( s, z ) → bakışın ( u, z )
        return (B.u(gx, gy + yon * p[0]), zc + p[1])

    gruplar = []
    for ad, katman, adi in _GERGI_PARCALARI:
        el = []
        k = B.kutu(el, katman, gd[ad], gr[ad][2], gr[ad][3], adi)
        if k is not None and duz:
            cokgen = _dortgen(geo[ad]) if ad == "kontak" else geo[ad]
            k["bicim"] = [{"noktalar": [nok(p) for p in cokgen]}] + (
                [{"noktalar": [nok(p) for p in o], "ince": True} for o in geo["oluklar"]]
                if ad == "plaka"
                else []
            )
            #  Mafsal ( plakada ) ve pim ( ağırlığın askısı ) — kolun üstünde
            if ad == "kol":
                for p, r in (
                    (geo["mafsal"], parcalar.GERGI_GOBEK[0]),
                    (geo["pim"], parcalar.GERGI_GOBEK[0] / 2.0),
                ):
                    u, z = nok(p)
                    el.append(B.derin_kutu(eleman.ad(eleman.daire("KONSOL", u, z, r), adi), gd[ad]))
        gruplar.append((gd[ad], el))
    el = []
    kasnak(el, B, gp, zc, gr["cap"], "y", "gergi_kasnagi")
    if duz and B.gorunur(gp):
        u, _z = nok((0.0, 0.0))
        for r, katman in ((gr["cap"] / 2.0 - 10.0, "KASNAK"), (parcalar.GERGI_GOBEK[1], "KASNAK")):
            el.append(B.derin_kutu(eleman.ad(eleman.daire(katman, u, zc, r), "gergi_kasnagi"), gp))
        pts = [nok(p) for p in geo["kapak"]]
        us, zs = [p[0] for p in pts], [p[1] for p in pts]
        k = eleman.ad(
            eleman.dikdortgen("KASNAK", min(us), min(zs), max(us) - min(us), max(zs) - min(zs)),
            "gergi_kapagi",
        )
        k["bicim"] = [{"noktalar": pts, "kapali": False}]
        el.append(B.derin_kutu(k, gp))
    gruplar.append((gp, el))
    return gruplar


def _dortgen(k):
    s0, s1, z0, z1 = k
    return [(s0, z0), (s1, z0), (s1, z1), (s0, z1)]


def _agirlik_gruplari(B, g, S, M, P, AK, K):
    """Karşı ağırlık:  çerçeve, dolgu, kasnak ve yazı bir grup;  patenler ayrı."""
    ag_raylari = [r for r in M["raylar"] if r["tur"] == "agirlik"]
    blok = M["agirlik"]["kutu"]
    cer = S["agirlik_cerceve"]
    el = []
    B.kutu(el, "AGIRLIK", blok, AK["alt"], AK["ust"], "agirlik")
    dolgu_alt, dolgu_ust = parca_kotlari.agirlik_dolgu_kotlari(g, S, AK)
    B.kutu(
        el,
        "AGIRLIK",
        (blok[0] + cer, blok[1] + cer, blok[2] - cer, blok[3] - cer),
        dolgu_alt,
        dolgu_ust,
        "agirlik_dolgu",
    )
    if P["agirlik_kasnak"]:
        kasnak(
            el,
            B,
            P["agirlik_kasnak"],
            AK["kasnak_merkez"],
            g["agirlik"]["kasnak_capi"],
            "x" if g["agirlik"]["yeri"] == "Arka" else "y",
            "agirlik_kasnagi",
        )
    um = sum(B.aralik(blok)) / 2.0
    #  Ağırlık rayı bakışta ortadan geçiyorsa ( B-B'de yandaki, A-A'da arkadaki
    #  ağırlık ) yazı rayın yanındaki geniş boşluğa:  eskiden rayın altında
    #  kalıyordu.
    b0, b1 = B.aralik(blok)
    for r in ag_raylari:
        r0, r1 = B.aralik(r["kutu"])
        if r0 - 1e-6 <= um <= r1 + 1e-6:
            um = (b0 + r0) / 2.0 if r0 - b0 >= b1 - r1 else (r1 + b1) / 2.0
            break
    if B.gorunur(blok):
        el.append(
            eleman.ad(
                eleman.yazi(
                    um,
                    (AK["alt"] + AK["kasnak_merkez"]) / 2.0 - 200,
                    "KARŞI AĞIRLIK",
                    uslup.NORMAL * K,
                    aci=90,
                ),
                "agirlik_yazi",
            )
        )
    gruplar = [(blok, el)]
    for z0, z1 in ((AK["ust_paten_alt"], AK["ust_paten"]), (AK["alt_paten"], AK["alt_paten_ust"])):
        for parca in baglantilar.agirlik_patenleri(g, S, blok, ag_raylari, z0, z1):
            el = makine.gorunus([parca], B, eleman.dikdortgen, eleman.daire, eleman.cizgi)
            gruplar.append((makine.sinirlar(parca)[:4], el))
    return gruplar


def _kuyu_tepesi(e, B, g, M, K):
    """Kuyu tepesinde ya da makine dairesinde:  makine şasesi, bağlantılar,
    makine ( makine.py:  parça parça, izdüşümüyle ), regülatör, ( odada )
    kumanda panosu."""
    for ad in ("agirlik_baglanti", "kabin_baglanti"):  # 1:1 askıda yok
        p = M[ad]
        if p:
            B.kutu(e, "BAGLANTI", p[:4], p[4], p[5], ad)
    e += makine.gorunus(M["sase_parcalari"] + M["makine"], B, eleman.dikdortgen, eleman.daire, eleman.cizgi)
    #  Makine dairesinde halatın tahrik kasnağındaki sarım açısı ( LiftDesigner
    #  "kasnak düzenlemesi" gibi ) — kasnağın daire göründüğü ön kesitte
    #  Kasnak, ekseni bakış yönündeyse daire görünür:  yan ağırlıkta B-B'de,
    #  arkadaki ağırlıkta ( halat düzlemi derinlik boyunca ) A-A'da
    duz_ = (M.get("KU") or {}).get("duzlem")
    daire_bakis = "yan" if duz_ is not None and duz_.yon == "y" else "on"
    if "MD" in M and B.tur == daire_bakis and B.gorunur(M["kasnak"][:4]):
        ks = M["kasnak"]
        e.append(
            eleman.ad(
                eleman.yazi(
                    B.u((ks[0] + ks[2]) / 2.0, 0),
                    ks[4] + g["makine"]["tahrik_kasnak_capi"] / 2.0 + 180 * K,
                    f"SARIM AÇISI {M['sarim_acisi']:.0f}°",
                    uslup.NORMAL * K,
                ),
                "sarim_acisi",
            )
        )
    if M["mrl"]:
        e += makine.gorunus(M["halat_konsolu"], B, eleman.dikdortgen, eleman.daire, eleman.cizgi)
    if M.get("pano"):
        p = M["pano"]
        B.kutu(e, "PANO", p[:4], p[4], p[5], "kumanda_panosu")
    regulator(e, B, M)


def regulator(e, B, M):
    """Hız regülatörü ( parcalar.regulator_geometrisi ).  Kasnağın düzlemi kuyunun
    derinliği boyuncadır:  B-B ( ön ) onu yandan görür — iki ayak, bacaklar ve
    üstteki büküm, aralarında iki oluklu kasnak, mekanizma ve kontak;  A-A ( yan )
    önden — bacak, kasnağın bacaktan taşan yayları ( halat ve deneme oluğu ),
    ayaklar, mil, kontak.  Zarflar plandaki kutular ( reg_govde · reg_kasnak )."""
    rc = M["KU"]["reg_cizim"]
    geo, rg, zc = rc["geo"], M["regulator"], M["regulator_kasnak"][4]
    zb, zt = zc - geo["eksen"], zc + geo["tepe"]
    t = parcalar.REGULATOR_SAC
    el = B.kutu(e, "MAKINE", rg[:4], rg[4], rg[5], "regulator")
    if el is None:
        return
    R = geo["R"]
    (b0, b0i), (b1i, b1) = geo["bacaklar"]
    ku0, ku1, kv0, kv1, kz0, kz1 = geo["kontak"]
    if B.tur == "on":

        def u(v):  # v ( düzleme dik ) → bakışın u'su
            return B.u(rc["x"] - rc["yan"] * v, rc["y"])

        def dortgen(v0, v1, z0, z1):
            return [(u(v0), z0), (u(v1), z0), (u(v1), z1), (u(v0), z1)]

        el["bicim"] = [{"noktalar": dortgen(a[2], a[3], zb, zb + t)} for a in geo["ayaklar"]] + [
            #  U:  iki bacak ve üstteki büküm
            {
                "noktalar": [
                    (u(b0), zb + t),
                    (u(b0), zt),
                    (u(b1), zt),
                    (u(b1), zb + t),
                    (u(b1i), zb + t),
                    (u(b1i), zt - t),
                    (u(b0i), zt - t),
                    (u(b0i), zb + t),
                ]
            },
            {"noktalar": dortgen(kv0, kv1, zc + kz0, zc + kz1)},
        ]
        _, _, sv0, sv1 = geo["kasnak"]
        k = eleman.ad(
            eleman.dikdortgen("KASNAK", min(u(sv0), u(sv1)), zc - R, abs(u(sv1) - u(sv0)), 2 * R),
            "regulator_kasnagi",
        )
        #  İki oluğun dibi ( halat oluğu ve deneme oluğu ) ince
        k["bicim"] = [{"noktalar": dortgen(sv0, sv1, zc - R, zc + R)}] + [
            {"noktalar": [(u(v), zc - r), (u(v), zc + r)], "kapali": False, "ince": True}
            for v, r in ((0.0, R - parcalar.REGULATOR_OLUK_DERIN), (sv0 + (sv1 - sv0) / 4.0, geo["deneme"]))
        ]
        e.append(B.derin_kutu(k, M["regulator_kasnak"][:4]))
        return
    #  Önden ( A-A ):  bacak kasnağın ortasını örter — yaylar bacağın iki yanında
    uc = B.u(rc["x"], rc["y"])
    w0, w1 = geo["bacak"]
    au0, au1 = geo["ayaklar"][0][:2]
    el["bicim"] = [
        {"noktalar": [(uc + au0, zb), (uc + au1, zb), (uc + au1, zb + t), (uc + au0, zb + t)]},
        {"noktalar": [(uc + w0, zb + t), (uc + w1, zb + t), (uc + w1, zt), (uc + w0, zt)]},
        {
            "noktalar": [
                (uc + ku0, zc + kz0),
                (uc + ku1, zc + kz0),
                (uc + ku1, zc + kz1),
                (uc + ku0, zc + kz1),
            ]
        },
    ]
    k = eleman.ad(eleman.dikdortgen("KASNAK", uc - R, zc - R, 2 * R, 2 * R), "regulator_kasnagi")
    k["bicim"] = []
    for r, ince in ((R, False), (geo["deneme"], True)):
        if r > w1:
            a = math.degrees(math.acos(w1 / r))
            for a0, a1 in ((-a, a), (180.0 - a, 180.0 + a)):
                k["bicim"].append(
                    {"noktalar": parcalar.yay((uc, zc), r, a0, a1, 12), "kapali": False, "ince": ince}
                )
    e.append(B.derin_kutu(k, M["regulator_kasnak"][:4]))
    e.append(B.derin_kutu(eleman.ad(eleman.daire("KONSOL", uc, zc, 10.0), "regulator"), rg[:4]))


def _halatlar_yan(e, B, g, M, P, KU, kt, AK, zt):
    """Yandaki ağırlıkla 2:1:  askı halatları."""
    zk = kt["kasnak_merkez"]
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
        agirlik = [((dx, dy_, zt), (tx1, ty1, za))]  # tahrik kasnağı → ağırlık kasnağı
    for (x0_, y0_, z0), (x1_, y1_, z1) in (
        [
            ((yakin, y0, zk), (yakin, y0, zt)),  # kabin → tahrik kasnağı
            ((uzak_x, y0, zk), (uzak_x, y0, zkb)),  # kabin → kabin bağlantısı
        ]
        + agirlik
        + [((tx2, ty2, za), (tx2, ty2, zab))]  # ağırlık kasnağı → bağlantı
    ):
        if B.gorunur((x0_, y0_, x0_, y0_)):
            B.halat_cizgisi(e, (x0_, y0_, z0), (x1_, y1_, z1), "aski_halati")
    if B.tur == "on":
        #  Kabinin altında iki kasnak arası
        r = g["aski"]["kasnak_capi"] / 2.0
        us = sorted(B.u((k[0] + k[2]) / 2.0, 0) for k in P["kabin_kasnak"])
        e.append(eleman.ad(eleman.cizgi("HALAT", us[0], zk - r, us[-1], zk - r), "aski_halati"))


def _regulator_halati(e, B, M, gr, rk, rgx):
    """Regülatör halatı:  tepedeki kasnaktan gergi kasnağına ( iki kol )."""
    R = gr["cap"] / 2.0
    ry_ = M["regulator_y"]
    for yy in (ry_ - R, ry_ + R):
        if B.gorunur((rgx, yy, rgx, yy)):
            B.halat_cizgisi(e, (rgx, yy, rk[4]), (rgx, yy, gr["merkez"]), "regulator_halati")


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
    for (x0_, y0_, z0), (x1_, y1_, z1) in (
        [((px, py, zk), (px, py, zt)), ((hx, hy, zk), (hx, hy, zkb))]
        + agirlik
        + [((bx, by, za), (bx, by, zab)), ((ax_, ay2, zk - Rk), (ox_, oy_, zk - Rk))]
    ):
        if gorunur(x0_, y0_) or gorunur(x1_, y1_):
            B.halat_cizgisi(e, (x0_, y0_, z0), (x1_, y1_, z1), "aski_halati")


def _halatlar_1_1(e, B, g, M, KU, kt, AK, zt):
    """1:1 askıda halatlar:  kabin şasesinin üst kirişinin ortasındaki
    bağlantıdan tahrik kasnağına;  kasnağın öbür teğetinden ( saptırma varsa
    ondan ) karşı ağırlığın ortasındaki bağlantıya.  Kabin bağlantısı üst
    kirişin üstünde, halat soketlerinin boyunda ( parca_kotlari.kabin_kotlari )."""
    hx, hy = KU["kabin_nokta"]
    ax, ay = KU["ag_nokta"]
    a = g["aski"]
    #  Kabin bağlantısı:  halat demetinin izi, üst kirişten soketlerin tepesine
    dk = makine.halat_deligi(hx, hy, a["halat_adedi"], a["halat_capi"], 0.0, KU["duzlem"].eksen)
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
            B.halat_cizgisi(e, (x0_, y0_, z0), (x1_, y1_, z1), "aski_halati")


def kabin_on(e, B, g, Y, P, kt):
    """Kabin ön görünüşte ( arkasından ):  gövde, iç, şase, patenler, fren blokları, kasnaklar."""
    S, KD = Y["S"], Y["KD"]
    kb = KD["kabin"]
    B.kutu(e, "KABIN", kb, kt["taban_alti"], kt["tavan"], "kabin")
    py = S["kabin_pano_yan"]
    B.kutu(e, "KABIN-IC", (kb[0] + py, kb[1], kb[2] - py, kb[3]), kt["doseme"], kt["ic_ust"])
    kp = g["kapi"]
    #  Kabin kapısı kabinin önündedir — arkadan bakışta görünmez ( kesik )
    B.kutu(
        e,
        "GIZLI",
        (kp["sol_pay"], kb[1], kp["sol_pay"] + kp["genislik"], kb[1] + 1),
        kt["doseme"],
        kt["doseme"] + kp["yukseklik"],
        "kabin_kapisi",
    )
    #  Dikmeler alt kirişin altından üst kirişin üstüne;  kirişler gerçek
    #  yükseklikleriyle iki dikmenin sırtı arasında ( plandaki gibi ), patenler
    #  kirişlerin dışında ( kabin_kotlari — LiftDesigner ve referans proje )
    for k in P["sase_dikme"]:
        B.kutu(e, "SASE", k, kt["alt_kiris_alt"], kt["ust_kiris_ust"], "sase")
    dikmeler = sorted(P["sase_dikme"], key=lambda k: k[0] + k[2])
    sx0, sx1 = dikmeler[0][2], dikmeler[-1][0]  # sol dikmenin sırtı · sağınınki
    sy0 = min(k[1] for k in P["sase_dikme"])
    sy1 = max(k[3] for k in P["sase_dikme"])
    for z0, z1 in ((kt["alt_kiris_alt"], kt["alt_kiris_ust"]), (kt["ust_kiris_alt"], kt["ust_kiris_ust"])):
        B.kutu(e, "SASE", (sx0, sy0, sx1, sy1), z0, z1, "sase_kirisi")
    for p in P["paten"]:
        B.kutu(e, "PATEN", p, kt["ust_paten_alt"], kt["ust_paten"], "ust_paten")
        B.kutu(e, "PATEN", p, kt["alt_paten"], kt["alt_paten_ust"], "alt_paten")
        B.kutu(e, "SASE", p, kt["fren_alti"], kt["fren_alti"] + S["fren_blogu_yukseklik"], "fren")
    for k in P["kabin_kasnak"]:
        kasnak(e, B, k, kt["kasnak_merkez"], g["aski"]["kasnak_capi"], "x", "kabin_kasnagi")


def korkuluk(e, B, Y, kt):
    """Küpeşte ve uç dikmeleri, planla aynı konum ve kenara özgü yükseklikte."""
    for kutu, yukseklik in kabin_ustu.korkuluklar(Y["KU"]):
        if not B.gorunur(kutu):
            continue
        u0, u1 = B.aralik(kutu)
        z0, z1 = kt["tavan"], kt["tavan"] + yukseklik
        for a, b in (((u0, z0), (u0, z1)), ((u0, z1), (u1, z1)), ((u1, z1), (u1, z0))):
            if a != b:
                e.append(eleman.ad(eleman.cizgi("KORKULUK", *a, *b), "korkuluk"))


def _kutu_farki(el, S):
    """Dikdörtgen eleman eksi S ( u0, z0, u1, z1 ):  dışarıda kalan parçalar."""
    x0, y0, x1, y1 = el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"]
    if not (x0 < S[2] and S[0] < x1 and y0 < S[3] and S[1] < y1):
        return [el]
    kalanlar = [
        (x0, y0, x1, S[1]),
        (x0, S[3], x1, y1),  # alt · üst
        (x0, max(y0, S[1]), S[0], min(y1, S[3])),
        (S[2], max(y0, S[1]), x1, min(y1, S[3])),
    ]
    cikti = []
    for a, b, c, d in kalanlar:
        if c - a > 1e-6 and d - b > 1e-6:
            yeni = dict(el, x=a, y=b, g=c - a, d=d - b)
            cikti.append(yeni)
    return cikti


def _cizgi_farki(el, S):
    """Çizgi eksi S:  S'nin dışında kalan ( en çok iki ) parça ( Liang–Barsky )."""
    x1, y1, x2, y2 = el["x1"], el["y1"], el["x2"], el["y2"]
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - S[0]), (dx, S[2] - x1), (-dy, y1 - S[1]), (dy, S[3] - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                return [el]
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return [el]
    cikti = []
    for a, b in ((0.0, t0), (t1, 1.0)):
        if b - a > 1e-9 and (b - a) * (abs(dx) + abs(dy)) > 1e-6:
            cikti.append(dict(el, x1=x1 + a * dx, y1=y1 + a * dy, x2=x1 + b * dx, y2=y1 + b * dy))
    return cikti


def kabin_arkasi(e, B, kabin, z0, z1, onde=()):
    """Düşey kesitte kabin OPAKTIR:  bakış ekseninde kabinin uzak yüzünün
    ötesinde kalan parçalar ( işareti _derin ) kabinin görünüşünün ( u: kabinin
    izi, z: taban altı – tavan ) içinde çizilmez.  onde:  kabinin üstünden
    görünen parçaların adları ( A-A'da kabin rayı — referans projenin ve
    LiftDesigner'ın yan kesitlerinde ray ve şase kabinin üstündedir ):  kabinin
    hizasındaki parçaları çizim sırasında kabin gövdesinin hemen arkasına
    alınır ( tamponun, patenlerin üstüne binmesinler ).  Eskiden kabinin yalnız SVG'deki beyaz
    dolgusu örtüyordu:  DXF'te ( DWG, pafta ) raylar, konsollar, halatlar ve
    B-B'de en üst kat kapısı kabinin içinden geçiyordu ( 4 Eki ).  İşaret
    elemanlardan kaldırılır."""
    eks = 0 if B.tur == "yan" else 1
    yon = B.kesit[2]
    uzak = kabin[eks] if yon < 0 else kabin[eks + 2]
    u0, u1 = B.aralik(kabin)
    S = (u0, z0, u1, z1)
    kalan, ustte = [], []
    for el in e:
        d = el.pop("_derin", None)
        ray = el.pop("_ray", None)
        arkada = d is not None and (d[1] <= uzak + 1e-6 if yon < 0 else d[0] >= uzak - 1e-6)
        if not arkada:
            kalan.append(el)
        elif (el.get("ad") in onde or ray in onde) and el["tip"] == "dikdortgen":
            kalan += _kutu_farki(el, S)
            x0, y0 = max(el["x"], S[0]), max(el["y"], S[1])
            x1, y1 = min(el["x"] + el["g"], S[2]), min(el["y"] + el["d"], S[3])
            if x1 - x0 > 1e-6 and y1 - y0 > 1e-6:
                ustte.append(dict(el, x=x0, y=y0, g=x1 - x0, d=y1 - y0))
        elif el["tip"] in ("dikdortgen", "tarama"):
            kalan += _kutu_farki(el, S)
        elif el["tip"] in ("cizgi", "eksen"):
            kalan += _cizgi_farki(el, S)
        elif el["tip"] == "daire":
            r = el["r"]
            if not (
                S[0] <= el["x"] - r and el["x"] + r <= S[2] and S[1] <= el["y"] - r and el["y"] + r <= S[3]
            ):
                kalan.append(el)
        elif el["tip"] == "yazi":
            if not (S[0] < el["x"] < S[2] and S[1] < el["y"] < S[3]):
                kalan.append(el)
        else:
            kalan.append(el)
    #  Kabin gövdesinin ( ve iç yüzünün ) hemen arkası
    i = next((n for n, el in enumerate(kalan) if el.get("ad") == "kabin"), len(kalan) - 1)
    i += 2 if i + 1 < len(kalan) and kalan[i + 1]["katman"] == "KABIN-IC" else 1
    e[:] = kalan[:i] + ustte + kalan[i:]
