"""Gerçek form girdileriyle katlar, tampon stroku ve SVG çizgi türleri."""

import copy
import json
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "hesap"))

from api import cizim as UC, uygulama as UA
from cizim import dusey as DY, geometri as GE, girdi as GI, kopru as KO
from cizim import kuyu_kesiti as KE, svg as SV, dxf as DX
from cizim import sabitler as CS
from engine.uygulama import girdi as UG, mukavemet_girdi as MG


def _veri(**alanlar):
    return {"asansorler": [alanlar], "proje_geneli": {}, "sabitler": {}}


def _g(veri):
    ham, i, proje = UC._istek(veri)
    a = UG.tamamla(ham)
    g, hata = KO.cizim_girdisi(a, None, proje, i + 1)
    return g, hata, a


class Katlar(unittest.TestCase):
    def test_kapi_ust_payi_ve_esik_icin_duvar_kalir(self):
        for montaj in GI.KAPI_MONTAJLARI:
            g = copy.deepcopy(GI.ORNEK)
            g["kapi"]["montaj"] = montaj
            #  Katalogdan ( referans projenin örneği:  üst payı 200;  eşik 50 —
            #  LiftDesigner )
            S = CS.sabitler(g["_cizim_sabitleri"])
            alt = S["esik_kalinlik"] if montaj == "Duvar boşluğuna" else 0
            sinir = g["kapi"]["yukseklik"] + S["kapi_ust_payi"] + alt
            for aralik, gecerli in ((sinir - 1, False), (sinir, False), (sinir + 1, True)):
                g["dusey"]["kat_yuksekligi"] = aralik
                with self.subTest(montaj=montaj, aralik=aralik):
                    self.assertEqual(not DY.durak_kotlari(g)[1], gecerli)

    def test_ozel_kapi_ust_payi_dogrulamada_kullanilir(self):
        g = copy.deepcopy(GI.ORNEK)
        g["dusey"]["kat_yuksekligi"] = 2400
        self.assertFalse(DY.durak_kotlari(g)[1])
        self.assertTrue(DY.durak_kotlari(g, {"kapi_ust_payi": 400})[1])

    def test_negatif_duvar_ureten_form_girdisi_reddedilir(self):
        v = _veri(seyir_mesafesi=15.05)  # 8 durak, 2150 mm aralık, 2000 mm kapı
        r = json.loads(UC.api_cizimler(v).body)
        self.assertFalse(r["aktif"])
        self.assertTrue(any("üst payı" in h for h in r["hata"]), r)

    def test_farkli_katlar_formdan_kesitlere_gecer(self):
        v = _veri(durak_adedi=4, seyir_mesafesi=9.6, kat_yukseklikleri="3400; 3000; 3200")
        g, hata, a = _g(v)
        self.assertEqual(hata, [])
        self.assertEqual(DY.durak_kotlari(g), ([0, 3400, 6400, 9600], []))
        self.assertEqual(a["seyir_mesafesi"], 9.6)
        r = json.loads(UC.api_cizimler(v).body)
        self.assertTrue(r["aktif"], r.get("hata"))
        for ciz in (KE.yan_kesit, KE.on_kesit):
            e = ciz(g)
            self.assertFalse(
                [p for p in e if p["tip"] in ("tarama", "dikdortgen") and (p["g"] <= 0 or p["d"] <= 0)]
            )
            metinler = {p["metin"] for p in e if p["tip"] == "yazi"}
            self.assertTrue({"+3,40", "+6,40", "+9,60"} <= metinler)
            self.assertFalse(DX.belge(e, olcek=50).audit().errors)

    def test_bos_alan_eski_esit_dagilimi_korur(self):
        for ham in (None, "", "  "):
            g, hata, _ = _g(_veri(kat_yukseklikleri=ham))
            self.assertEqual(hata, [])
            self.assertEqual(g["dusey"]["kat_yuksekligi"], 3000)

    def test_eksik_bozuk_ve_seyirle_celisen_listeler_reddedilir(self):
        for ham in (
            "3400; 3000",
            "3400; 3000; 3100",
            "abc; 3000; 3200",
            "3.400; 3000; 3200",
            "nan; 3000; 3200",
            "-1; 3000; 3200",
            "3400;;3200",
            [True, 3000, 3200],
            {"kat": 3400},
        ):
            with self.subTest(ham=ham):
                g, hata, _ = _g(_veri(durak_adedi=4, seyir_mesafesi=9.6, kat_yukseklikleri=ham))
                self.assertIsNone(g)
                self.assertTrue(any("kat yüksekli" in h.lower() for h in hata), hata)

    def test_ondalik_virgul_desteklenir(self):
        g, hata, _ = _g(_veri(durak_adedi=3, seyir_mesafesi=6.4005, kat_yukseklikleri="3400,5; 3000"))
        self.assertEqual(hata, [])
        self.assertEqual(DY.durak_kotlari(g)[0], [0, 3400.5, 6400.5])

    def test_alan_form_sozlesmesinde_ve_her_asansorde_ayridir(self):
        f = next(
            f
            for gr in UA.uygulama_alanlari()["gruplar"]
            for f in gr["alanlar"]
            if f["anahtar"] == "kat_yukseklikleri"
        )
        self.assertEqual((f["tur"], f["varsayilan"]), ("metin", None))
        a, _ = UA._asansor_girdileri(
            {
                "asansorler": [{"kat_yukseklikleri": "3400; 3000"}, {"kat_yukseklikleri": "3000; 3400"}],
                "proje_geneli": {},
                "sabitler": {},
            }
        )
        self.assertEqual([v["kat_yukseklikleri"] for v in a], ["3400; 3000", "3000; 3400"])


