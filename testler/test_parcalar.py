# -*- coding: utf-8 -*-
"""PARÇA KÜTÜPHANESİ ( cizim/parcalar ):  parçaların gerçek biçimleri kaynağıyla
tutarlıdır."""

import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [KOK, os.path.join(KOK, "hesap")]

from cizim import parcalar as CP  # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT  # noqa: E402


class RayKesiti(unittest.TestCase):
    """ISO 7465 / ISO 8100-33 kesiti:  çokgenin alanı kesit alanını ( S ) verir —
    ölçülerin yorumu ( n, c, f, g ) doğrudur."""

    #  ( b1, h1 ) → S mm²:  ISO 7465:2007 / ISO 8100-33:2022 Tablo 3 ve 5;
    #  T125/B ve T127-2/B hesabın RAY_PROFILI'nden ( ISO'nun B tablosu elimizde değil )
    S = {
        (50, 50): 475,
        (70, 65): 940,
        (75, 62): 1091,
        (82, 68): 1091,
        (89, 62): 1577,
        (90, 75): 1725,
        (125, 82): 2290,
        (127, 89): 2863,
    }

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
        for b, h in list(CP.RAY_EGIK) + list(CP.RAY_PARALEL):
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

    TIPLER = (
        "Teleskopik Sol",
        "Teleskopik Sağ",
        "Teleskopik 3 Kanat Sol",
        "Otomatik Merkezi",
        "Otomatik Merkezi 4 Kanat",
        "Manuel Sol",
    )

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE

        cls.planlar = {}
        for tip in cls.TIPLER:
            for montaj in ("Kuyu içine", "Duvar boşluğuna"):
                g, hata = Y.gecerli_duzen(1000, "Arka", kat_kapisi_tipi=tip, kapi_montaji=montaj)
                assert not hata, (tip, montaj, hata)
                cls.planlar[(tip, montaj)] = (g, CGE.plan(g))

    def _adli(self, e, *adlar):
        return [x for x in e if x.get("ad") in adlar]

    def test_bicim_zarfin_icinde(self):
        adlar = (
            "kapi_kasasi",
            "kat_esigi",
            "kat_kanadi",
            "kanat_cebi",
            "kabin_esigi",
            "kabin_kanadi",
            "kabin_kanat_cebi",
        )
        for (tip, montaj), (_g, e) in self.planlar.items():
            for el in self._adli(e, *adlar):
                with self.subTest(tip=tip, montaj=montaj, ad=el["ad"]):
                    self.assertIn("bicim", el)
                    for p in el["bicim"]:
                        for x, y in p["noktalar"]:
                            self.assertTrue(
                                el["x"] - 1e-6 <= x <= el["x"] + el["g"] + 1e-6
                                and el["y"] - 1e-6 <= y <= el["y"] + el["d"] + 1e-6
                            )

    def test_oluk_kanadin_altindan_gecmez(self):
        for (tip, montaj), (_g, e) in self.planlar.items():
            kanat = self._adli(e, "kat_kanadi", "kabin_kanadi", "kanat_durdurucu")
            oluk = [
                p
                for el in self._adli(e, "kat_esigi", "kanat_cebi", "kabin_esigi", "kabin_kanat_cebi")
                for p in el["bicim"]
                if p.get("ince")
            ]
            with self.subTest(tip=tip, montaj=montaj):
                if tip.startswith("Manuel"):
                    self.assertEqual(oluk, [])  # menteşeli kapının oluğu yok
                    continue
                self.assertTrue(oluk)
                for p in oluk:
                    (a, y), (b, _y) = p["noktalar"]
                    for k in kanat:
                        if k["y"] < y < k["y"] + k["d"]:
                            self.assertFalse(
                                a < k["x"] + k["g"] - 1e-6 and k["x"] < b - 1e-6, (p, k["ad"], k["x"], k["g"])
                            )

    def test_esikle_cep_arasinda_cizgi_yok(self):
        for (tip, montaj), (g, e) in self.planlar.items():
            if tip.startswith("Manuel"):
                continue
            esik = self._adli(e, "kat_esigi")[0]
            x0, x1 = esik["x"], esik["x"] + esik["g"]
            ceple = {round(c["x"] + c["g"]) for c in self._adli(e, "kanat_cebi")} | {
                round(c["x"]) for c in self._adli(e, "kanat_cebi")
            }
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
            yuz = nok[2][1]  # ( x0, yüz ) → ( x0 + g, yüz ) boydan boya
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
            self.assertTrue(313 - 204 < min(xs) and max(xs) < 204)  # bindirmenin içinde
        for q in b:  # duvardan raya, enin içinde
            for x, y in q["noktalar"]:
                self.assertTrue(0 <= x <= 313 and -150 <= y <= 150)

    def test_tirnak_tabana_gomulmez_delik_tabana_degmez(self):
        for b1, h1 in list(CP.RAY_EGIK) + list(CP.RAY_PARALEL):
            g, k = CP.ray_taban_ucu(b1, h1), CP.ray_dil_kalinligi(b1, h1)
            t = CP.TIRNAK.get(round(k))
            if t is None:
                continue
            L, _en, h2, h1_, d = t
            with self.subTest(ray=(b1, h1)):
                self.assertGreaterEqual(h2, g)  # topuk tabandan yüksek
                b = CP.tirnak_bicimi(0.0, 0.0, b1, g, k, +1, J=5)
                for q in b[0::3]:  # tırnaklar
                    for u, v in q["noktalar"]:
                        if abs(v) < b1 / 2.0 - 1e-6:
                            self.assertGreaterEqual(u, g - 1e-6)  # dil tabanın üstünde
                vb = b1 / 2.0 + d / 2.0 + CP.TIRNAK_PAYI
                self.assertGreaterEqual(vb - d / 2.0, b1 / 2.0)

    def test_planda_konsol_plaka_ve_kolun_icinde(self):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE

        for yer in ("Sağ", "Sol", "Arka"):
            g, hata = Y.gecerli_duzen(630, yer)
            self.assertFalse(hata, (yer, hata))
            e = CGE.plan(g)
            for kol in [x for x in e if x.get("ad") == "kol" and x.get("bicim")]:
                #  kola bitişik plaka;  biçim ikisinin kapsadığı dikdörtgende
                plaka = next(
                    x
                    for x in e
                    if x.get("ad") == "plaka"
                    and x["y"] <= kol["y"]
                    and kol["y"] + kol["d"] <= x["y"] + x["d"]
                    and (abs(x["x"] + x["g"] - kol["x"]) < 1e-6 or abs(kol["x"] + kol["g"] - x["x"]) < 1e-6)
                )
                x0, x1 = min(kol["x"], plaka["x"]), max(kol["x"] + kol["g"], plaka["x"] + plaka["g"])
                with self.subTest(yer=yer):
                    self.assertEqual(plaka["bicim"], [])
                    for q in kol["bicim"]:
                        for x, y in q["noktalar"]:
                            self.assertTrue(
                                x0 - 1e-6 <= x <= x1 + 1e-6
                                and plaka["y"] - 1e-6 <= y <= plaka["y"] + plaka["d"] + 1e-6
                            )
            self.assertTrue(any(x.get("ad") == "ray_tirnagi" for x in e))


