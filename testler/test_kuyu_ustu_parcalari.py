"""KUYU TEPESİNDEKİ PARÇALAR VE KORKULUK ( 23 Kas ) — makine dairesizde regülatör ve kabin halat
bağlantısı kabinin izdüşümünün dışında durur;  korkuluğun çevresindeki tavan parçaları TS EN 81-20
Şekil 5'e ve m.5.4.7.4 d'ye göre ölçülür.

Gerekçe ( cikti/arastirma/KUYU_USTU.md ):  standart yan ağırlıklı makine dairesiz düzen ( kabin
2.100, 1 m/s ) 4.080 mm son kat istiyordu;  üreticiler 3.300 – 3.430 ile kuruyor.  Sebep:
  · regülatörün gövdesi ray ekseninden kabine 152 mm uzanıyor, kabinin izdüşümüne 36 – 41 mm
    giriyordu;  halat bağlantısının plakası 8 – 40 mm.  LiftDesigner 4815-6 ( T-T planı ),
    Kleemann'ın sahadaki projesi ve kullanıcının sahadan iki fotoğrafı:  ikisi de kabinin dışında,
    regülatörün mekanizması kabine bakar ( m.5.6.2.2.1.4 c 2:  kabin tavanından muayene );
  · korkuluğun 0,40 m DIŞINA dek düşey açıklık aranıyordu.  Şekil 5'in 0,40 m'si izdüşümün
    İÇİNDE, küpeştenin kabin tarafındadır;  korkuluğun yanındaki parçaya yatay 0,10 m yeter.
Değişmezler:  arkadaki ağırlıkta ( halat kabin üstü kasnağa iner ) parçalar kabinin üstündedir ve
0,30 m aranır;  makine dairesinde regülatör odadadır, kaymaz;  gergi regülatörün tam altındadır."""

import copy
import unittest

from cizim import dusey
from cizim import kuyu_dibi
from cizim import kuyu_ustu
from cizim import sorunlu
from temel import kutu_merkezi, ortusur
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


class ParcalarKabininDisinda(unittest.TestCase):
    def test_yandaki_agirlikta_regulator_ve_baglanti_kabinin_ustune_tasmaz(self):
        for Q in (630, 1000):
            for yer in ("Sağ", "Sol"):
                g = _g(_standart(Q, yer))
                Y = kuyu_ustu.yerlesim(g)
                kabin, G = Y["kabin"], g["kuyu"]["genislik"]
                with self.subTest(Q=Q, agirlik=yer):
                    for ad in ("reg_govde", "kabin_baglanti"):
                        self.assertFalse(ortusur(Y[ad], kabin), (ad, Y[ad], kabin))
                    #  Regülatör kuyunun içinde ( duvara en çok dayanır )
                    self.assertGreaterEqual(Y["reg_govde"][0], -1e-6)
                    self.assertLessEqual(Y["reg_govde"][2], G + 1e-6)
                    #  Kenardan en az TAVAN_PARCASI_PAYI ( yer varsa ):  standart kuyuda var
                    pay = kuyu_dibi.TAVAN_PARCASI_PAYI
                    uzak = min(abs(Y["reg_govde"][2] - kabin[0]), abs(Y["reg_govde"][0] - kabin[2]))
                    self.assertGreaterEqual(uzak + 1e-6, pay)

    def test_gergi_regulatorun_tam_altinda(self):
        #  Halat düşey iner:  regülatör kaydıysa gergi kasnağı da aynı kadar kayar
        for v in (_standart(630, "Sağ"), _standart(1000, "Sol"), _gercek("4815-6"), _gercek("1250 KG")):
            g = _g(v)
            Y, KD = kuyu_ustu.yerlesim(g), kuyu_dibi.yerlesim(g)
            with self.subTest(kuyu=g["kuyu"]["genislik"]):
                self.assertAlmostEqual(kutu_merkezi(KD["gergi"])[0], Y["rgx"], places=6)

    def test_dar_kuyuda_regulator_duvara_dayanir(self):
        #  LD 4815-6:  kabinle sağ duvar arası 245 mm, regülatörün gövdesi 238:  ray ekseninden 48 mm
        #  duvara kayar, gövde duvara dayanır, kabinin dışında kalır ( LD'de de dışında )
        g = _g(_gercek("4815-6"))
        Y = kuyu_ustu.yerlesim(g)
        self.assertAlmostEqual(Y["reg_govde"][2], g["kuyu"]["genislik"], places=6)
        self.assertFalse(ortusur(Y["reg_govde"], Y["kabin"]))

    def test_makine_dairesinde_regulator_kaymaz(self):
        #  Regülatör makine dairesinde:  gergi kabin rayının ekseninde kalır
        g = _g(_standart(1000, "Sağ", mrl=False))
        KD = kuyu_dibi.yerlesim(g)
        kabin = KD["kabin"] if "kabin" in KD else None
        self.assertEqual(kuyu_dibi.regulator_kaymasi(g, kabin or (0, 0, 0, 0), 0.0), 0.0)
        raylar = sorted(KD["kabin_raylari"], key=lambda r: r[0])
        ray = raylar[-1] if g["kuyu_dibi"]["regulator_yan"] == "Sağ" else raylar[0]
        self.assertAlmostEqual(kutu_merkezi(KD["gergi"])[0], kutu_merkezi(ray)[0], places=6)


