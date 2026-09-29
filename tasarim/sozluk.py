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
             Formda kutuları yoktur ama aynı büyüklüğü çizim de bilir.  3. adımda
             yerleşimin ölçü listesi ( cizim/olculer.py ) xc · xi · ray ve halat
             boyları · kasnak sayıları · makinenin kirişteki yeri için bunları
             çizimden verdi;  sabitler yalnız çizim kurulamazsa yedek kalır
             ( raporda KABUL yazar ).

Durumlar:  "iki" iki kaynak · "yok" çizimde yok · "incele" bakılacak.
"""
from tasarim.alanlar import ALANLAR, ALAN, GRUPLAR, CIZIM

IKI, YOK, INCELE, TEK = "iki", "yok", "incele", "tek"

#  anahtar → ( durum , not , karar no )
SORUNLAR = {
    "yan_yatak_boyu": (IKI, "Makine dairesizde raylara oturan kirişin açıklığı ağırlık rayları "
                            "arasıdır ( DBGW );  yan yatak boyu ondan ayrıysa çizim uyuşmazlığı "
                            "söyler, hesap makinenin yerini ofis kabulüyle ( L − 335 ) alır.  "
                            "\"Bina yapısına\" oturan kiriş henüz çizilmiyor.", 3),
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