class AgirlikCercevesi(unittest.TestCase):
    """Karşı ağırlık konsol çerçevesi ( LiftDesigner K431 · K111 · 1250 KG gibi ):
    40 mm'lik ray profilleri rayın tabanının dış yanında;  duvar profili yalnız
    yer varsa;  bütün raylar tırnaklı."""

    @staticmethod
    def _plan(yer, **ek):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE

        g, hata = Y.gecerli_duzen(630, yer, **ek)
        assert not hata, (yer, ek, hata)
        return g, CGE.plan(g)

    def test_ray_profili_tabanin_disinda_40(self):
        for yer in ("Sağ", "Sol", "Arka"):
            g, e = self._plan(yer)
            ag = g["agirlik"]
            profiller = [
                q
                for el in e
                if el.get("ad") in ("plaka", "kol") and el.get("bicim") and el["katman"] == "KONSOL"
                for q in el["bicim"]
                if el.get("ad") == "plaka" or el["g"] < 200 or el["d"] < 200
            ]
            arkalar = [el for el in e if el.get("ad") == "agirlik_ray"]
            with self.subTest(yer=yer):
                self.assertTrue(arkalar)
                ince = [
                    q
                    for q in profiller
                    if abs(
                        min(
                            max(p[0] for p in q["noktalar"]) - min(p[0] for p in q["noktalar"]),
                            max(p[1] for p in q["noktalar"]) - min(p[1] for p in q["noktalar"]),
                        )
                        - CP.CERCEVE_PROFILI
                    )
                    < 1e-6
                ]
                self.assertGreaterEqual(len(ince), 2)  # iki ağırlık rayının profili

    def test_duvar_profili_yalniz_yer_varsa(self):
        #  Standart düzende ağırlık – duvar arası 50:  40 + 20 sığmaz
        g, e = self._plan("Sağ")
        G = g["kuyu"]["genislik"]

        def duvar_profili(e):
            return [
                q
                for el in e
                if el.get("bicim") and el["katman"] == "KONSOL"
                for q in el["bicim"]
                if all(
                    abs(p[0] - G) < 1e-6 or abs(p[0] - (G - CP.CERCEVE_PROFILI)) < 1e-6 for p in q["noktalar"]
                )
            ]

        self.assertEqual(duvar_profili(e), [])
        #  Ağırlık duvardan 40 uzaklaşınca ( boşluk 90 ) çerçeve kapanır ( K431 )
        g2, e2 = self._plan("Sağ", agirlik_ray_duvar=g["agirlik"]["ray_duvar"] + 40)
        G = g2["kuyu"]["genislik"]
        self.assertEqual(len(duvar_profili(e2)), 1)

    def test_butun_raylar_tirnakli(self):
        for yer in ("Sağ", "Sol", "Arka"):
            _g, e = self._plan(yer)
            with self.subTest(yer=yer):
                #  2 kabin rayı ( biri duvar konsolunda, biri ara kirişte ya da iki
                #  duvar konsolunda ) + 2 ağırlık rayı
                self.assertEqual(sum(1 for el in e if el.get("ad") == "ray_tirnagi"), 4)


