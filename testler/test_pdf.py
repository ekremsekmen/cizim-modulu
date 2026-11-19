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
        liste = pafta.bloklar(g)
        b = pdf.sayfalar(liste, kunyeler=pafta.kunyeler(g))
        r = PdfReader(io.BytesIO(b))
        self.assertEqual(len(r.pages), len(liste))
        self.assertEqual(len(pafta.kunyeler(g)), len(liste))
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
        #  Her sayfada antet ( 13 Eki ):  proje, asansör, çizim, ölçek, sayfa no
        n = len(liste)
        for i, s in enumerate(r.pages):
            m_ = s.extract_text()
            self.assertIn(f"SAYFA  {i + 1} / {n}", m_)
            self.assertIn(g["proje"]["asansor"], m_)
            #  Çizen / onaylayan alanı yok ( kullanıcı 13 Eki )
            self.assertNotIn("ÇİZEN", m_)
            self.assertNotIn("ONAYLAYAN", m_)
        self.assertIn("ÖLÇEK  1/50", r.pages[0].extract_text())
        self.assertIn("ÖLÇEK  —", r.pages[-1].extract_text())  # veri tablosu

    def test_antet_basligi_sigmazsa_aciklamasi_duser(self):
        uzun = (
            "KUYU ÜSTÜ PLANI  F-F  ( makine dairesiz — kuyu tepesinden yatay kesit, " + "çok uzun " * 8 + ")"
        )
        metin = [x["metin"] for x in pdf.antet("P", "A1", uzun, "1/20", "SAYFA  1 / 1") if x["tip"] == "yazi"]
        self.assertIn("KUYU ÜSTÜ PLANI  F-F", metin)
        #  Proje adı boşsa hücre boş kalır ( yazı yok )
        metin = [
            x["metin"] for x in pdf.antet("", "A1", "PLAN", "1/20", "SAYFA  1 / 1") if x["tip"] == "yazi"
        ]
        self.assertNotIn("", metin)

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
        cls.g = g
        dxf, _s, _t = dxf_cikti._proje_cizimi(dxf_cikti.sayfalari_topla(cls.paftalar))
        cls.dxf = cizim_uclari.paftaya_ekle([g])(dxf)
        cls.pdf = pafta_pdf.serit(cls.dxf, cls.paftalar, pafta.bloklar([g]))
        #  90 cm'lik rulo ( 19 Kas ):  hesap sayfaları, çizimler ve PDF aynı kâğıda
        dxf9, _s, _t = dxf_cikti._proje_cizimi(dxf_cikti.sayfalari_topla(cls.paftalar), kagit=900)
        cls.dxf9 = cizim_uclari.paftaya_ekle([g])(dxf9, 900)
        cls.pdf9 = pafta_pdf.serit(cls.dxf9, cls.paftalar, pafta.bloklar([g], 900), kagit=900)

    def _cerceve_boyu(self, dxf, kagit):
        d = ezdxf.read(io.StringIO(dxf.decode("utf-8")))
        ust = pafta.ust_kenar(kagit)
        xs = [
            p.x
            for e in d.modelspace().query("LINE")
            for p in (e.dxf.start, e.dxf.end)
            if abs(p.y - ust) < 0.5
        ]
        return max(xs) - min(xs)

    def test_tek_sayfa_paftanin_boyunda(self):
        #  Sayfa çerçeve ve 5 mm payı:  60 cm'lik rulonun eninde ( 610 mm — 19 Kas'a dek
        #  kapağın A4'ü yüzünden 614 mm'ydi ), 90 cm'de 910;  boyu şeridin boyu
        for pdf_, dxf, kagit in ((self.pdf, self.dxf, 600), (self.pdf9, self.dxf9, 900)):
            with self.subTest(kagit=kagit):
                r = PdfReader(io.BytesIO(pdf_))
                self.assertEqual(len(r.pages), 1)
                en, boy = float(r.pages[0].mediabox.width) / MM, float(r.pages[0].mediabox.height) / MM
                self.assertAlmostEqual(boy, kagit + 2 * 5.0, delta=0.05)
                self.assertAlmostEqual(en, self._cerceve_boyu(dxf, kagit) + 2 * 5.0, delta=0.05)
        #  90 cm'de üç A4 satırı:  şerit 60 cm'dekinden kısa
        self.assertLess(self._cerceve_boyu(self.dxf9, 900), self._cerceve_boyu(self.dxf, 600))

    def test_baska_kagida_dizilmis_dxf(self):
        """Şeridin PDF'i DXF'in kâğıdıyla kurulur:  ayrışırsa ( 90 cm'lik DXF'e 60 cm'lik
        yerleşim ) PDF üretilmez — sayfalar çizimlerin üstüne binerdi;  çizimler 60 cm'lik
        hesap DXF'ine 90 cm'le eklenmez ( çerçeve bulunamaz )."""
        from ciktilar import pafta_pdf
        from uclar import cizim_uclari

        with self.assertRaisesRegex(ValueError, "ayrıştı"):
            pafta_pdf.serit(self.dxf9, self.paftalar, pafta.bloklar([self.g], 900), kagit=600)
        dxf, _s, _t = dxf_cikti._proje_cizimi(dxf_cikti.sayfalari_topla(self.paftalar))
        with self.assertRaisesRegex(ValueError, "çerçevesi bulunamadı"):
            cizim_uclari.paftaya_ekle([self.g])(dxf, 900)

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
        self.assertIn("60 cm enindeki rulo", z.read("OKUBENI.txt").decode())

    def test_kagit_eni(self):
        """İstekteki kâğıt eni ( 19 Kas ):  900 → çerçeve 900 mm, şeridin PDF'i 910 mm ve
        OKUBENI söyler;  600 / 900 dışı değer hesaptan önce reddedilir ( paket inmez )."""
        import json

        from hesap_girdi import ASANSOR, ORTAK, SABITLER
        from uclar import uygulama_uclari

        veri = {
            "asansorler": [dict(ASANSOR, siginma_tipi_dip="Yatarak")],
            "proje_geneli": dict(ORTAK),
            "sabitler": dict(SABITLER),
            "asansor": 0,
        }
        for yanlis in (750, "60", True):
            with self.subTest(kagit=yanlis):
                yanit = uygulama_uclari.indir_uygulama_dwg(dict(veri, kagit=yanlis))
                self.assertIn("KÂĞIT ENİ", json.loads(yanit.body)["hata"])
        z = zipfile.ZipFile(io.BytesIO(uygulama_uclari.indir_uygulama_dwg(dict(veri, kagit=900)).body))
        self.assertIn("90 cm enindeki rulo", z.read("OKUBENI.txt").decode())
        d = ezdxf.read(
            io.StringIO(z.read(next(a for a in z.namelist() if a.endswith(".dxf"))).decode("utf-8"))
        )
        sol = [
            e
            for e in d.modelspace().query("LINE")
            if abs(e.dxf.start.x - pafta.BANT[0]) < 0.5 and abs(e.dxf.end.x - pafta.BANT[0]) < 0.5
        ]
        self.assertEqual([round(abs(e.dxf.end.y - e.dxf.start.y)) for e in sol], [900])
        #  Hesap sayfaları üç satırda, çizimler çerçevenin içinde
        self.assertEqual(len({round(b[1], 1) for b in dxf_cikti.a4_cerceveleri(d.modelspace())}), 3)
        serit = next(a for a in z.namelist() if a.endswith("Uygulama Projesi.pdf") and "/" not in a)
        kagit = PdfReader(io.BytesIO(z.read(serit))).pages[0].mediabox
        self.assertAlmostEqual(float(kagit.height) / MM, 910.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