class KorkulukKurali(unittest.TestCase):
    def test_standart_duzende_en_az_son_kat(self):
        #  Eskiden 4.080:  bağlantı ve regülatör izdüşüme giriyordu ( 0,50 + 0,30 ).  Şimdi bağlantı
        #  dışarıda, küpeştenin tepesinden 0,10 m yukarıda kalmalı ( 645 mm sarkar ):  3.875
        for Q in (630, 1000):
            with self.subTest(Q=Q):
                self.assertEqual(_ust_kirilan(_dusey(_standart(Q, son_kat_yuksekligi=3880))), {})
                kirilan = _ust_kirilan(_dusey(_standart(Q, son_kat_yuksekligi=3860)))
                self.assertIn("korkuluk", kirilan)
                self.assertEqual(kirilan["korkuluk"][1], 100.0)  # dışarıdaki parça:  0,10 m

    def test_korkuluk_yanindaki_parca_yatay_olculur(self):
        #  1250 KG:  makine şasesi korkuluğun 175 mm yanında, tepesinden alçakta — m.5.4.7.4 d
        #  ( yatay ≥ 0,10 ) sağlanır;  eskiden düşey −348 < 100 ret sebebiydi
        d = _dusey(_gercek("1250 KG"))
        self.assertEqual(d["ust_engel"]["korkuluk"][1], "kuyu tavanı")

    def test_arkadaki_agirlikta_parca_kabinin_ustunde_0_30(self):
        #  Arkadaki ağırlıkta halat kabin üstü kasnağa iner:  makine şasesi kabinin üstünde,
        #  korkuluğun 0,40 m içinde — 0,30 m aranır ( program haklı:  K106 · K408 · 12495-18 )
        d = _dusey(altin_cizim.duzenler()["1275 Arka 2:1 MRL"])
        self.assertEqual(d["ust_aciklik"]["korkuluk"][1], 300.0)
        self.assertEqual(d["ust_engel"]["korkuluk"][1], "sase")

    def test_revizyon_kutusu_korkuluklarin_icinde(self):
        #  Kutu korkulukların içinde ( m.5.4.8 a ):  küpeştenin dışındaki tavan parçası ona ölçülmez
        d = _dusey(_standart(630))
        ic = dusey.korkuluklarin_ici(d["KU"])
        t = d["KU"]["tavan"]
        self.assertTrue(t[0] <= ic[0] < ic[2] <= t[2] and t[1] <= ic[1] < ic[3] <= t[3])
        self.assertEqual(d["ust_engel"]["revizyon"][1], "kuyu tavanı")


if __name__ == "__main__":
    unittest.main()
