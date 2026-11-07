# -*- coding: utf-8 -*-
"""
KAPI YAN KESİTİ  —  giriş katının kapısı, ortasından düşey kesit ( 1/20 )
( 2 Kas'a kadar en alt durağın;  kapı her katta aynı, yazı giriş katının kotu —
katlar.giris_kotu, KAT_ADLARI_PLANI )

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

from cizim import istek_onbellegi
from cizim import eleman
from cizim import kisaltmalar
from cizim import uslup
from cizim import dusey
from cizim import katlar
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


@istek_onbellegi.sakla
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
        #  eşik altı sacı:  eşiğin kuyu kenarından iner, pahla biter ( kapı her
        #  katta aynı;  alttaki kapı bu görünüşte yok — lentoya bağlanan sac
        #  düşey kesitlerde )
        "sac": girdi.esik_alti_saci(g, S),
        #  önlük:  kabin eşiğinin kat tarafındaki kenarından iner, pahla kabine döner
        "onluk": (KB["kabin_esik"][0], -et, parcalar.ONLUK_DIK - et),
    }


def ciz(g, cizim_sabitleri=None):
    """Kapı yan kesitinin elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    don = g["kuyu"]["duvar_on"]
    e = []
    #  Görünüşün altı:  eşik altı sacının ve önlüğün pahlarının 150 altı
    on_u, on_z, on_boy = Y["onluk"]
    z_alt = min(Y["sac"]["alt"], on_z - on_boy - parcalar.PAH_DUSEY) - 150
    _duvar_ve_doseme(e, Y, don, z_alt)
    _kat_kapisi(e, Y)
    _kabin(e, Y)
    _yazilar(e, Y, don, dusey.kot_ofseti(g), katlar.giris_kotu(g))
    _olculer(e, Y, don, z_alt)
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e)
    return e


def _kutu(e, katman, k, ad):
    e.append(eleman.ad(eleman.dikdortgen(katman, k[0], k[1], k[2] - k[0], k[3] - k[1]), ad))
    return e[-1]


