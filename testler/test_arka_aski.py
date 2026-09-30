"""ARKADA KARŞI AĞIRLIKLA 2:1 ( cizim/arka_aski.py ) — kabin üstünde çapraz kasnaklar.

Kullanıcı kararı:  "çapraz, iki taraf dengeli" ( ofisin 12495-18'i );  makine
dairesizde makine duvardan duvara iki kirişte.  Karşı ağırlık kasnağı ağırlığın
ortasında, kabin askısı kabin merkezinde;  tahrik kasnağının iki inişi ağırlık
kasnağının teğetinde ve D1 önünde."""
import math
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_yol = os.path.join(KOK, "hesap")
if _yol not in sys.path:
    sys.path.append(_yol)

from cizim import arka_aski as CAA                        # noqa: E402
from cizim import geometri as CGE                         # noqa: E402
from cizim import kabin_ustu as CKUS                      # noqa: E402
from cizim import kopru as CK                             # noqa: E402
from cizim import kuyu_ustu as CKT                        # noqa: E402
from cizim import makine_dairesi as CMD                   # noqa: E402
from cizim import sabitler as CS                          # noqa: E402
from engine.uygulama import girdi as UG                   # noqa: E402
from engine.uygulama import hesap as UY                   # noqa: E402

#  12495-18'e yakın bir asansör ( kuyu 1.750 × 1.950, kabin 1.100 × 1.100 )
ARKA = {"agirlik_yeri": "Arka", "aski_orani": 2, "aski_duzeni": "Kabin üstü",
        "kuyu_genisligi": 1750, "kuyu_derinligi": 1950, "kabin_genisligi": 1100,
        "kabin_derinligi": 1100, "kapi_genisligi": 800, "beyan_yuku": 800,
        "makine_raya_biniyor": "Bina yapısına", "son_kat_yuksekligi": 4700}
MD = {"mk_yok": False, "mk_uzunluk": 3800, "mk_genislik": 2600}


def _girdi(**ek):
    return UG.tamamla({**UG.varsayilanlar(), **ARKA, **ek})


def _cizim(**ek):
    A = _girdi(**ek)
    g, h = CK.cizim_girdisi(A)
    assert g is not None, h
    return A, g, CS.sabitler(g.get("_cizim_sabitleri"))


