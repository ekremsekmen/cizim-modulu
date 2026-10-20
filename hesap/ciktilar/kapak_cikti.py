# -*- coding: utf-8 -*-
"""Asansör avan proje kapağını doğrudan vektör PDF olarak üretir.

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
KIRMIZI = HexColor("#D00000")
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


def _sigan_punto(metin: str, en: float, boyut: float, en_kucuk: float = 4.3) -> float:
    while boyut > en_kucuk and pdfmetrics.stringWidth(metin, YAZI, boyut) > max(en - 2, 1):
        boyut -= 0.2
    return max(boyut, en_kucuk)


#  BİRDEN ÇOK ASANSÖRÜN DEĞERİ  ( "1450/1350" · "0,63 / 1,00 / 1,60 m/s" )
#  en küçük puntoda bile hücreye sığmazsa YANDAKİ HÜCREYE TAŞMAZ:  ayraçtan
#  iki satıra bölünür.  Kabin derinliği hücresi 17 pt'dir — iki kabin
#  ölçüsü tek satırda "Standart" hücresinin üstüne biniyordu.  Tek satıra
#  sığan metin eskisi gibi tek satır basılır.
IKI_SATIR_EN_KUCUK = 3.2


def _satirlar(metin, en, boyut, hucre_boyu):
    """( satırlar, punto ) — tek satır sığmıyorsa ayraçtan dengeli iki satır."""
    tek = _sigan_punto(metin, en, boyut)
    if pdfmetrics.stringWidth(metin, YAZI, tek) <= max(en - 2, 1):
        return [metin], tek
    ayrac = " / " if " / " in metin else "/" if "/" in metin else None
    if ayrac is None:
        return [metin], tek
    parca = metin.split(ayrac)
    k = (len(parca) + 1) // 2
    iki = [ayrac.join(parca[:k]) + ayrac.rstrip(), ayrac.join(parca[k:])]
    #  İki satır hücre yüksekliğine sığmalı:  satır aralığı ~ 1,05 punto.
    punto = min(min(_sigan_punto(x, en, boyut, IKI_SATIR_EN_KUCUK) for x in iki), (hucre_boyu - 0.6) / 2.1)
    if all(pdfmetrics.stringWidth(x, YAZI, punto) <= max(en - 2, 1) for x in iki):
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
    yazi_tipi = KALIN_YAZI if kalin else YAZI
    satirlar, yazi_boyu = _satirlar(metin, x1 - x0, boyut, abs(alt_kot - ust_kot))
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
    yazi_tipi = KALIN_YAZI if kalin else YAZI
    satirlar, yazi_boyu = _satirlar(metin, x1 - x0 - bosluk * 2, boyut, abs(alt_kot - ust_kot))
    c.setFont(yazi_tipi, yazi_boyu)
    c.setFillColor(renk)
    _yaz(c, satirlar, yazi_tipi, yazi_boyu, lambda _t: x0 + bosluk, ust_kot, alt_kot)


def _sarili(c, deger, x0, x1, ust_kot, alt_kot, boyut=5.7, renk=SIYAH, bosluk=2.0):
    metin = _tek_satir(deger)
    if not metin:
        return
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
    c.saveState()
    c.setFont(YAZI, boyut)
    c.setFillColor(SIYAH)
    c.translate((x0 + x1) / 2, _y((ust_kot + alt_kot) / 2))
    c.rotate(90)
    c.drawCentredString(0, -boyut * 0.33, metin)
    c.restoreState()


def _yatay(c, x0, x1, ust_kot, en=0.45):
    c.setLineWidth(en)
    c.line(x0, _y(ust_kot), x1, _y(ust_kot))


def _dusey(c, x, ust_kot, alt_kot, en=0.45):
    c.setLineWidth(en)
    c.line(x, _y(ust_kot), x, _y(alt_kot))


def _kutu(c, x0, ust_kot, x1, alt_kot, en=0.45):
    c.setLineWidth(en)
    c.rect(x0, _y(alt_kot), x1 - x0, alt_kot - ust_kot, stroke=1, fill=0)


def _cerceve(c):
    """A4 teknik kapak paftasının sabit çizimlerini üretir."""
    c.saveState()
    c.setStrokeColor(SIYAH)
    c.setFillColor(SIYAH)
    _kutu(c, 70.0, 100.0, 525.0, 742.0, 0.9)
    _kutu(c, 80.0, 110.0, 515.0, 732.0, 0.6)
    _yapi_ve_arsa(c)
    _teknik_tablo(c)
    _muhendis_alani(c, 89.4, 297.0, 107.1, 182.5, "PLAN PROJE RESİM VE HESAPLARI YAPAN MAKİNA MÜHENDİSİ")
    _muhendis_alani(c, 311.1, 506.8, 329.8, 405.3, "PLAN PROJE RESİM VE HESAPLARI YAPAN ELEKTRİK MÜHENDİSİ")
    _kutu(c, 87.1, 362.3, 506.8, 464.2, 0.55)
    _onay_ve_firma(c)
    _kutu(c, 87.1, 631.7, 506.8, 667.0, 0.55)
    _kutu(c, 87.1, 667.0, 506.8, 727.0, 0.55)
    _kutu(c, 89.5, 669.3, 504.4, 724.7, 0.4)
    c.restoreState()


def _yapi_ve_arsa(c):
    """Yapı, yüklenici ve arsa satırları."""
    _kutu(c, 89.8, 119.6, 504.1, 137.4, 0.55)
    for x in [149.0, 242.4]:
        _dusey(c, x, 119.6, 137.4)
    _yatay(c, 149.0, 504.1, 128.5)
    _ortala(c, "YAPININ", 89.8, 149.0, 119.6, 137.4, 6.7)
    _ortala(c, "SAHİBİ", 149.0, 242.4, 119.6, 128.5, 6.7)
    _ortala(c, "KULLANIM AMACI", 149.0, 242.4, 128.5, 137.4, 6.4)

    _kutu(c, 89.8, 143.8, 504.1, 161.5, 0.55)
    for x in [149.0, 242.4]:
        _dusey(c, x, 143.8, 161.5)
    _yatay(c, 149.0, 504.1, 152.7)
    _ortala(c, "YÜKLENİCİ", 89.8, 149.0, 143.8, 161.5, 6.7)
    _ortala(c, "VERGİ DAİRESİ ve NUMARASI", 149.0, 242.4, 152.7, 161.5, 6.0)

    _kutu(c, 89.8, 168.0, 504.1, 185.7, 0.55)
    for x in [149.0, 203.1, 256.4, 321.5, 369.6, 419.3, 455.4]:
        _dusey(c, x, 168.0, 185.7)
    _yatay(c, 149.0, 504.1, 176.8)
    _ortala(c, "ARSANIN", 89.8, 149.0, 168.0, 185.7, 6.7)
    for baslik_, x0, x1 in [
        ("İLİ", 149.0, 203.1),
        ("İLÇESİ", 203.1, 256.4),
        ("MAHALLESİ", 256.4, 321.5),
        ("YÜZÖLÇÜMÜ", 321.5, 369.6),
        ("PAFTA NO", 369.6, 419.3),
        ("ADA NO", 419.3, 455.4),
        ("PARSEL NO", 455.4, 504.1),
    ]:
        _ortala(c, baslik_, x0, x1, 168.0, 176.8, 6.0)


def _teknik_tablo(c):
    """Asansör teknik tablosu."""
    _kutu(c, 87.1, 189.7, 506.8, 249.9, 0.6)
    _kutu(c, 89.8, 192.1, 504.1, 245.5, 0.5)
    _dusey(c, 124.4, 192.1, 245.5)
    for y in [202.1, 211.0, 220.1, 229.0, 236.6]:
        _yatay(c, 124.4, 504.1, y)
    for x in [179.0, 223.0, 288.5, 332.2, 395.2]:
        _dusey(c, x, 192.1, 211.0)
    _dusey(c, 369.6, 202.1, 211.0)
    for x in [178.5, 222.8, 288.1, 331.7, 394.8]:
        _dusey(c, x, 211.0, 229.0)
    for x in [174.3, 288.3, 332.0, 395.0]:
        _dusey(c, x, 229.0, 245.5)
    _ortala(c, "BLOK:", 89.8, 124.4, 192.1, 211.0, 10.0)
    for baslik_, x0, x1 in [
        ("Taşıma Kapasitesi", 124.4, 179.0),
        ("Asansör Hızı", 179.0, 223.0),
        ("Durak Sayısı", 223.0, 288.5),
        ("Seyir Mesafesi", 288.5, 332.2),
        ("Kabin Ölçüleri", 332.2, 395.2),
        ("Standart / Yönetmelik", 395.2, 504.1),
    ]:
        _ortala(c, baslik_, x0, x1, 192.1, 202.1, 5.8)
    _sola(c, "G:", 332.2, 343.0, 202.1, 211.0, 6.0, bosluk=1.2)
    _sola(c, "D:", 369.6, 378.0, 202.1, 211.0, 6.0, bosluk=1.0)
    for baslik_, x0, x1 in [
        ("Asansör Sınıfı", 124.4, 178.5),
        ("Askı Tipi", 178.5, 222.8),
        ("Asansör Sayısı", 222.8, 288.1),
        ("Tahrik Cinsi", 288.1, 331.7),
        ("Ray Ölçüsü", 331.7, 394.8),
    ]:
        _ortala(c, baslik_, x0, x1, 211.0, 220.1, 5.8)
    _ortala(c, "M. Motor Gücü", 124.4, 174.3, 229.0, 236.6, 5.8)
    _sola(c, "Ölçek", 174.3, 288.3, 229.0, 236.6, 5.8, bosluk=2.2)


def _muhendis_alani(c, sol_x, sag_x, no_sag, etiket_sag, baslik):
    """Mühendis alanı:  başlık, beş satır ( vergi dairesi … oda sicil no ), imza."""
    _kutu(c, sol_x, 253.6, sag_x, 362.3, 0.55)
    _yatay(c, sol_x, sag_x, 266.9)
    _dusey(c, no_sag, 266.9, 362.3)
    _dusey(c, etiket_sag, 266.9, 311.3)
    for y in [275.8, 284.7, 293.5, 302.4, 311.3]:
        _yatay(c, sol_x, sag_x, y)
    _sola(c, baslik, sol_x, sag_x, 253.6, 266.9, 5.0, bosluk=1.4)
    for no, etiket, ust_kot, alt_kot in [
        (1, "VERGİ DAİRESİ", 266.9, 275.8),
        (2, "SİCİL NO", 275.8, 284.7),
        (3, "SOYADI", 284.7, 293.5),
        (4, "ADI", 293.5, 302.4),
        (5, "ODA SİCİL NO", 302.4, 311.3),
    ]:
        _ortala(c, no, sol_x, no_sag, ust_kot, alt_kot, 5.5)
        _sola(c, etiket, no_sag, etiket_sag, ust_kot, alt_kot, 5.7, bosluk=1.5)
    _dikey(c, "İMZASI", sol_x, no_sag, 311.3, 362.3)


def _onay_ve_firma(c):
    """Avan proje onayı ve asansör montaj firması."""
    _kutu(c, 87.1, 483.0, 506.8, 631.7, 0.55)
    _dusey(c, 284.2, 483.0, 631.7, 0.5)
    _yatay(c, 87.1, 506.8, 495.1)
    _ortala(c, "MİMARİ PROJE AVAN PROJE UYGUNLUĞU GÖRÜLDÜ", 87.1, 284.2, 483.0, 495.1, 6.3)
    _ortala(c, "ASANSÖR MONTAJ FİRMA BİLGİLERİ", 284.2, 506.8, 483.0, 495.1, 6.5)
    _yatay(c, 284.2, 506.8, 505.6)
    _dusey(c, 302.1, 505.6, 631.7)
    _dusey(c, 377.4, 505.6, 558.9)
    for y in [523.4, 532.2, 541.1, 558.9]:
        _yatay(c, 284.2, 506.8, y)
    for no, etiket, ust_kot, alt_kot in [
        (1, "ADI SOYADI / UNVANI", 505.6, 523.4),
        (2, "VERGİ NO", 523.4, 532.2),
        (3, "VERGİ DAİRESİ", 532.2, 541.1),
        (4, "ADRESİ", 541.1, 558.9),
    ]:
        _ortala(c, no, 284.2, 302.1, ust_kot, alt_kot, 5.5)
        _sola(c, etiket, 302.1, 377.4, ust_kot, alt_kot, 5.7, bosluk=1.6)
    _dikey(c, "İMZASI", 284.2, 302.1, 558.9, 631.7)


def _degerler(c, d: Mapping[str, object]):
    # Yapı ve arsa
    _sola(c, d.get("owner"), 242.4, 504.1, 119.6, 128.5)
    _sola(c, d.get("usage"), 242.4, 504.1, 128.5, 137.4)
    _sola(c, d.get("contractor"), 242.4, 504.1, 143.8, 152.7, 5.7)
    _sola(c, d.get("contractor_tax"), 242.4, 504.1, 152.7, 161.5, 5.7)
    for anahtar, x0, x1, boyut in [
        ("city", 149.0, 203.1, 6.0),
        ("district", 203.1, 256.4, 6.0),
        ("neighborhood", 256.4, 321.5, 5.8),
        ("area", 321.5, 369.6, 5.7),
        ("sheet_no", 369.6, 419.3, 5.7),
        ("island_no", 419.3, 455.4, 5.7),
        ("parcel_no", 455.4, 504.1, 5.7),
    ]:
        _ortala(c, d.get(anahtar), x0, x1, 176.8, 185.7, boyut)

    # Asansör
    _ortala(c, d.get("block"), 89.8, 124.4, 211.0, 245.5, 12.0)
    for anahtar, x0, x1 in [
        ("capacity", 124.4, 179.0),
        ("speed", 179.0, 223.0),
        ("stops", 223.0, 288.5),
        ("travel", 288.5, 332.2),
        ("standard", 395.2, 504.1),
    ]:
        _ortala(c, d.get(anahtar), x0, x1, 202.1, 211.0, 7.0, KIRMIZI)
    _sola(c, d.get("cabin_width"), 343.0, 369.6, 202.1, 211.0, 7.0, KIRMIZI, 1.0)
    _sola(c, d.get("cabin_depth"), 378.0, 395.2, 202.1, 211.0, 7.0, KIRMIZI, 0.8)
    for anahtar, x0, x1 in [
        ("elevator_class", 124.4, 178.5),
        ("suspension", 178.5, 222.8),
        ("elevator_count", 222.8, 288.1),
        ("drive_type", 288.1, 331.7),
        ("rail_size", 331.7, 394.8),
    ]:
        _ortala(c, d.get(anahtar), x0, x1, 220.1, 229.0, 7.0, KIRMIZI)
    _ortala(c, d.get("motor_power"), 124.7, 174.3, 236.6, 245.5, 7.0, KIRMIZI)
    _sola(c, d.get("scale"), 174.3, 288.3, 236.6, 245.5, 7.0, KIRMIZI)

    # Mühendisler
    satir_kotlari = [(266.9, 275.8), (275.8, 284.7), (284.7, 293.5), (293.5, 302.4), (302.4, 311.3)]
    for anahtar, kotlar in zip(
        ["mech_tax", "mech_registry", "mech_surname", "mech_name", "mech_chamber"], satir_kotlari
    ):
        _sola(c, d.get(anahtar), 182.5, 297.0, *kotlar, 6.0)
    for anahtar, kotlar in zip(
        ["elec_tax", "elec_registry", "elec_surname", "elec_name", "elec_chamber"], satir_kotlari
    ):
        _sola(c, d.get(anahtar), 405.3, 506.8, *kotlar, 6.0)

    # Firma
    _sola(c, d.get("company_name"), 377.4, 506.8, 505.6, 523.4, 6.0)
    _sola(c, d.get("company_tax"), 377.4, 506.8, 523.4, 532.2, 6.0)
    _sola(c, d.get("company_tax_office"), 377.4, 506.8, 532.2, 541.1, 6.0)
    _sarili(c, d.get("company_address"), 377.4, 506.8, 541.1, 558.9)

    _ortala(c, d.get("project_title") or "ASANSÖR AVAN PROJESİ", 91.0, 502.0, 631.7, 667.0, 23.0)


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


def pdf_baytlari(kapak: Mapping[str, object] | None) -> bytes:
    """Kapağı tek sayfalı, temiz ve bağımsız PDF baytları olarak verir."""
    #  Sözlük olmayan gövde ( bozuk istek ) boş kapak sayılır — _proje_kimligi gibi
    d = dict(kapak) if isinstance(kapak, Mapping) else {}
    if not _tek_satir(d.get("project_title")):
        d["project_title"] = "ASANSÖR AVAN PROJESİ"
    cikti = io.BytesIO()
    c = canvas.Canvas(cikti, pagesize=A4, pageCompression=1)
    c.setTitle(_tek_satir(d.get("project_title")))
    c.setAuthor(_tek_satir(d.get("mech_name") or "Asansör Proje Programı"))
    c.setSubject("Asansör avan proje kapağı")
    c.setCreator("Asansör Proje Programı")
    #  SAYFAYI DOLDUR  —  kapak çizimi 455 x 642 pt'lik bir kutuya yerleşiktir
    #  ( 160,5 x 226,5 mm ).  Hesap paftaları ise A4'ün 12 mm kenar boşluğuyla
    #  186 x 273 mm'lik alanı doldurur.  Kapak, o paftaların yanına dizildiğinde
    #  ( CAD çıktısı ) gözle görülür biçimde KÜÇÜK kalıyordu.  Çizim, oranı
    #  bozulmadan paftaların YÜKSEKLİĞİNİ dolduracak kadar büyütülür; böylece
    #  bütün sayfaların üst ve alt kenarları aynı hizada olur.
    c.saveState()
    _sayfaya_sigdir(c)
    _cerceve(c)
    _degerler(c, d)
    c.restoreState()
    c.showPage()
    c.save()
    return cikti.getvalue()
