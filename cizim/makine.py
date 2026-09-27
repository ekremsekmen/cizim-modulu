# -*- coding: utf-8 -*-
"""
TAHRİK MAKİNESİ VE ŞASESİ  ( plan, yan ve ön görünüşte ortak )

Makine ve şase üç boyutlu basit cisimlerden kurulur;  plan ve düşey kesitler
aynı cisimlerin izdüşümünü çizer ( makine bir kez tanımlanır ):

  ( "silindir", eksen, merkez ( x, y, z ), çap, ( t0, t1 ) )   eksen x / y / z;
        t0 – t1 eksen boyunca;  ekseni bakış yönündeyse DAİRE, değilse dikdörtgen
  ( "kutu", ( x0, y0, x1, y1, z0, z1 ) )
  ( "cizgi", ( x0, y0, z0 ), ( x1, y1, z1 ) )                 profil kenarları

Her cismin katmanı ve adı vardır ( ad:  makine · tahrik_kasnagi ·
makine_sasesi;  parca:  alt parçanın adı ).

MAKİNE TİPLERİ  ( kullanıcı kararı:  ölçüler LiftDesigner makinelerinden )
  Dişlisiz   LiftDesigner'ın dişlisiz makinesi ( ofisin 4815-6 projesi ):
             kasnak, göbek, flanş, yatak flanşı, gövde, fren, fren diski,
             enkoder — hepsi kasnak ekseni üstünde.  Biçim LiftDesigner'ın;
             ölçüler projenin makine ZARFINA oranlanır ( gövde çapı
             makine_en, kasnak arkası boy makine_kasnak_boslugu + makine_boy ):
             ELEport'un gerçek makinesi LiftDesigner'ınkinden küçüktür ve
             kotları ölçülmüştür.  Kasnak kendi çapı ve eniyle çizilir.
  Dişli      LiftDesigner'ın A 160 sonsuz vidalı makinesi ( 12744-3 ):  motor
             ekseni kasnak eksenine DİK;  el çarkı, motor, fren, dişli kutusu,
             arka yatak, taban;  kasnak dişli kutusunun yanında, dış yatakla.
             Ölçüler aynen ( zarfı 1.316 × 590 × 600 ).

ŞASE
  Kuyu üstü  2 × UPN 200 ( DIN 1026:  h 200 · b 75 · gövde 8,5 · flanş 11,5 ) —
             ELEport'un şase hesabındaki kiriş ( Wx 191 cm³ );  kirişler
             karşı ağırlık rayları boyunca, aralarında üstle aynı hizada motor
             plakası ( ELEport:  700 mm ) ve uçlarda bağlantı levhaları.
"""

TIPLER = ("Dişlisiz", "Dişli")

#  Dişlisiz — kasnağın arka yüzünden eksen boyunca ( ad, boy, çap ):
#  LiftDesigner 4815-6 yan görünüşünden ölçüldü ( kasnak ø240 × 92 ).
DISLISIZ = (("gobek", 15, 100), ("flans", 28, 220), ("yatak", 50, 320), ("govde", 206, 400),
            ("fren", 70, 320), ("fren_diski", 18, 240), ("enkoder", 102, 270))
DISLISIZ_CAP = 400.0
DISLISIZ_BOY = float(sum(b for _, b, _ in DISLISIZ))          # 489

#  Dişli ( LiftDesigner A 160, 12744-3 ) — kasnak merkezine göre:  m motor ekseni
#  boyunca ( motora doğru eksi ), a kasnak ekseni boyunca ( dişli kutusuna doğru
#  artı ), z yukarı.  Silindirler m ekseninde:  ( ad, m0, m1, çap, a, z ).
DISLI_SILINDIR = (("el_carki", -1000, -930, 280, 230, 160), ("mil", -930, -880, 115, 230, 158),
                  ("kaplin", -880, -855, 145, 230, 142), ("motor_kapagi", -855, -750, 310, 230, 160),
                  ("motor", -750, -515, 300, 230, 158), ("fren_gobegi", -410, -320, 140, 230, 160),
                  ("fren_kasnagi", -320, -300, 260, 230, 160))
