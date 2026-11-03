"""KAT ADLARI VE GİRİŞ KATI ( cizim/katlar.durak_adlari — cikti/devir/KAT_ADLARI_PLANI.md, 2 Kas ).

·  kural:  giriş katı verilmişse o, yoksa kotu ±0,00'a en yakın durak;  ad giriş katından
   sayılır ( 0, altı −1, −2, üstü 1, 2 — LiftDesigner ve ofisin LD paftaları );  elle
   yazılan ad onun yerine geçer, boş parça kuraldan
·  ofisin 12 LD paftasının "0" katı kuraldan bulunur ( KOTLAR.md § 2.1 )
·  yanlış girdi:  fazla ad, aynı ad, uzun ad, aralık dışı giriş — pafta durur ( kesitin
   sorunu ), ekran kuraldan adlarla çizer;  hesap DURMAZ ( adlar yalnız yazı — 2 Kas
   tarayıcıda:  köprü durunca hesabın 4 bölümü "HESAP EKSİK" oluyordu )
·  köprü:  g["dusey"]["durak_adlari"] · ["giris_duragi"] ( 1'den );  tek kuyuda iki asansörde aynı ( kuyunun
   ortak girdisi );  hesaba girmez
·  çizim:  kesitlerde durağın adı ( eskiden "1. DURAK" );  giriş görünüşü ve kapı kesiti giriş
   katının kotunu yazar ( geometri aynı );  veri tablosunda "Giriş katı" satırı
"""

import copy
import unittest

from cizim import geometri, giris, kapi_kesiti, katlar, kuyu_kesiti, pafta, veri_tablosu
from motor.uygulama import uygulama_hesabi
from tasarim import alanlar
from testler.test_grup import ikili
from testler.test_proje_hukmu import ORNEK
from uclar import cizim_uclari, uygulama_istegi

KOTLU = dict(durak_kotlari="-3,00; ±0,00; +3,00; +6,00", kuyu_dibi_kotu="-4,75", kuyu_tavani_kotu="+10,25")


def cizim(**ek):
    v = {"asansorler": [dict(ORNEK, **ek)], "proje_geneli": {}, "sabitler": {}}
    a, o = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
    s = uygulama_hesabi.hesapla_coklu(a, o)
    ((g, h),) = cizim_uclari.girdiler(v, a, o, s, "DENEME")
    return g, h, s


class Kural(unittest.TestCase):
    def test_giristen_sayilir(self):
        self.assertEqual(
            katlar.durak_adlari(None, None, [-3000, 0, 3000, 6000]), (["-1", "0", "1", "2"], 1, [])
        )
        self.assertEqual(katlar.durak_adlari(None, None, [0, 3000, 6000]), (["0", "1", "2"], 0, []))
        self.assertEqual(katlar.durak_adlari(None, 1, [-3000, 0, 3000]), (["0", "1", "2"], 0, []))

    def test_ofisin_ld_paftalarinin_sifir_kati(self):
        #  ( en alt durak , LD'nin "0" katı ) — KOTLAR.md § 2.1;  kat arası 3.000 varsayıldı,
        #  yalnız en alt ile "0" katının kotu paftadan
        for alt, sifir in (
            (0, 0),
            (200, 200),
            (-2500, 500),
            (180, 180),
            (-3500, 0),
            (-2750, 250),
            (-7000, 0),
        ):
            with self.subTest(alt=alt):
                kotlar = [alt] + ([sifir] if sifir != alt else []) + [sifir + 3000 * k for k in (1, 2)]
                adlar, g, _h = katlar.durak_adlari(None, None, kotlar)
                self.assertEqual(kotlar[g], sifir)
                self.assertEqual(adlar[g], "0")

    def test_elle_yazilan_ad_bos_parca_kuraldan(self):
        k = [-3000, 0, 3000, 6000]
        self.assertEqual(katlar.durak_adlari("OTOPARK; ZEMİN", None, k)[0], ["OTOPARK", "ZEMİN", "1", "2"])
        self.assertEqual(katlar.durak_adlari("; ; ; ÇATI", None, k)[0], ["-1", "0", "1", "ÇATI"])
        self.assertEqual(katlar.durak_adlari(["B2", None, "", "3"], None, k)[0], ["B2", "0", "1", "3"])

    def test_yanlis_girdi(self):
        k = [-3000, 0, 3000]
        for ham, sira, parca in (
            ("A; B; C; D", None, "3 durak var"),
            ("A; A", None, "aynı olamaz"),
            ("ÇOK UZUN BİR KAT ADI", None, "en çok 12"),
            (None, 4, "4. durak olamaz"),
            (None, 0, "0. durak olamaz"),
            ("; 1", None, "aynı olamaz"),  # elle "1" + kuraldan "1"
        ):
            with self.subTest(ham=ham, sira=sira):
                adlar, _g, hata = katlar.durak_adlari(ham, sira, k)
                self.assertTrue(any(parca in h for h in hata), hata)
                self.assertEqual(len(adlar), 3)