class PatenKesiti(unittest.TestCase):
    """Kaymalı paten ( Metroplast 804 · referans proje · LiftDesigner ):  gövde
    dilin ucunu kavrar, astar dile değer, uçta 1 mm boşluk ( Has );  zarfın içinde."""

    def test_yuva_dile_acilir_astar_dili_sarar(self):
        #  Yatay ray, dil ucu x = 0, taban +x yönünde:  yuva sağa açılır
        govde, astar = CP.paten_bicimi(-25, -50, 50, 100, 0.0, 16, +1)
        g = govde["noktalar"]
        self.assertIn((25.0, -15.0), g)  # yuva 30, çene uçları
        self.assertIn((25.0, 15.0), g)
        dip = -CP.PATEN_BOSLUK - CP.PATEN_ASTAR_DIBI  # yuvanın dibi ( x )
        self.assertIn((dip, -15.0), g)
        self.assertFalse(astar.get("kapali", True))
        a = astar["noktalar"]
        self.assertEqual(a[0], (25.0, -8.0))  # astarın içi dilin yüzünde
        self.assertEqual(a[1], (-CP.PATEN_BOSLUK, -8.0))  # uçta 1 mm
        for x, y in g + a:
            self.assertTrue(-25 - 1e-6 <= x <= 25 + 1e-6 and -50 - 1e-6 <= y <= 50 + 1e-6)

    def test_dort_yonde_ayni_govde(self):
        alanlar = set()
        for yatay in (True, False):
            for yon in (-1, 1):
                x0, y0, gg, dd = (-25, -50, 50, 100) if yatay else (-50, -25, 100, 50)
                govde = CP.paten_bicimi(x0, y0, gg, dd, 0.0, 9, yon, yatay)[0]["noktalar"]
                alanlar.add(round(CP.alan(govde), 6))
                #  çene uçları dilin tabanı yönünde
                uclar = [p[0] if yatay else p[1] for p in govde]
                self.assertAlmostEqual(max(uclar) if yon > 0 else -min(uclar), 25.0)
        self.assertEqual(len(alanlar), 1)


