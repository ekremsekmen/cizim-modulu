"""LiftDesigner paftalarındaki iki görünüş ( kullanıcı isteği 1 Eki ):  GİRİŞ
( kat kapısı durak tarafından — cizim/giris.py ) ve KASNAK DÜZENLEMESİ ( tahrik
kasnağı, saptırma kasnağı, halatlar, sarım açısı — cizim/kasnak_duzeni.py ).

Ölçüler LiftDesigner'ın "Giriş" görünüşünün kuralıyla ( kaba boşluk kapıdan
2 × 140 geniş, 240 yüksek … — sabitler KAPI VE KATLAR );  ofisin gerçek
projelerinde LiftDesigner'ın kendi paftasıyla karşılaştırılır
( gercek_projeler.py )."""

import copy
import math
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import cizimler
from cizim import giris
from cizim import girdi
from cizim import kasnak_duzeni
from cizim import kopru
from cizim import makine_dairesi
from cizim import pafta
from cizim import sabitler

from testler import test_olcu_kaynagi


def _olculer(e):
    """Ölçülerin yazıları ( metinsiz ölçünün yazısı sayısıdır )."""
    return [o.get("metin") or f"{o['uzunluk']:g}" for o in e if o["tip"] == "olcu"]


def _gercek(ad):
    g, hata = test_olcu_kaynagi._g(test_olcu_kaynagi._gercek(ad))
    assert g is not None, hata
    return g


class Giris(unittest.TestCase):
    def test_liftdesigner_ile_ayni(self):
        #  800 KG ve 1022'nin LiftDesigner "Giriş"i:  kuyunun iç yüzlerinden kaba
        #  boşluğa 470 · 1.180 · 350 ve 235 · 1.180 · 585;  "Kapı giriş açıklığı
        #  2240";  kasa 2.220 ( kapının 220 üstü );  buton yuvası 160 × 290, altı
        #  1.055, butonun ortası 1.200 ve kapının kenarından 240;  gösterge 100.
        for ad, zincir in (("800 KG", ["470", "1180", "350"]), ("1022", ["235", "1180", "585"])):
            o = _olculer(giris.ciz(_gercek(ad)))
            with self.subTest(ad):
                i = o.index(zincir[0])
                self.assertEqual(o[i : i + 3], zincir)
                for beklenen in (
                    "DW900",
                    "DH2000",
                    "KAPI BOŞLUĞU 2240",
                    "BUTON 1200",
                    "220",
                    "1055",
                    "290",
                    "240",
                    "160",
                    "100",
                    "50",
                ):
                    self.assertIn(beklenen, o)

    def test_kaba_bosluk_kapi_genisligiyle(self):
        #  1275:  kapı 1.100 → boşluk 1.380 ( LiftDesigner )
        self.assertIn("1380", _olculer(giris.ciz(_gercek("1275"))))

    def test_referans_projenin_kendi_boslugu(self):
        #  Referans proje:  2.100'lük kapıda boşluk 2.300 ( kendi 200'ü )
        self.assertIn("KAPI BOŞLUĞU 2300", _olculer(giris.ciz(girdi.ORNEK)))

    def test_buton_acilisin_karsisinda(self):
        g = copy.deepcopy(girdi.ORNEK)
        for tip, sol in (
            ("Teleskopik Sol", False),
            ("Otomatik Merkezi", False),
            ("Teleskopik Sağ", True),
            ("Manuel Sağ", True),
        ):
            g["kapi"]["tip"] = tip
            Y = giris.yerlesim(g)
            with self.subTest(tip):
                self.assertEqual(Y["buton_sol"], sol)
                self.assertEqual(Y["bx"] < Y["x0"], sol)
                self.assertEqual(abs(Y["bx"] - (Y["x0"] if sol else Y["x1"])), 240)
                #  Yuva kaba boşluğun kenarından 20 içeride değil, dışında
                self.assertTrue(Y["yuva"][2] <= Y["bosluk"][0] or Y["yuva"][0] >= Y["bosluk"][2])

    def test_kanat_sayisi(self):
        g = copy.deepcopy(girdi.ORNEK)
        for tip, n in (("Teleskopik Sol", 2), ("Otomatik Merkezi", 2), ("Manuel Sol", 1)):
            g["kapi"]["tip"] = tip
            with self.subTest(tip):
                self.assertEqual(len(giris.yerlesim(g)["kanatlar"]), n)


