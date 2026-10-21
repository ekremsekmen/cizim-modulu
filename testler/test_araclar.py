"""GELİŞTİRME ARAÇLARI ( araclar/ ) — taramanın hüküm karşılaştırması bir
değişikliği kaçırırsa tarama boşuna "geçti" der."""

import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from araclar import fiziksel
from araclar import kesisme
from araclar import tarama
from cizim import cizimler
from cizim import eleman
from cizim import girdi
from cizim import kuyu_kesiti
from cizim import pafta

KAYIT = {"ana": {"A": {"durum": "çizildi", "sebep": ""}, "B": {"durum": "ret", "sebep": "X sığmıyor"}}}


class Karsilastirma(unittest.TestCase):
    def test_ayni_hukum_fark_yok(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": []},
            {"ad": "B", "durum": "ret", "hata": ["X sığmıyor", "Y de"]},
        ]
        self.assertEqual(tarama.karsilastir("ana", sonuc, KAYIT), [])

    def test_hukum_ve_sebep_degisimi(self):
        sonuc = [
            {"ad": "A", "durum": "ret", "hata": ["Z yok"]},
            {"ad": "B", "durum": "ret", "hata": ["W yok"]},
        ]
        f = tarama.karsilastir("ana", sonuc, KAYIT)
        self.assertEqual(
            f, ["A:  çizildi → ret  ( Z yok )", "B:  ret → ret  ( W yok )  ·  önceki sebep:  X sığmıyor"]
        )

    def test_sorun_cokme_ve_eksik_duzen(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": ["kuyu_plani: NaN kabin"]},
            {"ad": "C", "durum": "çöktü", "ayrinti": "KeyError"},
        ]
        f = tarama.karsilastir("ana", sonuc, KAYIT)
        self.assertIn("düzen artık taranmıyor:  B", f)
        self.assertIn("yeni düzen ( kayıtta yok ):  C  →  çöktü", f)
        self.assertIn("SORUN  A:  kuyu_plani: NaN kabin", f)
        self.assertIn("ÇÖKTÜ  C:  KeyError", f)

    def test_kayit_butun_gruplari_kapsar(self):
        import json

        with open(tarama.HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)
        self.assertEqual(sorted(kayit), sorted(tarama.GRUPLAR))
        self.assertEqual(
            {g: len(v) for g, v in kayit.items()},
            {g: sum(1 for _ in tarama.duzenler(g)) for g in tarama.GRUPLAR},
        )


def _beton(x, y, g, d):
    return eleman.dikdortgen("TARAMA", x, y, g, d, tip="tarama")


def _ornek():
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in girdi.ORNEK.items()}


class Kesisme(unittest.TestCase):
    """araclar/kesisme.py:  biçimi olan parçada çizilen biçimdir, dikdörtgen yalnız
    mantık zarfı ( svg._bicim zarfı çizmez ) — 21 Eki:  ağırlık konsolunun
    görünmeyen zarfı perde yazısına "binen" sayılıyordu ( 4815-6 DBGW 1315,
    63444-2 kuyu 2455 )."""

    def _yazi(self):
        return eleman.yazi(138.25, 651.25, "AĞIRLIK PERDESİ", 70.0, aci=90)

    def test_bicimli_parcada_zarf_kenari_sayilmaz(self):
        plaka = eleman.dikdortgen("KONSOL", 0, 282, 160, 100, ad="plaka")
        plaka["bicim"] = [{"noktalar": [(0, 292), (40, 292), (40, 1788), (0, 1788)]}]
        self.assertEqual(kesisme.kesismeler([plaka, self._yazi()]), [])
        #  Biçimsiz aynı dikdörtgen çizilir:  kenarı yazıdan geçer
        dz = eleman.dikdortgen("KONSOL", 0, 282, 160, 100, ad="plaka")
        self.assertEqual([x[2:] for x in kesisme.kesismeler([dz, self._yazi()])], [("KONSOL", "plaka")] * 2)

    def test_duvar_ici_kenar_payiyla(self):
        """Duvara 1 mm giren yazı kutusu ( kâğıtta 0,05 mm ) duvarın içinde sayılmaz
        — kenar denetimiyle aynı pay ( 2·k );  gerçekten içindeki sayılır."""
        duvar = eleman.dikdortgen("TARAMA", -150, 0, 150, 1850, tip="tarama")
        yazi = eleman.yazi(328, 1698, "HALAT BAĞLANTISI", 70.0)
        kb = kesisme.yazi_kutusu(yazi)
        self.assertLess(kb[1], 0.0)  # kutu duvara giriyor ( −1 )
        self.assertEqual(kesisme.kesismeler([duvar, yazi]), [])
        yazi["x"] -= 100
        self.assertIn("TARAMA-İÇİ", [x[2] for x in kesisme.kesismeler([duvar, yazi])])

    def test_bicimin_kenari_sayilir(self):
        kol = eleman.dikdortgen("KONSOL", 160, 2000, 100, 30, ad="kol")
        kol["bicim"] = [{"noktalar": [(0, 600), (283, 600), (283, 640), (0, 640)]}]
        f = kesisme.kesismeler([kol, self._yazi()])
        self.assertTrue(f and all(x[2:] == ("KONSOL", "kol") for x in f), f)


