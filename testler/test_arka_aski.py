"""ARKADA KARŞI AĞIRLIKLA 2:1 ( cizim/arka_aski.py ) — kabin üstünde çapraz kasnaklar.

Kullanıcı kararı:  "çapraz, iki taraf dengeli" ( ofisin 12495-18'i );  makine
dairesizde makine duvardan duvara iki kirişte.  Karşı ağırlık kasnağı ağırlığın
ortasında, kabin askısı kabin merkezinde;  tahrik kasnağının iki inişi ağırlık
kasnağının teğetinde ve D1 önünde."""

import math
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import arka_aski as CAA
from cizim import geometri as CGE
from cizim import kabin_ustu as CKUS
from cizim import kopru as CK
from cizim import dusey as CDY
from cizim import kuyu_ustu as CKT
from cizim import makine_dairesi as CMD
from cizim import sabitler as CS
from engine.uygulama import girdi as UG
from engine.uygulama import hesap as UY

#  12495-18'in düzeni ( çapraz kasnaklar, makine duvardan duvara ), kabin
#  1.350 × 1.400 ( 800 kg'ın standart kabini ):  12495-18'in 1.100 × 1.100
#  tavanını çapraz halat ( tavanın 80 üstünde ) ikiye böler, iki yarıda da
#  çömelme alanına yer kalmaz — 10 Eki'den beri halat engel
#  ( test_kucuk_tavanda_capraz_halat_siginmayi_boler ).  Kuyu kabinden yine
#  650 geniş, 850 derin.
ARKA = {
    "agirlik_yeri": "Arka",
    "aski_orani": 2,
    "aski_duzeni": "Kabin üstü",
    "kuyu_genisligi": 2000,
    "kuyu_derinligi": 2250,
    "kabin_genisligi": 1350,
    "kabin_derinligi": 1400,
    "kapi_genisligi": 800,
    "beyan_yuku": 800,
    "makine_raya_biniyor": "Bina yapısına",
    "son_kat_yuksekligi": 4500,
}
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

    def test_kucuk_tavanda_capraz_halat_siginmayi_boler(self):
        #  12495-18'in 1.100 × 1.100 kabini:  kasnaklar arasındaki çapraz halat
        #  tavanın 80 mm üstünden geçer ( hareketli.kabin_parcalari ), şasenin
        #  üst kirişi de ray ekseninde;  çömelme alanı ( 500 × 700 × 1.000 )
        #  hiçbir parçaya sığmaz.  10 Eki'ye dek halat sayılmıyor, alan halatın
        #  üstüne konuyordu ( denetim 9 Eki ).
        A = _girdi(kuyu_genisligi=1750, kuyu_derinligi=1950, kabin_genisligi=1100, kabin_derinligi=1100)
        g, _h = CK.cizim_girdisi(A)
        Y = CKUS.yerlesim(g)
        self.assertIsNone(Y["siginma"])
        self.assertTrue(any("aralarındaki halat" in h for h in Y["hata"]), Y["hata"])
        #  Halat şeridi gerçekten tavanın üstünde ve alanın yüksekliğinde
        from cizim import donanim as CDN, hareketli as CH

        S = CS.sabitler(g.get("_cizim_sabitleri"))
        kt = CDN.kabin_kotlari(g["dusey"], S, 0.0, g["aski"], True)
        halat = [p for p in CH.kabin_parcalari(g, S, Y["taban"], kt) if p[0] == CH.HALAT]
        self.assertTrue(halat)
        self.assertAlmostEqual(halat[0][2] - kt["tavan"], S["kabin_tavani_kasnak_boslugu"])
        self.assertTrue(any(CH.ortusur(p[1], Y["tavan"]) for p in halat))


class Cizimler(unittest.TestCase):
    def test_plan(self):
        _A, g, S = _cizim()
        e = CGE.plan(g, S)
        capraz = [x for x in e if x.get("ad") == "kabin_kasnak_capraz"]
        self.assertEqual(len(capraz), 8)  # iki kasnak × dört kenar
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

        for ad, nokta in (
            ("KABİN", G["P"]),
            ("AĞIRLIK", G["W"]),
            ("AĞIRLIK BAĞLANTISI", G["Hw"]),
            ("KABİN BAĞLANTISI", G["H"]),
        ):
            self.assertAlmostEqual(orta(d[ad])[0], nokta[0], msg=ad)
            self.assertAlmostEqual(orta(d[ad])[1], nokta[1], msg=ad)
        self.assertIsNone(Y["saptirma"])  # iniş düşey:  saptırma yok
        self.assertEqual(CK.sarim_acisi(g), 180.0)


