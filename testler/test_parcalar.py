# -*- coding: utf-8 -*-
"""PARÇA KÜTÜPHANESİ ( cizim/parcalar ):  parçaların gerçek biçimleri kaynağıyla
tutarlıdır."""
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [KOK, os.path.join(KOK, "hesap")]

from cizim import parcalar as CP                       # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT   # noqa: E402


class RayKesiti(unittest.TestCase):
    """ISO 7465 / ISO 8100-33 kesiti:  çokgenin alanı kesit alanını ( S ) verir —
    ölçülerin yorumu ( n, c, f, g ) doğrudur."""

    #  ( b1, h1 ) → S mm²:  ISO 7465:2007 / ISO 8100-33:2022 Tablo 3 ve 5;
    #  T125/B ve T127-2/B hesabın RAY_PROFILI'nden ( ISO'nun B tablosu elimizde değil )
    S = {(50, 50): 475, (70, 65): 940, (75, 62): 1091, (82, 68): 1091, (89, 62): 1577,
         (90, 75): 1725, (125, 82): 2290, (127, 89): 2863}

    def test_alan_iso_kesit_alanini_verir(self):
        for (b, h), s_ in self.S.items():
            with self.subTest(profil=(b, h)):
                self.assertAlmostEqual(CP.alan(CP.ray_kesiti(b, h)) / s_, 1.0, delta=0.01)

    def test_hesabin_butun_profilleri_kutuphanede(self):
        for profil in MT.RAY_PROFILLERI:
            b, h = (float(x.replace(",", ".")) for x in profil.split("x")[:2])
            self.assertIsNotNone(CP.ray_kesiti(b, h), profil)

    def test_hesabin_taban_kalinligi_ve_yuksekligi_kutuphaneyle_ayni(self):
        """Hesabın σF'sine giren f ( taban kalınlığı ) ve h1, çizilen kesitinkiyle
        aynı:  paralel tabanlı rayda f = p ( T50/A:  5 — kaynak 8 yazıyordu )."""
        for profil, f, _b, h1, _hbf, _hf in MT.RAY_GEOMETRI:
            b, h = (round(float(x.replace(",", "."))) for x in profil.split("x")[:2])
            if (b, h) in CP.RAY_EGIK:
                b1_, h1_, _k, _n, _c, f_, _g = CP.RAY_EGIK[(b, h)]
            else:
                b1_, h1_, _k, f_ = CP.RAY_PARALEL[(b, h)]
            with self.subTest(profil=profil):
                self.assertEqual((f, h1), (f_, h1_))

    def test_kesit_simetrik_ve_boyutlu(self):
        for (b, h) in list(CP.RAY_EGIK) + list(CP.RAY_PARALEL):
            k = CP.ray_kesiti(b, h)
            us, vs = [p[0] for p in k], [p[1] for p in k]
            self.assertEqual((min(us), max(us)), (0.0, h))
            self.assertEqual((min(vs), max(vs)), (-b / 2.0, b / 2.0))
            self.assertEqual(sorted(vs), sorted(-v for v in vs))

    def test_tabloda_olmayan_profil_zarfla_cizilir(self):
        self.assertIsNone(CP.ray_kesiti(100, 100))
        self.assertIsNone(CP.ray_bicimi(100, 100, 0, 0, 1))