class Fiziksel(unittest.TestCase):
    """araclar/fiziksel.py:  her kural bir hatalı, bir doğru düzenle ( 17 Eki —
    PR #26'nın üç hatası bu kurallarla bulundu )."""

    def test_r1_beton_parcaya_giriyor(self):
        duvar = _beton(1000, 0, 200, 2000)
        icinde = eleman.dikdortgen("KONSOL", 980, 500, 150, 150, ad="makine_sasesi")
        yaninda = eleman.dikdortgen("KONSOL", 840, 500, 150, 150, ad="makine_sasesi")
        f = fiziksel.sorunlar({}, "makine_dairesi", [duvar, icinde])
        self.assertEqual(len(f), 1)
        self.assertIn("R1 beton parçaya giriyor  makine_sasesi", f[0])
        self.assertEqual(fiziksel.sorunlar({}, "makine_dairesi", [duvar, yaninda]), [])

    def test_r1_bicime_bakar(self):
        """Biçimi olan parçada zarfa değil biçime bakılır:  zarfı duvara
        değen ama biçimi değmeyen parça sorun değildir."""
        duvar = _beton(1000, 0, 200, 2000)
        el = eleman.dikdortgen("KONSOL", 900, 500, 150, 150, ad="konsol")
        el["bicim"] = [{"noktalar": [(900, 500), (990, 500), (990, 650), (900, 650)]}]
        self.assertEqual(fiziksel.sorunlar({}, "makine_dairesi", [duvar, el]), [])

    def test_r2_kuyu_boslugunda_beton(self):
        g = _ornek()
        tavan = kuyu_kesiti.yerlesim(g)["M"]["tavan"]
        D = g["kuyu"]["derinlik"]
        e = [_beton(-150, -1500, D + 300, 150), _beton(D, -1500, 150, tavan + 1650)]
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", e), [])
        #  Kuyunun içine inen duvar ( oda duvarı hatası, PR #26 )
        e.append(_beton(D - 300, tavan - 1200, 200, 1200))
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", e)
        self.assertTrue(any("R2 kuyu boşluğunda beton" in m for m in f), f)

    def test_r3_duvarin_alti_bosta_lento_haric(self):
        g = _ornek()
        taban = _beton(-150, -1500, 2500, 150)
        havada = _beton(-150, 3000, 150, 2000)
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, havada])
        self.assertTrue(any("R3 duvarın altı boşta" in m for m in f), f)
        #  Altında kapı varsa lentodur
        kapi = eleman.dikdortgen("KAPI", -150, 0, 150, 2300)
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, havada, kapi]), [])

    def test_r3_dar_doseme_duvar_sayilmaz(self):
        """Kuyunun arkasından 195 mm taşan, 250 kalın oda döşemesi:  dar da olsa
        döşemedir ( 21 Eki bulanık tarama — 63444-2, kuyu derinliği 2455 ).  Aynı
        ölçüde adsız düşey beton ise duvardır, altı boştaysa sorun."""
        g = _ornek()
        taban = _beton(-150, -1500, 2500, 150)
        doseme = _beton(2705, 6000, 195, 250)
        ad = eleman.ad(eleman.dikdortgen("KUYU-DUVAR", 2705, 6000, 195, 250), "oda_dosemesi")
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, doseme, ad]), [])
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, doseme])
        self.assertTrue(any("R3 duvarın altı boşta" in m for m in f), f)

    def test_r4_kuyu_planinda_binis(self):
        kabin = eleman.dikdortgen("KABIN", 500, 300, 1000, 1200, ad="kabin")
        agirlik = eleman.dikdortgen("AGIRLIK", 1450, 400, 150, 800, ad="agirlik")
        f = fiziksel.sorunlar({}, "kuyu_plani", [kabin, agirlik])
        self.assertEqual(len(f), 1)
        self.assertIn("R4 kabin / agirlik biniyor", f[0])
        agirlik["x"] = 1550
        self.assertEqual(fiziksel.sorunlar({}, "kuyu_plani", [kabin, agirlik]), [])

    def test_ornek_projeler_temiz(self):
        """Programın örnek projeleri ( makine dairesiz ve daireli ) bütün
        çizimlerinde fiziksel olarak tutarlıdır."""
        for md in (False, True):
            with self.subTest(makine_dairesi=md):
                g = _ornek()
                if md:
                    g["makine"] = dict(g["makine"], yeri="Makine dairesi")
                for c in pafta.SIRA_MD if md else pafta.SIRA_MRL:
                    e = cizimler.CIZIMLER[c][1](g)
                    self.assertEqual(fiziksel.sorunlar(g, c, e), [], c)


if __name__ == "__main__":
    unittest.main()
