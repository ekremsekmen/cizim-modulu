# -*- coding: utf-8 -*-
"""
ÇİZİM  →  PDF   ( reportlab;  basılı pafta )

SVG ve DXF ile AYNI eleman listesini, aynı üslupla ( uslup ) çizer:  ISO 128
kalınlıkları kâğıtta milimetre, ISO çizgi tipleri, tarama aralığı, ölçü ucu,
renkler ekrandaki gibi.  Yazılar GERÇEK yazıdır ( eğri değil ):  gömülü
Liberation Sans — Arial'le harf enleri aynı ( harf_eni ), PDF'te aranır,
seçilir, kopyalanır.  12 Eki'ye kadar çizimlerin PDF'i ezdxf'in önizleme
SVG'sinden üretiliyordu:  yazılar eğriye çevrilmiş, tek sayfa 4.078 × 610 mm,
7,8 MB.

Koordinat:  çizim gerçek ölçüde ( mm ) kurulur;  `ciz` çağıranın kurduğu
dönüşümle ( 1 çizim mm'si = 1/ölçek kâğıt mm'si ) çizer.  Kalınlık, desen ve
yazı boyları 1/20'deki gibi tanımlıdır, ölçekle büyür ( svg ile aynı:  k ).
"""

import io
import math

from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from cizim import geometri
from cizim import uslup

YAZI_TIPI = "CizimYazi"
#  Yazının maskesi:  kutunun yazıdan taşması ( dxf.MASKE_PAYI ile aynı oran )
MASKE_PAYI = 1.25


def yazi_tipini_kaydet():
    """Liberation Sans'ı reportlab'a bir kez tanıtır ( PDF'e alt kümesi gömülür )."""
    if YAZI_TIPI not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(YAZI_TIPI, uslup.YAZI_DOSYASI))


def _renk(katman):
    return HexColor(uslup.KATMAN[katman].ekran)


def _kalem(c, katman, k, kalinlik=None):
    """Katmanın kalemi:  renk, kalınlık ( kâğıtta mm × 20 × k — çizim birimi )."""
    kal = uslup.KATMAN[katman].kalinlik if kalinlik is None else kalinlik
    c.setStrokeColor(_renk(katman))
    c.setLineWidth(kal * 20 * k)


def _desen(c, el, k):
    """Kesik çizgi:  uslup.DESENLER ( svg.kesik ile aynı sayılar )."""
    ad = "EKSEN" if el["tip"] == "eksen" else uslup.KATMAN[el["katman"]].desen
    if not ad:
        c.setDash()
        return
    d = uslup.DESENLER[ad]
    c.setDash([(abs(v) * d.olcek or uslup.NOKTA) * 20 * k for v in d.tanim])


def _cokgen(c, noktalar, kapali, dolgu, cizgi=True):
    p = c.beginPath()
    p.moveTo(*noktalar[0])
    for q in noktalar[1:]:
        p.lineTo(*q)
    if kapali:
        p.close()
    c.drawPath(p, stroke=1 if cizgi else 0, fill=1 if dolgu else 0)


def _dikdortgen(c, el, k):
    _kalem(c, el["katman"], k)
    _desen(c, el, k)
    dolgu = el["katman"] in _DOLGU
    if dolgu:
        c.setFillColor(white)
    c.rect(el["x"], el["y"], el["g"], el["d"], stroke=1, fill=1 if dolgu else 0)


#  Dolgu yalnız örtmek için ( zemin rengiyle ) — svg.DOLGU
_DOLGU = {"KAPI", "KABIN", "YUK"}


def _bicim(c, el, k):
    """Parçanın gerçek biçimi ( parcalar ):  kapalı çokgenler ( "dolu" kesit
    katmanın renginde ), açık sac profil, "ince" ayrıntı 0,18."""
    renk = _renk(el["katman"])
    if el["katman"] in _DOLGU:
        #  Zarfın içi örtülür ( svg._bicim:  yarım kalem içeriden )
        y = uslup.KATMAN[el["katman"]].kalinlik * 20 * k / 2.0
        if el["g"] > 2 * y and el["d"] > 2 * y:
            c.setFillColor(white)
            c.rect(el["x"] + y, el["y"] + y, el["g"] - 2 * y, el["d"] - 2 * y, stroke=0, fill=1)
    c.setDash()
    for p in el["bicim"]:
        _kalem(c, el["katman"], k, uslup.INCE if p.get("ince") else None)
        dolu = p.get("dolu")
        if dolu:
            c.setFillColor(renk)
        elif el["katman"] in _DOLGU and p.get("kapali", True):
            c.setFillColor(white)
        _cokgen(
            c,
            p["noktalar"],
            p.get("kapali", True),
            dolu or (el["katman"] in _DOLGU and p.get("kapali", True)),
        )


