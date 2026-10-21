# -*- coding: utf-8 -*-
"""
DÜŞEY KESİTLERİN YERLEŞİMİ VE AÇIKLIK DENETİMİ

Tam boy A-A / B-B kesitleri ( kuyu_kesiti.py ) bu yerleşimi kullanır.  Açıklıklar
iki konumda denetlenir:
  kuyu dibi   kabin tam ezilmiş tamponunun üstünde
  kuyu üstü   kabin en üst konumunda:  karşı ağırlık tam ezilmiş tamponunun
              üstünde + 0,035 · v²  ( m.5.2.5.6.1 )
Kuyu dibi ve kuyu üstü ayrıca DÜŞEY detay kesitle çizilmez:  ofisin paftalarında
( 477-8, 12744-3 ) ikisi de YATAY kesittir ( kuyu dibi planı E-E, kuyu üstü /
makine dairesi planı F-F ).

Yatay eksen kuyu derinliğidir ( 0 = ön duvarın iç yüzü );  plan çizimleriyle
aynı koordinat — kabin, ray, tampon ve sığınma alanı plandaki yerlerinden
okunur.  Düşey eksen döşeme kotudur ( 0 = en alt / en üst durak ).

KABİNİN DÜŞEY ÖLÇÜLERİ referans proje kabininden ( sabitler.py;  birleşik
programda hesabın Sabitler sekmesinden değiştirilir — cizim/kopru.OFIS_SABITLERI ).
Hesap programının bölüm 11'i ( sığınma alanları ve açıklıklar ) açıklıkları
BU MODELDEN okur:  paftadaki tablo ile kesitteki ölçü aynı sayıdır.  ( Eskiden
hesap ofisin paylarıyla ayrı hesaplıyordu — üst paten bir satırda 2.700, bir
başkasında 2.900 — ve iki pafta 150 mm ayrışabiliyordu. )

STANDARDIN DENETLEDİĞİ AÇIKLIKLAR
  kuyu dibi   m.5.2.5.8.1  sığınma yüksekliği ( Çizelge 4 )
              m.5.2.5.8.2 a  kabinin en alt kısımları ≥ 0,50 m;  etek ≥ 0,10;
                             şase, paten, fren bloğu ( raya yakın ) ≥ 0,10
  kuyu üstü   m.5.2.5.7.1  sığınma yüksekliği ( Çizelge 3 )
              m.5.2.5.7.2 b  paten ≥ 0,10  ( 0,40 m yatay uzaklık içindeki tavan parçalarına )
              m.5.2.5.7.2 c  korkuluğun üstü ≥ 0,30 kabin izdüşümünde, dışında ≥ 0,10
              m.5.2.5.6.2   kabin ve karşı ağırlık en üst konumdayken raylar en az
                            0,10 m daha kılavuzluk eder  ( konum:  m.5.2.5.6.1 Çizelge 2 )
  "Kuyu tavanının en alt kısmı" kirişler ve tavanın altındaki parçalar dahildir
  ( m.5.2.5.7.2 ):  makine dairesizde makine şasesi, halat bağlantıları ve
  regülatör — yerleri donanim.py'de.
  duraklar    m.5.2.3.1     ardışık iki kat kapısı eşiği arası 11 m'yi aşarsa ara
                            acil kapı gerekir — bu çizim acil kapı çizmez, durur
"""

from temel import eleman_kutusu, ortusur, sayi_mi
from cizim import istek_onbellegi
from cizim import eleman
from cizim import arka_aski
from cizim import donanim
from cizim import geometri
from cizim import parcalar
from cizim import hareketli
from cizim import kabin_ustu
from cizim import kuyu_dibi
from cizim import sabitler
from cizim import parca_kotlari
from cizim import kuyu_ustu
from cizim import makine
from cizim import sorun
from cizim import sorunlu

#  Çizelge 3 / Çizelge 4 — sığınma alanının YÜKSEKLİĞİ ( mm )
SIGINMA_UST_YUKSEKLIK = kabin_ustu.SIGINMA_YUKSEKLIK
SIGINMA_DIP_YUKSEKLIK = kuyu_dibi.SIGINMA_YUKSEKLIK
DIP_EN_ALT = 500.0  # m.5.2.5.8.2 a
DIP_ETEK = 100.0  # m.5.2.5.8.2 a 1)
DIP_RAYA_YAKIN = 100.0  # m.5.2.5.8.2 a 2) · Şekil 7  ( XH ≤ 0,15 m )
UST_PATEN = 100.0  # m.5.2.5.7.2 b
UST_DONANIM = 500.0  # m.5.2.5.7.2 a  kabin tavanına bağlı donanım ( revizyon kutusu, kabin üstü kasnaklar )
DIP_SABIT = 300.0  # m.5.2.5.8.2 b  kuyuya sabit parça ( regülatör gergisi ) – kabinin en alt kısmı
UST_KORKULUK = 300.0  # m.5.2.5.7.2 c 1)  kabin izdüşümünde
UST_KORKULUK_DIS = 100.0  # m.5.2.5.7.2 c 1)  korkuluğun dışında
YATAY_UZAKLIK = 400.0  # m.5.2.5.7.2 b / c 1)  "0,40 m yatay uzaklık içinde"
#  Şasenin kirişleri gerçek yükseklikleriyle ( Sabitler sase_ust_kiris,
#  sase_alt_kiris — 8 Eki'ye dek 10 mm'lik simgeydi );  üst kirişin altı kabin
#  tavanının, alt kirişin üstü platformun dışında kalır ( yerlesim ).
RAY_UZANTISI = 100.0  # m.5.2.5.6.2  ( en üst konum m.5.2.5.6.1:  + 0,035·v² )
ETEK_BOYU = parca_kotlari.ETEK_BOYU  # m.5.4.5.2:  kabin önlüğünün dik kısmı en az 0,75 m
ESIK_ARASI = 11000.0  # m.5.2.3.1:  ardışık kat kapısı eşikleri arası
DUSEY_ALANLAR = (
    "kabin_ic_yukseklik",
    "kabin_paten_arasi",
    "agirlik_paten_arasi",
    "son_kat",
    "beyan_hizi",
    "kabin_tampon_baba",
    "kabin_tampon_boyu",
    "kabin_carpma_arasi",
    "kabin_tampon_ezilme",
    "agirlik_tampon_baba",
    "agirlik_tampon_boyu",
    "agirlik_carpma_arasi",
    "agirlik_tampon_ezilme",
)