class MakaraliPaten(unittest.TestCase):
    def test_makaralar_dile_degmez_bosluk_bir(self):
        uc, yan1, yan2 = CP.makarali_paten_bicimi(0.0, 0.0, 9, +1, yatay=True)
        xs = [p[0] for p in uc["noktalar"]]
        self.assertAlmostEqual(max(xs), -CP.PATEN_BOSLUK)  # uç makarası dilin önünde
        self.assertAlmostEqual(max(xs) - min(xs), CP.MAKARA_CAPI)
        for m, s in ((yan1, -1), (yan2, 1)):
            ys = [p[1] for p in m["noktalar"]]
            yakin = max(ys) if s < 0 else min(ys)
            self.assertAlmostEqual(abs(yakin), 4.5)  # dilin yüzünde
            self.assertGreater(min(p[0] for p in m["noktalar"]), 0.0)  # dilin ucunun arkasında


class SaseDikmesi(unittest.TestCase):
    """Şase dikmesi raya açılan U:  sırtı patenin arkasında, kanatları dilin
    ucunu geçer ( LiftDesigner K431 · referans proje · Has )."""

    def test_u_kesit(self):
        q = CP.dikme_bicimi(100.0, 0.0, 300, 25, 5, -1)[0]
        self.assertTrue(q["dolu"])
        xs = [p[0] for p in q["noktalar"]]
        self.assertAlmostEqual(min(xs), 75.0)  # kanat ucu dil ucunu 25 geçer
        self.assertAlmostEqual(max(xs), 130.0)  # sırtın arkası
        self.assertAlmostEqual(CP.alan(q["noktalar"]), 5 * 300 + 2 * 5 * (55 - 5))

    def test_planda_paten_sirta_bagli_kabin_sirta_degmez(self):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE, sabitler as CS

        S = CS.sabitler()
        for yer in ("Sağ", "Sol", "Arka"):
            g, hata = Y.gecerli_duzen(630, yer)
            self.assertFalse(hata, (yer, hata))
            e = CGE.plan(g)
            kabin = next(x for x in e if x.get("ad") == "kabin_dis")
            patenler = [x for x in e if x["katman"] == "PATEN" and x.get("ad") != "agirlik_pateni"]
            dikmeler = [x for x in e if x.get("ad") == "sase_dikme"]
            with self.subTest(yer=yer):
                self.assertEqual((len(patenler), len(dikmeler)), (2, 2))
                for p in patenler:
                    d = next(
                        x
                        for x in dikmeler
                        if x["x"] <= p["x"] + 1e-6 and p["x"] + p["g"] <= x["x"] + x["g"] + 1e-6
                    )
                    sol = p["x"] + p["g"] / 2.0 < kabin["x"]
                    sirt = p["x"] + p["g"] if sol else p["x"]  # patenin arkası
                    xs = [pt[0] for pt in d["bicim"][0]["noktalar"]]
                    #  dikmenin sırtının ön yüzü patenin arkasında
                    self.assertIn(round(sirt, 6), {round(x, 6) for x in xs})
                    #  kabin dikmenin sırtının arkasında
                    if sol:
                        self.assertLessEqual(max(xs), kabin["x"])
                    else:
                        self.assertGreaterEqual(min(xs), kabin["x"] + kabin["g"])
                    self.assertEqual(d["d"], S["sase_dikme_derinlik"])

    def test_kiris_profili_planda_ve_yan_kesitte_50(self):
        #  Referans proje:  iki C profil 50 + 200 + 50 ( 8 Eki'ye dek planda 30 )
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE, kuyu_kesiti as CKK, sabitler as CS

        S = CS.sabitler()
        g, hata = Y.gecerli_duzen(630, "Sağ")
        self.assertFalse(hata)
        kiris = [x for x in CGE.plan(g) if x.get("ad") == "sase_kiris"]
        self.assertEqual([x["d"] for x in kiris], [CP.SASE_PROFIL_ENI] * 2)
        self.assertEqual(
            max(x["y"] + x["d"] for x in kiris) - min(x["y"] for x in kiris), S["sase_dikme_derinlik"]
        )
        yan = [x for x in CKK.yan_kesit(g) if x.get("ad") == "sase"]
        self.assertEqual([x["g"] for x in yan], [CP.SASE_PROFIL_ENI] * 2)


