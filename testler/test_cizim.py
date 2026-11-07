# -*- coding: utf-8 -*-
"""
TEST 15 — ÇİZİM MODÜLÜ  ( hesap motorundan bağımsız )

Çizim piksel piksel değil, GEOMETRİ olarak denetlenir:
  · ölçü zincirleri kapanıyor mu  ( parçaların toplamı = toplam ölçü )
  · her parça kuyunun içinde mi
  · kabin ile karşı ağırlık / raylar çakışıyor mu
  · girdi sözleşmesi eksik ya da tutarsız girdiyi reddediyor mu
"""

import collections
import os
import math
import re
import unittest
from unittest import mock


from temel import kutu_merkezi, ortusur
from cizim import eleman
from cizim import geometri
from cizim import girdi
from cizim import parca_adlari
from cizim import svg
from cizim import sabitler
from cizim import uslup
from cizim import parca_kotlari
from cizim import standart


def _ornek(**ezme):
    g = {k: (dict(v) if isinstance(v, dict) else v) for k, v in girdi.ORNEK.items()}
    for bolum, d in ezme.items():
        g[bolum].update(d)
    return g


def _duvar_boslugu():
    """Kapısı duvar boşluğuna monte örnek.  Referans projenin kendi kapısı kuyu
    içindedir ve üst payı 200'dür:  220'lik kasa ( LiftDesigner ) duvardaki
    boşluğa sığmaz ( geometri.dogrula ) — LiftDesigner'ın 240'ıyla."""
    return _ornek(
        kapi={"montaj": "Duvar boşluğuna"}, kabin={"on_pay": 210}, _cizim_sabitleri={"kapi_ust_payi": 240}
    )


def _sag_ayna(**ezme):
    """Örneğin aynası:  ağırlık sağda, kabin ve kapı simetrik yerde;  kapı da
    aynadır — sağa açılır ( sola açılan kapının kanat cebi sol duvara 470'te
    sığmaz:  480 gerekir — girdi.kanat_cepleri )."""
    g = _ornek(
        agirlik={"yeri": "Sağ"},
        kabin={"kaciklik_y": -130},
        kapi={"sol_pay": 2100 - 730 - 900, "tip": "Teleskopik Sağ"},
    )
    for bolum, d in ezme.items():
        g[bolum].update(d)
    return g


def _dikdortgenler(elemanlar, katman):
    return [el for el in elemanlar if el["tip"] == "dikdortgen" and el["katman"] == katman]


def _cakisma(a, b, pay=0.0):
    return (
        a["x"] + a["g"] - pay > b["x"]
        and b["x"] + b["g"] - pay > a["x"]
        and a["y"] + a["d"] - pay > b["y"]
        and b["y"] + b["d"] - pay > a["y"]
    )


class SozlesmeDenetimi(unittest.TestCase):
    def test_ornek_gecerli(self):
        self.assertEqual(geometri.dogrula(_ornek()), [])

    def test_eksik_bolum_reddedilir(self):
        g = _ornek()
        g.pop("kapi")
        self.assertTrue(any("kapi" in h for h in geometri.dogrula(g)))

    def test_sifir_ve_negatif_olcu_reddedilir(self):
        for bolum, alan in (("kuyu", "genislik"), ("kabin", "derinlik"), ("kapi", "genislik")):
            self.assertTrue(geometri.dogrula(_ornek(**{bolum: {alan: 0}})), (bolum, alan))
            self.assertTrue(geometri.dogrula(_ornek(**{bolum: {alan: -100}})), (bolum, alan))

    def test_kabin_kuyuya_sigmazsa_reddedilir(self):
        self.assertTrue(geometri.dogrula(_ornek(kabin={"genislik": 2500})))
        self.assertTrue(geometri.dogrula(_ornek(kabin={"derinlik": 2500})))

    def test_kapi_kuyuya_sigmazsa_reddedilir(self):
        self.assertTrue(geometri.dogrula(_ornek(kapi={"sol_pay": 1500})))

    def test_agirlik_yeri_secenekleri(self):
        self.assertTrue(geometri.dogrula(_ornek(agirlik={"yeri": "Ortada"})))
        for yer in girdi.AGIRLIK_YERLERI:
            g = {"Sağ": _sag_ayna, "Arka": _arka}.get(yer, lambda yer=yer: _ornek(agirlik={"yeri": yer}))()
            self.assertEqual(geometri.dogrula(g), [])