def durak_kotlari(g, cizim_sabitleri=None):
    """Durakların döşeme kotları ( en alt durak ±0 ) ve girdi hataları.

    kat_yuksekligi tek sayıysa bütün katlar o yükseklikte;  liste ise alttan
    üste ardışık iki durak arası ( durak_adedi − 1 tane ).  Referans projede
    hepsi 2.900;  LiftDesigner örneğinde 3.400, 3.400, 3.000 … karışık.
    """
    dy, kp = g.get("dusey") or {}, g.get("kapi") or {}
    n, kh = dy.get("durak_adedi"), dy.get("kat_yuksekligi")
    if not (sayi_mi(n) and n == int(n) and n >= 2):
        return [], [f"dusey.durak_adedi:  2 ya da daha büyük bir tam sayı olmalı ( {n!r} )."]
    n = int(n)
    araliklar = [kh] * (n - 1) if sayi_mi(kh) else kh
    if not (
        isinstance(araliklar, (list, tuple))
        and len(araliklar) == n - 1
        and all(sayi_mi(h) and h > 0 for h in araliklar)
    ):
        return [], [
            f"dusey.kat_yuksekligi:  sıfırdan büyük bir sayı ya da {n - 1} "
            f"sayılık bir liste olmalı ( {kh!r} )."
        ]
    hata = []
    kapi_h = kp.get("yukseklik") or 0
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    esik = S["esik_kalinlik"] if kp.get("montaj") == "Duvar boşluğuna" else 0.0
    bosluk_h = kapi_h + S["kapi_ust_payi"] + esik
    for i, h in enumerate(araliklar):
        ad = f"{i + 1}. – {i + 2}. durak arası {h:g} mm"
        if h <= kapi_h:
            hata.append(
                sorun.Sorun(
                    f"{ad}:  kat kapısı yüksekliğinden ( {kapi_h:g} ) büyük olmalı — "
                    f"kapı üstteki durağın döşemesine giriyor.",
                    _KAT_KAPISI,
                    "kuyu_kesiti_yan",
                    fark=h - kapi_h,
                )
            )
        elif h <= bosluk_h:
            hata.append(
                sorun.Sorun(
                    f"{ad}:  kapı yüksekliği {kapi_h:g} + üst payı {S['kapi_ust_payi']:g} "
                    f"+ eşik alt payı {esik:g} = {bosluk_h:g} mm'den büyük olmalı — "
                    "ardışık kapı boşlukları arasında duvar kalmıyor.",
                    _KAT_KAPISI,
                    "kuyu_kesiti_yan",
                    fark=h - bosluk_h,
                )
            )
        if h > ESIK_ARASI:
            hata.append(
                sorun.Sorun(
                    f"{ad} > {ESIK_ARASI:g} mm:  ara acil kapı gerekir "
                    f"( TS EN 81-20 m.5.2.3.1 );  bu çizim acil kapı çizmez.",
                    _KAT_KAPISI,
                    "kuyu_kesiti_yan",
                    fark=ESIK_ARASI - h,
                )
            )
    kotlar = [0.0]
    for h in araliklar:
        kotlar.append(kotlar[-1] + h)
    return kotlar, hata


kabin_kotlari = parca_kotlari.kabin_kotlari


