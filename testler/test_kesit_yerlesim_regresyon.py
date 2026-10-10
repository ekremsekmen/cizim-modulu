"""Kesitlerin fiziksel tutarlılığı ( 1 Eki incelemesi ):  kabin şasesinin üst
kirişi kabin tavanının üstünde, karşı ağırlığın patenleri raylarında, dolgu
ağırlık kasnağının altında;  karşı ağırlığın genişliği boşsa ray arasından
gelir.  Kabin üstü kasnaklarına taşıyıcı çizilmez ( kaynağı yok — kullanıcı
kararı 1 Eki ).  Kabin altı askının taşıyıcısı eskisi gibi."""

import json
import unittest

from temel import ortusur
from testler.test_gercek_projeler import GP, UC, UYG, E_UGR, E_UYG, CK
from cizim import baglantilar as CB, donanim as CDN, geometri as E
from cizim import kabin_ustu as KU, kuyu_kesiti as K
from cizim import makine as CMK, olculer as O


def _istek(values):
    a = dict(values)
    common = {k: a.pop(k) for k in list(a) if k in UYG.PROJE_GENELI_ALANLAR}
    return {"asansorler": [a], "proje_geneli": common, "sabitler": {}, "asansor": 0}


def _girdi(values):
    ham, _, _ = UC._istek(_istek(values))
    g, hata = CK.cizim_girdisi(E_UGR.tamamla(ham))
    if hata:
        raise AssertionError(hata)
    return g


#  Kesiti kurulmayan gerçek proje:  12495-18'in tavanında çömelme alanına yer
#  yok ( çapraz halat — test_gercek_projeler.test_12495_18_kabin_ustu_siginma )
KESITSIZ = {"12495-18"}


