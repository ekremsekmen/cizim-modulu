# -*- coding: utf-8 -*-
"""Asansör proje kapağını ( avan · uygulama ) doğrudan vektör PDF olarak üretir.

Bu modül hesap motorundan ve mevcut PDF raporlarından bağımsızdır. Pafta
çizgileri ile metinler tek adımda ReportLab tarafından çizilir; kaynak PDF,
arka plan veya ikinci bir katman kullanılmaz.
"""

from __future__ import annotations

import io
import os
from collections.abc import Mapping

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


SAYFA_EN, SAYFA_BOY = A4
SIYAH = HexColor("#000000")
YAZI_TIPI = "KapakGov"
KALIN_YAZI_TIPI = "KapakGovBold"
YAZI_TIPI_KLASORU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")


def _yazi_tipleri():
    if YAZI_TIPI in pdfmetrics.getRegisteredFontNames():
        return YAZI_TIPI, KALIN_YAZI_TIPI
    normal = os.path.join(YAZI_TIPI_KLASORU, "DejaVuSans.ttf")
    kalin = os.path.join(YAZI_TIPI_KLASORU, "DejaVuSans-Bold.ttf")
    if os.path.exists(normal) and os.path.exists(kalin):
        pdfmetrics.registerFont(TTFont(YAZI_TIPI, normal))
        pdfmetrics.registerFont(TTFont(KALIN_YAZI_TIPI, kalin))
        return YAZI_TIPI, KALIN_YAZI_TIPI
    return "Helvetica", "Helvetica-Bold"


YAZI, KALIN_YAZI = _yazi_tipleri()


def _tek_satir(deger) -> str:
    return " ".join(str(deger or "").replace("\n", " ").split())


def _y(ust_kot: float) -> float:
    return SAYFA_BOY - ust_kot


def _ayni(kot):
    return kot


def _kot(c, kot):
    """Formun kotu ( tek asansörlü kapağın puntosu ) → bu kapaktaki yeri.

    Çok asansörlü kapakta asansör tabloları alt alta dizilir ve altlarındaki
    kutular aşağı kayar ( bkz. yerlesim ).  Çizim işlevleri formun kendi
    kotlarıyla yazılmıştır;  kaydırma burada, tek yerde yapılır.  Eşleme
    tuvalin üstünde durur:  sunucu istekleri iş parçacıklarında aynı anda
    basar, modül düzeyinde bir değişken birbirine karışırdı."""
    return getattr(c, "kapak_kotu", _ayni)(kot)


def _sigan_punto(metin: str, en: float, boyut: float, en_kucuk: float = 4.3, yazi_tipi=YAZI) -> float:
    #  Kalın yazı kendi eniyle ölçülür:  normalin eniyle ölçülen kalın etiket
    #  ( "1. ASANSÖR" ) yandaki hücreye taşıyordu.
    while boyut > en_kucuk and pdfmetrics.stringWidth(metin, yazi_tipi, boyut) > max(en - 2, 1):
        boyut -= 0.2
    return max(boyut, en_kucuk)


#  BİRDEN ÇOK ASANSÖRÜN DEĞERİ  ( "1450/1350" · "0,63 / 1,00 / 1,60 m/s" )
#  en küçük puntoda bile hücreye sığmazsa YANDAKİ HÜCREYE TAŞMAZ:  ayraçtan
#  iki satıra bölünür.  Kabin derinliği hücresi 17 pt'dir — iki kabin
#  ölçüsü tek satırda "Standart" hücresinin üstüne biniyordu.  Tek satıra
#  sığan metin eskisi gibi tek satır basılır.
IKI_SATIR_EN_KUCUK = 3.2


def _satirlar(metin, en, boyut, hucre_boyu, yazi_tipi=YAZI):
    """( satırlar, punto ) — tek satır sığmıyorsa ayraçtan dengeli iki satır."""
    tek = _sigan_punto(metin, en, boyut, yazi_tipi=yazi_tipi)
    if pdfmetrics.stringWidth(metin, yazi_tipi, tek) <= max(en - 2, 1):
        return [metin], tek
    ayrac = " / " if " / " in metin else "/" if "/" in metin else None
    if ayrac is None:
        return [metin], tek
    parca = metin.split(ayrac)
    k = (len(parca) + 1) // 2
    iki = [ayrac.join(parca[:k]) + ayrac.rstrip(), ayrac.join(parca[k:])]
    #  İki satır hücre yüksekliğine sığmalı:  satır aralığı ~ 1,05 punto.
    punto = min(
        min(_sigan_punto(x, en, boyut, IKI_SATIR_EN_KUCUK, yazi_tipi) for x in iki), (hucre_boyu - 0.6) / 2.1
    )
    if all(pdfmetrics.stringWidth(x, yazi_tipi, punto) <= max(en - 2, 1) for x in iki):
        return iki, punto
    return [metin], tek


