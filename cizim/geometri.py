# -*- coding: utf-8 -*-
"""
KUYU PLANI GEOMETRİSİ

Girdiden ( cizim/girdi.py ) + ofis çizim sabitlerinden ( cizim/sabitler.py )
çizim elemanları üretir.  Elemanlar saf veridir;  SVG ve DXF yazıcıları aynı
listeyi okur — iki ayrı çizici yazılmaz.

EKSEN DÜZENİ:  x kuyu genişliği boyunca, y derinlik;  ( 0 , 0 ) kuyu iç
boşluğunun sol-ön ( kapı ) köşesidir.

DBG / DBGW:  rayların BİRBİRİNE BAKAN YÜZLERİ arasındaki açıklıktır, eksenden
eksene değil.  ( ELEport'un paftasında da böyle ölçülüyor:  sağ ray 1955'te
başlıyor, sol rayın yüzü 405'te bitiyor → 1550 = DBG. )  Ray, bu yüzden
DUVARA DOĞRU kendi yüksekliği ( h ) kadar uzanır.
"""
from cizim import sabitler as CS

KATMANLAR = ("KUYU-DUVAR", "TARAMA", "BINA", "KUYU-IC", "KABIN", "KABIN-IC",
             "SASE", "KAPI", "AGIRLIK", "RAY", "KONSOL", "CIVATA", "PATEN",
             "KASNAK", "PANO", "OLCU", "EKSEN", "YAZI", "CERCEVE")

#  T profilinde flanş / gövde et kalınlığı;  1/20 planda ayrıntı okunmaz,
#  flanş + gövde yeterlidir.
_ET = 0.18


def _dik(katman, x, y, g, d, tip="dikdortgen", ad=""):
    el = {"tip": tip, "katman": katman, "x": float(x), "y": float(y),
          "g": float(g), "d": float(d)}
    if ad:
        el["ad"] = ad
    return el