#  Kutular:  ( ad, m0, m1, a0, a1, z0, z1 )
DISLI_KUTU = (("klemens_kutusu", -715, -575, 158, 302, 305, 380),
              ("motor_flansi", -515, -410, 75, 385, 5, 405),
              ("fren", -285, -220, 45, 415, 15, 385),
              ("disli_kutusu", -160, 160, 100, 360, -160, 262),
              ("vida_yuvasi", -170, 0, 160, 300, 262, 410),
              ("arka_yatak", 160, 290, 160, 310, 85, 235),
              ("taban", -700, 180, 60, 400, -195, -160),
              ("dis_yatak_ayagi", -100, 100, -160, -75, -195, -150))
#  Kasnak ekseninde:  dış yatak ve kasnak mili  ( ad, a0, a1, çap )
DISLI_EKSEN = (("dis_yatak", -160, -75, 300), ("kasnak_mili", -175, 100, 55))
DISLI_ZARF = {"m": (-1000.0, 320.0), "a": (-175.0, 415.0), "z": (-195.0, 410.0)}

#  UPN 200  ( DIN 1026-1 )
UPN = {"h": 200.0, "b": 75.0, "s": 8.5, "t": 11.5}
MOTOR_PLAKASI_BOY = 700.0          # ELEport şase hesabı:  "motor bedplate length m"
MOTOR_PLAKASI_KALINLIK = 15.0
UC_LEVHASI = 10.0


def _parca(tur, katman, ad, parca, **v):
    return dict(tur=tur, katman=katman, ad=ad, parca=parca, **v)


def silindir(eksen, merkez, cap, t0, t1, katman="MAKINE", ad="makine", parca=""):
    return _parca("silindir", katman, ad, parca, eksen=eksen, merkez=tuple(merkez), cap=float(cap),
                  t=(min(t0, t1), max(t0, t1)))


def kutu(x0, y0, x1, y1, z0, z1, katman="MAKINE", ad="makine", parca=""):
    return _parca("kutu", katman, ad, parca,
                  k=(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), min(z0, z1), max(z0, z1)))


def cizgi(p0, p1, katman="KONSOL", ad="makine_sasesi", parca=""):
    return _parca("cizgi", katman, ad, parca, p0=tuple(p0), p1=tuple(p1))


def sinirlar(p):
    """Cismin ( x0, y0, x1, y1, z0, z1 ) kutusu."""
    if p["tur"] == "kutu":
        return p["k"]
    if p["tur"] == "cizgi":
        (a, b, c), (d, e, f) = p["p0"], p["p1"]
        return (min(a, d), min(b, e), max(a, d), max(b, e), min(c, f), max(c, f))
    x, y, z = p["merkez"]
    r = p["cap"] / 2.0
    t0, t1 = p["t"]
    return {"x": (t0, y - r, t1, y + r, z - r, z + r),
            "y": (x - r, t0, x + r, t1, z - r, z + r),
            "z": (x - r, y - r, x + r, y + r, t0, t1)}[p["eksen"]]


# ── MAKİNE ───────────────────────────────────────────────────────────────
def dislisiz(kasnak, D1, bk, s, zarf_cap, zarf_boy):
    """kasnak:  ( x, y, z ) kasnak merkezi;  kasnak ekseni y;  s:  gövdenin
    kasnağa göre yönü ( +1 / −1, y boyunca );  zarf_cap / zarf_boy:  gövdenin
    çapı ve kasnağın arka yüzünden boyu ( LiftDesigner oranları buna ölçeklenir )."""
    x, y, z = kasnak
    kc, kb = zarf_cap / DISLISIZ_CAP, zarf_boy / DISLISIZ_BOY
    p = [silindir("y", (x, 0, z), D1, y - bk / 2.0, y + bk / 2.0, "KASNAK", "tahrik_kasnagi", "kasnak")]
    a = bk / 2.0
    for ad, boy, cap in DISLISIZ:
        t0, t1 = y + s * a, y + s * (a + boy * kb)
        p.append(silindir("y", (x, 0, z), cap * kc, t0, t1, parca=ad))
        a += boy * kb
    return p