class KasnakDuzeni(unittest.TestCase):
    def test_saptirmali_makine_dairesi(self):
        #  800 KG ( Ø500 tahrik, Ø400 saptırma ):  açı hesabınkiyle aynı ve
        #  LiftDesigner'a yakın ( 151° );  halat arası döşemedeki deliklerin arası
        g = _gercek("800 KG")
        e = kasnak_duzeni.ciz(g)
        o = _olculer(e)
        alfa = kopru.sarim_acisi(g)
        self.assertAlmostEqual(alfa, 151, delta=1.5)
        self.assertIn(f"SARIM AÇISI {alfa:.0f}°", [x["metin"] for x in e if x["tip"] == "yazi"])
        self.assertIn("Ø 500", o)
        self.assertIn("Ø 400", o)
        d = {
            t: (k[1] + k[3]) / 2.0
            for t, k in makine_dairesi.yerlesim(g)["delikler"]
            if t in ("KABİN", "AĞIRLIK")
        }
        self.assertIn(f"HALAT ARASI {abs(d['AĞIRLIK'] - d['KABİN']):.0f}", o)
        #  Yay kasnağın üstünden, açı kadar ( 24 parça )
        self.assertEqual(sum(1 for x in e if x.get("ad") == "sarim_yayi"), 24)

    def test_duzey_inis_180(self):
        #  Makine dairesizde ve saptırmasız 2:1'de iki iniş düşey:  180°,
        #  halat arası kasnağın çapı ( LiftDesigner "Sarım açısı 0" yazıyordu ) —
        #  aynı aralık Ø ile ölçülmüş, HALAT ARASI yazılmaz ( 13 Eki:  her ölçü bir kez )
        for ad in ("4815-6", "1275"):
            g = _gercek(ad)
            e = kasnak_duzeni.ciz(g)
            with self.subTest(ad):
                self.assertIn("SARIM AÇISI 180°", [x["metin"] for x in e if x["tip"] == "yazi"])
                olculer = _olculer(e)
                self.assertIn(f"Ø {g['makine']['tahrik_kasnak_capi']:g}", olculer)
                self.assertFalse([m for m in olculer if m.startswith("HALAT ARASI")], olculer)

    def test_her_duzende_cizilir(self):
        for ad, v in test_olcu_kaynagi.DUZENLER.items():
            g, hata = test_olcu_kaynagi._g(v())
            if g is None:
                continue
            with self.subTest(ad):
                e = kasnak_duzeni.ciz(g)
                self.assertTrue(any(x.get("ad") == "tahrik_kasnagi" for x in e))
                self.assertEqual(sum(1 for x in e if x.get("ad") == "aski_halati") >= 2, True)


