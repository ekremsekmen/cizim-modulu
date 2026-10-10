"""ÇİZİM ELEMANLARI ( cizim/eleman.py ) — katmanların tek listesi:  SVG ve
DXF her katmanı tanır, çizimler yalnız bu katmanlara çizer."""

import unittest

from cizim import dxf as CDX
from cizim import eleman as CEL
from cizim import svg as CSV
from testler import altin_cizim as A


class Katmanlar(unittest.TestCase):
    def test_svg_ve_dxf_her_katmani_tanir(self):
        self.assertEqual(set(CSV.KALEM), set(CEL.KATMANLAR))
        self.assertEqual(set(CDX.KATMAN), set(CEL.KATMANLAR))
        self.assertEqual(len(CEL.KATMANLAR), len(set(CEL.KATMANLAR)))

    def test_cizimler_yalniz_bilinen_katmanlara_cizer(self):
        #  Altın çıktıdaki bütün düzenlerin bütün çizimleri ( 30 düzen, ~10 çizim )
        bilinen = set(CEL.KATMANLAR)
        for ad, k in A.oku().items():
            for c, ciz in (k.get("cizimler") or {}).items():
                with self.subTest(duzen=ad, cizim=c):
                    self.assertEqual({e["katman"] for e in ciz["elemanlar"]} - bilinen, set())


class Kurucular(unittest.TestCase):
    def test_elemanlar_sayilari_float_yazar(self):
        self.assertEqual(
            CEL.dikdortgen("RAY", 1, 2, 3, 4, ad="r"),
            {"tip": "dikdortgen", "katman": "RAY", "x": 1.0, "y": 2.0, "g": 3.0, "d": 4.0, "ad": "r"},
        )
        o = CEL.olcu("yatay", (0, 0), (1500, 0), 300)
        self.assertEqual((o["metin"], o["uzunluk"], o["kot"]), ("1500", 1500, 300.0))
        self.assertAlmostEqual(CEL.yazi(0, 0, "A", 52)["yukseklik"], CEL.OLCU_YAZI)

    def test_turkce_buyuk_harf(self):
        self.assertEqual(CEL.buyuk("Kabin altı · Dik duruş"), "KABİN ALTI · DİK DURUŞ")
