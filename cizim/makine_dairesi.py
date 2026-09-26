# -*- coding: utf-8 -*-
"""
MAKİNE DAİRESİ PLANI  ve  KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI

Makine daireli asansörde makine kuyunun üstündeki odadadır.  Makinenin,
halatların, bağlantıların ve regülatörün yeri kuyu üstü planıyla AYNIDIR
( kuyu_ustu.yerlesim ):  halatlar aynı noktalardan iner, yalnız bu kez
döşemedeki deliklerden geçer.  İki çizim üretilir:

  MAKİNE DAİRESİ PLANI
    · oda duvarları ve kapısı                      m.5.2.3.2 a ( kapı ≥ 0,60 m )
    · makine, halat bağlantıları, regülatör
    · kumanda panosu ve önündeki çalışma alanı     m.5.2.6.3.2.1 a
    · makinenin başında bakım alanı 0,50 × 0,60    m.5.2.6.3.2.1 b
    · döşeme delikleri ve kuyunun izi ( kesik )

  KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI  ( MMO yönetmeliği m.6/b/3 )
    · kuyunun üstündeki döşeme, delikler ve yerlerinin ölçüleri

DELİKLER ( m.5.2.6.3.3:  "amacı için en küçük" ):  askı halatı demeti
( n halat, kanal aralığı 1,6 · dh — hesap programının kasnak genişliği
bağıntısı ) çevresine halat_delik_payi bırakılır;  demet tahrik ve kabin
tarafında kasnak ekseni ( y ) boyunca, karşı ağırlık bağlantısında ağırlık
kasnağının ekseni ( x ) boyunca dizilir.  Regülatör halatı için
LiftDesigner'ın 200 × 200 deliği kullanılır.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kuyu_ustu as CKT
from cizim import sabitler as CS

#  TS EN 81-20 m.5.2.3.2 a:  makine dairesi kapısı en az 0,60 m genişlikte.
KAPI_ASGARI = 600.0
#  m.5.2.6.3.2.1 b:  hareketli parçaların başında en az 0,50 × 0,60 m.
BAKIM_ALANI = (500.0, 600.0)
#  m.5.2.6.3.2.1 a:  panonun önünde 0,70 m derin, en az 0,50 m ya da pano eni.
CALISMA_DERINLIK = CKT.CALISMA_DERINLIK
CALISMA_EN_ASGARI = CKT.CALISMA_EN_ASGARI
DUVARLAR = ("Ön", "Arka", "Sol", "Sağ")


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


_ortusur = CKT._ortusur


def _icinde(p, oda):
    return oda[0] - 1e-9 <= p[0] and p[2] <= oda[2] + 1e-9 and oda[1] - 1e-9 <= p[1] and p[3] <= oda[3] + 1e-9


def _duvar_seridi(oda, duvar, en, derinlik, konum):
    """Odanın iç yüzüne dayanan kutu:  duvar boyunca `en`, içeri `derinlik`,
    duvarın sol ( ön ) iç köşesinden `konum` kadar ötede.  Döner:  kutu ve
    içeri bakan yön ( çalışma alanı o yöne açılır )."""
    x0, y0, x1, y1 = oda
    if duvar == "Ön":
        return (x0 + konum, y0, x0 + konum + en, y0 + derinlik), (0, 1)
    if duvar == "Arka":
        return (x0 + konum, y1 - derinlik, x0 + konum + en, y1), (0, -1)
    if duvar == "Sol":
        return (x0, y0 + konum, x0 + derinlik, y0 + konum + en), (1, 0)
    return (x1 - derinlik, y0 + konum, x1, y0 + konum + en), (-1, 0)


def _onunde(kutu, yon, derinlik, en):
    """Kutunun iç yüzünün önünde, ona ortalı alan."""
    cx, cy = (kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0
    if yon[1]:
        y = kutu[3] if yon[1] > 0 else kutu[1] - derinlik
        return (cx - en / 2.0, y, cx + en / 2.0, y + derinlik)
    x = kutu[2] if yon[0] > 0 else kutu[0] - derinlik
    return (x, cy - en / 2.0, x + derinlik, cy + en / 2.0)


def _delik(cx, cy, ex, ey):
    return (cx - ex / 2.0, cy - ey / 2.0, cx + ex / 2.0, cy + ey / 2.0)


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    md, a = g.get("makine_dairesi") or {}, g.get("aski") or {}
    hata = []
    for alan in ("genislik", "derinlik", "duvar", "kapi_genislik"):
        if not (_sayi(md.get(alan)) and md[alan] > 0):
            hata.append(f"makine_dairesi.{alan}: sıfırdan büyük bir sayı olmalı ( {md.get(alan)!r} ).")
    for alan in ("x", "y", "kapi_konum"):
        if not _sayi(md.get(alan)):
            hata.append(f"makine_dairesi.{alan}: sayı olmalı ( {md.get(alan)!r} ).")
    for alan in ("kapi_duvar", "pano_duvar"):
        if md.get(alan) not in DUVARLAR:
            hata.append(f"makine_dairesi.{alan}: {DUVARLAR} içinden olmalı ( {md.get(alan)!r} ).")
    for alan in ("halat_adedi", "halat_capi"):
        if not (_sayi(a.get(alan)) and a[alan] > 0):
            hata.append(f"aski.{alan}: döşeme deliği için gerekli ( {a.get(alan)!r} ).")
    if hata:
        return {"hata": hata}
    if md["kapi_genislik"] < KAPI_ASGARI:
        hata.append(f"Makine dairesi kapısı {md['kapi_genislik']:g} mm — TS EN 81-20 m.5.2.3.2 a "
                    f"en az {KAPI_ASGARI:g} mm ister.")
    M = CKT.yerlesim(g, S, acil_pano=False)
    if M["hata"]:
        return {"hata": hata + M["hata"]}
    k = g["kuyu"]
    G, D = k["genislik"], k["derinlik"]
    oda = (md["x"], md["y"], md["x"] + md["genislik"], md["y"] + md["derinlik"])

    #  ── DÖŞEME DELİKLERİ ─────────────────────────────────────────────
    n, dh, p = a["halat_adedi"], a["halat_capi"], S["halat_delik_payi"]
    demet = (n - 1) * 1.6 * dh + dh                  # kasnak ekseni boyunca
    boy, en = demet + 2 * p, dh + 2 * p
    xl, y0 = M["halatlar"][0]
    delikler = [
        ("KABİN", _delik(M["yakin"], y0, en, boy)),
        ("AĞIRLIK", _delik(M["ag_dusus"][0], y0, en, boy)),
        ("AĞIRLIK BAĞLANTISI", _delik(M["ag_teget2"][0], M["ag_teget2"][1], boy, en)),
        ("KABİN BAĞLANTISI", _delik(M["uzak"], y0, en, boy)),
    ]
    rd = S["regulator_delik"]
    rg = g["kuyu_dibi"]["regulator_kasnak_capi"] / 2.0
    delikler += [("REGÜLATÖR", _delik(M["rgx"], M["rgy"] - rg, rd, rd)),
                 ("REGÜLATÖR", _delik(M["rgx"], M["rgy"] + rg, rd, rd))]
    for ad, d in delikler:
        if d[0] < 0 or d[1] < 0 or d[2] > G or d[3] > D:
            hata.append(f"{ad.capitalize()} halatı deliği kuyunun dışına düşüyor.")
    for i, (a1, d1) in enumerate(delikler):
        for a2, d2 in delikler[i + 1:]:
            if _ortusur(d1, d2):
                hata.append(f"{a1.capitalize()} ve {a2.lower()} delikleri üst üste biniyor.")

    #  ── KAPI ─────────────────────────────────────────────────────────
    #  Kapının önündeki geçiş payı:  kapı eni × çalışma derinliği, boş kalır.
    kapi, kyon = _duvar_seridi(oda, md["kapi_duvar"], md["kapi_genislik"], 0.0, md["kapi_konum"])
    kapi_onu = _onunde(kapi, kyon, CALISMA_DERINLIK, md["kapi_genislik"])

    #  ── KUMANDA PANOSU:  seçilen duvar boyunca kapıya en yakın boş yer ─
    sabit = [M["govde"], M["kasnak"], M["agirlik_baglanti"], M["kabin_baglanti"],
             M["reg_govde"], M["reg_kasnak"]] + [d for _, d in delikler]
    pe, pd = S["kumanda_pano_en"], S["kumanda_pano_derinlik"]
    ce = max(CALISMA_EN_ASGARI, pe)
    uzunluk = md["genislik"] if md["pano_duvar"] in ("Ön", "Arka") else md["derinlik"]
    kc = ((kapi[0] + kapi[2]) / 2.0, (kapi[1] + kapi[3]) / 2.0)
    adaylar = []
    konum = 0.0
    while konum + max(pe, ce) <= uzunluk + 1e-9:
        pano, pyon = _duvar_seridi(oda, md["pano_duvar"], pe, pd, konum + (ce - pe) / 2.0 if ce > pe else konum)
        calisma = _onunde(pano, pyon, CALISMA_DERINLIK, ce)
        if _icinde(pano, oda) and _icinde(calisma, oda) and not any(
                _ortusur(x, y) for x in (pano, calisma) for y in sabit + [kapi_onu]):
            pc = ((pano[0] + pano[2]) / 2.0, (pano[1] + pano[3]) / 2.0)
            adaylar.append((abs(pc[0] - kc[0]) + abs(pc[1] - kc[1]), konum, pano, calisma))
        konum += 25.0
    pano = calisma = None
    if adaylar:
        _, _, pano, calisma = min(adaylar)
    else:
        hata.append(f"Kumanda panosu önündeki {CALISMA_DERINLIK:g} mm çalışma alanıyla "
                    f"{md['pano_duvar'].lower()} duvara sığmıyor ( TS EN 81-20 m.5.2.6.3.2.1 a ).")

    #  ── MAKİNENİN BAŞINDA BAKIM ALANI  ( 0,50 × 0,60 ) ─────────────────
    #  Makinenin ( gövde + kasnak ) dört yanından birine, deliklere, panoya
    #  ve kapının önüne basmadan;  makineye en yakın yer.
    mk = (min(M["govde"][0], M["kasnak"][0]), min(M["govde"][1], M["kasnak"][1]),
          max(M["govde"][2], M["kasnak"][2]), max(M["govde"][3], M["kasnak"][3]))
    engel = sabit + [kapi_onu] + ([pano, calisma] if pano else [])
    bakim = None
    adaylar = []
    for w, h in (BAKIM_ALANI, BAKIM_ALANI[::-1]):
        for kutu in _bitisik_adaylar(mk, w, h):
            if _icinde(kutu, oda) and not any(_ortusur(kutu, x) for x in engel):
                c = ((kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0)
                mc = ((mk[0] + mk[2]) / 2.0, (mk[1] + mk[3]) / 2.0)
                adaylar.append((abs(c[0] - mc[0]) + abs(c[1] - mc[1]), kutu))
    if adaylar:
        bakim = min(adaylar)[1]
    else:
        hata.append("Makinenin başında 0,50 × 0,60 m bakım alanı kalmıyor ( TS EN 81-20 "
                    "m.5.2.6.3.2.1 b ).")

    #  Odada durması gerekenler odanın içinde
    for ad, kutu in (("Makine", mk), ("Ağırlık bağlantısı", M["agirlik_baglanti"]),
                     ("Kabin bağlantısı", M["kabin_baglanti"]), ("Regülatör", M["reg_govde"])):
        if not _icinde(kutu, oda):
            hata.append(f"{ad} makine dairesinin dışına taşıyor.")

    return {"M": M, "oda": oda, "delikler": delikler, "kapi": kapi, "kapi_onu": kapi_onu,
            "pano": pano, "calisma": calisma, "bakim": bakim, "makine": mk,
            "demet": demet, "hata": hata, "S": S}


def _bitisik_adaylar(mk, w, h, adim=25.0):
    """Makinenin dört kenarına bitişik, kenar boyunca kayan adaylar."""
    x0, y0, x1, y1 = mk
    xs = [x0 - w + i * adim for i in range(int((x1 - x0 + w) / adim) + 1)]
    ys = [y0 - h + i * adim for i in range(int((y1 - y0 + h) / adim) + 1)]
    for x in xs:
        yield (x, y1, x + w, y1 + h)
        yield (x, y0 - h, x + w, y0)
    for y in ys:
        yield (x1, y, x1 + w, y + h)
        yield (x0 - w, y, x0, y + h)


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _duvarlar(e, oda, t):
    x0, y0, x1, y1 = oda
    for x, y, w, h in ((x0 - t, y0 - t, x1 - x0 + 2 * t, t), (x0 - t, y1, x1 - x0 + 2 * t, t),
                       (x0 - t, y0, t, y1 - y0), (x1, y0, t, y1 - y0)):
        e.append(CGE._dik("TARAMA", x, y, w, h, tip="tarama"))
        e.append(CGE._dik("KUYU-DUVAR", x, y, w, h))
    e.append(CGE._dik("KUYU-IC", x0, y0, x1 - x0, y1 - y0))


def _delik_elemanlari(e, Y):
    for ad, d in Y["delikler"]:
        e.append(CGE._ad(CGE._dik("DELIK", d[0], d[1], d[2] - d[0], d[3] - d[1]), "delik"))


def ciz(g, cizim_sabitleri=None):
    """Makine dairesi planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    M, oda, md = Y["M"], Y["oda"], g["makine_dairesi"]
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    e = []
    _duvarlar(e, oda, md["duvar"])
    #  Kapı:  duvardaki boşluk
    kp, t = Y["kapi"], md["duvar"]
    if kp[1] == kp[3]:                                   # ön / arka duvar
        y = kp[1] if kp[1] > oda[1] else kp[1] - t
        e.append(CGE._ad(CGE._dik("KAPI", kp[0], y, kp[2] - kp[0], t), "oda_kapisi"))
        e.append(CGE._yazi((kp[0] + kp[2]) / 2.0, y + t / 2.0, f"KAPI {md['kapi_genislik']:g}", 34))
    else:
        x = kp[0] if kp[0] > oda[0] else kp[0] - t
        e.append(CGE._ad(CGE._dik("KAPI", x, kp[1], t, kp[3] - kp[1]), "oda_kapisi"))
        e.append(CGE._yazi(x + t / 2.0, (kp[1] + kp[3]) / 2.0, f"KAPI {md['kapi_genislik']:g}", 34, aci=90))
    #  Kuyunun izi
    e.append(CGE._ad(CGE._dik("GIZLI", 0, 0, G, D), "kuyu_izi"))
    _delik_elemanlari(e, Y)

    def kutu(katman, p, ad):
        e.append(CGE._ad(CGE._dik(katman, p[0], p[1], p[2] - p[0], p[3] - p[1]), ad))

    kutu("MAKINE", M["govde"], "makine")
    kutu("KASNAK", M["kasnak"], "tahrik_kasnagi")
    gv, ks = M["govde"], M["kasnak"]
    e.append(CGE._yazi((gv[0] + gv[2]) / 2.0, (gv[1] + gv[3]) / 2.0, "MAKİNE", 40))
    e.append(CGE._yazi((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0, f"ø {M['D1']:g}", 38))
    kutu("BAGLANTI", M["agirlik_baglanti"], "agirlik_baglanti")
    kutu("BAGLANTI", M["kabin_baglanti"], "kabin_baglanti")
    kutu("MAKINE", M["reg_govde"], "regulator")
    kutu("KASNAK", M["reg_kasnak"], "regulator_kasnak")
    rg = M["reg_govde"]
    e.append(CGE._yazi(rg[0] - 60 if rg[0] > G / 2 else rg[2] + 60, (rg[1] + rg[3]) / 2.0,
                       "REGÜLATÖR", 34, aci=90))
    for hx, hy in M["halatlar"] + [M["ag_dusus"], M["ag_teget2"]]:
        e.append(CGE._ad(CGE._daire("KASNAK", hx, hy, 20), "halat"))
    if Y["pano"]:
        kutu("PANO", Y["pano"], "kumanda_panosu")
        kutu("SIGINMA", Y["calisma"], "calisma_alani")
        pn, ca = Y["pano"], Y["calisma"]
        dik = (pn[2] - pn[0]) < (pn[3] - pn[1])
        e.append(CGE._yazi((pn[0] + pn[2]) / 2.0, (pn[1] + pn[3]) / 2.0, "KUMANDA PANOSU", 32,
                           aci=90 if dik else 0))
        e.append(CGE._yazi((ca[0] + ca[2]) / 2.0, (ca[1] + ca[3]) / 2.0, "ÇALIŞMA ALANI", 32,
                           aci=90 if dik else 0))
    if Y["bakim"]:
        kutu("SIGINMA", Y["bakim"], "bakim_alani")
        b = Y["bakim"]
        e.append(CGE._yazi((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0, "BAKIM ALANI", 32))

    #  ── ÖLÇÜLER:  oda ve odanın kuyuya göre yeri ──────────────────────
    O = CGE._olcu
    t = md["duvar"]
    u0, u1 = oda[3] + t + 120, oda[3] + t + 320
    xs = sorted({oda[0], oda[2], 0.0, G})
    e += [O("yatay", (a_, 0), (b_, 0), u0, "KUYU " + f"{G:g}" if (a_, b_) == (0.0, G) else None)
          for a_, b_ in zip(xs, xs[1:])]
    e.append(O("yatay", (oda[0], 0), (oda[2], 0), u1, f"MAKİNE DAİRESİ {oda[2] - oda[0]:g}"))
    s0, s1 = oda[2] + t + 120, oda[2] + t + 320
    ys = sorted({oda[1], oda[3], 0.0, D})
    e += [O("dusey", (0, a_), (0, b_), s0, "KUYU " + f"{D:g}" if (a_, b_) == (0.0, D) else None)
          for a_, b_ in zip(ys, ys[1:])]
    e.append(O("dusey", (0, oda[1]), (0, oda[3]), s1, f"MAKİNE DAİRESİ {oda[3] - oda[1]:g}"))
    #  Çalışma ve bakım alanlarının ölçüleri  ( standardın sayıları )
    for alan in (Y["calisma"], Y["bakim"]):
        if alan:
            e.append(O("yatay", (alan[0], 0), (alan[2], 0), alan[1] + 60, f"{alan[2] - alan[0]:g}",
                       yazi={"x": (alan[0] + alan[2]) / 2.0, "y": alan[1] + 110, "h": 34}))
            e.append(O("dusey", (0, alan[1]), (0, alan[3]), alan[0] + 60, f"{alan[3] - alan[1]:g}",
                       yazi={"x": alan[0] + 110, "y": (alan[1] + alan[3]) / 2.0, "aci": 90, "h": 34}))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e


def delik_plani(g, cizim_sabitleri=None):
    """Kuyu üstü döşeme halat delik planı:  döşeme, delikler ve yerleri."""
    Y = yerlesim(g, cizim_sabitleri)
    k = g["kuyu"]
    G, D, dg, dar, ds = k["genislik"], k["derinlik"], k["duvar_sag"], k["duvar_arka"], k["duvar_sol"]
    e = [el for el in CGE.plan(g, Y["S"])
         if el["katman"] in ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "EKSEN") and el["tip"] != "yazi"]
    _delik_elemanlari(e, Y)
    for ad, d in Y["delikler"]:
        w, h = d[2] - d[0], d[3] - d[1]
        dik = h > w
        e.append(CGE._yazi((d[0] + d[2]) / 2.0 + (0 if dik else 0),
                           (d[1] + d[3]) / 2.0,
                           f"{round(w):g} x {round(h):g}", 30, aci=90 if dik else 0))
    #  Deliklerin yeri EKSENLERİNDEN ölçülür ( inşaat çiziminde delik böyle
    #  verilir );  kenardan ölçülünce 31 – 66 mm'lik parçalarla dolan bir
    #  zincir çıkıyordu.  Her deliğin ekseni kısa çizgiyle işaretlenir.
    O = CGE._olcu
    for _, d in Y["delikler"]:
        cx, cy = (d[0] + d[2]) / 2.0, (d[1] + d[3]) / 2.0
        e.append(CGE._cizgi("EKSEN", d[0] - 40, cy, d[2] + 40, cy, tip="eksen"))
        e.append(CGE._cizgi("EKSEN", cx, d[1] - 40, cx, d[3] + 40, tip="eksen"))
    xs = sorted({0.0, G} | {round((d[0] + d[2]) / 2.0, 3) for _, d in Y["delikler"]})
    ys = sorted({0.0, D} | {round((d[1] + d[3]) / 2.0, 3) for _, d in Y["delikler"]})
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    e += [O("yatay", (a_, 0), (b_, 0), u0) for a_, b_ in zip(xs, xs[1:])]
    e.append(O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    e += [O("dusey", (0, a_), (0, b_), s0) for a_, b_ in zip(ys, ys[1:])]
    e.append(O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e
