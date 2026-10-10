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
from cizim import eleman as CEL
from cizim import arka_aski as CAA
from cizim import donanim as CDN
from cizim import geometri as CGE
from cizim import parcalar as CP
from cizim import girdi as CG
from cizim import hareketli as CH
from cizim import kabin_ustu as CKU
from cizim import kuyu_dibi as CKD
from cizim import sabitler as CS

#  Çizelge 3 / Çizelge 4 — sığınma alanının YÜKSEKLİĞİ ( mm )
SIGINMA_UST_YUKSEKLIK = CKU.SIGINMA_YUKSEKLIK
SIGINMA_DIP_YUKSEKLIK = CKD.SIGINMA_YUKSEKLIK
DIP_EN_ALT = 500.0  # m.5.2.5.8.2 a
DIP_ETEK = 100.0  # m.5.2.5.8.2 a 1)
DIP_RAYA_YAKIN = 100.0  # m.5.2.5.8.2 a 2) · Şekil 7  ( XH ≤ 0,15 m )
UST_PATEN = 100.0  # m.5.2.5.7.2 b
UST_DONANIM = 500.0  # m.5.2.5.7.2 a  kabin tavanına bağlı donanım ( kabin üstü kasnaklar )
UST_KORKULUK = 300.0  # m.5.2.5.7.2 c 1)  kabin izdüşümünde
UST_KORKULUK_DIS = 100.0  # m.5.2.5.7.2 c 1)  korkuluğun dışında
YATAY_UZAKLIK = 400.0  # m.5.2.5.7.2 b / c 1)  "0,40 m yatay uzaklık içinde"
#  Şasenin kirişleri gerçek yükseklikleriyle ( Sabitler sase_ust_kiris,
#  sase_alt_kiris — 8 Eki'ye dek 10 mm'lik simgeydi );  üst kirişin altı kabin
#  tavanının, alt kirişin üstü platformun dışında kalır ( yerlesim ).
RAY_UZANTISI = 100.0  # m.5.2.5.6.2  ( en üst konum m.5.2.5.6.1:  + 0,035·v² )
ETEK_BOYU = CDN.ETEK_BOYU  # m.5.4.5.2:  kabin önlüğünün dik kısmı en az 0,75 m
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
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    esik = S["esik_kalinlik"] if kp.get("montaj") == "Duvar boşluğuna" else 0.0
    bosluk_h = kapi_h + S["kapi_ust_payi"] + esik
    for i, h in enumerate(araliklar):
        ad = f"{i + 1}. – {i + 2}. durak arası {h:g} mm"
        if h <= kapi_h:
            hata.append(
                f"{ad}:  kat kapısı yüksekliğinden ( {kapi_h:g} ) büyük olmalı — "
                f"kapı üstteki durağın döşemesine giriyor."
            )
        elif h <= bosluk_h:
            hata.append(
                f"{ad}:  kapı yüksekliği {kapi_h:g} + üst payı {S['kapi_ust_payi']:g} "
                f"+ eşik alt payı {esik:g} = {bosluk_h:g} mm'den büyük olmalı — "
                "ardışık kapı boşlukları arasında duvar kalmıyor."
            )
        if h > ESIK_ARASI:
            hata.append(
                f"{ad} > {ESIK_ARASI:g} mm:  ara acil kapı gerekir "
                f"( TS EN 81-20 m.5.2.3.1 );  bu çizim acil kapı çizmez."
            )
    kotlar = [0.0]
    for h in araliklar:
        kotlar.append(kotlar[-1] + h)
    return kotlar, hata


