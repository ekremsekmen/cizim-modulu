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
from cizim import sabitler as CS_           # noqa: E402


def _ornek(**ezme):
    g = {k: (dict(v) if isinstance(v, dict) else v) for k, v in CG.ORNEK.items()}
    for bolum, d in ezme.items():
        g[bolum].update(d)
    return g


def _sag_ayna(**ezme):
    """Örneğin aynası:  ağırlık sağda, kabin ve kapı simetrik yerde."""
    g = _ornek(agirlik={"yeri": "Sağ"}, kabin={"kaciklik_y": -130},
               kapi={"sol_pay": 2100 - 730 - 900})
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
            g = _sag_ayna() if yer == "Sağ" else _ornek(agirlik={"yeri": yer})
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
        k = self.g["kuyu"]
        plakalar = [el for el in _dikdortgenler(self.e, "KONSOL")
                    if el.get("ad") == "plaka"]
        #  2 ağırlık rayı + ağırlığın OLMADIĞI yandaki kabin rayı;  öbür kabin
        #  rayı ağırlık konsollarına bağlı ara kirişte durur.
        self.assertEqual(len(plakalar), 3)
        for el in plakalar:
            duvarda = abs(el["x"]) < 1e-6 or abs(el["x"] + el["g"] - k["genislik"]) < 1e-6
            self.assertTrue(duvarda, f"konsol plakası duvara dayanmıyor: {el}")

    def test_konsol_kolu_plaka_ile_rayi_birlestiriyor(self):
        """Kabin konsolunun kolu plakaya ve rayın arkasına;  ağırlık konsolunun
        kolu plakaya ve kabin rayının ara kirişine değmeli."""
        from cizim import sabitler as CS
        S = CS.sabitler()
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        sag_ray_arkasi = round(kx + kr["arasi"] / 2.0 + kr["h"], 3)
        sol_ray_arkasi = round(kx - kr["arasi"] / 2.0 - kr["h"], 3)
        kiris = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "ara_kiris"]
        self.assertEqual(len(kiris), 1)
        self.assertAlmostEqual(kiris[0]["x"] + kiris[0]["g"], sol_ray_arkasi)
        kollar = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "kol"]
        self.assertEqual(len(kollar), 3)          # 1 kabin + 2 ağırlık
        for el in kollar:
            uclar = {round(el["x"], 3), round(el["x"] + el["g"], 3)}
            if el["x"] > kx:                      # kabin konsolu  ( sağ duvar )
                self.assertIn(sag_ray_arkasi, uclar)
                self.assertIn(round(k["genislik"] - S["konsol_kabin_en"], 3), uclar)
            else:                                 # ağırlık konsolu → ara kiriş
                self.assertIn(round(S["konsol_agirlik_en"], 3), uclar)
                self.assertIn(round(kiris[0]["x"], 3), uclar)

    def test_paten_ray_yuzunu_kavriyor(self):
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        for el in _dikdortgenler(self.e, "PATEN"):
            merkez = el["x"] + el["g"] / 2.0
            self.assertIn(round(merkez, 3),
                          (round(kx - kr["arasi"] / 2.0, 3), round(kx + kr["arasi"] / 2.0, 3)))

    def test_kabin_kasnaklari_girdideki_aralikta(self):
        from cizim import sabitler as CS
        S = CS.sabitler()
        kb, k, a = self.g["kabin"], self.g["kuyu"], self.g["aski"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        beklenen = {round(kx - a["kasnak_arasi"] / 2.0, 3), round(kx + a["kasnak_arasi"] / 2.0, 3)}
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
        # Kabin rayının arkası 343'te, ara kiriş 293 – 343;  ağırlık yarı
        # kalınlığı 80.  ray_duvar = 193 → kirişe tam 20 mm;  fazlası geçemez.
        for yer in ("Sol", "Sağ"):
            for duvar, uygun in ((192, True), (193, True), (194, False),
                                 (215, False), (285, False), (390, False)):
                g = (_sag_ayna(agirlik={"ray_duvar": duvar}) if yer == "Sağ" else
                     _ornek(agirlik={"yeri": yer, "ray_duvar": duvar}))
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
                self.assertEqual((q["a"][0], q["b"][0]), (625, 1475))
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


class ParcaTutarliligi(unittest.TestCase):
    """Parçalar kendi rayları arasında, birbirinin içinden geçmeden durur."""

    def _yerlesimler(self):
        return (("Sol", _ornek()), ("Sağ", _sag_ayna()),
                ("Arka", _ornek(agirlik={"yeri": "Arka"}, kabin={"kaciklik_y": 0},
                                kapi={"sol_pay": 600}, kuyu={"derinlik": 2100})))

    def test_agirlik_kendi_raylarinin_arasinda(self):
        for yer, g in self._yerlesimler():
            ag = g["agirlik"]
            blok = _dikdortgenler(CGE.plan(g), "AGIRLIK")[0]
            boy = blok["d"] if yer != "Arka" else blok["g"]
            with self.subTest(yer=yer):
                self.assertLess(boy, ag["ray_arasi"])

    def test_agirlik_raylardan_uzunsa_reddedilir(self):
        self.assertTrue(any("ağırlık rayları arasından" in h
                            for h in CG.dogrula(_ornek(agirlik={"genislik": 850}))))

    def test_sase_raylardan_genisse_reddedilir(self):
        self.assertTrue(any("kabin rayları arasından" in h
                            for h in CG.dogrula(_ornek(kabin_ray={"arasi": 1500}))))

    def test_kapi_kabinin_onune_duser(self):
        g = _ornek()
        kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        #  Örnekte kapı ekseni kabin ekseniyle aynı  ( ELEport:  1.180 )
        self.assertEqual(g["kapi"]["sol_pay"] + g["kapi"]["genislik"] / 2.0, kx)
        self.assertTrue(any("kabinin önüne düşmüyor" in h
                            for h in CG.dogrula(_ornek(kapi={"sol_pay": 300}))))

    def test_kabin_konsolu_agirligin_icinden_gecmez(self):
        for yer, g in self._yerlesimler():
            e = CGE.plan(g)
            blok = _dikdortgenler(e, "AGIRLIK")[0]
            for el in _dikdortgenler(e, "KONSOL"):
                with self.subTest(yer=yer, parca=el.get("ad")):
                    self.assertFalse(_cakisma(el, blok), el)

    def test_pano_agirlikla_ayni_duvarda_durmaz(self):
        for yer, g in self._yerlesimler():
            e = CGE.plan(g)
            blok = _dikdortgenler(e, "AGIRLIK")[0]
            pano = _dikdortgenler(e, "PANO")[0]
            with self.subTest(yer=yer):
                self.assertFalse(_cakisma(pano, blok))
                if yer == "Sağ":
                    self.assertEqual(pano["x"], 0)


class OlcuYazilari(unittest.TestCase):
    """Ölçü yazıları kendi ölçüsünün yanında, üst üste binmeden, çerçevede."""

    def _kutular(self, e):
        out = []
        for el in e:
            if el["tip"] == "olcu":
                y = el["yazi"]
                w, h = CGE._yazi_eni(el["metin"], y["h"]) / 2.0, y["h"] / 2.0
                if y["aci"]:
                    w, h = h, w
                out.append((el, y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h))
        return out

    def _projeler(self):
        yield "Sol", _ornek()
        yield "Sağ", _sag_ayna()
        yield "Arka", _ornek(agirlik={"yeri": "Arka"}, kabin={"kaciklik_y": 0},
                             kapi={"sol_pay": 600}, kuyu={"derinlik": 2100})
        g = _ornek()
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
        yield "Doğrudan", g

    def test_yazilar_ust_uste_binmiyor(self):
        import itertools
        for ad, g in self._projeler():
            k = self._kutular(CGE.plan(g))
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_yazi_kendi_olcusunun_yaninda(self):
        """Yazı ölçü çizgisinden en çok iki kat ( 170 mm ) uzakta;  eskiden
        sığmayan yazı başka bir sıranın üstüne itiliyordu."""
        for ad, g in self._projeler():
            for el in CGE.plan(g):
                if el["tip"] != "olcu":
                    continue
                y = el["yazi"]
                capraz = abs((y["y"] if el["yon"] == "yatay" else y["x"]) - el["kot"])
                with self.subTest(proje=ad, olcu=el["metin"]):
                    if y["aci"] == (0.0 if el["yon"] == "yatay" else 90.0):
                        self.assertLessEqual(capraz, 170 + 1e-6)

    def test_yazilar_cercevenin_icinde(self):
        for ad, g in self._projeler():
            e = CGE.plan(g)
            x1, y1, x2, y2 = CGE.sinir(e)
            for el, a, b, c, d in self._kutular(e):
                with self.subTest(proje=ad, olcu=el["metin"]):
                    self.assertTrue(x1 <= a and c <= x2 and y1 <= b and d <= y2)

    def test_aski_arasi_tek_olcu(self):
        q = [el for el in CGE.plan(_ornek()) if el["tip"] == "olcu"
             and el["metin"].startswith("ASKI ARASI")]
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["uzunluk"], _ornek()["aski"]["kasnak_arasi"])

    def test_uzatma_cizgisi_yok(self):
        e = CGE.plan(_ornek())
        s = CSV.yaz(e, CGE.sinir(e, 250), "", 20)
        self.assertNotIn('stroke-dasharray="30 20"', s)
        from cizim import dxf as CDX
        d = CDX.belge(e)
        for dim in d.modelspace().query("DIMENSION"):
            blok = d.blocks.get(dim.dxf.geometry)
            #  Uzatma çizgisi olsaydı ölçülen noktaya ( x = 0 ya da y = 0
            #  hizası ) inen çizgiler bulunurdu;  yalnız ölçü çizgisi + uçlar kalır.
            ciz = [x for x in blok if x.dxftype() == "LINE"]
            self.assertLessEqual(len(ciz), 3, dim.dxf.text)

    def test_dxf_yazisi_svg_ile_ayni_yerde(self):
        from cizim import dxf as CDX
        e = CGE.plan(_ornek())
        d = CDX.belge(e)
        olculer = [el for el in e if el["tip"] == "olcu"]
        for el, dim in zip(olculer, d.modelspace().query("DIMENSION")):
            p = dim.dxf.text_midpoint
            with self.subTest(olcu=el["metin"]):
                self.assertAlmostEqual(p.x, el["yazi"]["x"], places=3)
                self.assertAlmostEqual(p.y, el["yazi"]["y"], places=3)


