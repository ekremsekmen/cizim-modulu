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


def _olcu(yon, a, b, kot, metin=None, yazi=None):
    """Ölçü.  `yazi` verilmezse yazının yeri _yazilari_yerlestir'de bulunur;
    verilirse { x, y ( yazının MERKEZİ ), aci, h } olduğu gibi kullanılır."""
    uzunluk = abs(b[0] - a[0]) if yon == "yatay" else abs(b[1] - a[1])
    el = {"tip": "olcu", "katman": "OLCU", "yon": yon, "a": tuple(map(float, a)),
          "b": tuple(map(float, b)), "kot": float(kot),
          "metin": metin if metin is not None else f"{uzunluk:g}",
          "uzunluk": uzunluk}
    if yazi:
        el["yazi"] = {"x": float(yazi["x"]), "y": float(yazi["y"]),
                      "aci": float(yazi.get("aci", 0)), "h": float(yazi.get("h", OLCU_YAZI))}
    return el


#  Ölçü yazısının yüksekliği ( mm, 1/20'de 2,6 mm ) ve yazı eni tahmini:
#  harf başına yüksekliğin 0,6'sı  ( Arial / DejaVu ortalaması ).
OLCU_YAZI = 52.0


def _yazi_eni(metin, h=OLCU_YAZI):
    return len(metin) * h * 0.6