class KesitYerlesimRegresyon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projeler = {ad: _girdi(v) for ad, v in GP.PROJELER.items()}

    def _kesitli(self):
        for ad, g in self.projeler.items():
            Y = K.yerlesim(g)
            self.assertEqual("M" not in Y, ad in KESITSIZ, (ad, Y.get("hata")))
            if ad not in KESITSIZ:
                yield ad, g, Y

    def test_yuksek_kabin_sase_cakismasi_api_ve_hesapta_reddedilir(self):
        values = {"kabin_ic_yuksekligi": 2500, "son_kat_yuksekligi": 5000}
        g = _girdi(values)
        Y = K.yerlesim(g)
        #  8 Eki:  varsayılan paten arası 2.660 ( LiftDesigner — patenler kirişlerin
        #  dışında );  2.500'lük kabinin tavanı 2.560, kirişin altı 2.200 → 3.020
        self.assertEqual(g["dusey"]["kabin_paten_arasi"], 2660)
        self.assertTrue(any("üst şase kirişi" in h and "3020 mm" in h for h in Y["hata"]), Y["hata"])
        self.assertIn(Y["hata"][0], Y["diger"])
        api = json.loads(UC.api_cizimler(_istek(values)).body)
        self.assertFalse(api["aktif"])
        self.assertTrue(any("üst şase kirişi" in h for h in api["hata"]), api)
        sonuc = E_UYG.hesapla(values)
        b11 = next(b for b in sonuc["bolumler"] if b["kimlik"] == "siginma_alanlari")
        self.assertFalse(b11["sonuc"]["uygun"])
        self.assertIn("üst şase kirişi", b11["sonuc"]["metin"])
        self.assertNotIn("eksik_hesap", b11)

    def test_sase_tavan_siniri_ve_duzeltilmis_girdi(self):
        #  Kirişin altı = paten arası − 460 ( şase altı 320 − alt paten payı 50 +
        #  yarım paten 50 + kiriş 140 );  tavan 2.060 ( 2.500'lük kabinde 2.560 )
        for aralik, uygun in ((2519.9, False), (2520, True), (2520.1, True), (3020, True)):
            g = _girdi(
                {
                    "kabin_ic_yuksekligi": 2500 if aralik == 3020 else 2000,
                    "kabin_paten_arasi": aralik,
                    "son_kat_yuksekligi": 5000,
                }
            )
            with self.subTest(paten_arasi=aralik):
                self.assertEqual(not K.dogrula(g), uygun)
                self.assertEqual(g["dusey"]["kabin_paten_arasi"], aralik)
                if uygun:
                    for ciz in (K.yan_kesit, K.on_kesit):
                        e = ciz(g)
                        self.assertTrue(e)
                        if ciz == K.on_kesit:
                            Y = K.yerlesim(g)
                            roof = CDN.kabin_kotlari(g["dusey"], Y["S"], Y["kotlar"][-1], g["aski"])["tavan"]
                            beam = max((p for p in e if p.get("ad") == "sase_kirisi"), key=lambda p: p["y"])
                            self.assertGreaterEqual(beam["y"], roof - 1e-6)

    def test_agirlik_pateni_her_yonde_ray_yuzunu_kavrar(self):
        for ad, g, Y in self._kesitli():
            M, S = Y["M"], Y["S"]
            raylar = [r for r in M["raylar"] if r["tur"] == "agirlik"]
            parcalar = CB.agirlik_patenleri(g, S, M["agirlik"]["kutu"], raylar, -70, 70)
            patenler = [p["k"] for p in parcalar if p["tur"] == "kutu"]
            self.assertEqual(len(patenler), 2)
            arka = g["agirlik"]["yeri"] == "Arka"
            eks = 0 if arka else 1
            for pk, r in zip(patenler, raylar):
                rk = r["kutu"]
                with self.subTest(proje=ad, ray=rk):
                    self.assertTrue(ortusur(pk[:4], rk))
                    self.assertAlmostEqual(pk[eks + 2] - pk[eks], S["paten_en"])
                    self.assertAlmostEqual(pk[3 - eks] - pk[1 - eks], S["paten_boy"])
                    yuz = (pk[eks] + pk[eks + 2]) / 2
                    self.assertIn(yuz, (rk[eks], rk[eks + 2]))
                    self.assertAlmostEqual((pk[1 - eks] + pk[3 - eks]) / 2, (rk[1 - eks] + rk[3 - eks]) / 2)
            self.assertFalse([p for p in parcalar if p["tur"] != "kutu"])

    def test_1022_pateni_derinlikte_rayla_hizali(self):
        g = self.projeler["1022"]
        e = K.yan_kesit(g)
        patenler = [p for p in e if p.get("ad") == "agirlik_paten"]
        self.assertTrue(patenler)
        self.assertEqual({(p["x"], p["g"]) for p in patenler}, {(1770, 100)})
        self.assertTrue(all(p["x"] < 1820 < p["x"] + p["g"] for p in patenler))

    def test_paten_kesiti_ortak_cisimlerin_izdusumu(self):
        for ad in ("1022", "1275", "4815-6"):
            g = self.projeler[ad]
            Y = K.yerlesim(g)
            M, S = Y["M"], Y["S"]
            B = K.yan_bakis(g)
            AK = CDN.agirlik_kotlari(
                M, M["agirlik"]["tampon_ustu"] + g["dusey"]["agirlik_carpma_arasi"] + Y["kotlar"][-1]
            )
            e = K.yan_kesit(g)
            for z0, z1 in ((AK["alt_paten"], AK["alt_paten_ust"]), (AK["ust_paten_alt"], AK["ust_paten"])):
                parcalar = CB.agirlik_patenleri(
                    g, S, M["agirlik"]["kutu"], [r for r in M["raylar"] if r["tur"] == "agirlik"], z0, z1
                )
                for el in CMK.gorunus(parcalar, B, E._dik, E._daire, E._cizgi):
                    el.pop("_derin", None)  # kesitin iç işareti ( kabin_arkasi kaldırır )
                    with self.subTest(proje=ad, parca=el["ad"]):
                        self.assertIn(el, e)

    def test_dolgu_kesitte_hesapla_ayni_ve_kasnagin_altinda(self):
        for ad in ("4815-6", "1275", "1022", "800 KG"):
            g = self.projeler[ad]
            beklenen = 3280 if g["aski"]["duzen"] == "Doğrudan" else 2980
            self.assertEqual(O.hesap_olculeri(g)["agirlik_dolgu_yuksekligi"], beklenen)
            for ciz in (K.yan_kesit, K.on_kesit):
                e = ciz(g)
                dolgular = [p for p in e if p.get("ad") == "agirlik_dolgu"]
                for dolgu in dolgular:
                    with self.subTest(proje=ad, kesit=ciz.__name__):
                        self.assertEqual(dolgu["d"], beklenen)
                        for kasnak in (p for p in e if p.get("ad") == "agirlik_kasnagi"):
                            alt = kasnak["y"] - kasnak["r"] if kasnak["tip"] == "daire" else kasnak["y"]
                            self.assertLessEqual(dolgu["y"] + dolgu["d"], alt)

    def test_dolgu_katalog_degisiminde_de_ortak(self):
        g = _girdi({"agirlik_kasnak_capi": 500})
        g["_cizim_sabitleri"] = {"agirlik_kasnak_ust": 150, "agirlik_kiris": 20}
        e = K.yan_kesit(g)
        dolgu = next(p for p in e if p.get("ad") == "agirlik_dolgu")
        self.assertEqual(dolgu["d"], O.hesap_olculeri(g)["agirlik_dolgu_yuksekligi"])
        self.assertEqual(dolgu["d"], 2880)

    def test_dogrudan_askida_kasnak_tasiyicisi_yok(self):
        g = self.projeler["1022"]
        self.assertEqual(CB.kasnak_tasiyicilari(g, K.yerlesim(g)["S"], 0), [])
        self.assertFalse([p for p in K.yan_kesit(g) if p.get("ad") == "kasnak_tasiyici_sematik"])

    def test_kabin_ustu_kasnaklarina_tasiyici_cizilmez(self):
        #  Kullanıcı kararı 1 Eki:  kaynağı olmayan taşıyıcı çizilmez ( kabin
        #  üstü planında korkuluk çizgilerine biniyordu ).  Kabin altı askının
        #  taşıyıcısı eskisi gibi.
        #  Kapı ağırlığın tersine açılır:  sola açılan kabin kapısının cebi soldaki
        #  ağırlığın ara kirişine çarpar ( geometri.kanat_cebi_carpismalari )
        for v in (
            {
                "aski_duzeni": "Kabin üstü",
                "agirlik_yeri": "Sol",
                "son_kat_yuksekligi": 5000,
                "kat_kapisi_tipi": "Teleskopik Sağ",
            },
            GP.PROJELER["1275"],
        ):
            g = _girdi(v)
            with self.subTest(v.get("aski_duzeni")):
                self.assertEqual(CB.kasnak_tasiyicilari(g, K.yerlesim(g)["S"], 0), [])
                for e in (K.yan_kesit(g), K.on_kesit(g), E.plan(g), KU.ciz(g)):
                    self.assertFalse([p for p in e if p.get("ad") == "kasnak_tasiyici_sematik"])
        g = self.projeler["4815-6"]
        self.assertEqual(g["aski"]["duzen"], "Kabin altı")
        self.assertTrue(CB.kasnak_tasiyicilari(g, K.yerlesim(g)["S"], 0))

    def test_agirlik_genisligi_bossa_ray_arasindan(self):
        #  Kullanıcı kararı 1 Eki:  Gy boşsa DBGW − 60 ( iki uçta paten payı —
        #  referans proje 790 / 850 ), DBGW boşsa Gy + 60, ikisi de boşsa 960.
        #  Eskiden Gy hep 960'tı:  1022'de ( DBGW 1.700 ) çerçeve ile ray
        #  arasında her yanda 370 mm kalıyordu.
        for v, gy, dbgw in (
            ({}, 960, 1020),
            ({"agirlik_ray_arasi": 1700}, 1640, 1700),
            ({"agirlik_genisligi": 800}, 800, 860),
            ({"agirlik_genisligi": 800, "agirlik_ray_arasi": 1700}, 800, 1700),
        ):
            g = _girdi(v)
            with self.subTest(v):
                self.assertEqual((g["agirlik"]["genislik"], g["agirlik"]["ray_arasi"]), (gy, dbgw))
                self.assertEqual(E_UYG.hesapla(v)["girdi"]["agirlik_genisligi"], gy)
        for ad, g, Y in self._kesitli():
            M = Y["M"]
            blok = M["agirlik"]["kutu"]
            eks = 0 if g["agirlik"]["yeri"] == "Arka" else 1
            for r in (r["kutu"] for r in M["raylar"] if r["tur"] == "agirlik"):
                with self.subTest(proje=ad, ray=r):
                    self.assertAlmostEqual(min(abs(r[eks + 2] - blok[eks]), abs(r[eks] - blok[eks + 2])), 30)

    def test_planda_kabin_ile_agirlik_arasi_olculur(self):
        #  Kullanıcı isteği 1 Eki ( LiftDesigner gibi ):  arkadaki ağırlıkta kabin
        #  rayı – ağırlık rayı ( 800 KG:  LiftDesigner 850 · 970 · 180;  bizim kapı
        #  bölgemiz 10 kısa ) ve kabin – ağırlık – duvar;  yandakinde duvar –
        #  ağırlık – kabin ( 4815-6:  LiftDesigner 100 · 150 · 225 · PLW ).
        def olculer(g):
            return [o.get("metin") or f"{o['uzunluk']:g}" for o in E.plan(g) if o["tip"] == "olcu"]

        o = olculer(self.projeler["800 KG"])
        self.assertIn("KABİN RAYI – AĞIRLIK RAYI 980", o)
        i = o.index("RAY EKSENİ 840")
        self.assertEqual(o[i : i + 3], ["RAY EKSENİ 840", "KABİN RAYI – AĞIRLIK RAYI 980", "180"])
        i = o.index("KABİN + ŞASE 1370")
        self.assertEqual(o[i + 1 : i + 4], ["105", "150", "105"])
        #  8 Eki:  zincir kabinin dış yüzüne ( PLW ) — şasenin dikmeleri rayın
        #  ucunda;  LiftDesigner'la birebir ( eskiden "ŞASE DIŞI 1440" · 195 )
        o = olculer(self.projeler["4815-6"])
        i = o.index("KABİN DIŞI 1380")
        self.assertEqual(o[i + 1 : i + 4], ["100", "150", "225"])

    def test_duvarlar_ayri_ayri(self):
        #  2 Eki:  dört duvar ayrı kalınlıkta ( LiftDesigner 4815-6:  arka 250,
        #  öbürleri 200 → dış ölçü 2.500 × 2.450 );  boş bırakılan ortak
        #  kalınlığı alır, kuyu dibinin ve tavanın döşemesi ortak kalınlıktadır.
        o = [x.get("metin") for x in E.plan(self.projeler["4815-6"]) if x["tip"] == "olcu"]
        self.assertIn("DIŞ ÖLÇÜ 2500", o)
        self.assertIn("DIŞ ÖLÇÜ 2450", o)
        g = _girdi({"kuyu_duvar_kalinligi": 180, "kuyu_duvar_sag": 250})
        self.assertEqual(
            {k: g["kuyu"][k] for k in ("duvar_on", "duvar_arka", "duvar_sol", "duvar_sag", "doseme")},
            {"duvar_on": 180, "duvar_arka": 180, "duvar_sol": 180, "duvar_sag": 250, "doseme": 180},
        )
        g = _girdi({"kuyu_duvar_on": 300})
        Y = K.yerlesim(g)
        taban = [
            p
            for p in K.yan_kesit(g)
            if p["tip"] == "dikdortgen"
            and p["katman"] == "KUYU-DUVAR"
            and p["x"] == 0
            and abs(p["y"] + p["d"] - Y["taban"]) < 1e-6
        ]
        self.assertEqual([p["d"] for p in taban], [150])


if __name__ == "__main__":
    unittest.main()