#  ─────────────────────────────────────────────────────────────────────
#  KABİN ÜSTÜ PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import kabin_ustu as CKU        # noqa: E402


def _arka(kaciklik=0.0):
    """Ağırlık arkada:  kabinin iki yanı da duvara bakar, sınır denemesi kolay."""
    return _ornek(agirlik={"yeri": "Arka"}, kabin={"kaciklik_y": kaciklik},
                  kapi={"sol_pay": 600}, kuyu={"derinlik": 2100})


def _ustu_projeler():
    yield "Sol", _ornek()
    yield "Sağ", _sag_ayna()
    yield "Arka", _arka()
    g = _ornek(aski={"duzen": "Kabin üstü", "kasnak_arasi": 1000})
    yield "Kabin üstü askı", g
    g = _ornek(kabin_ustu={"siginma_tipi": "Dik duruş"})
    g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
    yield "Doğrudan · dik duruş", g


class KabinUstuSozlesme(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _ustu_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(CKU.dogrula(g), [])

    def test_siginma_tipi_zorunlu(self):
        self.assertTrue(CKU.dogrula(_ornek(kabin_ustu={"siginma_tipi": "Yatarak"})))

    def test_ray_ekseni_kabinin_icinden_gecmeli(self):
        self.assertTrue(any("kabinin derinliği içinden" in h
                            for h in CG.dogrula(_ornek(kabin={"derinlik": 800}))))

    def test_halat_parcanin_icinden_gecemez(self):
        #  1.470'lik kasnak aralığında sol halat kabin rayının ara kirişinden geçer
        self.assertTrue(any("Halat" in h for h in CKU.dogrula(_ornek(aski={"kasnak_arasi": 1470}))))

    def test_kabin_ustu_kasnagi_korkulugu_kesemez(self):
        self.assertTrue(any("korkuluğun yolunu" in h
                            for h in CKU.dogrula(_ornek(aski={"duzen": "Kabin üstü"}))))

    def test_siginmaya_yer_yoksa_reddedilir(self):
        #  Tavan 540 × 733;  korkuluklar içeri alınınca 450 genişlik kalır —
        #  500 × 700 hiçbir yönde sığmaz
        g = _arka()
        g["kabin"].update({"genislik": 450, "derinlik": 700})
        g["kabin_ray"].update({"arasi": 650, "kapi_arasi": 500})
        g["kapi"].update({"genislik": 400, "sol_pay": 850})
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 200}
        self.assertEqual(CG.dogrula(g), [])
        self.assertTrue(any("sığınma alanına" in h for h in CKU.dogrula(g)), CKU.dogrula(g))


