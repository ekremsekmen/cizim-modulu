# -*- coding: utf-8 -*-
"""Asansör avan proje kapağını doğrudan vektör PDF olarak üretir.

Bu modül hesap motorundan ve mevcut PDF raporlarından bağımsızdır. Pafta
çizgileri ile metinler tek adımda ReportLab tarafından çizilir; kaynak PDF,
arka plan veya ikinci bir katman kullanılmaz.
"""
from __future__ import annotations

import io
import os
from typing import Mapping

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = A4
BLACK = HexColor("#000000")
RED = HexColor("#D00000")
FONT = "KapakGov"
FONT_BOLD = "KapakGovBold"
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")


def _fonts():
    if FONT in pdfmetrics.getRegisteredFontNames():
        return FONT, FONT_BOLD
    normal = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    bold = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
    if os.path.exists(normal) and os.path.exists(bold):
        pdfmetrics.registerFont(TTFont(FONT, normal))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, bold))
        return FONT, FONT_BOLD
    return "Helvetica", "Helvetica-Bold"


F, FB = _fonts()


def _s(value) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def _y(top: float) -> float:
    return PAGE_H - top


def _fit(text: str, width: float, size: float, minimum: float = 4.3) -> float:
    while size > minimum and pdfmetrics.stringWidth(text, F, size) > max(width - 2, 1):
        size -= 0.2
    return max(size, minimum)


#  BİRDEN ÇOK ASANSÖRÜN DEĞERİ  ( "1450/1350" · "0,63 / 1,00 / 1,60 m/s" )
#  en küçük puntoda bile hücreye sığmazsa YANDAKİ HÜCREYE TAŞMAZ:  ayraçtan
#  iki satıra bölünür.  Kabin derinliği hücresi 17 pt'dir — iki kabin
#  ölçüsü tek satırda "Standart" hücresinin üstüne biniyordu.  Tek satıra
#  sığan metin eskisi gibi tek satır basılır.
IKI_SATIR_EN_KUCUK = 3.2


def _satirlar(text, width, size, height):
    """( satırlar, punto ) — tek satır sığmıyorsa ayraçtan dengeli iki satır."""
    tek = _fit(text, width, size)
    if pdfmetrics.stringWidth(text, F, tek) <= max(width - 2, 1):
        return [text], tek
    ayrac = " / " if " / " in text else "/" if "/" in text else None
    if ayrac is None:
        return [text], tek
    parca = text.split(ayrac)
    k = (len(parca) + 1) // 2
    iki = [ayrac.join(parca[:k]) + ayrac.rstrip(), ayrac.join(parca[k:])]
    #  İki satır hücre yüksekliğine sığmalı:  satır aralığı ~ 1,05 punto.
    punto = min(min(_fit(x, width, size, IKI_SATIR_EN_KUCUK) for x in iki),
                (height - 0.6) / 2.1)
    if all(pdfmetrics.stringWidth(x, F, punto) <= max(width - 2, 1) for x in iki):
        return iki, punto
    return [text], tek


def _yaz(c, satirlar, font, font_size, x_of, top, bottom):
    """Satırları hücrenin düşey ortasına dizer;  x_of( satır ) → sol kenar."""
    ara = font_size * 1.05
    orta = (top + bottom) / 2
    for i, satir in enumerate(satirlar):
        dy = (i - (len(satirlar) - 1) / 2) * ara
        c.drawString(x_of(satir), _y(orta + dy) - font_size * 0.33, satir)


def _center(c, value, x0, x1, top, bottom, size=7.0, color=BLACK, bold=False):
    text = _s(value)
    if not text:
        return
    font = FB if bold else F
    satirlar, font_size = _satirlar(text, x1 - x0, size, abs(bottom - top))
    c.setFont(font, font_size)
    c.setFillColor(color)
    _yaz(c, satirlar, font, font_size,
         lambda t: x0 + max(1.1, ((x1 - x0) - pdfmetrics.stringWidth(t, font, font_size)) / 2),
         top, bottom)


def _left(c, value, x0, x1, top, bottom, size=6.4, color=BLACK, padding=2.0, bold=False):
    text = _s(value)
    if not text:
        return
    font = FB if bold else F
    satirlar, font_size = _satirlar(text, x1 - x0 - padding * 2, size, abs(bottom - top))
    c.setFont(font, font_size)
    c.setFillColor(color)
    _yaz(c, satirlar, font, font_size, lambda _t: x0 + padding, top, bottom)


