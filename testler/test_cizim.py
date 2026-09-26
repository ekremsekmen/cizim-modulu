# -*- coding: utf-8 -*-
"""
TEST 15 — ÇİZİM MODÜLÜ  ( hesap motorundan bağımsız )

Çizim piksel piksel değil, GEOMETRİ olarak denetlenir:
  · ölçü zincirleri kapanıyor mu  ( parçaların toplamı = toplam ölçü )
  · her parça kuyunun içinde mi
  · kabin ile karşı ağırlık / raylar çakışıyor mu
  · girdi sözleşmesi eksik ya da tutarsız girdiyi reddediyor mu
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cizim import geometri as CGE            # noqa: E402
from cizim import girdi as CG                # noqa: E402
from cizim import svg as CSV                 # noqa: E402


def _ornek(**ezme):
    g = {k: (dict(v) if isinstance(v, dict) else v) for k, v in CG.ORNEK.items()}
    g.setdefault("aski_orani", 2)
    g.setdefault("kasnak_capi", 240)
    g.setdefault("agirlik_kasnak_capi", 400)
    for bolum, d in ezme.items():
        g[bolum].update(d)
    return g


def _dikdortgenler(elemanlar, katman):
    return [el for el in elemanlar
            if el["tip"] == "dikdortgen" and el["katman"] == katman]


def _cakisma(a, b, pay=0.0):
    return (a["x"] + a["g"] - pay > b["x"] and b["x"] + b["g"] - pay > a["x"]
            and a["y"] + a["d"] - pay > b["y"] and b["y"] + b["d"] - pay > a["y"])


class SozlesmeDenetimi(unittest.TestCase):
    def test_ornek_gecerli(self):
        self.assertEqual(CG.dogrula(_ornek()), [])

    def test_eksik_bolum_reddedilir(self):
        g = _ornek(); g.pop("kapi")
        self.assertTrue(any("kapi" in h for h in CG.dogrula(g)))

    def test_sifir_ve_negatif_olcu_reddedilir(self):
        for bolum, alan in (("kuyu", "genislik"), ("kabin", "derinlik"), ("kapi", "genislik")):
            self.assertTrue(CG.dogrula(_ornek(**{bolum: {alan: 0}})), (bolum, alan))
            self.assertTrue(CG.dogrula(_ornek(**{bolum: {alan: -100}})), (bolum, alan))

    def test_kabin_kuyuya_sigmazsa_reddedilir(self):
        self.assertTrue(CG.dogrula(_ornek(kabin={"genislik": 2500})))
        self.assertTrue(CG.dogrula(_ornek(kabin={"derinlik": 2500})))

    def test_kapi_kuyuya_sigmazsa_reddedilir(self):
        self.assertTrue(CG.dogrula(_ornek(kapi={"sol_pay": 1500})))

    def test_agirlik_yeri_secenekleri(self):
        self.assertTrue(CG.dogrula(_ornek(agirlik={"yeri": "Ortada"})))
        for yer in CG.AGIRLIK_YERLERI:
            g = _ornek(agirlik={"yeri": yer})
            if yer == "Sağ":
                g["kabin"]["kaciklik_y"] = -130
            self.assertEqual(CG.dogrula(g), [])


class PlanGeometrisi(unittest.TestCase):
    def setUp(self):
        self.g = _ornek()
        self.e = CGE.plan(self.g)

    def test_olcu_zincirleri_kapaniyor(self):
        for z in CGE.zincirler(self.e):
            self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"], places=6,
                                   msg=f"zincir kapanmadı: {z}")

    def test_her_zincirde_en_az_bir_olcu(self):
        self.assertGreaterEqual(len(CGE.zincirler(self.e)), 6)

    def test_kabin_kuyu_icinde(self):
        k = self.g["kuyu"]
        for el in _dikdortgenler(self.e, "KABIN"):
            self.assertGreaterEqual(el["x"], 0)
            self.assertGreaterEqual(el["y"], 0)
            self.assertLessEqual(el["x"] + el["g"], k["genislik"])
            self.assertLessEqual(el["y"] + el["d"], k["derinlik"])

    def test_kabin_rayi_ekseni_kapi_arasindan(self):
        #  Ray ekseni, ray – kapı arası kadar kapı duvarından içeridedir.
        raylar = _dikdortgenler(self.e, "RAY")
        eksenler = {round(el["y"] + el["d"] / 2.0) for el in raylar}
        self.assertIn(round(self.g["kabin_ray"]["kapi_arasi"]), eksenler)

    def test_kabin_rayi_arasi_DBG_yuzden_yuze(self):
        """DBG, rayların BİRBİRİNE BAKAN YÜZLERİ arasıdır  ( eksenden değil )."""
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        raylar = _dikdortgenler(self.e, "RAY")
        sol = [el for el in raylar if el["x"] + el["g"] <= kx]
        sag = [el for el in raylar if el["x"] >= kx]
        self.assertTrue(sol and sag)
        self.assertAlmostEqual(max(el["x"] + el["g"] for el in sol), kx - kr["arasi"] / 2.0, places=6)
        self.assertAlmostEqual(min(el["x"] for el in sag), kx + kr["arasi"] / 2.0, places=6)

    def test_ray_yuksekligi_duvara_dogru(self):
        """Ray, kabine bakan yüzünden duvara doğru kendi yüksekliği kadar uzanır."""
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        raylar = _dikdortgenler(self.e, "RAY")
        sag = [el for el in raylar if el["x"] >= kx]
        self.assertAlmostEqual(max(el["x"] + el["g"] for el in sag),
                               kx + kr["arasi"] / 2.0 + kr["h"], places=6)

    def test_hicbir_donanim_kuyu_disina_tasmaz(self):
        k = self.g["kuyu"]
        for kat in ("KABIN", "KABIN-IC", "SASE", "KASNAK", "AGIRLIK", "PATEN", "PANO", "RAY", "KONSOL"):
            for el in _dikdortgenler(self.e, kat):
                self.assertGreaterEqual(round(el["x"], 6), 0, (kat, el))
                self.assertGreaterEqual(round(el["y"], 6), 0, (kat, el))
                self.assertLessEqual(round(el["x"] + el["g"], 6), k["genislik"], (kat, el))
                self.assertLessEqual(round(el["y"] + el["d"], 6), k["derinlik"], (kat, el))

    def test_konsol_plakasi_duvara_dayaniyor(self):
        from cizim import sabitler as CS
        S = CS.sabitler()
        k = self.g["kuyu"]
        plakalar = [el for el in _dikdortgenler(self.e, "KONSOL")
                    if el.get("ad") == "plaka"]
        self.assertEqual(len(plakalar), 4)        # 2 kabin rayı + 2 ağırlık rayı
        for el in plakalar:
            duvarda = abs(el["x"]) < 1e-6 or abs(el["x"] + el["g"] - k["genislik"]) < 1e-6
            self.assertTrue(duvarda, f"konsol plakası duvara dayanmıyor: {el}")

    def test_konsol_kolu_plaka_ile_rayi_birlestiriyor(self):
        """Kol bir ucuyla plakaya, öbür ucuyla rayın arkasına değmeli."""
        from cizim import sabitler as CS
        S = CS.sabitler()
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        ray_arkasi = {round(kx - kr["arasi"] / 2.0 - kr["h"], 3),
                      round(kx + kr["arasi"] / 2.0 + kr["h"], 3)}
        plaka_ucu = {0.0 + S["konsol_kabin_en"], k["genislik"] - S["konsol_kabin_en"]}
        kollar = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "kol"]
        self.assertEqual(len(kollar), 2)
        for el in kollar:
            uclar = {round(el["x"], 3), round(el["x"] + el["g"], 3)}
            self.assertTrue(uclar & ray_arkasi, f"kol raya değmiyor: {el}")
            self.assertTrue({round(u, 3) for u in plaka_ucu} & uclar, f"kol plakaya değmiyor: {el}")

    def test_paten_ray_yuzunu_kavriyor(self):
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        for el in _dikdortgenler(self.e, "PATEN"):
            merkez = el["x"] + el["g"] / 2.0
            self.assertIn(round(merkez, 3),
                          (round(kx - kr["arasi"] / 2.0, 3), round(kx + kr["arasi"] / 2.0, 3)))

    def test_kabin_kasnagi_sase_dikmesine_ortali(self):
        from cizim import sabitler as CS
        S = CS.sabitler()
        kb, k = self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        dis_g = kb["genislik"] + 2 * S["kabin_pano_yan"]
        beklenen = {round(kx - dis_g / 2.0 - S["sase_dikme"] / 2.0, 3),
                    round(kx + dis_g / 2.0 + S["sase_dikme"] / 2.0, 3)}
        merkezler = {round(el["x"] + el["g"] / 2.0, 3) for el in _dikdortgenler(self.e, "KASNAK")
                     if round(el["d"]) == round(S["kabin_kasnak_genislik"])}
        self.assertEqual(merkezler, beklenen)

    def test_kapi_kasasi_bosluğun_iki_yaninda(self):
        from cizim import sabitler as CS
        S = CS.sabitler()
        kp = self.g["kapi"]
        kasalar = [el for el in _dikdortgenler(self.e, "KAPI")
                   if round(el["g"]) == round(S["kasa_yan"])]
        self.assertEqual(len(kasalar), 2)
        yerler = sorted(round(el["x"]) for el in kasalar)
        self.assertEqual(yerler, sorted([round(kp["sol_pay"] - S["kasa_yan"]),
                                         round(kp["sol_pay"] + kp["genislik"])]))

    def test_kabin_ile_agirlik_cakismiyor(self):
        kabin = _dikdortgenler(self.e, "KABIN")[0]
        for ag in _dikdortgenler(self.e, "AGIRLIK"):
            self.assertFalse(_cakisma(kabin, ag), f"kabin ile karşı ağırlık çakışıyor: {ag}")

    def test_kapi_boslugu_on_duvarda(self):
        k, kp = self.g["kuyu"], self.g["kapi"]
        kapilar = _dikdortgenler(self.e, "KAPI")
        bosluk = kapilar[0]
        self.assertAlmostEqual(bosluk["x"], kp["sol_pay"], places=6)
        self.assertAlmostEqual(bosluk["g"], kp["genislik"], places=6)
        self.assertAlmostEqual(bosluk["y"], -k["duvar_on"], places=6)

    def test_agirlik_yeri_cizimi_degistiriyor(self):
        sol = _dikdortgenler(CGE.plan(_ornek(agirlik={"yeri": "Sol"})), "AGIRLIK")[0]
        sag = _dikdortgenler(CGE.plan(_ornek(agirlik={"yeri": "Sağ"})), "AGIRLIK")[0]
        arka = _dikdortgenler(CGE.plan(_ornek(agirlik={"yeri": "Arka"})), "AGIRLIK")[0]
        self.assertLess(sol["x"], sag["x"])
        self.assertGreater(arka["y"], sol["y"])

    def test_sinir_butun_elemanlari_kapsiyor(self):
        x1, y1, x2, y2 = CGE.sinir(self.e)
        for el in _dikdortgenler(self.e, "KUYU-DUVAR"):
            self.assertGreaterEqual(el["x"], x1)
            self.assertLessEqual(el["x"] + el["g"], x2)
            self.assertGreaterEqual(el["y"], y1)
            self.assertLessEqual(el["y"] + el["d"], y2)


class SvgCiktisi(unittest.TestCase):
    def setUp(self):
        self.e = CGE.plan(_ornek())
        self.s = CSV.yaz(self.e, CGE.sinir(self.e, 250), "KUYU PLANI", 20)

    def test_svg_gecerli_bicimde(self):
        self.assertTrue(self.s.startswith("<svg"))
        self.assertTrue(self.s.rstrip().endswith("</svg>"))
        self.assertEqual(self.s.count("<svg"), 1)

    def test_bilinen_olculer_yaziya_giriyor(self):
        for beklenen in ("2100", "1850", "DBG 1550", "900 x 2100", "KUYU PLANI"):
            self.assertIn(beklenen, self.s, beklenen)

    def test_her_katman_bir_kalem_tanimli(self):
        katmanlar = {el["katman"] for el in self.e}
        for kat in katmanlar:
            self.assertIn(kat, CSV.KALEM, kat)


class DxfCiktisi(unittest.TestCase):
    """CAD çıktısı:  AutoCAD'in açabildiği, katmanlı ve GERÇEK ölçü varlıklı."""

    def setUp(self):
        from cizim import dxf as CDX
        self.CDX = CDX
        self.g = _ornek()
        self.e = CGE.plan(self.g)
        self.d = CDX.belge(self.e, "KUYU PLANI", 20)

    def test_denetimden_temiz_geciyor(self):
        from ezdxf.audit import Auditor
        denet = Auditor(self.d)
        denet.run()
        self.assertEqual(list(denet.errors), [])

    def test_birim_milimetre(self):
        self.assertEqual(self.d.header["$INSUNITS"], 4)

    def test_kullanilan_katmanlar_tanimli(self):
        for el in self.e:
            self.assertIn(el["katman"], self.d.layers, el["katman"])

    def test_olculer_gercek_dimension_varligi(self):
        say = sum(1 for x in self.d.modelspace() if x.dxftype() == "DIMENSION")
        self.assertEqual(say, sum(1 for el in self.e if el["tip"] == "olcu"))

    def test_duvar_taramasi_hatch_olarak(self):
        say = sum(1 for x in self.d.modelspace() if x.dxftype() == "HATCH")
        self.assertEqual(say, sum(1 for el in self.e
                                  if el["tip"] in ("tarama", "tarama_tugla")))

    def test_dxf_baytlari_yazilabiliyor(self):
        b = self.CDX.yaz(self.e, "KUYU PLANI", 20)
        self.assertGreater(len(b), 10000)
        self.assertIn(b"SECTION", b)
        self.assertIn(b"KUYU-DUVAR", b)

    def test_ayni_eleman_listesi_iki_bicime_de_gidiyor(self):
        #  SVG ve DXF AYNI listeden üretilir;  ikinci bir çizici yoktur.
        svg_metni = CSV.yaz(self.e, CGE.sinir(self.e, 250), "KUYU PLANI", 20)
        self.assertIn("KUYU PLANI", svg_metni)
        self.assertGreater(len(self.e), 40)


