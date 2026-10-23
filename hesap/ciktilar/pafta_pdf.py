# -*- coding: utf-8 -*-
"""
PAFTANIN PDF'İ — TİP PROJE FORMATI şeridi, paketteki DXF paftasının aynısı.

Yerleşimin tek kaynağı DXF paftasıdır ( dxf_cikti._formata_yerlestir +
cizim/pafta.birlestir ):  PDF onu kâğıda aynen çizer, iki yerde DAHA İYİSİNİ
koyar:

  · HESAP SAYFALARI ( kapak dahil ) programın KENDİ PDF'lerinden, DXF'teki
    yerlerine vektörel gömülür ( pypdf ) — DXF'tekiler o PDF'lerden geri
    dönüştürülmüş çizgi ve yazılardır;
  · ÇİZİMLER modelden çizilir ( cizim/pdf — ekranla aynı üslup, gerçek yazı ),
    DXF'teki blokların yerinde ve ölçeğinde.

Şablonun çerçevesi, anteti ve notları DXF'ten çizilir ( LINE, LWPOLYLINE,
TEXT, MTEXT — şablonda başka tür yok );  yazılar gerçek yazı:  Times'ın
yerine Liberation Serif, Arial'in yerine Liberation Sans ( harf enleri aynı ).
Renk siyah ( basılı pafta ), kalınlık katmanın kalınlığı.

12 Eki'ye kadar paftanın PDF'i ezdxf'in önizleme SVG'sinden üretiliyordu
( ornekler/uret.py ):  yazılar eğri, 7,8 MB, yalnız çizimler.
"""

import io
import math
import os
import tempfile

import ezdxf
from ezdxf import bbox
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import black
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from cizim import pafta
from cizim import pdf
from cizim import uslup
from ciktilar import dxf_cikti

KENAR = 5.0  # şeridin çevresindeki boşluk ( mm )
SANS, SERIF = "PaftaSans", "PaftaSerif"
#  Büyük harf yüksekliği / em:  DXF'te TEXT yüksekliği büyük harf yüksekliğidir
#  ( cizim/dxf.BUYUK_HARF );  Liberation Sans = Arial 0,716, Liberation Serif =
#  Times 0,662
_BUYUK_HARF = {SANS: 0.716, SERIF: 0.662}
#  Katmanın kalınlığı yoksa ( DEFAULT ) AutoCAD'in varsayılanı
VARSAYILAN_KALINLIK = 0.25


def _yazi_tiplerini_kaydet():
    for ad, dosya in ((SANS, uslup.YAZI_DOSYASI), (SERIF, uslup.SERIF_DOSYASI)):
        if ad not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(ad, dosya))


def _oku(dxf_baytlari):
    with tempfile.TemporaryDirectory() as t:
        yol = os.path.join(t, "pafta.dxf")
        with open(yol, "wb") as f:
            f.write(dxf_baytlari)
        return ezdxf.readfile(yol)


def sayfa_listesi(paftalar):
    """Hesap paftalarının sayfaları, sırayla:  [ { ad, genislik, yukseklik ( pt ),
    sayfa ( pypdf ) } ] — dxf_cikti.sayfalari_topla ile aynı sıra ve boy."""
    out = []
    for ad, ham in paftalar:
        if not ham:
            continue
        for s in PdfReader(io.BytesIO(ham)).pages:
            k = s.mediabox
            out.append(
                {
                    "ad": ad,
                    "genislik": float(k.width),
                    "yukseklik": float(k.height),
                    "sayfa": s,
                    "kok": (float(k.left), float(k.bottom)),
                }
            )
    return out


def _cizilecek(e):
    """Şeridin DXF'ten çizilen varlığı mı:  hesap sayfalarının DXF kopyası
    ( kendi PDF'leri gömülür ) ve çizimlerin blokları ( modelden ) değil."""
    if e.dxf.layer in (dxf_cikti.KATMAN_CIZGI, dxf_cikti.KATMAN_YAZI):
        return False
    if e.dxftype() == "INSERT":
        return False
    return e.dxftype() in ("LINE", "LWPOLYLINE", "TEXT", "MTEXT")


def _kalinlik(d, e):
    lw = e.dxf.get("lineweight", -1)
    if lw < 0:
        katman = d.layers.get(e.dxf.layer) if e.dxf.layer in d.layers else None
        lw = katman.dxf.get("lineweight", -3) if katman is not None else -3
    return VARSAYILAN_KALINLIK if lw < 0 else lw / 100.0


def _yazi_tipi(d, stil_adi, ham=""):
    """Şablonun yazı biçimi:  Times ( times.ttf ya da MTEXT'te \\fTimes ) →
    Serif, öbürleri ( Arial ) → Sans."""
    if "Times" in ham:
        return SERIF
    stil = d.styles.get(stil_adi) if stil_adi and stil_adi in d.styles else None
    dosya = str(stil.dxf.get("font", "")).lower() if stil is not None else ""
    return SERIF if dosya.startswith("times") else SANS


