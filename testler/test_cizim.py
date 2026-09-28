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
import math
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
            g = {"Sağ": _sag_ayna, "Arka": _arka}.get(yer, lambda: _ornek(agirlik={"yeri": yer}))()
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

    def test_yazi_boyu_svg_ile_ayni(self):
        """DXF'te TEXT / ölçü yazısı yüksekliği BÜYÜK HARF yüksekliğidir, SVG'de
        em:  Arial'de büyük harf 0,716 em.  Çarpılmazsa DXF yazısı 1,4 kat büyük
        çıkıp yerleşimin ayırdığı yere sığmıyordu."""
        self.assertEqual(self.CDX.BUYUK_HARF, 0.716)
        yazilar = sorted(x["yukseklik"] for x in self.e if x["tip"] == "yazi")
        dxf = sorted(t.dxf.height for t in self.d.modelspace().query("TEXT"))
        self.assertEqual(len(dxf), len(yazilar) + 1)              # + belge başlığı
        for h in yazilar:
            self.assertTrue(any(abs(v - h * 0.716) < 1e-6 for v in dxf), h)
        olcu = sorted(round(x["yazi"]["h"] * 0.716, 6) for x in self.e if x["tip"] == "olcu")
        boy = sorted(round(dim.override().get("dimtxt"), 6)
                     for dim in self.d.modelspace().query("DIMENSION"))
        self.assertEqual(boy, olcu)

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
        #  TS EN 81-20 m.5.2.5.5.1 h — arka ağırlığın ön yüzü kabinin arkasına.
        #  Kabinin arkası 270 + 1.400 + 33 = 1.703;  kuyu 2.000'de ağırlığın ön
        #  yüzü 2.000 − ray_duvar − 80:  ray_duvar = 167 → tam 50 mm,  170 → 47 mm
        for duvar, uygun in ((167, True), (170, False)):
            g = _ornek(agirlik={"yeri": "Arka", "ray_duvar": duvar}, kuyu={"derinlik": 2000})
            with self.subTest(ray_duvar=duvar):
                self.assertEqual(not any("m.5.2.5.5.1 h" in h for h in CG.dogrula(g)), uygun)

    def test_hatali_girdiler(self):
        for ezme, parca in (({"siginma_tipi": "Oturarak"}, "siginma_tipi"),
                            ({"kabin_tampon_adedi": 3}, "kabin_tampon_adedi"),
                            ({"kabin_tampon_adedi": 2}, "kabin_tampon_arasi"),
                            ({"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 100}, "üst üste"),
                            ({"agirlik_tampon_adedi": 2, "agirlik_tampon_arasi": 900},
                             "karşı ağırlığın altına"),
                            ({"regulator_yan": "Orta"}, "regulator_yan"),
                            ({"kuvvetler": {"FKR": 1, "FAR": 1, "Fkt": 1}}, "kuyu_dibi.kuvvetler"),
                            ({"kuvvetler": {"FKR": 1, "FAR": 1, "Fkt": 1, "Fat": 1}},
                             "kuyu_dibi.kuvvetler"),
                            ({"kuvvetler": dict.fromkeys(CKD.KUVVETLER, 1) | {"Fat": 0}},
                             "kuvvetler.Fat"),
                            ({"kuvvetler": dict.fromkeys(CKD.KUVVETLER, 1) | {"FKR": "22 kN"}},
                             "kuvvetler.FKR"),
                            ({"kuvvetler": dict.fromkeys(CKD.KUVVETLER, 1) | {"Fx_kabin": -5}},
                             "kuvvetler.Fx_kabin")):
            with self.subTest(ezme=ezme):
                self.assertTrue(any(parca in h for h in CKD.dogrula(_ornek(kuyu_dibi=ezme))),
                                CKD.dogrula(_ornek(kuyu_dibi=ezme)))


class KuyuDibiYerlesim(unittest.TestCase):
    KV = {"FKR": 30683.19, "FAR": 11545.12, "Fkt": 69810.08, "Fat": 54114.08,
          "Fx_kabin": 1543.39, "Fy_kabin": 802.64, "Fx_agirlik": 86.18, "Fy_agirlik": 457.84}

    def _tablo(self, e):
        return [x for x in e if x.get("ad") == "kuvvet_tablosu"]

    def test_kuvvet_tablosu(self):
        """Kuyu tabanı:  hesabın 9. bölümü, hesap paftasındaki adlarla;  iki
        tamponda her birine düşen de ( m.5.2.1.8.5 / 6 ).  Ray konsolu:  7. ve
        8. bölümlerin en büyük Fx / Fy'si ( ELEport "Building Forces" gibi )."""
        self.assertEqual(CKD.KUVVETLER, ("FKR", "FAR", "Fkt", "Fat", "Fx_kabin", "Fy_kabin",
                                         "Fx_agirlik", "Fy_agirlik"))
        self.assertEqual(self._tablo(CKD.ciz(_ornek())), [])      # girilmemiş:  tablo yok
        e = CKD.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV}))
        self.assertEqual([x["metin"] for x in self._tablo(e)],
                         ["RAY KONSOLUNA YATAY YÜKLER", "( yük durumlarının en büyüğü )",
                          "Kabin rayı:  Fx = 1,54 kN  ·  Fy = 0,80 kN",
                          "Ağırlık rayı:  Fx = 0,09 kN  ·  Fy = 0,46 kN"])
        #  Kuyu tabanı yükleri noktalarında, kN:  bir rayın / tamponun altına
        self.assertEqual(sorted(x["metin"] for x in e if x.get("ad") == "yuk"),
                         sorted(["FKR = 30,68 kN"] * 2 + ["FAR = 11,55 kN"] * 2 +
                                ["Fkt = 69,81 kN", "Fat = 54,11 kN"]))
        e = CKD.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV, "kabin_tampon_adedi": 2,
                                      "kabin_tampon_arasi": 600, "agirlik_tampon_adedi": 2,
                                      "agirlik_tampon_arasi": 400}))
        self.assertEqual(sorted(x["metin"] for x in e if x.get("ad") == "yuk" and x["metin"][1] != "K"
                                and x["metin"][1] != "A"),
                         sorted(["Fkt1 = 34,91 kN"] * 2 + ["Fat1 = 27,06 kN"] * 2))
        #  Ray kuvveti sıfır olabilir ( yük ekseni ray ekseninde ), kuyu tabanı yükü olamaz
        self.assertEqual(CKD.dogrula(_ornek(kuyu_dibi={"kuvvetler": dict(self.KV, Fy_agirlik=0)})), [])
        self.assertTrue(CKD.dogrula(_ornek(kuyu_dibi={"kuvvetler": dict(self.KV, FAR=0)})))

    def test_yuk_oklari_ve_kutulari(self):
        """Her yük noktasına bir ok ve çerçeveli kutu ( LiftDesigner "View of Pit"
        gibi ):  ok noktada biter, kutunun kenarından çıkar;  kutu kuyunun
        içinde, hiçbir parçaya, yazıya, ölçüye ve başka kutuya binmez;  ok başka
        bir kutuyu, yazıyı ya da oku kesmez."""
        projeler = list(_dip_projeler()) + [
            ("yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            ("iki tampon · çömelme", _ornek(kuyu_dibi={
                "kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600,
                "agirlik_tampon_adedi": 2, "agirlik_tampon_arasi": 400}))]
        for ad, g in projeler:
            for kv in (None, self.KV):
                if kv:
                    g["kuyu_dibi"]["kuvvetler"] = dict(kv)
                e = CKD.ciz(g)
                Y = CKD.yerlesim(g)
                G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
                noktalar = sorted(CKD._merkez(k) for k in Y["kabin_tamponlari"] + Y["agirlik_tamponlari"]
                                  + Y["kabin_raylari"] + Y["agirlik_raylari"])
                kutu = [CGE.sinir([x]) for x in e if x.get("ad") == "yuk_kutusu"]
                oklar = [x for x in e if x.get("ad") == "yuk_oku"]
                yazi = [x for x in e if x.get("ad") == "yuk"]
                geri = [x for x in e if x.get("ad") not in ("yuk_kutusu", "yuk_oku", "yuk")]
                #  Tek tamponda sığınma alanının yüzeyine de binmez;  iki tamponda
                #  ( 8 nokta ) yüzeyine binebilir, yazısına binmez
                iki = g["kuyu_dibi"]["kabin_tampon_adedi"] + g["kuyu_dibi"]["agirlik_tampon_adedi"] > 2
                kutular, yazilar = CKD._engeller(geri, siginma=not iki)
                with self.subTest(proje=ad, degerli=bool(kv)):
                    self.assertEqual(len(kutu), len(noktalar))
                    self.assertEqual(sorted((o["x2"], o["y2"]) for o in oklar), noktalar)
                    for o in oklar:
                        #  ok kutunun kenarından çıkar
                        self.assertTrue(any(abs(o["x1"] - k[0]) < 1e-6 or abs(o["x1"] - k[2]) < 1e-6
                                            or abs(o["y1"] - k[1]) < 1e-6 or abs(o["y1"] - k[3]) < 1e-6
                                            for k in kutu if k[0] - 1e-6 <= o["x1"] <= k[2] + 1e-6
                                            and k[1] - 1e-6 <= o["y1"] <= k[3] + 1e-6))
                    for k, y_ in zip(kutu, yazi):
                        self.assertTrue(0 < k[0] and k[2] < G and 0 < k[1] and k[3] < D)
                        self.assertLessEqual(CGE._yazi_eni(y_["metin"], y_["yukseklik"]), k[2] - k[0])
                    for i, k in enumerate(kutu):
                        engel = kutular + yazilar + kutu[:i] + kutu[i + 1:]
                        self.assertFalse([b for b in engel if CKD._ortusur(k, b)], k)
                    for i, o in enumerate(oklar):
                        p, q = (o["x2"], o["y2"]), (o["x1"], o["y1"])
                        self.assertFalse([b for b in yazilar if CKD._kesisir(p, q, b)])
                        for j, o2 in enumerate(oklar):
                            if i != j:
                                self.assertFalse(CKD._cakisir(p, q, (o2["x2"], o2["y2"]), (o2["x1"], o2["y1"])))
                        for k in kutu:
                            if not (k[0] - 1e-6 <= q[0] <= k[2] + 1e-6 and k[1] - 1e-6 <= q[1] <= k[3] + 1e-6):
                                self.assertFalse(CKD._kesisir(p, q, k))

    def test_kuvvet_semasi_yonleri(self):
        """Ray şemasında Fy ağzın doğrultusunda ( ağzın ucuna ), Fx ağza yandan
        ( EN 81-50 m.5.10.5 )."""
        e = CKD.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV}))
        sema = [x for x in e if x.get("ad") == "kuvvet_semasi"]
        taban, agiz = [x for x in sema if x["tip"] == "dikdortgen"]
        oklar = {y["metin"]: y for y in sema if y["tip"] == "yazi"}
        ok = [x for x in sema if x["tip"] == "ok"]
        fy = min(ok, key=lambda o: abs(o["x2"] - o["x1"]))       # düşey ok
        fx = min(ok, key=lambda o: abs(o["y2"] - o["y1"]))       # yatay ok
        self.assertGreater(taban["g"], taban["d"])               # taban yatay, ağız düşey
        self.assertGreater(agiz["d"], agiz["g"])
        self.assertAlmostEqual(fy["x2"], agiz["x"] + agiz["g"] / 2.0)
        self.assertGreater(fy["y1"], fy["y2"])
        self.assertGreaterEqual(fy["y2"], agiz["y"] + agiz["d"])  # ağzın ucuna iner
        self.assertTrue(agiz["y"] < fx["y2"] < agiz["y"] + agiz["d"])
        self.assertLessEqual(fx["x2"], agiz["x"])                 # ağza yandan
        self.assertEqual(set(oklar), {"Fx", "Fy"})

    def test_cerceve_yazilarin_enini_kapsar(self):
        """Sola hizalı tablo satırları çerçevenin içinde kalır ( taşıyordu )."""
        Y = CGE._yazi
        self.assertEqual(CGE.sinir([Y(0, 0, "ABCDE", 40, hiza="sol")]), (0, -20, 120, 20))
        self.assertEqual(CGE.sinir([Y(0, 0, "ABCDE", 40, hiza="sag")]), (-120, -20, 0, 20))
        self.assertEqual(CGE.sinir([Y(0, 0, "ABCDE", 40)]), (-60, -20, 60, 20))
        self.assertEqual(CGE.sinir([Y(0, 0, "ABCDE", 40, hiza="sol", aci=90)]), (-20, 0, 20, 120))
        e = CGE.cerceveli(CKD.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV})), "KUYU DİBİ PLANI")
        c = next(x for x in e if x["katman"] == "CERCEVE" and x["tip"] == "dikdortgen")
        for x in self._tablo(e):
            self.assertLessEqual(x["x"] + CGE._yazi_eni(x["metin"], x["yukseklik"]), c["x"] + c["g"])

    def test_olcu_yazisi_parcaya_binmez(self):
        """Kuyunun içindeki ölçü yazıları tampon, gergi, merdiven, ray, konsol,
        perde ve nokta adlarının üstüne düşmez ( Yatarak sığınmada "1000"
        kabin tamponunun üstündeydi )."""
        projeler = list(_dip_projeler()) + [
            ("Yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            ("Yatarak · ELEport tamponu", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak",
                                                           "regulator_kasnak_capi": 240}))]
        for ad, g in projeler:
            e = CKD.ciz(g)
            G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
            engel = [CGE.sinir([x]) for x in e if x["katman"] in CGE.PARCA_KATMANLARI
                     or (x["tip"] == "yazi" and x["katman"] == "YAZI")]
            for o in e:
                if o["tip"] != "olcu":
                    continue
                y_ = o["yazi"]
                if not (0 < y_["x"] < G and 0 < y_["y"] < D):
                    continue
                w, h = CGE._yazi_eni(o["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                if y_["aci"]:
                    w, h = h, w
                k = (y_["x"] - w, y_["y"] - h, y_["x"] + w, y_["y"] + h)
                with self.subTest(proje=ad, olcu=o["metin"]):
                    self.assertFalse([b for b in engel if CKD._ortusur(k, b)])

    def test_kuvvet_tablosu_cizimin_disinda(self):
        """Tablo planın ve ölçülerin sağında;  satırlar üst üste binmez."""
        for ad, g in _dip_projeler():
            g["kuyu_dibi"]["kuvvetler"] = dict(self.KV)
            e = CKD.ciz(g)
            t = self._tablo(e)
            sag = max(max(x.get("x", 0), x.get("x2", 0), x.get("x", 0) + x.get("g", 0),
                          x["yazi"]["x"] + x["yazi"]["h"] / 2.0 if x["tip"] == "olcu" else 0)
                      for x in e if x.get("ad") not in ("kuvvet_tablosu", "kuvvet_semasi"))
            sema = [x for x in e if x.get("ad") == "kuvvet_semasi"]
            with self.subTest(proje=ad):
                self.assertGreater(min(x["x"] for x in t), sag)
                self.assertGreater(CGE.sinir(sema)[0], sag)
                #  Şema tablonun altında, son satıra binmez
                self.assertLess(CGE.sinir(sema)[3], min(x["y"] for x in t) - 40)
                ys = [x["y"] for x in t]
                self.assertTrue(all(a - b >= 1.5 * 45 for a, b in zip(ys, ys[1:])))

    def test_kabin_cizilmez(self):
        """Kesit en alt duraktaki kabinin altından geçer:  kabin bu planda yoktur,
        izi de çizilmez."""
        for ad, g in _dip_projeler():
            e = CKD.ciz(g)
            with self.subTest(proje=ad):
                self.assertFalse([x.get("ad") for x in e if "kabin" in (x.get("ad") or "")
                                  and x.get("ad") not in ("kabin_tamponu", "kabin_ray")])
                self.assertFalse([x["katman"] for x in e if x["katman"].startswith("KABIN")])

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
        #  İki tamponda her birine düşen:  hesap paftasındaki Fkt1 = Fkt / ncar
        self.assertEqual(sorted(adlar), sorted(["FKR", "FKR", "FAR", "FAR", "Fkt1", "Fkt1", "Fat"]))

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
        #  Pano ön duvarda:  2.400'de her şey sığar, 2.200'de makinenin başında bakım alanı kalmaz
        self.assertEqual(CMD.dogrula(_ornek(makine_dairesi={"derinlik": 2400, "pano_duvar": "Ön"})), [])
        h = CMD.dogrula(_ornek(makine_dairesi={"derinlik": 2200, "pano_duvar": "Ön"}))
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


#  ─────────────────────────────────────────────────────────────────────
#  DÜŞEY KESİTLER
#  ─────────────────────────────────────────────────────────────────────
from cizim import donanim as CDN           # noqa: E402
from cizim import dusey as CDU             # noqa: E402
from cizim import kuyu_kesiti as CKK       # noqa: E402


class DuseyKesitler(unittest.TestCase):
    def test_ornek_gecerli_ve_elle_hesapla_ayni(self):
        g = _ornek()
        self.assertEqual(CDU.dogrula(g), [])
        Y = CDU.yerlesim(g)
        #  Patenlerin MERKEZLERİ arası hesabın paten arasıdır ( kabin 3.300, ağırlık
        #  1.500 ):  kabinde şasenin alt ve üst kirişine ortalı ( 140 / 2 = 70 taşar ),
        #  ağırlıkta çerçevenin ortasına göre.
        #  Kuyu dibi:  kabin döşemesi −( 96 + 90 ) = −186;  platform altı −306,
        #  kasnak altı −186 − 295 − 120 = −601,  etek −936,  alt paten −186 − 480 − 70 = −736
        self.assertEqual({k: v[0] for k, v in Y["dip_aciklik"].items()},
                         {"siginma": 1194, "en_alt": 899, "etek": 564, "sase": 764})
        #  Kuyu üstü:  yükselme 150 + 90 + 35 = 275;  tavan 275 + 2.310 = 2.585,
        #  kiriş altı 5.000 − 150 = 4.850;  üst paten 275 − 480 + 3.300 + 70 = 3.165.
        #  Makine şasesinin altı 5.000 − 250 − 345 − 200 = 4.205 ( ELEport ) ve
        #  şase soldaki patenin 0,40 m yakınında:  paten 4.205 − 3.165 = 1.040.
        #  Yakın kabin rayı şasede biter:  5.000 − 650 = 4.350 → 1.185.
        #  Korkuluk ( 3.685 ) — şase korkuluğun dışında ( 0,10 m ) → 520.
        #  Karşı ağırlık en üstte:  −1.040 + 150 + 21.000 + 96 + 90 + 35 = 20.331,
        #  üst paten 20.331 + 2.920 / 2 + 1.500 / 2 + 70 = 22.611;  ağırlık rayı
        #  26.000 − 650 = 25.350 → 2.739.
        self.assertEqual(Y["yukselme"], 275)
        self.assertEqual({k: v[0] for k, v in Y["ust_aciklik"].items()},
                         {"siginma": 2265, "paten": 1040, "ray": 1185, "korkuluk": 520,
                          "agirlik_ray": 2739})
        self.assertEqual({k: v[1] for k, v in Y["ust_engel"].items()},
                         {"siginma": "kuyu tavanı", "paten": "sase", "ray": "ray", "korkuluk": "sase"})

    def test_kabin_modeli_tutarli(self):
        g, S = _ornek(), CS_.sabitler()
        k = CDU.kabin_kotlari(g["dusey"], S, 0.0)
        self.assertEqual(k["sase_ust"] - k["sase_alt"], g["dusey"]["kabin_paten_arasi"])
        self.assertEqual(k["tavan"], g["dusey"]["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"])
        self.assertEqual(k["etek_alti"], -750)                      # m.5.4.5.1

    def test_kuyu_dibi_zinciri_kabinle_kapanmali(self):
        h = CDU.dogrula(_ornek(kuyu_dibi={"derinlik": 1600}))
        self.assertTrue(any("kabinle çelişiyor" in x for x in h), h)

    def test_korkuluk_sinirlari(self):
        #  Makine dairesinde kuyu tavanına 0,30:  kiriş altı − 3.685 = 300 → 4.135.
        #  Makine dairesizde korkuluğun dışındaki şaseye 0,10:  ( SK − 795 ) −
        #  3.685 = 100 → 4.580 ( m.5.2.5.7.2 c 1 ).
        for yeri, sinir in (("Makine dairesi", 4135), ("Kuyu üstü", 4580)):
            for sk, uygun in ((sinir, True), (sinir - 1, False)):
                h = CDU.dogrula(_ornek(dusey={"son_kat": sk}, makine={"yeri": yeri}))
                with self.subTest(yeri=yeri, son_kat=sk):
                    self.assertEqual(not any("m.5.2.5.7.2 c" in x for x in h), uygun, h)

    def test_tavan_parcalari_engel_sayilir(self):
        #  Sığınma alanının üstüne bir parça gelirse sığınma ona ölçülür:
        #  regülatör sığınmanın üstüne kaydırılınca engel regülatördür.
        g = _ornek()
        Y = CDU.yerlesim(g)
        M = Y["M"]
        self.assertEqual(CDN.tavan_engeli(M, Y["KU"]["siginma"])[1], "kuyu tavanı")
        self.assertEqual(CDN.tavan_engeli(M, M["sase"][:4]), (M["sase"][4], "sase"))
        self.assertEqual([p[0] for p in M["parcalar"]],
                         ["sase", "kabin_baglanti", "agirlik_baglanti", "regulator"])
        #  Makine dairesinde kuyuda parça yok
        self.assertEqual(CDU.yerlesim(_ornek(makine={"yeri": "Makine dairesi"}))["M"]["parcalar"], [])

    def test_karsi_agirlik_kilavuz_payi_ve_sase(self):
        #  Çerçeve yüksekliği X;  en üst konumda çerçevenin altı 20.331.
        #  Kılavuz payı ( m.5.2.5.6.2 ):  makine dairesinde ağırlık rayı tavan kirişinin
        #  altında biter ( 26.000 − 150 = 25.850 );  patenler çerçevenin uçlarında ( paten
        #  arası X − 140 ) → üst paten 20.331 + X;  25.850 − 20.331 − X ≥ 100 → X ≤ 5.419.
        #  Kuyu üstünde en yüksek nokta ağırlık kasnağı ( çerçeve üstü − 110 + 200 = + 90 ):
        #  20.331 + X + 90 ≤ şasenin altı 25.205 → X ≤ 4.784.
        def h(x, **ezme):
            g = _ornek(**ezme)
            g["_cizim_sabitleri"] = {"agirlik_yukseklik": x}
            return CDU.dogrula(g)
        for x, uygun in ((5419, True), (5420, False)):
            hata = h(x, makine={"yeri": "Makine dairesi"}, dusey={"agirlik_paten_arasi": x - 140})
            with self.subTest(cerceve=x):
                self.assertEqual(not any("m.5.2.5.6.2" in y and "ağırlık" in y.lower() for y in hata), uygun, hata)
        self.assertFalse(any("şasesine çarpıyor" in x for x in h(4784)))
        self.assertTrue(any("şasesine çarpıyor" in x for x in h(4785)))

    def test_kabin_ustu_siginma_yuksekligi(self):
        #  dik duruş 2.000:  kiriş altı − 2.585 ≥ 2.000  →  son kat en az 4.735
        g = _ornek(dusey={"son_kat": 4734}, kabin_ustu={"siginma_tipi": "Dik duruş"})
        self.assertTrue(any("m.5.2.5.7.1" in x for x in CDU.dogrula(g)))
        g = _ornek(dusey={"son_kat": 4735}, kabin_ustu={"siginma_tipi": "Dik duruş"})
        self.assertFalse(any("m.5.2.5.7.1" in x for x in CDU.dogrula(g)))

    def test_standart_sayilari(self):
        self.assertEqual(CDU.SIGINMA_UST_YUKSEKLIK, {"Dik duruş": 2000.0, "Çömelme": 1000.0})
        self.assertEqual(CDU.SIGINMA_DIP_YUKSEKLIK,
                         {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0})
        self.assertEqual((CDU.DIP_EN_ALT, CDU.DIP_ETEK, CDU.DIP_RAYA_YAKIN, CDU.UST_PATEN,
                          CDU.UST_KORKULUK, CDU.UST_KORKULUK_DIS, CDU.YATAY_UZAKLIK,
                          CDU.RAY_UZANTISI, CDU.ETEK_BOYU),
                         (500.0, 100.0, 100.0, 100.0, 300.0, 100.0, 400.0, 100.0, 750.0))


class TamBoyKesit(unittest.TestCase):
    def test_durak_kotlari(self):
        self.assertEqual(CDU.durak_kotlari(_ornek())[0], [0, 3000, 6000, 9000, 12000, 15000, 18000, 21000])
        #  LiftDesigner örneği gibi karışık kat yükseklikleri
        kotlar, hata = CDU.durak_kotlari(_ornek(dusey={"durak_adedi": 4,
                                                       "kat_yuksekligi": [3400, 3400, 3000]}))
        self.assertEqual((kotlar, hata), ([0, 3400, 6800, 9800], []))

    def test_hatali_durak_girdileri(self):
        for dy in ({"durak_adedi": 1}, {"durak_adedi": 2.5}, {"durak_adedi": True},
                   {"kat_yuksekligi": [3000, 3000]}, {"kat_yuksekligi": 0},
                   {"kat_yuksekligi": "3000"}):
            with self.subTest(dy=dy):
                self.assertTrue(CDU.dogrula(_ornek(dusey=dy)))

    def test_esik_arasi_11_m(self):
        #  m.5.2.3.1:  11 m'ye kadar olur, aşarsa ara acil kapı gerekir
        for h, uygun in ((11000, True), (11001, False)):
            kh = [3000] * 6 + [h]
            with self.subTest(h=h):
                hata = CDU.dogrula(_ornek(dusey={"kat_yuksekligi": kh}))
                self.assertEqual(not any("m.5.2.3.1" in x for x in hata), uygun, hata)
        self.assertEqual(CDU.ESIK_ARASI, 11000.0)

    def test_kat_kapi_yuksekliginden_buyuk(self):
        hata = CDU.dogrula(_ornek(dusey={"kat_yuksekligi": 2100}))
        self.assertTrue(any("kat kapısı yüksekliğinden" in x for x in hata), hata)

    def test_kesit_zincir_kotlar_yazilar_dxf(self):
        import itertools
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        for g in (_ornek(), _ornek(dusey={"durak_adedi": 4, "kat_yuksekligi": [3400, 3400, 3000]}),
                  _ornek(makine={"yeri": "Makine dairesi"}), _sag_ayna(kuyu_dibi={"regulator_yan": "Sol"})):
            for ciz in (CKK.yan_kesit, CKK.on_kesit):
                e = ciz(g)
                dy = g["dusey"]
                kotlar = CDU.durak_kotlari(g)[0]
                with self.subTest(cizim=ciz.__name__, duraklar=dy["durak_adedi"],
                                  makine=g["makine"]["yeri"], agirlik=g["agirlik"]["yeri"]):
                    self.assertEqual(sum(1 for x in e if x.get("ad") == "durak_adi"), dy["durak_adedi"])
                    oda = ([kotlar[-1] + dy["son_kat"] + g["makine_dairesi"]["tabliye_yuksekligi"]]
                           if g["makine"]["yeri"] == "Makine dairesi" else [])
                    self.assertEqual({x["metin"] for x in e if x.get("ad") == "kot"},
                                     {CDU._kot(z) for z in kotlar + [-g["kuyu_dibi"]["derinlik"]] + oda})
                    #  Sol zincir:  kuyu dibi + kat yükseklikleri + son kat = kuyu yüksekliği
                    #  ( ELEport:  1.500 + 29.000 + 5.000 = 35.500 )
                    toplam = g["kuyu_dibi"]["derinlik"] + kotlar[-1] + dy["son_kat"]
                    metinler = {x["metin"] for x in e if x["tip"] == "olcu"}
                    self.assertIn(f"KUYU YÜKSEKLİĞİ {toplam:g}", metinler)
                    self.assertIn(f"SEYİR {kotlar[-1]:g}", metinler)
                    zz = CGE.zincirler(e)
                    for z in zz:
                        self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                    self.assertTrue(any(z["adet"] == dy["durak_adedi"] + 1 and
                                        abs(z["toplam"] - toplam) < 1e-6 for z in zz))
                    #  Konsol zinciri kuyu tabanından kuyu tavanına kapanır
                    self.assertTrue(any(abs(z["bas"] + g["kuyu_dibi"]["derinlik"]) < 1e-6 and
                                        abs(z["son"] - kotlar[-1] - dy["son_kat"]) < 1e-6 and
                                        z["adet"] > dy["durak_adedi"] + 1 for z in zz))
                    k = OlcuYazilari._kutular(None, e)
                    for a, b in itertools.combinations(k, 2):
                        self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4],
                                         (a[0]["metin"], b[0]["metin"]))
                    #  1/50:  ölçü yazısı paftada 1/20'dekiyle aynı boyda
                    self.assertTrue(all(x["yazi"]["h"] == CGE.OLCU_YAZI * 2.5
                                        for x in e if x["tip"] == "olcu"))
                    au = Auditor(CDX.belge(e, "DÜŞEY", 50))
                    au.run()
                    self.assertEqual(list(au.errors), [])

    def test_olcek_kalemleri_buyutur(self):
        e = [CGE._dik("KUYU-DUVAR", 0, 0, 100, 100)]
        self.assertIn('stroke-width="12"', CSV.yaz(e, (0, 0, 100, 100), "", 20))
        self.assertIn('stroke-width="30"', CSV.yaz(e, (0, 0, 100, 100), "", 50))