class KapiKesiti(unittest.TestCase):
    """Kat ve kabin kapısı ( parcalar ):  kasa, eşik, oluk, kanat — markasız ortak
    biçim, zarfların içinde;  kuyu planında her kapı tipinde ve iki montajda."""

    TIPLER = ("Teleskopik Sol", "Teleskopik Sağ", "Teleskopik 3 Kanat Sol", "Otomatik Merkezi",
              "Otomatik Merkezi 4 Kanat", "Manuel Sol")

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE
        cls.planlar = {}
        for tip in cls.TIPLER:
            for montaj in ("Kuyu içine", "Duvar boşluğuna"):
                v = Y._veri(1000, True, "Arka", kat_kapisi_tipi=tip)
                v["asansorler"][0]["kapi_montaji"] = montaj
                g, _A, hata = Y._g(v)
                cls.planlar[(tip, montaj)] = (g, CGE.plan(g))

    def _adli(self, e, *adlar):
        return [x for x in e if x.get("ad") in adlar]

    def test_bicim_zarfin_icinde(self):
        adlar = ("kapi_kasasi", "kat_esigi", "kat_kanadi", "kanat_cebi", "kabin_esigi",
                 "kabin_kanadi", "kabin_kanat_cebi")
        for (tip, montaj), (_g, e) in self.planlar.items():
            for el in self._adli(e, *adlar):
                with self.subTest(tip=tip, montaj=montaj, ad=el["ad"]):
                    self.assertIn("bicim", el)
                    for p in el["bicim"]:
                        for x, y in p["noktalar"]:
                            self.assertTrue(el["x"] - 1e-6 <= x <= el["x"] + el["g"] + 1e-6
                                            and el["y"] - 1e-6 <= y <= el["y"] + el["d"] + 1e-6)

    def test_oluk_kanadin_altindan_gecmez(self):
        for (tip, montaj), (_g, e) in self.planlar.items():
            kanat = self._adli(e, "kat_kanadi", "kabin_kanadi", "kanat_durdurucu")
            oluk = [p for el in self._adli(e, "kat_esigi", "kanat_cebi", "kabin_esigi", "kabin_kanat_cebi")
                    for p in el["bicim"] if p.get("ince")]
            with self.subTest(tip=tip, montaj=montaj):
                if tip.startswith("Manuel"):
                    self.assertEqual(oluk, [])          # menteşeli kapının oluğu yok
                    continue
                self.assertTrue(oluk)
                for p in oluk:
                    (a, y), (b, _y) = p["noktalar"]
                    for k in kanat:
                        if k["y"] < y < k["y"] + k["d"]:
                            self.assertFalse(a < k["x"] + k["g"] - 1e-6 and k["x"] < b - 1e-6,
                                             (p, k["ad"], k["x"], k["g"]))

    def test_esikle_cep_arasinda_cizgi_yok(self):
        for (tip, montaj), (g, e) in self.planlar.items():
            if tip.startswith("Manuel"):
                continue
            esik = self._adli(e, "kat_esigi")[0]
            x0, x1 = esik["x"], esik["x"] + esik["g"]
            ceple = {round(c["x"] + c["g"]) for c in self._adli(e, "kanat_cebi")} | \
                    {round(c["x"]) for c in self._adli(e, "kanat_cebi")}
            for el in self._adli(e, "kat_esigi", "kanat_cebi"):
                for p in el["bicim"]:
                    (a, ya), (b, yb) = p["noktalar"][0], p["noktalar"][-1]
                    if abs(a - b) < 1e-6 and round(a) in ceple and round(a) in (round(x0), round(x1)):
                        self.fail(f"{tip} {montaj}:  eşik ile cep arasında düşey çizgi ( x = {a} )")

    def test_kanadin_yuzu_kendi_tarafinda(self):
        """Kat kapısı kanadının düz yüzü kata ( küçük y ), kabin kapısınınki kabine."""
        g, e = self.planlar[("Teleskopik Sol", "Kuyu içine")]
        for el in self._adli(e, "kat_kanadi", "kabin_kanadi"):
            nok = el["bicim"][0]["noktalar"]
            yuz = nok[2][1]                      # ( x0, yüz ) → ( x0 + g, yüz ) boydan boya
            self.assertEqual(yuz, el["y"] if el["ad"] == "kat_kanadi" else el["y"] + el["d"])
            self.assertEqual((nok[2][0], nok[3][0]), (el["x"], el["x"] + el["g"]))


