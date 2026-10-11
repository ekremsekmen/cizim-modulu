# -*- coding: utf-8 -*-
"""
KAPI YAN KESİTİ  —  en alt durağın kapısı, ortasından düşey kesit ( 1/20 )

LiftDesigner'ın "Front Entrance Side View"ü ve Wittur'un kat kapısı montaj
kesiti ( SB.2.007539 s.17 ) gibi:  kat tarafındaki duvar ve döşeme, kasa, üst
kutu ve tavana bağlantısı, oluklu eşik ve L konsolu, eşik altı sacı, kat kapısı
kanatları;  kabin durakta:  kabin eşiği, kabin kapısı kanatları, önlük.  Ölçüler
ve standardın sayıları parçaların yanında ( cizim/parcalar.py — KAPI YAN KESİTİ ).

Eksenler:  u planın y'si ( kuyunun ön iç yüzünden kuyuya +;  kat tarafı solda,
kuyu sağda — A-A kesitiyle aynı yön ), z durak döşemesinden yukarı.
Yerler planla aynı kaynaktan:  girdi.kapi_bolgesi ( kasa · eşik · kapı hattı ·
kabin eşiği ), kanat düzlemleri sabitlerden ( kanat_esik_payi, kanat_araligi,
kanat_kalinlik ).
"""

from cizim import eleman
from cizim import dusey
from cizim import geometri
from cizim import girdi
from cizim import kesit_parcalari
from cizim import parcalar
from cizim import sabitler

#  Görünüşün kat tarafında gösterilen döşeme boyu ve duvarın üstte / altta
#  gösterilen kısmı ( kesik kenar ) — çizimin çerçevesi, ölçü değil
DOSEME_GOSTERIM = 700.0
DUVAR_UST_GOSTERIM = 450.0
KABIN_GOSTERIM = 500.0
#  Üst kutunun içindeki askı mekanizması ( makaralar, askı rayı ):  LiftDesigner
#  K111'in kapı yan görünüşündeki iç dikdörtgen gibi, kutunun oranlarıyla —
#  kuyu tarafından %25, üstten %29, alttan %22 içeride;  kapalı sac kutunun
#  içinde kaldığı için kesik.  Ölçülü değil:  ÇİZİM KABULÜ.
ASKI_ORANLARI = (0.25, 0.29, 0.22)
_SAC_KURALI = (
    "TS EN 81-20 m.5.2.5.3.2 a:  eşiğin altında eşiğe bağlı düz yüzey, en az kilit "
    "bölgesinin yarısı + 50 mm.  Kilit bölgesi m.5.3.8.1'e göre en çok ±0,20 m, kabin "
    "ve kat kapısı birlikte mekanik açılıyorsa ±0,35 m;  bilinmediği için en büyüğü:  "
    "otomatikte 0,40 m, elle açılanda 0,25 m.  Altında en az 60° ve 20 mm pah ( d 2 )."
)
_ONLUK_KURALI = (
    "TS EN 81-20 m.5.4.5:  kabin eşiğinin önlüğü kat girişinin eninde;  dik kısmı "
    "en az 0,75 m, altında yatayla en az 60°, yatay izdüşümü en az 20 mm pah."
)


def dogrula(g):
    return geometri.dogrula(g)


def _duzlemler(S, tip, esik0, esik1):
    """Kanat düzlemlerinin başları ( u ) — geometri.plan'daki kanatlar() ile aynı kural."""
    KT = girdi.kapi_tipi(tip)
    if KT["tur"] == "manuel" or KT["duzlem"] == 1:
        return [(esik0 + esik1) / 2.0 - S["kanat_kalinlik"] / 2.0]
    return [esik0 + S["kanat_esik_payi"] + i * S["kanat_araligi"] for i in range(KT["duzlem"])]