class AgirlikPatenleri(unittest.TestCase):
    """Karşı ağırlığın patenleri planda da çizilir:  kesitlerin kutusuyla aynı
    zarf ( kullanıcı kararı 30 Eyl:  iki tipte aynı iz ), biçim tipine göre."""

    def test_her_agirlik_rayinda_kesitteki_kutuyla_ayni(self):
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import geometri as CGE, kuyu_kesiti as CKK, baglantilar as CB

        for yer in ("Sağ", "Sol", "Arka"):
            for tip in ("Kaymalı", "Makaralı"):
                #  Arkadaki ağırlıkla 2:1'de 630 kg'ın tavanına çömelme alanı
                #  sığmaz ( çapraz halat — test_yerlesim_saglamligi ):  kesit yok
                g, hata = Y.gecerli_duzen(800 if yer == "Arka" else 630, yer)
                self.assertFalse(hata)
                g["agirlik"]["paten_tipi"] = tip
                e = CGE.plan(g)
                pt = [x for x in e if x.get("ad") == "agirlik_pateni"]
                with self.subTest(yer=yer, tip=tip):
                    self.assertEqual(len(pt), 2)
                    self.assertEqual([len(x["bicim"]) for x in pt], [3 if tip == "Makaralı" else 2] * 2)
                    Yk = CKK.yerlesim(g)
                    blok = next(
                        (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
                        for x in e
                        if x.get("ad") == "agirlik_blok"
                    )
                    raylar = [r for r in Yk["M"]["raylar"] if r["tur"] == "agirlik"]
                    kesit = sorted(
                        tuple(round(v, 6) for v in p["k"][:4])
                        for p in CB.agirlik_patenleri(g, Yk["S"], blok, raylar, 0, 1)
                    )
                    plan = sorted(
                        tuple(round(v, 6) for v in (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"]))
                        for x in pt
                    )
                    self.assertEqual(kesit, plan)

    def test_makaralinin_tasan_makaralari_kabin_acikligina_sayilir(self):
        #  m.5.2.5.5.1 h:  ağırlığa BAĞLI parçalar da kabinden 50 uzakta.  Arkadaki
        #  ağırlıkta blok kabinden 51 uzakken kaymalı paten ( 100 ) 120'lik bloğun
        #  içinde kalır, makaralının yan makaraları ( 75 + dil / 2 ) bloğu aşar.
        sys.path.insert(0, os.path.join(KOK, "testler"))
        import test_yerlesim_saglamligi as Y
        from cizim import girdi as CGI, sabitler as CS

        S = CS.sabitler()
        g, hata = Y.gecerli_duzen(630, "Arka")
        self.assertFalse(hata)
        ag, kb, k = g["agirlik"], g["kabin"], g["kuyu"]
        ag["derinlik"] = 120.0  # ince ağırlık ( pik dolgu )
        arka = kb["on_pay"] + kb["derinlik"] + S["kabin_pano_arka"]
        ag["ray_duvar"] = k["derinlik"] - ag["derinlik"] / 2.0 - arka - 51.0
        uzun = CP.MAKARA_CAPI + CP.ray_dil_kalinligi(ag["b"], ag["h"]) / 2.0 - ag["derinlik"] / 2.0
        self.assertGreater(uzun, 1.0)
        for tip, ret in (("Kaymalı", False), ("Makaralı", True)):
            ag["paten_tipi"] = tip
            h = CGI.dogrula(g)
            with self.subTest(tip=tip):
                self.assertEqual(any("m.5.2.5.5.1 h" in x for x in h), ret, h)


if __name__ == "__main__":
    unittest.main()
