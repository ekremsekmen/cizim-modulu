"""ÖLÇÜ DİLİ — LiftDesigner gibi kısa kod + tablo ( cizim/kisaltmalar.py — 13 Eki ).

Kuyu planının KISALTMALAR tablosu paftanın tek tablosudur:  paftadaki bütün
çizimlerde geçen her kod tabloda, tablodaki her kod bir çizimde.  Kodlu ölçü
kimliğini taşır ( ölçüye tıklama onunla tanır ), kod tanımsızsa yazılmaz."""

import unittest

from cizim import geometri
from cizim import kisaltmalar
from cizim import pafta
from testler import test_yerlesim_saglamligi


class Kodlar(unittest.TestCase):
    def test_kod_ve_cozumu(self):
        self.assertEqual(kisaltmalar.kodlu("SW", 2100), "SW2100")
        self.assertEqual(kisaltmalar.kodlu("DBGW", 850.5), "DBGW850.5")
        self.assertEqual(kisaltmalar.kodu("DBGW850"), "DBGW")
        self.assertEqual(kisaltmalar.kodu("SW2100"), "SW")
        self.assertIsNone(kisaltmalar.kodu("2100"))
        self.assertIsNone(kisaltmalar.kodu("KUYU DİBİ 1600"))
        with self.assertRaises(KeyError):
            kisaltmalar.kodlu("XX", 1)

    def test_paftanin_kodlari_tablonun_kodlari(self):
        for mrl in (True, False):
            for yer in ("Sağ", "Arka"):
                with self.subTest(mrl=mrl, yer=yer):
                    g, hata = test_yerlesim_saglamligi.gecerli_duzen(800, yer, mrl)
                    self.assertIsNotNone(g, hata)
                    kullanilan, tablo = set(), []
                    for ad, _b, _o, e in pafta.cizim_listesi(g):
                        kullanilan |= set(kisaltmalar.kullanilanlar(e))
                        for el in e:
                            if (
                                el.get("ad") == "kisaltmalar"
                                and el["tip"] == "yazi"
                                and el["metin"] in kisaltmalar.KODLAR
                            ):
                                tablo.append(el["metin"])
                        #  Kodlu her ölçünün kimliği var
                        for el in e:
                            if el["tip"] == "olcu" and kisaltmalar.kodu(el["metin"]):
                                self.assertTrue(el.get("ad", "").startswith("olcu_"), (ad, el["metin"]))
                    self.assertEqual(set(tablo), kullanilan)
                    self.assertEqual(len(tablo), len(set(tablo)))
                    self.assertEqual(tablo, [k for k in kisaltmalar.KODLAR if k in kullanilan])

    def test_veriler_tablosu(self):
        g, hata = test_yerlesim_saglamligi.gecerli_duzen(800, "Sağ", True)
        metin = [
            x["metin"] for x in geometri.kuyu_plani(g) if x.get("ad") == "veriler" and x["tip"] == "yazi"
        ]
        self.assertEqual(metin[0], "VERİLER")
        self.assertIn("Kabin", metin)
        self.assertTrue(any(m.startswith("CW × CD") for m in metin), metin)
        self.assertTrue(any(m.startswith("DW × DH") for m in metin), metin)


if __name__ == "__main__":
    unittest.main()