kabin_kotlari = CDN.kabin_kotlari


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    dy = g.get("dusey") or {}
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
                f"{ad} tamponu ezilme miktarı ({ezilme:g} mm), tamponun boyundan ({boy:g} mm) büyük olamaz."
            )
    #  Çizilemeyen askı / ağırlık birleşimi ilk söylenir ( öbür planların
    #  hataları onun sonucudur )
    from cizim import kuyu_ustu as CKT

    hata += CKT.duzen_hatalari(g)
    if hata:
        return {"hata": hata}
    #  Karşı ağırlık çerçevesi patenlerin arasındadır ( çerçeve = paten arası −
    #  bir paten boyu — donanim.agirlik_kotlari ):  kasnağını ( üst kirişin
    #  agirlik_kasnak_ust altında ) ve iki kirişini taşıyacak kadar olmalı
    R = (g["agirlik"].get("kasnak_capi") or 0) / 2.0
    cerceve = dy["agirlik_paten_arasi"] - S["paten_yukseklik"]
    if cerceve <= max(2 * S["agirlik_kiris"], S["agirlik_kasnak_ust"] + R):
        return {
            "hata": [
                f"dusey.agirlik_paten_arasi:  patenlerin merkezleri arasıdır;  çerçeve "
                f"ondan bir paten boyu kısa ( {cerceve:g} mm ) — kasnağına ve "
                "kirişlerine yetmiyor."
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
                f"Kabin alt şase kirişi kabin tabanına giriyor:  kirişin üstü "
                f"{kabin['alt_kiris_ust']:g} mm, platformun altı {kabin['taban_alti']:g} mm "
                "( Sabitler:  şase altı, alt paten payı, paten ve alt kiriş yüksekliği )."
            ]
        }
    if kiris_alti < kabin["tavan"] - 1e-6:
        gerekli = dy["kabin_paten_arasi"] + kabin["tavan"] - kiris_alti
        hata.append(
            f"Kabin üst şase kirişi kabin tavanına giriyor:  kirişin altı "
            f"{kiris_alti:g} mm, tavan {kabin['tavan']:g} mm;  "
            f"bu ölçülerle kabin paten arası en az {gerekli:g} mm olmalı."
        )
    KD, KU = CKD.yerlesim(g, S), CKU.yerlesim(g, S)
    if KD["hata"] or KU["hata"]:
        return {"hata": KD["hata"] + KU["hata"]}
    kd, ku = g["kuyu_dibi"], g["kabin_ustu"]
    v = dy["beyan_hizi"]
    b35 = 35.0 * v * v  # 0,035 · v² · 1000

    #  ── KUYU DİBİ:  kabin tam ezilmiş tamponunda ──────────────────────
    KY = kd["derinlik"]
    #  Kuyu dibi zinciri kabinin şase altıyla kapanmalı:  kaide + tampon +
    #  çarpma arası + şase altı = kuyu dibi ( referans proje:  764 + 160 + 96 + 480 )
    zincir = (
        dy["kabin_tampon_baba"] + dy["kabin_tampon_boyu"] + dy["kabin_carpma_arasi"] + S["sase_alt_derinlik"]
    )
    if abs(zincir - KY) > 0.5:
        hata.append(
            f"Kuyu dibi {KY:g} mm, ama kaide {dy['kabin_tampon_baba']:g} + tampon "
            f"{dy['kabin_tampon_boyu']:g} + çarpma arası {dy['kabin_carpma_arasi']:g} + kabinin "
            f"şase altı {S['sase_alt_derinlik']:g} = {zincir:g} mm — girdiler kabinle çelişiyor."
        )
    aski = g.get("aski") or {}
    tavanda = CAA.arkada_iki_bir(g)
    dip = kabin_kotlari(dy, S, -(dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"]), aski, tavanda)
    taban = -KY
    #  KABİNİN PARÇALARI ( hareketli.kabin_parcalari — kuyu dibinin yerleşimi
    #  alanı aynı parçalardan kaçırır ):  sığınma alanının üstündeki en alçak
    #  parça ( kabin tabanı, alt şase kirişi, kabin altı kasnakları ve
    #  aralarındaki halat … ) ile kabinin en alt kısmı ( rayın yakınındaki
    #  patenler, fren bloğu ve dikmeler hariç — onlar m.5.2.5.8.2 a 2 ).  Eskiden
    #  yalnız platformun altı ve kabin altı kasnakları sayılıyordu:  alt şase
    #  kirişi sığınma alanının üstündeyken de yükseklik platformdan ölçülüyordu.
    kasnaklar = CKD.kabin_alti_askisi(g, S, KD["taban"])
    kasnak_capi = (g.get("aski") or {}).get("kasnak_capi") or 0
    sg = KD["siginma"]
    dip_parcalar = CH.kabin_parcalari(g, S, KD["taban"], dip)
    siginma_ustu, siginma_ad = CH.ustundeki_en_alt(dip_parcalar, sg, (dip["taban_alti"], CH.KABIN))
    en_alt, en_alt_ad = min(
        [(dip["taban_alti"], CH.KABIN)] + [(p[2], p[0]) for p in dip_parcalar if p[0] not in CH.RAYA_YAKIN]
    )
    dip_engel = {"siginma": siginma_ad, "en_alt": en_alt_ad}
    dip_aciklik = {
        "siginma": (
            siginma_ustu - taban,
            SIGINMA_DIP_YUKSEKLIK[kd["siginma_tipi"]],
            "m.5.2.5.8.1 · Çizelge 4",
        ),
        "en_alt": (en_alt - taban, DIP_EN_ALT, "m.5.2.5.8.2 a"),
        "etek": (dip["etek_alti"] - taban, DIP_ETEK, "m.5.2.5.8.2 a 1"),
        "sase": (
            min(dip["sase_alt"], dip["alt_paten"], dip["fren_alti"]) - taban,
            DIP_RAYA_YAKIN,
            "m.5.2.5.8.2 a 2 · Şekil 7",
        ),
    }

    #  ── KUYU ÜSTÜ:  kabin en üst konumunda ────────────────────────────
    #  Karşı ağırlık tam ezilmiş tamponunda + 0,035·v²  ( m.5.2.5.6.1 )
    H = kotlar[-1]
    M = CDN.yerlesim(g, S, H, H + dy["son_kat"], -KY)
    if M["hata"]:
        return {"hata": hata + M["hata"]}
    yukselme = dy["agirlik_carpma_arasi"] + dy["agirlik_tampon_ezilme"] + b35
    ust = kabin_kotlari(dy, S, yukselme, aski, tavanda)
    tavan_alti = dy["son_kat"] - S["tavan_kirisi"]

    def engel(kutu):
        z, ad = CDN.tavan_engeli(M, kutu)
        return z - H, ad

    def genislet(k, d):
        return (k[0] - d, k[1] - d, k[2] + d, k[3] + d)

    kabin_izi = KU["tavan"]
    ray_ustu = min(r["ust"] for r in M["raylar"] if r["tur"] == "kabin") - H
    korkuluk = max((k["yukseklik"] for k in KU["kenarlar"].values() if k["gerekli"]), default=0.0)
    sg_engel = engel(KU["siginma"])
    patenler = [
        eleman_kutusu(el)
        for el in KD["taban"]
        if el["katman"] == "PATEN" and el.get("ad") != "agirlik_pateni"
    ]
    pt_engel = min(engel(genislet(p, YATAY_UZAKLIK)) for p in patenler)
    ust_engel = {"siginma": sg_engel, "paten": pt_engel, "ray": (ray_ustu, "ray")}
    ust_aciklik = {
        "siginma": (
            sg_engel[0] - ust["tavan"],
            SIGINMA_UST_YUKSEKLIK[ku["siginma_tipi"]],
            "m.5.2.5.7.1 · Çizelge 3",
        ),
        "paten": (pt_engel[0] - ust["ust_paten"], UST_PATEN, "m.5.2.5.7.2 b"),
        "ray": (ray_ustu - ust["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2"),
    }
    #  KABİN ÜSTÜ ASKIDA kasnaklar kabin tavanına bağlı donanımdır:  en yüksek
    #  noktaları ile kabinin izdüşümündeki en alt tavan parçası arası en az
    #  0,50 m ( m.5.2.5.7.2 a ).
    if aski.get("duzen") == "Kabin üstü":
        ku_kasnak = CGE.kabin_kasnak_kutulari(g, S, KU["taban"])
        kasnak_ust = ust["kasnak_merkez"] + (aski.get("kasnak_capi") or 0) / 2.0
        ks_engel = min(engel(k) for k in ku_kasnak)
        ust_engel["kasnak"] = ks_engel
        ust_aciklik["kasnak"] = (ks_engel[0] - kasnak_ust, UST_DONANIM, "m.5.2.5.7.2 a")
    #  1:1 ASKIDA halat bağlantısı kabin şasesinin üst kirişinin üstündedir:
    #  soketlerin tepesi ile 0,40 m yatay uzaklık içindeki tavan parçaları arası
    #  en az 0,10 m ( m.5.2.5.7.2 b:  "the rope terminations" ).
    if aski.get("duzen") == "Doğrudan":
        from cizim import makine as CMK

        hx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        hy = (
            g["kabin"]["on_pay"]
            + (g["kabin"]["derinlik"] + S["kabin_pano_arka"]) / 2.0
            + aski.get("nokta_kaciklik", 0)
        )
        dk = CMK.halat_deligi(hx, hy, aski.get("halat_adedi") or 1, aski.get("halat_capi") or 0, 0.0)
        bg_engel = engel(genislet(dk, YATAY_UZAKLIK))
        ust_engel["baglanti"] = bg_engel
        ust_aciklik["baglanti"] = (bg_engel[0] - ust["baglanti_ust"], UST_PATEN, "m.5.2.5.7.2 b")
    if korkuluk:
        #  Korkuluğun 0,40 m yakınındaki tavan parçaları:  kabin izdüşümündeyse
        #  0,30, dışındaysa 0,10  ( m.5.2.5.7.2 c 1 ).  Her kenar kendi
        #  korkuluğunun yüksekliğiyle ( yan 0,70 · arka 1,10 olabilir — m.5.4.7.4
        #  b );  kuyu tavanı en yüksek korkuluğa.  Eskiden hepsine en yüksek
        #  korkuluk uygulanıyordu:  0,70'lik yan korkuluğun üstündeki halat
        #  bağlantısı 1,10'luk korkulukla ölçülüyordu.
        adaylar = [(tavan_alti, "kuyu tavanı", UST_KORKULUK, ust["tavan"] + korkuluk)]
        for kenar, yuk in CKU.korkuluklar(KU):
            bolge = genislet(kenar, YATAY_UZAKLIK)
            for ad, p, z in M["parcalar"]:
                if ortusur(p, bolge):
                    icinde = ortusur(p, kabin_izi)
                    adaylar.append(
                        (z - H, ad, UST_KORKULUK if icinde else UST_KORKULUK_DIS, ust["tavan"] + yuk)
                    )
        z, ad, asgari, k_ust = min(adaylar, key=lambda a: a[0] - a[3] - a[2])
        ust_engel["korkuluk"] = (z, ad)
        ust_aciklik["korkuluk"] = (z - k_ust, asgari, "m.5.2.5.7.2 c")
    #  Karşı ağırlık en üst konumunda:  kabin tam ezilmiş tamponunda + 0,035·v²
    ag_alt = (
        M["agirlik"]["tampon_ustu"]
        + dy["agirlik_carpma_arasi"]
        + H
        + dy["kabin_carpma_arasi"]
        + dy["kabin_tampon_ezilme"]
        + b35
    )
    AK = CDN.agirlik_kotlari(M, ag_alt)
    ag_ray = min(r["ust"] for r in M["raylar"] if r["tur"] == "agirlik")
    ust_aciklik["agirlik_ray"] = (ag_ray - AK["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2")
    #  KARŞI AĞIRLIĞIN UÇ KONUMLARI — parçaları ( çerçeve, patenler, 2:1'de
    #  kasnak:  hareketli.agirlik_parcalari ) kuyunun tavanına ve tabanına
    #  değmemeli.  Standardın sayısı yok ( m.5.2.5.6.2 yalnız rayın kılavuzluğunu
    #  ister ):  değmemesi aranır.  En üstte her parçanın izinin üstündeki en
    #  alçak tavan parçası ( makine şasesi, bağlantılar, tavan kirişi payı —
    #  makine daireli ve dairesizde );  en altta tamponu tam ezilmişken.
    #  Eskiden yalnız makine dairesizde çerçevenin makine şasesine çarpması
    #  denetleniyordu:  makine dairelide kasnak tavana girebiliyor, alt paten
    #  kuyu tabanının altına inebiliyordu ( denetim 8 Eki ).
    AKd = CDN.agirlik_kotlari(M, M["agirlik"]["tampon_ustu"] - dy["agirlik_tampon_ezilme"])
    #  Her uç konum için tek ileti:  en çok taşan parça, öbürleri adıyla.
    ust_carpan, alt_carpan = {}, {}
    for ad_, k, _, tepe in CH.agirlik_parcalari(g, S, KD["taban"], AK):
        z, engel_ad = CDN.tavan_engeli(M, k)
        if tepe > z + 1e-9 and tepe - z > ust_carpan.get(ad_, (0.0,))[0]:
            ust_carpan[ad_] = (tepe - z, tepe, z, engel_ad)
    for ad_, _k, dip_, _ in CH.agirlik_parcalari(g, S, KD["taban"], AKd):
        if dip_ < taban - 1e-9 and taban - dip_ > alt_carpan.get(ad_, 0.0):
            alt_carpan[ad_] = taban - dip_

    def ayrica(sozluk, en):
        oteki = [a for a in sozluk if a != en]
        return f"  ( ayrıca {', '.join(oteki)} )" if oteki else ""

    if ust_carpan:
        en = max(ust_carpan, key=lambda a: ust_carpan[a][0])
        _, tepe, z, engel_ad = ust_carpan[en]
        hata.append(
            f"Karşı ağırlık en üst konumunda tavana çarpıyor:  {en} tepesi {tepe - H:g} mm, "
            f"üstündeki en alt tavan kısmı ( {CDN.TAVAN_PARCASI.get(engel_ad, engel_ad)} ) "
            f"{z - H:g} mm ( son kattan ){ayrica(ust_carpan, en)}."
        )
    if alt_carpan:
        en = max(alt_carpan, key=alt_carpan.get)
        hata.append(
            f"Karşı ağırlık tamponu tam ezilmişken kuyu tabanına çarpıyor:  {en} altı "
            f"tabanın {alt_carpan[en]:g} mm altında{ayrica(alt_carpan, en)} ( ağırlık "
            "tampon kaidesi ya da tampon boyu büyütülmeli )."
        )
    #  Açıklık dışındaki fiziksel hatalar ( kuyu dibi zinciri, ağırlığın
    #  şaseye çarpması ):  hesabın bölüm 11'i açıklıkları sözlüklerden okur,
    #  bunları ayrıca basar.
    diger = list(hata)
    for ad, (deger, asgari, madde) in list(dip_aciklik.items()) + list(ust_aciklik.items()):
        if deger < asgari - 1e-9:
            hata.append(f"{AD[ad]}:  {deger:g} mm < {asgari:g} mm  ( TS EN 81-20 {madde} ).")
    return {
        "hata": hata,
        "diger": diger,
        "S": S,
        "KD": KD,
        "KU": KU,
        "M": M,
        "dip": dip,
        "ust": ust,
        "taban": taban,
        "tavan_alti": tavan_alti,
        "ray_ustu": ray_ustu,
        "yukselme": yukselme,
        "ust_engel": ust_engel,
        "agirlik_ust": AK,
        "korkuluk": korkuluk,
        "dip_aciklik": dip_aciklik,
        "ust_aciklik": ust_aciklik,
        "dip_parcalar": dip_parcalar,
        "dip_engel": dip_engel,
        "agirlik_alt": AKd,
        "kasnaklar": kasnaklar,
        "kasnak_capi": kasnak_capi,
        "kotlar": kotlar,
    }


AD = {
    "siginma": "Sığınma yüksekliği",
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


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _kot(z):
    """Kot yazısı ( m ):  Türkçe ondalık virgülle — "±0,00", "+3,40"."""
    m = z / 1000.0
    return "±0,00" if abs(m) < 5e-4 else f"{m:+.2f}".replace(".", ",")


def _kabin(e, kt, kabin_y, ry, S, kasnaklar_y=None, kasnak_capi=0, kr_b=89, esik_on=None):
    """Kabinin kesiti:  gövde, taban, etek, şase, patenler, fren bloğu, kasnak.
    esik_on:  kabin eşiğinin kat tarafındaki kenarı ( önlük orada asılıdır;
    verilmezse kabinin ön yüzü )."""
    y0, y1 = kabin_y
    D = CEL.dikdortgen
    e.append(CEL.ad(D("KABIN", y0, kt["taban_alti"], y1 - y0, kt["tavan"] - kt["taban_alti"]), "kabin"))
    e.append(D("KABIN-IC", y0, kt["doseme"], y1 - y0, kt["ic_ust"] - kt["doseme"]))
    #  Etek ( önlük, m.5.4.5 ):  kabin eşiğinin kat tarafındaki kenarından iner,
    #  dik kısmın altında pahla kabine döner ( eskiden kabinin ön yüzündeydi,
    #  eşiğin 90 gerisinde, pahsız )
    u = y0 if esik_on is None else esik_on
    ust = kt["doseme"] - S["esik_kalinlik"]
    et = CEL.ad(D("KABIN", u, kt["etek_alti"], CP.ONLUK_PAH, ust - kt["etek_alti"]), "etek")
    et["bicim"] = CP.pahli_sac(u, ust, ust - kt["etek_dik_alti"], u + CP.ONLUK_PAH, dz=CP.ONLUK_PAH_DUSEY)
    e.append(et)
    #  Şase:  ray ekseninde dikme, alt ve üst kiriş ( kabin_kotlari )
    #  Dikme iki ince profil olarak çizilir ( referans proje:  50 + 200 + 50 —
    #  parcalar.SASE_PROFIL_ENI;  plandaki kirişlerle aynı );  dolu çizilince
    #  kabinin kesitini örtüyordu.  Yandan bakışta kirişlerin iki C profili
    #  dikmelerin hizasında, uçlarıyla görünür ( LiftDesigner 4815-6 kuyu tepesi:
    #  40 + 160 + 40, 140 yüksek ).
    sd = S["sase_dikme_derinlik"]
    pe = min(CP.SASE_PROFIL_ENI, sd / 2.0)
    for x in (ry - sd / 2.0, ry + sd / 2.0 - pe):
        e.append(
            CEL.ad(
                D("KABIN-IC", x, kt["alt_kiris_alt"], pe, kt["ust_kiris_ust"] - kt["alt_kiris_alt"]), "sase"
            )
        )
        for z0, z1 in (
            (kt["alt_kiris_alt"], kt["alt_kiris_ust"]),
            (kt["ust_kiris_alt"], kt["ust_kiris_ust"]),
        ):
            e.append(CEL.ad(D("KABIN-IC", x, z0, pe, z1 - z0), "sase_kiris"))
    #  Patenler ve fren bloğu
    e.append(CEL.ad(D("PATEN", ry - 35, kt["ust_paten_alt"], 70, S["paten_yukseklik"]), "ust_paten"))
    e.append(CEL.ad(D("PATEN", ry - 35, kt["alt_paten"], 70, S["paten_yukseklik"]), "alt_paten"))
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(CEL.ad(D("SASE", x, kt["fren_alti"], 50, S["fren_blogu_yukseklik"]), "fren"))
    #  Kabin kasnağı ( 2:1 kabin altı ):  kesitte yandan, çapı düşey
    for ky in kasnaklar_y or ():
        e.append(
            CEL.ad(
                D(
                    "KASNAK",
                    ky - S["kabin_kasnak_genislik"] / 2.0,
                    kt["kasnak_merkez"] - kasnak_capi / 2.0,
                    S["kabin_kasnak_genislik"],
                    kasnak_capi,
                ),
                "kabin_kasnak",
            )
        )