class Tamponlar(unittest.TestCase):
    def test_iki_tamponun_asiri_ezilmesi_cizimde_reddedilir(self):
        for tur in ("kabin", "agirlik"):
            r = json.loads(UC.api_cizimler(_veri(**{tur + "_tampon_ezilme": 110})).body)
            with self.subTest(tur=tur):
                self.assertFalse(r["aktif"])
                self.assertTrue(any("ezilme" in h and "boyundan" in h for h in r["hata"]), r)

    def test_kendi_boyu_kadar_ezilme_sinirda_kabul_edilir(self):
        for tur in ("kabin", "agirlik"):
            g = copy.deepcopy(GI.ORNEK)
            g["dusey"][tur + "_tampon_ezilme"] = g["dusey"][tur + "_tampon_boyu"]
            self.assertFalse(KE.dogrula(g))

    def test_agirlik_tamponu_hesap_motorunda_da_denetlenir(self):
        for boy in (None, 100, 80):
            g = MG.tamamla({**MG.varsayilanlar(), "agirlik_tampon_boyu": boy, "agirlik_tampon_ezilme": 110})
            self.assertTrue(any("Ağırlık tamponu ezilme" in h and "aşamaz" in h for h in MG.dogrula(g)))
        g["agirlik_tampon_boyu"] = 120
        self.assertFalse(any("Ağırlık tamponu ezilme" in h for h in MG.dogrula(g)))


class KesikCizgiler(unittest.TestCase):
    def test_cizgi_daire_ve_dikdortgen_katman_desenini_kullanir(self):
        ns = "{http://www.w3.org/2000/svg}"
        for kat, desen in SV.KESIK.items():
            for olcek in (20, 50):
                e = [GE._cizgi(kat, 0, 0, 100, 0), GE._daire(kat, 0, 0, 50), GE._dik(kat, 0, 0, 100, 100)]
                r = ET.fromstring(SV.yaz(e, GE.sinir(e), olcek=olcek))
                for p in list(r.find(ns + "g")):
                    self.assertEqual(p.attrib["stroke-dasharray"], SV._kesik(desen, olcek / 20))

    def test_gercek_kesit_tavan_payi_svg_ve_dxfte_kesiklidir(self):
        g = copy.deepcopy(GI.ORNEK)
        for ciz in (KE.yan_kesit, KE.on_kesit):
            e = [q for q in ciz(g) if q.get("ad") == "tavan_kirisi"]
            svg = SV.yaz(e, GE.sinir(e), olcek=50)
            self.assertIn('stroke-dasharray="100 75"', svg)
            d = DX.belge(e, olcek=50)
            self.assertEqual(d.layers.get("GIZLI").dxf.linetype, "DASHED")


if __name__ == "__main__":
    unittest.main()