@istek_onbellegi.sakla
def yerlesim(g, cizim_sabitleri=None):
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    dy = g.get("dusey") or {}
    #  Denetim hatası yerleşimi durdurur;  sorunlu çizim kipinde ( yalnız ekran —
    #  cizim/sorunlu.py ) durmaz, kurabildiği kadar kurar.  Kip kapalıyken
    #  dönüş bugünküyle aynıdır ( hesap, paket ve sorun listesi kipin dışında ).
    surdur = sorunlu.acik()
    kotlar, hata = _girdi_hatalari(g, S, dy)
    if hata and not surdur:
        return {"hata": hata}
    durdu = _cerceve_ve_sase(g, S, dy, hata)
    if durdu:
        if not surdur:
            return durdu
        hata += durdu["hata"]
    KD, KU = kuyu_dibi.yerlesim(g, S), kabin_ustu.yerlesim(g, S)
    if KD["hata"] or KU["hata"]:
        #  Kuyu dibinin geometrisi hiç kurulamadıysa ( "taban" yok ) kip de durur
        if not surdur or "taban" not in KD:
            return {"hata": KD["hata"] + KU["hata"]}
        hata += KD["hata"] + KU["hata"]
    dip = _kuyu_dibi_acikliklari(g, S, dy, KD, hata)
    #  ── KUYU ÜSTÜ:  kabin en üst konumunda ────────────────────────────
    #  Karşı ağırlık tam ezilmiş tamponunda + 0,035·v²  ( m.5.2.5.6.1 )
    H = kotlar[-1]
    M = donanim.yerlesim(g, S, H, H + dy["son_kat"], dip["taban"])
    if M["hata"]:
        #  Donanımın geometrisi hiç kurulamadıysa ( "raylar" yok — örneğin
        #  çizilemeyen askı düzeni ) kip de durur
        if not surdur or "raylar" not in M:
            return {"hata": hata + M["hata"]}
        hata += M["hata"]
    _regulator_acikligi(KD, KU, M, dip)
    ust = _kuyu_ustu_acikliklari(g, S, dy, KD, KU, M, H)
    AK, AKd = _agirlik_uc_konumlari(g, S, dy, KD, M, H, dip["taban"], ust["ust_aciklik"], hata)
    #  Açıklık dışındaki fiziksel hatalar ( kuyu dibi zinciri, ağırlığın
    #  şaseye çarpması ):  hesabın bölüm 11'i açıklıkları sözlüklerden okur,
    #  bunları ayrıca basar.
    diger = list(hata)
    for yer, aciklik in (("dip", dip["dip_aciklik"]), ("ust", ust["ust_aciklik"])):
        for ad, (deger, asgari, madde) in aciklik.items():
            if deger < asgari - 1e-9:
                hata.append(
                    sorun.Sorun(
                        f"{AD[ad]}:  {deger:g} mm < {asgari:g} mm  ( TS EN 81-20 {madde} ).",
                        _aciklik_parcalari(yer, ad, dip["dip_engel"], ust["ust_engel"]),
                        _aciklik_kesiti(yer, ad),
                        fark=deger - asgari,
                    )
                )
    return {
        "hata": hata,
        "diger": diger,
        "S": S,
        "KD": KD,
        "KU": KU,
        "M": M,
        "dip": dip["dip"],
        "ust": ust["ust"],
        "taban": dip["taban"],
        "tavan_alti": ust["tavan_alti"],
        "ray_ustu": ust["ray_ustu"],
        "yukselme": ust["yukselme"],
        "ust_engel": ust["ust_engel"],
        "agirlik_ust": AK,
        "korkuluk": ust["korkuluk"],
        "dip_aciklik": dip["dip_aciklik"],
        "ust_aciklik": ust["ust_aciklik"],
        "dip_parcalar": dip["dip_parcalar"],
        "dip_engel": dip["dip_engel"],
        "agirlik_alt": AKd,
        "kasnaklar": dip["kasnaklar"],
        "kasnak_capi": dip["kasnak_capi"],
        "kotlar": kotlar,
    }


def _girdi_hatalari(g, S, dy):
    """( durak kotları, girdi hataları )."""
    hata = [
        f"dusey.{a}: sıfırdan büyük bir sayı olmalı ( {dy.get(a)!r} )."
        for a in DUSEY_ALANLAR
        if not (sayi_mi(dy.get(a)) and dy[a] > 0)
    ]
    kotlar, durak_hata = durak_kotlari(g, S)
    hata += durak_hata
    for tur, ad in (("kabin", "Kabin"), ("agirlik", "Karşı ağırlık")):
        boy, ezilme = dy.get(tur + "_tampon_boyu"), dy.get(tur + "_tampon_ezilme")
        if sayi_mi(boy) and sayi_mi(ezilme) and ezilme > boy:
            hata.append(
                sorun.Sorun(
                    f"{ad} tamponu ezilme miktarı ({ezilme:g} mm), tamponun boyundan ({boy:g} mm) büyük olamaz.",
                    (tur + "_tamponu",),
                    "kuyu_kesiti_yan",
                    fark=boy - ezilme,
                )
            )
    #  Çizilemeyen askı / ağırlık birleşimi ilk söylenir ( öbür planların
    #  hataları onun sonucudur )
    hata += kuyu_ustu.duzen_hatalari(g)
    return kotlar, hata


def _cerceve_ve_sase(g, S, dy, hata):
    """Karşı ağırlık çerçevesi ve kabin şasesi paten aralarına sığıyor mu.
    Çizim duruyorsa sonuç ( { hata } ), yoksa None ( üst kirişin tavana
    girmesi hataya eklenir, çizim sürer )."""
    #  Karşı ağırlık çerçevesi patenlerin arasındadır ( çerçeve = paten arası −
    #  bir paten boyu — parca_kotlari.agirlik_kotlari ):  kasnağını ( üst kirişin
    #  agirlik_kasnak_ust altında ) ve iki kirişini taşıyacak kadar olmalı
    R = (g["agirlik"].get("kasnak_capi") or 0) / 2.0
    cerceve = dy["agirlik_paten_arasi"] - S["paten_yukseklik"]
    if cerceve <= max(2 * S["agirlik_kiris"], S["agirlik_kasnak_ust"] + R):
        return {
            "hata": [
                sorun.Sorun(
                    f"dusey.agirlik_paten_arasi:  patenlerin merkezleri arasıdır;  çerçeve "
                    f"ondan bir paten boyu kısa ( {cerceve:g} mm ) — kasnağına ve "
                    "kirişlerine yetmiyor.",
                    ("agirlik", "agirlik_paten", "agirlik_kasnagi"),
                    "kuyu_kesiti_yan",
                    fark=cerceve - max(2 * S["agirlik_kiris"], S["agirlik_kasnak_ust"] + R),
                )
            ]
        }
    #  ŞASE ( kabin_kotlari:  patenler kirişlerin dışında ):  üst kiriş kabin
    #  tavanının, alt kiriş platformun dışında kalmalı.  Kabin iç yüksekliği
    #  paten arasına göre büyükse üst kiriş kabinin içinden geçer;  girilen
    #  ölçü değiştirilmez, çizim durur ve gereken paten arasını söyler.
    kabin = kabin_kotlari(dy, S, 0.0)
    kiris_alti = kabin["ust_kiris_alt"]
    if kabin["alt_kiris_ust"] > kabin["taban_alti"] + 1e-6:
        return {
            "hata": [
                sorun.Sorun(
                    f"Kabin alt şase kirişi kabin tabanına giriyor:  kirişin üstü "
                    f"{kabin['alt_kiris_ust']:g} mm, platformun altı {kabin['taban_alti']:g} mm "
                    "( Sabitler:  şase altı, alt paten payı, paten ve alt kiriş yüksekliği ).",
                    ("sase_kiris", "sase_kirisi", "kabin"),
                    "kuyu_kesiti_yan",
                    fark=kabin["taban_alti"] - kabin["alt_kiris_ust"],
                )
            ]
        }
    if kiris_alti < kabin["tavan"] - 1e-6:
        gerekli = dy["kabin_paten_arasi"] + kabin["tavan"] - kiris_alti
        hata.append(
            sorun.Sorun(
                f"Kabin üst şase kirişi kabin tavanına giriyor:  kirişin altı "
                f"{kiris_alti:g} mm, tavan {kabin['tavan']:g} mm;  "
                f"bu ölçülerle kabin paten arası en az {gerekli:g} mm olmalı.",
                ("sase_kiris", "sase_kirisi", "kabin"),
                "kuyu_kesiti_yan",
                fark=kiris_alti - kabin["tavan"],
            )
        )
    return None


