"""Kat ve kabin kapısının kanat sayısı ve kanat cebi ( kullanıcı isteği 2 Eki:
"kapıların içine girdiği bir yer var, LiftDesigner'da var, bizde yok" ).

Kanat cebi:  otomatik kapının kanatları açılınca kapı boşluğunun yanında üst
üste durur;  kat ve kabin kapısı ünitesi o yanda bir kanat eni ( kapı ÷ kanat
sayısı ) + 30 uzanır.  2 kanatlı teleskopikte LiftDesigner'ın altı projesinde
birebir ( DW 800 → 430, 900 → 480, 1.100 → 580 );  Fermator 40/10 aynı kuralı
3 ve 4 kanat için de verir.  Büyük kapılar ( 1.300 ) 3 kanatlı teleskopik ya da
4 kanatlı merkezi yapılır:  2 kanatlının cebi standart kuyuya sığmaz.  3
kanatlıda kanatlar üç düzlemde kayar, eşik 135 ( Fermator T3 )."""

import copy
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import geometri
from cizim import giris
from cizim import girdi
from cizim import sabitler
from motor.uygulama import mukavemet_tablolari

from testler import test_olcu_kaynagi
from testler import test_yerlesim_saglamligi


def _kapi(tip, sol_pay=500, genislik=900, on_pay=None):
    g = copy.deepcopy(girdi.ORNEK)
    g["kapi"].update({"tip": tip, "sol_pay": sol_pay, "genislik": genislik})
    if on_pay is not None:
        g["kabin"]["on_pay"] = on_pay
    return g


class KapiTipi(unittest.TestCase):
    def test_kanat_sayisi_esik_ve_cep(self):
        S = sabitler.sabitler()
        #  ( tip , kanat , eşik , cepler — kapı 500 – 1.700, DW 1.200 )
        for tip, n, esik, cep in (
            ("Teleskopik Sol", 2, 90, [(-130, 500)]),
            ("Teleskopik Sağ", 2, 90, [(1700, 2330)]),
            ("Teleskopik 3 Kanat Sol", 3, 135, [(70, 500)]),
            ("Teleskopik 3 Kanat Sağ", 3, 135, [(1700, 2130)]),
            ("Otomatik Merkezi", 2, 90, [(-130, 500), (1700, 2330)]),
            ("Otomatik Merkezi 4 Kanat", 4, 90, [(170, 500), (1700, 2030)]),
            ("Manuel Sol", 1, 90, []),
        ):
            g = _kapi(tip, genislik=1200)
            with self.subTest(tip):
                self.assertEqual(girdi.kapi_tipi(tip)["kanat"], n)
                self.assertEqual(girdi.esik_derinligi(S, tip), esik)
                self.assertEqual(girdi.esik_derinligi(S, tip, kabin=True), esik)
                self.assertEqual([tuple(round(v) for v in c) for c in girdi.kanat_cepleri(g, S)], cep)

    def test_yeni_tipler_hesabin_listesinde(self):
        for tip in ("Teleskopik 3 Kanat Sol", "Teleskopik 3 Kanat Sağ", "Otomatik Merkezi 4 Kanat"):
            self.assertIn(tip, mukavemet_tablolari.KAPI_TIPLERI)
            self.assertEqual(mukavemet_tablolari.kapi_kablosu(tip), "24 x 0,75")


class LiftDesigner(unittest.TestCase):
    def test_kat_kapisi_unitesi_projelerle_ayni(self):
        #  Kuyunun sol iç yüzünden:  kapı ve kanat cebi LiftDesigner planlarıyla
        #  birebir ( 1022 sağa, 800 KG ve 4815-6 sola, 1275 sağa açılır ).
        for ad, kapi, cep in (
            ("1022", (375, 1275), (1275, 1755)),
            ("800 KG", (610, 1510), (130, 610)),
            ("4815-6", (865, 1765), (385, 865)),
            ("1275", (345, 1445), (1445, 2025)),
        ):
            g, hata = test_olcu_kaynagi._g(test_olcu_kaynagi._gercek(ad))
            self.assertIsNotNone(g, hata)
            S = sabitler.sabitler(g.get("_cizim_sabitleri"))
            with self.subTest(ad):
                self.assertEqual((g["kapi"]["sol_pay"], g["kapi"]["sol_pay"] + g["kapi"]["genislik"]), kapi)
                self.assertEqual(girdi.kanat_cepleri(g, S), [cep])