def _wrapped(c, value, x0, x1, top, bottom, size=5.7, color=BLACK, padding=2.0):
    text = _s(value)
    if not text:
        return
    words = text.split()
    width = x1 - x0 - padding * 2
    #  SATIR BÜTÇESİ KUTUNUN GERÇEK YÜKSEKLİĞİNDEN TÜRETİLİR.  Eskiden 2'ye
    #  sabitlenmişti:  124 karakterlik normal bir adreste "İstanbul Türkiye
    #  34758" bölümü çıktıdan SESSİZCE düşüyordu.  Kutu daha küçük puntoda
    #  3 satır alabiliyor; yine sığmazsa kırpma artık GÖRÜNÜR ( … ).
    yukseklik = abs(bottom - top)

    def _sar(punto):
        satirlar, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and pdfmetrics.stringWidth(candidate, F, punto) > width:
                satirlar.append(current)
                current = word
            else:
                current = candidate
        if current:
            satirlar.append(current)
        return satirlar

    def _azami(punto):
        return max(1, int(yukseklik // (punto * 1.15)))

    font_size = size
    lines = _sar(font_size)
    while font_size > 4.3 and len(lines) > _azami(font_size):
        font_size -= 0.2
        lines = _sar(font_size)
    if len(lines) > _azami(font_size):
        #  En küçük puntoda bile sığmıyor — kırpıldığı ÇIKTIDA görünsün.
        lines = lines[:_azami(font_size)]
        lines[-1] = lines[-1].rstrip() + " …"
    lines = lines or [text]
    line_height = font_size * 1.15
    baseline = _y((top + bottom) / 2) + (len(lines) - 1) * line_height / 2 - font_size * 0.33
    c.setFont(F, font_size)
    c.setFillColor(color)
    for i, line in enumerate(lines):
        c.drawString(x0 + padding, baseline - i * line_height, line)


def _vertical(c, text, x0, x1, top, bottom, size=6.0):
    c.saveState()
    c.setFont(F, size)
    c.setFillColor(BLACK)
    c.translate((x0 + x1) / 2, _y((top + bottom) / 2))
    c.rotate(90)
    c.drawCentredString(0, -size * 0.33, text)
    c.restoreState()


def _h(c, x0, x1, top, width=0.45):
    c.setLineWidth(width)
    c.line(x0, _y(top), x1, _y(top))


def _v(c, x, top, bottom, width=0.45):
    c.setLineWidth(width)
    c.line(x, _y(top), x, _y(bottom))


def _box(c, x0, top, x1, bottom, width=0.45):
    c.setLineWidth(width)
    c.rect(x0, _y(bottom), x1 - x0, bottom - top, stroke=1, fill=0)


def _structure(c):
    """A4 teknik kapak paftasının sabit çizimlerini üretir."""
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setFillColor(BLACK)
    _box(c, 70.0, 100.0, 525.0, 742.0, 0.9)
    _box(c, 80.0, 110.0, 515.0, 732.0, 0.6)

    # Yapı
    _box(c, 89.8, 119.6, 504.1, 137.4, 0.55)
    for x in [149.0, 242.4]: _v(c, x, 119.6, 137.4)
    _h(c, 149.0, 504.1, 128.5)
    _center(c, "YAPININ", 89.8, 149.0, 119.6, 137.4, 6.7)
    _center(c, "SAHİBİ", 149.0, 242.4, 119.6, 128.5, 6.7)
    _center(c, "KULLANIM AMACI", 149.0, 242.4, 128.5, 137.4, 6.4)

    _box(c, 89.8, 143.8, 504.1, 161.5, 0.55)
    for x in [149.0, 242.4]: _v(c, x, 143.8, 161.5)
    _h(c, 149.0, 504.1, 152.7)
    _center(c, "YÜKLENİCİ", 89.8, 149.0, 143.8, 161.5, 6.7)
    _center(c, "VERGİ DAİRESİ ve NUMARASI", 149.0, 242.4, 152.7, 161.5, 6.0)

    _box(c, 89.8, 168.0, 504.1, 185.7, 0.55)
    for x in [149.0, 203.1, 256.4, 321.5, 369.6, 419.3, 455.4]: _v(c, x, 168.0, 185.7)
    _h(c, 149.0, 504.1, 176.8)
    _center(c, "ARSANIN", 89.8, 149.0, 168.0, 185.7, 6.7)
    for title, x0, x1 in [
        ("İLİ",149.0,203.1),("İLÇESİ",203.1,256.4),("MAHALLESİ",256.4,321.5),
        ("YÜZÖLÇÜMÜ",321.5,369.6),("PAFTA NO",369.6,419.3),("ADA NO",419.3,455.4),("PARSEL NO",455.4,504.1)]:
        _center(c, title, x0, x1, 168.0, 176.8, 6.0)

    # Asansör teknik tablosu
    _box(c, 87.1, 189.7, 506.8, 249.9, 0.6)
    _box(c, 89.8, 192.1, 504.1, 245.5, 0.5)
    _v(c, 124.4, 192.1, 245.5)
    for y in [202.1,211.0,220.1,229.0,236.6]: _h(c, 124.4, 504.1, y)
    for x in [179.0,223.0,288.5,332.2,395.2]: _v(c, x, 192.1, 211.0)
    _v(c, 369.6, 202.1, 211.0)
    for x in [178.5,222.8,288.1,331.7,394.8]: _v(c, x, 211.0, 229.0)
    for x in [174.3,288.3,332.0,395.0]: _v(c, x, 229.0, 245.5)
    _center(c, "BLOK:", 89.8, 124.4, 192.1, 211.0, 10.0)
    for title, x0, x1 in [
        ("Taşıma Kapasitesi",124.4,179.0),("Asansör Hızı",179.0,223.0),
        ("Durak Sayısı",223.0,288.5),("Seyir Mesafesi",288.5,332.2),
        ("Kabin Ölçüleri",332.2,395.2),("Standart / Yönetmelik",395.2,504.1)]:
        _center(c, title, x0, x1, 192.1, 202.1, 5.8)
    _left(c, "G:", 332.2, 343.0, 202.1, 211.0, 6.0, padding=1.2)
    _left(c, "D:", 369.6, 378.0, 202.1, 211.0, 6.0, padding=1.0)
    for title, x0, x1 in [
        ("Asansör Sınıfı",124.4,178.5),("Askı Tipi",178.5,222.8),
        ("Asansör Sayısı",222.8,288.1),("Tahrik Cinsi",288.1,331.7),("Ray Ölçüsü",331.7,394.8)]:
        _center(c, title, x0, x1, 211.0, 220.1, 5.8)
    _center(c, "M. Motor Gücü", 124.4, 174.3, 229.0, 236.6, 5.8)
    _left(c, "Ölçek", 174.3, 288.3, 229.0, 236.6, 5.8, padding=2.2)

    # Mühendis alanları
    def engineer(left, right, number_right, label_right, heading):
        _box(c, left, 253.6, right, 362.3, 0.55)
        _h(c, left, right, 266.9)
        _v(c, number_right, 266.9, 362.3)
        _v(c, label_right, 266.9, 311.3)
        for y in [275.8,284.7,293.5,302.4,311.3]: _h(c, left, right, y)
        _left(c, heading, left, right, 253.6, 266.9, 5.0, padding=1.4)
        for no, label, top, bottom in [
            (1,"VERGİ DAİRESİ",266.9,275.8),(2,"SİCİL NO",275.8,284.7),
            (3,"SOYADI",284.7,293.5),(4,"ADI",293.5,302.4),(5,"ODA SİCİL NO",302.4,311.3)]:
            _center(c, no, left, number_right, top, bottom, 5.5)
            _left(c, label, number_right, label_right, top, bottom, 5.7, padding=1.5)
        _vertical(c, "İMZASI", left, number_right, 311.3, 362.3)
    engineer(89.4,297.0,107.1,182.5,"PLAN PROJE RESİM VE HESAPLARI YAPAN MAKİNA MÜHENDİSİ")
    engineer(311.1,506.8,329.8,405.3,"PLAN PROJE RESİM VE HESAPLARI YAPAN ELEKTRİK MÜHENDİSİ")

    _box(c, 87.1, 362.3, 506.8, 464.2, 0.55)

    # Onay ve montaj firması
    _box(c, 87.1, 483.0, 506.8, 631.7, 0.55)
    _v(c, 284.2, 483.0, 631.7, 0.5)
    _h(c, 87.1, 506.8, 495.1)
    _center(c, "MİMARİ PROJE AVAN PROJE UYGUNLUĞU GÖRÜLDÜ", 87.1, 284.2, 483.0, 495.1, 6.3)
    _center(c, "ASANSÖR MONTAJ FİRMA BİLGİLERİ", 284.2, 506.8, 483.0, 495.1, 6.5)
    _h(c, 284.2, 506.8, 505.6)
    _v(c, 302.1, 505.6, 631.7)
    _v(c, 377.4, 505.6, 558.9)
    for y in [523.4,532.2,541.1,558.9]: _h(c, 284.2, 506.8, y)
    for no, label, top, bottom in [
        (1,"ADI SOYADI / UNVANI",505.6,523.4),(2,"VERGİ NO",523.4,532.2),
        (3,"VERGİ DAİRESİ",532.2,541.1),(4,"ADRESİ",541.1,558.9)]:
        _center(c, no, 284.2, 302.1, top, bottom, 5.5)
        _left(c, label, 302.1, 377.4, top, bottom, 5.7, padding=1.6)
    _vertical(c, "İMZASI", 284.2, 302.1, 558.9, 631.7)

    _box(c, 87.1, 631.7, 506.8, 667.0, 0.55)
    _box(c, 87.1, 667.0, 506.8, 727.0, 0.55)
    _box(c, 89.5, 669.3, 504.4, 724.7, 0.4)
    c.restoreState()


def _values(c, d: Mapping[str, object]):
    # Yapı ve arsa
    _left(c, d.get("owner"), 242.4, 504.1, 119.6, 128.5)
    _left(c, d.get("usage"), 242.4, 504.1, 128.5, 137.4)
    _left(c, d.get("contractor"), 242.4, 504.1, 143.8, 152.7, 5.7)
    _left(c, d.get("contractor_tax"), 242.4, 504.1, 152.7, 161.5, 5.7)
    for key, x0, x1, size in [
        ("city",149.0,203.1,6.0),("district",203.1,256.4,6.0),("neighborhood",256.4,321.5,5.8),
        ("area",321.5,369.6,5.7),("sheet_no",369.6,419.3,5.7),("island_no",419.3,455.4,5.7),("parcel_no",455.4,504.1,5.7)]:
        _center(c, d.get(key), x0, x1, 176.8, 185.7, size)

    # Asansör
    _center(c, d.get("block"), 89.8, 124.4, 211.0, 245.5, 12.0)
    for key, x0, x1 in [
        ("capacity",124.4,179.0),("speed",179.0,223.0),("stops",223.0,288.5),
        ("travel",288.5,332.2),("standard",395.2,504.1)]:
        _center(c, d.get(key), x0, x1, 202.1, 211.0, 7.0, RED)
    _left(c, d.get("cabin_width"), 343.0, 369.6, 202.1, 211.0, 7.0, RED, 1.0)
    _left(c, d.get("cabin_depth"), 378.0, 395.2, 202.1, 211.0, 7.0, RED, 0.8)
    for key, x0, x1 in [
        ("elevator_class",124.4,178.5),("suspension",178.5,222.8),("elevator_count",222.8,288.1),
        ("drive_type",288.1,331.7),("rail_size",331.7,394.8)]:
        _center(c, d.get(key), x0, x1, 220.1, 229.0, 7.0, RED)
    _center(c, d.get("motor_power"), 124.7, 174.3, 236.6, 245.5, 7.0, RED)
    _left(c, d.get("scale"), 174.3, 288.3, 236.6, 245.5, 7.0, RED)

    # Mühendisler
    rows = [(266.9,275.8),(275.8,284.7),(284.7,293.5),(293.5,302.4),(302.4,311.3)]
    for key, bounds in zip(["mech_tax","mech_registry","mech_surname","mech_name","mech_chamber"], rows):
        _left(c, d.get(key), 182.5, 297.0, *bounds, 6.0)
    for key, bounds in zip(["elec_tax","elec_registry","elec_surname","elec_name","elec_chamber"], rows):
        _left(c, d.get(key), 405.3, 506.8, *bounds, 6.0)

    # Firma
    _left(c, d.get("company_name"), 377.4, 506.8, 505.6, 523.4, 6.0)
    _left(c, d.get("company_tax"), 377.4, 506.8, 523.4, 532.2, 6.0)
    _left(c, d.get("company_tax_office"), 377.4, 506.8, 532.2, 541.1, 6.0)
    _wrapped(c, d.get("company_address"), 377.4, 506.8, 541.1, 558.9)

    _center(c, d.get("project_title") or "ASANSÖR AVAN PROJESİ", 91.0, 502.0, 631.7, 667.0, 23.0)


#  Kapak çiziminin kendi kutusu ( _structure içindeki en dış çerçeve ) ve
#  hesap paftalarının doldurduğu alan — ikisi de PDF puntosu cinsinden.
CIZIM_KUTUSU = (70.0, 99.9, 525.0, 741.9)        # sol, alt, sağ, üst
PAFTA_KENAR = 12.0 * 72.0 / 25.4                 # paftalarda 12 mm kenar boşluğu


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
    hedef_yuk = PAGE_H - 2 * PAFTA_KENAR
    hedef_gen = PAGE_W - 2 * PAFTA_KENAR
    olcek = min(hedef_yuk / yuk, hedef_gen / gen)
    c.translate((PAGE_W - gen * olcek) / 2 - sol * olcek,
                (PAGE_H - yuk * olcek) / 2 - alt * olcek)
    c.scale(olcek, olcek)


def pdf_bytes(kapak: Mapping[str, object] | None) -> bytes:
    """Kapağı tek sayfalı, temiz ve bağımsız PDF baytları olarak verir."""
    d = dict(kapak or {})
    if not _s(d.get("project_title")):
        d["project_title"] = "ASANSÖR AVAN PROJESİ"
    out = io.BytesIO()
    c = canvas.Canvas(out, pagesize=A4, pageCompression=1)
    c.setTitle(_s(d.get("project_title")))
    c.setAuthor(_s(d.get("mech_name") or "Asansör Proje Programı"))
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
    _structure(c)
    _values(c, d)
    c.restoreState()
    c.showPage()
    c.save()
    return out.getvalue()
