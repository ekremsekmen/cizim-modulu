"""Yayın öncesi senaryo taramasının üç hatası ( 15 Eki ) — cikti/arastirma/SENARYO_HATALARI.md.

1.  Kabin rayı / konsolu duvara giriyordu, denetim yoktu.
2.  Kabin altı kasnak ve halat engelleri eksikti.
3.  Arka ağırlıklı MRL'de kuyu üstü planının üst ölçü zinciri ağırlığın y'sini
    x diye yazıyordu.
"""

import copy
import itertools
import unittest

from cizim import geometri, girdi, kabin_ustu, kuyu_ustu
from temel import eleman_kutusu
from testler import test_yerlesim_saglamligi


def _kaydir(dx):
    """Örnek girdi ( ağırlık solda, sağ ray – duvar 83 mm ) kabini dx kaydırılmış."""
    g = copy.deepcopy(girdi.ORNEK)
    g["kabin"]["kaciklik_y"] += dx
    return g


class KabinRayiDuvar(unittest.TestCase):
    """Eşik 0 ( kullanıcı kararı ):  ray arkası – duvar < 0 hata;  dar ama
    geçerli boşlukta konsol plakası boşluk kadar çizilir."""

    def test_bosluk_cizimle_ayni(self):
        self.assertEqual(girdi.kabin_rayi_duvar_bosluklari(girdi.ORNEK)["Sağ"], 83.0)

    def test_duvara_giren_ray_hata(self):
        hata = girdi.dogrula(_kaydir(100))  # sağ boşluk −17
        self.assertTrue(any("Kabin rayı sağ duvara 17 mm giriyor" in h for h in hata), hata)

    def test_sifir_bosluk_gecerli(self):
        hata = girdi.dogrula(_kaydir(83))
        self.assertFalse(any("Kabin rayı" in h and "giriyor" in h for h in hata), hata)

    def test_agirlik_tarafinda_ara_kiris_denetler(self):
        #  ağırlık solda:  sol ray ara kirişe bağlıdır, bu kural o yanı saymaz
        g = _kaydir(-400)
        self.assertLess(girdi.kabin_rayi_duvar_bosluklari(g)["Sol"], 0)
        self.assertFalse(any("Kabin rayı sol duvara" in h for h in girdi.dogrula(g)))

    def test_dar_boslukta_plaka_raya_binmez(self):
        g = _kaydir(50)  # sağ boşluk 33
        G = g["kuyu"]["genislik"]
        e = geometri.plan(g)
        plaka = [eleman_kutusu(x) for x in e if x.get("ad") == "plaka" and eleman_kutusu(x)[2] >= G - 1]
        ray = [eleman_kutusu(x) for x in e if x.get("ad") == "kabin_ray"]
        self.assertTrue(plaka and ray)
        p = max(plaka, key=lambda k: k[2])
        self.assertAlmostEqual(p[2] - p[0], 33.0)
        sag_ray = max(ray, key=lambda k: k[2])
        self.assertLessEqual(p[0], G)
        self.assertGreaterEqual(p[0], sag_ray[2] - 1e-6)


def _aski(**ek):
    """Örnek girdi ( kabin altı, 1380 / ø 240, ağırlık solda ) askısı değişmiş."""
    g = copy.deepcopy(girdi.ORNEK)
    g["aski"].update(ek)
    return g


def _hata(g):
    return kabin_ustu.yerlesim(g)["hata"]


def _sag_parca(g, ad):
    e = geometri.plan(g, kapi_duzeyi=False)
    return max((eleman_kutusu(x) for x in e if x.get("ad") == ad), key=lambda k: k[2])