class KuyuKesitleri(unittest.TestCase):
    """A-A ve B-B tam boy kesitler:  donanımın yerleri ve halat geometrisi."""

    def _elemanlar(self, e, ad):
        return [x for x in e if x.get("ad") == ad]

    def test_eleport_kotlari(self):
        #  ELEport kesitlerinin vektörlerinden ölçülenler:  tavandan makine
        #  kapağının üstü 250, tahrik kasnağı merkezi 446, şase 595 – 795;
        #  şasenin altındaki raylar 650'de biter, regülatör kasnağı 462,
        #  gergi kasnağı tabandan 520, karşı ağırlık çerçevesi 2.920.
        g = _ornek()
        Y = CDU.yerlesim(g)
        M = Y["M"]
        T = M["tavan"]
        self.assertEqual(T, 21000 + 5000)
        self.assertEqual(T - M["kapak"][5], 250)
        self.assertEqual(T - M["kasnak"][4], 446)
        self.assertEqual((T - M["sase"][5], T - M["sase"][4]), (595, 795))
        #  Şase ağırlık raylarının dış yüzlerinden 8 taşar:  ELEport kesitinde
        #  raylar iç yüzden 627 – 1.607 ( yan kesit vektörleri ) → 619 – 1.615
        self.assertEqual(M["sase"][:4], (20, 619.0, 343.0, 1615.0))
        ustler = sorted(T - r["ust"] for r in M["raylar"])
        #  Öbür kabin rayı ELEport'ta 50'de biter;  kuyu tavanı payı ( 150 ) büyük
        self.assertEqual(ustler, [150, 650, 650, 650])
        self.assertEqual(T - M["regulator_kasnak"][4], 462)
        self.assertEqual(M["gergi"]["merkez"] - Y["taban"], 520)
        self.assertEqual(CDN.agirlik_kotlari(M, 0)["ust"], 2920)

    def test_konsollar_ve_ekler(self):
        #  İlk konsol tabandan 500, sonra "konsollar arası";  ray ucunu geçmez.
        for aralik in (1500, 3000):
            g = _ornek(dusey={"kabin_konsol_arasi": aralik, "agirlik_konsol_arasi": aralik})
            M = CDU.yerlesim(g)["M"]
            for r in M["raylar"]:
                with self.subTest(aralik=aralik, ray=r["kutu"]):
                    k = r["konsollar"]
                    self.assertEqual(k[0] - r["alt"], 500)
                    self.assertTrue(all(abs(b - a - aralik) < 1e-9 for a, b in zip(k, k[1:])))
                    self.assertLessEqual(k[-1], r["ust"])
                    self.assertGreater(k[-1] + aralik, r["ust"])
                    self.assertEqual(r["ekler"], [r["alt"] + 5000 * i for i in range(1, len(r["ekler"]) + 1)])
                    self.assertGreater(r["ekler"][-1] + 5000, r["ust"])

    def test_kabin_ve_agirlik_konumlari(self):
        g = _ornek()
        Y = CDU.yerlesim(g)
        M, dy = Y["M"], g["dusey"]
        tampon_ustu = -1500 + 300 + 160
        self.assertEqual(M["agirlik"]["tampon_ustu"], tampon_ustu)
        #  A-A:  kabin en alt durakta ( taban altı −120 ), ağırlık seyir kadar yukarıda
        e = CKK.yan_kesit(g)
        kabin = self._elemanlar(e, "kabin")[0]
        self.assertEqual(kabin["y"], -120)
        ag = self._elemanlar(e, "agirlik")[0]
        self.assertEqual(ag["y"], tampon_ustu + dy["agirlik_carpma_arasi"] + 21000)
        #  B-B:  kabin en üst durakta, ağırlık tamponunun çarpma arası üstünde
        e = CKK.on_kesit(g)
        self.assertEqual(self._elemanlar(e, "kabin")[0]["y"], 21000 - 120)
        self.assertEqual(self._elemanlar(e, "agirlik")[0]["y"], tampon_ustu + dy["agirlik_carpma_arasi"])

    def test_halatlar_kasnaklara_teget(self):
        #  Düşey halat bir kasnağın merkez kotunda bitiyorsa o kasnağa teğettir.
        for ciz, en_az in ((CKK.on_kesit, 4), (CKK.yan_kesit, 2)):
            e = ciz(_ornek())
            daireler = [x for x in e if x["tip"] == "daire" and x["katman"] == "KASNAK"]
            teget = 0
            for h in (x for x in e if x["katman"] == "HALAT" and abs(x["x1"] - x["x2"]) < 1e-9):
                for z in (h["y1"], h["y2"]):
                    for d in daireler:
                        if abs(d["y"] - z) < 1e-6 and abs(d["x"] - h["x1"]) <= d["r"] + 1e-6:
                            with self.subTest(cizim=ciz.__name__, kasnak=d.get("ad"), z=z):
                                self.assertAlmostEqual(abs(d["x"] - h["x1"]), d["r"])
                            teget += 1
            self.assertGreaterEqual(teget, en_az, ciz.__name__)

    def test_parcalar_var_ve_gorunurluk(self):
        #  A-A kabin ekseninden karşı ağırlığa bakar:  regülatör, kabin halat
        #  bağlantısı, gergi ve öbür kabin rayı bakanın gerisinde kalır;
        #  onlar B-B'de görünür ( ELEport da iki yan kesitte ayrı gösterir ).
        A = ("makine", "makine_sasesi", "tahrik_kasnagi", "agirlik_baglanti", "agirlik",
             "agirlik_kasnagi", "kabin_tamponu", "agirlik_tamponu", "kat_kapisi", "kat_dosemesi",
             "tavan_kirisi")
        B = ("makine", "makine_sasesi", "tahrik_kasnagi", "kabin_kasnagi", "regulator",
             "regulator_kasnagi", "kabin_baglanti", "gergi_kasnagi", "gergi_agirligi", "agirlik",
             "kat_kapisi", "durak_no", "kabin_kapisi", "sase", "fren")
        for ciz, adlar, yok, kabin_rayi in (
                (CKK.yan_kesit, A, ("regulator", "kabin_baglanti", "gergi_kasnagi"), 1),
                (CKK.on_kesit, B, (), 2)):
            e = ciz(_ornek())
            for ad in adlar:
                with self.subTest(cizim=ciz.__name__, ad=ad):
                    self.assertTrue(self._elemanlar(e, ad))
            for ad in yok:
                with self.subTest(cizim=ciz.__name__, gorunmez=ad):
                    self.assertFalse(self._elemanlar(e, ad))
            self.assertEqual(len(self._elemanlar(e, "kabin_rayi")), kabin_rayi)
            self.assertEqual(len(self._elemanlar(e, "agirlik_rayi")), 2)
        #  Karşı ağırlık sağdaysa A-A sağa bakar
        e = CKK.yan_kesit(_sag_ayna(kuyu_dibi={"regulator_yan": "Sol"}))
        self.assertTrue(self._elemanlar(e, "makine"))
        self.assertFalse(self._elemanlar(e, "regulator"))

    def test_girdi_hatalari(self):
        self.assertTrue(any("makine.yeri" in x for x in CDU.dogrula(_ornek(makine={"yeri": "Çatı"}))))
        for alan in ("kabin_konsol_arasi", "agirlik_konsol_arasi"):
            with self.subTest(alan=alan):
                self.assertTrue(any(alan in x for x in CDU.dogrula(_ornek(dusey={alan: 0}))))

    def test_makine_daireli_kesitler(self):
        #  Oda döşemesi hesabın tabliyesi:  kuyu tavanı 26.000 + 1.200 = 27.200;  tavanı + 3.500.
        #  Dişlisiz makine kaidede ( şase yüksekliği 1.100 ), kasnak merkezi + 149, üstü + 120
        #  → 28.569;  kasnak üstü 30.700 − 28.569 = 2.131 ( m.5.2.6.3.2.3:  ≥ 300 ).
        g = _ornek(makine={"yeri": "Makine dairesi"})
        self.assertEqual(CKK.dogrula(g), [])
        M = CDU.yerlesim(g)["M"]
        self.assertEqual((M["oda_doseme"], M["oda_tavan"]), (27200, 30700))
        self.assertEqual(M["kasnak"][4] + 120, 28569)
        self.assertEqual(M["parcalar"], [])                       # kuyuda tavan parçası yok
        for ciz in (CKK.yan_kesit, CKK.on_kesit):
            e = ciz(g)
            metinler = {x["metin"] for x in e if x["tip"] == "olcu"}
            with self.subTest(cizim=ciz.__name__):
                self.assertIn("KASNAK ÜSTÜ 2131 ≥ 300", metinler)
                self.assertIn("MAKİNE DAİRESİ 3500 ≥ 2100", metinler)
                #  Döşeme hesabın tabliyesi, çatı 150;  kaide hesabın şase yüksekliği
                self.assertTrue({"TABLİYE 1200", "150", "ŞASE 1100"} <= metinler, metinler)
                self.assertEqual({x["d"] for x in self._elemanlar(e, "oda_dosemesi")}, {1200})
                self.assertEqual({x["d"] for x in self._elemanlar(e, "oda_catisi")}, {150})
                for ad in ("oda_dosemesi", "oda_catisi", "oda_duvari", "makine", "doseme_deligi"):
                    self.assertTrue(self._elemanlar(e, ad), ad)
                #  Kumanda panosu odanın arka yarısında:  iki kesitte de bakanın gerisinde
                self.assertFalse(self._elemanlar(e, "kumanda_panosu"))
                self.assertIn(CDU._kot(27200), {x["metin"] for x in e if x.get("ad") == "kot"})

    def test_makine_dairesi_sinirlari(self):
        def h(**md):
            return CDU.dogrula(_ornek(makine={"yeri": "Makine dairesi"}, makine_dairesi=md))
        self.assertFalse(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=2100)))
        self.assertTrue(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=2099)))
        self.assertFalse(any("m.5.2.3.2 a" in x for x in h(kapi_yukseklik=2000)))
        self.assertTrue(any("m.5.2.3.2 a" in x for x in h(kapi_yukseklik=1999)))
        #  Kasnak üstü:  şase yüksekliği X ise 3.500 − ( X + 269 ) ≥ 300 → X ≤ 2.931
        for x, uygun in ((2931, True), (2932, False)):
            g = _ornek(makine={"yeri": "Makine dairesi"}, makine_dairesi={"sase_yuksekligi": x})
            with self.subTest(sase=x):
                self.assertEqual(not any("m.5.2.6.3.2.3" in y for y in CDU.dogrula(g)), uygun)
        self.assertTrue(any("makine_dairesi.yukseklik" in x for x in h(yukseklik=None)))
        #  Hesap programının makine dairesi girdileri eksik / geçersizse çizilmez
        for alan, v in (("tabliye_yuksekligi", None), ("tabliye_yuksekligi", 0), ("sase_yuksekligi", None),
                        ("yan_yatak_boyu", -1), ("dikine_kiris", 125), ("dikine_kiris", "NPU 120")):
            with self.subTest(alan=alan, deger=v):
                self.assertTrue(any(f"makine_dairesi.{alan}" in x for x in h(**{alan: v})))
        self.assertEqual((CDN.ODA_YUKSEKLIK, CDN.DONEN_PARCA_USTU, CDN.ODA_KAPI_YUKSEKLIK),
                         (2100.0, 300.0, 2000.0))

    def test_plandaki_kesit_isaretleri(self):
        e = CGE.plan(_ornek())
        self.assertEqual(sorted(x["metin"] for x in e if x.get("ad") == "kesit_harfi"), ["A", "A", "B", "B"])
        self.assertEqual(len([x for x in e if x.get("ad") == "kesit_isareti"]), 4)
        #  Kesit çizilemeyen düzende işaret de yok
        for g in (_arka(), _ornek(aski={"duzen": "Doğrudan", "nokta_arasi": 450})):
            self.assertFalse([x for x in CGE.plan(g) if x["katman"] == "KESIT"])
        self.assertTrue([x for x in CGE.plan(_ornek(makine={"yeri": "Makine dairesi"}))
                         if x["katman"] == "KESIT"])