class PlanGeometrisi(unittest.TestCase):
    def setUp(self):
        self.g = _ornek()
        self.e = geometri.plan(self.g)

    def test_olcu_zincirleri_kapaniyor(self):
        for z in geometri.zincirler(self.e):
            self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"], places=6, msg=f"zincir kapanmadı: {z}")

    def test_her_zincirde_en_az_bir_olcu(self):
        self.assertGreaterEqual(len(geometri.zincirler(self.e)), 6)

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
        self.assertAlmostEqual(
            max(el["x"] + el["g"] for el in sag), kx + kr["arasi"] / 2.0 + kr["h"], places=6
        )

    def test_hicbir_donanim_kuyu_disina_tasmaz(self):
        k = self.g["kuyu"]
        for kat in ("KABIN", "KABIN-IC", "SASE", "KASNAK", "AGIRLIK", "PATEN", "RAY", "KONSOL"):
            for el in _dikdortgenler(self.e, kat):
                self.assertGreaterEqual(round(el["x"], 6), 0, (kat, el))
                self.assertGreaterEqual(round(el["y"], 6), 0, (kat, el))
                self.assertLessEqual(round(el["x"] + el["g"], 6), k["genislik"], (kat, el))
                self.assertLessEqual(round(el["y"] + el["d"], 6), k["derinlik"], (kat, el))

    def test_konsol_plakasi_duvara_dayaniyor(self):
        k = self.g["kuyu"]
        plakalar = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "plaka"]
        #  2 ağırlık rayı + ağırlığın OLMADIĞI yandaki kabin rayı;  öbür kabin
        #  rayı ağırlık konsollarına bağlı ara kirişte durur.
        self.assertEqual(len(plakalar), 3)
        for el in plakalar:
            duvarda = abs(el["x"]) < 1e-6 or abs(el["x"] + el["g"] - k["genislik"]) < 1e-6
            self.assertTrue(duvarda, f"konsol plakası duvara dayanmıyor: {el}")

    def test_konsol_kolu_plaka_ile_rayi_birlestiriyor(self):
        """Kabin konsolunun kolu plakaya ve rayın arkasına;  ağırlık konsolunun
        kolu plakaya ve kabin rayının ara kirişine değmeli."""

        S = sabitler.sabitler(self.g.get("_cizim_sabitleri"))
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        sag_ray_arkasi = round(kx + kr["arasi"] / 2.0 + kr["h"], 3)
        sol_ray_arkasi = round(kx - kr["arasi"] / 2.0 - kr["h"], 3)
        kiris = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "ara_kiris"]
        self.assertEqual(len(kiris), 1)
        self.assertAlmostEqual(kiris[0]["x"] + kiris[0]["g"], sol_ray_arkasi)
        kollar = [el for el in _dikdortgenler(self.e, "KONSOL") if el.get("ad") == "kol"]
        self.assertEqual(len(kollar), 3)  # 1 kabin + 2 ağırlık
        for el in kollar:
            uclar = {round(el["x"], 3), round(el["x"] + el["g"], 3)}
            if el["x"] > kx:  # kabin konsolu  ( sağ duvar )
                self.assertIn(sag_ray_arkasi, uclar)
                self.assertIn(round(k["genislik"] - S["konsol_kabin_en"], 3), uclar)
            else:  # ağırlık konsolu → ara kiriş
                self.assertIn(round(S["konsol_agirlik_en"], 3), uclar)
                self.assertIn(round(kiris[0]["x"], 3), uclar)

    def test_paten_ray_yuzunu_kavriyor(self):
        kr, kb, k = self.g["kabin_ray"], self.g["kabin"], self.g["kuyu"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        for el in _dikdortgenler(self.e, "PATEN"):
            if el.get("ad") == "agirlik_pateni":
                continue
            merkez = el["x"] + el["g"] / 2.0
            self.assertIn(
                round(merkez, 3), (round(kx - kr["arasi"] / 2.0, 3), round(kx + kr["arasi"] / 2.0, 3))
            )
        #  Karşı ağırlığın patenleri ( 8 Eki'den planda ):  ağırlık raylarının dil uçlarında
        ag = self.g["agirlik"]
        ag_y = kr["kapi_arasi"] + ag["eksen_kaciklik"]
        uclar = {round(ag_y - ag["ray_arasi"] / 2.0, 3), round(ag_y + ag["ray_arasi"] / 2.0, 3)}
        pt = [el for el in _dikdortgenler(self.e, "PATEN") if el.get("ad") == "agirlik_pateni"]
        self.assertEqual({round(el["y"] + el["d"] / 2.0, 3) for el in pt}, uclar)

    def test_kabin_kasnaklari_girdideki_aralikta(self):

        S = sabitler.sabitler(self.g.get("_cizim_sabitleri"))
        kb, k, a = self.g["kabin"], self.g["kuyu"], self.g["aski"]
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        beklenen = {round(kx - a["kasnak_arasi"] / 2.0, 3), round(kx + a["kasnak_arasi"] / 2.0, 3)}
        #  Kuyu planında kabin altı kasnakları kesik çizgilidir ( GIZLI ):  adıyla
        merkezler = {
            round(el["x"] + el["g"] / 2.0, 3)
            for el in self.e
            if el.get("ad") == "kabin_kasnak" and round(el["d"]) == round(S["kabin_kasnak_genislik"])
        }
        self.assertEqual(merkezler, beklenen)

    def test_kapi_kasasi_boslugun_iki_yaninda(self):

        S = sabitler.sabitler(self.g.get("_cizim_sabitleri"))
        kp = self.g["kapi"]
        kasalar = [el for el in _dikdortgenler(self.e, "KAPI") if round(el["g"]) == round(S["kasa_yan"])]
        self.assertEqual(len(kasalar), 2)
        yerler = sorted(round(el["x"]) for el in kasalar)
        self.assertEqual(
            yerler, sorted([round(kp["sol_pay"] - S["kasa_yan"]), round(kp["sol_pay"] + kp["genislik"])])
        )

    def test_kabin_ile_agirlik_cakismiyor(self):
        kabin = _dikdortgenler(self.e, "KABIN")[0]
        for ag in _dikdortgenler(self.e, "AGIRLIK"):
            self.assertFalse(_cakisma(kabin, ag), f"kabin ile karşı ağırlık çakışıyor: {ag}")

    def test_kapi_boslugu_on_duvarda(self):
        #  Duvardaki kaba boşluk kapıdan iki yanda 140 geniş ( LiftDesigner
        #  800 KG planı:  900'lük kapıya 1.180 — giriş görünüşüyle aynı );  ön
        #  duvarın iki parçası boşluğun iki yanında biter.
        k, kp = self.g["kuyu"], self.g["kapi"]
        S = sabitler.sabitler(self.g["_cizim_sabitleri"])
        bosluk = next(x for x in self.e if x.get("ad") == "kapi_boslugu")
        self.assertAlmostEqual(bosluk["x"], kp["sol_pay"] - S["kaba_bosluk_yan_payi"], places=6)
        self.assertAlmostEqual(bosluk["g"], kp["genislik"] + 2 * S["kaba_bosluk_yan_payi"], places=6)
        self.assertAlmostEqual(bosluk["y"], -k["duvar_on"], places=6)
        duvar = [x for x in _dikdortgenler(self.e, "KUYU-DUVAR") if x["y"] == -k["duvar_on"]]
        self.assertEqual(sorted(round(x["x"] + x["g"]) for x in duvar)[0], round(bosluk["x"]))
        self.assertIn(round(bosluk["x"] + bosluk["g"]), [round(x["x"]) for x in duvar])

    def test_kasa_duvar_boslugunda_sigmali(self):
        g = _ornek(kapi={"montaj": "Duvar boşluğuna"}, kabin={"on_pay": 210})
        self.assertTrue(any("kaba boşluğa sığmıyor" in h for h in geometri.dogrula(g)))
        self.assertEqual(geometri.dogrula(_duvar_boslugu()), [])

    def test_agirlik_yeri_cizimi_degistiriyor(self):
        sol = _dikdortgenler(geometri.plan(_ornek(agirlik={"yeri": "Sol"})), "AGIRLIK")[0]
        sag = _dikdortgenler(geometri.plan(_ornek(agirlik={"yeri": "Sağ"})), "AGIRLIK")[0]
        arka = _dikdortgenler(geometri.plan(_ornek(agirlik={"yeri": "Arka"})), "AGIRLIK")[0]
        self.assertLess(sol["x"], sag["x"])
        self.assertGreater(arka["y"], sol["y"])

    def test_sinir_butun_elemanlari_kapsiyor(self):
        x1, y1, x2, y2 = geometri.sinir(self.e)
        for el in _dikdortgenler(self.e, "KUYU-DUVAR"):
            self.assertGreaterEqual(el["x"], x1)
            self.assertLessEqual(el["x"] + el["g"], x2)
            self.assertGreaterEqual(el["y"], y1)
            self.assertLessEqual(el["y"] + el["d"], y2)


class SvgCiktisi(unittest.TestCase):
    def setUp(self):
        self.e = geometri.plan(_ornek())
        self.s = svg.yaz(self.e, geometri.sinir(self.e, 250), "KUYU PLANI", 20)

    def test_ekranin_svgsi_dxf_renkleriyle(self):
        #  Ekranın tuvali AutoCAD'in koyu model alanı gibi ( kullanıcı kararı 13 Eki ):
        #  katman renkleri DXF'inki, zemin / örtü / hale AutoCAD zemini;  kâğıt siyahı yok
        s = svg.yaz(self.e, geometri.sinir(self.e, 250), "", 20, onek="c0-", etkilesimli=True, r=svg.CAD)
        self.assertIn(f'fill="{uslup.CAD_ZEMIN}"', s)
        for katman in ("KAPI", "RAY", "OLCU", "EKSEN", "KUYU-DUVAR"):
            self.assertIn(f'stroke="{uslup.cad_rengi(katman)}"', s, katman)
        self.assertNotIn(uslup.SIYAH, s)
        #  Yazının halesi zemin renginde ( kâğıtta beyaz )
        self.assertIn(f'stroke="{uslup.CAD_ZEMIN}" stroke-width', s)

    def test_ekrandaki_svgde_olcu_aciklamasi_baslik_olmaz(self):
        #  Ekranın SVG'si başlıksızdır;  ölçünün açıklaması ( <title> ) başlığın
        #  yerine çizimin altına yazılıyordu — değişken adı parametreyi eziyordu ( 13 Eki )
        #  ( son ölçü kodlu olunca:  kesitlerde SD / SW )
        e = [eleman.olcu("yatay", (0, 0), (2100, 0), 500, "SW2100")]
        geometri.yazilari_yerlestir(e)
        s = svg.yaz(e, geometri.sinir(e, 250), "", 20, onek="c0-", etkilesimli=True)
        self.assertIn("<title>Kuyu iç genişliği</title>", s)
        self.assertNotIn("&lt;title&gt;", s)

    def test_ekrandaki_parcalar_adli(self):
        #  Müdahale ( 13 Eki ):  ekranda parçanın üstüne gelince adı yazar, aynı parça
        #  örneğinin bütün çizgileri vurgulanır — elemanlar katmanı ve örneğiyle
        #  ( geometri.parca_ornekleri, DXF bloğuyla aynı ) işaretli;  kâğıt değişmez
        s = svg.yaz(self.e, geometri.sinir(self.e, 250), "", 20, onek="c0-", etkilesimli=True, r=svg.CAD)
        self.assertIn('data-ad="Kabin rayı"', s)
        self.assertIn('data-katman="KUYU-DUVAR"', s)
        self.assertEqual(
            len(set(re.findall(r'data-parca="([^"]+)"', s))), len(geometri.parca_ornekleri(self.e))
        )
        self.assertNotIn("data-parca", self.s)
        self.assertNotIn("data-katman", self.s)

    def test_parca_adi_tabloda_yoksa_okunur(self):
        self.assertEqual(parca_adlari.ad("kabin_rayi"), "Kabin rayı")
        self.assertEqual(parca_adlari.ad("yeni_parca"), "Yeni parca")

    def test_svg_gecerli_bicimde(self):
        self.assertTrue(self.s.startswith("<svg"))
        self.assertTrue(self.s.rstrip().endswith("</svg>"))
        self.assertEqual(self.s.count("<svg"), 1)

    def test_yazilar_haleli_ve_cizgilerden_sonra(self):
        """DXF'teki maskenin ekrandaki karşılığı:  her yazının çevresinde zemin
        renginde hale, yazılar bütün çizgilerden sonra çizilir."""
        self.assertEqual(self.s.count("<text"), self.s.count('paint-order="stroke"'))
        #  İlk yazıdan sonra yalnız ölçülerin kendi çizgileri ve yazılar
        sonra = self.s[self.s.index("<text") :]
        for parca in ("<rect", "<circle", "<polygon"):
            self.assertNotIn(parca, sonra)
        self.assertIsNotNone(re.search(r"<text[^>]*>CW1350</text>", sonra))

    def test_etiket_ortasindan_hizali(self):
        """Geometri etiketin ORTASINI verir ( DXF'te MIDDLE ):  SVG taban
        çizgisini 0,35·h aşağı koyar.  Eskiden etiketler ekranda 0,35·h
        yukarıdaydı."""
        el = eleman.yazi(1000, 2000, "DENEME", 60)
        s = svg.yaz([el], (0, 0, 3000, 3000), "", 20)
        self.assertIn(f"translate(1000.0,{2000 - 0.35 * el['yukseklik']:.1f})", s)

    def test_bilinen_olculer_yaziya_giriyor(self):
        for beklenen in ("SW2100", "SD1850", "DBG1550", "DW900", "KUYU PLANI"):
            self.assertIn(beklenen, self.s, beklenen)

    def test_her_katman_bir_kalem_tanimli(self):
        katmanlar = {el["katman"] for el in self.e}
        for kat in katmanlar:
            self.assertIn(kat, uslup.KATMAN, kat)


def _dxf_varliklari(d, yer):
    """Yerleşimin varlıkları, parça blokları ( geometri.parca_ornekleri ) açılarak:
    adı olan parçanın her örneği kendi bloğundadır ( 13 Eki )."""
    for e in yer:
        if e.dxftype() == "INSERT":
            yield from _dxf_varliklari(d, d.blocks.get(e.dxf.name))
        else:
            yield e


class ParcaBloklari(unittest.TestCase):
    """Adı olan parçanın her örneği DXF'te kendi adlı bloğunda ( 13 Eki — çizim
    kalitesi 6. adımı;  LiftDesigner'ın paftalarında her parça bloktur ):
    AutoCAD'de tıklanınca bütün parça seçilir.  Çizgiler yerinde kalır."""

    def setUp(self):
        from cizim import dxf

        self.CDX = dxf
        self.e = geometri.plan(_ornek())
        self.d = dxf.belge(self.e, "KUYU PLANI", 20)

    def _duz(self, d):
        out = collections.Counter()
        for e in _dxf_varliklari(d, d.modelspace()):
            n = e.dxf
            yer = (
                (round(n.start.x, 2), round(n.start.y, 2), round(n.end.x, 2), round(n.end.y, 2))
                if e.dxftype() == "LINE"
                else tuple(round(v, 2) for q in e.get_points("xy") for v in q)
                if e.dxftype() == "LWPOLYLINE"
                else ()
            )
            out[(e.dxftype(), n.layer, n.get("linetype", ""), round(n.get("ltscale", 1.0), 3), yer)] += 1
        return out

    def test_her_ornek_kendi_blogunda(self):
        bloklar = {i.dxf.name for i in self.d.modelspace().query("INSERT")}
        #  İki kabin rayı iki ayrı örnek ( flanş ve gövde aynı bloğun içinde )
        self.assertEqual(
            sorted(b for b in bloklar if b.startswith("PARCA_KABIN_RAY_")),
            ["PARCA_KABIN_RAY_1", "PARCA_KABIN_RAY_2"],
        )
        for ad in bloklar:
            for e in self.d.blocks.get(ad):
                with self.subTest(blok=ad):
                    self.assertNotIn(e.dxf.layer, geometri.BLOKSUZ_KATMANLAR)

    def test_bloklar_acilinca_cizim_ayni(self):
        bloklu = self._duz(self.d)
        with mock.patch.object(geometri, "parca_ornekleri", lambda e: []):
            bloksuz = self._duz(self.CDX.belge(self.e, "KUYU PLANI", 20))
        self.assertEqual(bloklu, bloksuz)
        self.assertGreater(sum(bloklu.values()), 100)


class DxfCiktisi(unittest.TestCase):
    """CAD çıktısı:  AutoCAD'in açabildiği, katmanlı ve GERÇEK ölçü varlıklı."""

    def setUp(self):
        from cizim import dxf

        self.CDX = dxf
        self.g = _ornek()
        self.e = geometri.plan(self.g)
        self.d = dxf.belge(self.e, "KUYU PLANI", 20)

    def test_denetimden_temiz_geciyor(self):
        from ezdxf.audit import Auditor

        denet = Auditor(self.d)
        denet.run()
        self.assertEqual(list(denet.errors), [])

    def test_yazilar_maskeli_ve_cizgilerden_sonra(self):
        """Çizgi yazının üstünden geçmez ( ISO 128 ):  etiketin arkası zemin
        rengiyle örtülür ( MTEXT arka planı ), ölçü yazısınınki dimtfill.  Örtü
        yalnız kendinden önce çizileni örter:  yazılar çizgilerden SONRA."""
        msp = self.d.modelspace()
        etiketler = list(msp.query("MTEXT"))
        self.assertTrue(etiketler)
        for m in etiketler:
            self.assertEqual(m.dxf.bg_fill & 2, 2, m.plain_text())  # zemin rengi
            self.assertEqual(m.dxf.box_fill_scale, self.CDX.MASKE_PAYI)
        for dim in msp.query("DIMENSION"):
            self.assertEqual(dim.override().get("dimtfill"), 1)
        tur = [e.dxftype() for e in msp if e.dxftype() != "TEXT"]  # belge başlığı ayrı
        son_cizgi = max(i for i, t in enumerate(tur) if t not in ("MTEXT", "DIMENSION"))
        ilk_yazi = min(i for i, t in enumerate(tur) if t in ("MTEXT", "DIMENSION"))
        self.assertLess(son_cizgi, ilk_yazi)
        self.assertLess(
            max(i for i, t in enumerate(tur) if t == "DIMENSION"),
            min(i for i, t in enumerate(tur) if t == "MTEXT"),
        )

    def test_cizgi_deseni_paftada_kuculmez(self):
        """AutoCAD bloğun içindeki çizgi desenini bloğun ölçeğiyle küçültmez:
        paftadaki ( 1/ölçek ) blokta desen ölçeği desenin kâğıt çarpanı
        ( uslup.DESENLER ), tek başına ( gerçek ölçüde ) açılan DXF'te × ölçek.
        Eskiden blokta da ölçek çarpılıyordu:  eksenler AutoCAD'de düz çizgi
        görünüyordu."""
        des = uslup.DESENLER["EKSEN"]
        eksen = [
            e
            for e in _dxf_varliklari(self.d, self.d.modelspace())
            if e.dxftype() == "LINE" and e.dxf.get("linetype") == des.dxf
        ]
        self.assertTrue(eksen)
        for e in eksen:
            self.assertEqual(e.dxf.ltscale, des.olcek * 20)
        d, bilgi = pafta.belge(self.g)
        for c in bilgi["cizimler"]:
            if c["ad"] in cizimler.OLCEKSIZ:
                continue  # tablo:  çizgisi yok
            blok = d.blocks.get(f"CIZIM_{c['ad'].upper()}")
            desenli = [
                e
                for e in _dxf_varliklari(d, blok)
                if e.dxftype() in ("LINE", "LWPOLYLINE", "CIRCLE")
                and (e.dxf.get("linetype") == des.dxf or uslup.KATMAN[e.dxf.layer].desen)
            ]
            self.assertTrue(desenli, c["ad"])
            for e in desenli:
                ad = "EKSEN" if e.dxf.get("linetype") == des.dxf else uslup.KATMAN[e.dxf.layer].desen
                self.assertEqual(e.dxf.ltscale, uslup.DESENLER[ad].olcek, c["ad"])

    def test_birim_milimetre(self):
        self.assertEqual(self.d.header["$INSUNITS"], 4)

    def test_yazi_boyu_svg_ile_ayni(self):
        """DXF'te etiket ( MTEXT ) / ölçü yazısı yüksekliği BÜYÜK HARF
        yüksekliğidir, SVG'de em:  Arial'de büyük harf 0,716 em.  Çarpılmazsa DXF
        yazısı 1,4 kat büyük çıkıp yerleşimin ayırdığı yere sığmıyordu."""
        self.assertEqual(self.CDX.BUYUK_HARF, 0.716)
        yazilar = sorted(x["yukseklik"] for x in self.e if x["tip"] == "yazi")
        msp = self.d.modelspace()
        dxf_metni = sorted(
            [t.dxf.height for t in msp.query("TEXT")] + [t.dxf.char_height for t in msp.query("MTEXT")]
        )
        self.assertEqual(len(dxf_metni), len(yazilar) + 1)  # + belge başlığı
        for h in yazilar:
            self.assertTrue(any(abs(v - h * 0.716) < 1e-6 for v in dxf_metni), h)
        #  Ölçü yazısı:  stilin boyu ( kâğıtta mm ) × DIMSCALE ( 12 Eki'den adlı stil )
        olcu = sorted(round(x["yazi"]["h"] * 0.716, 3) for x in self.e if x["tip"] == "olcu")
        boy = []
        for dim in self.d.modelspace().query("DIMENSION"):
            stil = self.d.dimstyles.get(dim.dxf.dimstyle)
            boy.append(round(dim.override().get("dimtxt", stil.dxf.dimtxt) * stil.dxf.dimscale, 3))
        self.assertEqual(sorted(boy), olcu)

    def test_kullanilan_katmanlar_tanimli(self):
        for el in self.e:
            self.assertIn(el["katman"], self.d.layers, el["katman"])

    def test_olculer_gercek_dimension_varligi(self):
        say = sum(1 for x in self.d.modelspace() if x.dxftype() == "DIMENSION")
        self.assertEqual(say, sum(1 for el in self.e if el["tip"] == "olcu"))

    def test_duvar_taramasi_hatch_olarak(self):
        #  Desenli HATCH duvar kesitidir;  SOLID HATCH parçanın dolu kesiti
        #  ( planda ray — parcalar.ray_bicimi )
        taramalar = [x for x in _dxf_varliklari(self.d, self.d.modelspace()) if x.dxftype() == "HATCH"]
        self.assertEqual(
            sum(1 for x in taramalar if x.dxf.solid_fill == 0),
            sum(1 for el in self.e if el["tip"] in ("tarama", "tarama_tugla")),
        )
        self.assertEqual(
            sum(1 for x in taramalar if x.dxf.solid_fill == 1),
            sum(1 for el in self.e for p in el.get("bicim", ()) if p.get("dolu")),
        )

    def test_dxf_baytlari_yazilabiliyor(self):
        b = self.CDX.yaz(self.e, "KUYU PLANI", 20)
        self.assertGreater(len(b), 10000)
        self.assertIn(b"SECTION", b)
        self.assertIn(b"KUYU-DUVAR", b)

    def test_ayni_eleman_listesi_iki_bicime_de_gidiyor(self):
        #  SVG ve DXF AYNI listeden üretilir;  ikinci bir çizici yoktur.
        svg_metni = svg.yaz(self.e, geometri.sinir(self.e, 250), "KUYU PLANI", 20)
        self.assertIn("KUYU PLANI", svg_metni)
        self.assertGreater(len(self.e), 40)


class YerlesimRegresyonlari(unittest.TestCase):
    def test_kabin_dis_zarfi_kuyu_icinde_olmali(self):
        for degisim in ({"kaciklik_y": 600}, {"kaciklik_y": -600}, {"kaciklik_y": 320}, {"derinlik": 1700}):
            with self.subTest(degisim=degisim):
                self.assertTrue(
                    any("şasesi kuyunun dışına" in h for h in geometri.dogrula(_ornek(kabin=degisim)))
                )

    def test_aciklik_siniri_ve_cakisma(self):
        # Kabin rayının arkası 343'te, ara kiriş 293 – 343;  ağırlık yarı
        # kalınlığı 80.  ray_duvar = 193 → kirişe tam 20 mm;  fazlası geçemez.
        for yer in ("Sol", "Sağ"):
            for duvar, uygun in (
                (192, True),
                (193, True),
                (194, False),
                (215, False),
                (285, False),
                (390, False),
            ):
                g = (
                    _sag_ayna(agirlik={"ray_duvar": duvar})
                    if yer == "Sağ"
                    else _ornek(agirlik={"yeri": yer, "ray_duvar": duvar})
                )
                with self.subTest(yer=yer, duvar=duvar):
                    self.assertEqual(not geometri.dogrula(g), uygun)

    def test_ozel_pano_olcusu_denetim_ve_cizimde_ayni(self):
        g = _ornek(kabin={"kaciklik_y": 290})
        g["_cizim_sabitleri"] = {"kabin_pano_yan": 100}
        self.assertTrue(any("şasesi kuyunun dışına" in h for h in geometri.dogrula(g)))
        kabin = _dikdortgenler(geometri.plan(g), "KABIN")[0]
        self.assertEqual(kabin["g"], 1550)

    def test_her_yerlesimde_zincirler_kapanir(self):
        for yer in girdi.AGIRLIK_YERLERI:
            e = geometri.plan(_ornek(agirlik={"yeri": yer}))
            for z in geometri.zincirler(e):
                with self.subTest(yer=yer, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            if yer != "Arka":
                olcu = next(q for q in e if q["tip"] == "olcu" and q.get("ad") == "olcu_agirlik_ekseni")
                self.assertEqual(olcu["uzunluk"], 130)
                self.assertEqual(olcu["metin"], "130")

    def test_dbgw_gercek_ray_yuzlerine_baglanir(self):
        for yer in girdi.AGIRLIK_YERLERI:
            g = _ornek(agirlik={"yeri": yer})
            e = geometri.plan(g)
            q = next(q for q in e if q["tip"] == "olcu" and q["metin"].startswith("DBGW"))
            self.assertEqual(q["uzunluk"], 850)
            if yer == "Arka":
                self.assertEqual(q["yon"], "yatay")
                self.assertEqual((q["a"][0], q["b"][0]), (625, 1475))
            else:
                self.assertEqual(q["yon"], "dusey")

    def test_dxf_yazi_hizasini_korur(self):
        from cizim import dxf

        elemanlar = [eleman.yazi(100, 200, h, hiza=h) for h in ("sol", "orta", "sag")]
        d = dxf.belge(elemanlar)
        yazilar = list(d.modelspace().query("MTEXT"))
        self.assertEqual(len(yazilar), 3)
        #  MIDDLE_LEFT · MIDDLE_CENTER · MIDDLE_RIGHT
        self.assertEqual([m.dxf.attachment_point for m in yazilar], [4, 5, 6])
        self.assertEqual([m.plain_text() for m in yazilar], ["sol", "orta", "sag"])

    def test_dxf_kullanici_yazisi_kod_sayilmaz(self):
        """Asansörün adı plan başlığına girer:  AutoCAD'in kodları ( "%%c" → Ø,
        "^I" → sekme;  şapka macOS'ta AutoCAD'i çökertiyor ) yazıyı bozmaz."""
        from cizim import dxf

        adlar = ("BLOK A %%c 2", "A^1 {x}\\", "%50 EĞİM", "%%%")
        d = dxf.belge([eleman.yazi(0, 0, a) for a in adlar], baslik="KUYU %%d PLANI")
        yazilar = [m.text for m in d.modelspace().query("MTEXT")]
        self.assertEqual(
            yazilar,
            ["BLOK A %%%%%%c 2", "A\u02c61 \\{x\\}\\\\", "%50 EĞİM", "%%%%%%%%%"],
        )
        baslik = [t.dxf.text for t in d.modelspace().query("TEXT")]
        self.assertEqual(baslik, ["KUYU %%%%%%d PLANI   1/20"])


class ParcaTutarliligi(unittest.TestCase):
    """Parçalar kendi rayları arasında, birbirinin içinden geçmeden durur."""

    def _yerlesimler(self):
        return (
            ("Sol", _ornek()),
            ("Sağ", _sag_ayna()),
            (
                "Arka",
                _ornek(
                    agirlik={"yeri": "Arka"},
                    kabin={"kaciklik_y": 0},
                    kapi={"sol_pay": 600},
                    kuyu={"derinlik": 2100},
                ),
            ),
        )

    def test_agirlik_kendi_raylarinin_arasinda(self):
        for yer, g in self._yerlesimler():
            ag = g["agirlik"]
            blok = _dikdortgenler(geometri.plan(g), "AGIRLIK")[0]
            boy = blok["d"] if yer != "Arka" else blok["g"]
            with self.subTest(yer=yer):
                self.assertLess(boy, ag["ray_arasi"])

    def test_agirlik_raylardan_uzunsa_reddedilir(self):
        self.assertTrue(
            any("ağırlık rayları arasından" in h for h in geometri.dogrula(_ornek(agirlik={"genislik": 850})))
        )

    def test_sase_raylardan_genisse_reddedilir(self):
        self.assertTrue(
            any("kabin rayları arasından" in h for h in geometri.dogrula(_ornek(kabin_ray={"arasi": 1500})))
        )

    def test_kapi_kabinin_onune_duser(self):
        g = _ornek()
        kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        #  Örnekte kapı ekseni kabin ekseniyle aynı  ( referans proje:  1.180 )
        self.assertEqual(g["kapi"]["sol_pay"] + g["kapi"]["genislik"] / 2.0, kx)
        self.assertTrue(
            any("kabinin önüne düşmüyor" in h for h in geometri.dogrula(_ornek(kapi={"sol_pay": 300})))
        )

    def test_kabin_konsolu_agirligin_icinden_gecmez(self):
        for yer, g in self._yerlesimler():
            e = geometri.plan(g)
            blok = _dikdortgenler(e, "AGIRLIK")[0]
            for el in _dikdortgenler(e, "KONSOL"):
                with self.subTest(yer=yer, parca=el.get("ad")):
                    self.assertFalse(_cakisma(el, blok), el)

    def test_kuyuda_kumanda_panosu_yok(self):
        """Kumanda panosu kuyunun içinde değildir:  makine dairesizde kuyunun
        dışındaki acil panoda, makine dairelide makine dairesinde.  Eskiden kuyu
        planında kaynağı belirsiz bir "PANO" vardı ( kesitlerde yoktu, makine
        dairelide çift oluyordu )."""
        for yer, g in list(self._yerlesimler()) + [
            ("makine dairesi", _ornek(makine={"yeri": "Makine dairesi"}))
        ]:
            with self.subTest(yer=yer):
                self.assertFalse([el for el in geometri.plan(g) if el["katman"] == "PANO"])


class OlcuYazilari(unittest.TestCase):
    """Ölçü yazıları kendi ölçüsünün yanında, üst üste binmeden, çerçevede."""

    def _kutular(self, e):
        out = []
        for el in e:
            if el["tip"] == "olcu":
                y = el["yazi"]
                w, h = eleman.yazi_eni(el["metin"], y["h"]) / 2.0, y["h"] / 2.0
                if y["aci"]:
                    w, h = h, w
                out.append((el, y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h))
        return out

    def _projeler(self):
        yield "Sol", _ornek()
        yield "Sağ", _sag_ayna()
        yield (
            "Arka",
            _ornek(
                agirlik={"yeri": "Arka"},
                kabin={"kaciklik_y": 0},
                kapi={"sol_pay": 600},
                kuyu={"derinlik": 2100},
            ),
        )
        g = _ornek()
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
        yield "Doğrudan", g

    def test_yazilar_ust_uste_binmiyor(self):
        import itertools

        for ad, g in self._projeler():
            k = self._kutular(geometri.plan(g))
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_yazi_kendi_olcusunun_yaninda(self):
        """Yazı ölçü çizgisinden en çok iki kat ( 170 mm ) uzakta;  eskiden
        sığmayan yazı başka bir sıranın üstüne itiliyordu."""
        for ad, g in self._projeler():
            for el in geometri.plan(g):
                if el["tip"] != "olcu":
                    continue
                y = el["yazi"]
                capraz = abs((y["y"] if el["yon"] == "yatay" else y["x"]) - el["kot"])
                with self.subTest(proje=ad, olcu=el["metin"]):
                    if y["aci"] == (0.0 if el["yon"] == "yatay" else 90.0):
                        self.assertLessEqual(capraz, 170 + 1e-6)

    def test_yazilar_cercevenin_icinde(self):
        for ad, g in self._projeler():
            e = geometri.plan(g)
            x1, y1, x2, y2 = geometri.sinir(e)
            for el, a, b, c, d in self._kutular(e):
                with self.subTest(proje=ad, olcu=el["metin"]):
                    self.assertTrue(x1 <= a and c <= x2 and y1 <= b and d <= y2)

    def test_aski_arasi_tek_olcu(self):
        q = [
            el for el in geometri.plan(_ornek()) if el["tip"] == "olcu" and el.get("ad") == "olcu_aski_arasi"
        ]
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["uzunluk"], _ornek()["aski"]["kasnak_arasi"])

    def test_uzatma_cizgisi_yok(self):
        e = geometri.plan(_ornek())
        s = svg.yaz(e, geometri.sinir(e, 250), "", 20)
        self.assertNotIn('stroke-dasharray="30 20"', s)
        from cizim import dxf

        d = dxf.belge(e)
        for dim in d.modelspace().query("DIMENSION"):
            blok = d.blocks.get(dim.dxf.geometry)
            #  Uzatma çizgisi olsaydı ölçülen noktaya ( x = 0 ya da y = 0
            #  hizası ) inen çizgiler bulunurdu;  yalnız ölçü çizgisi + uçlar kalır.
            ciz = [x for x in blok if x.dxftype() == "LINE"]
            self.assertLessEqual(len(ciz), 3, dim.dxf.text)

    def test_dxf_yazisi_svg_ile_ayni_yerde(self):
        from cizim import dxf

        e = geometri.plan(_ornek())
        d = dxf.belge(e)
        olculer = [el for el in e if el["tip"] == "olcu"]
        for el, dim in zip(olculer, d.modelspace().query("DIMENSION")):
            p = dim.dxf.text_midpoint
            with self.subTest(olcu=el["metin"]):
                self.assertAlmostEqual(p.x, el["yazi"]["x"], places=3)
                self.assertAlmostEqual(p.y, el["yazi"]["y"], places=3)


#  ─────────────────────────────────────────────────────────────────────
#  KABİN ÜSTÜ PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import kabin_ustu


def _arka(kaciklik=0.0):
    """Ağırlık arkada:  kabinin iki yanı da duvara bakar, sınır denemesi kolay."""
    return _ornek(
        agirlik={"yeri": "Arka"},
        kabin={"kaciklik_y": kaciklik},
        kapi={"sol_pay": 600},
        kuyu={"derinlik": 2100},
    )


def _kabin_ustu_askili():
    """Kabin üstü askı:  kasnaklar şasenin üst kirişinin üstünde, RAY
    EKSENİNDE ( askı ekseni ray ekseninde ).  Askı ekseni kabinin ortasında
    kalsaydı kasnaklar ve aralarındaki halat kirişin önünden ayrı bir bant
    olarak geçer, 1.440 × 1.433'lük tavanda çömelme alanına yer kalmazdı
    ( 10 Eki'den beri ikisi de engel — hareketli.kabin_parcalari )."""
    g = _ornek(aski={"duzen": "Kabin üstü", "kasnak_arasi": 1000})
    S, kb = sabitler.sabitler(g.get("_cizim_sabitleri")), g["kabin"]
    g["aski"]["kasnak_kaciklik"] = (
        g["kabin_ray"]["kapi_arasi"] - kb["on_pay"] - (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0
    )
    return g


def _ustu_projeler():
    yield "Sol", _ornek()
    yield "Sağ", _sag_ayna()
    yield "Arka", _arka()
    yield "Kabin üstü askı", _kabin_ustu_askili()
    g = _ornek(kabin_ustu={"siginma_tipi": "Dik duruş"})
    g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
    yield "Doğrudan · dik duruş", g


class KabinUstuSozlesme(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _ustu_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(kabin_ustu.dogrula(g), [])

    def test_siginma_tipi_zorunlu(self):
        self.assertTrue(kabin_ustu.dogrula(_ornek(kabin_ustu={"siginma_tipi": "Yatarak"})))

    def test_ray_ekseni_kabinin_icinden_gecmeli(self):
        self.assertTrue(
            any("kabinin derinliği içinden" in h for h in geometri.dogrula(_ornek(kabin={"derinlik": 800})))
        )

    def test_halat_parcanin_icinden_gecemez(self):
        #  1.470'lik kasnak aralığında sol halat kabin rayının ara kirişinden geçer
        self.assertTrue(any("Halat" in h for h in kabin_ustu.dogrula(_ornek(aski={"kasnak_arasi": 1470}))))

    def test_kabin_ustu_kasnagi_korkulugu_kesemez(self):
        self.assertTrue(
            any("korkuluğun yolunu" in h for h in kabin_ustu.dogrula(_ornek(aski={"duzen": "Kabin üstü"})))
        )

    def test_siginmaya_yer_yoksa_reddedilir(self):
        #  Tavan 540 × 733;  korkuluklar içeri alınınca 450 genişlik kalır —
        #  500 × 700 hiçbir yönde sığmaz
        g = _arka()
        g["kabin"].update({"genislik": 450, "derinlik": 700})
        g["kabin_ray"].update({"arasi": 650, "kapi_arasi": 500})
        g["kapi"].update({"genislik": 400, "sol_pay": 850})
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 200}
        self.assertEqual(geometri.dogrula(g), [])
        self.assertTrue(any("sığınma alanına" in h for h in kabin_ustu.dogrula(g)), kabin_ustu.dogrula(g))


class KabinUstuKorkuluk(unittest.TestCase):
    """TS EN 81-20 m.5.4.7.2 b ve m.5.4.7.4 — sınırların iki yanı."""

    def test_300_mm_asilinca_korkuluk(self):
        #  Arka yerleşimde sol boşluk = kabin ekseni − 720
        for kac, gerekli in ((-30, False), (-29, True)):
            k = kabin_ustu.yerlesim(_arka(kac))["kenarlar"]["Sol"]
            with self.subTest(bosluk=k["bos"]):
                self.assertEqual(k["gerekli"], gerekli)

    def test_yukseklik_500_mm_sinirinda_degisir(self):
        #  Küpeşte raydan 100 mm uzak durmak için 45 içeri alınır;
        #  boşluk 455 + 45 = 500 → 0,70 m,  456 + 45 = 501 → 1,10 m
        for kac, h in ((125, 700), (126, 1100)):
            k = kabin_ustu.yerlesim(_arka(kac))["kenarlar"]["Sol"]
            with self.subTest(bosluk=k["bos"]):
                self.assertEqual(k["iceri"], 45)
                self.assertEqual(k["yukseklik"], h)

    def test_kupeste_parcalardan_100_kenardan_en_cok_150(self):
        for ad, g in _ustu_projeler():
            Y = kabin_ustu.yerlesim(g)
            for yan, k in Y["kenarlar"].items():
                if not k["gerekli"]:
                    continue
                with self.subTest(proje=ad, yan=yan):
                    self.assertLessEqual(k["iceri"], standart.KORKULUK_KENAR_AZAMI)
                    if k["parca"] is not None:
                        self.assertGreaterEqual(
                            k["parca"] + k["iceri"], standart.KORKULUK_PARCA_ASGARI - 1e-9
                        )

    def test_150_mm_yetmezse_reddedilir(self):
        eski = standart.KORKULUK_PARCA_ASGARI
        try:
            standart.KORKULUK_PARCA_ASGARI = 300.0
            self.assertTrue(any("m.5.4.7.4 c" in h for h in kabin_ustu.dogrula(_ornek())))
        finally:
            standart.KORKULUK_PARCA_ASGARI = eski

    def test_korkuluk_cizgisi_yalniz_gerekli_kenarda(self):
        for ad, g in _ustu_projeler():
            Y = kabin_ustu.yerlesim(g)
            cizgiler = [el for el in kabin_ustu.ciz(g) if el.get("ad") == "korkuluk"]
            with self.subTest(proje=ad):
                self.assertEqual(len(cizgiler), sum(k["gerekli"] for k in Y["kenarlar"].values()))


class KabinUstuYerlesim(unittest.TestCase):
    def test_siginma_cizelge_3_olculerinde_ve_icerde(self):
        for ad, g in _ustu_projeler():
            Y = kabin_ustu.yerlesim(g)
            s, ic = Y["siginma"], Y["ic"]
            with self.subTest(proje=ad):
                self.assertEqual(
                    sorted((s[2] - s[0], s[3] - s[1])),
                    sorted(kabin_ustu.SIGINMA[g["kabin_ustu"]["siginma_tipi"]]),
                )
                self.assertTrue(ic[0] <= s[0] and s[2] <= ic[2] and ic[1] <= s[1] and s[3] <= ic[3])
                for p in Y["engeller"]:
                    self.assertFalse(ortusur(s, p), p)

    def test_kuyu_parcalari_plandan_eksiksiz_gelir(self):
        """Raylar, konsollar ve karşı ağırlık kuyu planındakinin aynısı."""
        for ad, g in _ustu_projeler():
            plan, ustu = geometri.plan(g), kabin_ustu.ciz(g)
            for kat in ("RAY", "KONSOL", "AGIRLIK", "CIVATA"):
                with self.subTest(proje=ad, katman=kat):
                    self.assertEqual(
                        sorted(
                            _kutu
                            for _kutu in (
                                tuple(round(el[a], 3) for a in ("x", "y", "g", "d"))
                                for el in _dikdortgenler(plan, kat)
                            )
                        ),
                        sorted(
                            tuple(round(el[a], 3) for a in ("x", "y", "g", "d"))
                            for el in _dikdortgenler(ustu, kat)
                        ),
                    )

    def test_on_duvar_dolu_kapi_gorunmez(self):
        e = kabin_ustu.ciz(_ornek())
        self.assertFalse(
            [el for el in e if el["katman"] == "KAPI" and el["tip"] == "dikdortgen" and el["y"] < 0]
        )

    def test_askiya_gore_tavan(self):
        e = kabin_ustu.ciz(_ornek())
        self.assertFalse([el for el in e if el.get("ad") == "kabin_kasnak"])
        self.assertEqual(len([el for el in e if el.get("ad") == "halat"]), 2)
        e = kabin_ustu.ciz(_ornek(aski={"duzen": "Kabin üstü", "kasnak_arasi": 1000}))
        self.assertEqual(len([el for el in e if el.get("ad") == "kabin_kasnak"]), 2)
        self.assertFalse([el for el in e if el.get("ad") == "halat"])

    def test_operator_tavanin_kapi_kenarinda(self):
        #  Operatör tavanın üstünde kutu boyu kadar, önde kabin kapısının
        #  üstünde kabin eşiğinin ön kenarına kadar;  enine kanatların yolunu
        #  ( kapı + cep ) örter — tavandan geniş olabilir ( 5 Eki )

        S = sabitler.sabitler()
        for ad, g in _ustu_projeler():
            Y = kabin_ustu.yerlesim(g)
            op, t = Y["operator"], Y["tavan"]
            KB = girdi.kapi_bolgesi(g, S)
            yol = [c for cep in girdi.kanat_cepleri(g, S, pay=False) for c in cep]
            x0, kg = g["kapi"]["sol_pay"], g["kapi"]["genislik"]
            with self.subTest(proje=ad):
                self.assertEqual(op[1], KB["kabin_esik"][0])
                self.assertEqual(op[3] - t[1], S["kabin_kapisi_kutu_boy"])
                self.assertEqual((op[0], op[2]), (min([x0] + yol), max([x0 + kg] + yol)))

    def test_kabin_ustunde_kapi_kesit_kotuna_gore(self):
        #  Kesit kabin tavanından ( kabin iç + 60 ) geçer:  kaba boşluğun
        #  ( kapı + 240 ) içindeyse ön duvar boşluklu, kasa kesilir;  üstündeyse
        #  duvar dolu, boşluk kesikli.  Kat ve kabin kapısı görünür;  operatör
        #  yalnız yerleşimde ( engel ), çizilmez — LiftDesigner 1022 X-X gibi
        #  ( 5 Eki;  eskiden ön duvar hep doluydu, kapı bölgesi boş )
        for kabin_h, acik in ((2150, True), (2300, False)):  # kapı 2.100, üst payı 200
            g = _ornek()
            g["dusey"]["kabin_ic_yukseklik"] = kabin_h
            e = kabin_ustu.ciz(g)
            with self.subTest(kabin_h=kabin_h):
                duvar = [el for el in e if el["katman"] == "KUYU-DUVAR" and el["y"] < 0]
                self.assertEqual(len(duvar), 2 if acik else 1)
                bosluk = next(el for el in e if el.get("ad") == "kapi_boslugu")
                self.assertEqual(bosluk["katman"], "KAPI" if acik else "GIZLI")
                for ad in ("kat_kanadi", "kat_esigi", "kapi_kasasi"):
                    self.assertTrue(all(el["katman"] == "KAPI" for el in e if el.get("ad") == ad), ad)
                    self.assertTrue(any(el.get("ad") == ad for el in e), ad)
                for ad in ("kabin_kanadi", "kabin_esigi"):
                    kk = [el for el in e if el.get("ad") == ad]
                    self.assertTrue(kk and all(el["katman"] != "GIZLI" for el in kk), ad)
                self.assertFalse(
                    [el for el in e if el.get("ad") == "operator" or "OPERATÖR" in str(el.get("metin", ""))]
                )

    def test_siginma_ust_kirisin_altina_girmez(self):
        #  Şasenin üst kirişi ( iki C profil ) tavanın üstündedir:  sığınma alanı
        #  onun dışında ( 4 Eki );  10 Eki'den beri kabin üstü askıda da
        #  ( hareketli.kabin_parcalari ) — kasnaklar ve aralarındaki halat da engel.
        for ad, g in _ustu_projeler():
            Y = kabin_ustu.yerlesim(g)
            kiris = [geometri.sinir([el]) for el in Y["taban"] if el.get("ad") == "sase_kiris"]
            kasnak = [geometri.sinir([el]) for el in Y["taban"] if el.get("ad") == "kabin_kasnak"]
            sg = Y["siginma"]
            with self.subTest(ad):
                for k in kiris + (kasnak if g["aski"]["duzen"] == "Kabin üstü" else []):
                    self.assertFalse(sg[0] < k[2] and k[0] < sg[2] and sg[1] < k[3] and k[1] < sg[3])
                    self.assertIn(k, Y["engeller"])
                if g["aski"]["duzen"] != "Kabin üstü":
                    continue
                if len(kasnak) == 2:  # kasnaklar arasındaki halat
                    bant = (
                        min(k[0] for k in kasnak),
                        min(k[1] for k in kasnak),
                        max(k[2] for k in kasnak),
                        max(k[3] for k in kasnak),
                    )
                    self.assertIn(bant, Y["engeller"])
                #  Kabin üstü planında kiriş çizilir, sığınma ölçüleri ona binmez
                e = kabin_ustu.ciz(g)
                self.assertEqual(len([x for x in e if x.get("ad") == "sase_kiris"]), 2)

    def test_olcu_zincirleri_ve_yazilar(self):
        import itertools

        for ad, g in _ustu_projeler():
            e = kabin_ustu.ciz(g)
            for z in geometri.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_dxf_temiz(self):
        from cizim import dxf
        from ezdxf.audit import Auditor

        d = dxf.belge(kabin_ustu.ciz(_ornek()), "KABİN ÜSTÜ", 20)
        a = Auditor(d)
        a.run()
        self.assertEqual(list(a.errors), [])
        self.assertIn("KORKULUK", d.layers)
        self.assertIn("SIGINMA", d.layers)


#  ─────────────────────────────────────────────────────────────────────
#  KUYU DİBİ PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import kuyu_dibi


def _dip_projeler():
    yield "Sol", _ornek()
    g = _sag_ayna()
    g["kuyu_dibi"] = dict(g["kuyu_dibi"], regulator_yan="Sol")
    yield "Sağ", g
    yield "Arka", _arka()
    yield (
        "İki tampon · yatarak",
        _ornek(
            kuyu_dibi={
                "kabin_tampon_adedi": 2,
                "kabin_tampon_arasi": 600,
                "agirlik_tampon_adedi": 2,
                "agirlik_tampon_arasi": 400,
                "siginma_tipi": "Yatarak",
            }
        ),
    )
    yield "Derin kuyu · dik duruş", _ornek(kuyu_dibi={"derinlik": 2600, "siginma_tipi": "Dik duruş"})


class KuyuDibiSozlesme(unittest.TestCase):
    def test_ornekler_gecerli(self):
        for ad, g in _dip_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(kuyu_dibi.dogrula(g), [])

    def test_kabin_agirlik_arasi_50_mm(self):
        #  TS EN 81-20 m.5.2.5.5.1 h — arka ağırlığın ön yüzü kabinin arkasına.
        #  Kabinin arkası 270 + 1.400 + 33 = 1.703;  kuyu 2.000'de ağırlığın ön
        #  yüzü 2.000 − ray_duvar − 80:  ray_duvar = 167 → tam 50 mm,  170 → 47 mm
        for duvar, uygun in ((167, True), (170, False)):
            g = _ornek(agirlik={"yeri": "Arka", "ray_duvar": duvar}, kuyu={"derinlik": 2000})
            with self.subTest(ray_duvar=duvar):
                self.assertEqual(not any("m.5.2.5.5.1 h" in h for h in geometri.dogrula(g)), uygun)

    def test_hatali_girdiler(self):
        for ezme, parca in (
            ({"siginma_tipi": "Oturarak"}, "siginma_tipi"),
            ({"kabin_tampon_adedi": 3}, "kabin_tampon_adedi"),
            ({"kabin_tampon_adedi": 2}, "kabin_tampon_arasi"),
            ({"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 100}, "üst üste"),
            ({"agirlik_tampon_adedi": 2, "agirlik_tampon_arasi": 900}, "karşı ağırlığın altına"),
            ({"regulator_yan": "Orta"}, "regulator_yan"),
            ({"kuvvetler": {"FKR": 1, "FAR": 1, "Fkt": 1}}, "kuyu_dibi.kuvvetler"),
            ({"kuvvetler": {"FKR": 1, "FAR": 1, "Fkt": 1, "Fat": 1}}, "kuyu_dibi.kuvvetler"),
            ({"kuvvetler": dict.fromkeys(kuyu_dibi.KUVVETLER, 1) | {"Fat": 0}}, "kuvvetler.Fat"),
            ({"kuvvetler": dict.fromkeys(kuyu_dibi.KUVVETLER, 1) | {"FKR": "22 kN"}}, "kuvvetler.FKR"),
            ({"kuvvetler": dict.fromkeys(kuyu_dibi.KUVVETLER, 1) | {"Fx_kabin": -5}}, "kuvvetler.Fx_kabin"),
        ):
            with self.subTest(ezme=ezme):
                self.assertTrue(
                    any(parca in h for h in kuyu_dibi.dogrula(_ornek(kuyu_dibi=ezme))),
                    kuyu_dibi.dogrula(_ornek(kuyu_dibi=ezme)),
                )


class KuyuDibiYerlesim(unittest.TestCase):
    KV = {
        "FKR": 30683.19,
        "FAR": 11545.12,
        "Fkt": 69810.08,
        "Fat": 54114.08,
        "Fx_kabin": 1543.39,
        "Fy_kabin": 802.64,
        "Fx_agirlik": 86.18,
        "Fy_agirlik": 457.84,
    }

    def _tablo(self, e):
        return [x for x in e if x.get("ad") == "kuvvet_tablosu"]

    def test_kuvvet_tablosu(self):
        """Kuyu tabanı:  hesabın 9. bölümü, hesap paftasındaki adlarla;  iki
        tamponda her birine düşen de ( m.5.2.1.8.5 / 6 ).  Ray konsolu:  7. ve
        8. bölümlerin en büyük Fx / Fy'si ( referans proje "Building Forces" gibi )."""
        self.assertEqual(
            kuyu_dibi.KUVVETLER,
            ("FKR", "FAR", "Fkt", "Fat", "Fx_kabin", "Fy_kabin", "Fx_agirlik", "Fy_agirlik"),
        )
        self.assertEqual(self._tablo(kuyu_dibi.ciz(_ornek())), [])  # girilmemiş:  tablo yok
        e = kuyu_dibi.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV}))
        self.assertEqual(
            [x["metin"] for x in self._tablo(e)],
            [
                "RAY KONSOLUNA YATAY YÜKLER",
                "( yük durumlarının en büyüğü )",
                "Kabin rayı:  Fx = 1,54 kN  ·  Fy = 0,80 kN",
                "Ağırlık rayı:  Fx = 0,09 kN  ·  Fy = 0,46 kN",
            ],
        )
        #  Kuyu tabanı yükleri noktalarında, kN:  bir rayın / tamponun altına
        self.assertEqual(
            sorted(x["metin"] for x in e if x.get("ad") == "yuk"),
            sorted(["FKR = 30,68 kN"] * 2 + ["FAR = 11,55 kN"] * 2 + ["Fkt = 69,81 kN", "Fat = 54,11 kN"]),
        )
        e = kuyu_dibi.ciz(
            _ornek(
                kuyu_dibi={
                    "kuvvetler": self.KV,
                    "kabin_tampon_adedi": 2,
                    "kabin_tampon_arasi": 600,
                    "agirlik_tampon_adedi": 2,
                    "agirlik_tampon_arasi": 400,
                }
            )
        )
        self.assertEqual(
            sorted(
                x["metin"]
                for x in e
                if x.get("ad") == "yuk" and x["metin"][1] != "K" and x["metin"][1] != "A"
            ),
            sorted(["Fkt1 = 34,91 kN"] * 2 + ["Fat1 = 27,06 kN"] * 2),
        )
        #  Ray kuvveti sıfır olabilir ( yük ekseni ray ekseninde ), kuyu tabanı yükü olamaz
        self.assertEqual(kuyu_dibi.dogrula(_ornek(kuyu_dibi={"kuvvetler": dict(self.KV, Fy_agirlik=0)})), [])
        self.assertTrue(kuyu_dibi.dogrula(_ornek(kuyu_dibi={"kuvvetler": dict(self.KV, FAR=0)})))

    def test_yuk_oklari_ve_kutulari(self):
        """Her yük noktasına bir ok ve çerçeveli kutu ( LiftDesigner "View of Pit"
        gibi ):  ok noktada biter, kutunun kenarından çıkar;  kutu kuyunun
        içinde, hiçbir parçaya, yazıya, ölçüye ve başka kutuya binmez;  ok başka
        bir kutuyu, yazıyı ya da oku kesmez."""
        projeler = list(_dip_projeler()) + [
            ("yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            (
                "iki tampon · çömelme",
                _ornek(
                    kuyu_dibi={
                        "kabin_tampon_adedi": 2,
                        "kabin_tampon_arasi": 600,
                        "agirlik_tampon_adedi": 2,
                        "agirlik_tampon_arasi": 400,
                    }
                ),
            ),
        ]
        for ad, g in projeler:
            for kv in (None, self.KV):
                if kv:
                    g["kuyu_dibi"]["kuvvetler"] = dict(kv)
                #  Geçersiz düzen çizilip sınanmaz ( sağ aynada gergi ağırlığı eskiden
                #  rayla çakışıyordu, test yine de çiziyordu )
                self.assertEqual(kuyu_dibi.dogrula(g), [], ad)
                e = kuyu_dibi.ciz(g)
                Y = kuyu_dibi.yerlesim(g)
                G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
                noktalar = sorted(
                    kutu_merkezi(k)
                    for k in Y["kabin_tamponlari"]
                    + Y["agirlik_tamponlari"]
                    + Y["kabin_raylari"]
                    + Y["agirlik_raylari"]
                )
                kutu = [geometri.sinir([x]) for x in e if x.get("ad") == "yuk_kutusu"]
                oklar = [x for x in e if x.get("ad") == "yuk_oku"]
                yazi = [x for x in e if x.get("ad") == "yuk"]
                geri = [x for x in e if x.get("ad") not in ("yuk_kutusu", "yuk_oku", "yuk")]
                #  Tek tamponda sığınma alanının yüzeyine de binmez;  iki tamponda
                #  ( 8 nokta ) yüzeyine binebilir, yazısına binmez
                iki = g["kuyu_dibi"]["kabin_tampon_adedi"] + g["kuyu_dibi"]["agirlik_tampon_adedi"] > 2
                kutular, yazilar = kuyu_dibi._engeller(geri, siginma=not iki)
                with self.subTest(proje=ad, degerli=bool(kv)):
                    self.assertEqual(len(kutu), len(noktalar))
                    self.assertEqual(sorted((o["x2"], o["y2"]) for o in oklar), noktalar)
                    for o in oklar:
                        #  ok kutunun kenarından çıkar
                        self.assertTrue(
                            any(
                                abs(o["x1"] - k[0]) < 1e-6
                                or abs(o["x1"] - k[2]) < 1e-6
                                or abs(o["y1"] - k[1]) < 1e-6
                                or abs(o["y1"] - k[3]) < 1e-6
                                for k in kutu
                                if k[0] - 1e-6 <= o["x1"] <= k[2] + 1e-6
                                and k[1] - 1e-6 <= o["y1"] <= k[3] + 1e-6
                            )
                        )
                    #  Kutu kuyunun içinde ya da ( içeride yer yoksa ) duvarların dışında
                    k_ = g["kuyu"]
                    dis = (-k_["duvar_sol"], -k_["duvar_on"], G + k_["duvar_sag"], D + k_["duvar_arka"])
                    for k, y_ in zip(kutu, yazi):
                        self.assertTrue(
                            (0 < k[0] and k[2] < G and 0 < k[1] and k[3] < D)
                            or k[2] < dis[0]
                            or k[0] > dis[2]
                            or k[3] < dis[1]
                            or k[1] > dis[3],
                            k,
                        )
                        self.assertLessEqual(eleman.yazi_eni(y_["metin"], y_["yukseklik"]), k[2] - k[0])
                    for i, k in enumerate(kutu):
                        engel = kutular + yazilar + kutu[:i] + kutu[i + 1 :]
                        self.assertFalse([b for b in engel if ortusur(k, b)], k)
                    for i, o in enumerate(oklar):
                        p, q = (o["x2"], o["y2"]), (o["x1"], o["y1"])
                        self.assertFalse([b for b in yazilar if kuyu_dibi._kesisir(p, q, b)])
                        for j, o2 in enumerate(oklar):
                            if i != j:
                                self.assertFalse(
                                    kuyu_dibi._cakisir(p, q, (o2["x2"], o2["y2"]), (o2["x1"], o2["y1"]))
                                )
                        for k in kutu:
                            if not (
                                k[0] - 1e-6 <= q[0] <= k[2] + 1e-6 and k[1] - 1e-6 <= q[1] <= k[3] + 1e-6
                            ):
                                self.assertFalse(kuyu_dibi._kesisir(p, q, k))

    def test_kuvvet_semasi_yonleri(self):
        """Ray şemasında Fy ağzın doğrultusunda ( ağzın ucuna ), Fx ağza yandan
        ( EN 81-50 m.5.10.5 )."""
        e = kuyu_dibi.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV}))
        sema = [x for x in e if x.get("ad") == "kuvvet_semasi"]
        taban, agiz = [x for x in sema if x["tip"] == "dikdortgen"]
        oklar = {y["metin"]: y for y in sema if y["tip"] == "yazi"}
        ok = [x for x in sema if x["tip"] == "ok"]
        fy = min(ok, key=lambda o: abs(o["x2"] - o["x1"]))  # düşey ok
        fx = min(ok, key=lambda o: abs(o["y2"] - o["y1"]))  # yatay ok
        self.assertGreater(taban["g"], taban["d"])  # taban yatay, ağız düşey
        self.assertGreater(agiz["d"], agiz["g"])
        self.assertAlmostEqual(fy["x2"], agiz["x"] + agiz["g"] / 2.0)
        self.assertGreater(fy["y1"], fy["y2"])
        self.assertGreaterEqual(fy["y2"], agiz["y"] + agiz["d"])  # ağzın ucuna iner
        self.assertTrue(agiz["y"] < fx["y2"] < agiz["y"] + agiz["d"])
        self.assertLessEqual(fx["x2"], agiz["x"])  # ağza yandan
        self.assertEqual(set(oklar), {"Fx", "Fy"})

    def test_cerceve_yazilarin_enini_kapsar(self):
        """Sola hizalı tablo satırları çerçevenin içinde kalır ( taşıyordu )."""
        Y = eleman.yazi
        #  Etiket 2,5 mm ( uslup.NORMAL );  eni harflerin gerçek eni ( 12 Eki )
        h = uslup.NORMAL
        w = eleman.yazi_eni("ABCDE", h)
        for hiza, beklenen in (
            ("sol", (0, -h / 2, w, h / 2)),
            ("sag", (-w, -h / 2, 0, h / 2)),
            (None, (-w / 2, -h / 2, w / 2, h / 2)),
        ):
            for a, b in zip(
                geometri.sinir([Y(0, 0, "ABCDE", h, **({"hiza": hiza} if hiza else {}))]), beklenen
            ):
                self.assertAlmostEqual(a, b)
        for a, b in zip(geometri.sinir([Y(0, 0, "ABCDE", h, hiza="sol", aci=90)]), (-h / 2, 0, h / 2, w)):
            self.assertAlmostEqual(a, b)
        e = geometri.cerceveli(kuyu_dibi.ciz(_ornek(kuyu_dibi={"kuvvetler": self.KV})), "KUYU DİBİ PLANI")
        c = next(x for x in e if x["katman"] == "CERCEVE" and x["tip"] == "dikdortgen")
        for x in self._tablo(e):
            self.assertLessEqual(x["x"] + eleman.yazi_eni(x["metin"], x["yukseklik"]), c["x"] + c["g"])

    def test_olcu_yazisi_parcaya_binmez(self):
        """Kuyunun içindeki ölçü yazıları tampon, gergi, merdiven, ray, konsol,
        perde ve nokta adlarının üstüne düşmez ( Yatarak sığınmada "1000"
        kabin tamponunun üstündeydi ).  Çizimin SON hâli ( etiketleri_ayir'dan
        sonra — ekrandaki, paftadaki ):  yazılar 2,5 mm'ye büyüyünce ( 12 Eki )
        REGÜLATÖR GERGİSİ ve DİK DURUŞ etiketleri ham çizimde ölçü yazısına
        uzanıyor, ayırıcı onları kaydırıyor."""
        projeler = list(_dip_projeler()) + [
            ("Yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            (
                "Yatarak · referans proje tamponu",
                _ornek(kuyu_dibi={"siginma_tipi": "Yatarak", "regulator_kasnak_capi": 240}),
            ),
        ]
        for ad, g in projeler:
            e = cizimler.CIZIMLER["kuyu_dibi"][1](g)
            G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
            engel = [
                geometri.sinir([x])
                for x in e
                if x["katman"] in geometri.PARCA_KATMANLARI or (x["tip"] == "yazi" and x["katman"] == "YAZI")
            ]
            for o in e:
                if o["tip"] != "olcu":
                    continue
                y_ = o["yazi"]
                if not (0 < y_["x"] < G and 0 < y_["y"] < D):
                    continue
                w, h = eleman.yazi_eni(o["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                if y_["aci"]:
                    w, h = h, w
                k = (y_["x"] - w, y_["y"] - h, y_["x"] + w, y_["y"] + h)
                with self.subTest(proje=ad, olcu=o["metin"]):
                    self.assertFalse([b for b in engel if ortusur(k, b)])

    def test_kuvvet_tablosu_cizimin_disinda(self):
        """Tablo planın ve ölçülerin sağında;  satırlar üst üste binmez."""
        for ad, g in _dip_projeler():
            g["kuyu_dibi"]["kuvvetler"] = dict(self.KV)
            e = kuyu_dibi.ciz(g)
            t = self._tablo(e)
            sag = max(
                max(
                    x.get("x", 0),
                    x.get("x2", 0),
                    x.get("x", 0) + x.get("g", 0),
                    x["yazi"]["x"] + x["yazi"]["h"] / 2.0 if x["tip"] == "olcu" else 0,
                )
                for x in e
                if x.get("ad") not in ("kuvvet_tablosu", "kuvvet_semasi")
            )
            sema = [x for x in e if x.get("ad") == "kuvvet_semasi"]
            with self.subTest(proje=ad):
                self.assertGreater(min(x["x"] for x in t), sag)
                self.assertGreater(geometri.sinir(sema)[0], sag)
                #  Şema tablonun altında, son satıra binmez
                self.assertLess(geometri.sinir(sema)[3], min(x["y"] for x in t) - 40)
                ys = [x["y"] for x in t]
                self.assertTrue(all(a - b >= 1.5 * 45 for a, b in zip(ys, ys[1:])))

    def test_kabin_cizilmez(self):
        """Kesit en alt duraktaki kabinin altından geçer:  kabin bu planda yoktur,
        izi de çizilmez."""
        for ad, g in _dip_projeler():
            e = kuyu_dibi.ciz(g)
            with self.subTest(proje=ad):
                self.assertFalse(
                    [
                        x.get("ad")
                        for x in e
                        if "kabin" in (x.get("ad") or "")
                        and x.get("ad") not in ("kabin_tamponu", "kabin_ray")
                    ]
                )
                self.assertFalse([x["katman"] for x in e if x["katman"].startswith("KABIN")])

    def test_tamponlar_eksenlerde(self):
        g = _ornek()
        Y = kuyu_dibi.yerlesim(g)
        kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
        ry = g["kabin_ray"]["kapi_arasi"]
        self.assertEqual(kutu_merkezi(Y["kabin_tamponlari"][0]), (kx, ry))
        self.assertEqual(kutu_merkezi(Y["agirlik_tamponlari"][0]), kutu_merkezi(Y["blok"]))
        Y = kuyu_dibi.yerlesim(_ornek(kuyu_dibi={"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600}))
        self.assertEqual([kutu_merkezi(t) for t in Y["kabin_tamponlari"]], [(kx - 300, ry), (kx + 300, ry)])

    def test_perde_agirligin_boyunca(self):
        """m.5.2.5.5.1 d:  perde en az ağırlığın genişliği kadar."""
        for ad, g in _dip_projeler():
            Y = kuyu_dibi.yerlesim(g)
            p, b = Y["perde"], Y["blok"]
            with self.subTest(proje=ad):
                if p[0] == p[2]:
                    self.assertLessEqual(p[1], b[1])
                    self.assertGreaterEqual(p[3], b[3])
                    self.assertTrue(b[2] < p[0] or p[0] < b[0])
                else:
                    self.assertLessEqual(p[0], b[0])
                    self.assertGreaterEqual(p[2], b[2])
                    self.assertLess(p[1], b[1])

    def test_perde_ucunda_300_den_buyuk_bosluk_kalmaz(self):
        """m.5.2.5.5.1 e:  ağırlık rayları ile duvar arası 0,30 m'yi aşıyorsa o
        bölge de korunur — standart düzenlerin hiçbirinde perdenin ucu ile duvar
        arasında 300'den büyük boşluk kalmaz ( eskiden 54 düzenin 50'sinde
        340 – 365 kalıyordu );  merdiven korunan bölgede durmaz."""
        from testler import test_yerlesim_saglamligi

        sayi = 0
        for Q in test_yerlesim_saglamligi.KABIN:
            for yer in ("Sağ", "Sol", "Arka"):
                g, hata = test_yerlesim_saglamligi.gecerli_duzen(Q, yer)
                if hata:  # 320 kg arkada:  gerçek ret
                    continue
                Y = kuyu_dibi.yerlesim(g)
                self.assertIn("perde", Y, (Q, yer, Y.get("hata")))
                p, m = Y["perde"], Y.get("merdiven")
                G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
                uclar = (p[1], D - p[3]) if p[0] == p[2] else (p[0], G - p[2])
                with self.subTest(Q=Q, yer=yer):
                    sayi += 1
                    self.assertLessEqual(max(uclar), kuyu_dibi.PERDE_BOSLUGU_AZAMI)
                    #  merdiven perde ile ağırlığın duvarı arasındaki korunan bölgede değil
                    if m is not None:
                        bolge = (
                            (p[0], p[1], G, p[3])
                            if yer == "Sağ"
                            else (0.0, p[1], p[0], p[3])
                            if yer == "Sol"
                            else (p[0], p[1], p[2], D)
                        )
                        self.assertFalse(
                            m[0] < bolge[2] - 1e-6
                            and bolge[0] < m[2] - 1e-6
                            and m[1] < bolge[3] - 1e-6
                            and bolge[1] < m[3] - 1e-6,
                            m,
                        )
        self.assertGreater(sayi, 20)

    def test_siginma_cizelge_4_kabinin_altinda(self):
        for ad, g in _dip_projeler():
            Y = kuyu_dibi.yerlesim(g)
            s, kb = Y["siginma"], Y["kabin"]
            with self.subTest(proje=ad):
                self.assertEqual(
                    sorted((s[2] - s[0], s[3] - s[1])),
                    sorted(kuyu_dibi.SIGINMA[g["kuyu_dibi"]["siginma_tipi"]]),
                )
                self.assertTrue(kb[0] <= s[0] and s[2] <= kb[2] and kb[1] <= s[1] and s[3] <= kb[3])
                engel = (
                    Y["kabin_tamponlari"]
                    + Y["agirlik_tamponlari"]
                    + [Y["gergi"]]
                    + Y["kabin_raylari"]
                    + Y["agirlik_raylari"]
                    + ([Y["merdiven"]] if Y["merdiven"] else [])
                )
                for p in engel:
                    self.assertFalse(ortusur(s, p), p)

    def test_merdiven_ek_f(self):
        for ad, g in _dip_projeler():
            Y = kuyu_dibi.yerlesim(g)
            m = Y["merdiven"]
            with self.subTest(proje=ad):
                if g["kuyu_dibi"]["derinlik"] > kuyu_dibi.MERDIVEN_AZAMI_DERINLIK:
                    self.assertIsNone(m)
                    continue
                G, kp = g["kuyu"]["genislik"], g["kapi"]
                self.assertTrue(m[0] == 0 or m[2] == G)  # yan duvara yaslı
                kenar = kp["sol_pay"] if m[0] == 0 else kp["sol_pay"] + kp["genislik"]
                dx = max(0.0, m[0] - kenar, kenar - m[2])
                self.assertLessEqual((dx**2 + m[1] ** 2) ** 0.5, kuyu_dibi.MERDIVEN_KAPI_AZAMI)

    def test_genis_kuyuda_merdiven_kapinin_yaninda(self):
        #  3 m genişlikte kuyu, kapı kabin ekseninde:  sağ duvara 820, sola 1.080 —
        #  yan duvara yaslanan merdiven kapıdan 800'den uzak.  Ek F.5 b yalnız
        #  kapı kenarına uzaklığı sınırlar:  merdiven kapının yanında ön duvara
        #  yaslanır ( eskiden proje reddediliyordu ).
        g = _ornek(kuyu={"genislik": 3000}, kapi={"sol_pay": 1180})
        self.assertEqual(geometri.dogrula(g), [])
        self.assertFalse(any("Ek F.5 b" in h for h in kuyu_dibi.dogrula(g)), kuyu_dibi.dogrula(g))
        m, kp = kuyu_dibi.yerlesim(g)["merdiven"], g["kapi"]
        x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
        self.assertEqual(m[1], 0.0)  # ön duvarda
        self.assertTrue(m[2] <= x0 or m[0] >= x1, m)  # kapı boşluğunun dışında
        self.assertLessEqual(max(x0 - m[2], m[0] - x1), kuyu_dibi.MERDIVEN_KAPI_AZAMI)

    def test_merdiven_kapi_unitesine_ve_kabinin_yoluna_binmez(self):
        """Ek F.2.3:  merdiven en alt durağın eşiğinin 1,10 m üstüne uzanır — planda en
        alt kat kapısının ünitesine ( kasa, eşik, kanatlar, kanat cebi ) ve eşik altı
        sacına binmez;  kabinden ve kabinle kuyu tabanına inen kabin kapısından ( eşik,
        kanatlar, cep ) en az KABIN_YOLU_ACIKLIGI uzakta durur ( Tavaslıoğlu 1.2.4.1 g ).
        Eskiden 223 çizilen standart düzenin 60'ında kapının ünitesine, 4'ünde eşik altı
        sacına, 48'inde kabin kapısının cebine giriyordu.  Bütün kapı tipleri, üç
        ağırlık yeri, iki montaj — denetim kuyu planının ( C-C ) parçalarıyla."""
        from motor.uygulama import mukavemet_tablolari
        from testler import test_yerlesim_saglamligi

        kapi_unitesi = ("kapi_kasasi", "kat_esigi", "kat_kanadi", "kanat_cebi", "kanat_durdurucu")
        kabin = ("kabin_dis", "kabin_esigi", "kabin_kanadi", "kabin_kanat_cebi")
        a = kuyu_dibi.KABIN_YOLU_ACIKLIGI
        md = sabitler.sabitler()["merdiven_derinlik"]
        sayi, yakin = 0, 0
        for Q in (450, 1000, 1600):
            for yer in ("Sağ", "Sol", "Arka"):
                for tip in mukavemet_tablolari.KAPI_TIPLERI:
                    for montaj in ("Kuyu içine", "Duvar boşluğuna"):
                        ek = (
                            {
                                "aski_duzeni": "Kabin üstü",
                                "son_kat_yuksekligi": 5000,
                                "makine_raya_biniyor": "Bina yapısına",
                            }
                            if yer == "Arka"
                            else {}
                        )
                        v = test_yerlesim_saglamligi.standart_istek(
                            Q, True, yer, kat_kapisi_tipi=tip, kapi_montaji=montaj, **ek
                        )
                        if yer == "Arka":
                            v["asansorler"][0]["kuyu_derinligi"] = test_yerlesim_saglamligi.KABIN[Q][1] + 700
                        g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(v)
                        if hata or kuyu_dibi.dogrula(g):
                            continue
                        m = kuyu_dibi.yerlesim(g)["merdiven"]
                        if m is None:
                            continue
                        sayi += 1
                        plan = [el for el in geometri.plan(g) if el["tip"] == "dikdortgen"]
                        sac = girdi.esik_alti_saci(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
                        with self.subTest(Q=Q, yer=yer, tip=tip, montaj=montaj, merdiven=m):
                            for el in plan:
                                k = (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])
                                if el.get("ad") in kapi_unitesi:
                                    self.assertFalse(ortusur(m, k), el["ad"])
                                if el.get("ad") in kabin:
                                    self.assertFalse(ortusur(m, k, a), el["ad"])
                            self.assertFalse(
                                ortusur(m, (sac["x"][0], sac["u"] - sac["pah"][0], sac["x"][1], sac["u"])),
                                "eşik altı sacı",
                            )
                        #  Kanat cebi yan duvardaki merdivenin yerine ( duvardan md + a )
                        #  uzanıyor mu — eskiden merdivenin girdiği düzenler
                        G = g["kuyu"]["genislik"]
                        yakin += any(
                            el.get("ad") in ("kanat_cebi", "kabin_kanat_cebi")
                            and (el["x"] < md + a or el["x"] + el["g"] > G - md - a)
                            for el in plan
                        )
        self.assertGreater(sayi, 60)
        self.assertGreater(yakin, 20)

    def test_merkezi_kapida_merdivene_yer_yoksa_ret(self):
        """Arkada ağırlık, 1000 kg, merkezi kapı:  iki kanat cebi de yan duvarlara 95 mm
        kalıyor;  merdiven yan duvarda kabin kapısının cebinin 50 mm arkasıyla ray
        konsolunun plakası arasına sığmıyor ( 330 mm yer, merdiven 350 ) — kapıdan 800
        mm'den uzağa da konamaz:  proje sebebiyle reddedilir ( 4 Kas, kullanıcı 50 mm
        açıklığı seçti;  eskiden merdiven iki cebin de içinden geçiyordu )."""
        from testler import test_yerlesim_saglamligi

        v = test_yerlesim_saglamligi.standart_istek(
            1000,
            True,
            "Arka",
            kat_kapisi_tipi="Otomatik Merkezi",
            aski_duzeni="Kabin üstü",
            son_kat_yuksekligi=5000,
            makine_raya_biniyor="Bina yapısına",
        )
        v["asansorler"][0]["kuyu_derinligi"] = test_yerlesim_saglamligi.KABIN[1000][1] + 700
        g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(v)
        self.assertFalse(hata, hata)
        self.assertEqual(geometri.dogrula(g), [])
        Y = kuyu_dibi.yerlesim(g)
        self.assertIsNone(Y["merdiven"])
        ileti = [h for h in Y["hata"] if "Ek F.5 b" in h]
        self.assertEqual(len(ileti), 1, Y["hata"])
        self.assertIn("Ek F.2.3", ileti[0])
        self.assertIn("kabin kapısının cebi", ileti[0])
        self.assertEqual(ileti[0].parcalar, ("merdiven",))

    def test_perde_kabinin_yolundan_gecmez(self):
        """m.5.2.5.5.1 b:  perde kuyu tabanından en az 2,0 m yükseğe çıkar — kabin en
        alttayken kabin kapısı o yüksekliğin içine iner:  perdenin uzayan ucu kabin
        kapısından ( eşik, kanatlar, cep ) KABIN_YOLU_ACIKLIGI önce biter.  Eskiden kat
        kapısının ünitesine dek uzuyor, örnek projelerde kabin kapısının cebinin
        içinden geçiyordu ( x 252 · cep 250 – 730 )."""
        a = kuyu_dibi.KABIN_YOLU_ACIKLIGI
        for ad, g in _dip_projeler():
            Y = kuyu_dibi.yerlesim(g)
            p = Y["perde"]
            for el in Y["taban"]:
                if el["tip"] != "dikdortgen" or el.get("ad") not in kuyu_dibi.KABIN_KAPISI:
                    continue
                k = (el["x"] - a, el["y"] - a, el["x"] + el["g"] + a, el["y"] + el["d"] + a)
                for c in [p] + Y["perde_donusu"]:  # perde ve duvara dönen kolu
                    with self.subTest(proje=ad, parca=el["ad"], cizgi=c):
                        if c[0] == c[2]:
                            lo, hi = sorted((c[1], c[3]))
                            self.assertFalse(k[0] < c[0] < k[2] and lo < k[3] and k[1] < hi, (c, k))
                        else:
                            lo, hi = sorted((c[0], c[2]))
                            self.assertFalse(k[1] < c[1] < k[3] and lo < k[2] and k[0] < hi, (c, k))

    def test_perde_kabinin_yolunda_bitince_duvara_doner(self):
        """m.5.2.5.5.1 e:  ray – duvar arası 0,30 m'yi aşıyorsa korunur.  Perde kabinin
        yolunda ( kabin kapısının cebinden KABIN_YOLU_ACIKLIGI önce ) bitince ucu ile ön
        duvar arası 320 mm kalıyordu ( örnek projeler ) — perde oradan ağırlığın yan
        duvarına döner, ağırlığın bölgesi önden kapanır.  Kat kapısının ünitesi boşluğu
        kapatmaz:  durak döşemesindedir, perdenin 0,30 – 2,0 m bandının altı açıktır."""
        a = kuyu_dibi.KABIN_YOLU_ACIKLIGI
        for ad, g in _dip_projeler():
            Y = kuyu_dibi.yerlesim(g)
            p, G = Y["perde"], g["kuyu"]["genislik"]
            if Y["ag_yan"] not in ("Sol", "Sağ"):
                continue
            cep = next(
                el
                for el in Y["taban"]
                if el.get("ad") == "kabin_kanat_cebi" and el["x"] < p[0] < el["x"] + el["g"]
            )
            duvar = G if Y["ag_yan"] == "Sağ" else 0.0
            with self.subTest(proje=ad):
                #  perde cebin 50 mm önünde biter, dönüş aynı hizadan ağırlığın duvarına
                self.assertAlmostEqual(p[1], cep["y"] + cep["d"] + a)
                self.assertEqual(Y["perde_donusu"], [(p[0], p[1], duvar, p[1])])
                #  ağırlığın parçaları dönüşün arkasında
                self.assertLess(p[1], Y["blok"][1])
                self.assertTrue(all(r[1] > p[1] for r in Y["agirlik_raylari"]))
                #  çizimde de var:  iki PERDE çizgisi
                e = kuyu_dibi.ciz(g)
                self.assertEqual(sum(1 for el in e if el.get("ad") == "perde"), 2)

    def test_perde_donusu_standart_duzenlerde_yok(self):
        """Dönüş yalnız boşluk kalınca:  standart düzenlerde perde ucu ile duvar arası
        zaten 300'ü aşmaz ( test_perde_ucunda_300_den_buyuk_bosluk_kalmaz )."""
        from testler import test_yerlesim_saglamligi

        for Q in test_yerlesim_saglamligi.KABIN:
            for yer in ("Sağ", "Sol", "Arka"):
                g, hata = test_yerlesim_saglamligi.gecerli_duzen(Q, yer)
                if hata:
                    continue
                with self.subTest(Q=Q, yer=yer):
                    self.assertEqual(kuyu_dibi.yerlesim(g)["perde_donusu"], [])

    def test_perdeyi_uzat_kapanmayan_engel(self):
        """_perdeyi_uzat:  durduran ama kapatmayan parçada ( yol ) biten perde, ötesinde
        300'den büyük boşluk varsa duvara döner;  sabit parçada biterse dönmez."""
        perde = (250.0, 700.0, 250.0, 1500.0)
        yol = [(200.0, 100.0, 700.0, 320.0)]
        p, korunan, donus = kuyu_dibi._perdeyi_uzat(perde, "Sol", 2000.0, 1700.0, [], yol)
        self.assertEqual(p, (250.0, 320.0, 250.0, 1500.0))
        self.assertEqual(korunan, [(0.0, 320.0, 250.0, 700.0)])
        self.assertEqual(donus, [(250.0, 320.0, 0.0, 320.0)])
        #  aynı kutu sabitse:  perde orada biter, dönmez
        p, _, donus = kuyu_dibi._perdeyi_uzat(perde, "Sol", 2000.0, 1700.0, yol, [])
        self.assertEqual((p, donus), ((250.0, 320.0, 250.0, 1500.0), []))
        #  yolun ötesinde boşluk 300'ü aşmıyorsa dönmez
        p, _, donus = kuyu_dibi._perdeyi_uzat(perde, "Sol", 2000.0, 1700.0, [(0, 0, 300, 100)], yol)
        self.assertEqual(donus, [])
        #  sağdaki ağırlık:  sağ duvara;  dönüş yolu bir sabit parça keserse onda biter
        perde = (1750.0, 700.0, 1750.0, 1500.0)
        yol = [(1300.0, 100.0, 1800.0, 320.0)]
        _, _, donus = kuyu_dibi._perdeyi_uzat(perde, "Sağ", 2000.0, 2000.0, [(1900, 300, 2000, 400)], yol)
        self.assertEqual(donus, [(1750.0, 320.0, 1900, 320.0)])
        #  arkadaki ağırlık:  arka duvara
        perde = (700.0, 1500.0, 1300.0, 1500.0)
        yol = [(300.0, 1400.0, 500.0, 1800.0)]
        p, _, donus = kuyu_dibi._perdeyi_uzat(perde, None, 2000.0, 2000.0, [], yol)
        self.assertEqual(p, (500.0, 1500.0, 2000.0, 1500.0))
        self.assertEqual(donus, [(500.0, 1500.0, 500.0, 2000.0)])

    def test_standart_tablolari(self):
        """Ölçüler standardın kendi sayılarıyla sabitlenir ( tablo kendisiyle
        kıyaslanırsa yanlış bir sayı testten geçerdi )."""
        self.assertEqual(
            kuyu_dibi.SIGINMA,
            {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0), "Yatarak": (700.0, 1000.0)},
        )  # Çizelge 4
        self.assertEqual(
            kabin_ustu.SIGINMA, {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0)}
        )  # Çizelge 3
        self.assertEqual((kuyu_dibi.MERDIVEN_AZAMI_DERINLIK, kuyu_dibi.MERDIVEN_KAPI_AZAMI), (2500.0, 800.0))
        #  Ek F.2.3 ( eşiğin 1,10 m üstü ) · Tavaslıoğlu 1.2.4.1 g ( merdiven – kabin 50 mm )
        #  · m.5.2.5.5.1 b ( perde kuyu tabanından 2,0 m )
        self.assertEqual(
            (
                kuyu_dibi.MERDIVEN_ESIK_USTU,
                kuyu_dibi.KABIN_YOLU_ACIKLIGI,
                standart.AGIRLIK_PERDESI_YUKSEKLIGI,
            ),
            (1100.0, 50.0, 2000.0),
        )
        self.assertEqual(
            (
                standart.KORKULUK_BOSLUK,
                standart.KORKULUK_KENAR_AZAMI,
                standart.KORKULUK_PARCA_ASGARI,
                standart.KORKULUK_YUKSEKLIK_SINIRI,
                standart.KORKULUK_ALCAK,
                standart.KORKULUK_YUKSEK,
            ),
            (300.0, 150.0, 100.0, 500.0, 700.0, 1100.0),
        )
        self.assertEqual(
            (girdi.KAPI_ARASI_AZAMI, girdi.ESIK_ARASI_AZAMI, girdi.KABIN_AGIRLIK_ACIKLIGI),
            (150.0, 35.0, 50.0),
        )

    def test_merdiven_2500_sinirinda(self):
        for derinlik, var in ((2500, True), (2501, False)):
            Y = kuyu_dibi.yerlesim(_ornek(kuyu_dibi={"derinlik": derinlik}))
            with self.subTest(derinlik=derinlik):
                self.assertEqual(Y["merdiven"] is not None, var)

    def test_yuk_noktalari_hesap_paftasi_adlariyla(self):
        e = kuyu_dibi.ciz(_ornek(kuyu_dibi={"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600}))
        adlar = [el["metin"] for el in e if el.get("ad") == "yuk"]
        #  İki tamponda her birine düşen:  hesap paftasındaki Fkt1 = Fkt / ncar
        self.assertEqual(sorted(adlar), sorted(["FKR", "FKR", "FAR", "FAR", "Fkt1", "Fkt1", "Fat"]))

    def test_olcu_zincirleri_ve_yazilar(self):
        import itertools

        for ad, g in _dip_projeler():
            e = kuyu_dibi.ciz(g)
            for z in geometri.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])

    def test_dxf_temiz(self):
        from cizim import dxf
        from ezdxf.audit import Auditor

        d = dxf.belge(kuyu_dibi.ciz(_ornek()), "KUYU DİBİ", 20)
        a = Auditor(d)
        a.run()
        self.assertEqual(list(a.errors), [])
        for kat in ("TAMPON", "PERDE", "MERDIVEN", "GIZLI"):
            self.assertIn(kat, d.layers)

    def test_arka_agirlik_raylari_konsollu(self):
        e = geometri.plan(_arka())
        plakalar = [el for el in _dikdortgenler(e, "KONSOL") if el.get("ad") == "plaka"]
        self.assertEqual(len(plakalar), 4)
        D = _arka()["kuyu"]["derinlik"]
        self.assertEqual(sum(1 for el in plakalar if abs(el["y"] + el["d"] - D) < 1e-6), 2)


#  ─────────────────────────────────────────────────────────────────────
#  KUYU ÜSTÜ PLANI  ( makine dairesiz )
#  ─────────────────────────────────────────────────────────────────────
from cizim import kuyu_ustu


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
                self.assertEqual(kuyu_ustu.dogrula(g), [])

    def test_referans_olculeriyle_birebir(self):
        """referans proje MRL paftasının vektör ölçüleri ( mm, kuyunun sol-ön iç köşesinden )."""
        Y = kuyu_ustu.yerlesim(_ornek())
        self.assertEqual((Y["kasnak"][0], Y["kasnak"][2]), (130, 370))
        self.assertEqual((Y["govde"][0], Y["govde"][2]), (101, 399))
        self.assertEqual((Y["agirlik_baglanti"][0], Y["agirlik_baglanti"][2]), (118, 382))
        self.assertEqual((Y["kabin_baglanti"][0], Y["kabin_baglanti"][2]), (1890, 2017))
        self.assertEqual(Y["sapma"], (0, 0))

    def test_halatlar_duseye_iner(self):
        for ad, g in _ust_projeler():
            Y = kuyu_ustu.yerlesim(g)
            xl, xr = Y["halatlar"][0][0], Y["halatlar"][1][0]
            ks = Y["kasnak"]
            with self.subTest(proje=ad):
                #  tahrik kasnağının bir teğeti kabinin yakın halatında
                self.assertTrue(abs(ks[2] - xl) < 1e-9 or abs(ks[0] - xr) < 1e-9)
                self.assertAlmostEqual(ks[2] - ks[0], g["makine"]["tahrik_kasnak_capi"])
                olculer = [el for el in kuyu_ustu.ciz(g) if el["tip"] == "olcu"]
                #  Sapma varsa ölçülür:  kendi ölçüsüyle ya da aynı aralığı ölçen
                #  zincirle ( 13 Eki — her ölçü bir kez );  yoksa HALAT SAPMASI yok
                for v, yon in zip(Y["sapma"], ("yatay", "dusey")):
                    if abs(v) > 0.5:
                        self.assertTrue(
                            any(o["yon"] == yon and abs(o["uzunluk"] - abs(v)) < 0.5 for o in olculer),
                            (yon, v),
                        )
                if not any(abs(v) > 0.5 for v in Y["sapma"]):
                    self.assertFalse([o for o in olculer if o["metin"].startswith("HALAT SAPMASI")])
        self.assertEqual(kuyu_ustu.yerlesim(_ornek(makine={"tahrik_kasnak_capi": 200}))["sapma"], (40, 0))

    def test_regulator_gergi_kasnaginin_ustunde(self):
        for ad, g in _ust_projeler():
            ust, dip = kuyu_ustu.yerlesim(g)["reg_kasnak"], kuyu_dibi.yerlesim(g)["gergi"]
            with self.subTest(proje=ad):
                self.assertAlmostEqual((ust[0] + ust[2]) / 2.0, (dip[0] + dip[2]) / 2.0)
                self.assertAlmostEqual((ust[1] + ust[3]) / 2.0, (dip[1] + dip[3]) / 2.0)

    def test_acil_pano_ve_calisma_alani(self):
        """m.5.2.6.6.4 → m.5.2.6.3.2.1 a:  0,70 m derin, en az 0,50 m ya da pano eni."""
        for en, beklenen in ((400, 500), (600, 600)):
            g = _ornek()
            g["_cizim_sabitleri"] = {"acil_pano_en": en}
            Y = kuyu_ustu.yerlesim(g)
            p, c = Y["pano"], Y["calisma"]
            with self.subTest(pano_eni=en):
                self.assertLessEqual(p[3], -g["kuyu"]["duvar_on"])  # kuyunun dışında
                self.assertEqual(c[3] - c[1], 700)
                self.assertEqual(c[2] - c[0], beklenen)
                self.assertEqual(c[3], p[1])

    def test_desteklenmeyen_duzenler_reddedilir(self):
        self.assertTrue(kuyu_ustu.dogrula(_ornek(agirlik={"yeri": "Arka"})))
        self.assertTrue(kuyu_ustu.dogrula(_ornek(kuyu_ustu={"acil_pano_yan": "Arka"})))

    def test_kabin_ustu_askida_halatlar_ayni_yerden_iner(self):
        #  Kasnaklar kabinin üstünde de planda aynı yerde:  halat, makine ve
        #  bağlantılar kabin altı askıdakiyle aynı noktalarda
        alt, ust = kuyu_ustu.yerlesim(_ornek()), kuyu_ustu.yerlesim(_ornek(aski={"duzen": "Kabin üstü"}))
        self.assertEqual(ust["hata"], [])
        for k in ("halatlar", "kasnak", "agirlik_baglanti", "kabin_baglanti"):
            self.assertEqual(ust[k], alt[k], k)

    def test_parcalar_ust_uste_binmez(self):
        #  Regülatör kabin halat bağlantısının üstüne kaydırılınca reddedilir
        h = kuyu_ustu.dogrula(_ornek(kuyu_dibi={"regulator_kaciklik": -250}))
        self.assertTrue(any("üst üste" in x for x in h), h)

    def test_olcu_zincirleri_yazilar_dxf(self):
        import itertools
        from cizim import dxf
        from ezdxf.audit import Auditor

        for ad, g in _ust_projeler():
            e = kuyu_ustu.ciz(g)
            for z in geometri.zincirler(e):
                with self.subTest(proje=ad, zincir=z):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
            k = OlcuYazilari._kutular(None, e)
            for a, b in itertools.combinations(k, 2):
                with self.subTest(proje=ad, a=a[0]["metin"], b=b[0]["metin"]):
                    self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])
            d = dxf.belge(e, "KUYU ÜSTÜ", 20)
            a = Auditor(d)
            a.run()
            self.assertEqual(list(a.errors), [])

    def test_calisma_alani_standart_sayilari(self):
        self.assertEqual((kuyu_ustu.CALISMA_DERINLIK, kuyu_ustu.CALISMA_EN_ASGARI), (700.0, 500.0))


#  ─────────────────────────────────────────────────────────────────────
#  MAKİNE DAİRESİ PLANI  ve  DÖŞEME HALAT DELİK PLANI
#  ─────────────────────────────────────────────────────────────────────
from cizim import makine_dairesi


def _md_projeler():
    yield "Sol", _ornek()
    g = _sag_ayna()
    g["kuyu_dibi"] = dict(g["kuyu_dibi"], regulator_yan="Sol")
    g["makine_dairesi"] = dict(g["makine_dairesi"], pano_duvar="Sol", kapi_konum=1500)
    yield "Sağ", g
    yield "Pano ön duvarda", _ornek(makine_dairesi={"pano_duvar": "Ön"})


class MakineDairesi(unittest.TestCase):
    def test_merdiven_notu_panoya_binmez(self):
        """Pano tabliyenin önündeki zemindeyse kot farkı notu panoya, çalışma
        alanına ve ölçülerine binmez.  Eskiden hep kenarın ortasında 300
        içerideydi:  çalışma alanının ( y 2.000 – 2.600 ) içine düşüyordu
        ( girdi taraması, oda grubu, 17 Eki )."""
        g = _ornek(
            makine={"yeri": "Makine dairesi"},
            makine_dairesi={"kapi_duvar": "Ön", "pano_duvar": "Sol", "tabliye_yuksekligi": 600},
        )
        self.assertEqual(makine_dairesi.dogrula(g), [])
        Y = makine_dairesi.yerlesim(g)
        es = [el for el in makine_dairesi.ciz(g) if el.get("ad") == "merdiven_notu"]
        self.assertTrue(es)
        p = makine_dairesi.NOT_PAYI
        for el in es:
            w, h = eleman.yazi_eni(el["metin"], el["yukseklik"]) / 2.0, 0.6 * el["yukseklik"]
            yazi = (el["x"] - w, el["y"] - h, el["x"] + w, el["y"] + h)
            for k in (Y["pano"], Y["calisma"]):
                self.assertFalse(ortusur(yazi, (k[0] - p, k[1] - p, k[2] + p, k[3] + p)), (el["metin"], k))

    def test_merdiven_notu_odanin_icinde(self):
        """Kot farkı notu odanın içinde kalır:  dar odada iki satır.  Eskiden hep
        tek satırdı — 2.100'lük odada iki yandaki duvarın içine taşıyordu
        ( 63444-2 A BLOK, 17 Eki ).  Örnekte 2.200:  2.100'lük odaya örneğin
        kaidesi ayak plakalarıyla sığmaz ( PR #26 )."""
        for gen, x, satir in ((2200, -50, 2), (2600, -250, 1)):
            with self.subTest(oda=gen):
                g = _ornek(
                    makine={"yeri": "Makine dairesi"},
                    makine_dairesi={"genislik": gen, "x": x, "tabliye_yuksekligi": 1500},
                )
                self.assertEqual(makine_dairesi.dogrula(g), [])
                oda = makine_dairesi.yerlesim(g)["oda"]
                es = [el for el in makine_dairesi.ciz(g) if el.get("ad") == "merdiven_notu"]
                self.assertEqual(len(es), satir)
                for el in es:
                    w = eleman.yazi_eni(el["metin"], el["yukseklik"]) / 2.0
                    self.assertGreater(el["x"] - w, oda[0], el["metin"])
                    self.assertLess(el["x"] + w, oda[2], el["metin"])

    def test_ornekler_gecerli(self):
        for ad, g in _md_projeler():
            with self.subTest(proje=ad):
                self.assertEqual(makine_dairesi.dogrula(g), [])

    def test_makine_ve_halatlar_kuyu_ustuyle_ayni(self):
        """Makine daireli ve dairesiz projede halatlar aynı noktalardan iner."""
        g = _ornek()
        M, K = makine_dairesi.yerlesim(g)["M"], kuyu_ustu.yerlesim(g)
        for anahtar in ("kasnak", "govde", "halatlar", "ag_dusus", "ag_teget2", "reg_kasnak"):
            self.assertEqual(M[anahtar], K[anahtar], anahtar)

    def test_delikler_halat_demetine_gore(self):
        g = _ornek()
        Y = makine_dairesi.yerlesim(g)
        a, p = g["aski"], sabitler.sabitler(g.get("_cizim_sabitleri"))["halat_delik_payi"]
        demet = (a["halat_adedi"] - 1) * 1.6 * a["halat_capi"] + a["halat_capi"]
        self.assertAlmostEqual(Y["demet"], demet)
        d = dict(Y["delikler"][:4])
        boy, en = demet + 2 * p, a["halat_capi"] + 2 * p
        for ad in ("KABİN", "AĞIRLIK", "KABİN BAĞLANTISI"):  # kasnak ekseni ( y ) boyunca
            self.assertAlmostEqual(d[ad][2] - d[ad][0], en)
            self.assertAlmostEqual(d[ad][3] - d[ad][1], boy)
        k = d["AĞIRLIK BAĞLANTISI"]  # ağırlık kasnağı ekseni ( x )
        self.assertAlmostEqual(k[2] - k[0], boy)
        self.assertAlmostEqual(k[3] - k[1], en)
        #  Delikler halatların tam üstünde
        M = Y["M"]
        merkez = lambda q: ((q[0] + q[2]) / 2.0, (q[1] + q[3]) / 2.0)
        self.assertEqual(merkez(d["KABİN"]), (M["yakin"], M["halatlar"][0][1]))
        self.assertEqual(merkez(d["AĞIRLIK BAĞLANTISI"]), M["ag_teget2"])

    def test_regulator_delikleri_halat_capindan(self):
        """Regülatör halatının deliği de ana halatlarınki gibi:  çap + 2 × pay
        ( 6 + 60 = 66 ).  Eskiden LiftDesigner'ın 200 × 200'ü kullanılıyordu:
        ø240 regülatörde iki delik arasında 40 mm beton, kuyu duvarına 14 mm
        kalıyordu.  Çap girilmezse çizim durur."""
        g = _ornek(kuyu_dibi={"regulator_kasnak_capi": 240})
        Y = makine_dairesi.yerlesim(g)
        self.assertEqual(Y["hata"], [])
        rd = [d for ad, d in Y["delikler"] if ad == "REGÜLATÖR"]
        p = sabitler.sabitler(g.get("_cizim_sabitleri"))["halat_delik_payi"]
        e = g["kuyu_dibi"]["regulator_halat_capi"] + 2 * p
        self.assertEqual(e, 66)
        self.assertEqual({(round(d[2] - d[0], 6), round(d[3] - d[1], 6)) for d in rd}, {(e, e)})
        self.assertEqual(round(rd[1][1] - rd[0][3], 6), 240 - e)  # 174 mm beton
        G = g["kuyu"]["genislik"]
        self.assertGreater(min(G - d[2] for d in rd), 50)
        h = makine_dairesi.dogrula(_ornek(kuyu_dibi={"regulator_halat_capi": None}))
        self.assertTrue(any("regulator_halat_capi" in x for x in h), h)

    def test_delik_kuyunun_disina_dusmez(self):
        h = makine_dairesi.dogrula(_ornek(kuyu_dibi={"regulator_kasnak_capi": 1600}))
        self.assertTrue(any("kuyunun dışına" in x for x in h), h)

    def test_kapi_600_sinirinda(self):
        for en, uygun in ((600, True), (599, False)):
            h = makine_dairesi.dogrula(_ornek(makine_dairesi={"kapi_genislik": en}))
            with self.subTest(kapi=en):
                self.assertEqual(not any("m.5.2.3.2 a" in x for x in h), uygun)

    def test_pano_calisma_alani_ve_bakim_alani(self):
        for ad, g in _md_projeler():
            Y = makine_dairesi.yerlesim(g)
            p, c, b, oda = Y["pano"], Y["calisma"], Y["bakim"], Y["oda"]
            with self.subTest(proje=ad):
                pe = sabitler.sabitler()["kumanda_pano_en"]
                olcu = sorted((c[2] - c[0], c[3] - c[1]))
                self.assertEqual(olcu, sorted((700.0, max(500.0, pe))))
                self.assertEqual(sorted((b[2] - b[0], b[3] - b[1])), [500.0, 600.0])
                engel = [q for _, q in Y["delikler"]] + [Y["makine"], Y["kapi_onu"]]
                for alan in (p, c, b):
                    self.assertTrue(makine_dairesi.icinde(alan, oda))
                    for q in engel:
                        self.assertFalse(ortusur(alan, q), (alan, q))
                #  bakım alanı makineye bitişik
                m = Y["makine"]
                self.assertTrue(b[0] == m[2] or b[2] == m[0] or b[1] == m[3] or b[3] == m[1])

    def test_kucuk_odada_reddedilir(self):
        #  Pano ön duvarda:  2.400'de her şey sığar;  2.100 × 2.300'lük odada makinenin
        #  başında bakım alanı kalmaz ( kaide makineyi sardığından ve alanlara yer
        #  bırakan konumu seçtiğinden beri 2.600 genişlikte 2.200 derinlik yetiyor )
        #  ( kot farkı yok:  odanın ölçüsü sınanır — tabliye 1.200 olsaydı arka
        #  duvardaki kapının önü tabliyenin kenarına denk gelirdi, aşağıda )
        self.assertEqual(
            makine_dairesi.dogrula(
                _ornek(makine_dairesi={"derinlik": 2400, "pano_duvar": "Ön", "tabliye_yuksekligi": 0})
            ),
            [],
        )
        h = makine_dairesi.dogrula(
            _ornek(
                makine_dairesi={
                    "genislik": 2100,
                    "x": 0,
                    "derinlik": 2300,
                    "pano_duvar": "Ön",
                    "tabliye_yuksekligi": 0,
                }
            )
        )
        self.assertTrue(any("m.5.2.6.3.2.1" in x for x in h), h)
        h = makine_dairesi.dogrula(_ornek(makine_dairesi={"x": 600}))
        self.assertTrue(any("dışına taşıyor" in x for x in h), h)
        #  Tabliye 1.200:  oda kuyudan 250 derinse kapının önünde zemin yok
        h = makine_dairesi.dogrula(_ornek(makine_dairesi={"derinlik": 2400, "pano_duvar": "Ön"}))
        self.assertTrue(any("kapısının önü tabliyenin kenarına" in x for x in h), h)

    def test_standart_sayilari(self):
        self.assertEqual(
            (
                makine_dairesi.KAPI_ASGARI,
                makine_dairesi.BAKIM_ALANI,
                makine_dairesi.CALISMA_DERINLIK,
                makine_dairesi.CALISMA_EN_ASGARI,
            ),
            (600.0, (500.0, 600.0), 700.0, 500.0),
        )

    def test_olcu_zincirleri_yazilar_dxf(self):
        import itertools
        from cizim import dxf
        from ezdxf.audit import Auditor

        for ad, g in _md_projeler():
            for ciz in (makine_dairesi.ciz, makine_dairesi.delik_plani):
                e = ciz(g)
                for z in geometri.zincirler(e):
                    with self.subTest(proje=ad, cizim=ciz.__name__, zincir=z):
                        self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                k = OlcuYazilari._kutular(None, e)
                for a, b in itertools.combinations(k, 2):
                    with self.subTest(proje=ad, cizim=ciz.__name__, a=a[0]["metin"], b=b[0]["metin"]):
                        self.assertFalse(a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4])
                d = dxf.belge(e, "MAKİNE DAİRESİ", 20)
                au = Auditor(d)
                au.run()
                self.assertEqual(list(au.errors), [])

    def test_alan_olculeri_disarida_adlar_icinde(self):
        """Çalışma ve bakım alanının ölçüleri alanın DIŞINDA ( yer varsa ), adı alanın
        içinde;  hiçbir ad bir ölçü çizgisini silmez ( 7 Kas çizim denetimi 4. adımı:
        ölçüler alanın içindeydi, 529'luk "ÇALIŞMA ALANI" 600'lük alanda ölçü
        çizgisini siliyordu — taramada pano adıyla 251 ).  Ön duvardaki panoda bakım
        alanının 500'ü içeride:  alanın yanında yer yok ( eski yeri )."""
        icerde = {"Pano ön duvarda": {("bakim", "dusey")}}
        for ad, g in _md_projeler():
            e, Y = makine_dairesi.ciz(g), makine_dairesi.yerlesim(g)
            olculer = geometri.OlcuIzgarasi(e)
            for alan, metin in (("calisma", "ÇALIŞMA ALANI"), ("bakim", "BAKIM ALANI")):
                a = Y[alan]
                with self.subTest(proje=ad, alan=alan):
                    os_ = [
                        o
                        for o in e
                        if o["tip"] == "olcu" and o.get("kural") == makine_dairesi._ALAN_KURALLARI[alan]
                    ]
                    self.assertEqual(sorted(o["yon"] for o in os_), ["dusey", "yatay"])
                    for o in os_:
                        ic = a[0] < o["kot"] < a[2] if o["yon"] == "dusey" else a[1] < o["kot"] < a[3]
                        self.assertEqual(ic, (alan, o["yon"]) in icerde.get(ad, ()), o["yon"])
                    y = next(x for x in e if x["tip"] == "yazi" and x["metin"] == metin)
                    m = geometri.maske_kutusu(y)
                    self.assertTrue(a[0] <= m[0] and a[1] <= m[1] and m[2] <= a[2] and m[3] <= a[3], metin)
                    self.assertEqual(olculer.silinen(m, y), (0.0, 0))

    def test_pano_adi_panonun_icinde(self):
        """Pano adı panonun içinde, uzun kenarı boyunca;  tek satıra sığmazsa son sözden
        önce iki satır ( 665'lik "KUMANDA PANOSU" 600'lük panoya sığmıyordu, etiket
        ayırıcı onu ölçünün üstüne ya da oklu uzağa koyuyordu — altın 16 düzenin 15'i )."""

        def satirlar(pn, metin):
            return [
                (x["metin"], x["x"], x["y"], x.get("aci", 0)) for x in makine_dairesi._pano_adi(pn, metin)
            ]

        #  90°:  ilk satır solda ( yazının üstü −x yanında );  0°:  üstte
        self.assertEqual(
            satirlar((0, 0, 400, 600), "KUMANDA PANOSU"),
            [("KUMANDA", 144.0, 300.0, 90), ("PANOSU", 256.0, 300.0, 90)],
        )
        self.assertEqual(
            satirlar((0, 0, 600, 400), "KUMANDA PANOSU"),
            [("KUMANDA", 300.0, 256.0, 0), ("PANOSU", 300.0, 144.0, 0)],
        )
        self.assertEqual(
            [s_[0] for s_ in satirlar((0, 0, 400, 600), "ASANSÖR 1 PANOSU")], ["ASANSÖR 1", "PANOSU"]
        )
        #  Sığarsa tek satır;  iki satır da sığmazsa tek satır ortada ( ayırıcı taşır )
        self.assertEqual(
            satirlar((0, 0, 400, 1000), "KUMANDA PANOSU"), [("KUMANDA PANOSU", 200.0, 500.0, 90)]
        )
        self.assertEqual(satirlar((0, 0, 100, 200), "KUMANDA PANOSU"), [("KUMANDA PANOSU", 50.0, 100.0, 90)])
        for ad, g in _md_projeler():
            e, p = makine_dairesi.ciz(g), makine_dairesi.yerlesim(g)["pano"]
            with self.subTest(proje=ad):
                ys = [x for x in e if x.get("ad") == "pano_adi"]
                self.assertEqual(sorted(x["metin"] for x in ys), ["KUMANDA", "PANOSU"])
                for x in ys:
                    m = geometri.maske_kutusu(x)
                    self.assertTrue(p[0] <= m[0] and p[1] <= m[1] and m[2] <= p[2] and m[3] <= p[3], m)


#  ─────────────────────────────────────────────────────────────────────
#  DÜŞEY KESİTLER
#  ─────────────────────────────────────────────────────────────────────
from cizim import donanim
from cizim import dusey
from cizim import kuyu_kesiti
from cizim import veri_tablosu


class DuseyKesitler(unittest.TestCase):
    def test_ornek_gecerli_ve_elle_hesapla_ayni(self):
        g = _ornek()
        self.assertEqual(dusey.dogrula(g), [])
        Y = dusey.yerlesim(g)
        #  Patenlerin MERKEZLERİ arası hesabın paten arası ( kabin 3.300, ağırlık
        #  3.060 );  patenler kirişlerin ve çerçevenin DIŞINDA ( 8 Eki — referans
        #  projenin kesiti:  alt paten şase altının 70 altında ortalı, 140 boy ).
        #  Kuyu dibi:  kabin döşemesi −( 96 + 90 ) = −186;  platform altı −306,
        #  kasnak altı −186 − 295 − 120 = −601,  etek −186 − 750 − 35 = −971 ( dik kısım
        #  750 + pah 35 — m.5.4.5 ),  alt paten −186 − 480 − 70 − 70 = −806 ( 8 Eki'ye
        #  dek −736 ),  alt şase kirişinin altı ( şasenin altı ) −186 − 480 = −666:
        #  kabinin en alt kısmı odur ( kasnaktan alçak;  10 Eki'ye dek kiriş
        #  sayılmıyordu, en alt kısım kasnak −601 → 899 ),  sığınma alanının
        #  üstünde kabin tabanı ( alan kirişin ve kasnakların dışında )
        self.assertEqual(
            {k: v[0] for k, v in Y["dip_aciklik"].items()},
            {"siginma": 1194, "en_alt": 834, "etek": 529, "sase": 694},
        )
        self.assertEqual(Y["dip_engel"], {"siginma": "kabin tabanı", "en_alt": "alt şase kirişi"})
        #  Kuyu üstü:  yükselme 150 + 90 + 35 = 275;  tavan 275 + 2.310 = 2.585,
        #  kiriş altı 5.000 − 150 = 4.850;  üst paten 275 − 480 − 70 + 3.300 + 70 = 3.095.
        #  Makine şasesinin altı 5.000 − 250 − 345 − 200 = 4.205 ( referans proje ) ve
        #  şase soldaki patenin 0,40 m yakınında:  paten 4.205 − 3.095 = 1.110.
        #  Yakın kabin rayı şasede biter:  5.000 − 650 = 4.350 → 1.255.
        #  Korkuluk ( 3.685 ) — şase korkuluğun dışında ( 0,10 m ) → 520.
        #  Karşı ağırlık en üstte:  −1.040 + 150 + 21.000 + 96 + 90 + 35 = 20.331 ( çerçeve
        #  altı ),  çerçeve 3.060 − 140 = 2.920, üst paten 20.331 + 2.920 + 140 = 23.391;
        #  ağırlık rayı 26.000 − 650 = 25.350 → 1.959.
        #  Revizyon kutusu tavandan 500 yukarıda ( 3.085 );  kabinin izdüşümündeki
        #  en alt tavan parçası kabin halat bağlantısı 5.000 − 645 = 4.355 → 1.270.
        self.assertEqual(Y["yukselme"], 275)
        self.assertEqual(
            {k: v[0] for k, v in Y["ust_aciklik"].items()},
            {
                "siginma": 2265,
                "revizyon": 1270,
                "paten": 1110,
                "ray": 1255,
                "korkuluk": 520,
                "agirlik_ray": 1959,
            },
        )
        self.assertEqual(
            {k: v[1] for k, v in Y["ust_engel"].items()},
            {
                "siginma": "kuyu tavanı",
                "revizyon": "kabin_baglanti",
                "paten": "sase",
                "ray": "ray",
                "korkuluk": "sase",
            },
        )

    def test_kabin_modeli_tutarli(self):
        g = _ornek()
        S = sabitler.sabitler(g.get("_cizim_sabitleri"))
        k = dusey.kabin_kotlari(g["dusey"], S, 0.0)
        #  Paten arası alt patenin merkezinden üst patenin merkezine;  patenler
        #  kirişlerin dışında ( üst paten üst kirişin üstünde — 8 Eki )
        P = S["paten_yukseklik"]
        self.assertEqual(
            (k["ust_paten"] - P / 2.0) - (k["alt_paten"] + P / 2.0), g["dusey"]["kabin_paten_arasi"]
        )
        self.assertEqual(k["alt_paten"] + P / 2.0, k["sase_alt"] + S["alt_paten_payi"])
        self.assertEqual((k["ust_kiris_ust"], k["ust_paten_alt"]), (k["sase_ust"], k["sase_ust"]))
        self.assertEqual(k["ust_kiris_ust"] - k["ust_kiris_alt"], S["sase_ust_kiris"])
        self.assertEqual(k["alt_kiris_ust"] - k["alt_kiris_alt"], S["sase_alt_kiris"])
        self.assertGreaterEqual(k["ust_kiris_alt"], k["tavan"])
        self.assertLessEqual(k["alt_kiris_ust"], k["taban_alti"])
        self.assertLessEqual(k["alt_kiris_alt"], k["alt_paten"] + P + 1e-9)
        self.assertEqual(k["tavan"], g["dusey"]["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"])
        #  m.5.4.5:  dik kısım 750, altında pah 35 ( önlüğün en alt noktası pahın ucu )
        self.assertEqual((k["etek_dik_alti"], k["etek_alti"]), (-750, -785))

    def test_kuyu_dibi_zinciri_kabinle_kapanmali(self):
        h = dusey.dogrula(_ornek(kuyu_dibi={"derinlik": 1600}))
        self.assertTrue(any("kabinle çelişiyor" in x for x in h), h)

    def test_korkuluk_sinirlari(self):
        #  Makine dairesinde kuyu tavanına 0,30:  kiriş altı − 3.685 = 300 → 4.135.
        #  Makine dairesizde korkuluğun dışındaki şaseye 0,10:  ( SK − 795 ) −
        #  3.685 = 100 → 4.580 ( m.5.2.5.7.2 c 1 ).
        for yeri, sinir in (("Makine dairesi", 4135), ("Kuyu üstü", 4580)):
            for sk, uygun in ((sinir, True), (sinir - 1, False)):
                h = dusey.dogrula(_ornek(dusey={"son_kat": sk}, makine={"yeri": yeri}))
                with self.subTest(yeri=yeri, son_kat=sk):
                    self.assertEqual(not any("m.5.2.5.7.2 c" in x for x in h), uygun, h)

    def test_tavan_parcalari_engel_sayilir(self):
        #  Sığınma alanının üstüne bir parça gelirse sığınma ona ölçülür:
        #  regülatör sığınmanın üstüne kaydırılınca engel regülatördür.
        g = _ornek()
        Y = dusey.yerlesim(g)
        M = Y["M"]
        self.assertEqual(donanim.tavan_engeli(M, Y["KU"]["siginma"])[1], "kuyu tavanı")
        self.assertEqual(donanim.tavan_engeli(M, M["sase"][:4]), (M["sase"][4], "sase"))
        self.assertEqual(
            [p[0] for p in M["parcalar"]], ["sase", "kabin_baglanti", "agirlik_baglanti", "regulator"]
        )
        #  Makine dairesinde kuyuda parça yok
        self.assertEqual(dusey.yerlesim(_ornek(makine={"yeri": "Makine dairesi"}))["M"]["parcalar"], [])

    def test_karsi_agirlik_kilavuz_payi_ve_sase(self):
        #  Ağırlık paten arası X = patenlerin merkezleri arası;  çerçeve X − 140
        #  ( patenler çerçevenin dışında — 8 Eki );  en üst konumda çerçevenin altı 20.331.
        #  Kılavuz payı ( m.5.2.5.6.2 ):  makine dairesinde ağırlık rayı tavan kirişi
        #  payının 50 altında biter ( 26.000 − 150 − 50 = 25.800 );  üst paten
        #  20.331 + X − 140 + 140;  25.800 − 20.331 − X ≥ 100 → X ≤ 5.369.
        #  Kuyu üstünde en yüksek nokta üst paten ( kasnak çerçeve üstü − 110 + 200 = + 90,
        #  patenin 50 altında ):  20.331 + X ≤ şasenin altı 25.205 → X ≤ 4.874.
        def h(x, **ezme):
            g = _ornek(**ezme)
            g["dusey"]["agirlik_paten_arasi"] = x
            return dusey.dogrula(g)

        for x, uygun in ((5369, True), (5370, False)):
            hata = h(x, makine={"yeri": "Makine dairesi"})
            with self.subTest(cerceve=x):
                self.assertEqual(
                    not any("m.5.2.5.6.2" in y and "ağırlık" in y.lower() for y in hata), uygun, hata
                )
        #  ( hareketli.agirlik_parcalari:  üst patenin izinin üstünde makine şasesi )
        self.assertFalse(any("tavana çarpıyor" in x for x in h(4874)))
        self.assertTrue(
            any("tavana çarpıyor" in x and "üst pateni" in x and "makine şasesi" in x for x in h(4875))
        )

    def test_kabin_ustu_siginma_yuksekligi(self):
        #  dik duruş 2.000:  kiriş altı − 2.585 ≥ 2.000  →  son kat en az 4.735
        g = _ornek(dusey={"son_kat": 4734}, kabin_ustu={"siginma_tipi": "Dik duruş"})
        self.assertTrue(any("m.5.2.5.7.1" in x for x in dusey.dogrula(g)))
        g = _ornek(dusey={"son_kat": 4735}, kabin_ustu={"siginma_tipi": "Dik duruş"})
        self.assertFalse(any("m.5.2.5.7.1" in x for x in dusey.dogrula(g)))

    def test_standart_sayilari(self):
        self.assertEqual(dusey.SIGINMA_UST_YUKSEKLIK, {"Dik duruş": 2000.0, "Çömelme": 1000.0})
        self.assertEqual(
            dusey.SIGINMA_DIP_YUKSEKLIK, {"Dik duruş": 2000.0, "Çömelme": 1000.0, "Yatarak": 500.0}
        )
        self.assertEqual(
            (
                dusey.DIP_EN_ALT,
                dusey.DIP_ETEK,
                dusey.DIP_RAYA_YAKIN,
                dusey.UST_PATEN,
                dusey.UST_KORKULUK,
                dusey.UST_KORKULUK_DIS,
                dusey.YATAY_UZAKLIK,
                dusey.RAY_UZANTISI,
                dusey.ETEK_BOYU,
            ),
            (500.0, 100.0, 100.0, 100.0, 300.0, 100.0, 400.0, 100.0, 750.0),
        )


class TamBoyKesit(unittest.TestCase):
    def test_durak_kotlari(self):
        self.assertEqual(dusey.durak_kotlari(_ornek())[0], [0, 3000, 6000, 9000, 12000, 15000, 18000, 21000])
        #  LiftDesigner örneği gibi karışık kat yükseklikleri
        kotlar, hata = dusey.durak_kotlari(
            _ornek(dusey={"durak_adedi": 4, "kat_yuksekligi": [3400, 3400, 3000]})
        )
        self.assertEqual((kotlar, hata), ([0, 3400, 6800, 9800], []))

    def test_hatali_durak_girdileri(self):
        for dy in (
            {"durak_adedi": 1},
            {"durak_adedi": 2.5},
            {"durak_adedi": True},
            {"kat_yuksekligi": [3000, 3000]},
            {"kat_yuksekligi": 0},
            {"kat_yuksekligi": "3000"},
        ):
            with self.subTest(dy=dy):
                self.assertTrue(dusey.dogrula(_ornek(dusey=dy)))

    def test_esik_arasi_11_m(self):
        #  m.5.2.3.1:  11 m'ye kadar olur, aşarsa ara acil kapı gerekir
        for h, uygun in ((11000, True), (11001, False)):
            kh = [3000] * 6 + [h]
            with self.subTest(h=h):
                hata = dusey.dogrula(_ornek(dusey={"kat_yuksekligi": kh}))
                self.assertEqual(not any("m.5.2.3.1" in x for x in hata), uygun, hata)
        self.assertEqual(dusey.ESIK_ARASI, 11000.0)

    def test_kat_kapi_yuksekliginden_buyuk(self):
        hata = dusey.dogrula(_ornek(dusey={"kat_yuksekligi": 2100}))
        self.assertTrue(any("kat kapısı yüksekliğinden" in x for x in hata), hata)

    def test_kesit_zincir_kotlar_yazilar_dxf(self):
        import itertools
        from cizim import dxf
        from ezdxf.audit import Auditor

        for g in (
            _ornek(),
            _ornek(dusey={"durak_adedi": 4, "kat_yuksekligi": [3400, 3400, 3000]}),
            _ornek(makine={"yeri": "Makine dairesi"}),
            _sag_ayna(kuyu_dibi={"regulator_yan": "Sol"}),
        ):
            for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
                e = ciz(g)
                dy = g["dusey"]
                kotlar = dusey.durak_kotlari(g)[0]
                with self.subTest(
                    cizim=ciz.__name__,
                    duraklar=dy["durak_adedi"],
                    makine=g["makine"]["yeri"],
                    agirlik=g["agirlik"]["yeri"],
                ):
                    self.assertEqual(sum(1 for x in e if x.get("ad") == "durak_adi"), dy["durak_adedi"])
                    #  Makine dairesinde:  tabliyenin üstü ( kuyu tavanı + döşeme ) ve
                    #  oda zemini ( onun tabliye beton yüksekliği altında )
                    zt = kotlar[-1] + dy["son_kat"] + g["kuyu"]["doseme"]
                    oda = (
                        [zt, zt - g["makine_dairesi"]["tabliye_yuksekligi"]]
                        if g["makine"]["yeri"] == "Makine dairesi"
                        else []
                    )
                    self.assertEqual(
                        {x["metin"] for x in e if x.get("ad") == "kot"},
                        {dusey.kot_yazisi(z) for z in kotlar + [-g["kuyu_dibi"]["derinlik"]] + oda},
                    )
                    #  Sol zincir:  kuyu dibi + kat yükseklikleri + son kat = kuyu yüksekliği
                    #  ( referans proje:  1.500 + 29.000 + 5.000 = 35.500 )
                    toplam = g["kuyu_dibi"]["derinlik"] + kotlar[-1] + dy["son_kat"]
                    metinler = {x["metin"] for x in e if x["tip"] == "olcu"}
                    self.assertIn(f"KUYU YÜKSEKLİĞİ {toplam:g}", metinler)
                    self.assertIn(f"SEYİR {kotlar[-1]:g}", metinler)
                    zz = geometri.zincirler(e)
                    for z in zz:
                        self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                    self.assertTrue(
                        any(
                            z["adet"] == dy["durak_adedi"] + 1 and abs(z["toplam"] - toplam) < 1e-6
                            for z in zz
                        )
                    )
                    #  Konsol zinciri kuyu tabanından kuyu tavanına kapanır
                    self.assertTrue(
                        any(
                            abs(z["bas"] + g["kuyu_dibi"]["derinlik"]) < 1e-6
                            and abs(z["son"] - kotlar[-1] - dy["son_kat"]) < 1e-6
                            and z["adet"] > dy["durak_adedi"] + 1
                            for z in zz
                        )
                    )
                    k = OlcuYazilari._kutular(None, e)
                    for a, b in itertools.combinations(k, 2):
                        self.assertFalse(
                            a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4],
                            (a[0]["metin"], b[0]["metin"]),
                        )
                    #  1/50:  ölçü yazısı paftada 1/20'dekiyle aynı boyda
                    self.assertTrue(
                        all(x["yazi"]["h"] == eleman.OLCU_YAZI * 2.5 for x in e if x["tip"] == "olcu")
                    )
                    au = Auditor(dxf.belge(e, "DÜŞEY", 50))
                    au.run()
                    self.assertEqual(list(au.errors), [])

    def test_olcek_kalemleri_buyutur(self):
        #  Kesilen duvar ISO 128'in 0,50 mm'si:  1/20'de 10 birim, 1/50'de 25
        e = [eleman.dikdortgen("KUYU-DUVAR", 0, 0, 100, 100)]
        self.assertEqual(svg.kalem("KUYU-DUVAR")[1], 10)
        self.assertIn('stroke-width="10"', svg.yaz(e, (0, 0, 100, 100), "", 20))
        self.assertIn('stroke-width="25"', svg.yaz(e, (0, 0, 100, 100), "", 50))


