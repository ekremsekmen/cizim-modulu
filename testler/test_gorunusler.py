"""LiftDesigner paftalarındaki iki görünüş ( kullanıcı isteği 1 Eki ):  GİRİŞ
( kat kapısı durak tarafından — cizim/giris.py ) ve KASNAK DÜZENLEMESİ ( tahrik
kasnağı, saptırma kasnağı, halatlar, sarım açısı — cizim/kasnak_duzeni.py ).

Ölçüler LiftDesigner'ın "Giriş" görünüşünün kuralıyla ( kaba boşluk kapıdan
2 × 140 geniş, 240 yüksek … — sabitler KAPI VE KATLAR );  ofisin gerçek
projelerinde LiftDesigner'ın kendi paftasıyla karşılaştırılır
( gercek_projeler.py )."""
import copy
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _yol in (os.path.join(KOK, "hesap"), os.path.join(KOK, "ornekler"),
             os.path.join(KOK, "testler")):
    if _yol not in sys.path:
        sys.path.append(_yol)

from cizim import cizimler as CZ                          # noqa: E402
from cizim import giris as CGI                            # noqa: E402
from cizim import girdi as CG                             # noqa: E402
from cizim import kasnak_duzeni as CKS                    # noqa: E402
from cizim import kopru as CK                             # noqa: E402
from cizim import makine_dairesi as CMD                   # noqa: E402
from cizim import pafta as CPF                            # noqa: E402

import test_olcu_kaynagi as T                             # noqa: E402


def _olculer(e):
    """Ölçülerin yazıları ( metinsiz ölçünün yazısı sayısıdır )."""
    return [o.get("metin") or f"{o['uzunluk']:g}" for o in e if o["tip"] == "olcu"]


def _gercek(ad):
    g, hata = T._g(T._gercek(ad))
    assert g is not None, hata
    return g


class Giris(unittest.TestCase):
    def test_liftdesigner_ile_ayni(self):
        #  800 KG ve 1022'nin LiftDesigner "Giriş"i:  kuyunun iç yüzlerinden kaba
        #  boşluğa 470 · 1.180 · 350 ve 235 · 1.180 · 585;  "Kapı giriş açıklığı
        #  2240";  kasa 2.220 ( kapının 220 üstü );  buton yuvası 160 × 290, altı
        #  1.055, butonun ortası 1.200 ve kapının kenarından 240;  gösterge 100.
        for ad, zincir in (("800 KG", ["470", "1180", "350"]), ("1022", ["235", "1180", "585"])):
            o = _olculer(CGI.ciz(_gercek(ad)))
            with self.subTest(ad):
                i = o.index(zincir[0])
                self.assertEqual(o[i:i + 3], zincir)
                for beklenen in ("KAPI 900", "KAPI 2000", "KAPI BOŞLUĞU 2240", "BUTON 1200",
                                 "220", "1055", "290", "240", "160", "100", "50"):
                    self.assertIn(beklenen, o)

    def test_kaba_bosluk_kapi_genisligiyle(self):
        #  1275:  kapı 1.100 → boşluk 1.380 ( LiftDesigner )
        self.assertIn("1380", _olculer(CGI.ciz(_gercek("1275"))))

    def test_referans_projenin_kendi_boslugu(self):
        #  Referans proje:  2.100'lük kapıda boşluk 2.300 ( kendi 200'ü )
        self.assertIn("KAPI BOŞLUĞU 2300", _olculer(CGI.ciz(CG.ORNEK)))

    def test_buton_acilisin_karsisinda(self):
        g = copy.deepcopy(CG.ORNEK)
        for tip, sol in (("Teleskopik Sol", False), ("Otomatik Merkezi", False),
                         ("Teleskopik Sağ", True), ("Manuel Sağ", True)):
            g["kapi"]["tip"] = tip
            Y = CGI.yerlesim(g)
            with self.subTest(tip):
                self.assertEqual(Y["buton_sol"], sol)
                self.assertEqual(Y["bx"] < Y["x0"], sol)
                self.assertEqual(abs(Y["bx"] - (Y["x0"] if sol else Y["x1"])), 240)
                #  Yuva kaba boşluğun kenarından 20 içeride değil, dışında
                self.assertTrue(Y["yuva"][2] <= Y["bosluk"][0] or Y["yuva"][0] >= Y["bosluk"][2])

    def test_kanat_sayisi(self):
        g = copy.deepcopy(CG.ORNEK)
        for tip, n in (("Teleskopik Sol", 2), ("Otomatik Merkezi", 2), ("Manuel Sol", 1)):
            g["kapi"]["tip"] = tip
            with self.subTest(tip):
                self.assertEqual(len(CGI.yerlesim(g)["kanatlar"]), n)


class KasnakDuzeni(unittest.TestCase):
    def test_saptirmali_makine_dairesi(self):
        #  800 KG ( Ø500 tahrik, Ø400 saptırma ):  açı hesabınkiyle aynı ve
        #  LiftDesigner'a yakın ( 151° );  halat arası döşemedeki deliklerin arası
        g = _gercek("800 KG")
        e = CKS.ciz(g)
        o = _olculer(e)
        alfa = CK.sarim_acisi(g)
        self.assertAlmostEqual(alfa, 151, delta=1.5)
        self.assertIn(f"SARIM AÇISI {alfa:.0f}°", [x["metin"] for x in e if x["tip"] == "yazi"])
        self.assertIn("Ø 500", o)
        self.assertIn("Ø 400", o)
        d = {t: (k[1] + k[3]) / 2.0 for t, k in CMD.yerlesim(g)["delikler"] if t in ("KABİN", "AĞIRLIK")}
        self.assertIn(f"HALAT ARASI {abs(d['AĞIRLIK'] - d['KABİN']):.0f}", o)
        #  Yay kasnağın üstünden, açı kadar ( 24 parça )
        self.assertEqual(sum(1 for x in e if x.get("ad") == "sarim_yayi"), 24)

    def test_duzey_inis_180(self):
        #  Makine dairesizde ve saptırmasız 2:1'de iki iniş düşey:  180°,
        #  halat arası kasnağın çapı ( LiftDesigner "Sarım açısı 0" yazıyordu )
        for ad in ("4815-6", "1275"):
            g = _gercek(ad)
            e = CKS.ciz(g)
            with self.subTest(ad):
                self.assertIn("SARIM AÇISI 180°", [x["metin"] for x in e if x["tip"] == "yazi"])
                self.assertIn(f"HALAT ARASI {g['makine']['tahrik_kasnak_capi']:g}", _olculer(e))

    def test_her_duzende_cizilir(self):
        for ad, v in T.DUZENLER.items():
            g, hata = T._g(v())
            if g is None:
                continue
            with self.subTest(ad):
                e = CKS.ciz(g)
                self.assertTrue(any(x.get("ad") == "tahrik_kasnagi" for x in e))
                self.assertEqual(sum(1 for x in e if x.get("ad") == "aski_halati") >= 2, True)


class Pafta(unittest.TestCase):
    def test_iki_gorunus_paftada_ve_ekranda(self):
        for sira in (CPF.SIRA_MRL, CPF.SIRA_MD):
            self.assertEqual(sira[-2:], ("kasnak_duzeni", "giris"))
        for ad in ("kasnak_duzeni", "giris"):
            self.assertIn(ad, CZ.CIZIMLER)


if __name__ == "__main__":
    unittest.main()