class KabinUstuKorkuluk(unittest.TestCase):
    """TS EN 81-20 m.5.4.7.2 b ve m.5.4.7.4 — sınırların iki yanı."""

    def test_300_mm_asilinca_korkuluk(self):
        #  Arka yerleşimde sol boşluk = kabin ekseni − 720
        for kac, gerekli in ((-30, False), (-29, True)):
            k = CKU.yerlesim(_arka(kac))["kenarlar"]["Sol"]
            with self.subTest(bosluk=k["bos"]):
                self.assertEqual(k["gerekli"], gerekli)

    def test_yukseklik_500_mm_sinirinda_degisir(self):
        #  Küpeşte raydan 100 mm uzak durmak için 45 içeri alınır;
        #  boşluk 455 + 45 = 500 → 0,70 m,  456 + 45 = 501 → 1,10 m
        for kac, h in ((125, 700), (126, 1100)):
            k = CKU.yerlesim(_arka(kac))["kenarlar"]["Sol"]
            with self.subTest(bosluk=k["bos"]):
                self.assertEqual(k["iceri"], 45)
                self.assertEqual(k["yukseklik"], h)

    def test_kupeste_parcalardan_100_kenardan_en_cok_150(self):
        for ad, g in _ustu_projeler():
            Y = CKU.yerlesim(g)
            for yan, k in Y["kenarlar"].items():
                if not k["gerekli"]:
                    continue
                with self.subTest(proje=ad, yan=yan):
                    self.assertLessEqual(k["iceri"], CKU.KORKULUK_KENAR_AZAMI)
                    if k["parca"] is not None:
                        self.assertGreaterEqual(k["parca"] + k["iceri"],
                                                CKU.KORKULUK_PARCA_ASGARI - 1e-9)

    def test_150_mm_yetmezse_reddedilir(self):
        eski = CKU.KORKULUK_PARCA_ASGARI
        try:
            CKU.KORKULUK_PARCA_ASGARI = 300.0
            self.assertTrue(any("m.5.4.7.4 c" in h for h in CKU.dogrula(_ornek())))
        finally:
            CKU.KORKULUK_PARCA_ASGARI = eski

    def test_korkuluk_cizgisi_yalniz_gerekli_kenarda(self):
        for ad, g in _ustu_projeler():
            Y = CKU.yerlesim(g)
            cizgiler = [el for el in CKU.ciz(g) if el.get("ad") == "korkuluk"]
            with self.subTest(proje=ad):
                self.assertEqual(len(cizgiler), sum(k["gerekli"] for k in Y["kenarlar"].values()))