def disli(kasnak, D1, bk, s, m_yon):
    """Sonsuz vidalı dişli makine:  kasnak ekseni y ( dişli kutusu s yönünde ),
    motor ekseni x ( motor m_yon yönünde:  +1 / −1 )."""
    x, y, z = kasnak

    def X(m):
        return x - m_yon * m            # m eksi → motor m_yon yönünde

    def Y(a):
        return y + s * a

    p = [silindir("y", (x, 0, z), D1, Y(-bk / 2.0), Y(bk / 2.0), "KASNAK", "tahrik_kasnagi", "kasnak")]
    for ad, a0, a1, cap in DISLI_EKSEN:
        p.append(silindir("y", (x, 0, z), cap, Y(a0), Y(a1), parca=ad))
    for ad, m0, m1, cap, a, zc in DISLI_SILINDIR:
        p.append(silindir("x", (0, Y(a), z + zc), cap, X(m0), X(m1), parca=ad))
    for ad, m0, m1, a0, a1, z0, z1 in DISLI_KUTU:
        p.append(kutu(X(m0), Y(a0), X(m1), Y(a1), z + z0, z + z1, parca=ad))
    return p


def disli_zarfi(kasnak, s, m_yon):
    """Dişli makinenin plandaki kutusu ( çakışma denetimi için )."""
    x, y, _ = kasnak
    xs = sorted((x - m_yon * DISLI_ZARF["m"][0], x - m_yon * DISLI_ZARF["m"][1]))
    ys = sorted((y + s * DISLI_ZARF["a"][0], y + s * DISLI_ZARF["a"][1]))
    return (xs[0], ys[0], xs[1], ys[1])


# ── ŞASE ─────────────────────────────────────────────────────────────────
def upn_sase(sase, motor_y):
    """sase:  ( x0, y0, x1, y1, zb, zt );  iki UPN kiriş y boyunca, sırtları
    dışarıda ( ağızlar birbirine bakar );  motor plakası motor_y çevresinde
    kirişlerin arasında, üstle aynı hizada;  uçlarda bağlantı levhaları."""
    x0, y0, x1, y1, zb, zt = sase
    h, b, s_, t = UPN["h"], UPN["b"], UPN["s"], UPN["t"]
    zb = zt - h
    p = []
    for sirt, yon in ((x0, 1.0), (x1, -1.0)):
        ag = sirt + yon * b
        xa, xb = sorted((sirt, ag))
        p.append(kutu(xa, y0, xb, y1, zb, zt, "KONSOL", "makine_sasesi", "upn_200"))
        #  Profilin iç kenarları:  gövde ve flanşlar ( uçtan bakınca C, yandan
        #  bakınca flanş çizgileri )
        xg = sirt + yon * s_
        for (ax, az), (bx, bz) in (((ag, zt - t), (xg, zt - t)), ((xg, zt - t), (xg, zb + t)),
                                   ((xg, zb + t), (ag, zb + t))):
            for yy in (y0, y1):
                p.append(cizgi((ax, yy, az), (bx, yy, bz), parca="upn_ici"))
        for zz in (zt - t, zb + t):
            p.append(cizgi((ag, y0, zz), (ag, y1, zz), parca="upn_flansi"))
    ic0, ic1 = x0 + b, x1 - b
    if ic1 > ic0:
        my0 = max(y0, motor_y - MOTOR_PLAKASI_BOY / 2.0)
        my1 = min(y1, motor_y + MOTOR_PLAKASI_BOY / 2.0)
        p.append(kutu(ic0, my0, ic1, my1, zt - MOTOR_PLAKASI_KALINLIK, zt, "KONSOL", "makine_sasesi",
                      "motor_plakasi"))
        for yy in (y0, y1 - UC_LEVHASI):
            p.append(kutu(ic0, yy, ic1, yy + UC_LEVHASI, zb + t, zt - t, "KONSOL", "makine_sasesi",
                          "uc_levhasi"))
    return p


def plan_parcalari(Y, S, sase=True):
    """Kuyu üstü / makine dairesi planı için makine ( ve kuyu üstünde şase )
    cisimleri — kuyu_ustu.yerlesim'in çıktısından;  kotlar yalnız çizim sırası
    içindir ( kasnak merkezi 0, şase makinenin altında )."""
    gv = Y["govde"]
    my = (gv[1] + gv[3]) / 2.0
    p = []
    if sase:
        p += upn_sase(Y["sase"] + (-1000.0 - UPN["h"], -1000.0), my)
    p += Y["makine"]
    if Y["tip"] == "Dişlisiz":
        mx = (Y["kasnak"][0] + Y["kasnak"][2]) / 2.0
        p.append(kutu(mx - S["makine_kapak_en"] / 2.0, my - S["makine_kapak_boy"] / 2.0,
                      mx + S["makine_kapak_en"] / 2.0, my + S["makine_kapak_boy"] / 2.0,
                      S["makine_en"] / 2.0, S["makine_en"] / 2.0 + S["makine_kapak_yukseklik"],
                      parca="klemens_kutusu"))
    return p