class KapiKesiti(unittest.TestCase):
    """Kapı yan kesiti ( LiftDesigner "Front Entrance Side View" · Wittur montaj
    kesiti ):  standardın sayıları parçaların ÇİZİLEN biçiminden ölçülür."""

    TIPLER = (
        "Teleskopik Sol",
        "Teleskopik 3 Kanat Sağ",
        "Otomatik Merkezi",
        "Otomatik Merkezi 4 Kanat",
        "Manuel Sol",
    )

    @classmethod
    def setUpClass(cls):
        from testler import test_yerlesim_saglamligi
        from cizim import geometri

        cls.durumlar = []
        for tip in cls.TIPLER:
            for montaj in ("Kuyu içine", "Duvar boşluğuna"):
                g, hata = test_yerlesim_saglamligi.gecerli_duzen(
                    1000, "Sağ", kat_kapisi_tipi=tip, kapi_montaji=montaj
                )
                assert not hata, (tip, montaj, hata)
                cls.durumlar.append(
                    (tip, montaj, g, cizimler.CIZIMLER["kapi_kesiti"][1](g), geometri.plan(g))
                )

    @staticmethod
    def _ad(e, ad):
        return [x for x in e if x.get("ad") == ad]

    def _pah(self, nok):
        """Açık çizginin son parçası:  ( yatayla açı °, yatay izdüşüm ), dik parçanın boyu."""
        (u0, z0), (u1, z1), (u2, z2) = nok
        return (math.degrees(math.atan2(abs(z2 - z1), abs(u2 - u1))), abs(u2 - u1)), abs(z0 - z1)

    def test_esik_alti_saci_m_5_2_5_3_2(self):
        """Dik kısmı eşiğin altından en az kilit bölgesinin yarısı + 50 ( otomatikte
        0,40 — kilit bölgesi ±0,35 —, elle açılanda 0,25 );  pah ≥ 60°, ≥ 20 mm."""
        for tip, montaj, g, e, _p in self.durumlar:
            with self.subTest(tip=tip, montaj=montaj):
                s = self._ad(e, "esik_alti_saci")[0]["bicim"][0]["noktalar"]
                (aci, izd), dik = self._pah(s)
                self.assertGreaterEqual(dik, 250.0 if tip.startswith("Manuel") else 400.0)
                self.assertGreaterEqual(round(aci, 6), 60.0)
                self.assertGreaterEqual(izd, 20.0)
                #  eşiğin kuyu kenarından iner ( eşiğe bağlı ), pahla duvara döner
                KB = girdi.kapi_bolgesi(g, sabitler.sabitler(None))
                self.assertEqual(s[0][0], KB["hat"])
                self.assertEqual(s[2][0], 0.0)

    def test_onluk_m_5_4_5(self):
        """Dik kısmı döşemeden en az 0,75 m;  pah kabine doğru ≥ 60°, ≥ 20 mm;
        kabin eşiğinin kat tarafındaki kenarında."""
        for tip, montaj, _g, e, _p in self.durumlar:
            with self.subTest(tip=tip, montaj=montaj):
                o = self._ad(e, "onluk")[0]["bicim"][0]["noktalar"]
                (aci, izd), _dik = self._pah(o)
                self.assertLessEqual(o[1][1], -750.0 + 1e-6)
                self.assertGreaterEqual(round(aci, 6), 60.0)
                self.assertGreaterEqual(izd, 20.0)
                self.assertGreater(o[2][0], o[1][0])  # kabine doğru
                es = self._ad(e, "kabin_esigi")[0]
                self.assertEqual(o[0][0], es["x"])

    def test_esik_arasi_ve_oluklar(self):
        for tip, montaj, _g, e, _p in self.durumlar:
            with self.subTest(tip=tip, montaj=montaj):
                ke, kk = self._ad(e, "kat_esigi")[0], self._ad(e, "kabin_esigi")[0]
                arasi = kk["x"] - (ke["x"] + ke["g"])
                self.assertTrue(0 < arasi <= girdi.ESIK_ARASI_AZAMI, arasi)
                #  her kanat düzleminin bir oluğu ( eşiğin üstünde dört noktalık çentik );  menteşelide yok
                cent = (len(ke["bicim"][0]["noktalar"]) - 4) // 4
                n = 0 if tip.startswith("Manuel") else girdi.kapi_tipi(tip)["duzlem"]
                self.assertEqual(cent, n)

    def test_kanatlar_planla_ayni_yerde(self):
        for tip, montaj, _g, e, plan in self.durumlar:
            for ad in ("kat_kanadi", "kabin_kanadi"):
                with self.subTest(tip=tip, montaj=montaj, ad=ad):
                    self.assertEqual(
                        sorted({round(x["x"], 6) for x in self._ad(e, ad)}),
                        sorted({round(x["y"], 6) for x in self._ad(plan, ad)}),
                    )

    def test_ust_kutu_kasanin_ustune_kadar(self):
        S = sabitler.sabitler(None)
        for tip, montaj, g, e, _p in self.durumlar:
            with self.subTest(tip=tip, montaj=montaj):
                u = self._ad(e, "kapi_ust_kutusu")[0]
                HH = g["kapi"]["yukseklik"]
                self.assertEqual((u["y"], u["y"] + u["d"]), (HH, HH + S["kasa_ust"]))


class Pafta(unittest.TestCase):
    def test_iki_gorunus_paftada_ve_ekranda(self):
        for sira in (pafta.SIRA_MRL, pafta.SIRA_MD):
            self.assertEqual(sira[-4:], ("kasnak_duzeni", "giris", "kapi_kesiti", "veriler"))
        for ad in ("kasnak_duzeni", "giris", "kapi_kesiti"):
            self.assertIn(ad, cizimler.CIZIMLER)


if __name__ == "__main__":
    unittest.main()