def _yazi(c, metin, x, y, yukseklik, yazi_tipi, aci=0.0, hiza=0, dusey=0, genislik=1.0):
    """Tek satır:  ( x, y ) hizalama noktası ( DXF ), yükseklik büyük harf ( mm ).
    hiza 0 sol · 1 orta · 2 sağ;  dusey 0 taban · 1 alt · 2 orta · 3 üst."""
    if not metin.strip():
        return
    em = yukseklik / _BUYUK_HARF[yazi_tipi]
    w = pdfmetrics.stringWidth(metin, yazi_tipi, em) * genislik
    dx = {0: 0.0, 1: -w / 2.0, 2: -w}.get(hiza, 0.0)
    dy = {0: 0.0, 1: 0.21 * em, 2: -yukseklik / 2.0, 3: -yukseklik}.get(dusey, 0.0)
    c.saveState()
    c.translate(x, y)
    c.rotate(aci)
    t = c.beginText(dx, dy)
    t.setFont(yazi_tipi, em)
    if abs(genislik - 1.0) > 1e-6:
        t.setHorizScale(genislik * 100.0)
    t.textOut(metin)
    c.drawText(t)
    c.restoreState()


def _sablonu_ciz(c, d):
    """Şeridin DXF'ten gelen varlıkları ( çizim birimi:  pafta mm )."""
    c.setStrokeColor(black)
    c.setFillColor(black)
    c.setLineCap(1)
    for e in d.modelspace():
        if not _cizilecek(e):
            continue
        t = e.dxftype()
        if t == "LINE":
            c.setLineWidth(_kalinlik(d, e))
            a, b = e.dxf.start, e.dxf.end
            c.line(a.x, a.y, b.x, b.y)
        elif t == "LWPOLYLINE":
            c.setLineWidth(_kalinlik(d, e))
            nok = [(p[0], p[1]) for p in e.get_points("xy")]
            if len(nok) < 2:
                continue
            yol = c.beginPath()
            yol.moveTo(*nok[0])
            for q in nok[1:]:
                yol.lineTo(*q)
            if e.closed:
                yol.close()
            c.drawPath(yol, stroke=1, fill=0)
        elif t == "TEXT":
            hiza = e.dxf.get("halign", 0)
            dusey = e.dxf.get("valign", 0)
            yer = e.dxf.insert if (hiza, dusey) == (0, 0) else e.dxf.get("align_point", e.dxf.insert)
            _yazi(
                c,
                e.plain_text(),
                yer.x,
                yer.y,
                e.dxf.height,
                _yazi_tipi(d, e.dxf.get("style")),
                e.dxf.get("rotation", 0.0),
                min(hiza, 2) if hiza in (0, 1, 2) else 1,
                dusey if hiza != 4 else 2,
                e.dxf.get("width", 1.0),
            )
        elif t == "MTEXT":
            _mtext(c, d, e)


def _kaydir(satir, genislik, yazi_tipi, em):
    """Sözcük sözcük kaydırma ( AutoCAD'in MTEXT'i gibi:  sütun genişliği )."""
    if genislik <= 0 or pdfmetrics.stringWidth(satir, yazi_tipi, em) <= genislik:
        return [satir]
    out, simdi = [], ""
    for soz in satir.split(" "):
        aday = f"{simdi} {soz}" if simdi else soz
        if simdi and pdfmetrics.stringWidth(aday, yazi_tipi, em) > genislik:
            out.append(simdi)
            simdi = soz
        else:
            simdi = aday
    return out + [simdi]