def _yazilari_yerlestir(elemanlar):
    """Yeri verilmemiş ölçü yazılarını yerleştirir — SVG ve DXF AYNI yeri kullanır.

    Yazı önce kendi parçasının ortasına, ölçü çizgisinin dışına konur.  Aynı
    sıradaki bir yazıyla çakışırsa sıranın ucundaysa ucun dışına, değilse
    bir kat dışarı alınır.  Eskiden sığmayan yazı 130 – 280 mm öteye, BAŞKA
    BİR SIRANIN üstüne itiliyordu;  okuyan onu o sıranın ölçüsü sanıyordu.
    """
    siralar = {}
    for el in elemanlar:
        if el["tip"] == "olcu" and "yazi" not in el:
            siralar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    for (yon, kot), liste in siralar.items():
        i = 0 if yon == "yatay" else 1
        liste.sort(key=lambda q: min(q["a"][i], q["b"][i]))
        dis = -1.0 if kot < 0 else 1.0
        yerlesen = []                                  # ( kat, bas, son )
        for n, q in enumerate(liste):
            bas, son = sorted((q["a"][i], q["b"][i]))
            w = _yazi_eni(q["metin"])
            aday = [(0, (bas + son) / 2.0)]
            uclar = ([(0, bas - w / 2.0 - 30)] if n == 0 else []) + \
                    ([(0, son + w / 2.0 + 30)] if n == len(liste) - 1 else [])
            #  Yazı parçasına sığmıyorsa ve sıranın ucundaysa ucun dışına yazılır
            #  ( ELEport'un "62 83"ü gibi );  sığıyorsa parçanın ortasında durur.
            aday = uclar + aday if w > son - bas - 20 else aday + uclar
            aday += [(1, (bas + son) / 2.0), (2, (bas + son) / 2.0)]
            secilen = aday[-1]
            for kat, orta in aday:
                if not any(k == kat and orta - w / 2.0 < s + 25 and b < orta + w / 2.0 + 25
                           for k, b, s in yerlesen):
                    secilen = (kat, orta)
                    break
            kat, orta = secilen
            yerlesen.append((kat, orta - w / 2.0, orta + w / 2.0))
            capraz = kot + dis * (50.0 + 60.0 * kat)
            q["yazi"] = ({"x": orta, "y": capraz, "aci": 0.0, "h": OLCU_YAZI} if yon == "yatay"
                         else {"x": capraz, "y": orta, "aci": 90.0, "h": OLCU_YAZI})


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
    #  KARŞI AĞIRLIK YANDAYSA o taraftaki kabin rayının duvara giden konsolu
    #  ağırlığın İÇİNDEN geçerdi:  ray ekseni ağırlığın boyu içinde kalır.
    #  O ray, iki ağırlık rayı konsolunun taşıdığı dikine bir ARA KİRİŞE
    #  bağlanır  ( ELEport'un paftasındaki çözüm ).
    ag_yan = ag["yeri"] if ag["yeri"] in ("Sağ", "Sol") else None
    ag_alt = ry - ag["ray_arasi"] / 2.0 - ag["h"]          # ağırlık rayı arkaları
    ag_ust = ry + ag["ray_arasi"] / 2.0 + ag["h"]
    for yon, yuz in ((-1, sol_yuz), (+1, sag_yuz)):
        e += _ray_yatay(yuz, ry, kr["b"], kr["h"], yon)
        arka = yuz + kr["h"] * yon          # rayın duvara bakan yüzü
        if ag_yan == ("Sol" if yon < 0 else "Sağ"):
            kiris_x = arka - S["ara_kiris_en"] if yon < 0 else arka
            e.append(_dik("KONSOL", kiris_x, ag_alt - S["konsol_agirlik_boy"] / 2.0,
                          S["ara_kiris_en"],
                          ag_ust - ag_alt + S["konsol_agirlik_boy"], ad="ara_kiris"))
        else:
            #  konsol:  duvara dayanan plaka  ( boşluğu doldurmaz )
            duvar_x = 0 if yon < 0 else G
            kx0 = duvar_x - S["konsol_kabin_en"] if yon > 0 else duvar_x
            e.append(_dik("KONSOL", kx0, ry - S["konsol_kabin_boy"] / 2.0,
                          S["konsol_kabin_en"], S["konsol_kabin_boy"], ad="plaka"))
            for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", kx0 + S["konsol_kabin_en"] / 2.0, cy,
                                S["konsol_civata_capi"] / 2.0))
            #  KONSOL KOLU:  plakayı rayın arkasına bağlar.
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
    aski_yari = 0.0                      # askı elemanının derinlikteki yarı boyu
    if duzen in ("Kabin altı", "Kabin üstü"):
        dc, aralik = aski["kasnak_capi"], aski["kasnak_arasi"]
        aski_yari = S["kabin_kasnak_genislik"] / 2.0
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(_dik("KASNAK", merkez - dc / 2.0, aski_y - aski_yari, dc, 2 * aski_yari))
            e.append(_yazi(merkez, aski_y + aski_yari + 45, f"ø {dc:g}", 45))
        e.append(_yazi(kx, aski_y - aski_yari - 230,
                       f"ASKI:  {duzen.upper()}  ·  2:1", 44))
    elif duzen == "Doğrudan":
        aralik = aski["nokta_arasi"]
        aski_yari = 45.0
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(_daire("KASNAK", merkez, aski_y, 45))
            e.append(_cizgi("KASNAK", merkez - 70, aski_y, merkez + 70, aski_y))
            e.append(_cizgi("KASNAK", merkez, aski_y - 70, merkez, aski_y + 70))
        e.append(_yazi(kx, aski_y - aski_yari - 230, "ASKI:  DOĞRUDAN  ·  1:1", 44))

    #  ── KARŞI AĞIRLIK:  çerçeve · dolgu · kasnak · raylar ────────────
    cer = S["agirlik_cerceve"]
    if ag_yan:
        sol = ag_yan == "Sol"
        ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]         # ağırlık ekseni
        ax, ay = ex - ag["derinlik"] / 2.0, ry - ag["genislik"] / 2.0
        e.append(_dik("AGIRLIK", ax, ay, ag["derinlik"], ag["genislik"]))
        e.append(_dik("AGIRLIK", ax + cer, ay + cer,
                      ag["derinlik"] - 2 * cer, ag["genislik"] - 2 * cer))
        #  Kabin rayının ara kirişi bu konsollara bağlanır:  kol plakadan
        #  kirişe uzanır  ( ağırlığın boyunun DIŞINDAN geçer ).
        kiris_ic = (sol_yuz - kr["h"] - S["ara_kiris_en"]) if sol else (sag_yuz + kr["h"]
                                                                        + S["ara_kiris_en"])
        for yuz, y_yon in ((ry + ag["ray_arasi"] / 2.0, +1), (ry - ag["ray_arasi"] / 2.0, -1)):
            e += _ray_dusey(yuz, ex, ag["b"], ag["h"], y_yon)
            duvar_x = 0 if sol else G
            plaka_x = duvar_x if sol else duvar_x - S["konsol_agirlik_en"]
            ray_arkasi = yuz + ag["h"] * y_yon
            e.append(_dik("KONSOL", plaka_x, ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
                          S["konsol_agirlik_en"], S["konsol_agirlik_boy"], ad="plaka"))
            for cx in (plaka_x + S["konsol_agirlik_en"] / 2.0 - S["konsol_civata_araligi"],
                       plaka_x + S["konsol_agirlik_en"] / 2.0 + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", cx, ray_arkasi, S["konsol_civata_capi"] / 2.0))
            kol_bas = plaka_x + S["konsol_agirlik_en"] if sol else kiris_ic
            kol_son = kiris_ic if sol else plaka_x
            if kol_son - kol_bas > 1:
                e.append(_dik("KONSOL", kol_bas, ray_arkasi - S["konsol_agirlik_boy"] / 6.0,
                              kol_son - kol_bas, S["konsol_agirlik_boy"] / 3.0, ad="kol"))
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(_dik("KASNAK", ex - ag["derinlik"] / 2.0 + cer, ry - dc / 2.0,
                          ag["derinlik"] - 2 * cer, dc))
            e.append(_yazi(ex, ry, f"ø {dc:g}", 40, aci=90))
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
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(_dik("KASNAK", ex - dc / 2.0, ey - ag["derinlik"] / 2.0 + cer,
                          dc, ag["derinlik"] - 2 * cer))
            e.append(_yazi(ex, ey, f"ø {dc:g}", 40))

    #  ── KUMANDA PANOSU ───────────────────────────────────────────────
    #  Karşı ağırlık aynı duvardaysa pano karşı duvara geçer:  ağırlık kuyu
    #  boyunca o duvarın önünden geçer, pano yolunu keserdi.
    pano_duvar = S["pano_duvar"]
    if pano_duvar == ag_yan:
        pano_duvar = "Sol" if pano_duvar == "Sağ" else "Sağ"
    if pano_duvar in ("Sağ", "Sol"):
        px = (G - S["pano_derinlik"]) if pano_duvar == "Sağ" else 0
        e.append(_dik("PANO", px, kb["on_pay"] + 200, S["pano_derinlik"], S["pano_en"]))
        e.append(_yazi(px + S["pano_derinlik"] / 2.0,
                       kb["on_pay"] + 200 + S["pano_en"] / 2.0, "PANO", 42))

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    #  Uzatma çizgisi yoktur:  ölçü, ölçtüğü noktaların hizasında durur.
    #  PLANIN DIŞINDAKİ SIRALAR yalnız kuyu sınırı boyunca okunabilen
    #  ölçüleri taşır;  bir iç parçayı ( askı, eşik ) ölçen ölçü parçanın
    #  yanına, planın İÇİNE konur — dışarıda neyi ölçtüğü görünmüyordu.
    #  Her sıra ( aynı kot ) bir zincirdir ve toplama kapanır.
    ic_sol = kx - dis_g / 2.0 - S["sase_dikme"]
    ic_sag = kx + dis_g / 2.0 + S["sase_dikme"]
    ARA = 200.0                                     # sıralar arası

    #  ÜST — kuyu genişliği boyunca
    u = [D + dar + 120 + i * ARA for i in range(5)]
    e += [
        _olcu("yatay", (-ds, 0), (0, 0), u[0], f"DUVAR {ds:g}"),
        _olcu("yatay", (0, 0), (G, 0), u[0], f"KUYU GENİŞLİĞİ {G:g}"),
        _olcu("yatay", (G, 0), (G + dg, 0), u[0], f"DUVAR {dg:g}"),
        _olcu("yatay", (-ds, 0), (G + dg, 0), u[1], f"DIŞ ÖLÇÜ {G + ds + dg:g}"),
        _olcu("yatay", (0, 0), (sol_yuz - kr["h"], 0), u[2]),
        _olcu("yatay", (sol_yuz - kr["h"], 0), (sol_yuz, 0), u[2], f"RAY {kr['h']:g}"),
        _olcu("yatay", (sol_yuz, 0), (sag_yuz, 0), u[2], f"DBG {kr['arasi']:g}"),
        _olcu("yatay", (sag_yuz, 0), (sag_yuz + kr["h"], 0), u[2], f"RAY {kr['h']:g}"),
        _olcu("yatay", (sag_yuz + kr["h"], 0), (G, 0), u[2]),
        _olcu("yatay", (0, 0), (ic_sol, 0), u[3]),
        _olcu("yatay", (ic_sol, 0), (ic_sag, 0), u[3], f"ŞASE DIŞI {ic_sag - ic_sol:g}"),
        _olcu("yatay", (ic_sag, 0), (G, 0), u[3]),
    ]
    if not ag_yan:
        #  Arkadaki ağırlığın rayları kuyu genişliği boyunca ölçülür
        e += [
            _olcu("yatay", (0, 0), (ex - ag["ray_arasi"] / 2.0, 0), u[4]),
            _olcu("yatay", (ex - ag["ray_arasi"] / 2.0, 0), (ex + ag["ray_arasi"] / 2.0, 0),
                  u[4], f"DBGW {ag['ray_arasi']:g}"),
            _olcu("yatay", (ex + ag["ray_arasi"] / 2.0, 0), (G, 0), u[4]),
        ]

    #  ALT — kapı zinciri, kuyu genişliği, kabin ve ağırlık eksenleri
    a1, a2, a3 = (-don - S["bina_duvari"] - 120, -don - S["bina_duvari"] - 320,
                  -don - S["bina_duvari"] - 520)
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
    noktalar = sorted(set([0.0, kx, G] + ([ex] if ag_yan else [])))
    for sol_n, sag_n in zip(noktalar, noktalar[1:]):
        metin = None
        if ((ag_yan == "Sol" and sol_n == 0 and sag_n == ex)
                or (ag_yan == "Sağ" and sol_n == ex and sag_n == G)):
            metin = f"AĞIRLIK RAYI {sag_n - sol_n:g}"
        e.append(_olcu("yatay", (sol_n, 0), (sag_n, 0), a3, metin))

    #  YANLAR — kuyu derinliği boyunca.  Sıra listesi duvardan dışarı
    #  doğrudur;  ağırlık yandaysa kendi zinciri O YANDA, duvara en yakın
    #  sırada durur  ( konsol kotları ağırlığın yanında okunur ).
    def _agirlik_zinciri(kot):
        return [
            _olcu("dusey", (0, 0), (0, ag_alt), kot),
            _olcu("dusey", (0, ag_alt), (0, ag_alt + ag["h"]), kot, f"{ag['h']:g}"),
            _olcu("dusey", (0, ag_alt + ag["h"]), (0, ag_ust - ag["h"]), kot,
                  f"DBGW {ag['ray_arasi']:g}"),
            _olcu("dusey", (0, ag_ust - ag["h"]), (0, ag_ust), kot, f"{ag['h']:g}"),
            _olcu("dusey", (0, ag_ust), (0, D), kot),
        ]

    def _civata(kot):
        #  Kabin rayı konsolunun cıvata aralığı — duvara dayanan konsolda
        c = S["konsol_civata_araligi"]
        return [_olcu("dusey", (0, ry - c), (0, ry), kot, f"CIVATA {c:g}"),
                _olcu("dusey", (0, ry), (0, ry + c), kot, f"{c:g}")]

    sol_siralar = []
    sag_siralar = []
    if ag_yan == "Sol":
        sol_siralar.append(_agirlik_zinciri)
    elif ag_yan == "Sağ":
        sag_siralar.append(_agirlik_zinciri)
    (sol_siralar if ag_yan == "Sağ" else sag_siralar).insert(0, _civata)
    sol_siralar += [
        lambda kot: [_olcu("dusey", (0, 0), (0, ry), kot, f"RAY EKSENİ {ry:g}"),
                     _olcu("dusey", (0, ry), (0, D), kot)],
        lambda kot: [_olcu("dusey", (0, -don), (0, D + dar), kot,
                           f"DIŞ ÖLÇÜ {D + don + dar:g}")],
    ]
    sag_siralar += [
        lambda kot: [_olcu("dusey", (0, 0), (0, D), kot, f"KUYU DERİNLİĞİ {D:g}")],
        lambda kot: [_olcu("dusey", (0, ic_on), (0, ic_on + kb["derinlik"]), kot,
                           f"KABİN {kb['derinlik']:g}")],
        lambda kot: [_olcu("dusey", (0, 0), (0, ic_on), kot, f"KAPI ARASI {ic_on:g}"),
                     _olcu("dusey", (0, ic_on), (0, ic_on + dis_d), kot,
                           f"KABİN + ŞASE {dis_d:g}"),
                     _olcu("dusey", (0, ic_on + dis_d), (0, D), kot)],
    ]
    for i, sira in enumerate(sol_siralar):
        e += sira(-ds - 120 - i * ARA)
    for i, sira in enumerate(sag_siralar):
        e += sira(G + dg + 120 + i * ARA)

    #  İÇ — kabin iç genişliği ve kabin – ray boşlukları  ( kabinin arkasında;
    #  ağırlık arkadaysa o şerit dolu olduğu için kabinin içinde, önde )
    kab_kot = ic_on + dis_d + 90 if ag_yan else ic_on + 150
    e += [
        _olcu("yatay", (0, 0), (ic_sol, 0), kab_kot),
        _olcu("yatay", (ic_sol, 0), (kx - kb["genislik"] / 2.0, 0), kab_kot),
        _olcu("yatay", (kx - kb["genislik"] / 2.0, 0), (kx + kb["genislik"] / 2.0, 0), kab_kot,
              f"KABİN İÇİ {kb['genislik']:g}"),
        _olcu("yatay", (kx + kb["genislik"] / 2.0, 0), (ic_sag, 0), kab_kot),
        _olcu("yatay", (ic_sag, 0), (G, 0), kab_kot),
    ]

    #  İÇ — EŞİKLER  ( kat eşiği · aradaki açıklık · kabin eşiği ).  Kapının
    #  yanındaki boş şeritte, kuyu ön duvarı ile kabin arasında durur;  yazılar
    #  yatay ve ölçünün dışındadır ( parçalar 30 – 60 mm, yazı sığmaz ).
    esik = [(0.0, S["esik_derinlik"], f"KAT EŞİĞİ {S['esik_derinlik']:g}"),
            (S["esik_derinlik"], ic_on - S["kabin_esik_derinlik"], None),
            (ic_on - S["kabin_esik_derinlik"], ic_on,
             f"KABİN EŞİĞİ {S['kabin_esik_derinlik']:g}")]
    h_esik = 40.0
    sol_bos = min(ic_sol, x0)                  # kapının solundaki boş şerit
    sag_bos = G - max(ic_sag, x0 + kg)
    if sol_bos >= sag_bos:
        esik_x, yan = sol_bos - 40.0, -1
    else:
        esik_x, yan = G - sag_bos + 40.0, +1
    onceki = -1e9
    for bas, son, metin in esik:
        metin = metin or f"{son - bas:g}"
        cy = max((bas + son) / 2.0, onceki + h_esik + 6)
        onceki = cy
        w = _yazi_eni(metin, h_esik)
        e.append(_olcu("dusey", (0, bas), (0, son), esik_x, metin,
                       yazi={"x": esik_x + yan * (30 + w / 2.0), "y": cy, "aci": 0,
                             "h": h_esik}))

    #  İÇ — ASKI:  kasnak / nokta aralığı askı elemanlarının hemen yanında,
    #  kaçıklık ise kabin merkezi ile askı ekseni arasında
    if duzen in ("Kabin altı", "Kabin üstü", "Doğrudan"):
        aralik = aski.get("kasnak_arasi") if duzen != "Doğrudan" else aski.get("nokta_arasi")
        e.append(_olcu("yatay", (kx - aralik / 2.0, 0), (kx + aralik / 2.0, 0),
                       aski_y - aski_yari - 70, f"ASKI ARASI {aralik:g}",
                       yazi={"x": kx, "y": aski_y - aski_yari - 70 + 50, "aci": 0}))
        kac = aski_y - (ic_on + dis_d / 2.0)
        if abs(kac) > 1e-9:
            kac_x = kx - kb["genislik"] / 2.0 + 150
            metin = f"ASKI KAÇIKLIĞI {abs(kac):g}"
            e.append(_olcu("dusey", (0, aski_y), (0, ic_on + dis_d / 2.0), kac_x, metin,
                           yazi={"x": kac_x + 30 + _yazi_eni(metin) / 2.0,
                                 "y": (aski_y + ic_on + dis_d / 2.0) / 2.0, "aci": 0}))

    #  ── YAZILAR ──────────────────────────────────────────────────────
    e.append(_dik("KABIN", x0, ic_on - S["kabin_esik_derinlik"], kg, S["kabin_esik_derinlik"]))
    #  Askı noktaları kabin ortasına yakınsa kabin yazısı arkaya kayar.
    kabin_yazi_y = ky if abs(aski_y - ky) >= 150 else ky + 200
    e.append(_yazi(kx, kabin_yazi_y, f"KABİN  {kb['genislik']:g} x {kb['derinlik']:g}", 55))
    #  Ölçü zincirlerinin sıfır noktaları  ( ELEport'ta da "0" yazar )
    for zx in (0, G):
        e.append(_yazi(zx, -don - S["bina_duvari"] - 420, "0", 45))
    if ag_yan:
        #  Blok dar ve uzun:  yazı DİK yazılır.  Kasnak bloğun ortasında
        #  durduğu için yazı blok ile kabin rayı arasındaki boşluğa konur;
        #  boşluk dar ise bloğun içine.
        blok_ic = ex + ag["derinlik"] / 2.0 if ag_yan == "Sol" else ex - ag["derinlik"] / 2.0
        bos = abs(kiris_ic - blok_ic)
        yx = (blok_ic + kiris_ic) / 2.0 if bos >= 60 else ex
        e.append(_yazi(yx, ry, "KARŞI AĞIRLIK", 40, aci=90))
    else:
        e.append(_yazi(ex, ey - ag["derinlik"] / 2.0 - 45, "KARŞI AĞIRLIK", 40))
    _yazilari_yerlestir(e)
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
            y_ = el.get("yazi")
            if y_:
                #  Yazı da çerçevenin içinde kalmalı  ( "ASKI KAÇIKLIĞI"
                #  çerçeveye taşıp kesiliyordu ).
                w, h = _yazi_eni(el["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                if y_["aci"]:
                    w, h = h, w
                xs += [y_["x"] - w, y_["x"] + w]; ys += [y_["y"] - h, y_["y"] + h]
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