class Cizim(unittest.TestCase):
    def test_kanatlar_cep_ve_durdurucular(self):
        for tip, n, duzlem, on_pay in (
            ("Teleskopik Sol", 2, 2, None),
            ("Teleskopik 3 Kanat Sağ", 3, 3, 360),
            ("Otomatik Merkezi 4 Kanat", 4, 2, None),
            ("Manuel Sol", 1, 1, None),
        ):
            g = _kapi(tip, sol_pay=730, genislik=900, on_pay=on_pay)
            self.assertEqual(geometri.dogrula(g), [], tip)
            e = geometri.plan(g)
            with self.subTest(tip):
                for ad in ("kat_kanadi", "kabin_kanadi"):
                    kanat = [x for x in e if x.get("ad") == ad]
                    self.assertEqual(len(kanat), n)
                    self.assertEqual(len({x["y"] for x in kanat}), duzlem)
                cep = [x for x in e if x.get("ad") in ("kanat_cebi", "kabin_kanat_cebi")]
                self.assertEqual(len(cep), 0 if n == 1 else 4 if tip.startswith("Otomatik") else 2)
                self.assertEqual(
                    len([x for x in e if x.get("ad") == "kanat_durdurucu"]), len(cep) * duzlem if cep else 0
                )
                self.assertEqual(len(giris.yerlesim(g)["kanatlar"]), n)

    def test_menteseli_kapinin_acilma_yayi(self):
        """Menteşeli kat kapısı kata açılır:  açık konum ve çeyrek yay ( ISO 128,
        ince );  "Manuel Sağ" sağa açılır ( kullanıcı 8 Eki — kattan bakınca menteşe sağda, +x ), yarıçap kapı
        eni;  alttaki ölçü sıraları yayın altında.  Öbür tiplerde yay yok."""
        for tip in ("Manuel Sol", "Manuel Sağ", "Teleskopik Sol"):
            g = _kapi(tip, sol_pay=730, genislik=900)
            e = geometri.plan(g)
            yay = [x for x in e if x.get("ad") == "kapi_acilisi"]
            with self.subTest(tip):
                if not tip.startswith("Manuel"):
                    self.assertEqual(yay, [])
                    continue
                self.assertEqual(len(yay), 1)
                acik, cember = yay[0]["bicim"]
                hx = 730 + 900 if tip.endswith("Sağ") else 730
                kanat = next(x for x in e if x.get("ad") == "kat_kanadi")
                self.assertEqual(acik["noktalar"][0], (hx, kanat["y"]))
                self.assertEqual(acik["noktalar"][1], (hx, kanat["y"] - 900))
                for x, y in cember["noktalar"]:
                    self.assertAlmostEqual(((x - hx) ** 2 + (y - kanat["y"]) ** 2) ** 0.5, 900.0)
                alt = min(o["kot"] for o in e if o["tip"] == "olcu" and o["yon"] == "yatay")
                self.assertLess(alt, kanat["y"] - 900)
                #  kuyu dibi ve kuyu üstü planlarında ( kapı düzeyinin altı / üstü ) yay yok
                self.assertFalse(
                    [x for x in geometri.plan(g, kapi_duzeyi=False) if x.get("ad") == "kapi_acilisi"]
                )

    def test_uc_kanatta_esikler_derin_kabin_geride(self):
        g = _kapi("Teleskopik 3 Kanat Sol", sol_pay=730, on_pay=360)
        KB = girdi.kapi_bolgesi(g, sabitler.sabitler(g["_cizim_sabitleri"]))
        self.assertEqual(KB["esik"][1] - KB["esik"][0], 135)
        self.assertEqual(KB["kabin_esik"][1] - KB["kabin_esik"][0], 135)
        #  Eşikler sığmazsa kabin önde kalır:  eşik aralığı denetimi söyler
        self.assertTrue(
            any("eşiğine biniyor" in h for h in geometri.dogrula(_kapi("Teleskopik 3 Kanat Sol", 730)))
        )


class Denetim(unittest.TestCase):
    def test_cep_kuyuya_sigmazsa_sigan_tipi_soyler(self):
        #  Standart 2.000 kg ( kapı 1.300, kuyu 2.450, ağırlık solda ):  2
        #  kanatlının cebi ( 680 ) iki yanda da sığmaz ( 575 ) — sığan tipler
        #  söylenir.  4 kanatlı merkezinin sol cebi ağırlığın ön konsoluna ve ara
        #  kirişe çarpar ( kabinle yürür );  sağa açılan 3 kanatlı çizilir.
        d = test_yerlesim_saglamligi._cizim(
            test_yerlesim_saglamligi._veri(2000, True, "Sol", kat_kapisi_tipi="Teleskopik Sol")
        )
        self.assertFalse(d.get("aktif"))
        h = next(x for x in d["hata"] if "kanat cebi" in x)
        self.assertIn("680 mm gerekir", h)
        self.assertIn("Teleskopik 3 Kanat Sağ", h)
        self.assertNotIn("Teleskopik Sağ ·", h)
        d = test_yerlesim_saglamligi._cizim(
            test_yerlesim_saglamligi._veri(2000, True, "Sol", kat_kapisi_tipi="Otomatik Merkezi 4 Kanat")
        )
        self.assertTrue(any("ara kirişine çarpıyor" in x for x in d["hata"]), d["hata"])
        self.assertTrue(
            test_yerlesim_saglamligi._cizim(
                test_yerlesim_saglamligi._veri(2000, True, "Sol", kat_kapisi_tipi="Teleskopik 3 Kanat Sağ")
            ).get("aktif")
        )

    def test_cep_konsola_ve_ara_kirise_carpmaz(self):
        #  Karşı ağırlık 450 öne alınınca ( referans projenin kapısı sola açılır )
        #  kabin kapısının cebi kabin rayının ara kirişine çarpar.
        g = copy.deepcopy(girdi.ORNEK)
        self.assertEqual(geometri.dogrula(g), [])
        g["agirlik"]["eksen_kaciklik"] = -450
        h = geometri.dogrula(g)
        self.assertTrue(
            any(x.startswith("Kabin kapısının kanat cebi kabin rayının ara kirişine") for x in h), h
        )
        #  Sağa açılan kapının cebi ara kirişe çarpmaz ( sağda yalnız 470 kalır:
        #  sığmadığı söylenir — çarpışma değil )
        g["kapi"]["tip"] = "Teleskopik Sağ"
        self.assertFalse([x for x in geometri.dogrula(g) if "çarpıyor" in x])


if __name__ == "__main__":
    unittest.main()
