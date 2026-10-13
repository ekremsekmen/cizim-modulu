"""PDF ÇIKTISI — çizimler ( cizim/pdf.py ) ve paftanın şeridi ( ciktilar/pafta_pdf.py ).

12 Eki'ye kadar çizimlerin PDF'i ezdxf'in önizleme SVG'sinden üretiliyordu:
yazılar eğri ( aranmaz ), tek sayfa 4.078 × 610 mm, 7,8 MB, hesap sayfaları
yoktu.  Şimdi:  çizimler modelden ( ekranla aynı üslup ), yazılar gerçek ve
bir kez basılır, hesap sayfaları programın kendi PDF'leri;  paket ikisini de
taşır ( şerit + her çizim kendi sayfasında )."""

import io
import unittest
import zipfile

import ezdxf
from pypdf import PdfReader

from cizim import eleman
from cizim import pafta
from cizim import pdf
from cizim import uslup
from ciktilar import dxf_cikti
from testler import test_yerlesim_saglamligi

MM = 72 / 25.4


def _metin(b):
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(b)).pages)


class Cizimler(unittest.TestCase):
    def test_yazi_bir_kez_ve_gomulu(self):
        e = [
            eleman.olcu("yatay", (0, 0), (2100, 0), 500, "SW2100", yazi={"x": 1050, "y": 540}),
            eleman.yazi(1000, 200, "KARŞI AĞIRLIK"),
            eleman.dikdortgen("KUYU-DUVAR", 0, 0, 150, 1000, tip="tarama"),
            eleman.cizgi("EKSEN", 0, 0, 2000, 0, tip="eksen"),
        ]
        b = pdf.sayfalar([("plan", "PLAN", 20, e)])
        m = _metin(b)
        #  Hale yazıyı ikinci kez basmaz ( maske dikdörtgen )
        self.assertEqual(m.count("SW2100"), 1, m)
        self.assertEqual(m.count("KARŞI AĞIRLIK"), 1, m)
        sayfa = PdfReader(io.BytesIO(b)).pages[0]
        fontlar = [str(f["/BaseFont"]) for f in sayfa["/Resources"]["/Font"].values()]
        #  Gömülü alt küme ( "AAAAAA+LiberationSans" ) — Arial'le aynı enler
        self.assertTrue(any(f.endswith("+LiberationSans") for f in fontlar), fontlar)

    def test_sayfa_a_serisinden(self):
        self.assertEqual(pdf.sayfa_boyu(150, 100)[0], "A4")
        self.assertEqual(pdf.sayfa_boyu(150, 100)[1:], (297.0, 210.0))  # yatay önce
        self.assertEqual(pdf.sayfa_boyu(380, 260)[0], "A3")
        self.assertEqual(pdf.sayfa_boyu(200, 560)[:3], ("A2", 420.0, 594.0))  # dikey
        self.assertEqual(pdf.sayfa_boyu(5000, 100)[0], "özel")

    def test_pafta_cizimleri_kendi_sayfalarinda(self):
        g, hata = test_yerlesim_saglamligi.gecerli_duzen(800, "Sağ", True)
        self.assertIsNotNone(g, hata)
        liste = pafta.cizim_listesi(g)
        b = pdf.sayfalar(liste)
        r = PdfReader(io.BytesIO(b))
        self.assertEqual(len(r.pages), len(liste))
        boylar = {
            (round(float(p.mediabox.width) / MM), round(float(p.mediabox.height) / MM)) for p in r.pages
        }
        a_serisi = {
            (round(en), round(boy))
            for _a, kisa, uzun in pdf.A_SERISI
            for en, boy in ((kisa, uzun), (uzun, kisa))
        }
        self.assertLessEqual(boylar, a_serisi)
        m = _metin(b)
        for kod in ("SW", "SD", "PLW", "DW", "OH", "KISALTMALAR", "VERİLER"):
            self.assertIn(kod, m)
        #  Küçük:  eskisi tek sayfada 7,8 MB'tı
        self.assertLess(len(b), 400 * 1024)

    def test_ekranla_ayni_uslup(self):
        #  Tarama aralığı ve kalınlık uslup'tan:  tek kaynak ( svg ve dxf de )
        self.assertEqual(uslup.TARAMALAR["tarama"].aralik, 3.0)
        self.assertTrue(pdf.YAZI_TIPI)