class KuyuKesitleri(unittest.TestCase):
    """A-A ve B-B tam boy kesitler:  donanımın yerleri ve halat geometrisi."""

    def _elemanlar(self, e, ad):
        return [x for x in e if x.get("ad") == ad]

    def test_referans_kotlari(self):
        #  referans proje kesitlerinin vektörlerinden ölçülenler:  tavandan makine
        #  kapağının üstü 250, tahrik kasnağı merkezi 446, şase 595 – 795;
        #  şasenin altındaki raylar 650'de biter, regülatör kasnağı 462,
        #  karşı ağırlık çerçevesi 2.920.  Gergi kasnağı tabandan 397 ( eskiden
        #  referans projenin 520'si — kollu gergide plaka en alt konsola çakışıyordu;
        #  PFB kılavuzu:  plakanın altı ~260 ).
        g = _ornek()
        Y = dusey.yerlesim(g)
        M = Y["M"]
        T = M["tavan"]
        self.assertEqual(T, 21000 + 5000)
        self.assertEqual(T - M["kapak"][5], 250)
        self.assertEqual(T - M["kasnak"][4], 446)
        self.assertEqual((T - M["sase"][5], T - M["sase"][4]), (595, 795))
        #  Şase ağırlık raylarının dış yüzlerinden 8 taşar:  referans proje kesitinde
        #  raylar iç yüzden 627 – 1.607 ( yan kesit vektörleri ) → 619 – 1.615
        self.assertEqual(M["sase"][:4], (20, 619.0, 343.0, 1615.0))
        ustler = sorted(T - r["ust"] for r in M["raylar"])
        #  Öbür kabin rayı referans projede tavanın 50 altında biter;  tavanın en alt
        #  kısmı kuyu tavanı payı ( 150 ) olunca onun 50 altında:  200 ( eskiden
        #  payın alt yüzüne tam değiyordu:  150 )
        self.assertEqual(ustler, [200, 650, 650, 650])
        self.assertEqual(T - M["regulator_kasnak"][4], 462)
        self.assertEqual(M["gergi"]["merkez"] - Y["taban"], 397)
        self.assertEqual(parca_kotlari.agirlik_kotlari(M, 0)["ust"], 2920)

    def test_konsollar_ve_ekler(self):
        #  İlk konsol tabandan 500, sonra "konsollar arası";  ray ucunu geçmez.
        for aralik in (1500, 3000):
            g = _ornek(dusey={"kabin_konsol_arasi": aralik, "agirlik_konsol_arasi": aralik})
            M = dusey.yerlesim(g)["M"]
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
        Y = dusey.yerlesim(g)
        M, dy = Y["M"], g["dusey"]
        tampon_ustu = -1500 + 300 + 160
        self.assertEqual(M["agirlik"]["tampon_ustu"], tampon_ustu)
        #  A-A:  kabin en alt durakta ( taban altı −120 ), ağırlık seyir kadar yukarıda
        e = kuyu_kesiti.yan_kesit(g)
        kabin = self._elemanlar(e, "kabin")[0]
        self.assertEqual(kabin["y"], -120)
        ag = self._elemanlar(e, "agirlik")[0]
        self.assertEqual(ag["y"], tampon_ustu + dy["agirlik_carpma_arasi"] + 21000)
        #  B-B:  kabin en üst durakta, ağırlık tamponunun çarpma arası üstünde
        e = kuyu_kesiti.on_kesit(g)
        self.assertEqual(self._elemanlar(e, "kabin")[0]["y"], 21000 - 120)
        self.assertEqual(self._elemanlar(e, "agirlik")[0]["y"], tampon_ustu + dy["agirlik_carpma_arasi"])

    def test_halatlar_kasnaklara_teget(self):
        #  Düşey halat bir kasnağın merkez kotunda bitiyorsa o kasnağa teğettir.
        for ciz, en_az in ((kuyu_kesiti.on_kesit, 4), (kuyu_kesiti.yan_kesit, 2)):
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
        #  onlar B-B'de görünür ( referans proje de iki yan kesitte ayrı gösterir ).
        A = (
            "makine",
            "makine_sasesi",
            "tahrik_kasnagi",
            "agirlik_baglanti",
            "agirlik",
            "agirlik_kasnagi",
            "kabin_tamponu",
            "agirlik_tamponu",
            "kat_kapisi",
            "kat_dosemesi",
            "tavan_kirisi",
        )
        B = (
            "makine",
            "makine_sasesi",
            "tahrik_kasnagi",
            "kabin_kasnagi",
            "regulator",
            "regulator_kasnagi",
            "kabin_baglanti",
            "gergi_kasnagi",
            "gergi_agirligi",
            "agirlik",
            "kat_kapisi",
            "durak_no",
            "kabin_kapisi",
            "sase",
            "fren",
        )
        for ciz, adlar, yok, kabin_rayi in (
            (kuyu_kesiti.yan_kesit, A, ("regulator", "kabin_baglanti", "gergi_kasnagi"), 1),
            (kuyu_kesiti.on_kesit, B, (), 2),
        ):
            e = ciz(_ornek())
            for ad in adlar:
                with self.subTest(cizim=ciz.__name__, ad=ad):
                    self.assertTrue(self._elemanlar(e, ad))
            for ad in yok:
                with self.subTest(cizim=ciz.__name__, gorunmez=ad):
                    self.assertFalse(self._elemanlar(e, ad))

            #  Raylar tabandan başlayan parçalarıyla sayılır:  kabinin arkasında
            #  kalan ray kabinin altında ve üstünde iki parçadır
            #  ( kesit_parcalari.kabin_arkasi )
            def raylar(ad, e=e):
                p = self._elemanlar(e, ad)
                return sum(1 for x in p if abs(x["y"] - min(q["y"] for q in p)) < 1e-6)

            self.assertEqual(raylar("kabin_rayi"), kabin_rayi)
            self.assertEqual(raylar("agirlik_rayi"), 2)
        #  Karşı ağırlık sağdaysa A-A sağa bakar
        e = kuyu_kesiti.yan_kesit(_sag_ayna(kuyu_dibi={"regulator_yan": "Sol"}))
        self.assertTrue(self._elemanlar(e, "makine"))
        self.assertFalse(self._elemanlar(e, "regulator"))

    def test_girdi_hatalari(self):
        self.assertTrue(any("makine.yeri" in x for x in dusey.dogrula(_ornek(makine={"yeri": "Çatı"}))))
        for alan in ("kabin_konsol_arasi", "agirlik_konsol_arasi"):
            with self.subTest(alan=alan):
                self.assertTrue(any(alan in x for x in dusey.dogrula(_ornek(dusey={alan: 0}))))

    def test_makine_daireli_kesitler(self):
        #  Tabliye ( kuyunun üstündeki beton, kuyu döşemesi 150 ):  kuyu tavanı 26.000,
        #  üstü 26.150 — makine buraya oturur.  Oda zemini tabliyenin 1.200 altında
        #  ( "tabliye beton yüksekliği" — LiftDesigner'ın makine dairesi kesiti ):
        #  24.950;  tavanı + 3.500 = 28.450.  Dişlisiz makine kaidede ( şase
        #  yüksekliği 1.100 ), kasnak merkezi + 149, üstü + 120 → 27.519;  kasnak
        #  üstü 28.450 − 27.519 = 931 ( m.5.2.6.3.2.3:  ≥ 300 ).  Eskiden oda zemini
        #  kuyu tavanının 1.200 üstündeydi ( tabliye 1.200 kalın beton sanılıyordu ).
        g = _ornek(makine={"yeri": "Makine dairesi"})
        self.assertEqual(kuyu_kesiti.dogrula(g), [])
        M = dusey.yerlesim(g)["M"]
        self.assertEqual((M["tabliye_ustu"], M["oda_doseme"], M["oda_tavan"]), (26150, 24950, 28450))
        self.assertEqual(M["kasnak"][4] + 120, 27519)
        self.assertEqual(M["parcalar"], [])  # kuyuda tavan parçası yok
        #  Açıklıklar ve uygunlukları ( m.5.2.6.3.2 ) veri tablosunda;  kesit aynı
        #  sayıları ölçer ( donanim.oda_acikliklari — 6 Kas çizim denetimi, karar D2 )
        acik = donanim.oda_acikliklari(g, M)
        self.assertEqual(
            [(ad, d, en) for ad, d, en in acik],
            [("yükseklik", 3500, 2100), ("tabliye üstü", 2300, 2100), ("kasnak üstü", 931, 300)],
        )
        satir = dict(veri_tablosu.satirlar(g))
        self.assertEqual(satir["Makine dairesi"], "yükseklik 3500 ≥ 2100  ·  tabliye üstü 2300 ≥ 2100")
        self.assertEqual(satir["Tahrik kasnağı üstü"], "931 ≥ 300")
        #  Oda zemini tabliyeyle aynı hizada:  tabliyenin üstü odanın yüksekliğidir
        g0 = _ornek(
            makine={"yeri": "Makine dairesi"}, makine_dairesi={"tabliye_yuksekligi": 0, "yukseklik": 2500}
        )
        self.assertEqual(dict(veri_tablosu.satirlar(g0))["Makine dairesi"], "yükseklik 2500 ≥ 2100")
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            e = ciz(g)
            metinler = {x["metin"] for x in e if x["tip"] == "olcu"}
            with self.subTest(cizim=ciz.__name__):
                #  Ölçüde uygunluk yok ( eskiden "KASNAK ÜSTÜ 931 ≥ 300" 1/50'de 41 mm,
                #  makine dairesinin çatısının üstüne taşıyordu );  adı aralığına
                #  sığmayan yalnız değer:  "KASNAK ÜSTÜ 931" 31,5 mm, aralığı 17,6 mm
                #  ( yazı payıyla );  "TABLİYE 1200" 23,2 mm, aralığı 23,0 mm
                self.assertFalse([m for m in metinler if "≥" in m], metinler)
                self.assertIn("931", metinler)
                self.assertIn("MAKİNE DAİRESİ 3500", metinler)
                #  Tabliyenin üstünde temiz yükseklik ( makinenin başı ) 3.500 − 1.200
                self.assertIn("2300", metinler)
                #  Tabliye oda zemininden, çatı 150;  kaide hesabın şase yüksekliği
                self.assertTrue({"1200", "150", "ŞASE 1100"} <= metinler, metinler)
                #  Tabliyenin ve oda zemininin betonu kuyu döşemesi kalınlığında
                self.assertEqual({x["d"] for x in self._elemanlar(e, "oda_dosemesi")}, {150})
                self.assertEqual({x["d"] for x in self._elemanlar(e, "tabliye")}, {150})
                self.assertEqual({x["d"] for x in self._elemanlar(e, "oda_catisi")}, {150})
                for ad in ("oda_dosemesi", "oda_catisi", "oda_duvari", "makine", "doseme_deligi"):
                    self.assertTrue(self._elemanlar(e, ad), ad)
                #  Kumanda panosu odanın arka yarısında:  iki kesitte de bakanın gerisinde
                self.assertFalse(self._elemanlar(e, "kumanda_panosu"))
                kotlar = {x["metin"] for x in e if x.get("ad") == "kot"}
                self.assertTrue({dusey.kot_yazisi(24950), dusey.kot_yazisi(26150)} <= kotlar, kotlar)

    def test_makine_dairesi_sinirlari(self):
        def h(**md):
            return dusey.dogrula(_ornek(makine={"yeri": "Makine dairesi"}, makine_dairesi=md))

        #  Odanın zemininde ve tabliyenin üstünde ( makinenin başı ) en az 2.100:
        #  tabliye 1.200 ise oda en az 3.300;  kot farkı yoksa 2.100
        self.assertFalse(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=3300)))
        self.assertTrue(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=3299)))
        self.assertTrue(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=2099, tabliye_yuksekligi=0)))
        self.assertFalse(any("m.5.2.6.3.2.1" in x for x in h(yukseklik=2100, tabliye_yuksekligi=0)))
        self.assertFalse(any("m.5.2.3.2 a" in x for x in h(kapi_yukseklik=2000)))
        self.assertTrue(any("m.5.2.3.2 a" in x for x in h(kapi_yukseklik=1999)))
        #  Kasnak üstü:  şase yüksekliği X ise 3.500 − 1.200 − ( X + 269 ) ≥ 300 → X ≤ 1.731
        for x, uygun in ((1731, True), (1732, False)):
            g = _ornek(makine={"yeri": "Makine dairesi"}, makine_dairesi={"sase_yuksekligi": x})
            with self.subTest(sase=x):
                self.assertEqual(not any("m.5.2.6.3.2.3" in y for y in dusey.dogrula(g)), uygun)
        self.assertTrue(any("makine_dairesi.yukseklik" in x for x in h(yukseklik=None)))
        #  Hesap programının makine dairesi girdileri eksik / geçersizse çizilmez
        #  Tabliye 0 olabilir ( oda zemini tabliyeyle aynı hizada ), eksi olamaz
        self.assertEqual([x for x in h(tabliye_yuksekligi=0) if "tabliye" in x], [])
        for alan, v in (
            ("tabliye_yuksekligi", None),
            ("tabliye_yuksekligi", -1),
            ("sase_yuksekligi", None),
            ("dikine_kiris", 125),
            ("dikine_kiris", "NPU 120"),
        ):
            with self.subTest(alan=alan, deger=v):
                self.assertTrue(any(f"makine_dairesi.{alan}" in x for x in h(**{alan: v})))
        self.assertEqual(
            (donanim.ODA_YUKSEKLIK, donanim.DONEN_PARCA_USTU, donanim.ODA_KAPI_YUKSEKLIK),
            (2100.0, 300.0, 2000.0),
        )

    def test_plandaki_kesit_isaretleri(self):
        e = geometri.plan(_ornek())
        self.assertEqual(sorted(x["metin"] for x in e if x.get("ad") == "kesit_harfi"), ["A", "A", "B", "B"])
        self.assertEqual(len([x for x in e if x.get("ad") == "kesit_isareti"]), 4)
        #  Kesit çizilemeyen düzende işaret de yok
        for g in (_arka(), _ornek(aski={"duzen": "Doğrudan", "nokta_arasi": 450})):
            self.assertFalse([x for x in geometri.plan(g) if x["katman"] == "KESIT"])
        self.assertTrue(
            [x for x in geometri.plan(_ornek(makine={"yeri": "Makine dairesi"})) if x["katman"] == "KESIT"]
        )


