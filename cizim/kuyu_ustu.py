# -*- coding: utf-8 -*-
"""
KUYU ÜSTÜ PLANI  ( makine dairesiz asansör — kuyu tepesinden yatay kesit )

Makine dairesi olmayan asansörde makine kuyunun tepesindedir;  bu plan
ELEport'un MRL paftasındaki "Machine Room" çiziminin karşılığıdır.  Kuyu
planının duvarlarını, raylarını ve konsollarını AYNEN kullanır;  kabin ve
karşı ağırlık yalnız izleriyle ( kesik ) görünür.  Üstüne gelenler:

  · makine ve tahrik kasnağı  ( karşı ağırlığın üstünde )
  · 2:1 askıda halatların kuyu tepesine bağlandığı yerler
  · hız regülatörü  ( kuyu dibindeki gergi kasnağının tam üstünde )
  · ACİL KURTARMA VE TEST PANOSU  kuyunun dışında, en üst katta kapının
    yanında, önünde çalışma alanıyla          TS EN 81-20 m.5.2.6.6

HALATLAR DÜŞEY İNER.  Tahrik kasnağının bir teğeti kabinin yakın halatının
hizasındadır ( kabin kasnağının dış teğeti );  öbür teğetinden inen halat
karşı ağırlık kasnağının teğetine düşmelidir.  Düşmüyorsa sapma ölçüyle
gösterilir — bu ELEport'un paftasında birebir tutar ( 370 − 240 = 130 ).

Bugün çizilen düzen:  karşı ağırlık yanda, kabin altı 2:1 askı ( ofisin ve
ELEport'un düzeni ).  Öteki düzenler için doğrulama açıkça reddeder.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import sabitler as CS

#  TS EN 81-20 m.5.2.6.6.4 → m.5.2.6.3.2.1 a:  panonun önünde en az 0,70 m
#  derinlikte, en az 0,50 m ya da pano eni kadar genişlikte boş alan.
CALISMA_DERINLIK = 700.0
CALISMA_EN_ASGARI = 500.0
YANLAR = ("Sol", "Sağ")
_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "EKSEN")


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    ku, kd, ag = g.get("kuyu_ustu") or {}, g.get("kuyu_dibi") or {}, g["agirlik"]
    hata = []
    if (g.get("aski") or {}).get("duzen") != "Kabin altı":
        hata.append("Kuyu üstü planı bugün yalnız kabin altı 2:1 askıyı çizer.")
    if ag["yeri"] not in YANLAR:
        hata.append("Kuyu üstü planı bugün yalnız yandaki karşı ağırlığı çizer.")
    if not (_sayi(ag.get("kasnak_capi")) and ag["kasnak_capi"] > 0):
        hata.append("agirlik.kasnak_capi:  2:1 askıda karşı ağırlık kasnağının çapı girilmeli.")
    if not (_sayi(ku.get("tahrik_kasnak_capi")) and ku["tahrik_kasnak_capi"] > 0):
        hata.append(f"kuyu_ustu.tahrik_kasnak_capi: sayı olmalı ( {ku.get('tahrik_kasnak_capi')!r} ).")
    if ku.get("acil_pano_yan") not in YANLAR:
        hata.append(f"kuyu_ustu.acil_pano_yan: {YANLAR} içinden olmalı ( {ku.get('acil_pano_yan')!r} ).")
    for alan in ("regulator_kaciklik", "regulator_kasnak_capi"):
        if not _sayi(kd.get(alan)):
            hata.append(f"kuyu_dibi.{alan}: regülatör onun tam üstündedir, girilmeli.")
    if kd.get("regulator_yan") not in YANLAR:
        hata.append("kuyu_dibi.regulator_yan: regülatör gergi kasnağının tam üstündedir, girilmeli.")
    if hata:
        return {"hata": hata}

    taban = CGE.plan(g, S)
    k = g["kuyu"]
    G, D = k["genislik"], k["derinlik"]
    kabin = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = _kutu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
    sol = ag["yeri"] == "Sol"
    ry = g["kabin_ray"]["kapi_arasi"]
    ag_y = ry + ag["eksen_kaciklik"]
    ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]

    #  ── HALATLAR ─────────────────────────────────────────────────────
    (xl, y0), (xr, _) = CGE.halat_konumlari(g, S)
    yakin, uzak = (xl, xr) if sol else (xr, xl)
    D1 = ku["tahrik_kasnak_capi"]
    y_ = -1.0 if sol else 1.0                       # kabinden ağırlığa doğru
    ag_dusus_x = yakin + y_ * D1                    # tahrik kasnağının öbür teğeti
    R = ag["kasnak_capi"] / 2.0
    teget1, teget2 = sorted((ag_y - R, ag_y + R), key=lambda t: abs(t - y0))
    sapma = (ag_dusus_x - ex, y0 - teget1)

    #  ── MAKİNE:  tahrik kasnağı + gövde ───────────────────────────────
    #  Kasnak halat çizgisinde;  gövde kasnağın ağırlık eksenine bakan
    #  tarafında ( ELEport:  kasnak 865–970, gövde 985–1.264 ).
    kx0, kx1 = sorted((yakin, ag_dusus_x))
    kt = S["tahrik_kasnak_kalinlik"] / 2.0
    kasnak = (kx0, y0 - kt, kx1, y0 + kt)
    s = 1.0 if ag_y >= y0 else -1.0
    kmx = (kx0 + kx1) / 2.0
    g0 = y0 + s * (kt + S["makine_kasnak_boslugu"])
    g1 = g0 + s * S["makine_boy"]
    govde = (kmx - S["makine_en"] / 2.0, min(g0, g1), kmx + S["makine_en"] / 2.0, max(g0, g1))

    #  ── HALAT BAĞLANTILARI ───────────────────────────────────────────
    #  Ağırlık tarafı:  ağırlık kasnağının öbür teğetinin üstünde;  plaka
    #  halattan kabine doğru uzanır.  Kabin tarafı:  kabinin uzak halatının
    #  üstünde, kabin rayının başına bağlı;  plaka halattan kabine doğru.
    ab_y0 = teget2 - s * S["agirlik_baglanti_y"]
    ab_y1 = ab_y0 + s * S["agirlik_baglanti_boy"]
    ab_x0 = ex + y_ * S["agirlik_baglanti_x"]
    ab_x1 = ab_x0 - y_ * S["agirlik_baglanti_en"]
    agirlik_baglanti = (min(ab_x0, ab_x1), min(ab_y0, ab_y1), max(ab_x0, ab_x1), max(ab_y0, ab_y1))
    kb_x0 = uzak + y_ * S["kabin_baglanti_x"]
    kb_x1 = kb_x0 - y_ * S["kabin_baglanti_en"]
    kabin_baglanti = (min(kb_x0, kb_x1), y0 - S["kabin_baglanti_boy"] / 2.0,
                      max(kb_x0, kb_x1), y0 + S["kabin_baglanti_boy"] / 2.0)

    #  ── REGÜLATÖR:  gergi kasnağının tam üstü ─────────────────────────
    raylar = sorted((_kutu(el) for el in taban if el.get("ad") == "kabin_ray"),
                    key=lambda r: r[0])
    sag_reg = kd["regulator_yan"] == "Sağ"
    rx = ((raylar[-1][0] + raylar[-1][2]) / 2.0 if sag_reg
          else (raylar[0][0] + raylar[0][2]) / 2.0)
    #  Rayın iki parçası ( flanş + gövde ) aynı hizada;  birleşik orta
    ray_parca = [r for r in raylar if (r[0] > kabin[2] - 1 if sag_reg else r[2] < kabin[0] + 1)]
    if ray_parca:
        rx = (min(r[0] for r in ray_parca) + max(r[2] for r in ray_parca)) / 2.0
    rgy = ry + kd["regulator_kaciklik"]
    re_, rd = S["regulator_eni"] / 2.0, kd["regulator_kasnak_capi"] / 2.0
    reg_kasnak = (rx - re_, rgy - rd, rx + re_, rgy + rd)
    ge, gb = S["regulator_govde_en"] / 2.0, S["regulator_govde_boy"] / 2.0
    reg_govde = (rx - ge, rgy - gb, rx + ge, rgy + gb)
    reg_ayak = ((reg_govde[2], rgy - gb, G, rgy + gb) if sag_reg
                else (0.0, rgy - gb, reg_govde[0], rgy + gb))

    #  ── ACİL KURTARMA VE TEST PANOSU ─────────────────────────────────
    kp, don = g["kapi"], k["duvar_on"]
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    kasa, pe, pd = S["kasa_yan"], S["acil_pano_en"], S["acil_pano_derinlik"]
    if ku["acil_pano_yan"] == "Sol":
        pano = (x0 - kasa - pe, -don - pd, x0 - kasa, -don)
    else:
        pano = (x1 + kasa, -don - pd, x1 + kasa + pe, -don)
    ce = max(CALISMA_EN_ASGARI, pe)
    pm = (pano[0] + pano[2]) / 2.0
    calisma = (pm - ce / 2.0, pano[1] - CALISMA_DERINLIK, pm + ce / 2.0, pano[1])

    #  ── ÇAKIŞMALAR ───────────────────────────────────────────────────
    parcalar = {"makine": govde, "tahrik kasnağı": kasnak, "ağırlık halat bağlantısı": agirlik_baglanti,
                "kabin halat bağlantısı": kabin_baglanti, "regülatör": reg_govde}
    for ad, p in parcalar.items():
        if p[0] < 0 or p[1] < 0 or p[2] > G or p[3] > D:
            hata.append(f"{ad.capitalize()} kuyunun dışına taşıyor.")
    adlar = list(parcalar)
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            if {a, b} == {"makine", "tahrik kasnağı"}:
                continue
            if _ortusur(parcalar[a], parcalar[b]):
                hata.append(f"Kuyu üstünde {a} ile {b} üst üste biniyor.")

    return {"taban": taban, "kabin": kabin, "blok": blok, "halatlar": [(xl, y0), (xr, y0)],
            "ag_dusus": (ag_dusus_x, y0), "ag_teget": (ex, teget1), "ag_teget2": (ex, teget2),
            "sapma": sapma, "kasnak": kasnak, "govde": govde, "agirlik_baglanti": agirlik_baglanti,
            "kabin_baglanti": kabin_baglanti, "reg_kasnak": reg_kasnak, "reg_govde": reg_govde,
            "reg_ayak": reg_ayak, "pano": pano, "calisma": calisma, "D1": D1,
            "ag_y": ag_y, "ry": ry, "ex": ex, "hata": hata, "S": S}


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    Y = yerlesim(g, cizim_sabitleri)
    k = g["kuyu"]
    G, D, don, dg, dar, ds = (k["genislik"], k["derinlik"], k["duvar_on"], k["duvar_sag"],
                              k["duvar_arka"], k["duvar_sol"])
    e = [el for el in Y["taban"] if el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi"]

    def kutu(katman, p, ad):
        e.append(CGE._ad(CGE._dik(katman, p[0], p[1], p[2] - p[0], p[3] - p[1]), ad))

    #  İzler:  kabin, karşı ağırlık, kat kapısı ( kesik )
    kutu("GIZLI", Y["kabin"], "kabin_izi")
    kutu("GIZLI", Y["blok"], "agirlik_izi")
    kp = g["kapi"]
    kutu("GIZLI", (kp["sol_pay"], -don, kp["sol_pay"] + kp["genislik"], 0), "kapi_izi")

    #  Makine
    kutu("MAKINE", Y["govde"], "makine")
    kutu("KASNAK", Y["kasnak"], "tahrik_kasnagi")
    gv, ks = Y["govde"], Y["kasnak"]
    e.append(CGE._yazi((gv[0] + gv[2]) / 2.0, (gv[1] + gv[3]) / 2.0, "MAKİNE", 40))
    e.append(CGE._yazi((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0, f"ø {Y['D1']:g}", 38))

    #  Halat bağlantıları, sonra halatlar ( işaret plakanın üstünde görünsün )
    kutu("BAGLANTI", Y["agirlik_baglanti"], "agirlik_baglanti")
    kutu("BAGLANTI", Y["kabin_baglanti"], "kabin_baglanti")
    for p in (Y["agirlik_baglanti"], Y["kabin_baglanti"]):
        e.append(CGE._yazi((p[0] + p[2]) / 2.0, p[3] + 40, "HALAT BAĞLANTISI", 30))
    for hx, hy in Y["halatlar"] + [Y["ag_dusus"], Y["ag_teget2"]]:
        e.append(CGE._ad(CGE._daire("KASNAK", hx, hy, 20), "halat"))

    #  Regülatör
    kutu("KONSOL", Y["reg_ayak"], "regulator_ayak")
    kutu("MAKINE", Y["reg_govde"], "regulator")
    kutu("KASNAK", Y["reg_kasnak"], "regulator_kasnak")
    rg = Y["reg_govde"]
    e.append(CGE._yazi(rg[0] - 60 if rg[0] > G / 2 else rg[2] + 60, (rg[1] + rg[3]) / 2.0,
                       "REGÜLATÖR", 34, aci=90))

    #  Acil kurtarma ve test panosu + çalışma alanı
    kutu("PANO", Y["pano"], "acil_pano")
    kutu("SIGINMA", Y["calisma"], "calisma_alani")
    pn, ca = Y["pano"], Y["calisma"]
    e.append(CGE._yazi((pn[0] + pn[2]) / 2.0, (pn[1] + pn[3]) / 2.0, "ACİL PANO", 34))
    e.append(CGE._yazi((ca[0] + ca[2]) / 2.0, (ca[1] + ca[3]) / 2.0, "ÇALIŞMA ALANI", 34))

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    O = CGE._olcu
    xl, xr = Y["halatlar"][0][0], Y["halatlar"][1][0]
    kx = (Y["kabin"][0] + Y["kabin"][2]) / 2.0
    u0, u1 = D + dar + 120, D + dar + 320
    xs = sorted({0.0, G, Y["ex"], Y["ag_dusus"][0], xl, xr, kx})
    e += [O("yatay", (a, 0), (b, 0), u0,
            f"ø {Y['D1']:g}" if (a, b) == (Y["kasnak"][0], Y["kasnak"][2]) else None)
          for a, b in zip(xs, xs[1:])]
    e.append(O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    #  Sağ:  halat çizgisi, kabin ray ekseni, regülatör
    s0, s1 = G + dg + 120, G + dg + 320
    ys = sorted({0.0, D, Y["halatlar"][0][1], Y["ry"], (Y["reg_kasnak"][1] + Y["reg_kasnak"][3]) / 2.0})
    e += [O("dusey", (0, a), (0, b), s0) for a, b in zip(ys, ys[1:])]
    e.append(O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    #  Sol:  ağırlık kasnağının teğetleri ve ekseni ( halat düşüşü )
    t1, t2 = Y["ag_teget"][1], Y["ag_teget2"][1]
    ys = sorted({0.0, D, t1, t2, Y["ag_y"], Y["ry"]})
    e += [O("dusey", (0, a), (0, b), -ds - 120) for a, b in zip(ys, ys[1:])]
    #  Acil pano çalışma alanı  ( m.5.2.6.3.2.1 a )
    e.append(O("yatay", (ca[0], 0), (ca[2], 0), ca[1] - 90, f"{ca[2] - ca[0]:g}"))
    e.append(O("dusey", (0, ca[1]), (0, ca[3]), ca[0] - 90 if ca[0] > G / 2 else ca[2] + 90,
               f"{ca[3] - ca[1]:g}"))
    #  Halat sapması — varsa
    dx, dy = Y["sapma"]
    if abs(dx) > 0.5:
        a, b = sorted((Y["ag_dusus"][0], Y["ex"]))
        e.append(O("yatay", (a, 0), (b, 0), Y["ag_dusus"][1] - 150, f"HALAT SAPMASI {abs(dx):g}"))
    if abs(dy) > 0.5:
        a, b = sorted((Y["ag_dusus"][1], t1))
        e.append(O("dusey", (0, a), (0, b), Y["ex"] + 150, f"HALAT SAPMASI {abs(dy):g}"))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e
