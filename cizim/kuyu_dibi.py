# -*- coding: utf-8 -*-
"""
KUYU DİBİ PLANI  ( kuyu tabanından yatay kesit )

Kuyu planının duvarlarını, raylarını ve konsollarını AYNEN kullanır:  yerleşim
ikinci kez hesaplanmaz, plan() elemanlarından okunur.  Kabin ve karşı ağırlık
bu kesitte yoktur ( kabin en altta iken bile kesit tamponların hizasından
geçer );  kabinin izi ve kat kapısı yalnız KESİK çizgiyle, yer göstermek için
çizilir.  Üstüne kuyu dibinde olanlar gelir:

  · kabin ve karşı ağırlık tamponları                 m.5.8.1.1
  · karşı ağırlık perdesi                             m.5.2.5.5.1
  · regülatör gergi kasnağı
  · SIĞINMA ALANI                                     m.5.2.5.8.1 · Çizelge 4
  · MERDİVEN  ( kuyu dibi 2,5 m'yi aşmıyorsa )         m.5.2.2.4 · Ek F
  · kuyu tabanına yük aktaran noktalar:  FKR ( kabin rayı ) · Fkt ( kabin
    tamponu ) · FAR ( ağırlık rayı ) · Fat ( ağırlık tamponu ) — adlar hesap
    paftasının "kuyu tabanına gelen yükler" bölümüyle aynıdır;  değerleri
    köprü kurulunca o bölümden gelir.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import sabitler as CS

#  TS EN 81-20 Çizelge 4 — kuyu dibi sığınma alanının yatay ölçüleri ( mm ).
#  Adlar hesap programının "Kuyu dibi sığınma hacmi tipi" seçenekleriyle aynı.
SIGINMA = {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0), "Yatarak": (700.0, 1000.0)}
#  m.5.2.2.4:  kuyu dibi 2,50 m'yi aşarsa erişim kapısı gerekir;  aşmıyorsa
#  kuyu içinde merdiven yeterlidir.
MERDIVEN_AZAMI_DERINLIK = 2500.0
#  Ek F.5 b:  saklanan merdiven ile kat girişinin kenarı arası en çok 800 mm.
MERDIVEN_KAPI_AZAMI = 800.0
TAMPON_ADETLERI = (1, 2)
YANLAR = ("Sağ", "Sol")

_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "EKSEN")


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _ortusur(a, b, pay=0.0):
    return a[0] < b[2] + pay and b[0] < a[2] + pay and a[1] < b[3] + pay and b[1] < a[3] + pay


def _birlesim(kutular):
    return (min(k[0] for k in kutular), min(k[1] for k in kutular),
            max(k[2] for k in kutular), max(k[3] for k in kutular))


def _raylar(taban, ad):
    """Aynı adlı ray parçalarını ( flanş + gövde ) raylara toplar."""
    parcalar = [_kutu(el) for el in taban if el.get("ad") == ad and el["tip"] == "dikdortgen"]
    raylar = []
    for p in parcalar:
        for r in raylar:
            if _ortusur(p, _birlesim(r), 1.0):
                r.append(p)
                break
        else:
            raylar.append([p])
    return sorted((_birlesim(r) for r in raylar), key=lambda k: (k[0], k[1]))


def _merkez(k):
    return ((k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0)


def yerlesim(g, cizim_sabitleri=None):
    """Kuyu dibinin yerleşimi — çizim de doğrulama da bunu kullanır."""
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    kd = g.get("kuyu_dibi") or {}
    hata = []
    for alan, secenek in (("siginma_tipi", tuple(SIGINMA)), ("regulator_yan", YANLAR)):
        if kd.get(alan) not in secenek:
            hata.append(f"kuyu_dibi.{alan}: {secenek} içinden olmalı ( {kd.get(alan)!r} ).")
    for alan in ("kabin_tampon_adedi", "agirlik_tampon_adedi"):
        if kd.get(alan) not in TAMPON_ADETLERI:
            hata.append(f"kuyu_dibi.{alan}: {TAMPON_ADETLERI} içinden olmalı ( {kd.get(alan)!r} ).")
    for alan in ("derinlik", "regulator_kaciklik", "regulator_kasnak_capi"):
        v = kd.get(alan)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or (alan != "regulator_kaciklik" and v <= 0):
            hata.append(f"kuyu_dibi.{alan}: sayı olmalı ( {v!r} ).")
    for adet, ara in (("kabin_tampon_adedi", "kabin_tampon_arasi"),
                      ("agirlik_tampon_adedi", "agirlik_tampon_arasi")):
        if kd.get(adet) == 2:
            v = kd.get(ara)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                hata.append(f"kuyu_dibi.{ara}: iki tamponda tamponlar arası girilmeli ( {v!r} ).")
    if hata:
        return {"hata": hata}

    taban = CGE.plan(g, S)
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    kabin = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = _kutu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
    kabin_raylari = _raylar(taban, "kabin_ray")
    agirlik_raylari = _raylar(taban, "agirlik_ray")
    konsollar = [_kutu(el) for el in taban if el["katman"] == "KONSOL" and el["tip"] == "dikdortgen"]
    ag_yan = g["agirlik"]["yeri"] if g["agirlik"]["yeri"] in ("Sağ", "Sol") else None
    ry = g["kabin_ray"]["kapi_arasi"]
    kx = (kabin[0] + kabin[2]) / 2.0

    #  ── TAMPONLAR ────────────────────────────────────────────────────
    #  Kabin tamponu kabin ekseninde, ray ekseni üstünde durur ( ELEport ve
    #  LiftDesigner paftaları ).  İki tamponda ray ekseni boyunca simetrik.
    #  Ağırlık tamponu ağırlığın ortasında;  iki tamponda ağırlığın boyu
    #  doğrultusunda simetrik.
    t = S["tampon_taban"] / 2.0

    def _tampon(cx, cy):
        return (cx - t, cy - t, cx + t, cy + t)

    if kd["kabin_tampon_adedi"] == 1:
        kabin_tamponlari = [_tampon(kx, ry)]
    else:
        a = kd["kabin_tampon_arasi"] / 2.0
        kabin_tamponlari = [_tampon(kx - a, ry), _tampon(kx + a, ry)]
    bx, by = _merkez(blok)
    if kd["agirlik_tampon_adedi"] == 1:
        agirlik_tamponlari = [_tampon(bx, by)]
    else:
        a = kd["agirlik_tampon_arasi"] / 2.0
        agirlik_tamponlari = ([_tampon(bx, by - a), _tampon(bx, by + a)] if ag_yan
                              else [_tampon(bx - a, by), _tampon(bx + a, by)])

    #  ── KARŞI AĞIRLIK PERDESİ  ( m.5.2.5.5.1 ) ───────────────────────
    #  Ağırlığın kuyuya bakan yüzünde, ağırlık rayları arasının tamamı
    #  boyunca ( d:  en az ağırlığın genişliği kadar ).  Ağırlık ile ona en
    #  yakın parça arasındaki boşluğun ortasından geçer.
    ar = _birlesim(agirlik_raylari)
    if ag_yan == "Sol":
        komsu = min([k[0] for k in konsollar + kabin_raylari if k[0] > blok[2]] + [kabin[0]])
        px = (blok[2] + komsu) / 2.0
        perde = (px, ar[1], px, ar[3])
    elif ag_yan == "Sağ":
        komsu = max([k[2] for k in konsollar + kabin_raylari if k[2] < blok[0]] + [kabin[2]])
        px = (blok[0] + komsu) / 2.0
        perde = (px, ar[1], px, ar[3])
    else:
        py = (blok[1] + kabin[3]) / 2.0
        perde = (ar[0], py, ar[2], py)

    #  ── REGÜLATÖR GERGİ KASNAĞI ──────────────────────────────────────
    #  Seçilen yandaki kabin rayının hizasında, ray ekseninin kaciklik kadar
    #  arkasında;  planda kasnak yandan görünür ( boyu çap, eni sabit ).
    ray = kabin_raylari[-1] if kd["regulator_yan"] == "Sağ" else kabin_raylari[0]
    gx, gy = _merkez(ray)[0], ry + kd["regulator_kaciklik"]
    dg_, eg = kd["regulator_kasnak_capi"] / 2.0, S["gergi_kasnak_eni"] / 2.0
    gergi = (gx - eg, gy - dg_, gx + eg, gy + dg_)

    #  ── MERDİVEN  ( m.5.2.2.4 · Ek F ) ───────────────────────────────
    #  Yan duvara yaslı saklanır, kapıya yakın yan seçilir.  Kuyu dibi
    #  2,5 m'yi aşıyorsa merdiven değil erişim kapısı gerekir — çizilmez.
    kp = g["kapi"]
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    sabit = konsollar + kabin_raylari + agirlik_raylari + [blok] + kabin_tamponlari + \
        agirlik_tamponlari + [gergi]
    merdiven = None
    if kd["derinlik"] <= MERDIVEN_AZAMI_DERINLIK:
        me, md = S["merdiven_eni"], S["merdiven_derinlik"]
        adaylar = []
        for yan, mx0, kenar in (("Sol", 0.0, x0), ("Sağ", G - md, x1)):
            y = 0.0
            while y + me <= D:
                k = (mx0, y, mx0 + md, y + me)
                if not any(_ortusur(k, p) for p in sabit):
                    #  Ek F.5 b:  kat girişinin kenarından merdivene
                    dx = max(0.0, k[0] - kenar, kenar - k[2])
                    uzak = (dx ** 2 + k[1] ** 2) ** 0.5
                    if uzak <= MERDIVEN_KAPI_AZAMI:
                        adaylar.append((uzak, y, yan, k))
                    break
                y += 25.0
        if adaylar:
            merdiven = min(adaylar)[3]
        else:
            hata.append("Kuyu dibi merdiveni kat girişine en çok 800 mm uzakta ( TS EN 81-20 "
                        "Ek F.5 b ) yan duvara yaslanamıyor — orada tampon, ray ya da konsol var.")

    #  ── ÇAKIŞMALAR ───────────────────────────────────────────────────
    for ad, liste in (("kabin tamponu", kabin_tamponlari), ("ağırlık tamponu", agirlik_tamponlari),
                      ("regülatör gergisi", [gergi])):
        for k in liste:
            if k[0] < 0 or k[1] < 0 or k[2] > G or k[3] > D:
                hata.append(f"{ad.capitalize()} kuyunun dışına taşıyor.")
            elif any(_ortusur(k, p) for p in konsollar + kabin_raylari + agirlik_raylari):
                hata.append(f"{ad.capitalize()} bir ray ya da konsolla çakışıyor.")
    for k in agirlik_tamponlari:
        if not (blok[0] <= _merkez(k)[0] <= blok[2] and blok[1] <= _merkez(k)[1] <= blok[3]):
            hata.append("Ağırlık tamponu karşı ağırlığın altına düşmüyor — tamponlar arasını daraltın.")
    for k in kabin_tamponlari:
        if not (kabin[0] <= _merkez(k)[0] <= kabin[2]):
            hata.append("Kabin tamponu kabinin altına düşmüyor — tamponlar arasını daraltın.")
    if len(kabin_tamponlari) == 2 and _ortusur(*kabin_tamponlari):
        hata.append("İki kabin tamponu üst üste biniyor — tamponlar arasını açın.")
    if len(agirlik_tamponlari) == 2 and _ortusur(*agirlik_tamponlari):
        hata.append("İki ağırlık tamponu üst üste biniyor — tamponlar arasını açın.")

    #  ── SIĞINMA ALANI  ( Çizelge 4 ) ──────────────────────────────────
    #  Kabinin izinin altında ( yüksekliği kabinin altına göre hesaplanır ),
    #  sabit donanıma basmadan, kapıya ve kabin eksenine en yakın yere.
    tip = kd["siginma_tipi"]
    engel = sabit + ([merdiven] if merdiven else [])
    siginma = None
    adaylar = []
    for w, h in {SIGINMA[tip], SIGINMA[tip][::-1]}:
        y = max(0.0, kabin[1])
        while y + h <= min(D, kabin[3]) + 1e-9:
            x = max(0.0, kabin[0])
            while x + w <= min(G, kabin[2]) + 1e-9:
                k = (x, y, x + w, y + h)
                if not any(_ortusur(k, p) for p in engel):
                    adaylar.append((round(y, 3), abs(x + w / 2.0 - kx), k))
                x += 25.0
            y += 25.0
    if adaylar:
        siginma = min(adaylar)[2]
    else:
        a, b = SIGINMA[tip]
        hata.append(f"Kuyu dibinde {tip.lower()} tipi sığınma alanına ( {a:g} × {b:g} mm, "
                    "TS EN 81-20 Çizelge 4 ) kabinin altında yer yok — tamponlar, gergi ve "
                    "merdiven dışında kalmalı.")

    return {"taban": taban, "kabin": kabin, "blok": blok, "kabin_raylari": kabin_raylari,
            "agirlik_raylari": agirlik_raylari, "kabin_tamponlari": kabin_tamponlari,
            "agirlik_tamponlari": agirlik_tamponlari, "perde": perde, "gergi": gergi,
            "merdiven": merdiven, "siginma": siginma, "siginma_tipi": tip, "hata": hata,
            "S": S, "ag_yan": ag_yan}


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    """Kuyu dibi planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    S = Y["S"]
    k = g["kuyu"]
    G, D, don, dg, dar = k["genislik"], k["derinlik"], k["duvar_on"], k["duvar_sag"], k["duvar_arka"]
    e = [el for el in Y["taban"] if el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi"]
    O = CGE._olcu

    #  Kabinin izi ve kat kapısı:  yalnız yer göstermek için, kesik
    kb = Y["kabin"]
    e.append(CGE._ad(CGE._dik("GIZLI", kb[0], kb[1], kb[2] - kb[0], kb[3] - kb[1]), "kabin_izi"))
    kp = g["kapi"]
    e.append(CGE._ad(CGE._dik("GIZLI", kp["sol_pay"], -don, kp["genislik"], don), "kapi_izi"))

    #  Tamponlar:  taban plakası + gövde
    def _tampon(kutu, ad):
        cx, cy = _merkez(kutu)
        e.append(CGE._ad(CGE._dik("TAMPON", kutu[0], kutu[1], kutu[2] - kutu[0], kutu[3] - kutu[1]), ad))
        e.append(CGE._ad(CGE._daire("TAMPON", cx, cy, S["tampon_capi"] / 2.0), ad))
    for t in Y["kabin_tamponlari"]:
        _tampon(t, "kabin_tamponu")
    for t in Y["agirlik_tamponlari"]:
        _tampon(t, "agirlik_tamponu")

    p = Y["perde"]
    e.append(CGE._ad(CGE._cizgi("PERDE", *p), "perde"))
    gr = Y["gergi"]
    e.append(CGE._ad(CGE._dik("KASNAK", gr[0], gr[1], gr[2] - gr[0], gr[3] - gr[1]), "gergi"))
    if Y["merdiven"]:
        m = Y["merdiven"]
        e.append(CGE._ad(CGE._dik("MERDIVEN", m[0], m[1], m[2] - m[0], m[3] - m[1]), "merdiven"))
        e.append(CGE._yazi(_merkez(m)[0] + (110 if m[0] < G / 2 else -110), _merkez(m)[1],
                           "MERDİVEN", 36, aci=90))
    sg = Y["siginma"]
    if sg:
        e.append(CGE._ad(CGE._dik("SIGINMA", sg[0], sg[1], sg[2] - sg[0], sg[3] - sg[1]), "siginma"))
        a, b = SIGINMA[Y["siginma_tipi"]]
        cx, cy = _merkez(sg)
        e.append(CGE._yazi(cx, cy + 35, "SIĞINMA ALANI", 38))
        e.append(CGE._yazi(cx, cy - 35, f"{Y['siginma_tipi'].upper()}  {a:g} x {b:g}", 34))

    #  ── YAZILAR ──────────────────────────────────────────────────────
    #  Kuyu tabanına yük aktaran noktalar — hesap paftasındaki adlarla
    yazilar = [(t, "Fkt") for t in Y["kabin_tamponlari"]] + \
              [(t, "Fat") for t in Y["agirlik_tamponlari"]] + \
              [(r, "FKR") for r in Y["kabin_raylari"]] + \
              [(r, "FAR") for r in Y["agirlik_raylari"]]
    for kutu, ad in yazilar:
        cx, cy = _merkez(kutu)
        e.append(CGE._ad(CGE._yazi(cx, kutu[3] + 45, ad, 40), "yuk"))
    e.append(CGE._yazi(_merkez(gr)[0] - (80 if gr[0] > G / 2 else -80), _merkez(gr)[1],
                       "REGÜLATÖR GERGİSİ", 34, aci=90))
    pm = ((p[0] + p[2]) / 2.0, (p[1] + p[3]) / 2.0)
    #  Perde yazısı ağırlıkla perde arasındaki boşluğa, tamponun yanına
    #  denk gelmeyen yarıya yazılır.
    bl = Y["blok"]
    tamp = _birlesim(Y["agirlik_tamponlari"])
    if p[0] == p[2]:
        yx = (p[0] + (bl[2] if Y["ag_yan"] == "Sol" else bl[0])) / 2.0
        yy = (tamp[3] + p[3]) / 2.0
        e.append(CGE._yazi(yx, yy, "KARŞI AĞIRLIK PERDESİ", 30, aci=90))
    else:
        yx = (tamp[2] + p[2]) / 2.0
        e.append(CGE._yazi(yx, (p[1] + bl[1]) / 2.0, "KARŞI AĞIRLIK PERDESİ", 30))

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    kx = (kb[0] + kb[2]) / 2.0
    ry = g["kabin_ray"]["kapi_arasi"]
    bx, by = _merkez(Y["blok"])
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    a0 = -don - 120
    #  Üst:  tampon eksenleri ( ağırlık ekseni · kabin ekseni )
    xs = sorted({0.0, G} | {_merkez(t)[0] for t in Y["kabin_tamponlari"] + Y["agirlik_tamponlari"]})
    e += [O("yatay", (a, 0), (b, 0), u0) for a, b in zip(xs, xs[1:])]
    e.append(O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    #  Sağ:  ray ekseni ve regülatör gergisi
    ys = sorted({0.0, D, ry, _merkez(gr)[1]} | {_merkez(t)[1] for t in Y["agirlik_tamponlari"]})
    e += [O("dusey", (0, a), (0, b), s0) for a, b in zip(ys, ys[1:])]
    e.append(O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    #  Alt:  kat kapısı ve merdivenin kapıya uzaklığı
    xs = sorted({0.0, G, kp["sol_pay"], kp["sol_pay"] + kp["genislik"]} |
                ({Y["merdiven"][0], Y["merdiven"][2]} if Y["merdiven"] else set()))
    e += [O("yatay", (a, 0), (b, 0), a0,
            f"KAPI {kp['genislik']:g}" if (a, b) == (kp["sol_pay"], kp["sol_pay"] + kp["genislik"])
            else None) for a, b in zip(xs, xs[1:])]
    #  Sığınma alanının yeri — kuyu duvarlarından
    if sg:
        kot_y = sg[3] + 90
        kot_x = sg[2] + 90
        e += [O("yatay", (0, 0), (sg[0], 0), kot_y), O("yatay", (sg[0], 0), (sg[2], 0), kot_y),
              O("yatay", (sg[2], 0), (G, 0), kot_y),
              O("dusey", (0, 0), (0, sg[1]), kot_x), O("dusey", (0, sg[1]), (0, sg[3]), kot_x),
              O("dusey", (0, sg[3]), (0, D), kot_x)]
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e