class PlanSeviyeleri(unittest.TestCase):
    """Düşey kesitlerde planların hangi yükseklikten alındığı ( C-C … G-G )."""

    def _seviyeler(self, e):
        return {
            x["ad"][len("plan_seviyesi_") :]: x["y1"]
            for x in e
            if x.get("ad", "").startswith("plan_seviyesi_")
        }

    def test_kotlar(self):
        #  C:  en alt durak + kapı / 2 = 1.050;  D:  kabinin tavanı ( A-A kabin
        #  altta 2.310, B-B üstte 21.000 + 2.310 );  E:  ilk konsolun üstü
        #  −1.500 + 500 = −1.000 ile kabinin en alt noktası ( önlüğün pahının ucu
        #  −750 − 35 = −785 — m.5.4.5 ) arası → −892,5;  F:  tahrik kasnağı ekseni
        #  ( kuyu tavanı 26.000 − 446 );  makine
        #  dairesinde tabliyenin üstü ( 26.000 + döşeme 150 ) + kaide 1.100 + 149 → 27.399,
        #  G tabliyenin betonunun ortası 26.075.
        g = _ornek()
        self.assertEqual(
            self._seviyeler(kuyu_kesiti.yan_kesit(g)),
            {"kuyu_plani": 1050, "kabin_ustu": 2310, "kuyu_dibi": -892.5, "kuyu_ustu": 25554},
        )
        self.assertEqual(self._seviyeler(kuyu_kesiti.on_kesit(g))["kabin_ustu"], 23310)
        md = _ornek(makine={"yeri": "Makine dairesi"})
        sev = self._seviyeler(kuyu_kesiti.on_kesit(md))
        self.assertEqual((sev["makine_dairesi"], sev["delik_plani"]), (27399, 26075))
        self.assertNotIn("kuyu_ustu", sev)

    def test_kuyu_dibi_kesiti_kabinden_gecmez(self):
        """E-E kuyu dibi planıdır:  A-A'da en alt durakta duran kabinin hiçbir
        parçasına değmez ( kabin o planda yoktur ), ilk konsolların üstündedir."""
        parcalar = (
            "kabin",
            "etek",
            "sase",
            "alt_paten",
            "fren",
            "kabin_kasnak",
            "kabin_esigi",
            "kabin_kanadi",
        )
        for g in (
            _ornek(),
            _ornek(makine={"yeri": "Makine dairesi"}),
            _ornek(dusey={"kabin_ic_yukseklik": 2100}),
        ):
            e = kuyu_kesiti.yan_kesit(g)
            z = self._seviyeler(e)["kuyu_dibi"]
            alt = {}
            for x in e:
                if x["tip"] == "dikdortgen" and x.get("ad") in parcalar:
                    alt[x["ad"]] = min(alt.get(x["ad"], x["y"]), x["y"])
            with self.subTest(makine=g["makine"]["yeri"]):
                self.assertEqual(set(alt), set(parcalar))
                self.assertLess(z, min(alt.values()))
                Y = kuyu_kesiti.yerlesim(g)
                self.assertGreater(z, max(r["konsollar"][0] for r in Y["M"]["raylar"]))

    def test_harfler_cakismaz(self):
        import itertools

        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"})):
            for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
                e = ciz(g)
                harfler = [x for x in e if x.get("ad") == "plan_harfi"]
                self.assertEqual(len(harfler), 2 * len(self._seviyeler(e)))
                kutular = [
                    (
                        x["x"] - x["yukseklik"] * 0.3,
                        x["y"] - x["yukseklik"] / 2,
                        x["x"] + x["yukseklik"] * 0.3,
                        x["y"] + x["yukseklik"] / 2,
                    )
                    for x in harfler
                ]
                for a, b in itertools.combinations(kutular, 2):
                    with self.subTest(cizim=ciz.__name__, makine=g["makine"]["yeri"]):
                        self.assertFalse(a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3])
                #  Harf başka bir seviyenin çizgisinin üstüne düşmez
                cizgiler = [x for x in e if x.get("ad", "").startswith("plan_seviyesi_")]
                for (x0, y0, x1, y1), c in itertools.product(kutular, cizgiler):
                    if y0 < c["y1"] < y1:
                        self.assertFalse(c["x1"] < x1 and x0 < c["x2"], (c["ad"], (x0, y0)))

    def test_plan_basliklari(self):

        b = "KUYU PLANI  ( kabin hizasından yatay kesit )"
        self.assertEqual(
            cizimler.plan_basligi(_ornek(), "kuyu_plani", b),
            "KUYU PLANI  C-C  ( kabin hizasından yatay kesit )",
        )
        md = _ornek(makine={"yeri": "Makine dairesi"})
        self.assertEqual(
            cizimler.plan_basligi(md, "makine_dairesi", "MAKİNE DAİRESİ PLANI"), "MAKİNE DAİRESİ PLANI  F-F"
        )
        self.assertEqual(cizimler.plan_basligi(md, "delik_plani", "DELİK PLANI"), "DELİK PLANI  G-G")
        #  Makine dairesizde F kuyu üstü planınındır;  makine dairesi / delik planı harfsiz
        self.assertEqual(
            cizimler.plan_basligi(_ornek(), "makine_dairesi", "MAKİNE DAİRESİ PLANI"), "MAKİNE DAİRESİ PLANI"
        )
        self.assertEqual(cizimler.plan_basligi(_ornek(), "delik_plani", "X"), "X")
        self.assertEqual(cizimler.plan_basligi(md, "kuyu_ustu", "KUYU ÜSTÜ PLANI"), "KUYU ÜSTÜ PLANI")
        self.assertEqual(
            cizimler.plan_basligi(_ornek(), "kuyu_ustu", "KUYU ÜSTÜ PLANI"), "KUYU ÜSTÜ PLANI  F-F"
        )
        #  Düşey kesit çizilemeyen düzende harf yok
        self.assertEqual(cizimler.plan_basligi(_arka(), "kuyu_plani", b), b)
        self.assertEqual(cizimler.plan_basligi(_ornek(), "kuyu_kesiti_yan", "X"), "X")