class Geometri(unittest.TestCase):
    def test_teget_ayna_denge(self):
        _A, g, S = _cizim()
        G = CAA.geometri(g, S)
        self.assertEqual(G["hata"], [])
        ag, mk, a = g["agirlik"], g["makine"], g["aski"]
        Rc, Rk, D1 = ag["kasnak_capi"] / 2.0, a["kasnak_capi"] / 2.0, mk["tahrik_kasnak_capi"]
        #  Karşı ağırlık kasnağı ağırlığın ortasında;  tahrik inişi onun teğetinde
        self.assertAlmostEqual(G["ex"], g["kuyu"]["genislik"] / 2.0)
        self.assertAlmostEqual(abs(G["W"][0] - G["ex"]), Rc)
        self.assertAlmostEqual(abs(G["Hw"][0] - G["ex"]), Rc)
        self.assertAlmostEqual(G["W"][1], G["ey"])
        #  İki iniş D1 aralıklı, aynı düzlemde ( derinlik boyunca )
        self.assertAlmostEqual(G["P"][0], G["W"][0])
        self.assertAlmostEqual(G["W"][1] - G["P"][1], D1)
        #  Askı kabin merkezinde:  iki düşey halatın ortası
        self.assertAlmostEqual((G["P"][0] + G["H"][0]) / 2.0, G["cx"])
        self.assertAlmostEqual((G["P"][1] + G["H"][1]) / 2.0, G["cy"])
        self.assertAlmostEqual(G["cx"], g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"])
        #  Kasnakların dış teğetleri P'de ve H'de
        arka, on = G["kasnaklar"]
        self.assertAlmostEqual(math.dist(arka, G["P"]), Rk)
        self.assertAlmostEqual(math.dist(on, G["H"]), Rk)
        self.assertAlmostEqual(G["aralik"], math.dist(arka, on))
        self.assertAlmostEqual(g["aski"]["kasnak_arasi"], round(G["aralik"], 1))

    def test_agirlik_kabine_gore(self):
        #  Ağırlık – duvar boşsa:  tahrik inişi kabin tavanının arka kenarından
        #  korkuluk payı kadar içeride, ağırlık kabine en az 50 mm
        _A, g, S = _cizim()
        G = CAA.geometri(g, S)
        kb, ag = g["kabin"], g["agirlik"]
        kabin_arka = kb["on_pay"] + kb["derinlik"] + S["kabin_pano_arka"]
        self.assertAlmostEqual(kabin_arka - G["P"][1], CKUS.KORKULUK_PARCA_ASGARI)
        self.assertGreaterEqual(G["ey"] - ag["derinlik"] / 2.0 - kabin_arka, 50.0)
        #  Arka kasnak korkuluğun yolunu kesmez
        self.assertEqual(CKUS.dogrula(g), [])


class Cizimler(unittest.TestCase):
    def test_plan(self):
        _A, g, S = _cizim()
        e = CGE.plan(g, S)
        capraz = [x for x in e if x.get("ad") == "kabin_kasnak_capraz"]
        self.assertEqual(len(capraz), 8)                   # iki kasnak × dört kenar
        self.assertFalse([x for x in e if x.get("ad") == "kabin_kasnak"])
        self.assertTrue(any("ÇAPRAZ" in x.get("metin", "") for x in e if x.get("ad") == "aski_yazi"))
        self.assertEqual(CGE.halat_konumlari(g, S), [CAA.geometri(g, S)["P"], CAA.geometri(g, S)["H"]])

    def test_makine_dairesizde_duvardan_duvara_simetrik_kiris(self):
        _A, g, S = _cizim()
        KU = CKT.yerlesim(g, S, acil_pano=False)
        self.assertEqual(KU["hata"], [])
        self.assertTrue(KU["duvardan_duvara"])
        sase = KU["sase"]
        #  Ön duvarın iç yüzünden arka duvarınkine
        self.assertEqual((sase[1], sase[3]), (0.0, g["kuyu"]["derinlik"]))
        #  Tahrik kasnağı iki kirişin tam ortasında ( her kirişe F / 2 )
        ks = KU["kasnak"]
        self.assertAlmostEqual((sase[0] + sase[2]) / 2.0, (ks[0] + ks[2]) / 2.0)
        self.assertEqual(KU["sapma"], (0.0, 0.0))

    def test_makine_dairesinde_delikler(self):
        _A, g, S = _cizim(**MD)
        Y = CMD.yerlesim(g, S)
        self.assertEqual(Y["hata"], [])
        G = CAA.geometri(g, S)
        d = dict(Y["delikler"])

        def orta(k):
            return ((k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0)
        for ad, nokta in (("KABİN", G["P"]), ("AĞIRLIK", G["W"]),
                          ("AĞIRLIK BAĞLANTISI", G["Hw"]), ("KABİN BAĞLANTISI", G["H"])):
            self.assertAlmostEqual(orta(d[ad])[0], nokta[0], msg=ad)
            self.assertAlmostEqual(orta(d[ad])[1], nokta[1], msg=ad)
        self.assertIsNone(Y["saptirma"])                   # iniş düşey:  saptırma yok
        self.assertEqual(CK.sarim_acisi(g), 180.0)


class Kopru(unittest.TestCase):
    def test_kabin_alti_cizilmez(self):
        _A, g, _S = _cizim(aski_duzeni="Kabin altı")
        self.assertTrue(any("kabin üstünde çizilir" in h for h in CKT.duzen_hatalari(g)))

    def test_makine_dairesizde_yuk_yolu_bina(self):
        A, g, _S = _cizim(makine_raya_biniyor="Kılavuz raylara")
        d = CK.tutarlilik_duzeltmeleri(g, A)
        self.assertEqual(d.get("makine_raya_biniyor"), "Bina yapısına")
        A, g, _S = _cizim()
        self.assertEqual(CK.tutarlilik(g, A), [])

    def test_girilen_kasnak_araligi_karsilastirilir(self):
        A, g, _S = _cizim(kabin_kasnak_arasi=1000)
        self.assertEqual(CK.tutarlilik_duzeltmeleri(g, A),
                         {"kabin_kasnak_arasi": g["aski"]["kasnak_arasi"]})


class Hesap(unittest.TestCase):
    """Program hesabı arkadaki 2:1'in geometrisini çizimden alır."""

    def test_makine_dairesiz(self):
        s = UY.hesapla(ARKA)
        self.assertTrue(s["aktif"], s.get("hata"))
        gi = s["girdi"]
        A, g, S = _cizim()
        G = CAA.geometri(g, S)
        kb = g["kabin"]
        #  Askı kabin merkezinde ( xs = kabin merkezi – ray ekseni ), iniş düşey
        self.assertAlmostEqual(gi["aski_kaciklik_x"], kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0
                               - g["kabin_ray"]["kapi_arasi"])
        self.assertEqual(gi["sarilma_acisi"], 180.0)
        self.assertEqual(gi["kasnak_tek_yon"], 2)
        #  Duvardan duvara kiriş:  açıklık kuyu derinliği, yük tahrik kasnağında
        self.assertEqual(gi["yan_yatak_boyu"], g["kuyu"]["derinlik"])
        self.assertAlmostEqual(s["ara"]["makine.X"], (G["P"][1] + G["W"][1]) / 2.0)
        b2 = next(b for b in s["bolumler"] if b["kimlik"] == "makine_konstruksiyonu")
        self.assertTrue(any("duvardan duvara" in str(a.get("kaynak", "")) for a in b2["adimlar"]))
        self.assertFalse(b2.get("eksik_hesap"))
        #  Son kat 4.700:  makine ve kirişler kabinin üstünde — bölüm 11 uygun
        b11 = next(b for b in s["bolumler"] if b["kimlik"] == "siginma_alanlari")
        self.assertTrue(b11["sonuc"]["uygun"], b11["sonuc"]["metin"])

    def test_makine_daireli(self):
        s = UY.hesapla({**ARKA, **MD})
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertEqual(s["girdi"]["sarilma_acisi"], 180.0)
        self.assertFalse(s["ozet"].get("eksik_hesap"))


if __name__ == "__main__":
    unittest.main()
