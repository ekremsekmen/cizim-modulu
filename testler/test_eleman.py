"""ÇİZİM ELEMANLARI ( cizim/eleman.py ) — katmanların tek listesi:  SVG ve
DXF her katmanı tanır, çizimler yalnız bu katmanlara çizer."""

import unittest

from cizim import dxf
from cizim import eleman
from cizim import svg
from cizim import uslup
from testler import altin_cizim


class Katmanlar(unittest.TestCase):
    def test_svg_ve_dxf_her_katmani_tanir(self):
        self.assertEqual(set(uslup.KATMAN), set(eleman.KATMANLAR))
        d = dxf.belge([])
        self.assertTrue(all(k in d.layers for k in eleman.KATMANLAR))
        self.assertTrue(all(svg.kalem(k) for k in eleman.KATMANLAR))
        self.assertEqual(len(eleman.KATMANLAR), len(set(eleman.KATMANLAR)))

    def test_cizimler_yalniz_bilinen_katmanlara_cizer(self):
        #  Altın çıktıdaki bütün düzenlerin bütün çizimleri ( 30 düzen, ~10 çizim )
        bilinen = set(eleman.KATMANLAR)
        for ad, k in altin_cizim.oku().items():
            for c, ciz in (k.get("cizimler") or {}).items():
                with self.subTest(duzen=ad, cizim=c):
                    self.assertEqual({e["katman"] for e in ciz["elemanlar"]} - bilinen, set())


class Kurucular(unittest.TestCase):
    def test_elemanlar_sayilari_float_yazar(self):
        self.assertEqual(
            eleman.dikdortgen("RAY", 1, 2, 3, 4, ad="r"),
            {"tip": "dikdortgen", "katman": "RAY", "x": 1.0, "y": 2.0, "g": 3.0, "d": 4.0, "ad": "r"},
        )
        o = eleman.olcu("yatay", (0, 0), (1500, 0), 300)
        self.assertEqual((o["metin"], o["uzunluk"], o["kot"]), ("1500", 1500, 300.0))
        self.assertEqual(eleman.yazi(0, 0, "A")["yukseklik"], uslup.NORMAL)

    def test_turkce_buyuk_harf(self):
        self.assertEqual(eleman.buyuk("Kabin altı · Dik duruş"), "KABİN ALTI · DİK DURUŞ")