class KirikKesit(unittest.TestCase):
    """Paftaya sığmayan düşey kesitte ara katlar kırılır ( referans proje, LiftDesigner )."""

    def _yukseklik(self, e):
        return kuyu_kesiti._yukseklik(e, kuyu_kesiti.OLCEK / 20.0)

    def test_sigmazsa_kirilir_sigarsa_kirilmaz(self):
        g = _ornek()
        tam = kuyu_kesiti.yan_kesit(g)
        self.assertFalse([x for x in tam if x.get("ad") == "kirik_cizgisi"])
        self.assertFalse(
            [
                x
                for x in kuyu_kesiti.yan_kesit(g, azami=self._yukseklik(tam) + 1)
                if x.get("ad") == "kirik_cizgisi"
            ]
        )
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
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
        for ciz, adlar in (
            (kuyu_kesiti.yan_kesit, ("ust_paten", "alt_paten", "sase")),
            (kuyu_kesiti.on_kesit, ("agirlik_paten", "agirlik")),
        ):
            e = ciz(g, azami=1)
            self.assertTrue([x for x in e if x.get("ad") == "kirik_cizgisi"])
            for ad in adlar:
                boylar = sorted({round(x["d"]) for x in e if x.get("ad") == ad})
                with self.subTest(cizim=ciz.__name__, ad=ad):
                    #  dikme alt kirişin altından ( −480 ) üst kirişin üstüne ( 2.680 )
                    beklenen = {
                        "ust_paten": [140],
                        "alt_paten": [140],
                        "sase": [3160],
                        "agirlik_paten": [140],
                        "agirlik": [2920],
                    }[ad]
                    self.assertEqual(boylar, beklenen)

    def test_kirik_olculer_ve_parcalar(self):
        import itertools

        g = _ornek()
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            e = ciz(g, azami=420 * 50)
            metinler = [x["metin"] for x in e if x["tip"] == "olcu"]
            with self.subTest(cizim=ciz.__name__):
                #  Kırığı geçen ölçüler gerçek değerini yazar
                self.assertTrue(any("× 3000" in m for m in metinler), metinler)
                self.assertTrue(any("× 1500" in m for m in metinler), metinler)
                self.assertIn("SEYİR 21000", metinler)
                self.assertIn("KUYU YÜKSEKLİĞİ 27500", metinler)
                #  Çizilen zincirler geometrik olarak kapanır
                for z in geometri.zincirler(e):
                    self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])
                #  Kabin ve karşı ağırlık bölünmez ( çerçeve 2.920, kabin 2.310 + 120 )
                self.assertEqual([x["d"] for x in e if x.get("ad") == "agirlik"], [2920])
                self.assertEqual([x["d"] for x in e if x.get("ad") == "kabin"], [2430])
                #  Durak adları ( giriş katı en alt:  0 … 7 ):  ara duraklar düşer, ilk ve
                #  son kalır
                adlar = {x["metin"] for x in e if x.get("ad") == "durak_adi"}
                self.assertIn("0", adlar)
                self.assertIn("7", adlar)
                self.assertLess(len(adlar), 8)
                k = OlcuYazilari._kutular(None, e)
                for a, b in itertools.combinations(k, 2):
                    self.assertFalse(
                        a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4],
                        (a[0]["metin"], b[0]["metin"]),
                    )