class KasnakVeHalatEngelleri(unittest.TestCase):
    """Kabin kasnağı kabinle bütün kuyu boyunca gider;  halat kuyuya sabit bir
    düşey çizgidir ( pay 20 mm — kullanıcı kararı )."""

    def setUp(self):
        g = girdi.ORNEK
        self.kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        self.ry = g["kabin_ray"]["kapi_arasi"]
        #  kasnak_kaciklik 0'da kasnakların derinlikteki yeri
        self.y0 = geometri.halat_konumlari(_aski(kasnak_kaciklik=0.0))[0][1]

    def _halat_yeri(self, x, y):
        """Sağ halat ( x, y )'de olsun diye kasnak aralığı ve kaçıklığı."""
        return _aski(kasnak_arasi=2 * (x - self.kx - 120.0), kasnak_kaciklik=y - self.y0)

    def test_ornek_temiz(self):
        self.assertEqual(_hata(girdi.ORNEK), [])

    def test_kasnak_raya_binince_hata(self):
        ray = _sag_parca(girdi.ORNEK, "kabin_ray")
        g = self._halat_yeri(ray[2] - 10, self.ry)
        self.assertTrue(
            any(h.startswith("Kabin kasnağı (") and "kabin rayı" in h for h in _hata(g)), _hata(g)
        )

    def test_halat_konsolun_gercek_zarfinda(self):
        #  ray arkası ile konsol plakası arasında, kolun ( ±50 ) dışında ama
        #  konsolun boyu ( ±150 ) içinde:  eski denetim görmüyordu
        ray = _sag_parca(girdi.ORNEK, "kabin_ray")
        g = self._halat_yeri(ray[2] + 5, self.ry + 120)
        self.assertTrue(
            any(h.startswith("Halat (") and ("plaka" in h or "kol" in h) for h in _hata(g)), _hata(g)
        )

    def test_kabin_altinda_halat_sase_dikmesine_degemez(self):
        #  dikme rayı sarar ( y 1017 – 1317, rayın tabanı 1122 – 1211 ):  halat
        #  dikmenin raydan uzak arka köşesinde
        d = _sag_parca(girdi.ORNEK, "sase_dikme")
        g = self._halat_yeri(d[0] + 15, d[3] - 25)
        self.assertTrue(any(h.startswith("Halat (") and "şase dikmesi" in h for h in _hata(g)), _hata(g))

    def test_dusey_kural_carpinca_eski_kural(self):
        #  r016 ( senaryo taraması ):  düşey iniş kuralının aralığı kasnağı ara
        #  kirişe sokuyordu;  çarpınca eski kural ( kabin genişliği + 30 )
        v = test_yerlesim_saglamligi.standart_istek(
            450, False, "Sağ", aski_duzeni="Kabin altı", kabin_yana_kaciklik=-150
        )
        v["asansorler"][0].update(kuyu_genisligi=2100, kuyu_derinligi=2150)
        d = test_yerlesim_saglamligi.cizim_yaniti(copy.deepcopy(v))
        self.assertTrue(d.get("aktif"), d.get("hata"))
        g, _A, _h = test_yerlesim_saglamligi.duzen_girdisi(copy.deepcopy(v))
        self.assertEqual(g["aski"]["kasnak_arasi"], g["kabin"]["genislik"] + 30)
        self.assertEqual(_hata(g), [])


class ArkaMrlOlcuZinciri(unittest.TestCase):
    """`Y["ex"]` ağırlık inişinin HALAT DÜZLEMİ boyunca koordinatıdır ( arkada
    y );  üst zincir ağırlık ekseninin plandaki x'ini ( `ag_eksen_x` ) ölçer."""

    def test_ust_zincir_agirlik_eksenini_olcer_ve_kuyuda_kalir(self):
        sayilan = 0
        for Q, kac, ek_G in itertools.product(
            test_yerlesim_saglamligi.KABIN, (0, -150, 150), (650, 800, 1100)
        ):
            ek = {"kabin_yana_kaciklik": kac} if kac else {}
            v = test_yerlesim_saglamligi.standart_istek(
                Q, True, "Arka", aski_duzeni="Kabin üstü", makine_raya_biniyor="Bina yapısına", **ek
            )
            v["asansorler"][0]["kuyu_genisligi"] = test_yerlesim_saglamligi.KABIN[Q][0] + ek_G
            g, _A, _h = test_yerlesim_saglamligi.duzen_girdisi(copy.deepcopy(v))
            Y = kuyu_ustu.yerlesim(g)
            if Y.get("hata"):
                continue
            sayilan += 1
            k = g["kuyu"]
            #  Acil pano ve önündeki çalışma alanı durakta ( kuyunun dışında ) — doğru
            ust = {
                round(p, 1)
                for el in kuyu_ustu._olculer(g, Y)
                if el["yon"] == "yatay" and "Acil pano" not in (el.get("kural") or "")
                for p in (el["a"][0], el["b"][0])
            }
            with self.subTest(Q=Q, kaciklik=kac, G=k["genislik"]):
                eksen = round((Y["blok"][0] + Y["blok"][2]) / 2.0, 1)
                self.assertIn(eksen, ust)
                self.assertTrue(
                    all(-k["duvar_sol"] - 1 <= p <= k["genislik"] + k["duvar_sag"] + 1 for p in ust), ust
                )
        self.assertGreater(sayilan, 40)


if __name__ == "__main__":
    unittest.main()