class PlanSeviyeleri(unittest.TestCase):
    """Düşey kesitlerde planların hangi yükseklikten alındığı ( C-C … G-G )."""

    def _seviyeler(self, e):
        return {x["ad"][len("plan_seviyesi_"):]: x["y1"] for x in e
                if x.get("ad", "").startswith("plan_seviyesi_")}

    def test_kotlar(self):
        #  C:  en alt durak + kapı / 2 = 1.050;  D:  kabinin tavanı ( A-A kabin
        #  altta 2.310, B-B üstte 21.000 + 2.310 );  E:  ilk konsolun üstü
        #  −1.500 + 500 = −1.000 ile kabinin en alt noktası ( etek −750 ) arası
        #  → −875;  F:  tahrik kasnağı ekseni ( kuyu tavanı 26.000 − 446 );  makine
        #  dairesinde tabliye 1.200 + kaide 1.100 + 149 → 28.449, G tabliyenin ortası 26.600.
        g = _ornek()
        self.assertEqual(self._seviyeler(CKK.yan_kesit(g)),
                         {"kuyu_plani": 1050, "kabin_ustu": 2310, "kuyu_dibi": -875, "kuyu_ustu": 25554})
        self.assertEqual(self._seviyeler(CKK.on_kesit(g))["kabin_ustu"], 23310)
        md = _ornek(makine={"yeri": "Makine dairesi"})
        sev = self._seviyeler(CKK.on_kesit(md))
        self.assertEqual((sev["makine_dairesi"], sev["delik_plani"]), (28449, 26600))
        self.assertNotIn("kuyu_ustu", sev)

    def test_kuyu_dibi_kesiti_kabinden_gecmez(self):
        """E-E kuyu dibi planıdır:  A-A'da en alt durakta duran kabinin hiçbir
        parçasına değmez ( kabin o planda yoktur ), ilk konsolların üstündedir."""
        parcalar = ("kabin", "etek", "sase", "alt_paten", "fren", "kabin_kasnak", "kabin_esigi",
                    "kabin_kanadi")
        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"}),
                  _ornek(dusey={"kabin_ic_yukseklik": 2100})):
            e = CKK.yan_kesit(g)
            z = self._seviyeler(e)["kuyu_dibi"]
            alt = {}
            for x in e:
                if x["tip"] == "dikdortgen" and x.get("ad") in parcalar:
                    alt[x["ad"]] = min(alt.get(x["ad"], x["y"]), x["y"])
            with self.subTest(makine=g["makine"]["yeri"]):
                self.assertEqual(set(alt), set(parcalar))
                self.assertLess(z, min(alt.values()))
                Y = CKK.yerlesim(g)
                self.assertGreater(z, max(r["konsollar"][0] for r in Y["M"]["raylar"]))

    def test_harfler_cakismaz(self):
        import itertools
        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"})):
            for ciz in (CKK.yan_kesit, CKK.on_kesit):
                e = ciz(g)
                harfler = [x for x in e if x.get("ad") == "plan_harfi"]
                self.assertEqual(len(harfler), 2 * len(self._seviyeler(e)))
                kutular = [(x["x"] - x["yukseklik"] * 0.3, x["y"] - x["yukseklik"] / 2,
                            x["x"] + x["yukseklik"] * 0.3, x["y"] + x["yukseklik"] / 2) for x in harfler]
                for a, b in itertools.combinations(kutular, 2):
                    with self.subTest(cizim=ciz.__name__, makine=g["makine"]["yeri"]):
                        self.assertFalse(a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3])
                #  Harf başka bir seviyenin çizgisinin üstüne düşmez
                cizgiler = [x for x in e if x.get("ad", "").startswith("plan_seviyesi_")]
                for (x0, y0, x1, y1), c in itertools.product(kutular, cizgiler):
                    if y0 < c["y1"] < y1:
                        self.assertFalse(c["x1"] < x1 and x0 < c["x2"], (c["ad"], (x0, y0)))

    def test_plan_basliklari(self):
        from cizim import cizimler as calistir
        b = "KUYU PLANI  ( kabin hizasından yatay kesit )"
        self.assertEqual(calistir.plan_basligi(_ornek(), "kuyu_plani", b),
                         "KUYU PLANI  C-C  ( kabin hizasından yatay kesit )")
        md = _ornek(makine={"yeri": "Makine dairesi"})
        self.assertEqual(calistir.plan_basligi(md, "makine_dairesi", "MAKİNE DAİRESİ PLANI"),
                         "MAKİNE DAİRESİ PLANI  F-F")
        self.assertEqual(calistir.plan_basligi(md, "delik_plani", "DELİK PLANI"), "DELİK PLANI  G-G")
        #  Makine dairesizde F kuyu üstü planınındır;  makine dairesi / delik planı harfsiz
        self.assertEqual(calistir.plan_basligi(_ornek(), "makine_dairesi", "MAKİNE DAİRESİ PLANI"),
                         "MAKİNE DAİRESİ PLANI")
        self.assertEqual(calistir.plan_basligi(_ornek(), "delik_plani", "X"), "X")
        self.assertEqual(calistir.plan_basligi(md, "kuyu_ustu", "KUYU ÜSTÜ PLANI"), "KUYU ÜSTÜ PLANI")
        self.assertEqual(calistir.plan_basligi(_ornek(), "kuyu_ustu", "KUYU ÜSTÜ PLANI"),
                         "KUYU ÜSTÜ PLANI  F-F")
        #  Düşey kesit çizilemeyen düzende harf yok
        self.assertEqual(calistir.plan_basligi(_arka(), "kuyu_plani", b), b)
        self.assertEqual(calistir.plan_basligi(_ornek(), "kuyu_kesiti_yan", "X"), "X")


