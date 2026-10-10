"""TEMEL YARDIMCILAR ( temel.py ) — her katmanın ortak sayı ve kutu denetimi."""

import math
import unittest

from temel import bos_mu, eleman_kutusu, kutu_merkezi, ortusur, sayi_mi


class Sayi(unittest.TestCase):
    def test_sayi(self):
        for v in (0, 1, -3, 2.5, 1e9):
            self.assertTrue(sayi_mi(v), v)

    def test_sayi_olmayanlar(self):
        #  True bir int'tir;  NaN ve sonsuz float'tır — hiçbiri hesaba giremez.
        #  Eskiden 13 kopyanın 10'u NaN'ı / sonsuzu sayı sayıyordu.
        for v in (True, False, math.nan, math.inf, -math.inf, None, "3", [1]):
            self.assertFalse(sayi_mi(v), v)

    def test_bos(self):
        for v in (None, "", "   ", "\t"):
            self.assertTrue(bos_mu(v), repr(v))
        for v in (0, "0", " x ", 0.0):
            self.assertFalse(bos_mu(v), repr(v))


class Kutu(unittest.TestCase):
    def test_eleman_kutusu_ve_merkez(self):
        k = eleman_kutusu({"x": 10.0, "y": 20.0, "g": 30.0, "d": 40.0})
        self.assertEqual(k, (10.0, 20.0, 40.0, 60.0))
        self.assertEqual(kutu_merkezi(k), (25.0, 40.0))

    def test_ortusur_kenarda_degmek_sayilmaz(self):
        a = (0, 0, 10, 10)
        self.assertTrue(ortusur(a, (5, 5, 15, 15)))
        self.assertFalse(ortusur(a, (10, 0, 20, 10)))  # kenarda değiyor
        self.assertTrue(ortusur(a, (10, 0, 20, 10), pay=0.5))  # yakınlık payıyla
        self.assertFalse(ortusur(a, (9, 0, 20, 10), pay=-1.0))  # küçültülmüş
