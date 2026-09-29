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
from cizim import donanim as CDN
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kabin_ustu as CKU
from cizim import kuyu_dibi as CKD
from cizim import sabitler as CS

#  Çizelge 3 / Çizelge 4 — sığınma alanının YÜKSEKLİĞİ ( mm )
SIGINMA_UST_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0}
SIGINMA_DIP_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0}
DIP_EN_ALT = 500.0          # m.5.2.5.8.2 a
DIP_ETEK = 100.0            # m.5.2.5.8.2 a 1)
DIP_RAYA_YAKIN = 100.0      # m.5.2.5.8.2 a 2) · Şekil 7  ( XH ≤ 0,15 m )
UST_PATEN = 100.0           # m.5.2.5.7.2 b
UST_DONANIM = 500.0         # m.5.2.5.7.2 a  kabin tavanına bağlı donanım ( kabin üstü kasnaklar )
UST_KORKULUK = 300.0        # m.5.2.5.7.2 c 1)  kabin izdüşümünde
UST_KORKULUK_DIS = 100.0    # m.5.2.5.7.2 c 1)  korkuluğun dışında
YATAY_UZAKLIK = 400.0       # m.5.2.5.7.2 b / c 1)  "0,40 m yatay uzaklık içinde"
RAY_UZANTISI = 100.0        # m.5.2.5.6.2  ( en üst konum m.5.2.5.6.1:  + 0,035·v² )
ETEK_BOYU = CDN.ETEK_BOYU   # m.5.4.5.1:  kabin eteğinin düşey kısmı en az 0,75 m
ESIK_ARASI = 11000.0        # m.5.2.3.1:  ardışık kat kapısı eşikleri arası
DUSEY_ALANLAR = ("kabin_ic_yukseklik", "kabin_paten_arasi", "agirlik_paten_arasi", "son_kat", "beyan_hizi",
                 "kabin_tampon_baba", "kabin_tampon_boyu",
                 "kabin_carpma_arasi", "kabin_tampon_ezilme", "agirlik_tampon_baba",
                 "agirlik_tampon_boyu", "agirlik_carpma_arasi", "agirlik_tampon_ezilme")


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def durak_kotlari(g):
    """Durakların döşeme kotları ( en alt durak ±0 ) ve girdi hataları.

    kat_yuksekligi tek sayıysa bütün katlar o yükseklikte;  liste ise alttan
    üste ardışık iki durak arası ( durak_adedi − 1 tane ).  Referans projede
    hepsi 2.900;  LiftDesigner örneğinde 3.400, 3.400, 3.000 … karışık.
    """
    dy, kp = g.get("dusey") or {}, g.get("kapi") or {}
    n, kh = dy.get("durak_adedi"), dy.get("kat_yuksekligi")
    if not (_sayi(n) and n == int(n) and n >= 2):
        return [], [f"dusey.durak_adedi:  2 ya da daha büyük bir tam sayı olmalı ( {n!r} )."]
    n = int(n)
    araliklar = [kh] * (n - 1) if _sayi(kh) else kh
    if not (isinstance(araliklar, (list, tuple)) and len(araliklar) == n - 1
            and all(_sayi(h) and h > 0 for h in araliklar)):
        return [], [f"dusey.kat_yuksekligi:  sıfırdan büyük bir sayı ya da {n - 1} "
                    f"sayılık bir liste olmalı ( {kh!r} )."]
    hata = []
    kapi_h = kp.get("yukseklik") or 0
    for i, h in enumerate(araliklar):
        ad = f"{i + 1}. – {i + 2}. durak arası {h:g} mm"
        if h <= kapi_h:
            hata.append(f"{ad}:  kat kapısı yüksekliğinden ( {kapi_h:g} ) büyük olmalı — "
                        f"kapı üstteki durağın döşemesine giriyor.")
        if h > ESIK_ARASI:
            hata.append(f"{ad} > {ESIK_ARASI:g} mm:  ara acil kapı gerekir "
                        f"( TS EN 81-20 m.5.2.3.1 );  bu çizim acil kapı çizmez.")
    kotlar = [0.0]
    for h in araliklar:
        kotlar.append(kotlar[-1] + h)
    return kotlar, hata


def _korkuluk_cizgileri(KU):
    """Gerekli korkulukların plandaki çizgileri ( ince kutu )."""
    return [k for k, _ in CKU.korkuluklar(KU)]


kabin_kotlari = CDN.kabin_kotlari