class KonsolZinciri(unittest.TestCase):
    """Konsol zincirinde aralıklarda yalnız sayı;  zincirin adı bir kez, zincirin
    dış yanında, hiçbir yazıya, ölçü çizgisine ve parçaya binmeden — kırık varsa
    kesilen katların hizasında ( 6 Kas çizim denetimi, karar D4 ).  Eskiden ad
    ikinci aralıktaydı:  "KABİN RAYI KONSOL ARASI 1500" 1/50'de 30 mm'lik aralıktan
    taşıyor, "İLK KONSOL 500" çizimin altına sarkıyordu."""

    def _ad(self, e):
        adlar = [x for x in e if x.get("ad") == "zincir_adi"]
        self.assertEqual(len(adlar), 1, [x["metin"] for x in adlar])
        return adlar[0]

    def test_ad_bir_kez_zincirin_yaninda_bos_yerde(self):
        g = _ornek()
        K = kuyu_kesiti.OLCEK / 20.0
        for ciz, metin in (
            (kuyu_kesiti.yan_kesit, "AĞIRLIK RAYI KONSOLLARI"),
            (kuyu_kesiti.on_kesit, "KABİN RAYI KONSOLLARI"),
        ):
            for azami in (None, 420 * 50):
                e = ciz(g, azami=azami)
                with self.subTest(cizim=ciz.__name__, azami=azami):
                    ad = self._ad(e)
                    self.assertEqual((ad["metin"], ad["aci"]), (metin, 90))
                    self.assertFalse([x["metin"] for x in e if x["tip"] == "olcu" and "KONSOL" in x["metin"]])
                    #  Bir ölçü sırasının dış yanında, yazılarının iki sıra ötesinde
                    sutunlar = {x["kot"] for x in e if x["tip"] == "olcu" and x["yon"] == "dusey"}
                    pay = (50.0 + 2 * eleman.KAT_ARALIGI) * K
                    self.assertTrue(any(abs(ad["x"] - (k + pay)) < 1e-6 for k in sutunlar), ad["x"])
                    #  Binmez:  başka yazının maskesine, ölçü çizgisine, parça kenarına
                    m = geometri.maske_kutusu(ad)
                    for x in e:
                        if x is ad or not (x["tip"] == "yazi" or (x["tip"] == "olcu" and x.get("yazi"))):
                            continue
                        b = geometri.maske_kutusu(x)
                        self.assertFalse(
                            m[0] < b[2] and b[0] < m[2] and m[1] < b[3] and b[1] < m[3], x["metin"]
                        )
                    cizgiler = geometri.parca_kenarlari(e) + [
                        s for o in e if o["tip"] == "olcu" for s in geometri.olcu_cizgileri(o, K)
                    ]
                    self.assertFalse([s for s in cizgiler if geometri.kenar_kesisir(s, m)])
                    kirik = [y for x in e if x.get("ad") == "kirik_cizgisi" for y in (x["y1"], x["y2"])]
                    if azami:
                        #  Kesilen katların hizasında ( kırığın iki çizgisinin arası )
                        self.assertTrue(kirik)
                        self.assertLess(min(kirik), ad["y"])
                        self.assertLess(ad["y"], max(kirik))
                    else:
                        self.assertFalse(kirik)

    def test_aralikta_yalniz_sayi(self):
        #  Zincir:  ray altı → ilk konsol 500, konsol arası 1500 … ( ağırlık rayı:
        #  A-A;  kabin rayı:  B-B ) — sayılar girdinin değeri
        g = _ornek()
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            metinler = [x["metin"] for x in ciz(g) if x["tip"] == "olcu"]
            with self.subTest(cizim=ciz.__name__):
                self.assertIn("500", metinler)
                self.assertGreaterEqual(metinler.count("1500"), 10)


class AdliOlcuMetni(unittest.TestCase):
    """Ölçünün adı aralığına sığıyorsa adıyla, sığmıyorsa sıradaki ( kısa ) adla,
    hiçbiri sığmıyorsa yalnız değer ( geometri.adli_olcu_metni — yerleştiricinin
    ölçütü:  yazı eni ≤ aralık − 20k )."""

    def test_sigarsa_adiyla_sigmazsa_yalniz_deger(self):
        w = eleman.yazi_eni("ŞASE 1100", eleman.OLCU_YAZI)
        self.assertEqual(geometri.adli_olcu_metni(("ŞASE",), 1100, w + 20.0), "ŞASE 1100")
        self.assertEqual(geometri.adli_olcu_metni(("ŞASE",), 1100, w + 19.0), "1100")
        #  Ölçekte ( 1/50:  k 2,5 ) yazı ve pay büyür
        self.assertEqual(geometri.adli_olcu_metni(("ŞASE",), 1100, w + 20.0, 2.5), "1100")
        self.assertEqual(geometri.adli_olcu_metni(("ŞASE",), 1100, 2.5 * (w + 20.0), 2.5), "ŞASE 1100")
        #  Sırayla:  uzun ad sığmazsa kısası
        k = eleman.yazi_eni("KISA 5", eleman.OLCU_YAZI) + 20.0
        self.assertEqual(geometri.adli_olcu_metni(("ÇOK UZUN BİR AD", "KISA"), 5, k), "KISA 5")
        self.assertEqual(geometri.adli_olcu_metni(("ÇOK UZUN BİR AD", "KISA"), 5, k - 1.0), "5")
        self.assertEqual(geometri.adli_olcu_metni(("A",), 1022.5, 10_000.0), "A 1022.5")


class EsikAltiSaci(unittest.TestCase):
    """Kat kapısının eşik altı sacı ( TS EN 81-20 m.5.2.5.3.2 ) düşey kesitlerde
    her durakta — kapı yan kesitiyle aynı kaynaktan ( girdi.esik_alti_saci ),
    LiftDesigner'ın ve referans projenin düşey kesitleri gibi ( 3 Kas ).
    Kısa katta pah yerine alttaki kapının üst kutusuna bağlanır ( d 1 )."""

    S = sabitler.sabitler(None)

    @staticmethod
    def _adli(e, ad):
        return [x for x in e if x.get("ad") == ad]

    def _yandan(self, g):
        e = kuyu_kesiti.yan_kesit(g)
        return {
            round(x["bicim"][0]["noktalar"][0][1] + self.S["esik_kalinlik"]): x
            for x in self._adli(e, "esik_alti_saci")
        }, e

    def test_her_durakta_kapi_yan_kesitindeki_gibi(self):
        from cizim import kapi_kesiti

        for g in (_ornek(), _duvar_boslugu(), _ornek(kapi={"tip": "Manuel Sol"})):
            with self.subTest(montaj=g["kapi"]["montaj"], tip=g["kapi"]["tip"]):
                kotlar = dusey.yerlesim(g)["kotlar"]
                saclar, e = self._yandan(g)
                self.assertEqual(sorted(saclar), [round(z) for z in kotlar])
                kk = kapi_kesiti.ciz(g)
                (bir,) = self._adli(kk, "esik_alti_saci")
                (ku,) = self._adli(kk, "kapi_ust_kutusu")
                kutular = sorted(
                    (round(x["y"]), x["x"], x["g"], x["d"]) for x in self._adli(e, "kapi_ust_kutusu")
                )
                self.assertEqual(len(kutular), len(kotlar))
                for z, (kz, x, gen, d) in zip(kotlar, kutular):
                    self.assertEqual((kz - round(z), x, gen, d), (round(ku["y"]), ku["x"], ku["g"], ku["d"]))
                #  3.000'lik katta sac pahıyla biter:  biçimi kapı yan kesitindekinin kotu kaymışı
                for z in kotlar:
                    nok = saclar[round(z)]["bicim"][0]["noktalar"]
                    self.assertEqual(nok, [(u, v + z) for u, v in bir["bicim"][0]["noktalar"]])

    def test_pah_ve_boy_standarttan(self):
        """Dik kısmı eşiğin altından 400 ( otomatik ) / 250 ( elle ), pah duvara
        doğru ≥ 60° ve ≥ 20 mm ama duvara kadar dönmez;  eni kabin girişi + iki yanda 25."""
        for g, dik in ((_ornek(), 400.0), (_ornek(kapi={"tip": "Manuel Sol"}), 250.0)):
            s = girdi.esik_alti_saci(g, self.S)
            (u0, z0), (u1, z1), (u2, z2) = self._yandan(g)[0][0]["bicim"][0]["noktalar"]  # en alt durak
            with self.subTest(tip=g["kapi"]["tip"]):
                self.assertEqual((u0, z0), (girdi.kapi_bolgesi(g, self.S)["hat"], -self.S["esik_kalinlik"]))
                self.assertEqual((u1, z0 - z1), (u0, dik))
                self.assertGreaterEqual(math.degrees(math.atan2(z1 - z2, u1 - u2)), 60.0)
                self.assertGreaterEqual(u1 - u2, 20.0)
                self.assertGreater(u2, 0.0)
                kp = g["kapi"]
                self.assertEqual(s["x"], (kp["sol_pay"] - 25, kp["sol_pay"] + kp["genislik"] + 25))

    def test_kisa_katta_alttaki_kapinin_lentosuna_baglanir(self):
        HH, ust = 2100, self.S["kasa_ust"]
        for h in (2805, 2804, 2700, 2400):
            g = _ornek(dusey={"kat_yuksekligi": h})
            saclar, e = self._yandan(g)
            kotlar = dusey.yerlesim(g)["kotlar"]
            for i, z in enumerate(kotlar):
                nok = saclar[round(z)]["bicim"][0]["noktalar"]
                with self.subTest(h=h, durak=i):
                    if i == 0 or h >= 2805:
                        #  pahla biter;  ucu alttaki kapının üst kutusunun üstünde
                        self.assertEqual(len(nok), 3)
                        if i:
                            self.assertGreaterEqual(nok[-1][1], kotlar[i - 1] + HH + ust - 1e-6)
                    else:
                        self.assertEqual(nok, [(150.0, z - 50.0), (150.0, kotlar[i - 1] + HH + ust)])

    def test_arkadan_bakista_kabinin_onlugu_ortulur(self):
        """B-B:  her durakta eşik ve altında sac ( kapı + iki yanda 25 ) — pahı
        şerit;  kabinin durduğu en üst durakta önlük ( kapı eninde ) sacın
        ortasını örter, iki yanda 25'er mm kalır;  şase alt kirişi ikisinin önünde."""
        g = _ornek()
        e = kuyu_kesiti.on_kesit(g)
        Y = dusey.yerlesim(g)
        kotlar, G, kp = Y["kotlar"], g["kuyu"]["genislik"], g["kapi"]
        x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
        H = kotlar[-1]
        for z in kotlar:
            parca = [x for x in self._adli(e, "esik_alti_saci") if z - 500 < x["y"] < z]
            with self.subTest(durak=z):
                if z < H:
                    self.assertEqual(
                        sorted((round(x["y"] - z), round(x["d"]), x["x"], x["g"]) for x in parca),
                        [(-485, 35, G - x1 - 25, x1 - x0 + 50), (-450, 400, G - x1 - 25, x1 - x0 + 50)],
                    )
                    self.assertTrue(
                        [x for x in self._adli(e, "kat_esigi") if abs(x["y"] + x["d"] - z) < 1e-6]
                    )
                else:
                    self.assertTrue(parca)
                    self.assertEqual({round(x["g"]) for x in parca}, {25})
        onluk = self._adli(e, "etek")
        self.assertTrue(onluk)
        self.assertEqual({(x["x"], x["x"] + x["g"]) for x in onluk}, {(G - x1, G - x0)})
        kiris = [x for x in self._adli(e, "sase_kirisi") if x["y"] < H]
        (k,) = kiris
        for x in onluk + [p for p in self._adli(e, "esik_alti_saci") if p["y"] > H - 500]:
            self.assertFalse(x["y"] < k["y"] + k["d"] - 1e-6 and k["y"] < x["y"] + x["d"] - 1e-6, x)

    def test_kirik_saci_kesmez(self):
        g = _ornek()
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            for azami in (560 * 50, 420 * 50, 1):
                e = ciz(g, azami=azami)
                with self.subTest(cizim=ciz.__name__, azami=azami):
                    self.assertTrue(self._adli(e, "kirik_cizgisi"))
                    for x in self._adli(e, "esik_alti_saci"):
                        if "bicim" in x:  # A-A:  kesit — dik 400 ve pah
                            nok = x["bicim"][0]["noktalar"]
                            self.assertEqual((len(nok), nok[0][1] - nok[1][1]), (3, 400.0))
                        elif round(x["g"]) != 25:  # B-B:  önlüğün yanında kalan şeritler dışında
                            self.assertIn(round(x["d"]), (400, 35))

    def test_kuyu_dibinde_siginma_alani_saca_girmez(self):
        """En alt durağın sacı kuyuya sarkar:  ucu sığınma yüksekliğinin altındaysa
        alan onun izine konmaz ( kabinin izinin dışındaki yer — m.5.2.5.8.1 )."""
        for derinlik, girer in ((1200, True), (1600, False)):
            g = _ornek(kuyu_dibi={"derinlik": derinlik, "siginma_tipi": "Çömelme"})
            S = sabitler.sabitler(None)
            Y = kuyu_dibi.yerlesim(g)
            s = girdi.esik_alti_saci(g, S)
            sac = (s["x"][0], s["u"] - s["pah"][0], s["x"][1], s["u"])
            G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
            alan = kuyu_dibi._siginma_yeri(
                g, S, Y["taban"], "Çömelme", (0.0, 0.0, G, D), Y["perde"], Y["ag_yan"], [], []
            )
            with self.subTest(derinlik=derinlik):
                self.assertIsNotNone(alan)
                self.assertEqual(ortusur(alan, sac), not girer)


