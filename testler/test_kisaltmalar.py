"""ÖLÇÜ DİLİ — LiftDesigner gibi kısa kod + tablo ( cizim/kisaltmalar.py — 13 Eki ).

Veri tablosunun ( veri_tablosu ) KISALTMALAR'ı asansörün tek tablosudur:  paftadaki bütün
çizimlerde geçen her kod tabloda, tablodaki her kod bir çizimde.  Kodlu ölçü
kimliğini taşır ( ölçüye tıklama onunla tanır ), kod tanımsızsa yazılmaz."""

import unittest

from cizim import cizimler
from cizim import kisaltmalar
from cizim import pafta
from cizim import veri_tablosu
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
        #  13 Eki ( 4. adım ):  kuyu planından çizimlerin yanındaki kendi çerçevesine
        g, hata = test_yerlesim_saglamligi.gecerli_duzen(800, "Sağ", True)
        self.assertIsNotNone(g, hata)
        self.assertNotIn("veriler", {x.get("ad") for x in cizimler.CIZIMLER["kuyu_plani"][1](g)})
        e = cizimler.CIZIMLER["veriler"][1](g)
        metin = [x["metin"] for x in e if x.get("ad") == "veriler" and x["tip"] == "yazi"]
        self.assertEqual(metin[0], "ASANSÖR VERİLERİ")
        satir = dict(veri_tablosu.satirlar(g))
        self.assertTrue(satir["Kabin"].startswith("CW × CD"), satir)
        self.assertTrue(satir["Kapı"].startswith("DW × DH"), satir)
        self.assertIn("2:1", satir["Askı"])
        self.assertIn("kotlar m", " ".join(x.get("metin", "") for x in e if x.get("ad") == "notlar"))
        #  Paftanın sonunda, başlığında ölçek yok
        self.assertEqual(pafta.sira(g)[-1], "veriler")
        ad, baslik, _o, c = pafta.cizim_listesi(g)[-1]
        self.assertEqual(ad, "veriler")
        self.assertIn(baslik, [x.get("metin") for x in c])

    def test_veri_satirlari_girdiden(self):
        #  Değerler girdiden ve hesabın özetinden ( kopru:  g["veri"] );  boş olan
        #  satır yazılmaz — sayı uydurulmaz
        g, hata = test_yerlesim_saglamligi.gecerli_duzen(800, "Sağ", True)
        g = dict(g, veri={"yuk": 800.0, "kisi": 10, "kabin_rayi": "89 x 62 x 15,88", "tampon": None})
        satir = dict(veri_tablosu.satirlar(g))
        self.assertEqual(satir["Beyan yükü"], "800 kg  ·  10 kişi")
        self.assertTrue(satir["Kabin rayı"].startswith("89 × 62 × 15,88"), satir)
        self.assertNotIn("Asansör", satir)
        self.assertNotIn("Güvenlik tertibatı", satir)
        g = dict(g, veri={})
        self.assertNotIn("Beyan yükü", dict(veri_tablosu.satirlar(g)))


if __name__ == "__main__":
    unittest.main()