def _duvar_ve_doseme(e, Y, don, z_alt):
    """DUVAR VE DÖŞEME:  ön duvar kaba boşluğun altında ( kuyu dibine doğru ) ve
    üstünde ( lento );  duvar boşluğuna montajda boşluk eşiğin altından başlar
    ( A-A gibi )."""
    bh, alt = Y["bosluk_h"], Y["alt"]
    z_ust = bh + DUVAR_UST_GOSTERIM
    for z0, z1 in ((z_alt, -alt), (bh, z_ust)):
        e.append(eleman.dikdortgen("TARAMA", -don, z0, don, z1 - z0, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", -don, z0, don, z1 - z0))
    dos = Y["S"]["kat_doseme_kalinlik"]
    e.append(eleman.dikdortgen("TARAMA", -don - DOSEME_GOSTERIM, -dos, DOSEME_GOSTERIM, dos, tip="tarama"))
    e.append(
        eleman.ad(
            eleman.dikdortgen("KUYU-DUVAR", -don - DOSEME_GOSTERIM, -dos, DOSEME_GOSTERIM, dos),
            "kat_dosemesi",
        )
    )


def _kat_kapisi(e, Y):
    """KAT KAPISI:  kasa, üst kutu ve konsolu, eşik ve konsolu, kanatlar, eşik altı sacı."""
    KB, et = Y["KB"], Y["et"]
    _kutu(e, "KAPI", Y["kasa"], "kapi_kasasi")
    ku = _kutu(e, "KAPI", Y["ust_kutu"], "kapi_ust_kutusu")
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
    es = _kutu(e, "KAPI", Y["kat_esigi"], "kat_esigi")
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
        _kutu(e, "KAPI", kk, "kat_kanadi")
    #  Eşik altı sacı ( m.5.2.5.3.2 ):  dik, sonra pahla duvara doğru
    e.append(kesit_parcalari.esik_alti_saci_kesiti(Y["sac"]))


def _kabin(e, Y):
    """KABİN ( durakta ):  eşik, kanatlar, taban, ön pano, önlük."""
    S, KB, HH, et = Y["S"], Y["KB"], Y["HH"], Y["et"]
    on_u, on_z, on_boy = Y["onluk"]
    ke = _kutu(e, "KABIN", Y["kabin_esigi"], "kabin_esigi")
    ke["bicim"] = parcalar.esik_kesiti(ke["x"], ke["x"] + ke["g"], 0.0, et, Y["kabin_oluklari"])
    for kk in Y["kabin_kanatlari"]:
        _kutu(e, "KAPI", kk, "kabin_kanadi")
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
    pz = parcalar.PAH_DUSEY
    o = eleman.ad(eleman.dikdortgen("KABIN", on_u, on_z - on_boy - pz, parcalar.PAH, on_boy + pz), "onluk")
    o["bicim"] = parcalar.pahli_sac(on_u, on_z, on_boy, on_u + parcalar.PAH, pz)
    e.append(o)


def _adli(e, u, z, metin, ad, hedef):
    """Parçanın adı oklu:  ok yazının yanından parçaya."""
    e.append(eleman.ad(eleman.yazi(u, z, metin, uslup.NORMAL, hiza="sol"), ad))
    e.append(eleman.ad(eleman.ok("YAZI", u - 15.0, z, hedef[0], hedef[1]), "etiket_oku"))


def _yazilar(e, Y, don, ofset, giris_kotu):
    """KAT ve KABİN yazıları, parça adları, durağın kot işareti.  Parça adlarının
    okları kabinin, kanatların ve önlüğün üstünden geçmez — sac ve önlük
    döşemenin altında, üst kutu kabin panosunun üstünden."""
    KB, sac = Y["KB"], Y["sac"]
    on_u, on_z, on_boy = Y["onluk"]
    on = KB["kabin_esik"][1]
    h = uslup.NORMAL
    #  Kat yanının adı kot işaretinin üstünde ( döşemenin ucunda ):  kapının ve kaba
    #  boşluğun ölçüleri duvarın yanında, eski yerinin içinden geçiyor
    e.append(eleman.yazi(-don - DOSEME_GOSTERIM + 120.0, 200.0, "KAT", h))
    e.append(eleman.yazi(on + KABIN_GOSTERIM / 2.0, 120.0, "KABİN", h))
    #  Sacın yazısı önlüğün ve sacın altında, duvarın yanından başlar:  ok duvar
    #  ile önlük arasından yukarı, pahın ortasına ( önlük sacın önünde daha
    #  aşağı iner — yandan gelen ok onu keserdi )
    du, dz = sac["pah"]
    onluk_dibi = on_z - on_boy - parcalar.PAH_DUSEY
    _adli(
        e,
        40.0,
        min(onluk_dibi, sac["alt"]) - 110.0,
        "EŞİK ALTI SACI",
        "sac_yazisi",
        (sac["u"] - du / 2.0, sac["dik_alt"] - dz / 2.0),
    )
    #  Önlüğün adı sacın ve önlüğün ölçülerinin ötesinde;  ok sacın alt ucunun
    #  hizasından:  sacın ölçü yazısı ister ortasında ister ucunun altında dursun
    #  üstünden geçmez ( ölçüler önlüğün yanında — _olculer )
    zo_ = _onluk_oku_z(Y)
    _adli(e, _sac_olcusu_u(Y) + 230.0 + 150.0, zo_, "ÖNLÜK", "onluk_yazisi", (on_u, zo_))
    ku = Y["ust_kutu"]
    _adli(e, on + 140.0, ku[3] + 220.0, "ÜST KUTU", "ust_kutu_yazisi", (KB["hat"], ku[3]))
    #  Kot işareti döşemenin ucunda ( yazısı sağında — solda olsaydı çizimin sınırı
    #  kotun uzunluğuyla oynardı ):  kaba boşluğun ölçüsü duvarın yanında
    kesit_parcalari.kot_isareti(
        e, -don - DOSEME_GOSTERIM + 60.0, 0.0, dusey.kot_yazisi(giris_kotu, ofset), 1.0
    )


def _sac_ve_onluk(Y):
    """Sacın ve önlüğün dik kısımlarının ölçüleri:  [ ( alt , üst , sıra , yazı , kural ) ]."""
    _on_u, on_z, on_boy = Y["onluk"]
    sac, et, u2 = Y["sac"], Y["et"], _sac_olcusu_u(Y)
    return (
        (sac["dik_alt"], sac["ust"], u2, f"SAC {sac['ust'] - sac['dik_alt']:g}", _SAC_KURALI),
        (on_z - on_boy, 0.0, u2 + 230.0, f"ÖNLÜK {on_boy + et:g}", _ONLUK_KURALI),
    )


def _ol_yazi_z(Y, a, b, metin):
    """Sacın / önlüğün ölçü yazısının ortası:  ölçünün ortası;  kabin tabanının
    ( 150 öteye dek gösterilir ) altına sığmıyorsa tabanın 30 altından başlar
    ( maskesi tabanın kenarını siliyordu )."""
    w = eleman.yazi_eni(metin, uslup.NORMAL) / 2.0
    tavan = -Y["S"]["kabin_taban_kalinlik"] - 30.0 - uslup.maske_payi(uslup.NORMAL)
    return min((a + b) / 2.0, tavan - w)


def _onluk_oku_z(Y):
    """Önlüğün adının okunun yüksekliği:  sacın ve önlüğün ölçü yazılarının
    ( _ol_yazi_z ) altında, önlüğün alt ucunun üstünde."""
    _on_u, on_z, on_boy = Y["onluk"]
    alt = min(
        _ol_yazi_z(Y, a, b, m) - eleman.yazi_eni(m, uslup.NORMAL) / 2.0
        for a, b, _u, m, _k in _sac_ve_onluk(Y)
    )
    return max(alt - 60.0 - uslup.maske_payi(uslup.NORMAL), on_z - on_boy + 30.0)


def _sac_olcusu_u(Y):
    """Sacın ölçüsünün sırası:  kabin eşiğinin ve önlüğün 150 ötesi ( önlüğün
    ölçüsü onun 230 ötesinde, önlüğün adı onun da ötesinde )."""
    on_u = Y["onluk"][0]
    return max(on_u + parcalar.PAH, Y["KB"]["kabin_esik"][1]) + 150.0


def _olculer(e, Y, don, z_alt):
    """Altta:  duvar · kasa · eşik · eşik arası · kabin eşiği ( kuyunun ön iç
    yüzünden );  kat tarafında kapı, üst kutu, kaba boşluk;  kuyu tarafında eşik
    altı sacının ve önlüğün dik kısımları."""
    S, KB, HH, bh = Y["S"], Y["KB"], Y["HH"], Y["bosluk_h"]
    #  Ölçüler ölçtükleri özelliğin yanında ( 7 Kas çizim denetimi 6. adımı, karar
    #  D3 ):  kapı ve kaba boşluk duvarın kat yüzünün yanında ( eskiden kat
    #  döşemesinin gösterilen ucunun ötesindeydi );  sac ve önlük önlüğün yanında
    #  ( eskiden kabin eşiğinin gösterilen ucunun ötesinde ).  Alttaki zincir yerinde:
    #  eşiklerin altına alınınca 60 · 90 · 30'un yazıları duvarın, sacın ve önlüğün
    #  çizgilerine sıkışıyordu
    zo = z_alt - 150.0
    nok = sorted(
        {-don, 0.0, KB["kasa"][0], KB["kasa"][1], KB["esik"][1], KB["kabin_esik"][0], KB["kabin_esik"][1]}
    )
    metin = {(KB["esik"][1], KB["kabin_esik"][0]): f"EŞİK ARASI {KB['kabin_esik'][0] - KB['esik'][1]:g}"}
    for a, b in zip(nok, nok[1:]):
        if b - a > 1e-6:
            e.append(eleman.olcu("yatay", (a, 0), (b, 0), zo, metin.get((a, b))))
    u1 = -don - 120.0
    e.append(eleman.olcu("dusey", (0, 0.0), (0, HH), u1, kisaltmalar.kodlu("DH", HH), ad="kapi_yuksekligi"))
    e.append(eleman.olcu("dusey", (0, HH), (0, HH + S["kasa_ust"]), u1, None))
    e.append(eleman.olcu("dusey", (0, 0.0), (0, bh), u1 - 200.0, f"KAPI BOŞLUĞU {bh:g}"))
    #  Eşik altı sacı eşiğin altından, önlük döşemeden ( m.5.4.5.2 )
    #  Yazıları sabit ( _ol_yazi_z — kabin tabanının altında ):  önlüğün adının oku
    #  ikisinin de altından geçer ( _onluk_oku_z )
    for a, b, u, metin, kural in _sac_ve_onluk(Y):
        yazi = {"x": u + 50.0, "y": _ol_yazi_z(Y, a, b, metin), "aci": 90, "h": uslup.NORMAL}
        e.append(eleman.olcu("dusey", (0, a), (0, b), u, metin, kural=kural, yazi=yazi))