from cizim import pafta
from cizim import makine


def _md(**makine_ayari):
    return _ornek(makine=dict({"yeri": "Makine dairesi"}, **makine_ayari))


class MakineVeSase(unittest.TestCase):
    """Makine parça parça ( LiftDesigner makineleri ), şase hesap programının
    profilleriyle ( kuyu üstünde 2 yan yatak, makine dairesinde kaide:  dikine
    kirişler + yan yataklar ), saptırma kasnağı ve sarım açısı."""

    def _parca(self, e, parca):
        return [x for x in e if x.get("parca") == parca]

    def _kutular(self, parcalar, parca):
        return [p["k"] for p in parcalar if p["tur"] == "kutu" and p["parca"] == parca]

    def test_tipler(self):
        self.assertEqual(makine.TIPLER, ("Dişlisiz", "Dişli"))
        self.assertTrue(
            any("makine.tip" in h for h in kuyu_kesiti.dogrula(_ornek(makine={"tip": "Dişlili"})))
        )
        #  Makine dairesizde dişli makine yok ( kuyu tepesindeki şaseye sığmaz )
        self.assertTrue(
            any("dişli makine çizilmez" in h for h in kuyu_kesiti.dogrula(_ornek(makine={"tip": "Dişli"})))
        )
        self.assertEqual(kuyu_kesiti.dogrula(_md(tip="Dişli")), [])

    def test_disli_ve_dislisiz_sabitleri(self):
        """LiftDesigner'dan ölçülen sayılar ( dişlisiz 4815-6, dişli A 160 )."""
        self.assertEqual(
            [(a, b, c) for a, b, c in makine.DISLISIZ],
            [
                ("gobek", 15, 100),
                ("flans", 28, 220),
                ("yatak", 50, 320),
                ("govde", 206, 400),
                ("fren", 70, 320),
                ("fren_diski", 18, 240),
                ("enkoder", 102, 270),
            ],
        )
        self.assertEqual((makine.DISLISIZ_CAP, makine.DISLISIZ_BOY), (400.0, 489.0))
        self.assertEqual(
            makine.DISLI_ZARF, {"m": (-1000.0, 320.0), "a": (-175.0, 415.0), "z": (-195.0, 410.0)}
        )
        #  NPU ( UPN ) DIN 1026-1;  anahtarlar hesap programının NPU listesi
        self.assertEqual(makine.npu(200), {"h": 200.0, "b": 75.0, "s": 8.5, "t": 11.5})
        self.assertEqual(makine.npu(120), {"h": 120.0, "b": 55.0, "s": 7.0, "t": 9.0})
        self.assertEqual(makine.npu(140), {"h": 140.0, "b": 60.0, "s": 7.0, "t": 10.0})
        self.assertEqual(makine.npu(100.0), makine.npu(100))
        self.assertIsNone(makine.npu(125))
        self.assertEqual(
            list(makine.NPU),
            ["30x15", 30, "40x20", 40, "50x25", 50, 60, 65, 80, 100, 120, 140, 160, 180, 200, 240, 280, 300],
        )
        self.assertEqual(makine.KAIDE_KISA, 100)

    def test_dislisiz_zarfa_oranlanir(self):
        """Biçim LiftDesigner'ın, ölçü projenin zarfı:  kasnağın arkasından
        boşluk + gövde boyu, çap gövde çapını aşmaz;  kasnak kendi çapında."""
        g, S = _ornek(), sabitler.sabitler()
        Y = kuyu_ustu.yerlesim(g)
        k = [p for p in Y["makine"] if p["ad"] == "makine"]
        kasnak = next(p for p in Y["makine"] if p["ad"] == "tahrik_kasnagi")
        self.assertEqual([p["parca"] for p in k], [a for a, _, _ in makine.DISLISIZ])
        self.assertEqual(kasnak["cap"], g["makine"]["tahrik_kasnak_capi"])
        self.assertAlmostEqual(kasnak["t"][1] - kasnak["t"][0], S["tahrik_kasnak_kalinlik"])
        uc = min(p["t"][0] for p in k) if Y["s"] < 0 else max(p["t"][1] for p in k)
        y0 = Y["halatlar"][0][1]
        self.assertAlmostEqual(
            abs(uc - y0), S["tahrik_kasnak_kalinlik"] / 2.0 + S["makine_kasnak_boslugu"] + S["makine_boy"]
        )
        self.assertAlmostEqual(max(p["cap"] for p in k), S["makine_en"])
        #  Zarf eskisiyle aynı:  çakışma denetimleri değişmez
        self.assertEqual((Y["govde"][0], Y["govde"][2]), (101, 399))

    def test_kuyu_ustu_sase_upn(self):
        """2 yan yatak ( referans proje:  UPN 200 ) karşı ağırlık rayları boyunca;
        referans proje kotları değişmez ( şase tavandan 595 – 795 );  motor plakası
        700, gövdenin ortasında.  Profil hesabın yan yatağıdır:  NPU 160'ta
        şasenin üstü yine 595, altı 755."""
        for olcu, alt in ((200, 795), (160, 755)):
            g = _ornek(makine={"yan_yatak": olcu})
            Y = kuyu_kesiti.yerlesim(g)
            M = Y["M"]
            P = makine.npu(olcu)
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
        M = kuyu_kesiti.yerlesim(g)["M"]
        mp = next(p for p in M["sase_parcalari"] if p["parca"] == "motor_plakasi")
        self.assertEqual(mp["k"][3] - mp["k"][1], 700)
        self.assertAlmostEqual((mp["k"][1] + mp["k"][3]) / 2.0, (M["govde"][1] + M["govde"][3]) / 2.0)
        self.assertEqual(mp["k"][5], M["sase"][5])  # üstle aynı hizada
        self.assertEqual(len([p for p in M["sase_parcalari"] if p["parca"] == "uc_levhasi"]), 2)

    def test_gorunusler(self):
        """Ön kesitte ( B-B ) kasnak ve gövde daire, yan kesitte ( A-A )
        dikdörtgen;  planda şase ve makine parça parça."""
        g = _ornek()
        D1 = g["makine"]["tahrik_kasnak_capi"]
        on, yan = kuyu_kesiti.on_kesit(g), kuyu_kesiti.yan_kesit(g)
        ks = [x for x in on if x.get("ad") == "tahrik_kasnagi"]
        self.assertTrue(ks and all(x["tip"] == "daire" and x["r"] == D1 / 2.0 for x in ks))
        ks = [x for x in yan if x.get("ad") == "tahrik_kasnagi"]
        self.assertTrue(ks and all(x["tip"] == "dikdortgen" and x["d"] == D1 for x in ks))
        for e in (on, yan):
            self.assertTrue(
                self._parca(e, "govde") and self._parca(e, "enkoder") and self._parca(e, "yan_yatak")
            )
        plan = kuyu_ustu.ciz(g)
        self.assertEqual(len([x for x in self._parca(plan, "yan_yatak") if x["tip"] == "dikdortgen"]), 2)
        self.assertTrue(self._parca(plan, "motor_plakasi") and self._parca(plan, "fren"))

    def test_disli_makine_dairesinde_kaide(self):
        """Dişli makine hesap programının kaidesinde:  döşemeden şase yüksekliği
        ( 1.100 ), dört dikine kiriş ( NPU 120 ), iki yan yatak ( NPU 200 )
        makinenin uzun ekseni boyunca, dikine kirişlerin eksenleri arası kaidenin
        açıklığı ( hesabın L'si );  kasnak merkezi tabanın 195 üstünde;  motor ekseni
        kasnak eksenine dik;  makine odada, bağlantılara binmez."""
        g = _md(tip="Dişli")
        Y = makine_dairesi.yerlesim(g)
        M = kuyu_kesiti.yerlesim(g)["M"]
        zd = M["tabliye_ustu"]
        self.assertEqual(M["sase"][5] - zd, g["makine_dairesi"]["sase_yuksekligi"])
        self.assertEqual(M["kasnak"][4] - M["sase"][5], 195)
        ayak = self._kutular(M["sase_parcalari"], "dikine_kiris")
        yan = self._kutular(M["sase_parcalari"], "yan_yatak")
        self.assertEqual((len(ayak), len(yan)), (4, 2))
        self.assertTrue(Y["kaide"]["uzun_x"])  # motor ekseni x boyunca
        for k in ayak:
            self.assertEqual((k[2] - k[0], k[3] - k[1]), (120, 55))
            self.assertEqual((k[4], k[5]), (zd + 20, M["sase"][5] - 200))
        xs = sorted({(k[0] + k[2]) / 2.0 for k in ayak})
        self.assertEqual(xs[1] - xs[0], Y["kaide"]["L"])  # hesabın L'si
        for k in yan:
            self.assertEqual((k[2] - k[0], k[3] - k[1], k[5] - k[4]), (Y["kaide"]["L"] + 120, 75, 200))
            self.assertEqual(k[5], M["sase"][5])
        motor = next(p for p in M["makine"] if p.get("parca") == "motor")
        kasnak = next(p for p in M["makine"] if p["ad"] == "tahrik_kasnagi")
        self.assertEqual((motor["eksen"], kasnak["eksen"]), ("x", "y"))
        taban = next(p for p in M["makine"] if p.get("parca") == "taban")
        self.assertEqual(taban["k"][4], M["sase"][5])  # makine çerçevenin üstünde
        oda, c = Y["oda"], Y["cerceve"]
        self.assertTrue(oda[0] <= c[0] and oda[1] <= c[1] and c[2] <= oda[2] and c[3] <= oda[3])
        mk = Y["M"]["govde"]
        for b in (Y["M"]["agirlik_baglanti"], Y["M"]["kabin_baglanti"], Y["M"]["reg_govde"]):
            self.assertFalse(ortusur(mk, b))
        self.assertEqual(M["sarim_acisi"], 180.0)  # saptırmasız

    def test_kaide_hesabin_girdileriyle(self):
        """Makine dairesinde makine HER ZAMAN kaidededir ( hesap programı
        makine daireli tesiste kolonların burkulmasını denetler ):  dişlisizde de.
        Profiller ve yükseklik hesabın girdileridir:  şase yüksekliği 900,
        dikine NPU 100, yan yatak NPU 160 → kasnak 900 + 149.  Boyu çizimden:
        dikine kirişlerin eksenleri arası kaidenin açıklığı ( hesabın L'si )."""
        g = _ornek(
            makine={"yeri": "Makine dairesi", "yan_yatak": 160},
            makine_dairesi={"sase_yuksekligi": 900, "dikine_kiris": 100},
        )
        self.assertEqual(kuyu_kesiti.dogrula(g), [])
        Y = makine_dairesi.yerlesim(g)
        M = kuyu_kesiti.yerlesim(g)["M"]
        zd, L = M["tabliye_ustu"], Y["kaide"]["L"]
        self.assertFalse(Y["kaide"]["uzun_x"])  # dişlisiz:  kasnak ekseni y
        self.assertEqual((M["sase"][4], M["sase"][5]), (zd, zd + 900))
        self.assertEqual(M["kasnak"][4] - M["sase"][5], 149)
        ayak = self._kutular(M["sase_parcalari"], "dikine_kiris")
        self.assertEqual({(k[2] - k[0], k[3] - k[1]) for k in ayak}, {(50, 100)})
        ys = sorted({(k[1] + k[3]) / 2.0 for k in ayak})
        self.assertEqual(ys[1] - ys[0], L)
        yan = self._kutular(M["sase_parcalari"], "yan_yatak")
        self.assertEqual({(k[2] - k[0], k[3] - k[1], k[5] - k[4]) for k in yan}, {(65, L + 100, 160)})
        c = Y["cerceve"]
        self.assertEqual(c[3] - c[1], L + 100)
        self.assertTrue(
            any("makine.yan_yatak" in x for x in kuyu_kesiti.dogrula(_ornek(makine={"yan_yatak": 210})))
        )

    def test_sarim_acisi_liftdesigner(self):
        """LiftDesigner 12744-3:  tahrik ø540, saptırma ø480 ( 560 yana, 842
        aşağıda ) → 'Sarim acisi 148';  saptırmasız 180."""
        for yon in (-1, 1):
            _, _, n = makine.teget((0, 0), 270, (yon * 560, -845), 240, yon)
            self.assertEqual(round(makine.sarim_acisi(yon, n)), 148)
            self.assertEqual(makine.sarim_acisi(yon, (yon, 0)), 180.0)

    def test_saptirma_kasnagi(self):
        """Halat aralığı kasnak çapından büyükse saptırma kasnağı halatı
        ağırlık kasnağının teğetine indirir ( delik de oraya );  çapı
        girilmezse ya da aralık küçükse reddedilir."""
        g = _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294)
        self.assertEqual(kuyu_kesiti.dogrula(g), [])
        Y = makine_dairesi.yerlesim(g)
        M = kuyu_kesiti.yerlesim(g)["M"]
        ex = Y["M"]["ex"]
        self.assertEqual(Y["agirlik_dusus"][0], ex)
        sp = Y["saptirma"]
        self.assertAlmostEqual(sp["x"] + sp["D"] / 2.0 * (-1 if g["agirlik"]["yeri"] == "Sol" else 1), ex)
        delik = dict(Y["delikler"])["AĞIRLIK"]
        self.assertAlmostEqual((delik[0] + delik[2]) / 2.0, ex)
        self.assertEqual(M["agirlik_dusus"][2] - M["tabliye_ustu"], 400)
        ((P1, P2),) = M["agirlik_yolu"]
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
        on = kuyu_kesiti.on_kesit(g)
        self.assertTrue([x for x in on if x.get("ad") == "saptirma_kasnagi" and x["tip"] == "daire"])
        self.assertTrue(
            [
                x
                for x in on
                if x.get("ad") == "sarim_acisi" and x["metin"] == f"SARIM AÇISI {M['sarim_acisi']:.0f}°"
            ]
        )
        self.assertTrue(
            any(
                "saptirma_kasnak_capi" in h
                for h in kuyu_kesiti.dogrula(_md(tip="Dişli", tahrik_kasnak_capi=200))
            )
        )
        self.assertTrue(any("içeride" in h for h in kuyu_kesiti.dogrula(_md(tahrik_kasnak_capi=280))))

    def test_kaide_halatlara_ortali_makineyi_sarar(self):
        """Kaide ( kullanıcı kararı ):  makinenin ve saptırma kasnağının izini
        her yana en az payı kadar sarar;  halatların ortası kaidenin ortasıdır
        ( Tavaslıoğlu:  "halat deliklerini ortalamalıdır" ) — enine eksende her
        zaman ( iki yan yatağa eşit yük ), uzun eksende oda yer verirse ( dişli
        makinede motor kasnaktan uzağa uzanır ).  Ayak plakaları deliklere
        basmaz;  dikine kirişlerin eksenleri arası hesabın L'sidir."""
        S = sabitler.sabitler()
        pay = S["md_cerceve_pay"]
        for ad, g, ortali in (
            ("dişlisiz 2:1", _ornek(makine={"yeri": "Makine dairesi"}), True),
            ("dişlisiz saptırmalı", _md(tahrik_kasnak_capi=200, saptirma_kasnak_capi=294), True),
            ("dişli", _md(tip="Dişli"), False),
            ("dişli saptırmalı", _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294), False),
        ):
            with self.subTest(ad):
                self.assertEqual(kuyu_kesiti.dogrula(g), [])
                Y = makine_dairesi.yerlesim(g)
                K, c, sp = Y["kaide"], Y["cerceve"], Y["saptirma"]
                iz = (
                    Y["makine_izi"]
                    if not sp
                    else (
                        min(Y["makine_izi"][0], sp["kutu"][0]),
                        min(Y["makine_izi"][1], sp["kutu"][1]),
                        max(Y["makine_izi"][2], sp["kutu"][2]),
                        max(Y["makine_izi"][3], sp["kutu"][3]),
                    )
                )
                #  Makineyi sarar;  tabliyenin kenarına dayanan yanda pay daralır
                #  ( dişli makine halatların yerinde kuyunun kenarına 80 mm yakın:
                #  kaide tabliyeye kaydırılır — 5 Eki )
                #  Kenara dayanan kaidenin izi:  kutusu ve ayak plakaları ( plaka
                #  kutudan taşar — tabliyeden sarkmaz )
                tb = Y["tabliye"]["izi"]
                a = makine.ayak_plakasi(K["E"], S)
                ps = [
                    (x - a / 2.0, y - a / 2.0, x + a / 2.0, y + a / 2.0)
                    for x, y in makine.ayaklar(c, K["E"], K["F"], K["uzun_x"])
                ]
                t = (
                    min([c[0]] + [q[0] for q in ps]),
                    min([c[1]] + [q[1] for q in ps]),
                    max([c[2]] + [q[2] for q in ps]),
                    max([c[3]] + [q[3] for q in ps]),
                )
                self.assertTrue(makine_dairesi.icinde(t, tb), (t, tb))
                p_ = [0.0 if abs(t[i] - tb[i]) < 1e-6 else pay for i in range(4)]
                self.assertTrue(
                    c[0] <= iz[0] - p_[0] + 1e-6
                    and c[1] <= iz[1] - p_[1] + 1e-6
                    and c[2] >= iz[2] + p_[2] - 1e-6
                    and c[3] >= iz[3] + p_[3] - 1e-6,
                    (c, iz),
                )
                self.assertTrue(tb[0] <= c[0] and tb[1] <= c[1] and c[2] <= tb[2] and c[3] <= tb[3])
                #  Halatlara ortalı ( enine hep )
                d = dict(Y["delikler"])
                hc = [
                    (
                        (d["KABİN"][i] + d["KABİN"][i + 2]) / 2.0
                        + (d["AĞIRLIK"][i] + d["AĞIRLIK"][i + 2]) / 2.0
                    )
                    / 2.0
                    for i in (0, 1)
                ]
                kc = [(c[0] + c[2]) / 2.0, (c[1] + c[3]) / 2.0]
                enine = 1 if K["uzun_x"] else 0
                self.assertAlmostEqual(kc[enine], hc[enine])
                self.assertEqual(K["ortali"], ortali)
                if ortali:
                    self.assertAlmostEqual(kc[1 - enine], hc[1 - enine])
                #  Mesnet aralığı ve ayak plakaları
                ayaklar = makine.ayaklar(c, K["E"], K["F"], K["uzun_x"])
                us = sorted({a_[1 - enine] for a_ in ayaklar})
                self.assertAlmostEqual(us[1] - us[0], K["L"])
                a = makine.ayak_plakasi(K["E"], S)
                plakalar = [(x - a / 2.0, y - a / 2.0, x + a / 2.0, y + a / 2.0) for x, y in ayaklar]
                self.assertFalse([d_ for p in plakalar for _, d_ in Y["delikler"] if ortusur(p, d_)])

    def test_saptirma_kasnagi_baglantinin_ustunde(self):
        """Saptırma kasnağı döşemenin 400 üstünde;  döşemedeki bir bağlantının
        üstüne düşerse onun 50 mm üstüne yükselir ( kotlar döşemeden )."""
        g = _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294)
        Y = makine_dairesi.yerlesim(g)
        S, sp, M, K = sabitler.sabitler(), Y["saptirma"], Y["M"], Y["kaide"]
        y_ = -1 if g["agirlik"]["yeri"] == "Sol" else 1
        self.assertEqual(
            makine_dairesi.saptirma_kotu(M, sp, M["kasnak"], M["D1"], K["hs"], K["hk"], y_, S)["z"], 400
        )
        sk = sp["kutu"]
        M2 = dict(M, agirlik_baglanti=(sk[0], sk[1], sk[0] + 200, sk[1] + 100))
        self.assertAlmostEqual(
            makine_dairesi.saptirma_kotu(M2, sp, M["kasnak"], M["D1"], K["hs"], K["hk"], y_, S)["z"],
            S["agirlik_baglanti_yukseklik"] + 50 + 147,
        )
        #  Düşey kesit aynı kotu kullanır
        Mk = kuyu_kesiti.yerlesim(g)["M"]
        self.assertEqual(Mk["agirlik_dusus"][2] - Mk["tabliye_ustu"], sp["z"])

    def test_dxf_temiz(self):
        from cizim import dxf
        from ezdxf.audit import Auditor

        for g in (
            _ornek(),
            _md(tip="Dişli"),
            _md(tip="Dişli", tahrik_kasnak_capi=200, saptirma_kasnak_capi=294),
        ):
            for ciz in (kuyu_kesiti.on_kesit, kuyu_kesiti.yan_kesit, makine_dairesi.ciz):
                d = dxf.belge(ciz(g), "X", 20)
                au = Auditor(d)
                au.run()
                with self.subTest(ciz=ciz.__name__, tip=g["makine"]["tip"]):
                    self.assertEqual(list(au.errors), [])


from cizim import cizimler


