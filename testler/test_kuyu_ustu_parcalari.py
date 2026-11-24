"""KORKULUĞUN ÇEVRESİNDEKİ TAVAN PARÇALARI ( 23–24 Kas ) — TS EN 81-20 m.5.2.5.7.2 c · Şekil 5 ve
m.5.4.7.4 d;  revizyon kutusu m.5.4.8 a.

Gerekçe ( cikti/arastirma/KUYU_USTU.md ):
  · Şekil 5'in 0,40 m'si izdüşümün İÇİNDE, küpeştenin kabin tarafındadır:  orada küpeştenin tepesiyle
    tavan parçası arası düşey en az 0,30 m;
  · küpeştenin öbür yanındaki parçaya 0,10 m açıklık yeter — parça küpeştenin tepesinden alçaktaysa
    yatay ( m.5.4.7.4 d ).  Eskiden korkuluğun 0,40 m DIŞINA dek düşey açıklık aranıyordu;
    izdüşüme birkaç mm değen ama küpeştenin dışında kalan parça da 0,30 istiyordu;
  · revizyon kutusu korkulukların içindedir:  küpeştenin dışındaki tavan parçası ona ölçülmez.
Kural yalnız gevşetir:  eskiden kurulan her düzen yine kurulur.
Regülatör ve gergi yerinde kalır:  halat seçilen kabin rayının ekseninde iner, gergi tam altındadır
( LiftDesigner 4815-6'nın kuyu üstü ve kuyu dibi planlarında da ikisi aynı düşeyde ).  24 Kas:
regülatörü duvara kaydırmak gergiyi raydan koparıyordu, yapılmadı.  Gövdenin kabine girişi kasnak
çapının ailesinden ( parcalar.regulator_ailesi ):  standart düzende Ø300 ( varsayılan, R6 ) 36 mm,
Ø240 / Ø200 ( R5 ) 5 mm."""

import copy
import unittest

from cizim import dusey
from cizim import kuyu_dibi
from cizim import kuyu_ustu
from cizim import sorunlu
from temel import kutu_merkezi
from testler import altin_cizim
from testler import gercek_projeler
from testler.test_yerlesim_saglamligi import duzen_girdisi, standart_istek
from uclar import uygulama_istegi


def _standart(Q, yer="Sağ", mrl=True, **ek):
    """Standart düzen:  kuyu kabinden 950 geniş;  kabin 2.100, kapı 2.000, 1 m/s."""
    return standart_istek(Q, mrl, yer, kabin_ic_yuksekligi=2100, kapi_yuksekligi=2000, beyan_hizi=1.0, **ek)


def _gercek(ad, **ek):
    a = dict(gercek_projeler.PROJELER[ad], **ek)
    pg = {k: a.pop(k) for k in list(a) if k in uygulama_istegi.PROJE_GENELI_ALANLAR}
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def _g(v):
    g, _A, hata = duzen_girdisi(copy.deepcopy(v))
    assert g is not None, hata
    return g


def _dusey(v):
    with sorunlu.kip():
        return dusey.yerlesim(_g(v))


def _ust_kirilan(d):
    """Kuyu üstünün sağlanmayan açıklıkları:  { ad:  ( değer, asgari, madde ) }."""
    return {k: x for k, x in d["ust_aciklik"].items() if x[0] < x[1] - 1e-9}


class RegulatorYerinde(unittest.TestCase):
    def test_gergi_regulatorun_tam_altinda(self):
        #  Halat düşey iner:  gergi kasnağı regülatör halatının tam altında ( LiftDesigner 4815-6:
        #  regülatör kasnağı duvardan ~125, gergi ~138 mm — ikisi de ray ekseninde )
        for v in (_standart(630, "Sağ"), _standart(1000, "Sol"), _gercek("4815-6"), _gercek("1250 KG")):
            g = _g(v)
            Y, KD = kuyu_ustu.yerlesim(g), kuyu_dibi.yerlesim(g)
            with self.subTest(kuyu=g["kuyu"]["genislik"]):
                self.assertAlmostEqual(kutu_merkezi(KD["gergi"])[0], Y["rgx"], places=6)


class KorkulukKurali(unittest.TestCase):
    def test_standart_duzende_en_az_son_kat(self):
        #  Ø300 ( varsayılan, R6 ):  regülatörün gövdesi küpeşteyi 21 mm geçer — içeride, 0,30 m
        #  ( revizyon kutusuna da 0,50 ):  4.065.  Ø240 ( R5 ):  gövde izdüşüme 5 mm girer ama
        #  küpeştenin dışında;  bağlayan dışarıdaki kabin halat bağlantısı ( 645 mm sarkar ),
        #  küpeştenin tepesinden 0,10 m:  3.880.  Eskiden ikisi de 4.080.
        for Q in (630, 1000):
            for cap, sinir, asgari in ((300, 4065, 300.0), (240, 3880, 100.0)):
                with self.subTest(Q=Q, kasnak=cap):
                    v = _standart(Q, son_kat_yuksekligi=sinir, reg_kasnak_capi=cap)
                    self.assertEqual(_ust_kirilan(_dusey(v)), {})
                    v = _standart(Q, son_kat_yuksekligi=sinir - 20, reg_kasnak_capi=cap)
                    kirilan = _ust_kirilan(_dusey(v))
                    self.assertIn("korkuluk", kirilan)
                    self.assertEqual(kirilan["korkuluk"][1], asgari)

    def test_korkuluk_yanindaki_parca_yatay_olculur(self):
        #  1250 KG:  makine şasesi korkuluğun 175 mm yanında, tepesinden alçakta — m.5.4.7.4 d
        #  ( yatay ≥ 0,10 ) sağlanır;  eskiden düşey −348 < 100 ret sebebiydi
        d = _dusey(_gercek("1250 KG"))
        self.assertEqual(d["ust_engel"]["korkuluk"][1], "kuyu tavanı")

    def test_arkadaki_agirlikta_parca_kabinin_ustunde_0_30(self):
        #  Arkadaki ağırlıkta halat kabin üstü kasnağa iner:  makine şasesi kabinin üstünde,
        #  korkuluğun 0,40 m içinde — 0,30 m aranır ( program haklı:  K106 · K408 · 12495-18 ).
        #  Ø240:  regülatör küpeştenin dışında, en yakın parça şase ( Ø300'de regülatör içeride,
        #  ona da 0,30 )
        v = copy.deepcopy(altin_cizim.duzenler()["1275 Arka 2:1 MRL"])
        v["asansorler"][0]["reg_kasnak_capi"] = 240
        d = _dusey(v)
        self.assertEqual(d["ust_aciklik"]["korkuluk"][1], 300.0)
        self.assertEqual(d["ust_engel"]["korkuluk"][1], "sase")

    def test_revizyon_kutusu_korkuluklarin_icinde(self):
        #  Kutu korkulukların içinde ( m.5.4.8 a ):  küpeştenin dışındaki tavan parçası ona ölçülmez.
        #  Ø240:  regülatörün gövdesi izdüşüme 5 mm girer ( x 460 – 465 ), küpeşte x 475 — eskiden
        #  revizyon kutusu ona ölçülüyordu
        d = _dusey(_standart(630, reg_kasnak_capi=240))
        ic = dusey.korkuluklarin_ici(d["KU"])
        t = d["KU"]["tavan"]
        self.assertTrue(t[0] <= ic[0] < ic[2] <= t[2] and t[1] <= ic[1] < ic[3] <= t[3])
        self.assertEqual(d["ust_engel"]["revizyon"][1], "kuyu tavanı")


if __name__ == "__main__":
    unittest.main()