class KirikKesit(unittest.TestCase):
    """Paftaya sığmayan düşey kesitte ara katlar kırılır ( ELEport, LiftDesigner )."""

    def _yukseklik(self, e):
        return CKK._yukseklik(e, CKK.OLCEK / 20.0)

    def test_sigmazsa_kirilir_sigarsa_kirilmaz(self):
        g = _ornek()
        tam = CKK.yan_kesit(g)
        self.assertFalse([x for x in tam if x.get("ad") == "kirik_cizgisi"])
        self.assertFalse([x for x in CKK.yan_kesit(g, azami=self._yukseklik(tam) + 1)
                          if x.get("ad") == "kirik_cizgisi"])
        for ciz in (CKK.yan_kesit, CKK.on_kesit):
            for azami in (560 * 50, 420 * 50, 300 * 50):
                e = ciz(g, azami=azami)
                with self.subTest(cizim=ciz.__name__, azami=azami):
                    self.assertTrue([x for x in e if x.get("ad") == "kirik_cizgisi"])
                    if azami >= 420 * 50:
                        self.assertLessEqual(self._yukseklik(e), azami)

    def test_en_siki_kirik_hareketli_parcalara_degmez(self):
        #  Yalnız birer durak kalınca kırık kabinin ( A-A ) ve karşı ağırlığın
        #  ( B-B ) patenlerinin hemen üstünden geçer:  hiçbiri bölünmez.
        g = _ornek()
        for ciz, adlar in ((CKK.yan_kesit, ("ust_paten", "alt_paten", "sase")),
                           (CKK.on_kesit, ("agirlik_paten", "agirlik"))):
            e = ciz(g, azami=1)
            self.assertTrue([x for x in e if x.get("ad") == "kirik_cizgisi"])
            for ad in adlar:
                boylar = sorted({round(x["d"]) for x in e if x.get("ad") == ad})
                with self.subTest(cizim=ciz.__name__, ad=ad):
                    beklenen = {"ust_paten": [140], "alt_paten": [140], "sase": [3300],
                                "agirlik_paten": [140], "agirlik": [2920]}[ad]
                    self.assertEqual(boylar, beklenen)

    def test_kirik_olculer_ve_parcalar(self):
        import itertools
        g = _ornek()
        for ciz in (CKK.yan_kesit, CKK.on_kesit):
            e = ciz(g, azami=420 * 50)
            metinler = [x["metin"] for x in e if x["tip"] == "olcu"]
            with self.subTest(cizim=ciz.__name__):
                #  Kırığı geçen ölçüler gerçek değerini yazar
                self.assertTrue(any("× 3000" in m for m in metinler), metinler)
                self.assertTrue(any("× 1500" in m for m in metinler), metinler)
                self.assertIn("SEYİR 21000", metinler)
                self.assertIn("KUYU YÜKSEKLİĞİ 27500", metinler)
                #  Çizilen zincirler geometrik olarak kapanır
                for z in CGE.zincirler(e):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                #  Kabin ve karşı ağırlık bölünmez ( çerçeve 2.920, kabin 2.310 + 120 )
                self.assertEqual([x["d"] for x in e if x.get("ad") == "agirlik"], [2920])
                self.assertEqual([x["d"] for x in e if x.get("ad") == "kabin"], [2430])
                #  Durak adları:  ara duraklar düşer, ilk ve son kalır
                adlar = {x["metin"] for x in e if x.get("ad") == "durak_adi"}
                self.assertIn("1. DURAK", adlar)
                self.assertIn("8. DURAK", adlar)
                self.assertLess(len(adlar), 8)
                k = OlcuYazilari._kutular(None, e)
                for a, b in itertools.combinations(k, 2):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4],
                                     (a[0]["metin"], b[0]["metin"]))


