"""Gerçek form girdileriyle katlar, tampon stroku ve SVG çizgi türleri."""

import copy
import json
import unittest
import xml.etree.ElementTree as ET


from uclar import cizim_uclari, uygulama_uclari
from cizim import eleman
from cizim import dusey, geometri, girdi, kopru
from cizim import kuyu_kesiti, svg, dxf
from cizim import sabitler
from cizim import uslup
from motor.uygulama import uygulama_girdisi, mukavemet_girdi
from uclar import uygulama_istegi


def _veri(**alanlar):
    return {"asansorler": [alanlar], "proje_geneli": {}, "sabitler": {}}


def _g(veri):
    ham, i, proje = cizim_uclari._istek(veri)
    a = uygulama_girdisi.tamamla(ham)
    g, hata = kopru.cizim_girdisi(a, None, proje, i + 1)
    return g, hata, a


class Katlar(unittest.TestCase):
    def test_kapi_ust_payi_ve_esik_icin_duvar_kalir(self):
        for montaj in girdi.KAPI_MONTAJLARI:
            g = copy.deepcopy(girdi.ORNEK)
            g["kapi"]["montaj"] = montaj
            #  Katalogdan ( referans projenin örneği:  üst payı 200;  eşik 50 —
            #  LiftDesigner )
            S = sabitler.sabitler(g["_cizim_sabitleri"])
            alt = S["esik_kalinlik"] if montaj == "Duvar boşluğuna" else 0
            sinir = g["kapi"]["yukseklik"] + S["kapi_ust_payi"] + alt
            for aralik, gecerli in ((sinir - 1, False), (sinir, False), (sinir + 1, True)):
                g["dusey"]["kat_yuksekligi"] = aralik
                with self.subTest(montaj=montaj, aralik=aralik):
                    self.assertEqual(not dusey.durak_kotlari(g)[1], gecerli)

    def test_ozel_kapi_ust_payi_dogrulamada_kullanilir(self):
        g = copy.deepcopy(girdi.ORNEK)
        g["dusey"]["kat_yuksekligi"] = 2400
        self.assertFalse(dusey.durak_kotlari(g)[1])
        self.assertTrue(dusey.durak_kotlari(g, {"kapi_ust_payi": 400})[1])

    def test_negatif_duvar_ureten_form_girdisi_reddedilir(self):
        v = _veri(seyir_mesafesi=15.05)  # 8 durak, 2150 mm aralık, 2000 mm kapı
        r = json.loads(cizim_uclari.api_cizimler(v).body)
        self.assertFalse(r["aktif"])
        self.assertTrue(any("üst payı" in h for h in r["hata"]), r)

    def test_farkli_katlar_formdan_kesitlere_gecer(self):
        v = _veri(durak_adedi=4, seyir_mesafesi=9.6, kat_yukseklikleri="3400; 3000; 3200")
        g, hata, a = _g(v)
        self.assertEqual(hata, [])
        self.assertEqual(dusey.durak_kotlari(g), ([0, 3400, 6400, 9600], []))
        self.assertEqual(a["seyir_mesafesi"], 9.6)
        r = json.loads(cizim_uclari.api_cizimler(v).body)
        self.assertTrue(r["aktif"], r.get("hata"))
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            e = ciz(g)
            self.assertFalse(
                [p for p in e if p["tip"] in ("tarama", "dikdortgen") and (p["g"] <= 0 or p["d"] <= 0)]
            )
            metinler = {p["metin"] for p in e if p["tip"] == "yazi"}
            self.assertTrue({"+3,40", "+6,40", "+9,60"} <= metinler)
            self.assertFalse(dxf.belge(e, olcek=50).audit().errors)

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
        ):
            with self.subTest(ham=ham):
                g, hata, _ = _g(_veri(durak_adedi=4, seyir_mesafesi=9.6, kat_yukseklikleri=ham))
                self.assertIsNone(g)
                self.assertTrue(any("kat yüksekli" in h.lower() for h in hata), hata)
        #  Yazı olmayan değer isteğin kapısında durur ( uygulama_istegi )
        for ham in ([True, 3000, 3200], {"kat": 3400}):
            with self.subTest(ham=ham), self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                _g(_veri(durak_adedi=4, seyir_mesafesi=9.6, kat_yukseklikleri=ham))
            self.assertIn("Kat yükseklikleri", k.exception.hatalar[0])

    def test_ondalik_virgul_desteklenir(self):
        g, hata, _ = _g(_veri(durak_adedi=3, seyir_mesafesi=6.4005, kat_yukseklikleri="3400,5; 3000"))
        self.assertEqual(hata, [])
        self.assertEqual(dusey.durak_kotlari(g)[0], [0, 3400.5, 6400.5])

    def test_alan_form_sozlesmesinde_ve_her_asansorde_ayridir(self):
        f = next(
            f
            for gr in uygulama_uclari.uygulama_alanlari()["gruplar"]
            for f in gr["alanlar"]
            if f["anahtar"] == "kat_yukseklikleri"
        )
        self.assertEqual((f["tur"], f["varsayilan"]), ("metin", None))
        a, _ = uygulama_istegi.asansor_girdileri(
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
            r = json.loads(cizim_uclari.api_cizimler(_veri(**{tur + "_tampon_ezilme": 110})).body)
            with self.subTest(tur=tur):
                self.assertFalse(r["aktif"])
                self.assertTrue(any("ezilme" in h and "boyundan" in h for h in r["hata"]), r)

    def test_kendi_boyu_kadar_ezilme_sinirda_kabul_edilir(self):
        for tur in ("kabin", "agirlik"):
            g = copy.deepcopy(girdi.ORNEK)
            g["dusey"][tur + "_tampon_ezilme"] = g["dusey"][tur + "_tampon_boyu"]
            self.assertFalse(kuyu_kesiti.dogrula(g))

    def test_agirlik_tamponu_hesap_motorunda_da_denetlenir(self):
        for boy in (None, 100, 80):
            g = mukavemet_girdi.tamamla(
                {**mukavemet_girdi.varsayilanlar(), "agirlik_tampon_boyu": boy, "agirlik_tampon_ezilme": 110}
            )
            self.assertTrue(
                any("Ağırlık tamponunun ezilmesi" in h and "aşamaz" in h for h in mukavemet_girdi.dogrula(g))
            )
        g["agirlik_tampon_boyu"] = 120
        self.assertFalse(any("Ağırlık tamponunun ezilmesi" in h for h in mukavemet_girdi.dogrula(g)))


class KesikCizgiler(unittest.TestCase):
    def test_cizgi_daire_ve_dikdortgen_katman_desenini_kullanir(self):
        ns = "{http://www.w3.org/2000/svg}"
        for kat, desen in ((k, v.desen) for k, v in uslup.KATMAN.items() if v.desen):
            for olcek in (20, 50):
                e = [
                    eleman.cizgi(kat, 0, 0, 100, 0),
                    eleman.daire(kat, 0, 0, 50),
                    eleman.dikdortgen(kat, 0, 0, 100, 100),
                ]
                r = ET.fromstring(svg.yaz(e, geometri.sinir(e), olcek=olcek))
                for p in list(r.find(ns + "g")):
                    self.assertEqual(p.attrib["stroke-dasharray"], svg.kesik(desen, olcek / 20))

    def test_gercek_kesit_tavan_payi_svg_ve_dxfte_kesiklidir(self):
        g = copy.deepcopy(girdi.ORNEK)
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            e = [q for q in ciz(g) if q.get("ad") == "tavan_kirisi"]
            svg_metni = svg.yaz(e, geometri.sinir(e), olcek=50)
            self.assertIn(f'stroke-dasharray="{svg.kesik("GIZLI", 2.5)}"', svg_metni)
            d = dxf.belge(e, olcek=50)
            self.assertEqual(d.layers.get("GIZLI").dxf.linetype, uslup.DESENLER["GIZLI"].dxf)


if __name__ == "__main__":
    unittest.main()


class Duvarlar(unittest.TestCase):
    def test_bina_duvari_girilince_cizimler_kurulur(self):
        """Sabitler'de bina duvarı ( tuğla tarama ) girilince geometri.sinir
        tuğla taramayı tanımıyordu:  min() hatası, ekrana hiçbir çizim
        gelmiyordu ( 20 Eki )."""
        from testler import test_yerlesim_saglamligi

        v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
        v["sabitler"] = {"bina_duvari": 200}
        yanit = json.loads(cizim_uclari.api_cizimler(v).body)
        self.assertTrue(yanit.get("aktif"), yanit.get("hata"))
        tugla = [e for e in geometri.plan(_g(v)[0]) if e["tip"] == "tarama_tugla"]
        self.assertTrue(tugla)
        x1, y1, x2, y2 = geometri.sinir(tugla)
        self.assertEqual(y2 - y1, 200)

    def test_makine_dairesi_duvarlarin_kendi_kalinligiyla_ortalanir(self):
        """Boş md_x / md_y:  oda kuyunun DIŞ genişliğine ortalı, önü ön
        duvarın dış yüzünde — sol / ön duvar ortak kalınlıktan farklıyken de
        ( eskiden ortak kalınlıkla kurulup 100 mm kayıyordu )."""
        from testler import test_yerlesim_saglamligi

        v = test_yerlesim_saglamligi.standart_istek(800, False, "Sağ")
        v["asansorler"][0].update(kuyu_duvar_kalinligi=200, kuyu_duvar_on=300, kuyu_duvar_sol=400)
        g = _g(v)[0]
        k, md = g["kuyu"], g["makine_dairesi"]
        self.assertEqual(
            md["x"] + md["genislik"] / 2.0, (k["genislik"] + k["duvar_sag"] - k["duvar_sol"]) / 2.0
        )
        self.assertEqual(md["y"], -k["duvar_on"])


class KatKirigi(unittest.TestCase):
    def test_kirilan_kesitte_parcanin_bicimi_zarfiyla_kayar(self):
        """Uzun kuyuda ara katlar kesitten çıkarılınca regülatörün gerçek
        biçimi kırılmamış kotunda — paftanın dışında — kalıyordu ( 20 Eki )."""
        from cizim import pafta
        from testler import test_yerlesim_saglamligi

        for mrl in (True, False):
            v = test_yerlesim_saglamligi.standart_istek(630, mrl, "Sağ", durak_adedi=12, seyir_mesafesi=33)
            g = test_yerlesim_saglamligi.duzen_girdisi(v)[0]
            for ad, _baslik, _olcek, e in pafta.cizim_listesi(g):
                if not ad.startswith("kuyu_kesiti"):
                    continue
                for el in e:
                    if el.get("bicim"):
                        ys = [y for p in el["bicim"] for _x, y in p["noktalar"]]
                        with self.subTest(mrl=mrl, cizim=ad, parca=el.get("ad")):
                            self.assertGreaterEqual(min(ys), el["y"] - 1)
                            self.assertLessEqual(max(ys), el["y"] + el["d"] + 1)