class YerlesimRegresyonlari(unittest.TestCase):
    def test_kabin_dis_zarfi_kuyu_icinde_olmali(self):
        for degisim in ({"kaciklik_y": 600}, {"kaciklik_y": -600},
                        {"kaciklik_y": 320}, {"derinlik": 1700}):
            with self.subTest(degisim=degisim):
                self.assertTrue(any("şasesi kuyunun dışına" in h
                                    for h in CG.dogrula(_ornek(kabin=degisim))))

    def test_aciklik_siniri_ve_cakisma(self):
        # Sol şase yüzü x=430, ağırlık yarı kalınlığı=125.
        # ray_duvar=285 -> tam 20 mm açıklık; daha fazlası geçemez.
        for yer in ("Sol", "Sağ"):
            for duvar, uygun in ((284, True), (285, True), (286, False),
                                 (305, False), (315, False), (390, False)):
                g = _ornek(agirlik={"yeri": yer, "ray_duvar": duvar},
                           kabin={"kaciklik_y": 130 if yer == "Sol" else -130})
                with self.subTest(yer=yer, duvar=duvar):
                    self.assertEqual(not CG.dogrula(g), uygun)

    def test_ozel_pano_olcusu_denetim_ve_cizimde_ayni(self):
        g = _ornek(kabin={"kaciklik_y": 290})
        g["_cizim_sabitleri"] = {"kabin_pano_yan": 100}
        self.assertTrue(any("şasesi kuyunun dışına" in h for h in CG.dogrula(g)))
        kabin = _dikdortgenler(CGE.plan(g), "KABIN")[0]
        self.assertEqual(kabin["g"], 1550)

    def test_her_yerlesimde_zincirler_kapanir(self):
        for yer in CG.AGIRLIK_YERLERI:
            e = CGE.plan(_ornek(agirlik={"yeri": yer}))
            for z in CGE.zincirler(e):
                with self.subTest(yer=yer, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            if yer != "Arka":
                olcu = next(q for q in e if q["tip"] == "olcu"
                            and q["metin"].startswith("AĞIRLIK RAYI"))
                self.assertEqual(olcu["uzunluk"], 130)
                self.assertEqual(olcu["metin"], "AĞIRLIK RAYI 130")

    def test_dbgw_gercek_ray_yuzlerine_baglanir(self):
        for yer in CG.AGIRLIK_YERLERI:
            g = _ornek(agirlik={"yeri": yer})
            e = CGE.plan(g)
            q = next(q for q in e if q["tip"] == "olcu" and q["metin"].startswith("DBGW"))
            self.assertEqual(q["uzunluk"], 850)
            if yer == "Arka":
                self.assertEqual(q["yon"], "yatay")
                self.assertEqual(q["a"], (625, 1720))
                self.assertEqual(q["b"], (1475, 1720))
            else:
                self.assertEqual(q["yon"], "dusey")

    def test_dxf_yazi_hizasini_korur(self):
        from cizim import dxf
        from ezdxf.enums import TextEntityAlignment as A
        elemanlar = [CGE._yazi(100, 200, h, hiza=h) for h in ("sol", "orta", "sag")]
        d = dxf.belge(elemanlar)
        for text, beklenen in zip(d.modelspace().query("TEXT"),
                                  (A.MIDDLE_LEFT, A.MIDDLE_CENTER, A.MIDDLE_RIGHT)):
            self.assertEqual(text.get_placement()[0], beklenen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