class Kopru(unittest.TestCase):
    def test_kotla_giris_ve_adlar(self):
        g, h, _s = cizim(**KOTLU)
        self.assertEqual(h, [])
        self.assertEqual((g["dusey"]["durak_adlari"], g["dusey"]["giris_duragi"]), (["-1", "0", "1", "2"], 2))
        g, _h, _s = cizim(**KOTLU, giris_duragi=3, durak_adlari="OTOPARK")
        self.assertEqual(
            (g["dusey"]["durak_adlari"], g["dusey"]["giris_duragi"]), (["OTOPARK", "-1", "0", "1"], 3)
        )

    def test_yanlis_ad_paftayi_durdurur_hesabi_degil(self):
        g, h, s = cizim(**KOTLU, durak_adlari="A; A")
        self.assertIsNone(g)
        self.assertEqual(h, ["Kat adları:  iki durağın adı aynı olamaz ( 'A' )."])
        self.assertEqual(h[0].cizim, "kuyu_kesiti_yan")
        #  Hesap adsız girdininkiyle aynı:  çizimden ölçtükleri eksik kalmadı
        _g, _h, s0 = cizim(**KOTLU)
        a, a0 = s["asansorler"][0], s0["asansorler"][0]
        self.assertEqual([b.get("sonuc") for b in a["bolumler"]], [b.get("sonuc") for b in a0["bolumler"]])
        #  Ekran ( sorunlu çizim ):  girdi kurulur, adlar kuraldan
        v = {"asansorler": [dict(ORNEK, **KOTLU, durak_adlari="A; A")], "proje_geneli": {}, "sabitler": {}}
        A, o = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
        ge, he = cizim_uclari.asansor_girdisi(A, o, uygulama_hesabi.hesapla_coklu(A, o), "DENEME", 0)
        self.assertEqual(he, h)
        self.assertEqual(ge["dusey"]["durak_adlari"], ["-1", "0", "1", "2"])

    def test_hesaba_girmez(self):
        _g, _h, s0 = cizim(**KOTLU)
        _g, _h, s1 = cizim(**KOTLU, giris_duragi=4, durak_adlari="B; Z; 1; ÇATI")
        a0, a1 = s0["asansorler"][0], s1["asansorler"][0]
        self.assertEqual([b.get("sonuc") for b in a0["bolumler"]], [b.get("sonuc") for b in a1["bolumler"]])
        self.assertEqual(a0["ara"], a1["ara"])

    def test_tek_kuyuda_ortak(self):
        self.assertIn(alanlar.DURAK_ADLARI, alanlar.KUYU_ORTAK)
        self.assertIn(alanlar.GIRIS_DURAGI, alanlar.KUYU_ORTAK)
        v = ikili()
        v["asansorler"][0].update(giris_duragi=2, durak_adlari="B")
        v["asansorler"][1].update(giris_duragi=1)
        a, _o = uygulama_istegi.asansor_girdileri(v)
        self.assertEqual([(x.get("giris_duragi"), x.get("durak_adlari")) for x in a], [(2, "B")] * 2)


def yazilar(e):
    return [el["metin"] for el in e if el["tip"] == "yazi"]


def yazisiz(e):
    return [{k: v for k, v in el.items() if k != "metin"} for el in e]