def _cizgi(katman, x1, y1, x2, y2, tip="cizgi"):
    return {"tip": tip, "katman": katman, "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2)}


def _olcu(yon, a, b, kot, metin=None):
    uzunluk = abs(b[0] - a[0]) if yon == "yatay" else abs(b[1] - a[1])
    return {"tip": "olcu", "katman": "OLCU", "yon": yon, "a": tuple(map(float, a)),
            "b": tuple(map(float, b)), "kot": float(kot),
            "metin": metin if metin is not None else f"{uzunluk:g}",
            "uzunluk": uzunluk}


def _daire(katman, x, y, r):
    return {"tip": "daire", "katman": katman, "x": float(x), "y": float(y), "r": float(r)}


def _ok(katman, x1, y1, x2, y2):
    """Yön oku  ( kapı açılış yönü gibi )."""
    return {"tip": "ok", "katman": katman, "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2)}


def _yazi(x, y, metin, yukseklik=55, hiza="orta", katman="YAZI", aci=0):
    return {"tip": "yazi", "katman": katman, "x": float(x), "y": float(y),
            "metin": metin, "yukseklik": yukseklik, "hiza": hiza, "aci": float(aci)}


def _ray_yatay(yuz_x, eksen_y, b, h, yon):
    """Kabin rayı:  yüzü kabine bakar, gövdesi `yon` yönünde duvara uzanır."""
    t = b * _ET
    dis = yuz_x + h * yon                      # flanşın dış yüzü  ( duvar tarafı )
    flans_x = dis if yon > 0 else dis          # dikdörtgen sol köşesi
    flans_x = dis - t if yon > 0 else dis
    govde_x = yuz_x if yon > 0 else dis + t    # gövde YÜZDEN flanşa uzanır
    return [
        _dik("RAY", flans_x, eksen_y - b / 2.0, t, b),                      # flanş
        _dik("RAY", govde_x, eksen_y - t / 2.0, h - t, t),                  # gövde
    ]


def _ray_dusey(yuz_y, eksen_x, b, h, yon):
    """Ağırlık rayı:  yüzü ağırlığa bakar, gövdesi `yon` yönünde uzanır."""
    t = b * _ET
    dis = yuz_y + h * yon
    flans_y = dis - t if yon > 0 else dis
    govde_y = yuz_y if yon > 0 else dis + t
    return [
        _dik("RAY", eksen_x - b / 2.0, flans_y, b, t),
        _dik("RAY", eksen_x - t / 2.0, govde_y, t, h - t),
    ]


def plan(g, cizim_sabitleri=None):
    """Kuyu planının elemanları  ( liste )."""
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    k, kb, kp = g["kuyu"], g["kabin"], g["kapi"]
    kr, ag = g["kabin_ray"], g["agirlik"]
    G, D = k["genislik"], k["derinlik"]
    ds, dg, don, dar = k["duvar_sol"], k["duvar_sag"], k["duvar_on"], k["duvar_arka"]
    e = []

    #  ── DUVARLAR  ( tarama yalnız duvar kesitinde ) ───────────────────
    for x, y, g_, d_ in ((-ds, -don, G + ds + dg, don), (-ds, D, G + ds + dg, dar),
                         (-ds, 0, ds, D), (G, 0, dg, D)):
        e.append(_dik("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(_dik("KUYU-DUVAR", x, y, g_, d_))
    e.append(_dik("KUYU-IC", 0, 0, G, D))

    #  ── KAPI:  boşluk · kasa · eşik · kanatlar ───────────────────────
    #  Kanatlar ve eşik KUYUNUN İÇİNDEDİR;  kasa duvarın içine oturur.
    x0 = kp["sol_pay"]
    kg = kp["genislik"]
    e.append(_dik("KAPI", x0, -don, kg, don))                       # boşluk
    for kx0 in (x0 - S["kasa_yan"], x0 + kg):                       # kasa yanları
        e.append(_dik("KAPI", kx0, -S["kasa_derinlik"], S["kasa_yan"], S["kasa_derinlik"]))
    e.append(_dik("KAPI", x0, 0, kg, S["esik_derinlik"]))           # kat kapısı eşiği
    #  KANATLAR:  kapalı konumda çizilir, eşiğin hemen arkasında dururlar.
    #  Teleskopik kapıda kanatlar AYRI DERİNLİKTE ( biri öbürünün önünde ),
    #  merkezi kapıda aynı hizadadır.
    kanat = kg / 2.0
    tel = str(kp.get("tip", "")).startswith("Teleskopik")
    for i in range(2):
        kx0 = x0 + i * kanat
        ky0 = S["esik_derinlik"] + (i * S["kanat_araligi"] if tel else 0)
        e.append(_dik("KAPI", kx0, ky0, kanat, S["kanat_kalinlik"]))
    #  Açılış yönü oku:  teleskopik kapı hangi yana açılıyorsa o yöne bakar.
    ok_y = S["esik_derinlik"] + S["kanat_kalinlik"] / 2.0
    if tel:
        sag = str(kp.get("tip", "")).endswith("Sağ")
        e.append(_ok("KAPI", x0 + (kg * 0.65 if sag else kg * 0.35), ok_y,
                     x0 + (kg if sag else 0), ok_y))
    else:
        e.append(_ok("KAPI", x0 + kg / 2.0, ok_y, x0, ok_y))
        e.append(_ok("KAPI", x0 + kg / 2.0, ok_y, x0 + kg, ok_y))
    #  Kapının iki yanındaki bina duvarı yalnız istenirse çizilir.
    if S["bina_duvari"] > 0:
        for bx0, bg in ((-ds, x0 + ds), (x0 + kg, G - (x0 + kg) + dg)):
            if bg > 0:
                e.append(_dik("BINA", bx0, -don - S["bina_duvari"], bg, S["bina_duvari"],
                              tip="tarama_tugla"))

    #  ── KABİN:  pano · şase · kapı mekanizması ───────────────────────
    kx = G / 2.0 + kb["kaciklik_y"]
    ic_on = kb["on_pay"]                                   # kabin iç ön yüzü
    ky = ic_on + kb["derinlik"] / 2.0
    dis_g = kb["genislik"] + 2 * S["kabin_pano_yan"]
    dis_d = kb["derinlik"] + S["kabin_pano_arka"]
    e.append(_dik("KABIN", kx - dis_g / 2.0, ic_on, dis_g, dis_d))          # kabin dışı
    e.append(_dik("KABIN-IC", kx - kb["genislik"] / 2.0, ic_on,
                  kb["genislik"], kb["derinlik"]))                          # kabin içi
    #  şase dikmeleri:  kabinin iki yanında, ray eksenine dik
    for sx in (kx - dis_g / 2.0 - S["sase_dikme"], kx + dis_g / 2.0):
        e.append(_dik("SASE", sx, ic_on, S["sase_dikme"], dis_d))
    #  şase ALT / ÜST kirişleri:  iki dikmeyi bağlar  ( planda kabinin ön ve
    #  arka kenarında görünür )
    for sy in (ic_on, ic_on + dis_d - S["sase_dikme"]):
        e.append(_dik("SASE", kx - dis_g / 2.0 - S["sase_dikme"], sy,
                      dis_g + 2 * S["sase_dikme"], S["sase_dikme"]))
    #  Kabin kapısı mekanizma kutusu KABİN ÖN YÜZÜNDE durur  ( kapı ile kabin
    #  arasında;  kullanıcı kararı — ELEport'un paftasındaki yerleşimin aynısı ).
    e.append(_dik("KABIN", x0 + kg / 2.0 - S["kabin_kapisi_kutu_en"] / 2.0,
                  ic_on - S["kabin_kapisi_kutu_boy"] + 20,
                  S["kabin_kapisi_kutu_en"], S["kabin_kapisi_kutu_boy"]))
    e.append(_cizgi("EKSEN", kx, -don - 150, kx, D + dar + 150, tip="eksen"))
    e.append(_cizgi("EKSEN", -ds - 150, ky, G + dg + 150, ky, tip="eksen"))

    #  ── KABİN RAYLARI · KONSOL · PATEN ───────────────────────────────
    ry = kr["kapi_arasi"]
    sol_yuz, sag_yuz = kx - kr["arasi"] / 2.0, kx + kr["arasi"] / 2.0
    for yon, yuz in ((-1, sol_yuz), (+1, sag_yuz)):
        e += _ray_yatay(yuz, ry, kr["b"], kr["h"], yon)
        #  konsol:  duvara dayanan plaka  ( boşluğu doldurmaz )
        arka = yuz + kr["h"] * yon          # rayın duvara bakan yüzü
        duvar_x = 0 if yon < 0 else G
        kx0 = duvar_x if yon > 0 else duvar_x - S["konsol_kabin_en"]
        kx0 = duvar_x - S["konsol_kabin_en"] if yon > 0 else duvar_x
        e.append(_dik("KONSOL", kx0, ry - S["konsol_kabin_boy"] / 2.0,
                      S["konsol_kabin_en"], S["konsol_kabin_boy"], ad="plaka"))
        for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
            e.append(_daire("CIVATA", kx0 + S["konsol_kabin_en"] / 2.0, cy,
                            S["konsol_civata_capi"] / 2.0))
        #  KONSOL KOLU:  plakayı rayın arkasına bağlar.  Kolsuz çizimde konsol
        #  raydan kopuk duruyordu  ( karşı ağırlık tarafında açıklık büyük ).
        kol_bas = min(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else min(arka, kx0)
        kol_son = max(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else max(arka, kx0)
        if kol_son - kol_bas > 1:
            e.append(_dik("KONSOL", kol_bas, ry - S["konsol_kabin_boy"] / 6.0,
                          kol_son - kol_bas, S["konsol_kabin_boy"] / 3.0, ad="kol"))
        #  paten:  ray yüzünü kavrar
        e.append(_dik("PATEN", yuz - S["paten_en"] / 2.0, ry - S["paten_boy"] / 2.0,
                      S["paten_en"], S["paten_boy"]))
    e.append(_cizgi("EKSEN", -ds - 150, ry, G + dg + 150, ry, tip="eksen"))

    #  ── ASKI DÜZENİ  ( kullanıcı seçer:  kabin altı · kabin üstü · doğrudan )
    #  Kasnakların ve askı noktalarının yeri GİRDİDEN gelir;  koda gömülmez.
    aski = g.get("aski") or {}
    duzen = aski.get("duzen")
    aski_y = ic_on + dis_d / 2.0 + aski.get(
        "kasnak_kaciklik" if duzen in ("Kabin altı", "Kabin üstü") else "nokta_kaciklik", 0)
    if duzen in ("Kabin altı", "Kabin üstü"):
        dc, aralik = aski["kasnak_capi"], aski["kasnak_arasi"]
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(_dik("KASNAK", merkez - dc / 2.0, aski_y - S["kabin_kasnak_genislik"] / 2.0,
                          dc, S["kabin_kasnak_genislik"]))
            e.append(_yazi(merkez, aski_y + S["kabin_kasnak_genislik"] / 2.0 + 45,
                           f"ø {dc:g}", 45))
        e.append(_yazi(kx, aski_y - S["kabin_kasnak_genislik"] / 2.0 - 60,
                       f"ASKI:  {duzen.upper()}  ·  2:1", 44))
    elif duzen == "Doğrudan":
        aralik = aski["nokta_arasi"]
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(_daire("KASNAK", merkez, aski_y, 45))
            e.append(_cizgi("KASNAK", merkez - 70, aski_y, merkez + 70, aski_y))
            e.append(_cizgi("KASNAK", merkez, aski_y - 70, merkez, aski_y + 70))
        e.append(_yazi(kx, aski_y - 130, "ASKI:  DOĞRUDAN  ·  1:1", 44))

    #  ── KARŞI AĞIRLIK:  çerçeve · dolgu · kasnak · raylar ────────────
    cer = S["agirlik_cerceve"]
    if ag["yeri"] in ("Sağ", "Sol"):
        sol = ag["yeri"] == "Sol"
        yon = +1 if sol else -1
        ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]         # ağırlık ekseni
        ax, ay = ex - ag["derinlik"] / 2.0, ry - ag["genislik"] / 2.0
        e.append(_dik("AGIRLIK", ax, ay, ag["derinlik"], ag["genislik"]))
        e.append(_dik("AGIRLIK", ax + cer, ay + cer,
                      ag["derinlik"] - 2 * cer, ag["genislik"] - 2 * cer))
        for yuz, y_yon in ((ry + ag["ray_arasi"] / 2.0, +1), (ry - ag["ray_arasi"] / 2.0, -1)):
            e += _ray_dusey(yuz, ex, ag["b"], ag["h"], y_yon)
            #  AĞIRLIK RAYI KONSOLU:  duvara dayanan plaka + kolu + cıvataları.
            #  Ray ekseni duvara dik olduğu için konsol da dik durur.
            duvar_x = 0 if sol else G
            plaka_x = duvar_x if sol else duvar_x - S["konsol_agirlik_en"]
            ray_arkasi = yuz + ag["h"] * y_yon
            e.append(_dik("KONSOL", plaka_x, ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
                          S["konsol_agirlik_en"], S["konsol_agirlik_boy"], ad="plaka"))
            for cx in (plaka_x + S["konsol_agirlik_en"] / 2.0 - S["konsol_civata_araligi"],
                       plaka_x + S["konsol_agirlik_en"] / 2.0 + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", cx, ray_arkasi, S["konsol_civata_capi"] / 2.0))
        if g.get("agirlik_kasnak_capi"):
            dc = g["agirlik_kasnak_capi"]
            e.append(_dik("KASNAK", ex - ag["derinlik"] / 2.0 + cer, ry - dc / 2.0,
                          ag["derinlik"] - 2 * cer, dc))
            e.append(_yazi(ex, ry + dc / 2.0 + 45, f"ø {dc:g}", 45))
    else:
        ey = D - ag["ray_duvar"]
        ex = G / 2.0
        ax, ay = G / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0
        e.append(_dik("AGIRLIK", ax, ay, ag["genislik"], ag["derinlik"]))
        e.append(_dik("AGIRLIK", ax + cer, ay + cer,
                      ag["genislik"] - 2 * cer, ag["derinlik"] - 2 * cer))
        for yuz, x_yon in ((G / 2.0 + ag["ray_arasi"] / 2.0, +1),
                           (G / 2.0 - ag["ray_arasi"] / 2.0, -1)):
            e += _ray_yatay(yuz, ey, ag["b"], ag["h"], x_yon)

    #  ── KUMANDA PANOSU ───────────────────────────────────────────────
    if S["pano_duvar"] in ("Sağ", "Sol"):
        px = (G - S["pano_derinlik"]) if S["pano_duvar"] == "Sağ" else 0
        e.append(_dik("PANO", px, kb["on_pay"] + 200, S["pano_derinlik"], S["pano_en"]))
        e.append(_yazi(px + S["pano_derinlik"] / 2.0,
                       kb["on_pay"] + 200 + S["pano_en"] / 2.0, "PANO", 42))

    #  ── ÖLÇÜLER  ( üç kademe;  her zincir toplama kapanır ) ──────────
    u1, u2, u3 = D + dar + 120, D + dar + 320, D + dar + 520
    e += [
        _olcu("yatay", (-ds, 0), (0, 0), u1, f"DUVAR {ds:g}"),
        _olcu("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"),
        _olcu("yatay", (G, 0), (G + dg, 0), u1, f"DUVAR {dg:g}"),
        _olcu("yatay", (-ds, 0), (G + dg, 0), u2, f"DIŞ ÖLÇÜ {G + ds + dg:g}"),
        _olcu("yatay", (0, 0), (sol_yuz - kr["h"], 0), u3),
        _olcu("yatay", (sol_yuz - kr["h"], 0), (sol_yuz, 0), u3, f"RAY {kr['h']:g}"),
        _olcu("yatay", (sol_yuz, 0), (sag_yuz, 0), u3, f"DBG {kr['arasi']:g}"),
        _olcu("yatay", (sag_yuz, 0), (sag_yuz + kr["h"], 0), u3, f"RAY {kr['h']:g}"),
        _olcu("yatay", (sag_yuz + kr["h"], 0), (G, 0), u3),
    ]
    a1, a2, a3 = (-don - S["bina_duvari"] - 120, -don - S["bina_duvari"] - 320,
                  -don - S["bina_duvari"] - 520)
    #  KAPI ZİNCİRİ:  kasa payları AYRI ölçülür  ( ELEport da böyle veriyor ).
    kasa = S["kasa_yan"]
    e += [
        _olcu("yatay", (0, 0), (x0 - kasa, 0), a1),
        _olcu("yatay", (x0 - kasa, 0), (x0, 0), a1, f"KASA {kasa:g}"),
        _olcu("yatay", (x0, 0), (x0 + kg, 0), a1,
              f"KAPI {kg:g} x {kp.get('yukseklik', 2100):g}"),
        _olcu("yatay", (x0 + kg, 0), (x0 + kg + kasa, 0), a1, f"KASA {kasa:g}"),
        _olcu("yatay", (x0 + kg + kasa, 0), (G, 0), a1),
        _olcu("yatay", (0, 0), (G, 0), a2, f"KUYU GENİŞLİĞİ {G:g}"),
    ]
    # Soldan sağa sıralanmış noktalar: sağ ağırlıkta zincir geri dönmez.
    noktalar = sorted(set([0.0, kx, G] + ([ex] if ag["yeri"] in ("Sağ", "Sol") else [])))
    for sol, sag in zip(noktalar, noktalar[1:]):
        metin = None
        if ((ag["yeri"] == "Sol" and sol == 0 and sag == ex)
                or (ag["yeri"] == "Sağ" and sol == ex and sag == G)):
            metin = f"AĞIRLIK RAYI {sag - sol:g}"
        e.append(_olcu("yatay", (sol, 0), (sag, 0), a3, metin))
    s1, s2 = -ds - 120, -ds - 320
    e += [
        _olcu("dusey", (0, 0), (0, ry), s1, f"RAY EKSENİ {ry:g}"),
        _olcu("dusey", (0, ry), (0, D), s1),
        _olcu("dusey", (0, -don), (0, D + dar), s2, f"DIŞ ÖLÇÜ {D + don + dar:g}"),
    ]
    sg1, sg2, sg3 = G + dg + 120, G + dg + 320, G + dg + 520
    e += [
        _olcu("dusey", (0, 0), (0, D), sg1, f"KUYU DERİNLİĞİ {D:g}"),
        _olcu("dusey", (0, kb["on_pay"]), (0, kb["on_pay"] + kb["derinlik"]), sg2,
              f"KABİN {kb['derinlik']:g}"),
    ]
    if ag["yeri"] == "Arka":
        e.append(_olcu("yatay", (ex - ag["ray_arasi"] / 2.0, ey),
                        (ex + ag["ray_arasi"] / 2.0, ey), D + dar + 920,
                        f"DBGW {ag['ray_arasi']:g}"))
    else:
        e.append(_olcu("dusey", (ex, ry - ag["ray_arasi"] / 2.0),
                        (ex, ry + ag["ray_arasi"] / 2.0), sg3,
                        f"DBGW {ag['ray_arasi']:g}"))

    #  Kabin ile duvar / kapı arasındaki SERBEST BOŞLUKLAR
    ic_sol = kx - dis_g / 2.0 - S["sase_dikme"]
    ic_sag = kx + dis_g / 2.0 + S["sase_dikme"]
    #  Boşluk zincirleri ÇİZİMİN DIŞINDA durur;  içeride kabinin üstüne binip
    #  okunmaz hâle geliyorlardı.
    u4 = D + dar + 720
    sg4 = G + dg + 720
    e += [
        _olcu("yatay", (0, 0), (ic_sol, 0), u4),
        _olcu("yatay", (ic_sol, 0), (ic_sag, 0), u4, f"ŞASE DIŞI {ic_sag - ic_sol:g}"),
        _olcu("yatay", (ic_sag, 0), (G, 0), u4),
        _olcu("dusey", (0, 0), (0, ic_on), sg4, f"KAPI ARASI {ic_on:g}"),
        _olcu("dusey", (0, ic_on), (0, ic_on + dis_d), sg4, f"KABİN + ŞASE {dis_d:g}"),
        _olcu("dusey", (0, ic_on + dis_d), (0, D), sg4),
    ]

    #  Kabin iç genişliği ve kabin – ray boşlukları  ( çizimin içinde, boş alanda )
    kab_kot = ic_on + dis_d + 90
    e += [
        _olcu("yatay", (0, 0), (ic_sol, 0), kab_kot),
        _olcu("yatay", (ic_sol, 0), (kx - kb["genislik"] / 2.0, 0), kab_kot),
        _olcu("yatay", (kx - kb["genislik"] / 2.0, 0), (kx + kb["genislik"] / 2.0, 0), kab_kot,
              f"KABİN İÇİ {kb['genislik']:g}"),
        _olcu("yatay", (kx + kb["genislik"] / 2.0, 0), (ic_sag, 0), kab_kot),
        _olcu("yatay", (ic_sag, 0), (G, 0), kab_kot),
    ]
    #  EŞİK DERİNLİKLERİ  ( kat kapısı ve kabin eşiği ) — çizimin SOLUNDA
    esik_kot = -ds - 520
    e += [
        _olcu("dusey", (0, 0), (0, S["esik_derinlik"]), esik_kot, f"EŞİK {S['esik_derinlik']:g}"),
        _olcu("dusey", (0, S["esik_derinlik"]), (0, ic_on - S["kabin_esik_derinlik"]), esik_kot),
        _olcu("dusey", (0, ic_on - S["kabin_esik_derinlik"]), (0, ic_on), esik_kot,
              f"KABİN EŞİĞİ {S['kabin_esik_derinlik']:g}"),
    ]
    #  AĞIRLIK RAYI KONSOLLARININ KOTLARI  ( ELEport'ta 307 ve 542 )
    if ag["yeri"] in ("Sağ", "Sol"):
        ust = ry + ag["ray_arasi"] / 2.0 + ag["h"]
        alt = ry - ag["ray_arasi"] / 2.0 - ag["h"]
        kon_kot = -ds - 720
        e += [
            _olcu("dusey", (0, 0), (0, alt), kon_kot, f"KONSOL {alt:g}"),
            _olcu("dusey", (0, alt), (0, ust), kon_kot),
            _olcu("dusey", (0, ust), (0, D), kon_kot),
        ]

    #  ASKI ÖLÇÜLERİ:  kasnak / nokta aralığı kabin eksenine göre iki yana,
    #  kaçıklık ise kabin merkezine göre derinlikte ölçülür.
    if duzen in ("Kabin altı", "Kabin üstü", "Doğrudan"):
        aralik = aski.get("kasnak_arasi") or aski.get("nokta_arasi")
        if aralik:
            #  Arka yerleşimde DBGW ölçüsü 920 kotunda duruyor;  askı
            #  zinciri onunla aynı sıraya düşmesin.
            askı_kot = D + dar + 1120
            e += [
                _olcu("yatay", (kx - aralik / 2.0, 0), (kx, 0), askı_kot),
                _olcu("yatay", (kx, 0), (kx + aralik / 2.0, 0), askı_kot,
                      f"ASKI ARASI {aralik:g}"),
            ]
        kac = aski_y - (ic_on + dis_d / 2.0)
        if abs(kac) > 1e-9:
            e.append(_olcu("dusey", (0, aski_y), (0, ic_on + dis_d / 2.0), G + dg + 1120,
                           f"ASKI KAÇIKLIĞI {abs(kac):g}"))

    #  KONSOL CIVATA ARALIĞI  ( sağ konsolda ölçülür )
    civ_kot = G + dg + 920
    e += [
        _olcu("dusey", (0, ry - S["konsol_civata_araligi"]), (0, ry), civ_kot,
              f"CIVATA {S['konsol_civata_araligi']:g}"),
        _olcu("dusey", (0, ry), (0, ry + S["konsol_civata_araligi"]), civ_kot,
              f"{S['konsol_civata_araligi']:g}"),
    ]

    #  ── YAZILAR ──────────────────────────────────────────────────────
    e.append(_dik("KABIN", x0, ic_on - S["kabin_esik_derinlik"], kg, S["kabin_esik_derinlik"]))
    e.append(_yazi(kx, ky, f"KABİN  {kb['genislik']:g} x {kb['derinlik']:g}", 55))
    #  Ölçü zincirlerinin sıfır noktaları  ( ELEport'ta da "0" yazar )
    for zx in (0, G):
        e.append(_yazi(zx, -don - S["bina_duvari"] - 420, "0", 45))
    if ag["yeri"] in ("Sağ", "Sol"):
        #  Blok dar ve uzun:  yazı DİK yazılır ki dışına taşmasın.
        e.append(_yazi(ex, ry, "KARŞI AĞIRLIK", 44, aci=90))
    return e


def sinir(elemanlar, pay=0.0):
    """Elemanların kapsayan dikdörtgeni  ( x1, y1, x2, y2 )."""
    xs, ys = [], []
    for el in elemanlar:
        if el["tip"] in ("dikdortgen", "tarama"):
            xs += [el["x"], el["x"] + el["g"]]; ys += [el["y"], el["y"] + el["d"]]
        elif el["tip"] in ("cizgi", "eksen"):
            xs += [el["x1"], el["x2"]]; ys += [el["y1"], el["y2"]]
        elif el["tip"] == "olcu":
            if el["yon"] == "yatay":
                xs += [el["a"][0], el["b"][0]]; ys += [el["kot"]]
            else:
                ys += [el["a"][1], el["b"][1]]; xs += [el["kot"]]
        elif el["tip"] == "yazi":
            xs.append(el["x"]); ys.append(el["y"])
    return (min(xs) - pay, min(ys) - pay, max(xs) + pay, max(ys) + pay)


def zincirler(elemanlar):
    """Aynı kota düşen ölçüleri zincir hâlinde toplar  ( kapanma denetimi )."""
    gruplar = {}
    for el in elemanlar:
        if el["tip"] == "olcu":
            gruplar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    cikti = []
    for (yon, kot), liste in sorted(gruplar.items()):
        i = 0 if yon == "yatay" else 1
        cikti.append({"yon": yon, "kot": kot,
                      "bas": min(min(el["a"][i], el["b"][i]) for el in liste),
                      "son": max(max(el["a"][i], el["b"][i]) for el in liste),
                      "toplam": sum(el["uzunluk"] for el in liste),
                      "adet": len(liste)})
    return cikti


def cerceveli(elemanlar, baslik, olcek=20, pay=300, seritler=()):
    """Çizimi kendi çerçevesine alır ve altına başlık şeridi ekler.

    ELEport'ta da her çizim ayrı bir çerçevededir ve altında adı ile ölçeği
    yazar.  Çerçeve ölçüleri de kapsar;  yazılar dışarıda kalmaz.
    """
    x1, y1, x2, y2 = sinir(elemanlar, pay)
    serit = 220.0
    e = list(elemanlar)
    e.append(_dik("CERCEVE", x1, y1 - serit, x2 - x1, (y2 - y1) + serit))
    e.append(_cizgi("CERCEVE", x1, y1, x2, y1))
    e.append(_yazi(x1 + 120, y1 - serit / 2.0, f"{baslik}   1/{olcek:g}", 95, hiza="sol",
                   katman="CERCEVE"))
    for i, metin in enumerate(seritler):
        e.append(_yazi(x2 - 120, y1 - serit / 2.0 - i * 120, metin, 70, hiza="sag",
                       katman="CERCEVE"))
    return e