from cizim import pafta as CPF              # noqa: E402
from cizim import makine as CMK_            # noqa: E402


def _md(**makine):
    return _ornek(makine=dict({"yeri": "Makine dairesi"}, **makine))


class MakineVeSase(unittest.TestCase):
    """Makine parça parça ( LiftDesigner makineleri ), şase hesap programının
    profilleriyle ( kuyu üstünde 2 yan yatak, makine dairesinde kaide:  dikine
    kirişler + yan yataklar ), saptırma kasnağı ve sarım açısı."""

    def _parca(self, e, parca):
        return [x for x in e if x.get("parca") == parca]

    def _kutular(self, parcalar, parca):
        return [p["k"] for p in parcalar if p["tur"] == "kutu" and p["parca"] == parca]

    def test_tipler(self):
        self.assertEqual(CMK_.TIPLER, ("Dişlisiz", "Dişli"))
        self.assertTrue(any("makine.tip" in h for h in CKK.dogrula(_ornek(makine={"tip": "Dişlili"}))))
        #  Makine dairesizde dişli makine yok ( kuyu tepesindeki şaseye sığmaz )
        self.assertTrue(any("dişli makine çizilmez" in h for h in CKK.dogrula(_ornek(makine={"tip": "Dişli"}))))
        self.assertEqual(CKK.dogrula(_md(tip="Dişli")), [])

    def test_disli_ve_dislisiz_sabitleri(self):
        """LiftDesigner'dan ölçülen sayılar ( dişlisiz 4815-6, dişli A 160 )."""
        self.assertEqual([(a, b, c) for a, b, c in CMK_.DISLISIZ],
                         [("gobek", 15, 100), ("flans", 28, 220), ("yatak", 50, 320), ("govde", 206, 400),
                          ("fren", 70, 320), ("fren_diski", 18, 240), ("enkoder", 102, 270)])
        self.assertEqual((CMK_.DISLISIZ_CAP, CMK_.DISLISIZ_BOY), (400.0, 489.0))
        self.assertEqual(CMK_.DISLI_ZARF, {"m": (-1000.0, 320.0), "a": (-175.0, 415.0), "z": (-195.0, 410.0)})
        #  NPU ( UPN ) DIN 1026-1;  anahtarlar hesap programının NPU listesi
        self.assertEqual(CMK_.npu(200), {"h": 200.0, "b": 75.0, "s": 8.5, "t": 11.5})
        self.assertEqual(CMK_.npu(120), {"h": 120.0, "b": 55.0, "s": 7.0, "t": 9.0})
        self.assertEqual(CMK_.npu(140), {"h": 140.0, "b": 60.0, "s": 7.0, "t": 10.0})
        self.assertEqual(CMK_.npu(100.0), CMK_.npu(100))
        self.assertIsNone(CMK_.npu(125))
        self.assertEqual(list(CMK_.NPU), ["30x15", 30, "40x20", 40, "50x25", 50, 60, 65, 80, 100, 120, 140,
                                          160, 180, 200, 240, 280, 300])
        self.assertEqual(CMK_.KAIDE_KISA, 100)

    def test_dislisiz_zarfa_oranlanir(self):
        """Biçim LiftDesigner'ın, ölçü projenin zarfı:  kasnağın arkasından
        boşluk + gövde boyu, çap gövde çapını aşmaz;  kasnak kendi çapında."""
        g, S = _ornek(), CS_.sabitler()
        Y = CKT.yerlesim(g)
        k = [p for p in Y["makine"] if p["ad"] == "makine"]
        kasnak = next(p for p in Y["makine"] if p["ad"] == "tahrik_kasnagi")
        self.assertEqual([p["parca"] for p in k], [a for a, _, _ in CMK_.DISLISIZ])
        self.assertEqual(kasnak["cap"], g["makine"]["tahrik_kasnak_capi"])
        self.assertAlmostEqual(kasnak["t"][1] - kasnak["t"][0], S["tahrik_kasnak_kalinlik"])
        uc = min(p["t"][0] for p in k) if Y["s"] < 0 else max(p["t"][1] for p in k)
        y0 = Y["halatlar"][0][1]
        self.assertAlmostEqual(abs(uc - y0), S["tahrik_kasnak_kalinlik"] / 2.0
                               + S["makine_kasnak_boslugu"] + S["makine_boy"])
        self.assertAlmostEqual(max(p["cap"] for p in k), S["makine_en"])
        #  Zarf eskisiyle aynı:  çakışma denetimleri değişmez
        self.assertEqual((Y["govde"][0], Y["govde"][2]), (101, 399))

    def test_kuyu_ustu_sase_upn(self):
        """2 yan yatak ( ELEport:  UPN 200 ) karşı ağırlık rayları boyunca;
        ELEport kotları değişmez ( şase tavandan 595 – 795 );  motor plakası
        700, gövdenin ortasında.  Profil hesabın yan yatağıdır:  NPU 160'ta
        şasenin üstü yine 595, altı 755."""
        for olcu, alt in ((200, 795), (160, 755)):
            g = _ornek(makine={"yan_yatak": olcu})
            Y = CKK.yerlesim(g)
            M = Y["M"]
            P = CMK_.npu(olcu)
            T = Y["kotlar"][-1] + g["dusey"]["son_kat"]
            with self.subTest(yan_yatak=olcu):
                self.assertEqual((T - M["sase"][5], T - M["sase"][4]), (595, alt))
                upn = self._kutular(M["sase_parcalari"], "yan_yatak")
                self.assertEqual(len(upn), 2)
                for x0, y0, x1, y1, z0, z1 in upn:
                    self.assertEqual((x1 - x0, z1 - z0), (P["b"], P["h"]))
                    self.assertEqual((y0, y1), (M["sase"][1], M["sase"][3]))
                self.assertEqual(sorted(k[0] for k in upn), [M["sase"][0], M["sase"][2] - P["b"]])
        g = _ornek()
        M = CKK.yerlesim(g)["M"]
        mp = next(p for p in M["sase_parcalari"] if p["parca"] == "motor_plakasi")
        self.assertEqual(mp["k"][3] - mp["k"][1], 700)
        self.assertAlmostEqual((mp["k"][1] + mp["k"][3]) / 2.0, (M["govde"][1] + M["govde"][3]) / 2.0)
        self.assertEqual(mp["k"][5], M["sase"][5])                    # üstle aynı hizada
        self.assertEqual(len([p for p in M["sase_parcalari"] if p["parca"] == "uc_levhasi"]), 2)

    def test_gorunusler(self):
        """Ön kesitte ( B-B ) kasnak ve gövde daire, yan kesitte ( A-A )
        dikdörtgen;  planda şase ve makine parça parça."""
        g = _ornek()
        D1 = g["makine"]["tahrik_kasnak_capi"]
        on, yan = CKK.on_kesit(g), CKK.yan_kesit(g)
        ks = [x for x in on if x.get("ad") == "tahrik_kasnagi"]
        self.assertTrue(ks and all(x["tip"] == "daire" and x["r"] == D1 / 2.0 for x in ks))
        ks = [x for x in yan if x.get("ad") == "tahrik_kasnagi"]
        self.assertTrue(ks and all(x["tip"] == "dikdortgen" and x["d"] == D1 for x in ks))
        for e in (on, yan):
            self.assertTrue(self._parca(e, "govde") and self._parca(e, "enkoder") and self._parca(e, "yan_yatak"))
        plan = CKT.ciz(g)
        self.assertEqual(len([x for x in self._parca(plan, "yan_yatak") if x["tip"] == "dikdortgen"]), 2)
        self.assertTrue(self._parca(plan, "motor_plakasi") and self._parca(plan, "fren"))

    def test_disli_makine_dairesinde_kaide(self):
        """Dişli makine hesap programının kaidesinde:  döşemeden şase yüksekliği
        ( 1.100 ), dört dikine kiriş ( NPU 120 ), iki yan yatak ( NPU 200 )
        makinenin uzun ekseni boyunca, dikine kirişlerin eksenleri arası yan
        yatak boyu ( 1.400 );  kasnak merkezi tabanın 195 üstünde;  motor ekseni
        kasnak eksenine dik;  makine odada, bağlantılara binmez."""
        g = _md(tip="Dişli")
        Y = CMD.yerlesim(g)
        M = CKK.yerlesim(g)["M"]
        zd = M["oda_doseme"]
        self.assertEqual(M["sase"][5] - zd, g["makine_dairesi"]["sase_yuksekligi"])
        self.assertEqual(M["kasnak"][4] - M["sase"][5], 195)
        ayak = self._kutular(M["sase_parcalari"], "dikine_kiris")
        yan = self._kutular(M["sase_parcalari"], "yan_yatak")
        self.assertEqual((len(ayak), len(yan)), (4, 2))
        self.assertTrue(Y["kaide"]["uzun_x"])                          # motor ekseni x boyunca
        for k in ayak:
            self.assertEqual((k[2] - k[0], k[3] - k[1]), (120, 55))
            self.assertEqual((k[4], k[5]), (zd + 20, M["sase"][5] - 200))
        xs = sorted({(k[0] + k[2]) / 2.0 for k in ayak})
        self.assertEqual(xs[1] - xs[0], g["makine_dairesi"]["yan_yatak_boyu"])
        for k in yan:
            self.assertEqual((k[2] - k[0], k[3] - k[1], k[5] - k[4]), (1400 + 120, 75, 200))
            self.assertEqual(k[5], M["sase"][5])
        motor = next(p for p in M["makine"] if p.get("parca") == "motor")
        kasnak = next(p for p in M["makine"] if p["ad"] == "tahrik_kasnagi")
        self.assertEqual((motor["eksen"], kasnak["eksen"]), ("x", "y"))
        taban = next(p for p in M["makine"] if p.get("parca") == "taban")
        self.assertEqual(taban["k"][4], M["sase"][5])                 # makine çerçevenin üstünde
        oda, c = Y["oda"], Y["cerceve"]
        self.assertTrue(oda[0] <= c[0] and oda[1] <= c[1] and c[2] <= oda[2] and c[3] <= oda[3])
        mk = Y["M"]["govde"]
        for b in (Y["M"]["agirlik_baglanti"], Y["M"]["kabin_baglanti"], Y["M"]["reg_govde"]):
            self.assertFalse(CKD._ortusur(mk, b))
        self.assertEqual(M["sarim_acisi"], 180.0)                      # saptırmasız

    def test_kaide_hesabin_girdileriyle(self):
        """Makine dairesinde makine HER ZAMAN kaidededir ( hesap programı
        makine daireli tesiste kolonların burkulmasını denetler ):  dişlisizde de.
        Ölçüler hesabın girdileridir:  şase yüksekliği 900, dikine NPU 100,
        yan yatak NPU 160, boyu 1.000 → kaide 1.100 uzun, kasnak 900 + 149."""
        g = _ornek(makine={"yeri": "Makine dairesi", "yan_yatak": 160},
                   makine_dairesi={"sase_yuksekligi": 900, "dikine_kiris": 100, "yan_yatak_boyu": 1000})
        self.assertEqual(CKK.dogrula(g), [])
        Y = CMD.yerlesim(g)
        M = CKK.yerlesim(g)["M"]
        zd = M["oda_doseme"]
        self.assertFalse(Y["kaide"]["uzun_x"])                         # dişlisiz:  kasnak ekseni y
        self.assertEqual((M["sase"][4], M["sase"][5]), (zd, zd + 900))
        self.assertEqual(M["kasnak"][4] - M["sase"][5], 149)
        ayak = self._kutular(M["sase_parcalari"], "dikine_kiris")
        self.assertEqual({(k[2] - k[0], k[3] - k[1]) for k in ayak}, {(50, 100)})
        ys = sorted({(k[1] + k[3]) / 2.0 for k in ayak})
        self.assertEqual(ys[1] - ys[0], 1000)
        yan = self._kutular(M["sase_parcalari"], "yan_yatak")
        self.assertEqual({(k[2] - k[0], k[3] - k[1], k[5] - k[4]) for k in yan}, {(65, 1100, 160)})
        c = Y["cerceve"]
        self.assertEqual(c[3] - c[1], 1100)
        #  Makine kaideye sığmazsa çizilmez:  dişli makine 1.320 uzun
        h = CKK.dogrula(_ornek(makine={"yeri": "Makine dairesi", "tip": "Dişli"},
                                makine_dairesi={"yan_yatak_boyu": 1100}))
        self.assertTrue(any("kaideye sığmıyor" in x and "yan_yatak_boyu" in x for x in h), h)
        self.assertEqual(CKK.dogrula(_ornek(makine={"yeri": "Makine dairesi", "tip": "Dişli"},
                                             makine_dairesi={"yan_yatak_boyu": 1200})), [])
        self.assertTrue(any("makine.yan_yatak" in x for x in CKK.dogrula(_ornek(makine={"yan_yatak": 210}))))

    def test_sarim_acisi_liftdesigner(self):
        """LiftDesigner 12744-3:  tahrik ø540, saptırma ø480 ( 560 yana, 842
        aşağıda ) → 'Sarim acisi 148';  saptırmasız 180."""
        for yon in (-1, 1):
            _, _, n = CMK_.teget((0, 0), 270, (yon * 560, -845), 240, yon)
            self.assertEqual(round(CMK_.sarim_acisi(yon, n)), 148)
            self.assertEqual(CMK_.sarim_acisi(yon, (yon, 0)), 180.0)

    def test_saptirma_kasnagi(self):
        """Halat aralığı kasnak çapından büyükse saptırma kasnağı halatı
        ağırlık kasnağının teğetine indirir ( delik de oraya );  çapı
        girilmezse ya da aralık küçükse reddedilir."""
        g = _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294)
        self.assertEqual(CKK.dogrula(g), [])
        Y = CMD.yerlesim(g)
        M = CKK.yerlesim(g)["M"]
        ex = Y["M"]["ex"]
        self.assertEqual(Y["agirlik_dusus"][0], ex)
        sp = Y["saptirma"]
        self.assertAlmostEqual(sp["x"] + sp["D"] / 2.0 * (-1 if g["agirlik"]["yeri"] == "Sol" else 1), ex)
        delik = dict(Y["delikler"])["AĞIRLIK"]
        self.assertAlmostEqual((delik[0] + delik[2]) / 2.0, ex)
        self.assertEqual(M["agirlik_dusus"][2] - M["oda_doseme"], 400)
        (P1, P2), = M["agirlik_yolu"]
        kmx = (Y["M"]["kasnak"][0] + Y["M"]["kasnak"][2]) / 2.0
        self.assertAlmostEqual(math.hypot(P1[0] - kmx, P1[2] - M["kasnak"][4]), 100.0)
        self.assertAlmostEqual(math.hypot(P2[0] - sp["x"], P2[2] - M["agirlik_dusus"][2]), 147.0)
        #  Halat iki kasnağı da ağırlık tarafından terk eder ( saptırma kasnağı
        #  tahrik kasnağının hemen altındayken 'üstteki teğet' yanlış yanı
        #  seçiyordu:  sarım 3,7° )
        y_ = -1 if g["agirlik"]["yeri"] == "Sol" else 1
        self.assertGreater(y_ * (P1[0] - kmx), 0)
        self.assertGreater(y_ * (P2[0] - sp["x"]), 0)
        self.assertTrue(90.0 < M["sarim_acisi"] < 180.0)
        on = CKK.on_kesit(g)
        self.assertTrue([x for x in on if x.get("ad") == "saptirma_kasnagi" and x["tip"] == "daire"])
        self.assertTrue([x for x in on if x.get("ad") == "sarim_acisi" and x["metin"] == f"SARIM AÇISI {M['sarim_acisi']:.0f}°"])
        self.assertTrue(any("saptirma_kasnak_capi" in h
                            for h in CKK.dogrula(_md(tip="Dişli", tahrik_kasnak_capi=200))))
        self.assertTrue(any("içeride" in h for h in CKK.dogrula(_md(tahrik_kasnak_capi=280))))

    def test_kaide_ayaklari_deliklere_basmaz(self):
        """Ayak plakası bir döşeme deliğine basan kaide önce uzun ekseninde
        kayar ( yan yatak boyu 700:  ortada ayak ağırlık bağlantısı deliğine
        basıyordu, 25 kayınca basmaz ), kayacak yer yoksa enine büyür ( boy
        294:  pay 100 → 200 )."""
        S = CS_.sabitler()
        for boy, kayar in ((700, True), (294, False)):
            g = _ornek(makine={"yeri": "Makine dairesi", "tahrik_kasnak_capi": 200, "saptirma_kasnak_capi": 294},
                       makine_dairesi={"yan_yatak_boyu": boy})
            with self.subTest(yan_yatak_boyu=boy):
                self.assertEqual(CKK.dogrula(g), [])
                Y = CMD.yerlesim(g)
                K, c = Y["kaide"], Y["cerceve"]
                a = CMK_.ayak_plakasi(K["E"], S)
                plakalar = [(x - a / 2.0, y - a / 2.0, x + a / 2.0, y + a / 2.0)
                            for x, y in CMK_.ayaklar(c, K["E"], K["F"], K["uzun_x"])]
                self.assertFalse([d for p in plakalar for _, d in Y["delikler"] if CKD._ortusur(p, d)])
                iz = (min(Y["makine_izi"][0], Y["saptirma"]["kutu"][0]),
                      min(Y["makine_izi"][1], Y["saptirma"]["kutu"][1]),
                      max(Y["makine_izi"][2], Y["saptirma"]["kutu"][2]),
                      max(Y["makine_izi"][3], Y["saptirma"]["kutu"][3]))
                self.assertFalse(K["uzun_x"])
                self.assertEqual(iz[0] - c[0] > S["md_cerceve_pay"], not kayar)
                self.assertEqual(abs((c[1] + c[3]) - (iz[1] + iz[3])) > 1e-6, kayar)
                #  Ortalı ve paysız yer gerçekten deliğe basıyordu
                o, b = (iz[1] + iz[3]) / 2.0, boy + K["E"]["h"]
                c0 = (iz[0] - 100, o - b / 2.0, iz[2] + 100, o + b / 2.0)
                p0 = [(x - a / 2.0, y - a / 2.0, x + a / 2.0, y + a / 2.0)
                      for x, y in CMK_.ayaklar(c0, K["E"], K["F"], False)]
                self.assertTrue([d for p in p0 for _, d in Y["delikler"] if CKD._ortusur(p, d)])

    def test_saptirma_kasnagi_baglantinin_ustunde(self):
        """Döşemedeki bağlantının üstüne düşerse 50 mm açık kalacak kadar yükselir."""
        from unittest import mock
        gercek = CMD.yerlesim

        def kaydir(g, S=None):
            Y = gercek(g, S)
            if Y.get("saptirma"):
                sk = Y["saptirma"]["kutu"]
                Y["M"] = dict(Y["M"], agirlik_baglanti=(sk[0], sk[1], sk[0] + 200, sk[1] + 100))
            return Y
        g = _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294)
        with mock.patch.object(CDN.CMD, "yerlesim", kaydir):
            M = CKK.yerlesim(g)["M"]
        S = CS_.sabitler()
        self.assertAlmostEqual(M["agirlik_dusus"][2] - M["oda_doseme"],
                               S["agirlik_baglanti_yukseklik"] + 50 + 147)

    def test_dxf_temiz(self):
        from cizim import dxf as CDX
        from ezdxf.audit import Auditor
        for g in (_ornek(), _md(tip="Dişli"), _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294)):
            for ciz in (CKK.on_kesit, CKK.yan_kesit, CMD.ciz):
                d = CDX.belge(ciz(g), "X", 20)
                au = Auditor(d)
                au.run()
                with self.subTest(ciz=ciz.__name__, tip=g["makine"]["tip"]):
                    self.assertEqual(list(au.errors), [])