class KabinUstuYerlesim(unittest.TestCase):
    def test_siginma_cizelge_3_olculerinde_ve_icerde(self):
        for ad, g in _ustu_projeler():
            Y = CKU.yerlesim(g)
            s, ic = Y["siginma"], Y["ic"]
            with self.subTest(proje=ad):
                self.assertEqual(sorted((s[2] - s[0], s[3] - s[1])),
                                 sorted(CKU.SIGINMA[g["kabin_ustu"]["siginma_tipi"]]))
                self.assertTrue(ic[0] <= s[0] and s[2] <= ic[2] and ic[1] <= s[1] and s[3] <= ic[3])
                for p in Y["engeller"]:
                    self.assertFalse(CKU._ortusur(s, p), p)

    def test_kuyu_parcalari_plandan_eksiksiz_gelir(self):
        """Raylar, konsollar ve karşı ağırlık kuyu planındakinin aynısı."""
        for ad, g in _ustu_projeler():
            plan, ustu = CGE.plan(g), CKU.ciz(g)
            for kat in ("RAY", "KONSOL", "AGIRLIK", "CIVATA"):
                with self.subTest(proje=ad, katman=kat):
                    self.assertEqual(
                        sorted(_kutu for _kutu in (tuple(round(el[a], 3) for a in ("x", "y", "g", "d"))
                                                   for el in _dikdortgenler(plan, kat))),
                        sorted(tuple(round(el[a], 3) for a in ("x", "y", "g", "d"))
                               for el in _dikdortgenler(ustu, kat)))

    def test_on_duvar_dolu_kapi_gorunmez(self):
        e = CKU.ciz(_ornek())
        self.assertFalse([el for el in e if el["katman"] == "KAPI" and el["tip"] == "dikdortgen"
                          and el["y"] < 0])

    def test_askiya_gore_tavan(self):
        e = CKU.ciz(_ornek())
        self.assertFalse([el for el in e if el.get("ad") == "kabin_kasnak"])
        self.assertEqual(len([el for el in e if el.get("ad") == "halat"]), 2)
        e = CKU.ciz(_ornek(aski={"duzen": "Kabin üstü", "kasnak_arasi": 1000}))
        self.assertEqual(len([el for el in e if el.get("ad") == "kabin_kasnak"]), 2)
        self.assertFalse([el for el in e if el.get("ad") == "halat"])

    def test_operator_tavanin_kapi_kenarinda(self):
        from cizim import sabitler as CS
        S = CS.sabitler()
        for ad, g in _ustu_projeler():
            Y = CKU.yerlesim(g)
            op, t = Y["operator"], Y["tavan"]
            with self.subTest(proje=ad):
                self.assertEqual(op[1], t[1])
                self.assertEqual(op[3] - op[1], S["kabin_kapisi_kutu_boy"])
                self.assertTrue(t[0] <= op[0] and op[2] <= t[2])

    def test_olcu_zincirleri_ve_yazilar(self):
        import itertools
        for ad, g in _ustu_projeler():
            e = CKU.ciz(g)
            for z in CGE.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_dxf_temiz(self):
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        d = CDX.belge(CKU.ciz(_ornek()), "KABİN ÜSTÜ", 20)
        a = Auditor(d)
        a.run()
        self.assertEqual(list(a.errors), [])
        self.assertIn("KORKULUK", d.layers)
        self.assertIn("SIGINMA", d.layers)


#  ─────────────────────────────────────────────────────────────────────
#  KUYU DİBİ PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import kuyu_dibi as CKD         # noqa: E402