def yerlesim(g, cizim_sabitleri=None):
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    dy = g.get("dusey") or {}
    hata = [f"dusey.{a}: sıfırdan büyük bir sayı olmalı ( {dy.get(a)!r} )."
            for a in DUSEY_ALANLAR if not (_sayi(dy.get(a)) and dy[a] > 0)]
    kotlar, durak_hata = durak_kotlari(g)
    hata += durak_hata
    #  Çizilemeyen askı / ağırlık birleşimi ilk söylenir ( öbür planların
    #  hataları onun sonucudur )
    from cizim import kuyu_ustu as CKT
    hata += CKT.duzen_hatalari(g)
    if hata:
        return {"hata": hata}
    #  Karşı ağırlık çerçevesinin yüksekliği paten arasıdır:  kasnağını ( üst
    #  kirişin agirlik_kasnak_ust altında ) ve patenlerini taşıyacak kadar olmalı
    R = (g["agirlik"].get("kasnak_capi") or 0) / 2.0
    if dy["agirlik_paten_arasi"] <= max(S["paten_yukseklik"], S["agirlik_kasnak_ust"] + R):
        return {"hata": [f"dusey.agirlik_paten_arasi:  karşı ağırlık çerçevesinin yüksekliğidir "
                         f"( patenler uçlarında );  {dy['agirlik_paten_arasi']:g} mm kasnağına ve "
                         "patenlerine yetmiyor."]}
    if dy["kabin_paten_arasi"] <= S["paten_yukseklik"]:
        return {"hata": ["Kabin patenleri üst üste biniyor."]}
    KD, KU = CKD.yerlesim(g, S), CKU.yerlesim(g, S)
    if KD["hata"] or KU["hata"]:
        return {"hata": KD["hata"] + KU["hata"]}
    kd, ku = g["kuyu_dibi"], g["kabin_ustu"]
    v = dy["beyan_hizi"]
    b35 = 35.0 * v * v                                   # 0,035 · v² · 1000

    #  ── KUYU DİBİ:  kabin tam ezilmiş tamponunda ──────────────────────
    KY = kd["derinlik"]
    #  Kuyu dibi zinciri kabinin şase altıyla kapanmalı:  kaide + tampon +
    #  çarpma arası + şase altı = kuyu dibi ( referans proje:  764 + 160 + 96 + 480 )
    zincir = dy["kabin_tampon_baba"] + dy["kabin_tampon_boyu"] + dy["kabin_carpma_arasi"] + \
        S["sase_alt_derinlik"]
    if abs(zincir - KY) > 0.5:
        hata.append(
            f"Kuyu dibi {KY:g} mm, ama kaide {dy['kabin_tampon_baba']:g} + tampon "
            f"{dy['kabin_tampon_boyu']:g} + çarpma arası {dy['kabin_carpma_arasi']:g} + kabinin "
            f"şase altı {S['sase_alt_derinlik']:g} = {zincir:g} mm — girdiler kabinle çelişiyor.")
    aski = g.get("aski") or {}
    dip = kabin_kotlari(dy, S, -(dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"]), aski)
    taban = -KY
    #  Kabin kasnaklarının planda sığınma alanının üstüne düşüp düşmediği
    #  ( yalnız kabin altı askıda kasnaklar kabinin altındadır )
    kasnaklar = [_kutu(el) for el in KU["taban"] if el.get("ad") == "kabin_kasnak"] \
        if aski.get("duzen") == "Kabin altı" else []
    kasnak_capi = (g.get("aski") or {}).get("kasnak_capi") or 0
    sg = KD["siginma"]
    ustunde_kasnak = bool(kasnaklar) and any(k[0] < sg[2] and sg[0] < k[2] for k in kasnaklar)
    kasnak_alti = dip["kasnak_merkez"] - kasnak_capi / 2.0
    en_alt = min(dip["taban_alti"], kasnak_alti) if kasnaklar else dip["taban_alti"]
    siginma_ustu = min(dip["taban_alti"], kasnak_alti) if ustunde_kasnak else dip["taban_alti"]
    dip_aciklik = {
        "siginma": (siginma_ustu - taban, SIGINMA_DIP_YUKSEKLIK[kd["siginma_tipi"]],
                    "m.5.2.5.8.1 · Çizelge 4"),
        "en_alt": (en_alt - taban, DIP_EN_ALT, "m.5.2.5.8.2 a"),
        "etek": (dip["etek_alti"] - taban, DIP_ETEK, "m.5.2.5.8.2 a 1"),
        "sase": (min(dip["alt_paten"], dip["fren_alti"]) - taban, DIP_RAYA_YAKIN,
                 "m.5.2.5.8.2 a 2 · Şekil 7"),
    }

    #  ── KUYU ÜSTÜ:  kabin en üst konumunda ────────────────────────────
    #  Karşı ağırlık tam ezilmiş tamponunda + 0,035·v²  ( m.5.2.5.6.1 )
    H = kotlar[-1]
    M = CDN.yerlesim(g, S, H, H + dy["son_kat"], -KY)
    if M["hata"]:
        return {"hata": hata + M["hata"]}
    yukselme = dy["agirlik_carpma_arasi"] + dy["agirlik_tampon_ezilme"] + b35
    ust = kabin_kotlari(dy, S, yukselme, aski)
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
    patenler = [_kutu(el) for el in KD["taban"] if el["katman"] == "PATEN"]
    pt_engel = min(engel(genislet(p, YATAY_UZAKLIK)) for p in patenler)
    ust_engel = {"siginma": sg_engel, "paten": pt_engel, "ray": (ray_ustu, "ray")}
    ust_aciklik = {
        "siginma": (sg_engel[0] - ust["tavan"], SIGINMA_UST_YUKSEKLIK[ku["siginma_tipi"]],
                    "m.5.2.5.7.1 · Çizelge 3"),
        "paten": (pt_engel[0] - ust["ust_paten"], UST_PATEN, "m.5.2.5.7.2 b"),
        "ray": (ray_ustu - ust["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2"),
    }
    #  KABİN ÜSTÜ ASKIDA kasnaklar kabin tavanına bağlı donanımdır:  en yüksek
    #  noktaları ile kabinin izdüşümündeki en alt tavan parçası arası en az
    #  0,50 m ( m.5.2.5.7.2 a ).
    if aski.get("duzen") == "Kabin üstü":
        ku_kasnak = [_kutu(el) for el in KU["taban"] if el.get("ad") == "kabin_kasnak"]
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
        hy = g["kabin"]["on_pay"] + (g["kabin"]["derinlik"] + S["kabin_pano_arka"]) / 2.0 + \
            aski.get("nokta_kaciklik", 0)
        dk = CMK.halat_deligi(hx, hy, aski.get("halat_adedi") or 1, aski.get("halat_capi") or 0, 0.0)
        bg_engel = engel(genislet(dk, YATAY_UZAKLIK))
        ust_engel["baglanti"] = bg_engel
        ust_aciklik["baglanti"] = (bg_engel[0] - ust["baglanti_ust"], UST_PATEN, "m.5.2.5.7.2 b")
    if korkuluk:
        #  Korkuluğun 0,40 m yakınındaki tavan parçaları:  kabin izdüşümündeyse
        #  0,30, dışındaysa 0,10  ( m.5.2.5.7.2 c 1 )
        k_ust = ust["tavan"] + korkuluk
        adaylar = [(tavan_alti, "kuyu tavanı", UST_KORKULUK)]
        for kenar in _korkuluk_cizgileri(KU):
            bolge = genislet(kenar, YATAY_UZAKLIK)
            for ad, p, z in M["parcalar"]:
                if CDN._ortusur(p, bolge):
                    icinde = CDN._ortusur(p, kabin_izi)
                    adaylar.append((z - H, ad, UST_KORKULUK if icinde else UST_KORKULUK_DIS))
        z, ad, asgari = min(adaylar, key=lambda a: a[0] - k_ust - a[2])
        ust_engel["korkuluk"] = (z, ad)
        ust_aciklik["korkuluk"] = (z - k_ust, asgari, "m.5.2.5.7.2 c")
    #  Karşı ağırlık en üst konumunda:  kabin tam ezilmiş tamponunda + 0,035·v²
    ag_alt = (M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"] + H
              + dy["kabin_carpma_arasi"] + dy["kabin_tampon_ezilme"] + b35)
    AK = CDN.agirlik_kotlari(M, ag_alt)
    ag_ray = min(r["ust"] for r in M["raylar"] if r["tur"] == "agirlik")
    ust_aciklik["agirlik_ray"] = (ag_ray - AK["ust_paten"], RAY_UZANTISI, "m.5.2.5.6.2")
    if M["mrl"] and CDN._ortusur(M["agirlik"]["kutu"], M["sase"][:4]):
        ag_tepe = max(AK["ust_paten"], AK["kasnak_merkez"] + (g["agirlik"].get("kasnak_capi") or 0) / 2.0)
        if ag_tepe > M["sase"][4] + 1e-9:
            hata.append(f"Karşı ağırlık en üst konumunda makine şasesine çarpıyor:  tepesi "
                        f"{ag_tepe - H:g} mm, şasenin altı {M['sase'][4] - H:g} mm ( son kattan ).")
    #  Açıklık dışındaki fiziksel hatalar ( kuyu dibi zinciri, ağırlığın
    #  şaseye çarpması ):  hesabın bölüm 11'i açıklıkları sözlüklerden okur,
    #  bunları ayrıca basar.
    diger = list(hata)
    for ad, (deger, asgari, madde) in list(dip_aciklik.items()) + list(ust_aciklik.items()):
        if deger < asgari - 1e-9:
            hata.append(f"{AD[ad]}:  {deger:g} mm < {asgari:g} mm  ( TS EN 81-20 {madde} ).")
    return {"hata": hata, "diger": diger, "S": S, "KD": KD, "KU": KU, "M": M, "dip": dip, "ust": ust,
            "taban": taban,
            "tavan_alti": tavan_alti, "ray_ustu": ray_ustu, "yukselme": yukselme,
            "ust_engel": ust_engel, "agirlik_ust": AK,
            "korkuluk": korkuluk, "dip_aciklik": dip_aciklik, "ust_aciklik": ust_aciklik,
            "kasnaklar": kasnaklar, "kasnak_capi": kasnak_capi, "kotlar": kotlar}


AD = {"siginma": "Sığınma yüksekliği", "en_alt": "Kuyu tabanı – kabinin en alt kısmı",
      "etek": "Kuyu tabanı – kabin eteği", "sase": "Kuyu tabanı – şase / paten / fren bloğu",
      "paten": "Üst paten – kuyu tavanı", "ray": "Üst paten – rayın üst ucu",
      "kasnak": "Kabin üstü kasnağı – kuyu tavanı",
      "baglanti": "Kabindeki halat bağlantısı – kuyu tavanı",
      "korkuluk": "Korkuluk – kuyu tavanı",
      "agirlik_ray": "Karşı ağırlık üst pateni – rayın üst ucu"}


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _kot(z):
    m = z / 1000.0
    return "±0.00" if abs(m) < 5e-4 else f"{m:+.2f}"


def _kabin(e, kt, kabin_y, ry, S, kasnaklar_y=None, kasnak_capi=0, kr_b=89):
    """Kabinin kesiti:  gövde, taban, etek, şase, patenler, fren bloğu, kasnak."""
    y0, y1 = kabin_y
    D = CGE._dik
    e.append(CGE._ad(D("KABIN", y0, kt["taban_alti"], y1 - y0, kt["tavan"] - kt["taban_alti"]), "kabin"))
    e.append(D("KABIN-IC", y0, kt["doseme"], y1 - y0, kt["ic_ust"] - kt["doseme"]))
    #  Etek:  kabin eşiğinin altında, ön yüzde
    e.append(CGE._ad(D("KABIN", y0, kt["etek_alti"], 30, kt["taban_alti"] - kt["etek_alti"]), "etek"))
    #  Şase:  ray ekseninde dikme, alt ve üst kiriş
    #  Dikme iki ince profil olarak çizilir ( referans proje:  50 + 200 + 50 );
    #  dolu çizilince kabinin kesitini örtüyordu.
    sd = S["sase_dikme_derinlik"]
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(CGE._ad(D("KABIN-IC", x, kt["sase_alt"], 50, kt["sase_ust"] - kt["sase_alt"]), "sase"))
    for z in (kt["sase_alt"], kt["sase_ust"] - 10):
        e.append(D("KABIN-IC", ry - sd / 2.0, z, sd, 10))
    #  Patenler ve fren bloğu
    e.append(CGE._ad(D("PATEN", ry - 35, kt["ust_paten_alt"], 70, S["paten_yukseklik"]), "ust_paten"))
    e.append(CGE._ad(D("PATEN", ry - 35, kt["alt_paten"], 70, S["paten_yukseklik"]), "alt_paten"))
    for x in (ry - sd / 2.0, ry + sd / 2.0 - 50):
        e.append(CGE._ad(D("SASE", x, kt["fren_alti"], 50, S["fren_blogu_yukseklik"]), "fren"))
    #  Kabin kasnağı ( 2:1 kabin altı ):  kesitte yandan, çapı düşey
    for ky in kasnaklar_y or ():
        e.append(CGE._ad(D("KASNAK", ky - S["kabin_kasnak_genislik"] / 2.0,
                             kt["kasnak_merkez"] - kasnak_capi / 2.0,
                             S["kabin_kasnak_genislik"], kasnak_capi), "kabin_kasnak"))