def _yaz(c, satirlar, yazi_tipi, yazi_boyu, sol_kenar, ust_kot, alt_kot):
    """Satırları hücrenin düşey ortasına dizer;  x_of( satır ) → sol kenar."""
    ara = yazi_boyu * 1.05
    orta = (ust_kot + alt_kot) / 2
    for i, satir in enumerate(satirlar):
        dy = (i - (len(satirlar) - 1) / 2) * ara
        c.drawString(sol_kenar(satir), _y(orta + dy) - yazi_boyu * 0.33, satir)


def _ortala(c, deger, x0, x1, ust_kot, alt_kot, boyut=7.0, renk=SIYAH, kalin=False):
    metin = _tek_satir(deger)
    if not metin:
        return
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    yazi_tipi = KALIN_YAZI if kalin else YAZI
    satirlar, yazi_boyu = _satirlar(metin, x1 - x0, boyut, abs(alt_kot - ust_kot), yazi_tipi)
    c.setFont(yazi_tipi, yazi_boyu)
    c.setFillColor(renk)
    _yaz(
        c,
        satirlar,
        yazi_tipi,
        yazi_boyu,
        lambda t: x0 + max(1.1, ((x1 - x0) - pdfmetrics.stringWidth(t, yazi_tipi, yazi_boyu)) / 2),
        ust_kot,
        alt_kot,
    )


def _sola(c, deger, x0, x1, ust_kot, alt_kot, boyut=6.4, renk=SIYAH, bosluk=2.0, kalin=False):
    metin = _tek_satir(deger)
    if not metin:
        return
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    yazi_tipi = KALIN_YAZI if kalin else YAZI
    satirlar, yazi_boyu = _satirlar(metin, x1 - x0 - bosluk * 2, boyut, abs(alt_kot - ust_kot), yazi_tipi)
    c.setFont(yazi_tipi, yazi_boyu)
    c.setFillColor(renk)
    _yaz(c, satirlar, yazi_tipi, yazi_boyu, lambda _t: x0 + bosluk, ust_kot, alt_kot)