def _kuyu_dibi_acikliklari(g, S, dy, KD, hata):
    """KUYU DİBİ:  kabin tam ezilmiş tamponunda."""
    kd = g["kuyu_dibi"]
    KY = kd["derinlik"]
    #  Kuyu dibi zinciri kabinin şase altıyla kapanmalı:  kaide + tampon +
    #  çarpma arası + şase altı = kuyu dibi ( referans proje:  764 + 160 + 96 + 480 )
    zincir = (
        dy["kabin_tampon_baba"] + dy["kabin_tampon_boyu"] + dy["kabin_carpma_arasi"] + S["sase_alt_derinlik"]
    )
    if abs(zincir - KY) > 0.5:
        hata.append(
            sorun.Sorun(
                f"Kuyu dibi {KY:g} mm, ama kaide {dy['kabin_tampon_baba']:g} + tampon "
                f"{dy['kabin_tampon_boyu']:g} + çarpma arası {dy['kabin_carpma_arasi']:g} + kabinin "
                f"şase altı {S['sase_alt_derinlik']:g} = {zincir:g} mm — girdiler kabinle çelişiyor.",
                ("kabin_kaidesi", "kabin_tamponu"),
                "kuyu_kesiti_yan",
            )
        )
    aski = g.get("aski") or {}
    tavanda = arka_aski.arkada_iki_bir(g)
    dip = kabin_kotlari(dy, S, -(dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"]), aski, tavanda)
    taban = -KY
    #  KABİNİN PARÇALARI ( hareketli.kabin_parcalari — kuyu dibinin yerleşimi
    #  alanı aynı parçalardan kaçırır ):  sığınma alanının üstündeki en alçak
    #  parça ( kabin tabanı, alt şase kirişi, kabin altı kasnakları ve
    #  aralarındaki halat … ) ile kabinin en alt kısmı ( rayın yakınındaki
    #  patenler, fren bloğu ve dikmeler hariç — onlar m.5.2.5.8.2 a 2 ).  Eskiden
    #  yalnız platformun altı ve kabin altı kasnakları sayılıyordu:  alt şase
    #  kirişi sığınma alanının üstündeyken de yükseklik platformdan ölçülüyordu.
    kasnaklar = kuyu_dibi.kabin_alti_askisi(g, S, KD["taban"])
    dip_parcalar = hareketli.kabin_parcalari(g, S, KD["taban"], dip)
    en_alt, en_alt_ad = min(
        [(dip["taban_alti"], hareketli.KABIN)]
        + [(p[2], p[0]) for p in dip_parcalar if p[0] not in hareketli.RAYA_YAKIN]
    )
    dip_engel, sg_aciklik = {}, {}
    #  Sığınma alanı yerleşemediyse ( yalnız sorunlu kipte buraya gelinir —
    #  sorunu kuyu dibi planı söyler ) üstündeki yükseklik ölçülmez.  Eskiden
    #  boş kutu karşılaştırmada çöküyor, ekranın bütün çizimleri kayboluyordu
    #  ( pafta başlığı da bu denetimi çağırır — 20 Eki ).
    if KD["siginma"] is not None:
        siginma_ustu, dip_engel["siginma"] = hareketli.ustundeki_en_alt(
            dip_parcalar, KD["siginma"], (dip["taban_alti"], hareketli.KABIN)
        )
        sg_aciklik["siginma"] = (
            siginma_ustu - taban,
            SIGINMA_DIP_YUKSEKLIK[kd["siginma_tipi"]],
            "m.5.2.5.8.1 · Çizelge 4",
        )
    dip_engel["en_alt"] = en_alt_ad
    return {
        "dip": dip,
        "taban": taban,
        "kasnaklar": kasnaklar,
        "kasnak_capi": aski.get("kasnak_capi") or 0,
        "dip_parcalar": dip_parcalar,
        "dip_engel": dip_engel,
        "dip_aciklik": {
            **sg_aciklik,
            "en_alt": (en_alt - taban, DIP_EN_ALT, "m.5.2.5.8.2 a"),
            "etek": (dip["etek_alti"] - taban, DIP_ETEK, "m.5.2.5.8.2 a 1"),
            "sase": (
                min(dip["sase_alt"], dip["alt_paten"], dip["fren_alti"]) - taban,
                DIP_RAYA_YAKIN,
                "m.5.2.5.8.2 a 2 · Şekil 7",
            ),
        },
    }


def _regulator_acikligi(KD, KU, M, dip):
    """KUYUYA SABİT PARÇA ( regülatör gergisi ) kabinin izdüşümündeyse, tam
    ezilmiş tamponundaki kabinin üstündeki en alt kısmıyla arası en az 0,30 m
    ( m.5.2.5.8.2 b ).  Kollu gerginin parçaları ayrı ayrı:  kasnak koruma
    kapağıyla, kol, ağırlık ( askısıyla ), plaka, kontak — en kısası.  Eskiden
    yalnız bölüm 11 ölçüyordu ( 21 Eki ).  İzdüşümde değilse açıklık yoktur."""
    gr, gd = M["gergi"], KD["gergi_donanim"]
    gp, Rk = gr["plan"], gr["geo"]["kapak_r"]
    gy = (gp[1] + gp[3]) / 2.0
    gergi = [((gp[0], gy - Rk, gp[2], gy + Rk), gr["merkez"] + Rk, "gergi kasnağının koruma kapağı")] + [
        (gd[ad], gr[ad][3], adi)
        for ad, adi in (
            ("kol", "gergi kolu"),
            ("agirlik", "gergi ağırlığı"),
            ("plaka", "gergi plakası"),
            ("kontak", "gergi kontağı"),
        )
    ]
    aralar = []
    for kutu, tepe, adi in gergi:
        if ortusur(kutu, KU["tavan"]):
            z, ad = hareketli.ustundeki_en_alt(
                dip["dip_parcalar"], kutu, (dip["dip"]["taban_alti"], hareketli.KABIN)
            )
            aralar.append((z - tepe, adi, ad))
    if aralar:
        ara, adi, ad = min(aralar)
        dip["dip_aciklik"]["regulator"] = (ara, DIP_SABIT, "m.5.2.5.8.2 b")
        dip["dip_engel"]["regulator"] = ad
        dip["dip_engel"]["regulator_parcasi"] = adi


def _genislet(k, d):
    return (k[0] - d, k[1] - d, k[2] + d, k[3] + d)


def _kuyu_ustu_acikliklari(g, S, dy, KD, KU, M, H):
    """KUYU ÜSTÜ:  kabin en üst konumunda ( karşı ağırlık tam ezilmiş
    tamponunda + 0,035·v² — m.5.2.5.6.1 ).  Engeller son kattan ölçülür."""
    aski = g.get("aski") or {}
    b35 = 35.0 * dy["beyan_hizi"] * dy["beyan_hizi"]  # 0,035 · v² · 1000
    yukselme = dy["agirlik_carpma_arasi"] + dy["agirlik_tampon_ezilme"] + b35
    ust = kabin_kotlari(dy, S, yukselme, aski, arka_aski.arkada_iki_bir(g))

    def engel(kutu):
        z, ad = donanim.tavan_engeli(M, kutu)
        return z - H, ad

    ray_ustu = min(r["ust"] for r in M["raylar"] if r["tur"] == "kabin") - H
    korkuluk = max((k["yukseklik"] for k in KU["kenarlar"].values() if k["gerekli"]), default=0.0)
    patenler = [
        eleman_kutusu(el)
        for el in KD["taban"]
        if el["katman"] == "PATEN" and el.get("ad") != "agirlik_pateni"
    ]
    pt_engel = min(engel(_genislet(p, YATAY_UZAKLIK)) for p in patenler)
    ust_engel, ust_aciklik = {}, {}
    #  Kabin üstünde sığınma alanı yerleşemediyse ( yalnız sorunlu kipte —
    #  sorunu kabin üstü planı söyler ) yüksekliği ölçülmez ( kuyu dibindeki gibi )
    if KU["siginma"] is not None:
        ust_engel["siginma"] = sg_engel = engel(KU["siginma"])
        ust_aciklik["siginma"] = (
            sg_engel[0] - ust["tavan"],
            SIGINMA_UST_YUKSEKLIK[g["kabin_ustu"]["siginma_tipi"]],
            "m.5.2.5.7.1 · Çizelge 3",
        )
    #  REVİZYON KUTUSU ( kabin üstündeki en yüksek donanım;  çizilmez — karar 10 ):
    #  kabin tavanından revizyon_payi yukarıda, kabinin izdüşümündeki en alt tavan
    #  parçasıyla arası en az 0,50 m ( m.5.2.5.7.2 a ).  Eskiden yalnız bölüm 11
    #  ölçüyordu:  çizim "uygun" derken hesap kalabiliyordu ( 21 Eki ).
    ust_engel["revizyon"] = rv_engel = engel(KU["tavan"])
    ust_aciklik["revizyon"] = (
        rv_engel[0] - (ust["tavan"] + S["revizyon_payi"]),
        UST_DONANIM,
        "m.5.2.5.7.2 a",
    )
    ust_engel.update(paten=pt_engel, ray=(ray_ustu, "ray"))
    ust_aciklik.update(
        paten=(pt_engel[0] - ust["ust_paten"], UST_PATEN, "m.5.2.5.7.2 b"),
        ray=(ray_ustu - ust["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2"),
    )
    #  KABİN ÜSTÜ ASKIDA kasnaklar kabin tavanına bağlı donanımdır:  en yüksek
    #  noktaları ile kabinin izdüşümündeki en alt tavan parçası arası en az
    #  0,50 m ( m.5.2.5.7.2 a ).
    if aski.get("duzen") == "Kabin üstü":
        ku_kasnak = geometri.kabin_kasnak_kutulari(g, S, KU["taban"])
        kasnak_ust = ust["kasnak_merkez"] + (aski.get("kasnak_capi") or 0) / 2.0
        ks_engel = min(engel(k) for k in ku_kasnak)
        ust_engel["kasnak"] = ks_engel
        ust_aciklik["kasnak"] = (ks_engel[0] - kasnak_ust, UST_DONANIM, "m.5.2.5.7.2 a")
    #  1:1 ASKIDA halat bağlantısı kabin şasesinin üst kirişinin üstündedir:
    #  soketlerin tepesi ile 0,40 m yatay uzaklık içindeki tavan parçaları arası
    #  en az 0,10 m ( m.5.2.5.7.2 b:  "the rope terminations" ).
    if aski.get("duzen") == "Doğrudan":
        hx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        hy = (
            g["kabin"]["on_pay"]
            + (g["kabin"]["derinlik"] + S["kabin_pano_arka"]) / 2.0
            + aski.get("nokta_kaciklik", 0)
        )
        dk = makine.halat_deligi(hx, hy, aski.get("halat_adedi") or 1, aski.get("halat_capi") or 0, 0.0)
        bg_engel = engel(_genislet(dk, YATAY_UZAKLIK))
        ust_engel["baglanti"] = bg_engel
        ust_aciklik["baglanti"] = (bg_engel[0] - ust["baglanti_ust"], UST_PATEN, "m.5.2.5.7.2 b")
    tavan_alti = dy["son_kat"] - S["tavan_kirisi"]
    if korkuluk:
        z, ad, asgari, k_ust = _korkuluk_engeli(KU, M, H, ust, korkuluk, tavan_alti)
        ust_engel["korkuluk"] = (z, ad)
        ust_aciklik["korkuluk"] = (z - k_ust, asgari, "m.5.2.5.7.2 c")
    return {
        "ust": ust,
        "tavan_alti": tavan_alti,
        "ray_ustu": ray_ustu,
        "yukselme": yukselme,
        "ust_engel": ust_engel,
        "korkuluk": korkuluk,
        "ust_aciklik": ust_aciklik,
    }


def _korkuluk_engeli(KU, M, H, ust, korkuluk, tavan_alti):
    """Korkuluğun 0,40 m yakınındaki tavan parçaları:  kabin izdüşümündeyse
    0,30, dışındaysa 0,10  ( m.5.2.5.7.2 c 1 ).  Her kenar kendi
    korkuluğunun yüksekliğiyle ( yan 0,70 · arka 1,10 olabilir — m.5.4.7.4
    b );  kuyu tavanı en yüksek korkuluğa.  Eskiden hepsine en yüksek
    korkuluk uygulanıyordu:  0,70'lik yan korkuluğun üstündeki halat
    bağlantısı 1,10'luk korkulukla ölçülüyordu.
    ( parçanın kotu, adı, asgari açıklık, korkuluğun üstü ) — en dar olanı."""
    adaylar = [(tavan_alti, "kuyu tavanı", UST_KORKULUK, ust["tavan"] + korkuluk)]
    for kenar, yuk in kabin_ustu.korkuluklar(KU):
        bolge = _genislet(kenar, YATAY_UZAKLIK)
        for ad, p, z in M["parcalar"]:
            if ortusur(p, bolge):
                icinde = ortusur(p, KU["tavan"])
                adaylar.append((z - H, ad, UST_KORKULUK if icinde else UST_KORKULUK_DIS, ust["tavan"] + yuk))
    return min(adaylar, key=lambda a: a[0] - a[3] - a[2])


def _agirlik_uc_konumlari(g, S, dy, KD, M, H, taban, ust_aciklik, hata):
    """KARŞI AĞIRLIĞIN UÇ KONUMLARI — parçaları ( çerçeve, patenler, 2:1'de
    kasnak:  hareketli.agirlik_parcalari ) kuyunun tavanına ve tabanına
    değmemeli.  Standardın sayısı yok ( m.5.2.5.6.2 yalnız rayın kılavuzluğunu
    ister ):  değmemesi aranır.  En üstte her parçanın izinin üstündeki en
    alçak tavan parçası ( makine şasesi, bağlantılar, tavan kirişi payı —
    makine daireli ve dairesizde );  en altta tamponu tam ezilmişken.
    Eskiden yalnız makine dairesizde çerçevenin makine şasesine çarpması
    denetleniyordu:  makine dairelide kasnak tavana girebiliyor, alt paten
    kuyu tabanının altına inebiliyordu ( denetim 8 Eki ).
    Ağırlık rayının kılavuzluğu ust_aciklik'e girer.  ( en üst, en alt kotlar )"""
    #  Karşı ağırlık en üst konumunda:  kabin tam ezilmiş tamponunda + 0,035·v²
    b35 = 35.0 * dy["beyan_hizi"] * dy["beyan_hizi"]
    ag_alt = (
        M["agirlik"]["tampon_ustu"]
        + dy["agirlik_carpma_arasi"]
        + H
        + dy["kabin_carpma_arasi"]
        + dy["kabin_tampon_ezilme"]
        + b35
    )
    AK = parca_kotlari.agirlik_kotlari(M, ag_alt)
    ag_ray = min(r["ust"] for r in M["raylar"] if r["tur"] == "agirlik")
    ust_aciklik["agirlik_ray"] = (ag_ray - AK["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2")
    AKd = parca_kotlari.agirlik_kotlari(M, M["agirlik"]["tampon_ustu"] - dy["agirlik_tampon_ezilme"])
    #  Her uç konum için tek ileti:  en çok taşan parça, öbürleri adıyla.
    ust_carpan, alt_carpan = {}, {}
    for ad_, k, _, tepe in hareketli.agirlik_parcalari(g, S, KD["taban"], AK):
        z, engel_ad = donanim.tavan_engeli(M, k)
        if tepe > z + 1e-9 and tepe - z > ust_carpan.get(ad_, (0.0,))[0]:
            ust_carpan[ad_] = (tepe - z, tepe, z, engel_ad)
    for ad_, _k, dip_, _ in hareketli.agirlik_parcalari(g, S, KD["taban"], AKd):
        if dip_ < taban - 1e-9 and taban - dip_ > alt_carpan.get(ad_, 0.0):
            alt_carpan[ad_] = taban - dip_

    def ayrica(sozluk, en):
        oteki = [a for a in sozluk if a != en]
        return f"  ( ayrıca {', '.join(oteki)} )" if oteki else ""

    if ust_carpan:
        en = max(ust_carpan, key=lambda a: ust_carpan[a][0])
        _, tepe, z, engel_ad = ust_carpan[en]
        hata.append(
            sorun.Sorun(
                f"Karşı ağırlık en üst konumunda tavana çarpıyor:  {en} tepesi {tepe - H:g} mm, "
                f"üstündeki en alt tavan kısmı ( {donanim.TAVAN_PARCASI.get(engel_ad, engel_ad)} ) "
                f"{z - H:g} mm ( son kattan ){ayrica(ust_carpan, en)}.",
                sum((_KESIT_PARCASI.get(a, ()) for a in ust_carpan), ()) + _KESIT_PARCASI.get(engel_ad, ()),
                "kuyu_kesiti_yan",
                fark=-ust_carpan[en][0],
            )
        )
    if alt_carpan:
        en = max(alt_carpan, key=alt_carpan.get)
        hata.append(
            sorun.Sorun(
                f"Karşı ağırlık tamponu tam ezilmişken kuyu tabanına çarpıyor:  {en} altı "
                f"tabanın {alt_carpan[en]:g} mm altında{ayrica(alt_carpan, en)} ( ağırlık "
                "tampon kaidesi ya da tampon boyu büyütülmeli ).",
                sum((_KESIT_PARCASI.get(a, ()) for a in alt_carpan), ())
                + ("agirlik_tamponu", "agirlik_kaidesi"),
                #  Ağırlık en altta = kabin en üstte:  B-B
                "kuyu_kesiti_on",
                fark=-alt_carpan[en],
            )
        )
    return AK, AKd


AD = {
    "siginma": "Sığınma yüksekliği",
    "regulator": "Regülatör gergisi – kabinin en alt kısmı",
    "revizyon": "Revizyon kutusu – kuyu tavanı",
    "en_alt": "Kuyu tabanı – kabinin en alt kısmı",
    "etek": "Kuyu tabanı – kabin eteği",
    "sase": "Kuyu tabanı – şase / paten / fren bloğu",
    "paten": "Üst paten – kuyu tavanı",
    "ray": "Üst paten – rayın üst ucu",
    "kasnak": "Kabin üstü kasnağı – kuyu tavanı",
    "baglanti": "Kabindeki halat bağlantısı – kuyu tavanı",
    "korkuluk": "Korkuluk – kuyu tavanı",
    "agirlik_ray": "Karşı ağırlık üst pateni – rayın üst ucu",
}


#  Durak aralığı sorunlarında işaretlenen:  kat kapıları
_KAT_KAPISI = ("kat_kapisi", "kapi_kasasi")
#  SORUNLARIN PARÇALARI ( sorun.Sorun — ekran kesitte kırmızı işaretler ):
#  hareketli parçaların ( hareketli ) ve tavan engellerinin ( donanim.tavan_engeli )
#  adlarına karşılık kesitteki elemanların adları.
_KESIT_PARCASI = {
    hareketli.KABIN: ("kabin",),
    hareketli.ALT_KIRIS: ("sase_kiris", "sase_kirisi"),
    hareketli.UST_KIRIS: ("sase_kiris", "sase_kirisi"),
    hareketli.DIKME: ("sase",),
    hareketli.ALT_PATEN: ("alt_paten",),
    hareketli.UST_PATEN: ("ust_paten",),
    hareketli.FREN: ("fren",),
    hareketli.KASNAK: ("kabin_kasnak", "kabin_kasnagi"),
    #  Halat ve sığınma maskeli katmanda:  parça olarak işaretlenmez ( svg ),
    #  yanındaki kasnaklar / kabin yanar
    hareketli.HALAT: ("aski_halati", "kabin_kasnak", "kabin_kasnagi"),
    hareketli.BAGLANTI: ("kabin_baglanti",),
    hareketli.AG_CERCEVE: ("agirlik",),
    hareketli.AG_ALT_PATEN: ("agirlik_paten",),
    hareketli.AG_UST_PATEN: ("agirlik_paten",),
    hareketli.AG_KASNAK: ("agirlik_kasnagi",),
    "sase": ("makine_sasesi",),
    "kabin_baglanti": ("kabin_baglanti",),
    "agirlik_baglanti": ("agirlik_baglanti",),
    "regulator": ("regulator",),
    "kuyu tavanı": ("tavan_kirisi",),
    "ray": ("kabin_rayi",),
}
#  Açıklığın kendi tarafı ( öbür tarafı — engeli — dip_engel / ust_engel söyler )
_ACIKLIK_PARCASI = {
    ("dip", "siginma"): ("siginma", "kabin"),
    ("dip", "etek"): ("etek",),
    ("dip", "sase"): ("sase", "alt_paten", "fren", "sase_kiris", "sase_kirisi"),
    ("dip", "regulator"): (
        "gergi",
        "gergi_kapagi",
        "gergi_kasnagi",
        "gergi_kolu",
        "gergi_agirligi",
        "gergi_plakasi",
        "gergi_kontagi",
    ),
    ("ust", "siginma"): ("siginma", "kabin"),
    ("ust", "revizyon"): ("kabin",),
    ("ust", "paten"): ("ust_paten",),
    ("ust", "ray"): ("ust_paten",),
    ("ust", "kasnak"): ("kabin_kasnak", "kabin_kasnagi"),
    ("ust", "baglanti"): ("kabin_baglanti",),
    ("ust", "korkuluk"): ("korkuluk",),
    ("ust", "agirlik_ray"): ("agirlik_paten", "agirlik_rayi"),
}


def _aciklik_kesiti(yer, ad):
    """Açıklığın göründüğü kesit:  kuyu dibi ( kabin en altta ) A-A, kuyu üstü
    ( kabin en üstte ) B-B — A-A'da tavandaki korkuluk kuyunun dibindeydi,
    engeli tepede:  ikisini birlikte göstermek bütün kuyuyu kaplıyordu.
    Karşı ağırlığın üst ucu kabin en alttayken:  A-A."""
    return "kuyu_kesiti_on" if yer == "ust" and ad != "agirlik_ray" else "kuyu_kesiti_yan"


def _aciklik_parcalari(yer, ad, dip_engel, ust_engel):
    """Yetmeyen açıklığın iki yanındaki parçalar ( kesitteki adlarıyla )."""
    engel = (dip_engel if yer == "dip" else ust_engel).get(ad)
    if isinstance(engel, tuple):  # ust_engel:  ( kot , ad )
        engel = engel[1]
    return _ACIKLIK_PARCASI.get((yer, ad), ()) + _KESIT_PARCASI.get(engel, ())


def dogrula(g):
    hata = geometri.dogrula(g)
    #  Sorunlu kipte ( cizim/sorunlu.py ) ilk hatada durulmaz:  çare bulucu gizli
    #  kalan sorunları da görür ( uclar/care_uclari.py ).  Kip kapalıyken aynı.
    if hata and not sorunlu.acik():
        return hata
    return hata + yerlesim(g)["hata"]


def kot_yazisi(z):
    """Kot yazısı ( m ):  Türkçe ondalık virgülle — "±0,00", "+3,40"."""
    m = z / 1000.0
    return "±0,00" if abs(m) < 5e-4 else f"{m:+.2f}".replace(".", ",")


def kabin_kesiti(e, kt, kabin_y, ry, S, kasnaklar_y=None, kasnak_capi=0, kr_b=89, esik_on=None):
    """Kabinin kesiti:  gövde, taban, etek, şase, patenler, fren bloğu, kasnak.
    esik_on:  kabin eşiğinin kat tarafındaki kenarı ( önlük orada asılıdır;
    verilmezse kabinin ön yüzü )."""
    y0, y1 = kabin_y
    e.append(
        eleman.ad(
            eleman.dikdortgen("KABIN", y0, kt["taban_alti"], y1 - y0, kt["tavan"] - kt["taban_alti"]), "kabin"
        )
    )
    e.append(eleman.dikdortgen("KABIN-IC", y0, kt["doseme"], y1 - y0, kt["ic_ust"] - kt["doseme"]))
    #  Etek ( önlük, m.5.4.5 ):  kabin eşiğinin kat tarafındaki kenarından iner,
    #  dik kısmın altında pahla kabine döner ( eskiden kabinin ön yüzündeydi,
    #  eşiğin 90 gerisinde, pahsız )
    u = y0 if esik_on is None else esik_on
    ust = kt["doseme"] - S["esik_kalinlik"]
    et = eleman.ad(
        eleman.dikdortgen("KABIN", u, kt["etek_alti"], parcalar.ONLUK_PAH, ust - kt["etek_alti"]), "etek"
    )
    et["bicim"] = parcalar.pahli_sac(
        u, ust, ust - kt["etek_dik_alti"], u + parcalar.ONLUK_PAH, dz=parcalar.ONLUK_PAH_DUSEY
    )
    e.append(et)
    #  Şase:  ray ekseninde dikme, alt ve üst kiriş ( kabin_kotlari )
    #  Dikme iki ince profil olarak çizilir ( referans proje:  50 + 200 + 50 —
    #  parcalar.SASE_PROFIL_ENI;  plandaki kirişlerle aynı );  dolu çizilince
    #  kabinin kesitini örtüyordu.  Yandan bakışta kirişlerin iki C profili
    #  dikmelerin hizasında, uçlarıyla görünür ( LiftDesigner 4815-6 kuyu tepesi:
    #  40 + 160 + 40, 140 yüksek ).
    sd = S["sase_dikme_derinlik"]
    pe = min(parcalar.SASE_PROFIL_ENI, sd / 2.0)
    for x in (ry - sd / 2.0, ry + sd / 2.0 - pe):
        e.append(
            eleman.ad(
                eleman.dikdortgen(
                    "KABIN-IC", x, kt["alt_kiris_alt"], pe, kt["ust_kiris_ust"] - kt["alt_kiris_alt"]
                ),
                "sase",
            )
        )
        for z0, z1 in (
            (kt["alt_kiris_alt"], kt["alt_kiris_ust"]),
            (kt["ust_kiris_alt"], kt["ust_kiris_ust"]),
        ):
            e.append(eleman.ad(eleman.dikdortgen("KABIN-IC", x, z0, pe, z1 - z0), "sase_kiris"))
    #  Patenler ve fren bloğu
    e.append(
        eleman.ad(
            eleman.dikdortgen("PATEN", ry - 35, kt["ust_paten_alt"], 70, S["paten_yukseklik"]), "ust_paten"
        )
    )
    e.append(
        eleman.ad(eleman.dikdortgen("PATEN", ry - 35, kt["alt_paten"], 70, S["paten_yukseklik"]), "alt_paten")
    )
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(
            eleman.ad(eleman.dikdortgen("SASE", x, kt["fren_alti"], 50, S["fren_blogu_yukseklik"]), "fren")
        )
    #  Kabin kasnağı ( 2:1 kabin altı ):  kesitte yandan, çapı düşey
    for ky in kasnaklar_y or ():
        e.append(
            eleman.ad(
                eleman.dikdortgen(
                    "KASNAK",
                    ky - S["kabin_kasnak_genislik"] / 2.0,
                    kt["kasnak_merkez"] - kasnak_capi / 2.0,
                    S["kabin_kasnak_genislik"],
                    kasnak_capi,
                ),
                "kabin_kasnak",
            )
        )