from cizim import cizimler as CZ_           # noqa: E402


class OlcuYazisiParcayaBinmez(unittest.TestCase):
    """Hiçbir çizimde ölçü yazısı bir parçanın ( ray, konsol, şase, tampon,
    kasnak, merdiven, perde, makine, pano, paten ) ya da bir etiketin üstüne
    düşmez.  Kuyu planında kabin duvarının "75"i şase dikmesinin, kuyu
    dibinde Yatarak sığınmanın "1000"i kabin tamponunun üstündeydi."""

    def test_butun_cizimler(self):
        projeler = [("örnek", _ornek()), ("sağ", _sag_ayna()), ("arka", _arka()),
                    ("makine dairesi", _ornek(makine={"yeri": "Makine dairesi"})),
                    ("yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
                    ("dik duruş", _ornek(kabin_ustu={"siginma_tipi": "Dik duruş"}))]
        sayi = 0
        for ad, g in projeler:
            for cizim, (dogrula, ciz, _) in CZ_.CIZIMLER.items():
                if dogrula(g):
                    continue
                e = ciz(g)
                engel = [CGE.sinir([x]) for x in e if x["katman"] in CGE.PARCA_KATMANLARI
                         or (x["tip"] == "yazi" and x["katman"] == "YAZI")
                         or x.get("ad") == "yuk_kutusu"]
                for o in e:
                    if o["tip"] != "olcu":
                        continue
                    y_ = o["yazi"]
                    w, h = CGE._yazi_eni(o["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                    if y_["aci"]:
                        w, h = h, w
                    k = (y_["x"] - w, y_["y"] - h, y_["x"] + w, y_["y"] + h)
                    sayi += 1
                    with self.subTest(proje=ad, cizim=cizim, olcu=o["metin"]):
                        self.assertFalse([b for b in engel if CKD._ortusur(k, b)])
        self.assertGreater(sayi, 500)


class Pafta(unittest.TestCase):
    """Çizimlerin ofisin TİP PROJE FORMATINA yerleştirilmesi."""

    @classmethod
    def setUpClass(cls):
        cls.d, cls.bilgi = CPF.belge(_ornek())
        cls.d_md, cls.bilgi_md = CPF.belge(_ornek(makine={"yeri": "Makine dairesi"}))

    def test_onizlemede_blok_taramasi_olcekli(self):
        """Önizleme ( pafta PDF'i ) ölçekli bloktaki taramayı bloksuz hâliyle
        aynı sıklıkta çizer — ezdxf 1.4 deseni ölçeklemiyor, 1/50 kesitte
        duvarda tek çizgi kalıyordu;  asıl belgeye dokunulmaz."""
        import re
        import ezdxf
        sayilar = []
        for olcek in (None, 1.0, 1 / 50.0, 1 / 20.0):
            d = ezdxf.new("R2018")
            hedef = d.modelspace() if olcek is None else d.blocks.new("B")
            h = hedef.add_hatch(color=8)
            h.set_pattern_fill("ANSI31", scale=50)
            #  Büyük alan:  ezdxf'in seyrek deseni de birkaç çizgi verir ( çift çizim yakalanır )
            h.paths.add_polyline_path([(0, 26000), (30000, 26000), (30000, 38000), (0, 38000)], is_closed=True)
            if olcek is not None:
                d.modelspace().add_blockref("B", (0, 0), dxfattribs={"xscale": olcek, "yscale": olcek})
            svg = CPF.onizleme(d)
            sayilar.append(sum(p.count("m") + p.count("M") for p in re.findall(r'<path d="([^"]*)"', svg)))
            self.assertEqual([e.dxftype() for e in d.modelspace()], ["HATCH" if olcek is None else "INSERT"])
        self.assertGreater(sayilar[0], 10)
        self.assertEqual(len(set(sayilar)), 1, sayilar)

    def test_cizimler_ve_olcekler(self):
        #  Düşey kesit yalnız tam boy A-A / B-B;  kuyu dibi ve kuyu üstü / makine
        #  dairesi YATAY kesittir ( ofisin 477-8 ve 12744-3 paftaları gibi )
        self.assertEqual([c["ad"] for c in self.bilgi["cizimler"]],
                         ["kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu",
                          "kuyu_dibi", "kuyu_ustu"])
        self.assertEqual([c["ad"] for c in self.bilgi_md["cizimler"]],
                         ["kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu",
                          "kuyu_dibi", "makine_dairesi", "delik_plani"])
        bloklar = {e.dxf.name: e for e in self.d.modelspace().query("INSERT")
                   if e.dxf.name.startswith("CIZIM_")}
        for c in self.bilgi["cizimler"]:
            with self.subTest(ad=c["ad"]):
                i = bloklar["CIZIM_" + c["ad"].upper()]
                self.assertAlmostEqual(i.dxf.xscale, 1.0 / c["olcek"])
                self.assertEqual(c["olcek"], 50 if c["ad"].startswith("kuyu_kesiti") else 20)

    def test_cizimler_serbest_alanda_ve_ust_uste_binmez(self):
        import itertools
        for bilgi in (self.bilgi, self.bilgi_md):
            kutular = [c["kutu"] for c in bilgi["cizimler"]]
            for k in kutular:
                self.assertGreaterEqual(k[0], CPF.SERBEST[0] + CPF.KENAR - 1e-6)
                self.assertLessEqual(k[2], bilgi["sag"] - CPF.KENAR + 1e-6)
                self.assertGreaterEqual(k[1], CPF.SERBEST[1] + CPF.KENAR - 1e-6)
                self.assertLessEqual(k[3], CPF.SERBEST[3] - CPF.KENAR + 1e-6)
            for a, b in itertools.combinations(kutular, 2):
                self.assertFalse(a[0] < b[2] + CPF.ARA - 1e-6 and b[0] < a[2] + CPF.ARA - 1e-6 and
                                 a[1] < b[3] + CPF.ARA - 1e-6 and b[1] < a[3] + CPF.ARA - 1e-6, (a, b))

    def test_antet(self):
        yazilar = {e.dxf.text for e in self.d.modelspace().query("TEXT")}
        for beklenen in ("1,00 m/sn", "8 DURAK", "21000", "1350", "1400", "2:1", "89*62", "1/20 1/50"):
            self.assertIn(beklenen, yazilar)
        #  Çizimin bilmediği değerler boş:  şablonun örnekleri kalmaz
        for ornek in ("300 KG (4 KİŞİ)", "Sınıf I", "2,67 KW", "0,1/2 DURAK", "70*70*9"):
            self.assertNotIn(ornek, yazilar)

    def test_yerlesim_ve_cerceve_uzatma(self):
        #  Sığan yerleşim çerçeveyi uzatmaz;  sığmayan sağa uzatır ( aşağı taşmaz )
        yerler, sag = CPF.yerlesim([(200, 400)] * 3)
        self.assertEqual(sag, CPF.SERBEST[2])
        yerler, sag = CPF.yerlesim([(400, 400)] * 9)
        self.assertGreater(sag, CPF.SERBEST[2])
        self.assertTrue(all(y >= CPF.SERBEST[1] + CPF.KENAR - 1e-6 for _, y in yerler))
        import ezdxf
        d = ezdxf.readfile(CPF.SABLON)
        CPF._cerceveyi_uzat(d, sag)
        xs = {round(p.x, 1) for e in d.modelspace().query("LINE") for p in (e.dxf.start, e.dxf.end)}
        self.assertIn(round(sag, 1), xs)
        self.assertNotIn(round(CPF.BANT[2], 1), xs)

    def test_sablon_degisirse_durur(self):
        import ezdxf
        d = ezdxf.readfile(CPF.SABLON)
        CPF._sablon_dogrula(d)
        CPF._antet_yazisi(d, CPF.ANTET["hiz"][1]).dxf.insert = (0, 0)
        with self.assertRaises(ValueError):
            CPF._sablon_dogrula(d)

    def test_dxf_gecerli(self):
        import tempfile
        import ezdxf
        from ezdxf.audit import Auditor
        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"})):
            with tempfile.TemporaryDirectory() as k:
                yol = os.path.join(k, "p.dxf")
                open(yol, "wb").write(CPF.yaz(g))
                d = ezdxf.readfile(yol)
                au = Auditor(d)
                au.run()
                self.assertEqual(list(au.errors), [])

    def test_katman_baglantilari_gecerli(self):
        #  AutoCAD AUDIT ( AcCoreConsole ):  şablonun dört katmanı olmayan malzeme /
        #  çizim stilini gösteriyordu — 16 hata.  Her katman geçerli kayda bağlı.
        db = self.d.entitydb
        for k in self.d.layers:
            with self.subTest(katman=k.dxf.name):
                self.assertEqual(db.get(k.dxf.material_handle).dxftype(), "MATERIAL")
                self.assertEqual(db.get(k.dxf.plotstyle_handle).dxftype(), "ACDBPLACEHOLDER")

    def test_girdi_hatasinda_pafta_uretilmez(self):
        with self.assertRaises(ValueError):
            CPF.belge(_ornek(dusey={"kabin_konsol_arasi": 0}))


class KapiBolgesi(unittest.TestCase):
    """Kat kapısı ve kabin kapısı ( ELEport kuyu planı vektörleri ve kapı detayı )."""

    def _kutular(self, e, ad):
        return [(x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"]) for x in e if x.get("ad") == ad]

    def test_tarama_kapi_boslugundan_gecmez(self):
        """Kapının olduğu duvar boşluğun iki yanında iki parça:  hiçbir çizimde
        tarama bir kapı parçasına ( boşluk, kasa, oda kapısı ) binmez.  Kuyu
        planında ön duvarın, makine dairesi planında oda duvarının taraması
        kapı boşluğundan geçiyordu ( DWG'de de ).  Kapı hizasından kesilmeyen
        planlarda ön duvar kesintisizdir."""
        from cizim import cizimler as CZ
        projeler = [_ornek(), _ornek(kapi={"montaj": "Duvar boşluğuna"}, kabin={"on_pay": 210})] + [
            _ornek(makine={"yeri": "Makine dairesi"},
                   makine_dairesi={"kapi_duvar": d, "pano_duvar": "Sol" if d == "Sağ" else "Sağ"})
            for d in ("Ön", "Arka", "Sol", "Sağ")]
        sayi = 0
        for g in projeler:
            for cizim, (dogrula, ciz, _) in CZ.CIZIMLER.items():
                self.assertEqual(dogrula(g), [], cizim)
                e = ciz(g)
                tarama = [(x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"]) for x in e
                          if x["tip"] in ("tarama", "tarama_tugla")]
                kapi = [(x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"]) for x in e
                        if x["katman"] == "KAPI" and x["tip"] == "dikdortgen"]
                for t in tarama:
                    for k in kapi:
                        sayi += 1
                        with self.subTest(cizim=cizim, montaj=g["kapi"]["montaj"],
                                          oda_kapisi=g["makine_dairesi"]["kapi_duvar"], tarama=t, kapi=k):
                            self.assertFalse(t[0] < k[2] - 1e-6 and k[0] < t[2] - 1e-6
                                             and t[1] < k[3] - 1e-6 and k[1] < t[3] - 1e-6)
        self.assertGreater(sayi, 100)
        #  Ön duvar:  kapı hizasında boşluğun ( kuyu içine montaj:  kapı eni ) iki
        #  yanında;  kabin üstü, kuyu dibi, kuyu üstü ve delik planında kesintisiz
        k, kp = CG.ORNEK["kuyu"], CG.ORNEK["kapi"]
        self.assertEqual(kp["montaj"], "Kuyu içine")

        def on_duvar(e):
            return sorted((x["x"], x["x"] + x["g"]) for x in e if x["tip"] == "tarama" and x["y"] == -k["duvar_on"])
        self.assertEqual(on_duvar(CGE.plan(_ornek())),
                         [(-k["duvar_sol"], kp["sol_pay"]),
                          (kp["sol_pay"] + kp["genislik"], k["genislik"] + k["duvar_sag"])])
        for cizim in ("kabin_ustu", "kuyu_dibi", "kuyu_ustu", "delik_plani"):
            with self.subTest(cizim=cizim):
                self.assertEqual(on_duvar(CZ.CIZIMLER[cizim][1](_ornek())),
                                 [(-k["duvar_sol"], k["genislik"] + k["duvar_sag"])])

    def test_kanatlar_esiklerin_ustunde_kabinle_cakismaz(self):
        for g in (_ornek(), _ornek(kapi={"montaj": "Duvar boşluğuna"}, kabin={"on_pay": 210}),
                  _ornek(kapi={"tip": "Otomatik Merkezi"}), _sag_ayna(), _arka()):
            self.assertEqual(CG.dogrula(g), [])
            e = CGE.plan(g)
            kabin = self._kutular(e, "kabin_dis")[0]
            for kanat, esik in (("kat_kanadi", "kat_esigi"), ("kabin_kanadi", "kabin_esigi")):
                es = self._kutular(e, esik)[0]
                for k in self._kutular(e, kanat):
                    with self.subTest(montaj=g["kapi"]["montaj"], tip=g["kapi"]["tip"], kanat=kanat):
                        self.assertTrue(es[1] - 1e-9 <= k[1] and k[3] <= es[3] + 1e-9, (k, es))
                        #  Kanat kabin gövdesinin içine girmez
                        self.assertLessEqual(k[3], kabin[1] + 1e-9)

    def test_montaj_yerleri(self):
        S = CS_.sabitler()
        for montaj, kasa, esik, hat in (("Duvar boşluğuna", (-60, 0), (0, 90), 90),
                                        ("Kuyu içine", (0, 60), (60, 150), 150)):
            KB = CG.kapi_bolgesi(_ornek(kapi={"montaj": montaj}), S)
            self.assertEqual((KB["kasa"], KB["esik"], KB["hat"]), (kasa, esik, hat))
        self.assertTrue(any("kapi.montaj" in h for h in CG.dogrula(_ornek(kapi={"montaj": "Havada"}))))

    def test_esik_araligi_ve_kuyu_yuzu_sinirlari(self):
        #  Kabin eşiği 90;  duvar boşluğunda kapı hattı 90 → aralık on_pay − 180
        #  ( 0 < … ≤ 35:  181 – 215 );  kuyu içinde hat 150 → on_pay − 240 ( 241 – 275 ).
        for montaj, alt, ust in (("Duvar boşluğuna", 180, 215), ("Kuyu içine", 240, 275)):
            for on, uygun in ((alt, False), (alt + 1, True), (ust, True), (ust + 1, False)):
                h = CG.dogrula(_ornek(kapi={"montaj": montaj}, kabin={"on_pay": on}))
                with self.subTest(montaj=montaj, on_pay=on):
                    self.assertEqual(not any("eşiğ" in x for x in h), uygun, h)

    def test_eleport_kapi_zinciri(self):
        #  ELEport:  iç yüzden kapı hattına 150, oradan ray eksenine 1.017,
        #  ray ekseninden arka iç yüze 682 ( 150 + 1.017 + 682 = 1.849 ≈ 1.850 )
        g = _ornek()
        KB = CG.kapi_bolgesi(g, CS_.sabitler())
        ry = g["kabin_ray"]["kapi_arasi"]
        self.assertEqual(KB["hat"], 150)
        self.assertEqual(ry - KB["hat"], 1017)
        self.assertAlmostEqual(g["kuyu"]["derinlik"] - ry, 682, delta=1)
        metinler = {x["metin"] for x in CGE.plan(g) if x["tip"] == "olcu"}
        self.assertIn("KAT KAPISI 150", metinler)
        self.assertIn("KABİN EŞİĞİ 90", metinler)


if __name__ == "__main__":
    unittest.main(verbosity=2)