def _sarili(c, deger, x0, x1, ust_kot, alt_kot, boyut=5.7, renk=SIYAH, bosluk=2.0):
    metin = _tek_satir(deger)
    if not metin:
        return
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    kelimeler = metin.split()
    en = x1 - x0 - bosluk * 2
    #  SATIR BÜTÇESİ KUTUNUN GERÇEK YÜKSEKLİĞİNDEN TÜRETİLİR.  Eskiden 2'ye
    #  sabitlenmişti:  124 karakterlik normal bir adreste "İstanbul Türkiye
    #  34758" bölümü çıktıdan SESSİZCE düşüyordu.  Kutu daha küçük puntoda
    #  3 satır alabiliyor; yine sığmazsa kırpma artık GÖRÜNÜR ( … ).
    yukseklik = abs(alt_kot - ust_kot)

    def _sar(punto):
        satirlar, gecerli = [], ""
        for word in kelimeler:
            aday = f"{gecerli} {word}".strip()
            if gecerli and pdfmetrics.stringWidth(aday, YAZI, punto) > en:
                satirlar.append(gecerli)
                gecerli = word
            else:
                gecerli = aday
        if gecerli:
            satirlar.append(gecerli)
        return satirlar

    def _azami(punto):
        return max(1, int(yukseklik // (punto * 1.15)))

    yazi_boyu = boyut
    dizi = _sar(yazi_boyu)
    while yazi_boyu > 4.3 and len(dizi) > _azami(yazi_boyu):
        yazi_boyu -= 0.2
        dizi = _sar(yazi_boyu)
    if len(dizi) > _azami(yazi_boyu):
        #  En küçük puntoda bile sığmıyor — kırpıldığı ÇIKTIDA görünsün.
        dizi = dizi[: _azami(yazi_boyu)]
        dizi[-1] = dizi[-1].rstrip() + " …"
    dizi = dizi or [metin]
    satir_araligi = yazi_boyu * 1.15
    taban = _y((ust_kot + alt_kot) / 2) + (len(dizi) - 1) * satir_araligi / 2 - yazi_boyu * 0.33
    c.setFont(YAZI, yazi_boyu)
    c.setFillColor(renk)
    for i, dizi_satiri in enumerate(dizi):
        c.drawString(x0 + bosluk, taban - i * satir_araligi, dizi_satiri)


def _dikey(c, metin, x0, x1, ust_kot, alt_kot, boyut=6.0):
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    c.saveState()
    c.setFont(YAZI, boyut)
    c.setFillColor(SIYAH)
    c.translate((x0 + x1) / 2, _y((ust_kot + alt_kot) / 2))
    c.rotate(90)
    c.drawCentredString(0, -boyut * 0.33, metin)
    c.restoreState()


def _yatay(c, x0, x1, ust_kot, en=0.45):
    ust_kot = _kot(c, ust_kot)
    c.setLineWidth(en)
    c.line(x0, _y(ust_kot), x1, _y(ust_kot))


def _dusey(c, x, ust_kot, alt_kot, en=0.45):
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    c.setLineWidth(en)
    c.line(x, _y(ust_kot), x, _y(alt_kot))


def _kutu(c, x0, ust_kot, x1, alt_kot, en=0.45):
    ust_kot, alt_kot = _kot(c, ust_kot), _kot(c, alt_kot)
    c.setLineWidth(en)
    c.rect(x0, _y(alt_kot), x1 - x0, alt_kot - ust_kot, stroke=1, fill=0)


#  FORMUN DÜZENİ  ( kotlar PDF puntosu, sayfanın üstünden )
#  Bütün bölümler aynı sol / sağ kenarda ( SOL , SAG ) ve aralarında aynı
#  boşlukla ( ARA ) durur;  sütun çizgileri satırlar boyunca aynı hizadadır.
#  Eskiden kenarlar 87,1 / 89,4 / 89,8 · 504,1 / 504,4 / 506,8 arasında
#  oynuyor, tablonun sütunları satırdan satıra 0,2 – 0,5 pt kayıyordu.
SOL, SAG = 87.1, 506.8
ARA = 6.4

#  Çizgi kalınlıkları:  sayfa çerçevesi, bölüm kutusu, iç çizgiler.
CERCEVE_DIS, CERCEVE_IC = 0.4, 1.0
KUTU, IZGARA = 0.6, 0.3

#  Yazı boyları:  bölüm adı ( kalın ), alan adı, değer.
BOLUM, ETIKET, DEGER = 6.4, 5.8, 7.0

#  ASANSÖR TABLOSU.  Blok sütununun sağı, öbür sütunların sağ kenarları
#  ( kapasite · hız · durak · seyir · kabin;  sonra standart ) ve satırlar
#  ( başlık / değer, üç kez ).  Sütunlar en uzun değere göre:  "1000 kg /
#  13 kişi" 58 pt, "Standart / Yönetmelik" 63 pt, kabinin G / D yarıları eşit.
BLOK_SAG = 128.1
SUTUN = (191.1, 235.1, 287.1, 337.1, 401.1)
KABIN_ORTA = (SUTUN[3] + SUTUN[4]) / 2
GD_EN = 11.0  # "G:" / "D:" hücresi ( 5,8 pt yazı 6,5 pt;  _sola iki yandan pay bırakır )
SATIR = (192.1, 200.7, 209.9, 218.5, 227.7, 236.3, 245.5)
#  ÇİZİM KABULÜ:  çok asansörlü kapakta iki tablonun arası.
TABLO_ARA = 4.0

#  MÜHENDİSLER:  iki kutu, arada ARA;  numara ve alan adı sütunları.
MUHENDIS_UST = SATIR[-1] + ARA
MUHENDIS_BASLIK = MUHENDIS_UST + 13.3
MUHENDIS_SATIR = 8.9
MUHENDIS_IMZA = MUHENDIS_BASLIK + 5 * MUHENDIS_SATIR
MUHENDIS_ALT = 360.6
ORTA = (SOL + SAG + ARA) / 2  # elektrik mühendisinin ve firmanın solu
NO_EN, AD_EN = 18.0, 75.5

#  Mühendislerin altındaki boş kutu ( kaşe / onay ) ve onay · firma kutusu.
BOS_UST, BOS_ALT = MUHENDIS_ALT + ARA, 483.0 - ARA
FIRMA_UST, FIRMA_BASLIK, FIRMA_ALT = 483.0, 495.1, 631.7
FIRMA_SATIRLAR = (
    ("ADI SOYADI / UNVANI", 17.8),
    ("VERGİ NO", 8.9),
    ("VERGİ DAİRESİ", 8.9),
    ("ADRESİ", 17.8),
)
FIRMA_IMZA = FIRMA_BASLIK + sum(boy for _ad, boy in FIRMA_SATIRLAR)
BASLIK_UST, BASLIK_ALT, SAYFA_ALT = FIRMA_ALT, 667.0, 727.0

#  TABLOLAR UZAYINCA DARALAN KUTULAR — ( üst kot , alt kot , inebileceği boy ),
#  daralma sırasıyla:  önce boş kaşe kutusu makul bir boya, sonra imza
#  alanları, sonra kaşe kutusu en küçüğüne, en son en alttaki boş kutu ( bir
#  kutu iki kez yazılabilir ).  Yetmezse ( dört asansör ) tablonun satırları
#  ( yazılarıyla birlikte ) incelir.  Boylar ÇİZİM KABULÜdür:  imza alanına
#  imza, boş kutulara kaşe sığsın.
DARALAN = (
    (BOS_UST, BOS_ALT, 60.0),
    (MUHENDIS_IMZA, MUHENDIS_ALT, 32.0),
    (FIRMA_IMZA, FIRMA_ALT, 50.0),
    (BOS_UST, BOS_ALT, 36.0),
    (BASLIK_ALT, SAYFA_ALT, 50.0),
)


def _daralmalar(uzama):
    """uzama kadar boyu DARALAN'ın sırasıyla kutulardan düşer:  [ ( üst , alt , daralma ) ]."""
    daralma = {}
    for ust, alt, en_kucuk in DARALAN:
        simdiki = alt - ust - daralma.get((ust, alt), 0.0)
        r = max(0.0, min(uzama - sum(daralma.values()), simdiki - en_kucuk))
        daralma[(ust, alt)] = daralma.get((ust, alt), 0.0) + r
    return sorted((ust, alt, r) for (ust, alt), r in daralma.items())


def daralma_payi():
    """Kutuların toplam daralma payı ( her kutu en küçüğüne kadar )."""
    en_kucuk = {}
    for ust, alt, boy in DARALAN:
        en_kucuk[(ust, alt)] = min(boy, en_kucuk.get((ust, alt), boy))
    return sum(alt - ust - boy for (ust, alt), boy in en_kucuk.items())


def yerlesim(adet):
    """adet asansör tablosunun yeri:  ( tablo eşlemeleri , alt bölümün
    eşlemesi , tablo yazılarının çarpanı ).

    Her eşleme formun kotunu bu kapaktaki yerine çevirir ( _kot ).  Tek
    asansörde form BİREBİR aynıdır ( eşlemeler birim ).  Tablolar sığdığı
    kadar tam boyludur ( iki, üç asansör );  sığmazsa ( dört ) satırları ve
    yazıları AYNI ORANDA küçülür:  tablo tek asansörlüdeki gibi görünür.
    Yalnız satırlar incelince yazılar çizgilere değiyordu."""
    if adet <= 1:
        return [_ayni], _ayni, 1.0
    tek = SATIR[-1] - SATIR[0]
    boy = min(tek, (daralma_payi() + tek - (adet - 1) * TABLO_ARA) / adet)
    oran = boy / tek
    tablolar = [
        (lambda kot, ust=SATIR[0] + i * (boy + TABLO_ARA): ust + (kot - SATIR[0]) * oran) for i in range(adet)
    ]
    uzama = adet * boy + (adet - 1) * TABLO_ARA - tek
    daralma = _daralmalar(uzama)

    def asagi(kot):
        #  Tabloların altı uzama kadar iner;  daralan kutunun içinde kalan kot
        #  orantılı, altındaki onun bütün daralmasını geri alır.
        yeni = kot + uzama
        for ust, alt, r in daralma:
            if kot >= alt:
                yeni -= r
            elif kot > ust:
                yeni -= r * (kot - ust) / (alt - ust)
        return yeni

    return tablolar, asagi, oran


def _cerceve(c, yer):
    """A4 teknik kapak paftasının sabit çizimlerini üretir."""
    tablolar, asagi, yazi = yer
    c.saveState()
    c.setStrokeColor(SIYAH)
    c.setFillColor(SIYAH)
    _kutu(c, 70.0, 100.0, 525.0, 742.0, CERCEVE_DIS)
    _kutu(c, 80.0, 110.0, 515.0, 732.0, CERCEVE_IC)
    _yapi_ve_arsa(c)
    for i, esleme in enumerate(tablolar):
        c.kapak_kotu = esleme
        _teknik_tablo(c, f"{i + 1}. ASANSÖR" if len(tablolar) > 1 else None, yazi)
    c.kapak_kotu = asagi
    _muhendis_alani(c, SOL, ORTA - ARA, "PLAN PROJE RESİM VE HESAPLARI YAPAN MAKİNA MÜHENDİSİ")
    _muhendis_alani(c, ORTA, SAG, "PLAN PROJE RESİM VE HESAPLARI YAPAN ELEKTRİK MÜHENDİSİ")
    _kutu(c, SOL, BOS_UST, SAG, BOS_ALT, KUTU)
    _onay_ve_firma(c)
    _kutu(c, SOL, BASLIK_UST, SAG, BASLIK_ALT, KUTU)
    _kutu(c, SOL, BASLIK_ALT, SAG, SAYFA_ALT, KUTU)
    c.kapak_kotu = _ayni
    c.restoreState()


def _iki_satirli(c, ad, ust, alt, basliklar):
    """Yapı · yüklenici · arsa satırı:  solda bölüm adı, sağda başlıklı hücreler."""
    _kutu(c, SOL, ust, SAG, alt, KUTU)
    orta = (ust + alt) / 2
    for x in [x0 for _b, x0, _x1 in basliklar]:
        _dusey(c, x, ust, alt, IZGARA)
    _yatay(c, basliklar[0][1], SAG, orta, IZGARA)
    _ortala(c, ad, SOL, basliklar[0][1], ust, alt, BOLUM, kalin=True)
    return orta


def _yapi_ve_arsa(c):
    """Yapı, yüklenici ve arsa satırları."""
    orta = _iki_satirli(c, "YAPININ", 119.6, 137.4, [("", 149.0, 242.4), ("", 242.4, SAG)])
    _ortala(c, "SAHİBİ", 149.0, 242.4, 119.6, orta, ETIKET)
    _ortala(c, "KULLANIM AMACI", 149.0, 242.4, orta, 137.4, ETIKET)

    orta = _iki_satirli(c, "YÜKLENİCİ", 143.8, 161.5, [("", 149.0, 242.4), ("", 242.4, SAG)])
    _ortala(c, "VERGİ DAİRESİ ve NUMARASI", 149.0, 242.4, orta, 161.5, ETIKET)

    arsa = [
        ("İLİ", 149.0, 203.1),
        ("İLÇESİ", 203.1, 256.4),
        ("MAHALLESİ", 256.4, 321.5),
        ("YÜZÖLÇÜMÜ", 321.5, 369.6),
        ("PAFTA NO", 369.6, 419.3),
        ("ADA NO", 419.3, 459.0),
        ("PARSEL NO", 459.0, SAG),
    ]
    orta = _iki_satirli(c, "ARSANIN", 168.0, 185.7, arsa)
    for baslik_, x0, x1 in arsa:
        _ortala(c, baslik_, x0, x1, 168.0, orta, ETIKET)


def _teknik_tablo(c, etiket=None, yazi=1.0):
    """Bir asansörün teknik tablosu.  etiket:  çok asansörlü kapakta blok
    sütununun başında asansörün sırası ( "2. ASANSÖR" ).  yazi:  satırlar
    inceldiyse yazıların çarpanı ( yerlesim ).

    Boş kalan hücreler ( standart sütununun alt satırları, ölçeğin sağı )
    birleşiktir:  yazısız ızgara karışıklık yaratıyordu."""
    s, x = SATIR, (BLOK_SAG, *SUTUN, SAG)
    _kutu(c, SOL, s[0], SAG, s[-1], KUTU)
    _dusey(c, BLOK_SAG, s[0], s[-1], IZGARA)
    for i in (1, 3, 4):  # hız · seyir · kabin:  ilk dört satır
        _dusey(c, SUTUN[i], s[0], s[4], IZGARA)
    for i in (0, 2):  # kapasite · durak:  bütün satırlar ( ölçek ikisinin arası )
        _dusey(c, SUTUN[i], s[0], s[-1], IZGARA)
    _dusey(c, KABIN_ORTA, s[1], s[2], IZGARA)
    _yatay(c, BLOK_SAG, SAG, s[1], IZGARA)
    _yatay(c, BLOK_SAG, SAG, s[2], IZGARA)
    _yatay(c, BLOK_SAG, SUTUN[4], s[3], IZGARA)
    _yatay(c, BLOK_SAG, SAG, s[4], IZGARA)
    _yatay(c, BLOK_SAG, SUTUN[2], s[5], IZGARA)
    if etiket:
        _ortala(c, etiket, SOL, BLOK_SAG, s[0], s[1], 5.4 * yazi, kalin=True)
        _ortala(c, "BLOK", SOL, BLOK_SAG, s[1], s[2], ETIKET * yazi)
    else:
        _ortala(c, "BLOK", SOL, BLOK_SAG, s[0], s[2], BOLUM, kalin=True)
    for baslik_, i in [
        ("Taşıma Kapasitesi", 0),
        ("Asansör Hızı", 1),
        ("Durak Sayısı", 2),
        ("Seyir Mesafesi", 3),
        ("Kabin Ölçüleri", 4),
        ("Standart / Yönetmelik", 5),
    ]:
        _ortala(c, baslik_, x[i], x[i + 1], s[0], s[1], ETIKET * yazi)
    _sola(c, "G:", SUTUN[3], SUTUN[3] + GD_EN, s[1], s[2], ETIKET * yazi, bosluk=1.2)
    _sola(c, "D:", KABIN_ORTA, KABIN_ORTA + GD_EN, s[1], s[2], ETIKET * yazi, bosluk=1.2)
    for baslik_, i in [
        ("Asansör Sınıfı", 0),
        ("Askı Tipi", 1),
        ("Asansör Sayısı", 2),
        ("Tahrik Cinsi", 3),
        ("Ray Ölçüsü", 4),
    ]:
        _ortala(c, baslik_, x[i], x[i + 1], s[2], s[3], ETIKET * yazi)
    _ortala(c, "M. Motor Gücü", x[0], x[1], s[4], s[5], ETIKET * yazi)
    _ortala(c, "Ölçek", x[1], x[3], s[4], s[5], ETIKET * yazi)


def _muhendis_alani(c, sol_x, sag_x, baslik):
    """Mühendis alanı:  başlık, beş satır ( vergi dairesi … oda sicil no ), imza."""
    no_sag, ad_sag = sol_x + NO_EN, sol_x + NO_EN + AD_EN
    _kutu(c, sol_x, MUHENDIS_UST, sag_x, MUHENDIS_ALT, KUTU)
    _yatay(c, sol_x, sag_x, MUHENDIS_BASLIK, IZGARA)
    _dusey(c, no_sag, MUHENDIS_BASLIK, MUHENDIS_ALT, IZGARA)
    _dusey(c, ad_sag, MUHENDIS_BASLIK, MUHENDIS_IMZA, IZGARA)
    _sola(c, baslik, sol_x, sag_x, MUHENDIS_UST, MUHENDIS_BASLIK, 5.4, bosluk=2.0, kalin=True)
    for no, etiket in enumerate(["VERGİ DAİRESİ", "SİCİL NO", "SOYADI", "ADI", "ODA SİCİL NO"], 1):
        ust = MUHENDIS_BASLIK + (no - 1) * MUHENDIS_SATIR
        _yatay(c, sol_x, sag_x, ust + MUHENDIS_SATIR, IZGARA)
        _ortala(c, no, sol_x, no_sag, ust, ust + MUHENDIS_SATIR, 5.5)
        _sola(c, etiket, no_sag, ad_sag, ust, ust + MUHENDIS_SATIR, 5.7, bosluk=1.5)
    _dikey(c, "İMZASI", sol_x, no_sag, MUHENDIS_IMZA, MUHENDIS_ALT)


def _onay_ve_firma(c):
    """Avan proje onayı ve asansör montaj firması."""
    no_sag, ad_sag = ORTA + NO_EN, ORTA + NO_EN + AD_EN
    _kutu(c, SOL, FIRMA_UST, SAG, FIRMA_ALT, KUTU)
    _dusey(c, ORTA, FIRMA_UST, FIRMA_ALT, KUTU)
    _yatay(c, SOL, SAG, FIRMA_BASLIK, IZGARA)
    _ortala(
        c, "MİMARİ PROJE AVAN PROJE UYGUNLUĞU GÖRÜLDÜ", SOL, ORTA, FIRMA_UST, FIRMA_BASLIK, 6.0, kalin=True
    )
    _ortala(c, "ASANSÖR MONTAJ FİRMA BİLGİLERİ", ORTA, SAG, FIRMA_UST, FIRMA_BASLIK, 6.0, kalin=True)
    _dusey(c, no_sag, FIRMA_BASLIK, FIRMA_ALT, IZGARA)
    _dusey(c, ad_sag, FIRMA_BASLIK, FIRMA_IMZA, IZGARA)
    ust = FIRMA_BASLIK
    for no, (etiket, boy) in enumerate(FIRMA_SATIRLAR, 1):
        _yatay(c, ORTA, SAG, ust + boy, IZGARA)
        _ortala(c, no, ORTA, no_sag, ust, ust + boy, 5.5)
        _sola(c, etiket, no_sag, ad_sag, ust, ust + boy, 5.7, bosluk=1.5)
        ust += boy
    _dikey(c, "İMZASI", ORTA, no_sag, FIRMA_IMZA, FIRMA_ALT)


def _degerler(c, d: Mapping[str, object], asansorler, yer):
    tablolar, asagi, yazi = yer
    # Yapı ve arsa
    _sola(c, d.get("owner"), 242.4, SAG, 119.6, 128.5)
    _sola(c, d.get("usage"), 242.4, SAG, 128.5, 137.4)
    _sola(c, d.get("contractor"), 242.4, SAG, 143.8, 152.7, 5.7)
    _sola(c, d.get("contractor_tax"), 242.4, SAG, 152.7, 161.5, 5.7)
    for anahtar, x0, x1 in [
        ("city", 149.0, 203.1),
        ("district", 203.1, 256.4),
        ("neighborhood", 256.4, 321.5),
        ("area", 321.5, 369.6),
        ("sheet_no", 369.6, 419.3),
        ("island_no", 419.3, 459.0),
        ("parcel_no", 459.0, SAG),
    ]:
        _ortala(c, d.get(anahtar), x0, x1, 176.8, 185.7, 6.0)

    # Asansör — her asansörün kendi tablosu
    for esleme, a in zip(tablolar, asansorler):
        c.kapak_kotu = esleme
        _asansor_degerleri(c, a, yazi)
    c.kapak_kotu = asagi

    # Mühendisler
    for anahtarlar, sol_x in [
        (["mech_tax", "mech_registry", "mech_surname", "mech_name", "mech_chamber"], SOL),
        (["elec_tax", "elec_registry", "elec_surname", "elec_name", "elec_chamber"], ORTA),
    ]:
        sag_x = ORTA - ARA if sol_x == SOL else SAG
        for i, anahtar in enumerate(anahtarlar):
            ust = MUHENDIS_BASLIK + i * MUHENDIS_SATIR
            _sola(c, d.get(anahtar), sol_x + NO_EN + AD_EN, sag_x, ust, ust + MUHENDIS_SATIR, 6.0)

    # Firma
    ust = FIRMA_BASLIK
    for anahtar, (_etiket, boy) in zip(
        ["company_name", "company_tax", "company_tax_office", "company_address"], FIRMA_SATIRLAR
    ):
        if anahtar == "company_address":
            _sarili(c, d.get(anahtar), ORTA + NO_EN + AD_EN, SAG, ust, ust + boy)
        else:
            _sola(c, d.get(anahtar), ORTA + NO_EN + AD_EN, SAG, ust, ust + boy, 6.0)
        ust += boy

    _ortala(
        c,
        d.get("project_title") or "ASANSÖR AVAN PROJESİ",
        SOL + 4,
        SAG - 4,
        BASLIK_UST,
        BASLIK_ALT,
        21.0,
        kalin=True,
    )
    c.kapak_kotu = _ayni


def _asansor_degerleri(c, d: Mapping[str, object], yazi=1.0):
    """Bir asansör tablosunun değerleri ( kotlar formun tek tablosununki )."""
    s, x = SATIR, (BLOK_SAG, *SUTUN, SAG)
    deger = DEGER * yazi
    _ortala(c, d.get("block"), SOL, BLOK_SAG, s[2], s[-1], 14.0 * yazi, kalin=True)
    for anahtar, i in [("capacity", 0), ("speed", 1), ("stops", 2), ("travel", 3), ("standard", 5)]:
        _ortala(c, d.get(anahtar), x[i], x[i + 1], s[1], s[2], deger)
    _ortala(c, d.get("cabin_width"), SUTUN[3] + GD_EN, KABIN_ORTA, s[1], s[2], deger)
    _ortala(c, d.get("cabin_depth"), KABIN_ORTA + GD_EN, SUTUN[4], s[1], s[2], deger)
    for anahtar, i in [
        ("elevator_class", 0),
        ("suspension", 1),
        ("elevator_count", 2),
        ("drive_type", 3),
        ("rail_size", 4),
    ]:
        _ortala(c, d.get(anahtar), x[i], x[i + 1], s[3], s[4], deger)
    _ortala(c, d.get("motor_power"), x[0], x[1], s[5], s[6], deger)
    _ortala(c, d.get("scale"), x[1], x[3], s[5], s[6], deger)


#  Kapak çiziminin kendi kutusu ( _cerceve içindeki en dış çerçeve ) ve
#  hesap paftalarının doldurduğu alan — ikisi de PDF puntosu cinsinden.
CIZIM_KUTUSU = (70.0, 99.9, 525.0, 741.9)  # sol, alt, sağ, üst
PAFTA_KENAR = 12.0 * 72.0 / 25.4  # paftalarda 12 mm kenar boşluğu


def _sayfaya_sigdir(c):
    """
    Kapak çizimini, oranını bozmadan hesap paftalarıyla aynı yüksekliğe
    büyütür ve sayfada ortalar.

    Oranlar birebir aynı olmadığı için YÜKSEKLİK esas alınır:  sayfalar CAD
    çıktısında yan yana dizildiğinde göz önce üst ve alt kenarları takip eder.
    Ölçekleme her iki eksende AYNIDIR — farklı olsaydı yazılar da yatayda
    gerilir, harfler bozulurdu.
    """
    sol, alt, sag, ust = CIZIM_KUTUSU
    gen, yuk = sag - sol, ust - alt
    hedef_yuk = SAYFA_BOY - 2 * PAFTA_KENAR
    hedef_gen = SAYFA_EN - 2 * PAFTA_KENAR
    olcek = min(hedef_yuk / yuk, hedef_gen / gen)
    c.translate((SAYFA_EN - gen * olcek) / 2 - sol * olcek, (SAYFA_BOY - yuk * olcek) / 2 - alt * olcek)
    c.scale(olcek, olcek)


def pdf_baytlari(kapak: Mapping[str, object] | None, asansorler=None) -> bytes:
    """Kapağı tek sayfalı, temiz ve bağımsız PDF baytları olarak verir.

    asansorler:  her asansörün tablo değerleri ( [ { capacity, speed … } ] );
    verilmezse tek tablo kapağın kendi alanlarıyla basılır ( avan kapağı ).
    Birden çok asansör alt alta ayrı tablolara basılır ( bkz. yerlesim )."""
    #  Sözlük olmayan gövde ( bozuk istek ) boş kapak sayılır — _proje_kimligi gibi
    d = dict(kapak) if isinstance(kapak, Mapping) else {}
    tablolar = [a for a in (asansorler or []) if isinstance(a, Mapping)] or [d]
    if not _tek_satir(d.get("project_title")):
        d["project_title"] = "ASANSÖR AVAN PROJESİ"
    cikti = io.BytesIO()
    c = canvas.Canvas(cikti, pagesize=A4, pageCompression=1)
    c.setTitle(_tek_satir(d.get("project_title")))
    c.setAuthor(_tek_satir(d.get("mech_name") or "Asansör Proje Programı"))
    c.setSubject("Asansör proje kapağı")
    c.setCreator("Asansör Proje Programı")
    #  SAYFAYI DOLDUR  —  kapak çizimi 455 x 642 pt'lik bir kutuya yerleşiktir
    #  ( 160,5 x 226,5 mm ).  Hesap paftaları ise A4'ün 12 mm kenar boşluğuyla
    #  186 x 273 mm'lik alanı doldurur.  Kapak, o paftaların yanına dizildiğinde
    #  ( CAD çıktısı ) gözle görülür biçimde KÜÇÜK kalıyordu.  Çizim, oranı
    #  bozulmadan paftaların YÜKSEKLİĞİNİ dolduracak kadar büyütülür; böylece
    #  bütün sayfaların üst ve alt kenarları aynı hizada olur.
    c.saveState()
    _sayfaya_sigdir(c)
    yer = yerlesim(len(tablolar))
    _cerceve(c, yer)
    _degerler(c, d, tablolar, yer)
    c.restoreState()
    c.showPage()
    c.save()
    return cikti.getvalue()
