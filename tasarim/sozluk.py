# -*- coding: utf-8 -*-
"""
SAYI SÖZLÜĞÜ — programdaki her sayının kaynağı ve açık sorunlar

Satırlar tasarım şemasından ( tasarim/alanlar.py ) üretilir:  alanın grubu,
kaynağı, formda olup olmadığı şemadadır, burada ikinci kez yazılmaz.  Bu
dosya yalnız şemanın bilmediği iki şeyi tutar:

  SORUNLAR   şemadaki bir alanın hâlâ açık sorunu ( hesapla çizim aynı şeye
             iki sayı veriyor ya da çizim hesabın varsaydığını gösteremiyor ).
             Sorun çözülünce satır buradan silinir.
  ICSEL      hesabın içinde geometri TAHMİN eden sabitler ve formüller.
             Formda kutuları yoktur ama aynı büyüklüğü çizim de bilir;
             yerleşimin ölçü listesi ( 3. adım ) bunları çizimden verince silinir.

Durumlar:  "iki" iki kaynak · "yok" çizimde yok · "incele" bakılacak.
"""
from tasarim.alanlar import ALANLAR, ALAN, GRUPLAR, CIZIM

IKI, YOK, INCELE, TEK = "iki", "yok", "incele", "tek"

#  anahtar → ( durum , not , karar no )
SORUNLAR = {
    "kasnak_tek_yon": (IKI, "Askı oranından sayılıyor ( 1:1 → 1, 2:1 → 2 ); çizilen kasnaklardan "
                            "sayılmalı — saptırmasız 1:1'de hesap 1, çizimde 0.", None),
    "kasnak_ters_yon": (IKI, "Ters bükülme çizimdeki kasnak dizilişinden sayılmalı.", None),
    "yan_yatak_boyu": (IKI, "Makine dairesizde çizimdeki kiriş 1.136 mm ve raylara oturuyor; "
                            "hesap 1.400 açıklıkla eğiliyor.", None),
    "makine_raya_biniyor": (YOK, "Çizim makine kirişlerini her zaman raylara oturtuyor; "
                                 "\"Bina yapısına\" ( duvardan duvara kiriş ) çizilmiyor.", 3),
    "paten_tipi": (YOK, "Çizim yalnız kaymalı patenin ölçüsünü biliyor ( 140 mm ).", 2),
    "agirlik_paten_tipi": (YOK, "Çizim yalnız kaymalı patenin ölçüsünü biliyor.", 2),
    "paten_balata_boyu": (INCELE, "Hesaptaki balata ile çizimdeki paten boyu ( 100 mm ) aynı parça mı.",
                          None),
    "agirlik_yeri": (YOK, "Arkada karşı ağırlıkla 2:1 çizilemiyor ( makine dairesizde kabin altında "
                          "çapraz kasnaklar, makine dairelide kabin üstünde iki kasnak ).", 4),
    "kanal_sekli": (YOK, "Çift sarımda çizim duruyor.", 6),
    "uzun_pervaz": (YOK, "Kabin girişi girintisi çizilmiyor; yalnız 100 mm'yi aşarsa kabin "
                         "alanına girer.", 8),
    "denge_zinciri": (YOK, "Hesapta var, çizimde yok.", 9),
    "agirlik_malzemesi": (YOK, "Dolgunun çerçeveye sığdığı denetlenmiyor.", 11),
}

#  ( ad , hesaptaki yeri , grup , not , durum , karar no )
ICSEL = (
    ("Kabin merkezinin ray eksenine uzaklığı ( xc )", "hesap içi sabit:  kabin_merkez_payi = 130",
     "Kabin ve kapı", "Hesap derinlik/2 + 130 − RK kullanıyor, çizim eşik arası + kabin eşiği + "
     "arka pano/2;  varsayılan projede 155 ↔ 161,5 mm.", IKI, None),
    ("Eşik kuvvetinin noktası ( xi )", "hesap:  −ray_kapi_arasi",
     "Kabin ve kapı", "m.5.7.2.3.6 kuvveti kabin girişinin eşiğinin ortasına koyar;  hesap "
     "−650, çizim −575 mm.", IKI, None),
    ("Ray boyu ( ray ağırlığı için )", "hesap içi:  ray_kaide_payi 200 · ray_kuyu_payi 300",
     "Raylar ve patenler", "Makine dairesizde 26.300 ↔ 26.150, makine dairelide "
     "27.500 ↔ 26.600 mm.", IKI, None),
    ("Askı halatı boyu ( halat ağırlığı için )", "hesap içi:  kuyu boyu − yığın + halat_pay_m",
     "Askı ve halatlar", "Halatın çizimdeki yolundan ölçülmeli.", IKI, None),
    ("Regülatör halatı boyu", "hesap içi:  ( alt duraktan tavana + tabliye − 200 ) × 2",
     "Hız regülatörü", "Makine dairesizde 50,0 ↔ 52,6 m, makine dairelide 52,4 ↔ 56,3 m.",
     IKI, None),
    ("Atalete giren kasnaklar", "ofis:  kasnak_adet_kabin 2 · kasnak_adet_agirlik 1",
     "Askı ve halatlar", "Makine dairesindeki saptırma kasnağının ataleti hesapta hep 0.",
     IKI, None),
    ("Makinenin kiriş üstündeki yeri ( X = L − 335 )", "ofis:  yan_yatak_L_X = 335",
     "Makine", "Makinenin kirişteki yeri çizimde belli.", IKI, None),
    ("Revizyon kutusu", "ofis:  revizyon_payi = 500",
     "Kabin ve kapı", "Bölüm 11'in bu satırını hesap kendisi hesaplıyor; kutu çizimde yok.",
     YOK, 10),
)


def satirlar():
    """Sözlüğün satırları, tasarım sırasıyla:  şemadaki her alan + hesabın
    içindeki tahminler.  Her satır bir sözlük:  grup · ad · anahtar · kaynak ·
    formda · sozlesme · durum · not · karar."""
    out = []
    for g in GRUPLAR:
        for a in ALANLAR:
            if a.grup != g:
                continue
            durum, notu, karar = SORUNLAR.get(a.anahtar, (TEK, "", None))
            if not a.formda and a.kaynak == CIZIM and durum == TEK:
                notu = "Formda kutusu yok:  değer çizimden gelir."
            out.append({"grup": g, "ad": a.etiket, "anahtar": a.anahtar, "kaynak": a.kaynak,
                        "formda": a.formda, "gelismis": a.gelismis, "sozlesme": a.sozlesme,
                        "yerlesim": a.yerlesim, "durum": durum, "not": notu, "karar": karar})
        for ad, yeri, grup, notu, durum, karar in ICSEL:
            if grup == g:
                out.append({"grup": g, "ad": ad, "anahtar": yeri, "kaynak": CIZIM, "formda": False,
                            "gelismis": False, "sozlesme": "mukavemet", "yerlesim": None,
                            "durum": durum, "not": notu, "karar": karar})
    return out


def _denetle():
    for k in SORUNLAR:
        assert k in ALAN, f"sözlükteki sorun şemada yok: {k}"
    for _ad, _y, grup, *_x in ICSEL:
        assert grup in GRUPLAR, grup


_denetle()
