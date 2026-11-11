"""10 KAS FİZİKSEL TARAMASININ İKİ BULGUSU ( gerçekçi 1.800 düzen — taslaklardan türetilmiş ).

1  Makine dairesizde regülatör elle makinenin ( karşı ağırlığın ) yanına alınınca kuyu
   üstünde kasnağı ve halatı ağırlık halat bağlantısının içine çiziliyordu ( aynı kot —
   kesitlerle doğrulandı ) ve çizim reddetmiyordu:  kuyu_ustu._cakismalar yalnız
   regülatörün gövdesine bakıyordu, kasnak gövdeden taşar.  O rayda gövde planda şasenin
   üstündedir:  kesitte şasenin üst yüzüne oturur ( eskiden 35 mm içindeydi ).
2  Tek kuyuda iki küçük asansörde ( 630 + 630, 630 + 800;  ağırlıklar sağda ) kuyu dibi
   planı "yük kutusuna yer yok" diye duruyor, bütün çizimler gidiyordu.  Kutu bizim
   koyduğumuz bir gösterimdir ( kullanıcı:  "fiziksel bir sınır değil" ):  yer yoksa
   küçük yazıyla, o da olmazsa kuyudan uzağa uzun okla konur.
"""

import copy
import json
import unittest
import unittest.mock

from cizim import cizimler
from cizim import geometri
from cizim import grup
from cizim import kuyu_dibi
from cizim import kuyu_ustu
from cizim import sabitler
from temel import ortusur
from testler.test_taslaklar import TASLAKLAR, istek
from uclar import cizim_uclari
from uclar import uygulama_istegi

T = {t["kimlik"]: t for t in TASLAKLAR}


def yanit(v):
    return json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)


def tek_kuyu(a, b, soldaki="1"):
    """İki taslak tek kuyuda:  kuyunun ortak girdileri birincininki, açık yandaki
    1,10 m'lik korkuluk için kuyu tavanı 0,50 m yukarıda."""
    v = istek(T[a])
    x, y = v["asansorler"][0], dict(T[b]["asansor"])
    x["kuyu_tavani_kotu"] = "+19,70"
    v["asansorler"].append(y)
    v["proje_geneli"].update(kuyu_duzeni="Tek kuyu", soldaki_asansor=soldaki, ayirma_kirisi="140")
    return v


class RegulatorMakineninYaninda(unittest.TestCase):
    def test_taslakta_regulator_karsi_yanda_ve_temiz(self):
        for k in ("630", "1275"):
            with self.subTest(k):
                r = yanit(istek(T[k]))
                self.assertTrue(r["aktif"], r.get("hata"))

    def test_makinenin_yanindaki_regulator_halat_baglantisina_binmez(self):
        """Regülatör elle makinenin yanına alınınca program kasnağı ve halatı halat
        bağlantısından uzak tutan kaçıklığı seçer ( eskiden kasnağın bağlantıya bindiği
        −200'ü seçiyordu );  yer yoksa reddeder — bindirerek çizmez."""
        #  630:  ağırlık ve makine sağda;  1275:  solda
        for k, yan in (("630", "Sağ"), ("1275", "Sol")):
            with self.subTest(k):
                v = istek(T[k])
                self.assertEqual(v["asansorler"][0]["agirlik_yeri"], yan)
                v["asansorler"][0]["regulator_yani"] = yan
                asansorler, ortak = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
                g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, None, "DENEME", 0)
                Y = kuyu_ustu.yerlesim(g)
                if hata:
                    self.assertTrue(any("egülatör" in str(h) for h in hata), hata)
                    continue
                kasnak = kuyu_ustu._reg_halat_kutusu(g, Y["reg_kasnak"])
                for b in (Y["agirlik_baglanti"], Y["kabin_baglanti"]):
                    for kutu in (kasnak, Y["reg_govde"], Y["reg_ayak"]):
                        self.assertFalse(ortusur(kutu, b), (k, kutu, b))

    def test_denetim_kasnagi_ve_ayagi_halat_baglantisina_karsi_sinar(self):
        Y = {
            "reg_govde": (100.0, 100.0, 300.0, 250.0),
            "reg_kasnak": (180.0, 30.0, 220.0, 330.0),
            "reg_ayak": (300.0, 100.0, 900.0, 250.0),
            "agirlik_baglanti": (150.0, 280.0, 400.0, 400.0),
            "kabin_baglanti": (600.0, 120.0, 800.0, 200.0),
        }
        g = {"kuyu_dibi": {"regulator_halat_capi": 6.0}}
        h = [str(x) for x in kuyu_ustu._regulator_cakismalari(g, Y)]
        self.assertEqual(len(h), 2, h)
        self.assertIn("kasnağı ve halatı ağırlık halat bağlantısı", h[0])
        self.assertIn("duvara giden ayağı kabin halat bağlantısı", h[1])
        #  Bağlantılardan uzakta sorun yok
        Y["agirlik_baglanti"], Y["kabin_baglanti"] = (
            (150.0, 400.0, 400.0, 500.0),
            (600.0, 300.0, 800.0, 400.0),
        )
        self.assertEqual(kuyu_ustu._regulator_cakismalari(g, Y), [])