class Cizim(unittest.TestCase):
    def test_kesitler_durak_adini_yazar(self):
        g, _h, _s = cizim(**KOTLU, giris_duragi=3, durak_adlari="OTOPARK")
        for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
            with self.subTest(ciz=ciz.__name__):
                y = yazilar(ciz(g))
                for ad in ("OTOPARK", "-1", "0", "1"):
                    self.assertIn(ad, y)
                self.assertFalse([m for m in y if "DURAK" in m], y)

    def test_giris_ve_kapi_kesiti_giris_katinin_kotu(self):
        g0, _h, _s = cizim(**KOTLU)
        g3, _h, _s = cizim(**KOTLU, giris_duragi=3)
        for ciz in (giris.ciz, kapi_kesiti.ciz):
            with self.subTest(ciz=ciz.__module__):
                e0, e3 = ciz(g0), ciz(g3)
                self.assertIn("±0,00", yazilar(e0))
                self.assertIn("+3,00", yazilar(e3))
                self.assertNotIn("-3,00", yazilar(e0))
                #  kapı her katta aynı:  yalnız yazı değişir
                self.assertEqual(yazisiz(e0), yazisiz(e3))

    def test_veri_tablosunda_giris_kati(self):
        g, _h, _s = cizim(**KOTLU)
        self.assertIn(("Giriş katı", "0  ·  ±0,00"), veri_tablosu.satirlar(g))
        g, _h, _s = cizim(**KOTLU, giris_duragi=4, durak_adlari="; ; ; ÇATI")
        self.assertIn(("Giriş katı", "ÇATI  ·  +6,00"), veri_tablosu.satirlar(g))

    def test_kopru_disi_girdide_kuraldan(self):
        #  elle kurulmuş çizim girdisi ( adsız ) ya da köprüden sonra durak sayısı değişmiş
        g, _h, _s = cizim(**KOTLU)
        del g["dusey"]["durak_adlari"]
        self.assertEqual(katlar.adlar_ve_giris(g), (["-1", "0", "1", "2"], 1))
        g["dusey"]["durak_adlari"] = ["A", "B"]
        self.assertEqual(katlar.adlar_ve_giris(g), (["-1", "0", "1", "2"], 1))
        g["dusey"]["durak_adedi"] = 1
        self.assertEqual(katlar.adlar_ve_giris(g), ([], 0))
        self.assertEqual(katlar.giris_kotu(g), 0.0)


class KirikKesit(unittest.TestCase):
    """Kırık kesitte giriş katı kalır ( 2 Kas:  63444-2'nin A-A / B-B'sinde ara katlar
    kesilince "0" yoktu ):  kırığa düşerse iki kırık, arada giriş katı;  kırığı
    aşan zincirler kapanır."""

    def _kesitler(self, **ek):
        from testler.test_kotlar import KOT_63444, _kotla, _md_63444
        from testler.test_yerlesim_saglamligi import standart_istek

        v = _kotla(_md_63444(standart_istek(1000, False, "Sağ")), KOT_63444, **ek)
        a, o = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
        s = uygulama_hesabi.hesapla_coklu(a, o)
        ((g, h),) = cizim_uclari.girdiler(v, a, o, s, "DENEME")
        self.assertEqual(h, [])
        return {ad: e for ad, _b, _o, e in pafta.cizim_listesi(g) if ad.startswith("kuyu_kesiti")}

    def test_giris_kati_kirikta_kalir(self):
        for ek, beklenen, kirik in (
            ({}, "0", 1),
            ({"giris_duragi": "12"}, "0", 2),
            ({"giris_duragi": "1"}, "0", 1),
        ):
            for ad, e in self._kesitler(**ek).items():
                with self.subTest(ek=ek, cizim=ad):
                    adlar = {x["metin"] for x in e if x.get("ad") == "durak_adi"}
                    self.assertIn(beklenen, adlar)
                    self.assertLess(len(adlar), 21)  # kırık:  ara katlar düştü
                    self.assertEqual(sum(x.get("ad") == "kirik_cizgisi" for x in e), 10 * kirik)
                    for z in geometri.zincirler(e):
                        self.assertAlmostEqual(z["toplam"], z["son"] - z["bas"])


if __name__ == "__main__":
    unittest.main()