def kaydir(parcalar, dz):
    """Cisimleri dz kadar yukarı taşır ( planda kasnak merkezi 0 kotundaydı )."""
    out = []
    for p in parcalar:
        q = dict(p)
        if p["tur"] == "silindir":
            x, y, z = p["merkez"]
            q["merkez"] = (x, y, z + dz)
            if p["eksen"] == "z":
                q["t"] = (p["t"][0] + dz, p["t"][1] + dz)
        elif p["tur"] == "kutu":
            x0, y0, x1, y1, z0, z1 = p["k"]
            q["k"] = (x0, y0, x1, y1, z0 + dz, z1 + dz)
        else:
            q["p0"] = p["p0"][:2] + (p["p0"][2] + dz,)
            q["p1"] = p["p1"][:2] + (p["p1"][2] + dz,)
        out.append(q)
    return out


# ── MAKİNE DAİRESİ:  AYAKLI ŞASE ÇERÇEVESİ VE SAPTIRMA KASNAĞI ──────────────
def cerceve(iz, zd, S):
    """iz:  çerçevenin plandaki kutusu;  zd:  döşeme.  Dört ayak, uzun
    kenarlarda UPN 200, kısa kenarlarda UPN 100, ayak plakaları."""
    x0, y0, x1, y1 = iz
    H, a = S["md_cerceve_yukseklik"], S["md_cerceve_ayak"]
    zt = zd + H
    uzun_x = (x1 - x0) >= (y1 - y0)
    p = []
    ap, at = S["md_cerceve_ayak_plakasi"], S["md_cerceve_ayak_plakasi_kalinlik"]
    for x in (x0, x1 - a):
        for y in (y0, y1 - a):
            p.append(kutu(x, y, x + a, y + a, zd + at, zt - UPN["h"], "KONSOL", "makine_sasesi", "ayak"))
            cx, cy = x + a / 2.0, y + a / 2.0
            p.append(kutu(cx - ap / 2.0, cy - ap / 2.0, cx + ap / 2.0, cy + ap / 2.0, zd, zd + at,
                          "KONSOL", "makine_sasesi", "ayak_plakasi"))
    b = UPN["b"]
    if uzun_x:
        uzun = [(x0, y0, x1, y0 + b), (x0, y1 - b, x1, y1)]
        kisa = [(x0, y0 + b, x0 + b, y1 - b), (x1 - b, y0 + b, x1, y1 - b)]
    else:
        uzun = [(x0, y0, x0 + b, y1), (x1 - b, y0, x1, y1)]
        kisa = [(x0 + b, y0, x1 - b, y0 + b), (x0 + b, y1 - b, x1 - b, y1)]
    for k in uzun:
        p.append(kutu(*k, zt - UPN["h"], zt, "KONSOL", "makine_sasesi", "upn_200"))
    for k in kisa:
        p.append(kutu(*k, zt - 100.0, zt, "KONSOL", "makine_sasesi", "upn_100"))
    return p


def saptirma(merkez, D, bk, zt):
    """Saptırma kasnağı ( ekseni y ) ve çerçevenin üst kirişine asılı iki
    taşıyıcı levha."""
    x, y, z = merkez
    p = [silindir("y", (x, 0, z), D, y - bk / 2.0, y + bk / 2.0, "KASNAK", "saptirma_kasnagi",
                  "saptirma_kasnagi")]
    for yy in (y - bk / 2.0 - 25, y + bk / 2.0 + 5):
        p.append(kutu(x - 50, yy, x + 50, yy + 20, z - 60, zt - UPN["h"], "KONSOL", "makine_sasesi",
                      "saptirma_levhasi"))
    return p


