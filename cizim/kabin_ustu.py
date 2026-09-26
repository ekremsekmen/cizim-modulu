# -*- coding: utf-8 -*-
"""
KABİN ÜSTÜ PLANI  ( kabin tavanı hizasından yatay kesit )

Kuyu planının duvarlarını, raylarını, konsollarını ve karşı ağırlığını AYNEN
kullanır:  yerleşim ikinci kez hesaplanmaz, plan() elemanlarından okunur —
iki çizim ayrışamaz.  Üstüne kabin tavanında olanlar gelir:

  · kabin tavanı ve şase dikmeleri
  · kapı operatörü  ( tavanın kapı kenarında )
  · askı:  kabin üstü askıda kasnaklar tavanda;  kabin altı askıda halatlar
    tavanın dışından geçer;  doğrudan askıda askı noktaları tavandadır
  · KORKULUK            TS EN 81-20 m.5.4.7.2 b ve m.5.4.7.4
  · SIĞINMA ALANI       TS EN 81-20 m.5.2.5.7.1 · Çizelge 3

Kat kapısı bu kesitte görünmez:  kesit kapı lentosunun üstünden geçer, ön
duvar dolu çizilir.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import sabitler as CS

#  TS EN 81-20 Çizelge 3 — kabin üstü sığınma alanının yatay ölçüleri ( mm ).
#  Adlar hesap programının "Kabin üstü sığınma hacmi tipi" seçenekleriyle
#  aynıdır;  köprü değeri olduğu gibi taşır.
SIGINMA = {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0)}

#  TS EN 81-20 m.5.4.7.2 b:  tavan kenarından kuyu duvarına yatay boşluk
#  0,30 m'yi AŞARSA korkuluk gerekir.
KORKULUK_BOSLUK = 300.0
#  m.5.4.7.4 c:  korkuluk tavan kenarından en çok 0,15 m içeride durur.
KORKULUK_KENAR_AZAMI = 150.0
#  m.5.4.7.4 d:  küpeştenin dış kenarı kuyudaki parçalardan ( karşı ağırlık,
#  raylar, konsollar … ) en az 0,10 m uzakta olmalıdır.
KORKULUK_PARCA_ASGARI = 100.0
#  m.5.4.7.4 b:  küpeştenin iç kenarından duvara boşluk 0,50 m'ye kadar ise
#  yükseklik en az 0,70 m, aşarsa en az 1,10 m.
KORKULUK_YUKSEKLIK_SINIRI = 500.0
KORKULUK_ALCAK, KORKULUK_YUKSEK = 700.0, 1100.0

#  Kuyuda duran ( kabinle birlikte gitmeyen ) parçaların katmanları
_KUYU_PARCALARI = ("RAY", "KONSOL", "AGIRLIK", "PANO")
#  Kuyu planından alınan katmanlar ve adlar
_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA",
                   "PATEN", "AGIRLIK", "PANO", "EKSEN")
_PLANDAN_AD = ("agirlik_kasnak", "agirlik_kasnak_yazi", "agirlik_yazi", "pano_yazi",
               "sase_dikme")


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _operator(g, tavan, S):
    """Kapı operatörünün tavandaki izi.  Kanatlar açılınca operatörün kirişi
    boyunca kayar:  merkezi kapıda her yana yarım kapı, teleskopikte açılış
    yanına bir kanat eni ( kapının yarısı ) kadar taşar.  Derinliği kabin
    kapısı mekanizma kutusunun derinliğidir ( sabitler )."""
    kp = g["kapi"]
    x0, kg = kp["sol_pay"], kp["genislik"]
    tip = str(kp.get("tip", ""))
    if tip.startswith("Teleskopik"):
        x1, x2 = (x0, x0 + 1.5 * kg) if tip.endswith("Sağ") else (x0 - 0.5 * kg, x0 + kg)
    else:
        x1, x2 = x0 - 0.5 * kg, x0 + 1.5 * kg
    x1, x2 = max(x1, tavan[0]), min(x2, tavan[2])
    return (x1, tavan[1], x2, tavan[1] + S["kabin_kapisi_kutu_boy"])


def yerlesim(g, cizim_sabitleri=None):
    """Kabin üstünün yerleşimi — çizim de doğrulama da bunu kullanır.

    Dönen:  { taban ( plan elemanları ), tavan, kenarlar, operator, engeller,
              siginma ( kutu ya da None ), hata [ … ] }
    """
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    taban = CGE.plan(g, S)
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    tavan = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    parcalar = [_kutu(el) for el in taban
                if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI]
    hata = []

    #  ── KORKULUK:  her kenar ayrı değerlendirilir ─────────────────────
    #  bos:     tavan kenarından duvara  ( m.5.4.7.2 b )
    #  parca:   tavan kenarından o yandaki en yakın kuyu parçasına
    kenarlar = {}
    for yan in ("Sol", "Sağ", "Arka", "Ön"):
        if yan == "Sol":
            bos = tavan[0]
            yakin = [tavan[0] - p[2] for p in parcalar
                     if p[2] <= tavan[0] + 1e-9 and p[1] < tavan[3] and tavan[1] < p[3]]
        elif yan == "Sağ":
            bos = G - tavan[2]
            yakin = [p[0] - tavan[2] for p in parcalar
                     if p[0] >= tavan[2] - 1e-9 and p[1] < tavan[3] and tavan[1] < p[3]]
        elif yan == "Arka":
            bos = D - tavan[3]
            yakin = [p[1] - tavan[3] for p in parcalar
                     if p[1] >= tavan[3] - 1e-9 and p[0] < tavan[2] and tavan[0] < p[2]]
        else:
            bos = tavan[1]
            yakin = [tavan[1] - p[3] for p in parcalar
                     if p[3] <= tavan[1] + 1e-9 and p[0] < tavan[2] and tavan[0] < p[2]]
        k = {"bos": bos, "gerekli": bos > KORKULUK_BOSLUK, "iceri": 0.0,
             "parca": min(yakin) if yakin else None, "yukseklik": None}
        if k["gerekli"]:
            #  Küpeşte parçalardan 0,10 m uzak durmalı:  gerekirse içeri alınır
            k["iceri"] = max(0.0, KORKULUK_PARCA_ASGARI - (k["parca"] if yakin else 1e9))
            if k["iceri"] > KORKULUK_KENAR_AZAMI:
                hata.append(
                    f"{yan} kenarda korkuluk kuyudaki parçalara {KORKULUK_PARCA_ASGARI:g} mm "
                    f"uzak durmak için {k['iceri']:g} mm içeri alınmalı;  TS EN 81-20 "
                    f"m.5.4.7.4 c en çok {KORKULUK_KENAR_AZAMI:g} mm verir.")
            k["yukseklik"] = (KORKULUK_ALCAK if bos + k["iceri"] <= KORKULUK_YUKSEKLIK_SINIRI
                              else KORKULUK_YUKSEK)
        kenarlar[yan] = k

    #  HALAT KUYUDAKİ BİR PARÇANIN İÇİNDEN GEÇEMEZ  ( kabin altı askı )
    halatlar = CGE.halat_konumlari(g, S)
    for hx, hy in halatlar:
        if not (0 < hx < G):
            hata.append(f"Halat kuyunun dışına düşüyor ( x = {hx:g} ) — kasnak aralığını gözden geçirin.")
            continue
        for el in taban:
            if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI:
                p = _kutu(el)
                if p[0] - 20 < hx < p[2] + 20 and p[1] - 20 < hy < p[3] + 20:
                    hata.append(f"Halat ( x = {hx:g}, y = {hy:g} ) kuyudaki bir parçanın "
                                f"( {el['katman'].lower()} ) içinden geçiyor.")
                    break

    #  Sığınma alanı korkulukların içinde kalır
    ic = (tavan[0] + kenarlar["Sol"]["iceri"], tavan[1] + kenarlar["Ön"]["iceri"],
          tavan[2] - kenarlar["Sağ"]["iceri"], tavan[3] - kenarlar["Arka"]["iceri"])

    #  ── TAVANDAKİ ENGELLER ───────────────────────────────────────────
    operator = _operator(g, tavan, S)
    engeller = [operator]
    duzen = (g.get("aski") or {}).get("duzen")
    if duzen == "Kabin üstü":
        engeller += [_kutu(el) for el in taban if el.get("ad") == "kabin_kasnak"]
    elif duzen == "Doğrudan":
        for el in taban:
            if el.get("ad") == "aski_nokta" and el["tip"] == "daire":
                engeller.append((el["x"] - 70, el["y"] - 70, el["x"] + 70, el["y"] + 70))

    #  Kabin üstü kasnağı korkuluğun yolunu kesemez
    for yan, k in kenarlar.items():
        if not k["gerekli"] or duzen != "Kabin üstü":
            continue
        for p in engeller[1:]:
            if yan in ("Sol", "Sağ"):
                x = ic[0] if yan == "Sol" else ic[2]
                kesiyor = p[0] < x < p[2] and p[1] < ic[3] and ic[1] < p[3]
            else:
                y = ic[3] if yan == "Arka" else ic[1]
                kesiyor = p[1] < y < p[3] and p[0] < ic[2] and ic[0] < p[2]
            if kesiyor:
                hata.append(f"Kabin üstü kasnağı {yan.lower()} kenardaki korkuluğun yolunu "
                            "kesiyor — kasnak aralığını daraltın.")
                break

    #  ── SIĞINMA ALANI  ( Çizelge 3 ) ──────────────────────────────────
    #  Kapıya en yakın, sonra kabin eksenine en yakın boş yer aranır:  bakımcı
    #  tavana kapıdan çıkar.
    tip = (g.get("kabin_ustu") or {}).get("siginma_tipi")
    siginma = None
    if tip not in SIGINMA:
        hata.append(f"kabin_ustu.siginma_tipi: {tuple(SIGINMA)} içinden olmalı ( {tip!r} ).")
    else:
        kx = (tavan[0] + tavan[2]) / 2.0
        adaylar = []
        for w, h in {SIGINMA[tip], SIGINMA[tip][::-1]}:
            y = ic[1]
            while y + h <= ic[3] + 1e-9:
                x = ic[0]
                while x + w <= ic[2] + 1e-9:
                    kutu = (x, y, x + w, y + h)
                    if not any(_ortusur(kutu, e) for e in engeller):
                        adaylar.append((round(y, 3), abs(x + w / 2.0 - kx), kutu))
                    x += 25.0
                y += 25.0
        if adaylar:
            siginma = min(adaylar)[2]
        else:
            a, b = SIGINMA[tip]
            hata.append(f"Kabin tavanında {tip.lower()} tipi sığınma alanına ( {a:g} × {b:g} mm, "
                        "TS EN 81-20 Çizelge 3 ) yer yok — korkulukların içinde, kapı "
                        "operatörü ve askı elemanları dışında kalmalı.")
    return {"taban": taban, "tavan": tavan, "kenarlar": kenarlar, "ic": ic,
            "operator": operator, "engeller": engeller, "siginma": siginma,
            "siginma_tipi": tip, "halatlar": halatlar, "hata": hata, "S": S}


def dogrula(g):
    """Kuyu planının doğrulaması + kabin üstünün kendi kuralları."""
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    """Kabin üstü planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    S, tavan, ken = Y["S"], Y["tavan"], Y["kenarlar"]
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    dg, dar = g["kuyu"]["duvar_sag"], g["kuyu"]["duvar_arka"]
    duzen = (g.get("aski") or {}).get("duzen")
    ad_sec = _PLANDAN_AD + (("kabin_kasnak", "kabin_kasnak_yazi") if duzen == "Kabin üstü"
                            else ("aski_nokta",) if duzen == "Doğrudan" else ())
    e = [el for el in Y["taban"]
         if el.get("ad") in ad_sec
         or (el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi" and not el.get("ad", "").startswith(
             ("kabin", "aski", "sase")))]

    #  ── KABİN TAVANI ─────────────────────────────────────────────────
    tg, td = tavan[2] - tavan[0], tavan[3] - tavan[1]
    e.append(CGE._ad(CGE._dik("KABIN", tavan[0], tavan[1], tg, td), "tavan"))
    kx, ky = (tavan[0] + tavan[2]) / 2.0, (tavan[1] + tavan[3]) / 2.0

    #  Kapı operatörü
    op = Y["operator"]
    e.append(CGE._ad(CGE._dik("KAPI", op[0], op[1], op[2] - op[0], op[3] - op[1]), "operator"))
    e.append(CGE._yazi((op[0] + op[2]) / 2.0, (op[1] + op[3]) / 2.0, "KAPI OPERATÖRÜ", 40))

    #  Kabin altı askıda halatlar tavanın DIŞINDAN, kasnakların dış
    #  teğetinden yukarı çıkar
    for hx, hy in Y["halatlar"]:
        e.append(CGE._ad(CGE._daire("KASNAK", hx, hy, 20), "halat"))
        e.append(CGE._yazi(hx, hy - 70, "HALAT", 36))

    #  ── KORKULUK ─────────────────────────────────────────────────────
    #  Küpeşte çizgisi, gerekli olan her kenarda iceri kadar içeride durur.
    ic = Y["ic"]
    for yan, k in ken.items():
        if not k["gerekli"]:
            continue
        if yan in ("Sol", "Sağ"):
            x = ic[0] if yan == "Sol" else ic[2]
            e.append(CGE._ad(CGE._cizgi("KORKULUK", x, ic[1], x, ic[3]), "korkuluk"))
        else:
            y = ic[3] if yan == "Arka" else ic[1]
            e.append(CGE._ad(CGE._cizgi("KORKULUK", ic[0], y, ic[2], y), "korkuluk"))

    #  ── SIĞINMA ALANI ────────────────────────────────────────────────
    sg = Y["siginma"]
    if sg:
        e.append(CGE._ad(CGE._dik("SIGINMA", sg[0], sg[1], sg[2] - sg[0], sg[3] - sg[1]),
                         "siginma"))
        a, b = SIGINMA[Y["siginma_tipi"]]
        cx, cy = (sg[0] + sg[2]) / 2.0, (sg[1] + sg[3]) / 2.0
        e.append(CGE._yazi(cx, cy + 35, "SIĞINMA ALANI", 38))
        e.append(CGE._yazi(cx, cy - 35, f"{Y['siginma_tipi'].upper()}  {a:g} x {b:g}", 34))

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    O = CGE._olcu
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    e += [
        O("yatay", (0, 0), (tavan[0], 0), u0),
        O("yatay", (tavan[0], 0), (tavan[2], 0), u0, f"KABİN TAVANI {tg:g}"),
        O("yatay", (tavan[2], 0), (G, 0), u0),
        O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"),
        O("dusey", (0, 0), (0, tavan[1]), s0),
        O("dusey", (0, tavan[1]), (0, tavan[3]), s0, f"KABİN TAVANI {td:g}"),
        O("dusey", (0, tavan[3]), (0, D), s0),
        O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"),
    ]
    #  Korkuluğun kenardan içeri alınması  ( 0'dan büyükse )
    for yan, k in ken.items():
        if not (k["gerekli"] and k["iceri"] > 1e-9):
            continue
        if yan in ("Sol", "Sağ"):
            x1, x2 = (tavan[0], ic[0]) if yan == "Sol" else (ic[2], tavan[2])
            #  Her kenarın ölçüsü kendi sırasında  ( iki kenar aynı sırada
            #  kopuk bir zincir oluştururdu )
            kot = tavan[3] - (120 if yan == "Sol" else 200)
            e.append(O("yatay", (x1, 0), (x2, 0), kot, f"{k['iceri']:g}",
                       yazi={"x": (x2 + 30 + CGE._yazi_eni(f"{k['iceri']:g}", 40) / 2.0)
                             if yan == "Sol" else (x1 - 30 - CGE._yazi_eni(f"{k['iceri']:g}", 40) / 2.0),
                             "y": kot, "h": 40}))
        else:
            y1, y2 = (ic[3], tavan[3]) if yan == "Arka" else (tavan[1], ic[1])
            kot = tavan[0] + (120 if yan == "Arka" else 200)
            e.append(O("dusey", (0, y1), (0, y2), kot, f"{k['iceri']:g}",
                       yazi={"x": kot + 30 + CGE._yazi_eni(f"{k['iceri']:g}", 40) / 2.0,
                             "y": (y1 + y2) / 2.0, "h": 40}))
    #  Sığınma alanının yeri — tavan kenarlarından
    if sg:
        kot_y = sg[3] + 90 if sg[3] + 200 < tavan[3] else sg[1] - 90
        kot_x = sg[2] + 90 if sg[2] + 200 < tavan[2] else sg[0] - 90
        e += [
            O("yatay", (tavan[0], 0), (sg[0], 0), kot_y),
            O("yatay", (sg[0], 0), (sg[2], 0), kot_y),
            O("yatay", (sg[2], 0), (tavan[2], 0), kot_y),
            O("dusey", (0, tavan[1]), (0, sg[1]), kot_x),
            O("dusey", (0, sg[1]), (0, sg[3]), kot_x),
            O("dusey", (0, sg[3]), (0, tavan[3]), kot_x),
        ]
    #  KORKULUK YAZISI:  küpeşte boyunca, operatöre ve sığınma ölçüsüne
    #  denk gelmeyen en uzun boş parçanın ortasına
    for yan, k in ken.items():
        if not k["gerekli"]:
            continue
        metin = f"KORKULUK  h = {k['yukseklik']:g}"
        dikey = yan in ("Sol", "Sağ")
        bas, son = (ic[1], ic[3]) if dikey else (ic[0], ic[2])
        cizgi = (ic[0] if yan == "Sol" else ic[2]) if dikey else (ic[3] if yan == "Arka" else ic[1])
        dolu = []
        if dikey and op[0] <= cizgi <= op[2]:
            dolu.append((op[1], op[3]))
        if not dikey and op[1] <= cizgi <= op[3]:
            dolu.append((op[0], op[2]))
        for el in e:
            if el["tip"] == "olcu" and el["yon"] == ("yatay" if dikey else "dusey"):
                i = 0 if dikey else 1
                if min(el["a"][i], el["b"][i]) <= cizgi + 60 and cizgi - 60 <= max(el["a"][i], el["b"][i]):
                    dolu.append((el["kot"] - 70, el["kot"] + 110))
        parcalar, a = [], bas
        for d1, d2 in sorted(dolu):
            if d1 > a:
                parcalar.append((a, min(d1, son)))
            a = max(a, d2)
        if a < son:
            parcalar.append((a, son))
        p1, p2 = max(parcalar or [(bas, son)], key=lambda t: t[1] - t[0])
        orta = (p1 + p2) / 2.0
        if dikey:
            e.append(CGE._yazi(cizgi + (60 if yan == "Sol" else -60), orta, metin, 40, aci=90))
        else:
            e.append(CGE._yazi(orta, cizgi + (-60 if yan == "Arka" else 60), metin, 40))

    #  Sıfır boylu ölçü çizilmez  ( sığınma alanı kenara dayanmışsa )
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e