def _mtext(c, d, m):
    """Çok satırlı yazı:  paragraflar \\P'den, uzun satır MTEXT'in sütun
    genişliğinde kaydırılır ( şablonun notları — AutoCAD de kaydırır ), satır
    aralığı yükseklik × 5/3 ( AutoCAD )."""
    h = m.dxf.get("char_height", 2.5)
    yt = _yazi_tipi(d, m.dxf.get("style"), m.text)
    em = h / _BUYUK_HARF[yt]
    satirlar = [
        parca
        for satir in m.plain_text().split("\n")
        for parca in _kaydir(satir, m.dxf.get("width", 0.0), yt, em)
    ]
    ap = m.dxf.get("attachment_point", 1)
    hiza = (ap - 1) % 3
    adim = h * 5.0 / 3.0
    toplam = h + adim * (len(satirlar) - 1)
    ust = {0: 0.0, 1: toplam / 2.0, 2: toplam}[(ap - 1) // 3]
    p, aci = m.dxf.insert, m.dxf.get("rotation", 0.0)
    a = math.radians(aci)
    for i, satir in enumerate(satirlar):
        #  i. satırın taban çizgisi:  kutunun üstünden h + i × adım aşağı
        ofs = ust - h - i * adim
        _yazi(c, satir, p.x - ofs * math.sin(a), p.y + ofs * math.cos(a), h, yt, aci, hiza, 0)


def _cizimleri_ciz(c, d, cizimler):
    """Çizimler modelden, DXF'teki blokların yerinde:  blok "CIZIM_<AD>"ın
    taban noktası ( çizim mm'si ) INSERT'in yerine ( pafta mm'si ) 1/ölçek."""
    ekler = {e.dxf.name: e for e in d.modelspace().query("INSERT")}
    for ad, _baslik, olcek, e in cizimler:
        ins = ekler.get(pafta.blok_adi(ad))
        if ins is None:
            raise ValueError(f"Paftada {pafta.blok_adi(ad)} bloğu yok — DXF ile çizimler ayrışmış.")
        taban = d.blocks.get(ins.dxf.name).block.dxf.base_point
        c.saveState()
        c.translate(ins.dxf.insert.x, ins.dxf.insert.y)
        c.scale(1.0 / olcek, 1.0 / olcek)
        c.translate(-taban.x, -taban.y)
        pdf.ciz(c, e, olcek)
        c.restoreState()


def serit(dxf_baytlari, paftalar, cizimler=(), baslik="Asansör projesi", elektrikler=()) -> bytes:
    """Paftanın PDF'i:  tek sayfa, paftanın boyunda ( 1:1, mm ).

    dxf_baytlari:  paketin DXF paftası ( çizimler eklenmiş ).  paftalar:  hesap
    paftalarının PDF'leri [ ( ad, bayt ) ] — DXF'e dizilenlerin AYNISI.
    cizimler:  pafta.bloklar( g ) — DXF'teki bloklar.  elektrikler:  elektrik
    projeleri ( cizim/elektrik.pafta_sayfalari — DXF'te alt satırın başında,
    hesap sayfaları onlara göre dizilir )."""
    _yazi_tiplerini_kaydet()
    d = _oku(dxf_baytlari)
    sayfalar = sayfa_listesi(paftalar)
    yerler, _uzatma, _tasti = dxf_cikti.sayfa_yerleri(sayfalar, len(elektrikler))
    #  Kâğıt:  çizilen her şeyin kutusu ( şablonun uzatılmış çerçevesi dahil )
    kutu = bbox.extents([e for e in d.modelspace() if _cizilecek(e)], fast=True)
    x0, y0 = kutu.extmin.x - KENAR, kutu.extmin.y - KENAR
    x1, y1 = kutu.extmax.x + KENAR, kutu.extmax.y + KENAR
    for (ox, oy, _k), s in zip(yerler, sayfalar):
        x0, y0 = min(x0, ox - KENAR), min(y0, oy - KENAR)
        x1 = max(x1, ox + s["genislik"] * dxf_cikti.PT_MM + KENAR)
        y1 = max(y1, oy + s["yukseklik"] * dxf_cikti.PT_MM + KENAR)
    akis = io.BytesIO()
    c = canvas.Canvas(akis, pagesize=((x1 - x0) * mm, (y1 - y0) * mm), pageCompression=1)
    c.setTitle(baslik)
    c.setCreator("Asansör hesap ve çizim programı")
    c.saveState()
    c.scale(mm, mm)
    c.translate(-x0, -y0)
    _sablonu_ciz(c, d)
    _cizimleri_ciz(c, d, list(cizimler) + list(elektrikler))
    c.restoreState()
    c.showPage()
    c.save()
    #  Hesap sayfaları:  kendi PDF'leri, DXF'teki yerlerine ( pt )
    yazar = PdfWriter(clone_from=PdfReader(io.BytesIO(akis.getvalue())))
    kagit = yazar.pages[0]
    for (ox, oy, _k), s in zip(yerler, sayfalar):
        tx = (ox - x0) * mm - s["kok"][0]
        ty = (oy - y0) * mm - s["kok"][1]
        kagit.merge_transformed_page(s["sayfa"], Transformation().translate(tx, ty))
    yazar.compress_identical_objects()
    cikti = io.BytesIO()
    yazar.write(cikti)
    return cikti.getvalue()


def paket_pdfleri(paftalar, gler=(), elektrikler=()):
    """ "Projeyi paketle"nin PDF işlemi ( dxf_cikti.proje_paketi ):  son DXF'ten
    ( paftanın şeridi , çizimlerin sayfaları — çizim yoksa None ).  gler:
    asansörlerin çizim girdileri ( DXF'e eklenenlerle aynı — pafta.bloklar );
    elektrikler:  elektrik projeleri ( DXF'tekilerin aynısı ) — ayrı sayfalı
    PDF'te çizimlerin ardından, kendi çerçeveleriyle ( antetsiz )."""

    def islem(dxf_baytlari):
        cizimler = pafta.bloklar(list(gler)) if gler else []
        kunyeler = pafta.kunyeler(list(gler)) if gler else []
        tum = cizimler + list(elektrikler)
        kunyeler += [{"kendi_sayfasi": True} for _ in elektrikler]
        sayfalar = pdf.sayfalar(tum, kunyeler=kunyeler) if tum else None
        return serit(dxf_baytlari, paftalar, cizimler, elektrikler=elektrikler), sayfalar

    return islem