def teget(c1, r1, c2, r2, yon):
    """Aynı yönde dönen iki kasnağın ( x–z düzleminde ) ortak dış teğeti:
    ( P1, P2, n ) — n kasnak merkezlerinden teğet noktalarına birim vektör.
    yon:  halatın tahrik kasnağını terk ettiği yan ( ağırlık tarafı, x
    boyunca ±1 ):  iki dış teğetten normali o yana bakanı."""
    import math
    vx, vz = c2[0] - c1[0], c2[1] - c1[1]
    L = math.hypot(vx, vz)
    phi = math.atan2(vz, vx)
    d = math.acos(max(-1.0, min(1.0, (r1 - r2) / L)))
    adaylar = [(math.cos(phi + s * d), math.sin(phi + s * d)) for s in (1, -1)]
    n = max(adaylar, key=lambda q: yon * q[0])
    return ((c1[0] + r1 * n[0], c1[1] + r1 * n[1]), (c2[0] + r2 * n[0], c2[1] + r2 * n[1]), n)


def sarim_acisi(y_, n):
    """Tahrik kasnağında halatın sarıldığı açı ( derece ):  kabin tarafındaki
    yatay uçtan ( −y_ ) kasnağın üstünden n'ye."""
    import math
    a = math.degrees(math.atan2(n[1], -y_ * n[0]))      # kabin yönünden, üstten
    return a if a >= 0 else a + 360.0


# ── İZDÜŞÜMLER ───────────────────────────────────────────────────────────
def _el(_katman, ad, parca, el):
    el["ad"] = ad
    if parca:
        el["parca"] = parca
    return el


def plan(parcalar, _dik, _daire, _cizgi):
    """Plan ( yukarıdan ):  alçaktaki önce, üstteki sonra çizilir."""
    e = []
    for p in sorted(parcalar, key=lambda q: sinirlar(q)[5]):
        x0, y0, x1, y1, z0, z1 = sinirlar(p)
        if p["tur"] == "cizgi":
            (a, b, _), (c, d, _) = p["p0"], p["p1"]
            if abs(a - c) + abs(b - d) > 1e-9:
                e.append(_el(p["katman"], p["ad"], p["parca"], _cizgi(p["katman"], a, b, c, d)))
        elif p["tur"] == "silindir" and p["eksen"] == "z":
            x, y, _ = p["merkez"]
            e.append(_el(p["katman"], p["ad"], p["parca"], _daire(p["katman"], x, y, p["cap"] / 2.0)))
        else:
            e.append(_el(p["katman"], p["ad"], p["parca"], _dik(p["katman"], x0, y0, x1 - x0, y1 - y0)))
    return e


def gorunus(parcalar, B, _dik, _daire, _cizgi):
    """Düşey kesit ( B:  kesit_parcalari.Bakis ):  kesit düzleminin gerisi
    çizilmez;  bakanın uzağındaki önce, yakınındaki sonra çizilir."""
    yon = B.kesit[2] if B.kesit else 1.0
    #  Bakış yönü:  yan ( u = y ) x boyunca, ön ( u = G − x ) y boyunca bakar
    eks = 0 if B.tur == "yan" else 1

    def uzaklik(q):
        k = sinirlar(q)
        return yon * (k[eks] + k[eks + 2]) / 2.0

    e = []
    for p in sorted(parcalar, key=uzaklik, reverse=True):
        x0, y0, x1, y1, z0, z1 = sinirlar(p)
        if not B.gorunur((x0, y0, x1, y1)):
            continue
        if p["tur"] == "cizgi":
            (a, b, c), (d, f, h) = p["p0"], p["p1"]
            ua, ub = B.u(a, b), B.u(d, f)
            if abs(ua - ub) + abs(c - h) > 1e-9:
                e.append(_el(p["katman"], p["ad"], p["parca"], _cizgi(p["katman"], ua, c, ub, h)))
            continue
        bakis_ekseni = "x" if B.tur == "yan" else "y"
        if p["tur"] == "silindir" and p["eksen"] == bakis_ekseni:
            x, y, z = p["merkez"]
            e.append(_el(p["katman"], p["ad"], p["parca"], _daire(p["katman"], B.u(x, y), z, p["cap"] / 2.0)))
            continue
        u0, u1 = B.aralik((x0, y0, x1, y1))
        e.append(_el(p["katman"], p["ad"], p["parca"], _dik(p["katman"], u0, z0, u1 - u0, z1 - z0)))
    return e