def _dip_projeler():
    yield "Sol", _ornek()
    g = _sag_ayna()
    g["kuyu_dibi"] = dict(g["kuyu_dibi"], regulator_yan="Sol")
    yield "Sağ", g
    yield "Arka", _arka()
    yield "İki tampon · yatarak", _ornek(kuyu_dibi={
        "kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600, "agirlik_tampon_adedi": 2,
        "agirlik_tampon_arasi": 400, "siginma_tipi": "Yatarak"})
    yield "Derin kuyu · dik duruş", _ornek(kuyu_dibi={"derinlik": 2600, "siginma_tipi": "Dik duruş"})


class KuyuDibiSozlesme(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _dip_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(CKD.dogrula(g), [])

    def test_kabin_agirlik_arasi_50_mm(self):
        #  TS EN 81-20 m.5.2.5.5.1 h — arka ağırlığın ön yüzü kabinin arkasına
        #  ray_duvar = 157 → tam 50 mm,  160 → 47 mm
        for duvar, uygun in ((157, True), (160, False)):
            g = _ornek(agirlik={"yeri": "Arka", "ray_duvar": duvar})
            with self.subTest(ray_duvar=duvar):
                self.assertEqual(not any("m.5.2.5.5.1 h" in h for h in CG.dogrula(g)), uygun)

    def test_hatali_girdiler(self):
        for ezme, parca in (({"siginma_tipi": "Oturarak"}, "siginma_tipi"),
                            ({"kabin_tampon_adedi": 3}, "kabin_tampon_adedi"),
                            ({"kabin_tampon_adedi": 2}, "kabin_tampon_arasi"),
                            ({"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 100}, "üst üste"),
                            ({"agirlik_tampon_adedi": 2, "agirlik_tampon_arasi": 900},
                             "karşı ağırlığın altına"),
                            ({"regulator_yan": "Orta"}, "regulator_yan")):
            with self.subTest(ezme=ezme):
                self.assertTrue(any(parca in h for h in CKD.dogrula(_ornek(kuyu_dibi=ezme))),
                                CKD.dogrula(_ornek(kuyu_dibi=ezme)))


class KuyuDibiYerlesim(unittest.TestCase):
    def test_tamponlar_eksenlerde(self):
        g = _ornek()
        Y = CKD.yerlesim(g)
        kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        ry = g["kabin_ray"]["kapi_arasi"]
        self.assertEqual(CKD._merkez(Y["kabin_tamponlari"][0]), (kx, ry))
        self.assertEqual(CKD._merkez(Y["agirlik_tamponlari"][0]), CKD._merkez(Y["blok"]))
        Y = CKD.yerlesim(_ornek(kuyu_dibi={"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600}))
        self.assertEqual([CKD._merkez(t) for t in Y["kabin_tamponlari"]],
                         [(kx - 300, ry), (kx + 300, ry)])

    def test_perde_agirligin_boyunca(self):
        """m.5.2.5.5.1 d:  perde en az ağırlığın genişliği kadar."""
        for ad, g in _dip_projeler():
            Y = CKD.yerlesim(g)
            p, b = Y["perde"], Y["blok"]
            with self.subTest(proje=ad):
                if p[0] == p[2]:
                    self.assertLessEqual(p[1], b[1]); self.assertGreaterEqual(p[3], b[3])
                    self.assertTrue(b[2] < p[0] or p[0] < b[0])
                else:
                    self.assertLessEqual(p[0], b[0]); self.assertGreaterEqual(p[2], b[2])
                    self.assertLess(p[1], b[1])

    def test_siginma_cizelge_4_kabinin_altinda(self):
        for ad, g in _dip_projeler():
            Y = CKD.yerlesim(g)
            s, kb = Y["siginma"], Y["kabin"]
            with self.subTest(proje=ad):
                self.assertEqual(sorted((s[2] - s[0], s[3] - s[1])),
                                 sorted(CKD.SIGINMA[g["kuyu_dibi"]["siginma_tipi"]]))
                self.assertTrue(kb[0] <= s[0] and s[2] <= kb[2] and kb[1] <= s[1] and s[3] <= kb[3])
                engel = (Y["kabin_tamponlari"] + Y["agirlik_tamponlari"] + [Y["gergi"]]
                         + Y["kabin_raylari"] + Y["agirlik_raylari"]
                         + ([Y["merdiven"]] if Y["merdiven"] else []))
                for p in engel:
                    self.assertFalse(CKD._ortusur(s, p), p)

    def test_merdiven_ek_f(self):
        for ad, g in _dip_projeler():
            Y = CKD.yerlesim(g)
            m = Y["merdiven"]
            with self.subTest(proje=ad):
                if g["kuyu_dibi"]["derinlik"] > CKD.MERDIVEN_AZAMI_DERINLIK:
                    self.assertIsNone(m)
                    continue
                G, kp = g["kuyu"]["genislik"], g["kapi"]
                self.assertTrue(m[0] == 0 or m[2] == G)             # yan duvara yaslı
                kenar = kp["sol_pay"] if m[0] == 0 else kp["sol_pay"] + kp["genislik"]
                dx = max(0.0, m[0] - kenar, kenar - m[2])
                self.assertLessEqual((dx ** 2 + m[1] ** 2) ** 0.5, CKD.MERDIVEN_KAPI_AZAMI)

    def test_merdiven_kapidan_800_ustunde_reddedilir(self):
        #  3 m genişlikte kuyu, kapı kabin ekseninde:  sağ duvara 820, sola 1.080
        g = _ornek(kuyu={"genislik": 3000}, kapi={"sol_pay": 1180})
        self.assertEqual(CG.dogrula(g), [])
        self.assertTrue(any("Ek F.5 b" in h for h in CKD.dogrula(g)), CKD.dogrula(g))

    def test_standart_tablolari(self):
        """Ölçüler standardın kendi sayılarıyla sabitlenir ( tablo kendisiyle
        kıyaslanırsa yanlış bir sayı testten geçerdi )."""
        self.assertEqual(CKD.SIGINMA, {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0),
                                       "Yatarak": (700.0, 1000.0)})           # Çizelge 4
        self.assertEqual(CKU.SIGINMA, {"Dik duruş": (400.0, 500.0),
                                       "Çömelme": (500.0, 700.0)})            # Çizelge 3
        self.assertEqual((CKD.MERDIVEN_AZAMI_DERINLIK, CKD.MERDIVEN_KAPI_AZAMI), (2500.0, 800.0))
        self.assertEqual((CKU.KORKULUK_BOSLUK, CKU.KORKULUK_KENAR_AZAMI, CKU.KORKULUK_PARCA_ASGARI,
                          CKU.KORKULUK_YUKSEKLIK_SINIRI, CKU.KORKULUK_ALCAK, CKU.KORKULUK_YUKSEK),
                         (300.0, 150.0, 100.0, 500.0, 700.0, 1100.0))
        self.assertEqual((CG.KAPI_ARASI_AZAMI, CG.ESIK_ARASI_AZAMI, CG.KABIN_AGIRLIK_ACIKLIGI),
                         (150.0, 35.0, 50.0))

    def test_merdiven_2500_sinirinda(self):
        for derinlik, var in ((2500, True), (2501, False)):
            Y = CKD.yerlesim(_ornek(kuyu_dibi={"derinlik": derinlik}))
            with self.subTest(derinlik=derinlik):
                self.assertEqual(Y["merdiven"] is not None, var)

    def test_yuk_noktalari_hesap_paftasi_adlariyla(self):
        e = CKD.ciz(_ornek(kuyu_dibi={"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600}))
        adlar = [el["metin"] for el in e if el.get("ad") == "yuk"]
        self.assertEqual(sorted(adlar), sorted(["FKR", "FKR", "FAR", "FAR", "Fkt", "Fkt", "Fat"]))

    def test_olcu_zincirleri_ve_yazilar(self):
        import itertools
        for ad, g in _dip_projeler():
            e = CKD.ciz(g)
            for z in CGE.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_dxf_temiz(self):
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        d = CDX.belge(CKD.ciz(_ornek()), "KUYU DİBİ", 20)
        a = Auditor(d)
        a.run()
        self.assertEqual(list(a.errors), [])
        for kat in ("TAMPON", "PERDE", "MERDIVEN", "GIZLI"):
            self.assertIn(kat, d.layers)

    def test_arka_agirlik_raylari_konsollu(self):
        e = CGE.plan(_arka())
        plakalar = [el for el in _dikdortgenler(e, "KONSOL") if el.get("ad") == "plaka"]
        self.assertEqual(len(plakalar), 4)
        D = _arka()["kuyu"]["derinlik"]
        self.assertEqual(sum(1 for el in plakalar if abs(el["y"] + el["d"] - D) < 1e-6), 2)


#  ─────────────────────────────────────────────────────────────────────
#  KUYU ÜSTÜ PLANI  ( makine dairesiz )
#  ─────────────────────────────────────────────────────────────────────
from cizim import kuyu_ustu as CKT         # noqa: E402


def _ust_projeler():
    yield "Sol", _ornek()
    g = _sag_ayna()
    g["kuyu_dibi"] = dict(g["kuyu_dibi"], regulator_yan="Sol")
    g["kuyu_ustu"] = dict(g["kuyu_ustu"], acil_pano_yan="Sağ")
    yield "Sağ", g
    yield "Kasnak 200 ( sapmalı )", _ornek(makine={"tahrik_kasnak_capi": 200})


class KuyuUstu(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _ust_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(CKT.dogrula(g), [])

    def test_elepport_olculeriyle_birebir(self):
        """ELEport MRL paftasının vektör ölçüleri ( mm, kuyunun sol-ön iç köşesinden )."""
        Y = CKT.yerlesim(_ornek())
        self.assertEqual((Y["kasnak"][0], Y["kasnak"][2]), (130, 370))
        self.assertEqual((Y["govde"][0], Y["govde"][2]), (101, 399))
        self.assertEqual((Y["agirlik_baglanti"][0], Y["agirlik_baglanti"][2]), (118, 382))
        self.assertEqual((Y["kabin_baglanti"][0], Y["kabin_baglanti"][2]), (1890, 2017))
        self.assertEqual(Y["sapma"], (0, 0))

    def test_halatlar_duseye_iner(self):
        for ad, g in _ust_projeler():
            Y = CKT.yerlesim(g)
            xl, xr = Y["halatlar"][0][0], Y["halatlar"][1][0]
            ks = Y["kasnak"]
            with self.subTest(proje=ad):
                #  tahrik kasnağının bir teğeti kabinin yakın halatında
                self.assertTrue(abs(ks[2] - xl) < 1e-9 or abs(ks[0] - xr) < 1e-9)
                self.assertAlmostEqual(ks[2] - ks[0], g["makine"]["tahrik_kasnak_capi"])
                sapma = [el for el in CKT.ciz(g) if el["tip"] == "olcu"
                         and el["metin"].startswith("HALAT SAPMASI")]
                self.assertEqual(bool(sapma), any(abs(v) > 0.5 for v in Y["sapma"]))
        self.assertEqual(CKT.yerlesim(_ornek(makine={"tahrik_kasnak_capi": 200}))["sapma"],
                         (40, 0))

    def test_regulator_gergi_kasnaginin_ustunde(self):
        for ad, g in _ust_projeler():
            ust, dip = CKT.yerlesim(g)["reg_kasnak"], CKD.yerlesim(g)["gergi"]
            with self.subTest(proje=ad):
                self.assertAlmostEqual((ust[0] + ust[2]) / 2.0, (dip[0] + dip[2]) / 2.0)
                self.assertAlmostEqual((ust[1] + ust[3]) / 2.0, (dip[1] + dip[3]) / 2.0)

    def test_acil_pano_ve_calisma_alani(self):
        """m.5.2.6.6.4 → m.5.2.6.3.2.1 a:  0,70 m derin, en az 0,50 m ya da pano eni."""
        for en, beklenen in ((400, 500), (600, 600)):
            g = _ornek()
            g["_cizim_sabitleri"] = {"acil_pano_en": en}
            Y = CKT.yerlesim(g)
            p, c = Y["pano"], Y["calisma"]
            with self.subTest(pano_eni=en):
                self.assertLessEqual(p[3], -g["kuyu"]["duvar_on"])       # kuyunun dışında
                self.assertEqual(c[3] - c[1], 700)
                self.assertEqual(c[2] - c[0], beklenen)
                self.assertEqual(c[3], p[1])

    def test_desteklenmeyen_duzenler_reddedilir(self):
        self.assertTrue(CKT.dogrula(_ornek(agirlik={"yeri": "Arka"})))
        self.assertTrue(CKT.dogrula(_ornek(aski={"duzen": "Kabin üstü"})))
        self.assertTrue(CKT.dogrula(_ornek(kuyu_ustu={"acil_pano_yan": "Arka"})))

    def test_parcalar_ust_uste_binmez(self):
        #  Regülatör kabin halat bağlantısının üstüne kaydırılınca reddedilir
        h = CKT.dogrula(_ornek(kuyu_dibi={"regulator_kaciklik": -250}))
        self.assertTrue(any("üst üste" in x for x in h), h)

    def test_olcu_zincirleri_yazilar_dxf(self):
        import itertools
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        for ad, g in _ust_projeler():
            e = CKT.ciz(g)
            for z in CGE.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])
            d = CDX.belge(e, "KUYU ÜSTÜ", 20)
            a = Auditor(d)
            a.run()
            self.assertEqual(list(a.errors), [])

    def test_calisma_alani_standart_sayilari(self):
        self.assertEqual((CKT.CALISMA_DERINLIK, CKT.CALISMA_EN_ASGARI), (700.0, 500.0))


#  ─────────────────────────────────────────────────────────────────────
#  MAKİNE DAİRESİ PLANI  ve  DÖŞEME HALAT DELİK PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import makine_dairesi as CMD    # noqa: E402


def _md_projeler():
    yield "Sol", _ornek()
    g = _sag_ayna()
    g["kuyu_dibi"] = dict(g["kuyu_dibi"], regulator_yan="Sol")
    g["makine_dairesi"] = dict(g["makine_dairesi"], pano_duvar="Sol", kapi_konum=1500)
    yield "Sağ", g
    yield "Pano ön duvarda", _ornek(makine_dairesi={"pano_duvar": "Ön"})


class MakineDairesi(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _md_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(CMD.dogrula(g), [])

    def test_makine_ve_halatlar_kuyu_ustuyle_ayni(self):
        """Makine daireli ve dairesiz projede halatlar aynı noktalardan iner."""
        g = _ornek()
        M, K = CMD.yerlesim(g)["M"], CKT.yerlesim(g)
        for anahtar in ("kasnak", "govde", "halatlar", "ag_dusus", "ag_teget2", "reg_kasnak"):
            self.assertEqual(M[anahtar], K[anahtar], anahtar)

    def test_delikler_halat_demetine_gore(self):
        g = _ornek()
        Y = CMD.yerlesim(g)
        a, p = g["aski"], CS_.sabitler()["halat_delik_payi"]
        demet = (a["halat_adedi"] - 1) * 1.6 * a["halat_capi"] + a["halat_capi"]
        self.assertAlmostEqual(Y["demet"], demet)
        d = dict(Y["delikler"][:4])
        boy, en = demet + 2 * p, a["halat_capi"] + 2 * p
        for ad in ("KABİN", "AĞIRLIK", "KABİN BAĞLANTISI"):          # kasnak ekseni ( y ) boyunca
            self.assertAlmostEqual(d[ad][2] - d[ad][0], en)
            self.assertAlmostEqual(d[ad][3] - d[ad][1], boy)
        k = d["AĞIRLIK BAĞLANTISI"]                                   # ağırlık kasnağı ekseni ( x )
        self.assertAlmostEqual(k[2] - k[0], boy)
        self.assertAlmostEqual(k[3] - k[1], en)
        #  Delikler halatların tam üstünde
        M = Y["M"]
        merkez = lambda q: ((q[0] + q[2]) / 2.0, (q[1] + q[3]) / 2.0)
        self.assertEqual(merkez(d["KABİN"]), (M["yakin"], M["halatlar"][0][1]))
        self.assertEqual(merkez(d["AĞIRLIK BAĞLANTISI"]), M["ag_teget2"])

    def test_delik_kuyunun_disina_dusmez(self):
        h = CMD.dogrula(_ornek(kuyu_dibi={"regulator_kasnak_capi": 1600}))
        self.assertTrue(any("kuyunun dışına" in x for x in h), h)

    def test_kapi_600_sinirinda(self):
        for en, uygun in ((600, True), (599, False)):
            h = CMD.dogrula(_ornek(makine_dairesi={"kapi_genislik": en}))
            with self.subTest(kapi=en):
                self.assertEqual(not any("m.5.2.3.2 a" in x for x in h), uygun)

    def test_pano_calisma_alani_ve_bakim_alani(self):
        for ad, g in _md_projeler():
            Y = CMD.yerlesim(g)
            p, c, b, oda = Y["pano"], Y["calisma"], Y["bakim"], Y["oda"]
            with self.subTest(proje=ad):
                pe = CS_.sabitler()["kumanda_pano_en"]
                olcu = sorted((c[2] - c[0], c[3] - c[1]))
                self.assertEqual(olcu, sorted((700.0, max(500.0, pe))))
                self.assertEqual(sorted((b[2] - b[0], b[3] - b[1])), [500.0, 600.0])
                engel = [q for _, q in Y["delikler"]] + [Y["makine"], Y["kapi_onu"]]
                for alan in (p, c, b):
                    self.assertTrue(CMD._icinde(alan, oda))
                    for q in engel:
                        self.assertFalse(CKT._ortusur(alan, q), (alan, q))
                #  bakım alanı makineye bitişik
                m = Y["makine"]
                self.assertTrue(b[0] == m[2] or b[2] == m[0] or b[1] == m[3] or b[3] == m[1])

    def test_kucuk_odada_reddedilir(self):
        h = CMD.dogrula(_ornek(makine_dairesi={"derinlik": 2100}))
        self.assertTrue(any("m.5.2.6.3.2.1" in x for x in h), h)
        h = CMD.dogrula(_ornek(makine_dairesi={"x": 600}))
        self.assertTrue(any("dışına taşıyor" in x for x in h), h)

    def test_standart_sayilari(self):
        self.assertEqual((CMD.KAPI_ASGARI, CMD.BAKIM_ALANI, CMD.CALISMA_DERINLIK,
                          CMD.CALISMA_EN_ASGARI), (600.0, (500.0, 600.0), 700.0, 500.0))

    def test_olcu_zincirleri_yazilar_dxf(self):
        import itertools
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        for ad, g in _md_projeler():
            for ciz in (CMD.ciz, CMD.delik_plani):
                e = ciz(g)
                for z in CGE.zincirler(e):
                    with self.subTest(proje=ad, cizim=ciz.__name__, zincir=z):
                        self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                k = OlcuYazilari._kutular(None, e)
                for a, b in itertools.combinations(k, 2):
                    with self.subTest(proje=ad, cizim=ciz.__name__, a=a[0]["metin"], b=b[0]["metin"]):
                        self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])
                d = CDX.belge(e, "MAKİNE DAİRESİ", 20)
                au = Auditor(d)
                au.run()
                self.assertEqual(list(au.errors), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