class Serit(unittest.TestCase):
    """Paketteki şeridin PDF'i:  DXF paftasıyla aynı yerleşim."""

    @classmethod
    def setUpClass(cls):
        from hesap_girdi import ASANSOR, ORTAK, SABITLER
        from motor.uygulama import uygulama_hesabi
        from ciktilar import kapak_cikti, pafta_pdf, pdf_cikti
        from uclar import cizim_uclari, uygulama_istegi

        veri = {
            "asansorler": [dict(ASANSOR, siginma_tipi_dip="Yatarak")],
            "proje_geneli": dict(ORTAK),
            "sabitler": dict(SABITLER),
        }
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        cls.paftalar = [
            ("Kapak", kapak_cikti.pdf_baytlari({"project_title": "ASANSÖR UYGULAMA PROJESİ"})),
            ("Uygulama Projesi", pdf_cikti.uygulama_pdf(s)),
        ]
        ((g, _h),) = cizim_uclari.girdiler(veri, asansorler, ortak, s, "DENEME")
        dxf, _s, _t = dxf_cikti._proje_cizimi(dxf_cikti.sayfalari_topla(cls.paftalar))
        cls.dxf = cizim_uclari.paftaya_ekle([g])(dxf)
        cls.pdf = pafta_pdf.serit(cls.dxf, cls.paftalar, pafta.bloklar([g]))

    def test_tek_sayfa_paftanin_boyunda(self):
        r = PdfReader(io.BytesIO(self.pdf))
        self.assertEqual(len(r.pages), 1)
        en, boy = float(r.pages[0].mediabox.width) / MM, float(r.pages[0].mediabox.height) / MM
        #  Şablonun bandı 600 mm yüksek;  hesap sayfaları ve çizimler sağa uzatır
        self.assertAlmostEqual(boy, 600 + 2 * 5.0 + 4.0, delta=6.0)
        self.assertGreater(en, 3242.0)

    def test_hesap_sayfalari_ve_cizimler_yazi_olarak(self):
        m = _metin(self.pdf)
        self.assertIn("ASANSÖR UYGULAMA PROJESİ", m)  # kapak
        self.assertIn("HESAPLARI", m)  # hesap sayfaları ( kendi PDF'leri )
        for kod in ("SW2100", "KISALTMALAR", "KUYU PLANI"):
            self.assertIn(kod, m)  # çizimler modelden
        self.assertIn("ASANSÖR MONTAJINDAN SORUMLU", m)  # şablonun notları

    def test_kapak_hucresinde_sablon_cizgisi_kalmaz(self):
        #  Şablonun antetinden kalan iki çizgi ( ucu iç çerçevenin 1,5 mm
        #  dışında ) kapağın "ADI" satırının üstünden geçiyordu ( 13 Eki )
        d = ezdxf.read(io.StringIO(self.dxf.decode("utf-8")))
        x0, y0, x1, y1 = dxf_cikti.KAPAK_IC
        icinde = [
            e
            for e in d.modelspace().query("LINE")
            if e.dxf.layer not in (dxf_cikti.KATMAN_CIZGI, dxf_cikti.KATMAN_YAZI)
            and any(x0 + 0.5 < p.x < x1 - 0.5 and y0 + 0.5 < p.y < y1 - 0.5 for p in (e.dxf.start, e.dxf.end))
        ]
        self.assertEqual(icinde, [])


class Paket(unittest.TestCase):
    def test_paket_pdfleri_tasir(self):
        from hesap_girdi import ASANSOR, ORTAK, SABITLER
        from uclar import uygulama_uclari

        veri = {
            "asansorler": [dict(ASANSOR, siginma_tipi_dip="Yatarak")],
            "proje_geneli": dict(ORTAK),
            "sabitler": dict(SABITLER),
            "asansor": 0,
        }
        z = zipfile.ZipFile(io.BytesIO(uygulama_uclari.indir_uygulama_dwg(veri).body))
        adlar = z.namelist()
        self.assertTrue(any(a.endswith("Uygulama Projesi.pdf") for a in adlar), adlar)
        self.assertTrue(any(a.endswith("çizimler.pdf") for a in adlar), adlar)
        self.assertIn("Paftanın PDF'i", z.read("OKUBENI.txt").decode())


if __name__ == "__main__":
    unittest.main()