def _tarama(c, el, k):
    """Duvar kesiti ( 45° ) ya da tuğla taraması — uslup.TARAMALAR aralığıyla,
    kutuya kırpılmış;  tuğlanın kenarı da çizilir ( svg gibi )."""
    x0, y0, x1, y1 = el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"]
    c.saveState()
    yol = c.beginPath()
    yol.rect(x0, y0, el["g"], el["d"])
    c.clipPath(yol, stroke=0, fill=0)
    c.setDash()
    c.setStrokeColor(_renk("TARAMA"))
    c.setLineWidth(uslup.KATMAN["TARAMA"].kalinlik * 20 * k)
    if el["tip"] == "tarama":
        a = uslup.TARAMALAR["tarama"].aralik * 20 * k * math.sqrt(2.0)
        #  45° çizgiler ( x − y = sabit ):  kutuyu tarayan sabitler
        s = math.floor((x0 - y1) / a) * a
        while s <= x1 - y0:
            c.line(s + y0, y0, s + y1, y1)
            s += a
    else:
        t = uslup.TARAMALAR["tarama_tugla"].aralik * 20 * k
        sira = math.floor(y0 / t)
        while sira * t <= y1:
            y = sira * t
            c.line(x0, y, x1, y)
            kay = 0.0 if sira % 2 == 0 else t
            x = math.floor((x0 - kay) / (2 * t)) * 2 * t + kay
            while x <= x1:
                c.line(x, y, x, y + t)
                x += 2 * t
            sira += 1
    c.restoreState()
    if el["tip"] == "tarama_tugla":
        _kalem(c, el["katman"], k)
        c.setDash()
        c.rect(x0, y0, el["g"], el["d"], stroke=1, fill=0)


def _ok(c, el, k):
    _kalem(c, el["katman"], k)
    c.setDash()
    c.line(el["x1"], el["y1"], el["x2"], el["y2"])
    dx, dy = el["x2"] - el["x1"], el["y2"] - el["y1"]
    boy = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / boy, dy / boy
    u = 55 * k
    c.setFillColor(_renk(el["katman"]))
    _cokgen(
        c,
        [
            (el["x2"], el["y2"]),
            (el["x2"] - ux * u - uy * u * 0.4, el["y2"] - uy * u + ux * u * 0.4),
            (el["x2"] - ux * u + uy * u * 0.4, el["y2"] - uy * u - ux * u * 0.4),
        ],
        True,
        True,
        cizgi=False,
    )


def _metin(c, x, y, metin, h, renk, aci=0.0, hiza="orta", k=1.0):
    """Yazı:  ( x, y ) yazının ORTASI ( geometri );  taban çizgisi 0,35·h aşağıda
    ( svg ile aynı ).  Önce zemin renginde MASKE — AutoCAD'deki gibi yazının
    kutusu, payı DXF'teki maskeninki ( dxf.MASKE_PAYI:  1,25 → yazı boyunun
    0,125'i ) —, sonra yazı BİR KEZ:  hale yazıyı ikinci kez basınca PDF'ten
    kopyalanan metin çift çıkıyordu ( "SD1850SD1850" )."""
    a = math.radians(aci)
    bx, by = x + 0.35 * h * math.sin(a), y - 0.35 * h * math.cos(a)
    w = pdfmetrics.stringWidth(metin, YAZI_TIPI, h)
    dx = {"orta": -w / 2.0, "sol": 0.0, "sag": -w}.get(hiza, -w / 2.0)
    pay = (MASKE_PAYI - 1.0) / 2.0 * h
    c.saveState()
    c.translate(bx, by)
    c.rotate(aci)
    #  Kutunun altı alt uzantılı harflere ( Ç, Ş, g ), üstü büyük harfe
    c.setFillColor(white)
    c.rect(dx - pay, -0.21 * h - pay, w + 2 * pay, (0.21 + uslup.BUYUK_HARF) * h + 2 * pay, stroke=0, fill=1)
    t = c.beginText(dx, 0.0)
    t.setFont(YAZI_TIPI, h)
    c.setFillColor(renk)
    t.textOut(metin)
    c.drawText(t)
    c.restoreState()