class Dusey(unittest.TestCase):
    """Kuyu tepesi ( LiftDesigner 12495-18:  son kat 4.200, kabin 2.000 ):
    kasnaklar kabin tavanında, makine duvardan duvara kirişlerin üstünde
    tavana yakın."""

    def test_kasnaklar_tavanda(self):
        _A, g, S = _cizim()
        Y = CDY.yerlesim(g)
        ust, Rk = Y["ust"], g["aski"]["kasnak_capi"] / 2.0
        self.assertAlmostEqual(ust["kasnak_merkez"] - Rk, ust["tavan"] + S["kabin_tavani_kasnak_boslugu"])
        #  Kasnaklar arasındaki halat ( kasnakların altı ) üst patenin altından
        #  geçer ( LiftDesigner:  kasnaklar 2.080 – 2.320, üst paten 2.200 – 2.340 )
        self.assertLess(ust["kasnak_merkez"] - Rk, ust["ust_paten_alt"])

    def test_makine_tavana_yakin(self):
        _A, g, S = _cizim()
        M = CDY.yerlesim(g)["M"]
        self.assertAlmostEqual(M["kapak"][5], M["tavan"] - S["duvar_kirisi_tepe_boslugu"])
        #  Yandaki ağırlıkta makine raylara oturur:  tavandan eski pay
        g = CK.cizim_girdisi(UG.tamamla(UG.varsayilanlar()))[0]
        self.assertIn(g["agirlik"]["yeri"], ("Sol", "Sağ"))
        M = CDY.yerlesim(g)["M"]
        self.assertFalse(M["KU"].get("duvardan_duvara"))
        self.assertAlmostEqual(M["kapak"][5], M["tavan"] - S["makine_tepe_boslugu"])

    def test_son_kat(self):
        #  1.350 × 1.400, ofisin kabini ( 2.000 ):  4.260'ta yalnız arkadaki 1,10
        #  m'lik korkuluk kirişe yakın ( m.5.2.5.7.2 c ), 4.270'te hepsi uygun.
        for son_kat, kalan in ((4260, ["korkuluk"]), (4270, [])):
            _A, g, _S = _cizim(son_kat_yuksekligi=son_kat)
            Y = CDY.yerlesim(g)
            self.assertEqual([k for k, v in Y["ust_aciklik"].items() if v[0] < v[1] - 1e-9], kalan, son_kat)
            self.assertEqual(Y["korkuluk"], 1100.0)


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
        self.assertEqual(CK.tutarlilik_duzeltmeleri(g, A), {"kabin_kasnak_arasi": g["aski"]["kasnak_arasi"]})


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
        self.assertAlmostEqual(
            gi["aski_kaciklik_x"],
            kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 - g["kabin_ray"]["kapi_arasi"],
        )
        self.assertEqual(gi["sarilma_acisi"], 180.0)
        self.assertEqual(gi["kasnak_tek_yon"], 2)
        #  Duvardan duvara kiriş:  açıklık kuyu derinliği, yük tahrik kasnağında
        self.assertEqual(gi["yan_yatak_boyu"], g["kuyu"]["derinlik"])
        self.assertAlmostEqual(s["ara"]["makine.X"], (G["P"][1] + G["W"][1]) / 2.0)
        b2 = next(b for b in s["bolumler"] if b["kimlik"] == "makine_konstruksiyonu")
        self.assertTrue(any("duvardan duvara" in str(a.get("kaynak", "")) for a in b2["adimlar"]))
        self.assertFalse(b2.get("eksik_hesap"))
        #  Son kat 4.500:  makine ve kirişler kabinin üstünde — bölüm 11 uygun
        b11 = next(b for b in s["bolumler"] if b["kimlik"] == "siginma_alanlari")
        self.assertTrue(b11["sonuc"]["uygun"], b11["sonuc"]["metin"])

    def test_makine_daireli(self):
        s = UY.hesapla({**ARKA, **MD})
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertEqual(s["girdi"]["sarilma_acisi"], 180.0)
        self.assertFalse(s["ozet"].get("eksik_hesap"))


if __name__ == "__main__":
    unittest.main()