class RegulatorSaseninUstunde(unittest.TestCase):
    """Regülatör makinenin yanındaki raydaysa gövdesi planda şasenin üstüne düşer:
    kesitte şasenin üst yüzüne oturur ( 11 Kas — tavandan sabit 462 ile gövdenin altı
    şasenin içine 35 mm giriyordu ).  Karşıdaki rayda kot değişmez."""

    def _kotlar(self, v):
        asansorler, ortak = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
        g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, None, "DENEME", 0)
        self.assertEqual(hata, [])
        e = cizimler.CIZIMLER["kuyu_kesiti_on"][1](g)
        govde = [
            geometri.sinir([x])
            for x in e
            if x.get("ad") == "regulator" and x["katman"] == "MAKINE" and x["tip"] == "dikdortgen"
        ]
        sase = [geometri.sinir([x]) for x in e if x.get("ad") == "makine_sasesi" and x["tip"] == "dikdortgen"]
        return min(k[1] for k in govde), max(k[3] for k in sase), g

    def test_makinenin_yaninda_sasenin_ust_yuzunde(self):
        v = istek(T["630"])
        v["asansorler"][0]["regulator_yani"] = "Sağ"
        alt, sase_ustu, _g = self._kotlar(v)
        self.assertAlmostEqual(alt, sase_ustu, delta=0.5)

    def test_karsidaki_rayda_kot_ayni(self):
        alt, sase_ustu, g = self._kotlar(istek(T["630"]))
        S = sabitler.sabitler(g.get("_cizim_sabitleri"))
        eksen = kuyu_ustu.yerlesim(g)["reg_cizim"]["geo"]["eksen"]
        tavan = alt + eksen + S["regulator_kasnak_merkez"]
        #  Kasnak merkezi tavandan 462:  gövdenin altı şasenin üst yüzünün altında kalır
        self.assertLess(alt, sase_ustu)
        self.assertAlmostEqual(tavan - alt, S["regulator_kasnak_merkez"] + eksen, delta=0.5)
        self.assertEqual(g["kuyu_dibi"]["regulator_yan"], "Sol")


class TekKuyudaKucukAsansorler(unittest.TestCase):
    def test_iki_kucuk_asansorun_kuyu_dibi_cizilir(self):
        for a, b, soldaki in (
            ("630", "630", "1"),
            ("630", "630", "2"),
            ("630", "800", "1"),
            ("800", "630", "2"),
        ):
            with self.subTest(f"{a} + {b} soldaki {soldaki}"):
                r = yanit(tek_kuyu(a, b, soldaki))
                self.assertTrue(r["aktif"], r.get("hata"))
                c = next(c for c in r["cizimler"] if c["ad"] == grup.ADLAR["kuyu_dibi"])
                self.assertIn("FKR", c["svg"])
                self.assertFalse(c.get("sorunlar"))

    def test_yer_yoksa_once_kucuk_yazi_sonra_uzak(self):
        """Kutunun yeri kademelidir:  normal boy yakında → küçük boy yakında → uzakta."""
        G, D = 1000.0, 1000.0
        duvar = [
            {"tip": "dikdortgen", "katman": "KUYU-DUVAR", "x": -150.0, "y": -150.0, "g": 1300.0, "d": 150.0},
            {"tip": "dikdortgen", "katman": "KUYU-DUVAR", "x": -150.0, "y": 1000.0, "g": 1300.0, "d": 150.0},
        ]
        nokta = [((500.0, 500.0), "FKR = 28,14 kN")]
        cagri = []
        asil = kuyu_dibi._yuk_yerlesimi

        def izle(*a, **k):
            cagri.append((k.get("boy"), k.get("uzak"), k.get("dis") is not None))
            if len(cagri) < 13:
                raise ValueError("yer yok")
            return asil(*a, **k)

        with unittest.mock.patch.object(kuyu_dibi, "_yuk_yerlesimi", izle):
            e = kuyu_dibi._yuk_etiketleri(duvar, nokta, G, D)
        self.assertEqual([c[:2] for c in cagri[:6]], [(kuyu_dibi.YUK_YAZI, False)] * 6)
        self.assertEqual([c[:2] for c in cagri[6:12]], [(kuyu_dibi.YUK_YAZI_KUCUK, False)] * 6)
        self.assertEqual(cagri[12], (kuyu_dibi.YUK_YAZI, True, True))
        self.assertTrue(any(x.get("ad") == "yuk_kutusu" for x in e))
        self.assertLess(kuyu_dibi.YUK_YAZI_KUCUK, kuyu_dibi.YUK_YAZI)
        self.assertGreater(kuyu_dibi.YUK_UZAK, 900.0)


if __name__ == "__main__":
    unittest.main()