class RayKonsolu(unittest.TestCase):
    """Kabin rayının duvar konsolu ( TSE K 179 tipi çift L — Savera standart
    konsolu ) ve tırnakları ( Donati GF ) — parcalar."""

    def test_konsol_tipi_ray_grubundan(self):
        self.assertEqual(CP.konsol_tipi(50)[:4], (130, 50, 75, 4))
        self.assertEqual(CP.konsol_tipi(89)[:4], (200, 62, 95, 5))
        self.assertEqual(CP.konsol_tipi(127)[:4], (270, 65, 100, 6))

    def test_uzun_aralikta_ayaklar_uzar_ve_bindirir(self):
        """Standart kuyuda duvar – ray arkası 313:  ayaklar 204'er, bindirme 95
        ( Savera C ), iki cıvata bindirmede."""
        b = CP.konsol_cifti_bicimi(0.0, 313.0, 0.0, 300.0, 89)
        ray_konsolu = b[0]["noktalar"]
        self.assertEqual(min(p[0] for p in ray_konsolu), 313 - 204)
        civatalar = [q for q in b if len(q["noktalar"]) == 6]
        self.assertEqual(len(civatalar), 2)
        for q in civatalar:
            xs = [p[0] for p in q["noktalar"]]
            self.assertTrue(313 - 204 < min(xs) and max(xs) < 204)       # bindirmenin içinde
        for q in b:                                                      # duvardan raya, enin içinde
            for x, y in q["noktalar"]:
                self.assertTrue(0 <= x <= 313 and -150 <= y <= 150)

    def test_tirnak_tabana_gomulmez_delik_tabana_degmez(self):
        for (b1, h1) in list(CP.RAY_EGIK) + list(CP.RAY_PARALEL):
            g, k = CP.ray_taban_ucu(b1, h1), CP.ray_dil_kalinligi(b1, h1)
            t = CP.TIRNAK.get(round(k))
            if t is None:
                continue
            L, _en, h2, h1_, d = t
            with self.subTest(ray=(b1, h1)):
                self.assertGreaterEqual(h2, g)                           # topuk tabandan yüksek
                b = CP.tirnak_bicimi(0.0, 0.0, b1, g, k, +1, J=5)
                for q in b[0::3]:                                        # tırnaklar
                    for u, v in q["noktalar"]:
                        if abs(v) < b1 / 2.0 - 1e-6:
                            self.assertGreaterEqual(u, g - 1e-6)         # dil tabanın üstünde
                vb = b1 / 2.0 + d / 2.0 + CP.TIRNAK_PAYI
                self.assertGreaterEqual(vb - d / 2.0, b1 / 2.0)

    def test_planda_konsol_plaka_ve_kolun_icinde(self):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE
        for yer in ("Sağ", "Sol", "Arka"):
            g, _A, _h = Y._g(Y._veri(630, True, yer))
            e = CGE.plan(g)
            for kol in [x for x in e if x.get("ad") == "kol" and x.get("bicim")]:
                #  kola bitişik plaka;  biçim ikisinin kapsadığı dikdörtgende
                plaka = next(x for x in e if x.get("ad") == "plaka"
                             and x["y"] <= kol["y"] and kol["y"] + kol["d"] <= x["y"] + x["d"]
                             and (abs(x["x"] + x["g"] - kol["x"]) < 1e-6
                                  or abs(kol["x"] + kol["g"] - x["x"]) < 1e-6))
                x0, x1 = min(kol["x"], plaka["x"]), max(kol["x"] + kol["g"], plaka["x"] + plaka["g"])
                with self.subTest(yer=yer):
                    self.assertEqual(plaka["bicim"], [])
                    for q in kol["bicim"]:
                        for x, y in q["noktalar"]:
                            self.assertTrue(x0 - 1e-6 <= x <= x1 + 1e-6
                                            and plaka["y"] - 1e-6 <= y <= plaka["y"] + plaka["d"] + 1e-6)
            self.assertTrue(any(x.get("ad") == "ray_tirnagi" for x in e))


class PatenKesiti(unittest.TestCase):
    def test_yuva_dile_acilir(self):
        #  Yatay ray, dil ucu x = 0, taban +x yönünde:  yuva sağa açılır
        p = CP.paten_bicimi(-25, -50, 50, 100, 0.0, 16, +1)[0]["noktalar"]
        self.assertIn((0.0, -10.0), p)
        self.assertIn((25, -10.0), p)
        self.assertAlmostEqual(CP.alan(p), 50 * 100 - 25 * 20)


if __name__ == "__main__":
    unittest.main()
