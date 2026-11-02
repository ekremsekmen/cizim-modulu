"""AYIRMA KİRİŞİNİN HESABI ( hesap/motor/uygulama/ayirma_kirisi.py — 2 Kas ).

·  model:  basit mesnetli kiriş, tekil yükler — moment ve sehim ders kitabının
   kapalı formülleriyle ( ortada tek yük:  F·L/4, F·L³/(48·E·I);  kenara yakın
   yük:  F·a·b/L ) karşılaştırılır
·  yükler:  ortaya bakan kabin rayının Fy'si, ortadaki karşı ağırlığın raylarının
   Fx'i — iki asansörün de;  sehim rayın kendi sehimine eklenir ( δstr )
·  rapor:  tek kuyuda iki asansörün raporunda karşı ağırlık raylarından sonra aynı
   bölüm, numaralar ardışık;  ayrı kuyuda yok;  küçük profil UYGUN DEĞİL —
   asansörün hükmü düşer, kiriş uygunluk işaretinde ( hesap_isareti )
"""

import unittest

from cizim import hesap_isareti
from motor.uygulama import ayirma_kirisi
from motor.uygulama import uygulama_hesabi
from testler.test_grup import ikili
from uclar import uygulama_istegi


def hesap(**ek):
    a, o = uygulama_istegi.asansor_girdileri(ikili(**ek))
    return uygulama_hesabi.hesapla_coklu(a, o)


def bolumu(s):
    return next((b for b in s["bolumler"] if b.get("kimlik") == ayirma_kirisi.KIMLIK), None)


class Formul(unittest.TestCase):
    def test_ortada_tek_yuk(self):
        L, F, EI = 2000.0, 1000.0, 210000.0 * 6.05e6
        self.assertAlmostEqual(ayirma_kirisi._moment(L, [(L / 2, F)], L / 2), F * L / 4)
        self.assertAlmostEqual(ayirma_kirisi._sehim(L, [(L / 2, F)], L / 2, EI), F * L**3 / (48 * EI))

    def test_kenara_yakin_yuk_ve_ust_uste_binme(self):
        L, EI = 3000.0, 1e12
        a, b = 800.0, 2200.0
        self.assertAlmostEqual(ayirma_kirisi._moment(L, [(a, 500.0)], a), 500.0 * a * b / L)
        #  Yükün kendi noktasındaki sehim:  F·a²·b² / ( 3·E·I·L )
        self.assertAlmostEqual(
            ayirma_kirisi._sehim(L, [(a, 500.0)], a, EI), 500.0 * a * a * b * b / (3 * EI * L)
        )
        #  Simetri:  x'teki sehim yük L−a'dayken L−x'teki sehime eşit
        self.assertAlmostEqual(
            ayirma_kirisi._sehim(L, [(a, 1.0)], 1700.0, EI),
            ayirma_kirisi._sehim(L, [(L - a, 1.0)], L - 1700.0, EI),
        )
        iki = ayirma_kirisi._sehim(L, [(a, 1.0), (2400.0, 2.0)], 1200.0, EI)
        self.assertAlmostEqual(
            iki,
            ayirma_kirisi._sehim(L, [(a, 1.0)], 1200.0, EI)
            + ayirma_kirisi._sehim(L, [(2400.0, 2.0)], 1200.0, EI),
        )


class Rapor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = hesap()
        cls.orta = hesap(Q1=1000, yer1="Sağ", Q2=630, yer2="Sol")

    def test_iki_asansorde_ayni_bolum_agirlik_raylarindan_sonra(self):
        b = [bolumu(x) for x in self.s["asansorler"]]
        self.assertTrue(all(b))
        self.assertEqual(b[0]["adimlar"], b[1]["adimlar"])
        for x in self.s["asansorler"]:
            kimlik = [y.get("kimlik") for y in x["bolumler"]]
            self.assertEqual(kimlik[kimlik.index("agirlik_raylari") + 1], ayirma_kirisi.KIMLIK)
            self.assertEqual([y["sira"] for y in x["bolumler"]], list(range(1, len(kimlik) + 1)))
            self.assertEqual(x["mukavemet_bolum_sayisi"], kimlik.index("kuyu_aydinlatma") - 1)

    def test_yukler_ortaya_bakan_raylar(self):
        #  Arkadaki ağırlıkta yalnız kabin rayları;  ağırlıklar ortadaysa onların rayları da
        for s, adet in ((self.s, 2), (self.orta, 6)):
            raylar = [r for x in s["asansorler"] for r in ayirma_kirisi.yukler(x)[1]]
            self.assertEqual(len(raylar), adet)
            for x in s["asansorler"]:
                kv = x["ara"]
                self.assertIn(ayirma_kirisi.yukler(x)[0], {x["girdi"]["kuyu_derinligi"]})
                self.assertTrue(kv)

    def test_kucuk_profil_uygun_degil_hukum_ve_isaret(self):
        s = hesap(kiris=30)
        for x in s["asansorler"]:
            b = bolumu(x)
            self.assertIs(b["sonuc"]["uygun"], False)
            self.assertIn("NPU profilini büyütün", b["sonuc"]["metin"])
            self.assertEqual(x["ozet"]["genel_sonuc_kisa"], "UYGUN DEĞİL")
            isaret = [u for u in hesap_isareti.uygun_olmayanlar(x) if u["kimlik"] == ayirma_kirisi.KIMLIK]
            self.assertEqual(
                [(u["ad"], u["parcalar"]) for u in isaret], [("Ayırma kirişi", ["Ayırma kirişi"])]
            )
        self.assertIs(bolumu(self.s["asansorler"][0])["sonuc"]["uygun"], True)

    def test_ayri_kuyuda_ya_da_kirissiz_yok(self):
        for s in (hesap(duzen="Ayrı"), hesap(kiris=None)):
            self.assertFalse([x for x in s["asansorler"] if bolumu(x)])


if __name__ == "__main__":
    unittest.main()