class OlcuYazisiParcayaBinmez(unittest.TestCase):
    """Hiçbir çizimde ölçü yazısı bir parçanın ( ray, konsol, şase, tampon,
    kasnak, merdiven, perde, makine, pano, paten ) ya da bir etiketin üstüne
    düşmez.  Kuyu planında kabin duvarının "75"i şase dikmesinin, kuyu
    dibinde Yatarak sığınmanın "1000"i kabin tamponunun üstündeydi."""

    def test_butun_cizimler(self):
        projeler = [
            ("örnek", _ornek()),
            ("sağ", _sag_ayna()),
            ("arka", _arka()),
            ("makine dairesi", _ornek(makine={"yeri": "Makine dairesi"})),
            ("yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            ("dik duruş", _ornek(kabin_ustu={"siginma_tipi": "Dik duruş"})),
        ]
        sayi = 0
        for ad, g in projeler:
            for cizim, (dogrula, ciz, _) in cizimler.CIZIMLER.items():
                if dogrula(g):
                    continue
                e = ciz(g)
                engel = [
                    geometri.sinir([x])
                    for x in e
                    if x["katman"] in geometri.PARCA_KATMANLARI
                    or (x["tip"] == "yazi" and x["katman"] == "YAZI")
                    or x.get("ad") == "yuk_kutusu"
                ]
                for o in e:
                    if o["tip"] != "olcu":
                        continue
                    y_ = o["yazi"]
                    w, h = eleman.yazi_eni(o["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                    if y_["aci"]:
                        w, h = h, w
                    k = (y_["x"] - w, y_["y"] - h, y_["x"] + w, y_["y"] + h)
                    sayi += 1
                    with self.subTest(proje=ad, cizim=cizim, olcu=o["metin"]):
                        self.assertFalse([b for b in engel if ortusur(k, b)])
        self.assertGreater(sayi, 500)


class YaziParcaKenarinaBinmez(unittest.TestCase):
    """Yazılar maskelidir ( DXF arka plan / dimtfill, SVG hale ):  maske altındaki
    çizgiyi siler.  Eksen, ölçü, gizli çizgi, alan sınırı, seviye, kesit
    işareti ve halatın yazıda kesilmesi doğrudur ( ISO 128 ) — PARÇA KENARININ
    değil.
    Hiçbir çizimde etiket ya da ölçü yazısı bir parçanın kenarına binmez
    ( kuyu üstünde HALAT BAĞLANTISI makine şasesinin, B-B'de durak numarası
    kanat ayrımının, kuyu planında "75" kabinin çizgilerinin üstündeydi )."""

    def test_butun_cizimler(self):
        projeler = [
            ("örnek", _ornek()),
            ("sağ", _sag_ayna()),
            ("arka", _arka()),
            ("makine dairesi", _ornek(makine={"yeri": "Makine dairesi"})),
            ("yatarak", _ornek(kuyu_dibi={"siginma_tipi": "Yatarak"})),
            ("dik duruş", _ornek(kabin_ustu={"siginma_tipi": "Dik duruş"})),
        ]
        sayi = 0
        for ad, g in projeler:
            for cizim, (dogrula, ciz, _) in cizimler.CIZIMLER.items():
                if dogrula(g):
                    continue
                k = cizimler.OLCEKLER.get(cizim, 20) / 20.0
                e = ciz(g)
                kenarlar = geometri.parca_kenarlari(e)
                duvarlar = [geometri.sinir([x]) for x in e if x["tip"] in ("tarama", "tarama_tugla")]
                for o in e:
                    if o["tip"] == "yazi":
                        h, aci, hiza = o["yukseklik"], o.get("aci", 0), o.get("hiza", "orta")
                        x, y = o["x"], o["y"]
                    elif o["tip"] == "olcu":
                        h, aci, hiza = o["yazi"]["h"], o["yazi"]["aci"], "orta"
                        x, y = o["yazi"]["x"], o["yazi"]["y"]
                    else:
                        continue
                    #  Görünen kutu:  büyük harf 0,72 em, en harflerin gerçek eni
                    #  ( Arial — eskiden harf × 0,58 em sayılıyordu, 12 Eki )
                    w, c = eleman.yazi_eni(o["metin"], h), 0.36 * h
                    a, b = {"sol": (0.0, w), "sag": (-w, 0.0)}.get(hiza, (-w / 2.0, w / 2.0))
                    if abs(abs(aci) - 90) < 1e-6:
                        ys = (y + a, y + b) if aci > 0 else (y - b, y - a)
                        kutu = (x - c, ys[0], x + c, ys[1])
                    else:
                        kutu = (x + a, y - c, x + b, y + c)
                    sayi += 1
                    with self.subTest(proje=ad, cizim=cizim, yazi=o["metin"]):
                        self.assertFalse([s_ for s_ in kenarlar if geometri.kenar_kesisir(s_, kutu, 2.0 * k)])
                        #  Etiket duvarın ( taramalı kesit ) içinde durmaz — etiketleri_ayir'in
                        #  payıyla ( 2 mm;  1/20'de kâğıtta 0,1 mm ):  test yazıyı harf × 0,58
                        #  em sayarken ayırıcıdan dar ölçüyordu, pay görünmüyordu ( 12 Eki )
                        if o["tip"] == "yazi":
                            p_ = 2.0 * k
                            self.assertFalse(
                                [
                                    d
                                    for d in duvarlar
                                    if kutu[0] < d[2] - p_
                                    and d[0] < kutu[2] - p_
                                    and kutu[1] < d[3] - p_
                                    and d[1] < kutu[3] - p_
                                ]
                            )
        self.assertGreater(sayi, 1000)


class KaydirdaYaziKapidanKacar(unittest.TestCase):
    """kaydir'da ( kuyu planı, kabin üstü ) ölçü yazısı kapının kenarına değil
    İÇİNE düşüyorsa da kaçar:  kenar denetimi yalnız kenarı görür.  Kural bir
    ad değişikliğinde sessizce ölmüştü;  gerçek çizimlerde kapı parçaları ince
    olduğu için tetiklenmez, burada yapay bir kutuyla sınanır."""

    def _yazi(self, kaydir):
        kapi = eleman.dikdortgen("KAPI", 1300, 1480, 400, 160)
        o = eleman.olcu("yatay", (1000, 1500), (2000, 1500), 1500)
        geometri.yazilari_yerlestir([kapi, o], kaydir=kaydir)
        return geometri.yazi_kutusu(o), geometri.sinir([kapi])

    def test_kaydirsiz_ortada_kalir(self):
        yazi, kapi = self._yazi(False)
        self.assertTrue(ortusur(yazi, kapi))  # yapay durum gerçekten içeride

    def test_kaydirda_kapinin_disina_kayar(self):
        yazi, kapi = self._yazi(True)
        self.assertFalse(ortusur(yazi, kapi))


class OlcuYazisiOlcuCizgisineKonmaz(unittest.TestCase):
    """Ölçü yazısı başka bir ölçünün çizgisine ya da ucuna konmaz ( 26 Eki,
    kalite 2. adımı:  kabin üstünde sığınma alanının düşey ölçüsü "215"in
    içinden geçiyordu );  çizgiye binmeyen yazının yeri değişmez."""

    def _yerlestir(self, kesen_x):
        o = eleman.olcu("yatay", (1000, 0), (2000, 0), 0)
        e = [o]
        if kesen_x is not None:
            yazi = {"x": kesen_x + 50, "y": -300, "aci": 90}
            e.append(eleman.olcu("dusey", (0, -500), (0, 500), kesen_x, yazi=yazi))
        geometri.yazilari_yerlestir(e)
        return o, e

    def test_cizgi_yokken_ortada(self):
        o, _ = self._yerlestir(None)
        self.assertEqual((o["yazi"]["x"], o["yazi"]["y"]), (1500.0, 50.0))

    def test_uzaktaki_cizgi_yeri_degistirmez(self):
        o, _ = self._yerlestir(1900)
        self.assertEqual((o["yazi"]["x"], o["yazi"]["y"]), (1500.0, 50.0))

    def test_cizgiye_binen_yazi_kendi_olcusu_boyunca_kayar(self):
        o, e = self._yerlestir(1500)
        self.assertEqual(geometri.cizgiye_binen_yazilar(e), [])
        self.assertEqual(o["yazi"]["y"], 50.0)  # çizgisinin hemen dışında kalır
        self.assertTrue(1000 < o["yazi"]["x"] < 2000)


class KopukVeKucukOlcu(unittest.TestCase):
    """Kalite 4. adımı ( 27 Eki ):  dar aralıktaki ölçü yazısı kendi çizgisinden
    kopmaz ( iç yan boşsa çizginin öbür yanına bitişik yazılır — kapı kesitinin
    eşik zinciri );  rastlantısal küçük zincir ölçüsü komşusuyla birleşir."""

    def test_dar_zincirin_yazilari_cizgisine_bitisik(self):
        from araclar import karne

        nok = [0, 150, 240, 300, 330, 420]
        e = [eleman.olcu("yatay", (a, 0), (b, 0), -150) for a, b in zip(nok, nok[1:])]
        geometri.yazilari_yerlestir(e)
        self.assertEqual(karne.karne(e, 20)["yazi_cizgisinden_kopuk"], [])
        self.assertEqual(karne.karne(e, 20)["olcu_yaziyi_kesiyor"], [])

    def test_ic_yanda_sira_varsa_ic_yana_yazilmaz(self):
        nok = [0, 150, 240, 300, 330, 420]
        e = [eleman.olcu("yatay", (a, 0), (b, 0), -150) for a, b in zip(nok, nok[1:])]
        e.append(eleman.olcu("yatay", (0, 0), (420, 0), -50, yazi={"x": 210, "y": 0}))
        geometri.yazilari_yerlestir(e)
        self.assertTrue(all(o["yazi"]["y"] < -150 for o in e[:-1]))

    def test_kucuk_aralik_komsusuyla_birlesir(self):
        uzun = eleman.olcu("yatay", (0, 0), (1000, 0), -150)
        kucuk = eleman.olcu("yatay", (1000, 0), (1004, 0), -150)
        kimlikli = eleman.olcu("yatay", (2000, 0), (2015, 0), -150, ad="kabin_duvari")
        e = geometri.kucukleri_birlestir([uzun, kucuk, kimlikli])
        self.assertEqual([o["metin"] for o in e], ["1004", "15"])
        self.assertEqual(e[0]["b"][0], 1004)


class YaziKendiAraliginda(unittest.TestCase):
    """Çizim denetimi 2. adımı ( 6 – 7 Kas ):  sığmayan ara ölçünün yazısı aynı
    zincirin başka aralığının hizasına ( yanlış aralık ) ya da komşu yazıya 2 mm'den
    yakın ( bitişik ) konmaz.  Kuyu planının eşik zinciri ( 150 · 30 · 90 ):  "30"
    90'ın yanındaydı, "150"ye bitişikti;  iç yandaki CD sırası 270'ten başladığı
    için "30" çizginin iç yanına, kendi aralığına yazılır."""

    @staticmethod
    def _zincirler(cd_bas):
        nok = [0, 150, 180, 270]
        e = [eleman.olcu("dusey", (0, a), (0, b), 2520) for a, b in zip(nok, nok[1:])]
        e.append(eleman.olcu("dusey", (0, cd_bas), (0, 2370), 2420, "CD2100"))
        e += [eleman.olcu("dusey", (0, a), (0, b), 2620) for a, b in ((0, 270), (270, 2390))]
        return e

    def test_kucuk_ara_olcu_kendi_araliginda(self):
        from araclar import karne

        e = self._zincirler(270)
        geometri.yazilari_yerlestir(e, kaydir=True)
        otuz = next(o for o in e if o["metin"] == "30")
        self.assertTrue(150 <= otuz["yazi"]["y"] <= 180, otuz["yazi"])
        self.assertLess(otuz["yazi"]["x"], 2520)  # çizginin iç yanı
        b = karne.karne(e, 20)
        self.assertEqual(b["yazi_yanlis_aralikta"], [])
        self.assertEqual(b["yazi_bitisik"], [])
        self.assertEqual(b["yazi_cizgisinden_kopuk"], [])

    def test_ic_sira_yazinin_hizasindaysa_ic_yana_yazilmaz(self):
        #  CD sırası eşik zincirinin hizasından başlıyorsa iç yandaki yazı onun
        #  ölçüsü sanılır ( 5 Eki ):  "30" iç yana geçmez
        e = self._zincirler(100)
        geometri.yazilari_yerlestir(e, kaydir=True)
        otuz = next(o for o in e if o["metin"] == "30")
        self.assertGreater(otuz["yazi"]["x"], 2520)

    def test_aciklamali_yazi_yerinde_kalir(self):
        #  Açıklamalı uzun yazılar ( "MAKİNE 345" ) 3. adımda yeniden yazılır:
        #  ikinci aşama yalnız sayı yazılarını kaydırır
        e = self._zincirler(270)
        e[1]["metin"] = "EŞİK 30"
        once = [dict(o) for o in e]
        geometri.yazilari_yerlestir([dict(o) for o in once], kaydir=True)
        geometri.yazilari_yerlestir(e, kaydir=True)
        esik = next(o for o in e if o["metin"] == "EŞİK 30")
        self.assertFalse(150 <= esik["yazi"]["y"] <= 180 and esik["yazi"]["x"] < 2520)


class EtiketMaskesi(unittest.TestCase):
    """Etiketin GERÇEK maskesi ( uslup.maske_kutusu — alt uzantılı harfin
    yanında çıplak kutudan 0,19 em uzun ) bir parçanın kenarını ya da önce
    çizilen bir ölçünün çizgisini silmez ( 26 Eki, kalite 3. adımı:  kumanda
    panosunun adı panonun ön yüzünü siliyordu ).  Bloğun satırı kıpırdamaz."""

    def _silinen(self, e, el):
        kenarlar = geometri.KenarIzgarasi(geometri.parca_kenarlari(e))
        m = geometri.maske_kutusu(el)
        return sum(geometri.kutudaki_boy(s, m) for s in kenarlar.adaylar(m))

    def _parca(self):
        #  Üst kenarı yazının ortasının 46 mm altında:  çıplak kutunun ( payıyla )
        #  altında, maskenin içinde
        return eleman.dikdortgen("PANO", -500, -1000, 1000, 954)

    def test_kenari_silen_etiket_az_kayar(self):
        y = eleman.yazi(0, 0, "PANO")
        e = [self._parca(), y]
        self.assertGreater(self._silinen(e, y), geometri.MASKE_ESIGI * 20)
        geometri.etiketleri_ayir(e)
        self.assertLessEqual(self._silinen(e, y), geometri.MASKE_ESIGI * 20)
        self.assertLessEqual(math.hypot(y["x"], y["y"]), 100.0)

    def test_blogun_satiri_kipirdamaz(self):
        adim = uslup.NORMAL + 2 * uslup.maske_payi(uslup.NORMAL)
        ust, alt = eleman.yazi(0, adim, "YÜK"), eleman.yazi(0, 0, "PANO")
        geometri.etiketleri_ayir([self._parca(), ust, alt])
        self.assertEqual((alt["x"], alt["y"]), (0, 0))

    def test_olcu_cizgisindeki_uzun_etiket_kendi_dogrultusunda_kayar(self):
        o = eleman.olcu("yatay", (0, 0), (2000, 0), 0, yazi={"x": 1800, "y": 50, "h": uslup.NORMAL})
        y = eleman.yazi(1000, 0, "PERDE", aci=90)
        e = geometri.etiketleri_ayir([o, y])
        self.assertEqual(y["x"], 1000)
        self.assertEqual(geometri.OlcuIzgarasi(e).silinen(geometri.maske_kutusu(y)), (0.0, 0))


class KuyuIciEtiketi(unittest.TestCase):
    """Kuyunun içindeki parçanın etiketi ( geometri.KUYU_ICI_ETIKETLERI ):  ayırıcı onu
    kuyunun dışına düşürürse OKU parçasını gösterir;  maskesi kayınca da kenar silerse
    kuyunun içinde kısa oklu temiz yere taşınır ( 7 Kas çizim denetimi 5. adımı:  B-B'de
    dar ağırlığın "KARŞI AĞIRLIK"ı duvarın ötesinde, kot yazılarının yanında oksuzdu —
    taramada 210 / 283 kesit;  "ø 400"ün maskesi ( 82 ) 80'lik kasnağın kenarlarını
    siliyordu ).  Sahne 1/20:  60'lık duvarlar, SW 1000, solda dar ağırlık, sağı
    40'ta bir çizgili ( boş yer yok )."""

    def _sahne(self, ad, metin, kutu):
        e = [
            eleman.dikdortgen("TARAMA", -60, -500, 60, 3500, tip="tarama"),
            eleman.dikdortgen("TARAMA", 1000, -500, 60, 3500, tip="tarama"),
            eleman.olcu("yatay", (0, 0), (1000, 0), -300, "SW1000"),
            eleman.dikdortgen("AGIRLIK", kutu[0], 0, kutu[1] - kutu[0], 2000),
        ]
        e += [eleman.cizgi("KAPI", x, -500, x, 3000) for x in range(self.CIZGI, 1001, self.ADIM)]
        y = eleman.ad(eleman.yazi(60, 1000, metin, uslup.NORMAL, aci=90), ad)
        return e + [y], y

    CIZGI, ADIM = 120, 40

    def _oklar(self, e):
        return [(o["x1"], o["y1"], o["x2"], o["y2"]) for o in e if o.get("ad") == "etiket_oku"]

    def test_disari_dusen_etiketin_oku_parcasini_gosterir(self):
        from araclar import karne

        #  60'lık ağırlığa 70'lik dik yazı sığmaz, sağ dolu:  ayırıcı duvarın dışına koyar
        e, y = self._sahne("agirlik_yazi", "KARŞI AĞIRLIK", (30, 90))
        e = geometri.etiketleri_ayir(e)
        self.assertLess(y["x"], -60)
        ((x1, y1, x2, y2),) = self._oklar(e)
        self.assertTrue(30 < x2 < 90 and 900 < y2 < 1100, (x2, y2))  # ağırlığın içi
        self.assertEqual(karne.karne(e, 20)["etiket_kuyu_disinda"], [])
        #  Başka etiket aynı yere oksuz gider ( kural yalnız kuyu içi etiketlerinde )
        e, y = self._sahne("baska", "KARŞI AĞIRLIK", (30, 90))
        e = geometri.etiketleri_ayir(e)
        self.assertLess(y["x"], -60)
        self.assertEqual(self._oklar(e), [])

    def test_kenari_silen_etiket_kuyunun_icinde_kisa_okla(self):
        from araclar import karne

        #  80'lik kasnakta "ø 400"ün maskesi kenarları siler;  100 mm içinde ( az kayma )
        #  çizgi var, 220'den sonrası boş:  kuyunun içinde kısa okla
        self.CIZGI, self.ADIM = 130, 20
        e, y = self._sahne("agirlik_kasnak_yazi", "ø 400", (20, 100))
        e += [eleman.cizgi("KAPI", x, -500, x, 3000) for x in (140, 160, 180, 200, 220)]
        e = [x for x in e if not (x.get("katman") == "KAPI" and x["x1"] > 220)]
        self.assertTrue(karne.karne(e, 20)["maske_kenar_siliyor"])
        e = geometri.etiketleri_ayir(e)
        self.assertEqual(karne.karne(e, 20)["maske_kenar_siliyor"], [])
        self.assertTrue(220 < y["x"] < 60 + 300)  # kuyunun içinde, 300 mm'den yakın
        ((x1, y1, x2, y2),) = self._oklar(e)
        #  Ok kasnağın içine ( etiketin eski yerinin ortasına ) gider
        self.assertTrue(20 < x2 < 100 and 900 < y2 < 1100, (x2, y2))


class Pafta(unittest.TestCase):
    """Çizimlerin ofisin TİP PROJE FORMATINA yerleştirilmesi."""

    @classmethod
    def setUpClass(cls):
        cls.d, cls.bilgi = pafta.belge(_ornek())
        cls.d_md, cls.bilgi_md = pafta.belge(_ornek(makine={"yeri": "Makine dairesi"}))

    def test_onizlemede_blok_taramasi_olcekli(self):
        """Önizleme ( pafta PDF'i ) ölçekli bloktaki taramayı bloksuz hâliyle
        aynı sıklıkta çizer — ezdxf 1.4 deseni ölçeklemiyor, 1/50 kesitte
        duvarda tek çizgi kalıyordu;  asıl belgeye dokunulmaz."""
        import ezdxf

        sayilar = []
        for olcek in (None, 1.0, 1 / 50.0, 1 / 20.0):
            d = ezdxf.new("R2018")
            hedef = d.modelspace() if olcek is None else d.blocks.new("B")
            h = hedef.add_hatch(color=8)
            h.set_pattern_fill("ANSI31", scale=50)
            #  Büyük alan:  ezdxf'in seyrek deseni de birkaç çizgi verir ( çift çizim yakalanır )
            h.paths.add_polyline_path(
                [(0, 26000), (30000, 26000), (30000, 38000), (0, 38000)], is_closed=True
            )
            if olcek is not None:
                d.modelspace().add_blockref("B", (0, 0), dxfattribs={"xscale": olcek, "yscale": olcek})
            svg_metni = pafta.onizleme(d)
            sayilar.append(
                sum(p.count("m") + p.count("M") for p in re.findall(r'<path d="([^"]*)"', svg_metni))
            )
            self.assertEqual([e.dxftype() for e in d.modelspace()], ["HATCH" if olcek is None else "INSERT"])
        self.assertGreater(sayilar[0], 10)
        self.assertEqual(len(set(sayilar)), 1, sayilar)

    def test_cizimler_ve_olcekler(self):
        #  Düşey kesit yalnız tam boy A-A / B-B;  kuyu dibi ve kuyu üstü / makine
        #  dairesi YATAY kesittir ( ofisin 477-8 ve 12744-3 paftaları gibi )
        self.assertEqual(
            [c["ad"] for c in self.bilgi["cizimler"]],
            [
                "kuyu_kesiti_yan",
                "kuyu_kesiti_on",
                "kuyu_plani",
                "kabin_ustu",
                "kuyu_dibi",
                "kuyu_ustu",
                "kasnak_duzeni",
                "giris",
                "kapi_kesiti",
                "veriler",
            ],
        )
        self.assertEqual(
            [c["ad"] for c in self.bilgi_md["cizimler"]],
            [
                "kuyu_kesiti_yan",
                "kuyu_kesiti_on",
                "kuyu_plani",
                "kabin_ustu",
                "kuyu_dibi",
                "makine_dairesi",
                "delik_plani",
                "kasnak_duzeni",
                "giris",
                "kapi_kesiti",
                "veriler",
            ],
        )
        bloklar = {
            e.dxf.name: e for e in self.d.modelspace().query("INSERT") if e.dxf.name.startswith("CIZIM_")
        }
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
                self.assertGreaterEqual(k[0], pafta.SERBEST[0] + pafta.KENAR - 1e-6)
                self.assertLessEqual(k[2], bilgi["sag"] - pafta.KENAR + 1e-6)
                self.assertGreaterEqual(k[1], pafta.SERBEST[1] + pafta.KENAR - 1e-6)
                self.assertLessEqual(k[3], pafta.SERBEST[3] - pafta.KENAR + 1e-6)
            for a, b in itertools.combinations(kutular, 2):
                self.assertFalse(
                    a[0] < b[2] + pafta.ARA - 1e-6
                    and b[0] < a[2] + pafta.ARA - 1e-6
                    and a[1] < b[3] + pafta.ARA - 1e-6
                    and b[1] < a[3] + pafta.ARA - 1e-6,
                    (a, b),
                )

    def test_antet(self):
        yazilar = {e.dxf.text for e in self.d.modelspace().query("TEXT")}
        for beklenen in ("1,00 m/sn", "8 DURAK", "21000", "1350", "1400", "2:1", "89*62", "1/20 1/50"):
            self.assertIn(beklenen, yazilar)
        #  Çizimin bilmediği değerler boş:  şablonun örnekleri kalmaz
        for ornek in ("300 KG (4 KİŞİ)", "Sınıf I", "2,67 KW", "0,1/2 DURAK", "70*70*9"):
            self.assertNotIn(ornek, yazilar)

    def test_yerlesim_ve_cerceve_uzatma(self):
        #  Sığan yerleşim çerçeveyi uzatmaz;  sığmayan sağa uzatır ( aşağı taşmaz )
        yerler, sag = pafta.yerlesim([(200, 400)] * 3)
        self.assertEqual(sag, pafta.SERBEST[2])
        yerler, sag = pafta.yerlesim([(400, 400)] * 9)
        self.assertGreater(sag, pafta.SERBEST[2])
        self.assertTrue(all(y >= pafta.SERBEST[1] + pafta.KENAR - 1e-6 for _, y in yerler))
        import ezdxf

        d = ezdxf.readfile(pafta.SABLON)
        pafta._cerceveyi_uzat(d, sag)
        xs = {round(p.x, 1) for e in d.modelspace().query("LINE") for p in (e.dxf.start, e.dxf.end)}
        self.assertIn(round(sag, 1), xs)
        self.assertNotIn(round(pafta.BANT[2], 1), xs)

    def test_sablon_degisirse_durur(self):
        import ezdxf

        d = ezdxf.readfile(pafta.SABLON)
        pafta._sablon_dogrula(d)
        pafta._antet_yazisi(d, pafta.ANTET["hiz"][1]).dxf.insert = (0, 0)
        with self.assertRaises(ValueError):
            pafta._sablon_dogrula(d)

    def test_dxf_gecerli(self):
        import tempfile
        import ezdxf
        from ezdxf.audit import Auditor

        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"})):
            with tempfile.TemporaryDirectory() as k:
                yol = os.path.join(k, "p.dxf")
                open(yol, "wb").write(pafta.yaz(g))
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
            pafta.belge(_ornek(dusey={"kabin_konsol_arasi": 0}))


class KapiBolgesi(unittest.TestCase):
    """Kat kapısı ve kabin kapısı ( referans proje kuyu planı vektörleri ve kapı detayı )."""

    def _kutular(self, e, ad):
        return [(x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"]) for x in e if x.get("ad") == ad]

    def test_tarama_kapi_boslugundan_gecmez(self):
        """Kapının olduğu duvar boşluğun iki yanında iki parça:  hiçbir çizimde
        tarama bir kapı parçasına ( boşluk, kasa, oda kapısı ) binmez.  Kuyu
        planında ön duvarın, makine dairesi planında oda duvarının taraması
        kapı boşluğundan geçiyordu ( DWG'de de ).  Kapı hizasından kesilmeyen
        planlarda ön duvar kesintisizdir."""

        projeler = [_ornek(), _duvar_boslugu()] + [
            _ornek(
                makine={"yeri": "Makine dairesi"},
                makine_dairesi={
                    "kapi_duvar": d,
                    "pano_duvar": "Sol" if d == "Sağ" else "Sağ",
                    #  yan duvarda kapı tabliyenin gerisinde ( önü tek kotta )
                    **({"kapi_konum": 2500} if d in ("Sol", "Sağ") else {}),
                },
            )
            for d in ("Ön", "Arka", "Sol", "Sağ")
        ]
        sayi = 0
        for g in projeler:
            for cizim, (dogrula, ciz, _) in cizimler.CIZIMLER.items():
                self.assertEqual(dogrula(g), [], cizim)
                e = ciz(g)
                tarama = [
                    (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
                    for x in e
                    if x["tip"] in ("tarama", "tarama_tugla")
                ]
                kapi = [
                    (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
                    for x in e
                    if x["katman"] == "KAPI" and x["tip"] == "dikdortgen"
                ]
                for t in tarama:
                    for k in kapi:
                        sayi += 1
                        with self.subTest(
                            cizim=cizim,
                            montaj=g["kapi"]["montaj"],
                            oda_kapisi=g["makine_dairesi"]["kapi_duvar"],
                            tarama=t,
                            kapi=k,
                        ):
                            self.assertFalse(
                                t[0] < k[2] - 1e-6
                                and k[0] < t[2] - 1e-6
                                and t[1] < k[3] - 1e-6
                                and k[1] < t[3] - 1e-6
                            )
        self.assertGreater(sayi, 100)
        #  Ön duvar:  kapı hizasında kaba boşluğun ( kapıdan iki yanda 140 —
        #  LiftDesigner, giriş görünüşüyle aynı ) iki yanında;  kabin üstü, kuyu
        #  dibi, kuyu üstü ve delik planında kesintisiz
        k, kp = girdi.ORNEK["kuyu"], girdi.ORNEK["kapi"]
        self.assertEqual(kp["montaj"], "Kuyu içine")
        yan = sabitler.sabitler(girdi.ORNEK["_cizim_sabitleri"])["kaba_bosluk_yan_payi"]

        def on_duvar(e):
            return sorted(
                (x["x"], x["x"] + x["g"]) for x in e if x["tip"] == "tarama" and x["y"] == -k["duvar_on"]
            )

        self.assertEqual(
            on_duvar(geometri.plan(_ornek())),
            [
                (-k["duvar_sol"], kp["sol_pay"] - yan),
                (kp["sol_pay"] + kp["genislik"] + yan, k["genislik"] + k["duvar_sag"]),
            ],
        )
        for cizim in ("kabin_ustu", "kuyu_dibi", "kuyu_ustu", "delik_plani"):
            with self.subTest(cizim=cizim):
                self.assertEqual(
                    on_duvar(cizimler.CIZIMLER[cizim][1](_ornek())),
                    [(-k["duvar_sol"], k["genislik"] + k["duvar_sag"])],
                )

    def test_kanatlar_esiklerin_ustunde_kabinle_cakismaz(self):
        #  Ortadan açılan 2 kanatlı kapı referans projede sağda sığmaz ( 470 <
        #  480 — kanat_cepleri );  4 kanatlı merkezi sığar.  3 kanatlı teleskopikte
        #  eşikler 135:  kabin 90 geride ( kapı hattı 195 + 30 + 135 ).
        for g in (
            _ornek(),
            _duvar_boslugu(),
            _ornek(kapi={"tip": "Otomatik Merkezi 4 Kanat"}),
            _ornek(kapi={"tip": "Teleskopik 3 Kanat Sol"}, kabin={"on_pay": 360}),
            _sag_ayna(),
            _arka(),
        ):
            self.assertEqual(geometri.dogrula(g), [])
            e = geometri.plan(g)
            kabin = self._kutular(e, "kabin_dis")[0]
            for kanat, esik in (("kat_kanadi", "kat_esigi"), ("kabin_kanadi", "kabin_esigi")):
                es = self._kutular(e, esik)[0]
                for k in self._kutular(e, kanat):
                    with self.subTest(montaj=g["kapi"]["montaj"], tip=g["kapi"]["tip"], kanat=kanat):
                        self.assertTrue(es[1] - 1e-9 <= k[1] and k[3] <= es[3] + 1e-9, (k, es))
                        #  Kanat kabin gövdesinin içine girmez
                        self.assertLessEqual(k[3], kabin[1] + 1e-9)

    def test_montaj_yerleri(self):
        S = sabitler.sabitler()
        for montaj, kasa, esik, hat in (
            ("Duvar boşluğuna", (-60, 0), (0, 90), 90),
            ("Kuyu içine", (0, 60), (60, 150), 150),
        ):
            KB = girdi.kapi_bolgesi(_ornek(kapi={"montaj": montaj}), S)
            self.assertEqual((KB["kasa"], KB["esik"], KB["hat"]), (kasa, esik, hat))
        self.assertTrue(any("kapi.montaj" in h for h in geometri.dogrula(_ornek(kapi={"montaj": "Havada"}))))

    def test_esik_araligi_ve_kuyu_yuzu_sinirlari(self):
        #  Kabin eşiği 90;  duvar boşluğunda kapı hattı 90 → aralık on_pay − 180
        #  ( 0 < … ≤ 35:  181 – 215 );  kuyu içinde hat 150 → on_pay − 240 ( 241 – 275 ).
        for montaj, alt, ust in (("Duvar boşluğuna", 180, 215), ("Kuyu içine", 240, 275)):
            for on, uygun in ((alt, False), (alt + 1, True), (ust, True), (ust + 1, False)):
                h = geometri.dogrula(_ornek(kapi={"montaj": montaj}, kabin={"on_pay": on}))
                with self.subTest(montaj=montaj, on_pay=on):
                    self.assertEqual(not any("eşiğ" in x for x in h), uygun, h)

    def test_referans_kapi_zinciri(self):
        #  referans proje:  iç yüzden kapı hattına 150, oradan ray eksenine 1.017,
        #  ray ekseninden arka iç yüze 682 ( 150 + 1.017 + 682 = 1.849 ≈ 1.850 )
        g = _ornek()
        KB = girdi.kapi_bolgesi(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
        ry = g["kabin_ray"]["kapi_arasi"]
        self.assertEqual(KB["hat"], 150)
        self.assertEqual(ry - KB["hat"], 1017)
        self.assertAlmostEqual(g["kuyu"]["derinlik"] - ry, 682, delta=1)
        metin = {x.get("ad"): x["metin"] for x in geometri.plan(g) if x["tip"] == "olcu"}
        self.assertEqual(metin["olcu_kat_kapisi"], "150")
        self.assertEqual(metin["olcu_kabin_esigi"], "90")


if __name__ == "__main__":
    unittest.main(verbosity=2)