def _olcu(c, el, k):
    """Ölçü çizgisi, iki uçta 45° eğik çizgi + kısa uzatma çizgisi ( uslup ),
    yazı ( svg._olcu ile aynı çizgiler )."""
    renk = _renk("OLCU")
    t, sp = uslup.TIK * 20 * k, uslup.SAPLAMA * 20 * k
    _kalem(c, "OLCU", k)
    c.setDash()
    if el["yon"] == "yatay":
        x1, x2, y = el["a"][0], el["b"][0], el["kot"]
        c.line(x1, y, x2, y)
        uclar = [((x, y - sp), (x, y + sp), (x - t, y - t), (x + t, y + t)) for x in (x1, x2)]
    else:
        y1, y2, x = el["a"][1], el["b"][1], el["kot"]
        c.line(x, y1, x, y2)
        uclar = [((x - sp, y), (x + sp, y), (x + t, y - t), (x - t, y + t)) for y in (y1, y2)]
    for a, b, p, q in uclar:
        c.setLineWidth(uslup.KATMAN["OLCU"].kalinlik * 20 * k)
        c.line(*a, *b)
        c.setLineWidth(uslup.TIK_KALEM * 20 * k)
        c.line(*p, *q)
    yz = el["yazi"]
    _metin(c, yz["x"], yz["y"], el["metin"], yz["h"], renk, yz["aci"], k=k)


def ciz(c, elemanlar, olcek=20):
    """Elemanları çizer ( çizim birimi:  mm, gerçek ölçü — dönüşüm çağıranın ).
    Sıra svg / dxf gibi:  parçalar, ölçüler, en son yazılar ( hale kendinden
    önce çizileni örter )."""
    yazi_tipini_kaydet()
    k = olcek / 20.0
    c.setLineCap(0)
    c.setLineJoin(0)
    sira = {"olcu": 1, "yazi": 2}
    for el in sorted(elemanlar, key=lambda el: sira.get(el["tip"], 0)):
        tur = el["tip"]
        if tur in ("tarama", "tarama_tugla"):
            _tarama(c, el, k)
        elif tur == "dikdortgen":
            (_bicim if "bicim" in el else _dikdortgen)(c, el, k)
        elif tur in ("cizgi", "eksen"):
            _kalem(c, el["katman"], k)
            _desen(c, el, k)
            c.line(el["x1"], el["y1"], el["x2"], el["y2"])
        elif tur == "daire":
            _kalem(c, el["katman"], k)
            _desen(c, el, k)
            c.circle(el["x"], el["y"], el["r"], stroke=1, fill=0)
        elif tur == "ok":
            _ok(c, el, k)
        elif tur == "olcu":
            _olcu(c, el, k)
        elif tur == "yazi":
            _metin(
                c,
                el["x"],
                el["y"],
                el["metin"],
                el["yukseklik"],
                _renk(el["katman"]),
                el.get("aci", 0),
                el.get("hiza", "orta"),
                k,
            )
    c.setDash()


def yerlestir(c, elemanlar, olcek, taban, yer):
    """Çizimi kâğıda koyar:  çizimin `taban` noktası ( mm, gerçek ölçü ) kâğıtta
    `yer`e ( kâğıt mm'si ) gelir, 1/ölçek küçültülür."""
    c.saveState()
    c.translate(yer[0] * mm, yer[1] * mm)
    c.scale(mm / olcek, mm / olcek)
    c.translate(-taban[0], -taban[1])
    ciz(c, elemanlar, olcek)
    c.restoreState()


#  A serisi ( ISO 216, mm ):  her çizim sığdığı en küçük sayfaya
A_SERISI = (
    ("A4", 210.0, 297.0),
    ("A3", 297.0, 420.0),
    ("A2", 420.0, 594.0),
    ("A1", 594.0, 841.0),
    ("A0", 841.0, 1189.0),
)
SAYFA_KENARI = 10.0  # mm


def sayfa_boyu(g, y):
    """( ad, en, boy ) — g × y mm'lik çizimin ( kenar payıyla ) sığdığı en küçük
    A sayfası;  yatay ya da dikey, hangisi sığarsa ( önce yatay )."""
    g2, y2 = g + 2 * SAYFA_KENARI, y + 2 * SAYFA_KENARI
    for ad, kisa, uzun in A_SERISI:
        for en, boy in ((uzun, kisa), (kisa, uzun)):
            if g2 <= en + 1e-6 and y2 <= boy + 1e-6:
                return ad, en, boy
    return "özel", g2, y2


def sayfalar(cizimler, baslik="Asansör çizimleri") -> bytes:
    """Her çizim kendi A sayfasında, ortada ( cizimler:  [ ( ad, başlık, ölçek,
    elemanlar ) ] — pafta.cizim_listesi gibi çerçeveli ).  Dönen:  PDF baytları."""
    akis = io.BytesIO()
    c = canvas.Canvas(akis, pageCompression=1)
    c.setTitle(baslik)
    c.setCreator("Asansör çizim modülü")
    for _ad, _baslik, olcek, e in cizimler:
        x0, y0, x1, y1 = geometri.sinir(e)
        g, y = (x1 - x0) / olcek, (y1 - y0) / olcek
        _a, en, boy = sayfa_boyu(g, y)
        c.setPageSize((en * mm, boy * mm))
        yerlestir(c, e, olcek, (x0, y0), ((en - g) / 2.0, (boy - y) / 2.0))
        c.showPage()
    c.save()
    return akis.getvalue()