def yerlesim(g, cizim_sabitleri=None):
    """Kesitin parçaları ( u, z ) — çizim, ölçüler ve testler bunu okur."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    kp = g["kapi"]
    KB = girdi.kapi_bolgesi(g, S)
    tip = kp.get("tip")
    KT = girdi.kapi_tipi(tip)
    HH = kp["yukseklik"]
    et = S["esik_kalinlik"]
    kat_d = _duzlemler(S, tip, *KB["esik"])
    kab_d = _duzlemler(S, tip, *KB["kabin_esik"])
    yarim = S["kanat_kalinlik"] / 2.0
    tur = "manuel" if KT["tur"] == "manuel" else "otomatik"
    sac_boy = parcalar.ESIK_ALTI_SACI[tur]
    return {
        "S": S,
        "KB": KB,
        "HH": HH,
        "et": et,
        "tur": tur,
        "bosluk_h": girdi.kaba_bosluk(g, S)[2],
        "alt": et if kp["montaj"] == "Duvar boşluğuna" else 0.0,
        "kasa": (KB["kasa"][0], -et, KB["kasa"][1], HH + S["kasa_ust"]),
        "ust_kutu": (KB["kasa"][1], HH, KB["hat"], HH + S["kasa_ust"]),
        "kat_esigi": (KB["esik"][0], -et, KB["esik"][1], 0.0),
        "kabin_esigi": (KB["kabin_esik"][0], -et, KB["kabin_esik"][1], 0.0),
        "kat_kanatlari": [(u, 0.0, u + S["kanat_kalinlik"], HH) for u in kat_d],
        "kabin_kanatlari": [(u, 0.0, u + S["kanat_kalinlik"], HH) for u in kab_d],
        "kat_oluklari": [] if tur == "manuel" else [u + yarim for u in kat_d],
        "kabin_oluklari": [] if tur == "manuel" else [u + yarim for u in kab_d],
        #  eşik altı sacı:  eşiğin kuyu kenarından iner, pahla duvara döner
        "sac": (KB["hat"], -et, sac_boy),
        #  önlük:  kabin eşiğinin kat tarafındaki kenarından iner, pahla kabine döner
        "onluk": (KB["kabin_esik"][0], -et, parcalar.ONLUK_DIK - et),
    }


def ciz(g, cizim_sabitleri=None):
    """Kapı yan kesitinin elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    S, KB, HH, et = Y["S"], Y["KB"], Y["HH"], Y["et"]
    don = g["kuyu"]["duvar_on"]
    bh, alt = Y["bosluk_h"], Y["alt"]
    e = []

    def kutu(katman, k, ad):
        e.append(eleman.ad(eleman.dikdortgen(katman, k[0], k[1], k[2] - k[0], k[3] - k[1]), ad))
        return e[-1]

    #  ── DUVAR VE DÖŞEME ──────────────────────────────────────────────
    #  Ön duvar kaba boşluğun altında ( kuyu dibine doğru ) ve üstünde ( lento );
    #  duvar boşluğuna montajda boşluk eşiğin altından başlar ( A-A gibi ).
    sac_u, sac_z, sac_boy = Y["sac"]
    on_u, on_z, on_boy = Y["onluk"]
    import math

    tan = math.tan(math.radians(parcalar.PAH_ACISI))
    z_alt = min(sac_z - sac_boy - sac_u * tan, on_z - on_boy - parcalar.ONLUK_PAH_DUSEY) - 150
    z_ust = bh + DUVAR_UST_GOSTERIM
    for z0, z1 in ((z_alt, -alt), (bh, z_ust)):
        e.append(eleman.dikdortgen("TARAMA", -don, z0, don, z1 - z0, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", -don, z0, don, z1 - z0))
    dos = S["kat_doseme_kalinlik"]
    e.append(eleman.dikdortgen("TARAMA", -don - DOSEME_GOSTERIM, -dos, DOSEME_GOSTERIM, dos, tip="tarama"))
    e.append(
        eleman.ad(
            eleman.dikdortgen("KUYU-DUVAR", -don - DOSEME_GOSTERIM, -dos, DOSEME_GOSTERIM, dos),
            "kat_dosemesi",
        )
    )

    #  ── KAT KAPISI ───────────────────────────────────────────────────
    kutu("KAPI", Y["kasa"], "kapi_kasasi")
    ku = kutu("KAPI", Y["ust_kutu"], "kapi_ust_kutusu")
    a_k, a_u, a_a = ASKI_ORANLARI
    e.append(
        eleman.ad(
            eleman.dikdortgen(
                "GIZLI", ku["x"], ku["y"] + a_a * ku["d"], ku["g"] * (1 - a_k), ku["d"] * (1 - a_u - a_a)
            ),
            "aski_mekanizmasi",
        )
    )
    #  Üst kutu duvara L konsolla bağlı ( kutunun üstünden duvar yüzünde yukarı )
    k = eleman.ad(
        eleman.dikdortgen("KONSOL", 0.0, Y["ust_kutu"][3], KB["hat"], parcalar.UST_KONSOL_UZANTI),
        "ust_konsol",
    )
    k["bicim"] = parcalar.l_konsol(0.0, KB["hat"], Y["ust_kutu"][3], parcalar.UST_KONSOL_UZANTI, yukari=True)
    e.append(k)
    es = kutu("KAPI", Y["kat_esigi"], "kat_esigi")
    es["bicim"] = parcalar.esik_kesiti(es["x"], es["x"] + es["g"], 0.0, et, Y["kat_oluklari"])
    #  Eşik L konsolun yatay ayağında;  dik ayağı duvarın kuyu yüzünde aşağı
    k = eleman.ad(
        eleman.dikdortgen(
            "KONSOL", 0.0, -et - parcalar.ESIK_KONSOLU_BOY, KB["hat"], parcalar.ESIK_KONSOLU_BOY
        ),
        "esik_konsolu",
    )
    k["bicim"] = parcalar.l_konsol(0.0, KB["hat"], -et, parcalar.ESIK_KONSOLU_BOY)
    e.append(k)
    for kk in Y["kat_kanatlari"]:
        kutu("KAPI", kk, "kat_kanadi")
    #  Eşik altı sacı ( m.5.2.5.3.2 ):  dik, sonra pahla duvara
    dz = sac_u * tan
    s = eleman.ad(eleman.dikdortgen("KAPI", 0.0, sac_z - sac_boy - dz, sac_u, sac_boy + dz), "esik_alti_saci")
    s["bicim"] = parcalar.pahli_sac(sac_u, sac_z, sac_boy, 0.0)
    e.append(s)

    #  ── KABİN ( durakta ) ────────────────────────────────────────────
    ke = kutu("KABIN", Y["kabin_esigi"], "kabin_esigi")
    ke["bicim"] = parcalar.esik_kesiti(ke["x"], ke["x"] + ke["g"], 0.0, et, Y["kabin_oluklari"])
    for kk in Y["kabin_kanatlari"]:
        kutu("KAPI", kk, "kabin_kanadi")
    on = KB["kabin_esik"][1]
    e.append(
        eleman.ad(
            eleman.dikdortgen(
                "KABIN", on, -S["kabin_taban_kalinlik"], KABIN_GOSTERIM, S["kabin_taban_kalinlik"]
            ),
            "kabin_tabani",
        )
    )
    e.append(eleman.ad(eleman.dikdortgen("KABIN", on, HH, S["kabin_pano_yan"], 300.0), "kabin_on_panosu"))
    #  Önlük ( m.5.4.5 ):  kabin eşiğinin kat tarafındaki kenarından dik, sonra pahla kabine
    pz = parcalar.ONLUK_PAH_DUSEY
    o = eleman.ad(
        eleman.dikdortgen("KABIN", on_u, on_z - on_boy - pz, parcalar.ONLUK_PAH, on_boy + pz), "onluk"
    )
    o["bicim"] = parcalar.pahli_sac(
        on_u, on_z, on_boy, on_u + parcalar.ONLUK_PAH, dz=parcalar.ONLUK_PAH_DUSEY
    )
    e.append(o)

    #  ── YAZILAR ──────────────────────────────────────────────────────
    h = 40.0
    e.append(eleman.yazi(-don - DOSEME_GOSTERIM / 2.0, 120.0, "KAT", h))
    e.append(eleman.yazi(on + KABIN_GOSTERIM / 2.0, 120.0, "KABİN", h))

    #  Parça adları oklu:  ok yazının yanından parçaya ( kabinin ve kanatların
    #  üstünden geçmez — sac ve önlük döşemenin altında, üst kutu kabin panosunun üstünden )
    def adli(u, z, metin, ad, hedef):
        e.append(eleman.ad(eleman.yazi(u, z, metin, 32, hiza="sol"), ad))
        e.append(eleman.ad(eleman.ok("YAZI", u - 15.0, z, hedef[0], hedef[1]), "etiket_oku"))

    #  Sacın yazısı önlüğün ve pahın altında;  ok sac ile önlük arasından pahın ortasına
    pah_z = sac_z - sac_boy - sac_u * tan / 2.0
    onluk_dibi = on_z - on_boy - parcalar.ONLUK_PAH_DUSEY
    adli(
        on_u + 40.0,
        min(onluk_dibi, sac_z - sac_boy - sac_u * tan) - 110.0,
        "EŞİK ALTI SACI",
        "sac_yazisi",
        (sac_u / 2.0, pah_z),
    )
    zo_ = on_z - on_boy * 0.6
    adli(on_u + 200.0, zo_, "ÖNLÜK", "onluk_yazisi", (on_u, zo_))
    ku = Y["ust_kutu"]
    adli(on + 140.0, ku[3] + 220.0, "ÜST KUTU", "ust_kutu_yazisi", (KB["hat"], ku[3]))
    kesit_parcalari.kot_isareti(e, -don - DOSEME_GOSTERIM + 150.0, 0.0, dusey._kot(0.0), 1.0)

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    #  Altta:  duvar · kasa · eşik · eşik arası · kabin eşiği ( kuyunun ön iç yüzünden )
    zo = z_alt - 150.0
    nok = sorted(
        {-don, 0.0, KB["kasa"][0], KB["kasa"][1], KB["esik"][1], KB["kabin_esik"][0], KB["kabin_esik"][1]}
    )
    metin = {(KB["esik"][1], KB["kabin_esik"][0]): f"EŞİK ARASI {KB['kabin_esik'][0] - KB['esik'][1]:g}"}
    for a, b in zip(nok, nok[1:]):
        if b - a > 1e-6:
            e.append(eleman.olcu("yatay", (a, 0), (b, 0), zo, metin.get((a, b))))
    #  Kat tarafı:  kapı, üst kutu ( kasanın üstü ), kaba boşluk
    u1 = -don - DOSEME_GOSTERIM - 150.0
    e.append(eleman.olcu("dusey", (0, 0.0), (0, HH), u1, f"KAPI {HH:g}"))
    e.append(eleman.olcu("dusey", (0, HH), (0, HH + S["kasa_ust"]), u1, None))
    e.append(eleman.olcu("dusey", (0, 0.0), (0, bh), u1 - 230.0, f"KAPI BOŞLUĞU {bh:g}"))
    #  Kuyu tarafı:  eşik altı sacının dik kısmı ( eşiğin altından ) ve önlüğün
    #  dik kısmı ( döşemeden — m.5.4.5.2 )
    u2 = on + KABIN_GOSTERIM + 150.0
    e.append(
        eleman.olcu("dusey", (0, sac_z - sac_boy), (0, sac_z), u2, f"SAC {sac_boy:g}", kural=_SAC_KURALI)
    )
    e.append(
        eleman.olcu(
            "dusey", (0, on_z - on_boy), (0, 0.0), u2 + 230.0, f"ÖNLÜK {on_boy + et:g}", kural=_ONLUK_KURALI
        )
    )
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri._yazilari_yerlestir(e)
    return e
