"""HAREKETLİ PARÇALAR ( cizim/hareketli.py ) — denetimin ( 8–10 Eki ) bulduğu
yanlış "uygun"ların sınır testleri:  sınırın hemen altı, tam sınır, hemen üstü.

Beklenen sayılar girdilerden elle bulunur ( yorumlarda ), programın kendi
ara değerlerinden değil.  Girdiler programın yolundan:  hesap motoru →
köprü → düşey yerleşim."""

import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from temel import ortusur
from cizim import dusey
from cizim import hareketli
from cizim import kopru
from motor.uygulama import uygulama_hesabi

#  Denetimin kuyu dibi örneği:  1.275 kg, kabin 2.000 × 1.400, ağırlık sağda
DIP = {
    "beyan_yuku": 1275,
    "kabin_genisligi": 2000,
    "kabin_derinligi": 1400,
    "kapi_genisligi": 1100,
    "kuyu_genisligi": 2950,
    "kuyu_derinligi": 1850,
    "agirlik_yeri": "Sağ",
    "ray_kapi_arasi": 500,
    "kabin_tampon_adedi": 1,
    "kat_kapisi_tipi": "Teleskopik Sol",
    "mk_yok": True,
}
#  Denetimin karşı ağırlık örnekleri ( temel ölçüleri ortak )
TEMEL = {"temel_a": 26.55, "temel_b": 16.4, "sarilma_acisi": 180}
ODA = {
    "mk_yok": False,
    "mk_genislik": 2600,
    "mk_uzunluk": 3800,
    "kabin_genisligi": 1350,
    "kabin_derinligi": 1400,
    "kuyu_genisligi": 2300,
    "kuyu_derinligi": 1850,
}


def _yerlesim(girdi):
    s = uygulama_hesabi.hesapla(girdi)
    g, hata = kopru.cizim_girdisi(s["girdi"])
    assert g is not None, hata
    return dusey.yerlesim(g), g


class KuyuDibiSiginma(unittest.TestCase):
    def test_alt_kiris_sinirda(self):
        #  Kabin tam ezilmiş tamponunda:  döşeme −( çarpma arası 150 + ezilme 90 )
        #  = −240;  alt şase kirişinin altı döşemenin 320 − 50 − 100 / 2 = 220
        #  altında ( şase altı, alt paten payı, paten yarısı — ofisin kabini ):
        #  −460.  Kuyu dibi KY'de kirişin altı tabandan KY − 460;  çömelme
        #  yüksekliği 1.000:  KY 1.460'ta kiriş tam sınırda.
        #  KY < 1.460:  kiriş alana iner — alan kirişin dışına konur ( kabin
        #  tabanının altında, 1.110 değil KY − 290 );  KY ≥ 1.460:  alan kapıya en
        #  yakın yerde, kirişin altında, yüksekliği kirişe ölçülür.
        #  Eskiden ( denetim 9 Eki ) KY 1.400'de alan kirişin altındaydı, kiriş
        #  940'tayken sığınma 1.110 ( platformdan ) diye UYGUN çıkıyordu.
        for KY, ustunde, deger, engel in (
            (1400, False, 1110.0, hareketli.KABIN),
            (1459, False, 1169.0, hareketli.KABIN),
            (1460, True, 1000.0, hareketli.ALT_KIRIS),
            (1461, True, 1001.0, hareketli.ALT_KIRIS),
        ):
            Y, _g = _yerlesim({**DIP, "kuyu_dibi": KY})
            sg = Y["KD"]["siginma"]
            kiris = [p for p in Y["dip_parcalar"] if p[0] == hareketli.ALT_KIRIS]
            with self.subTest(KY=KY):
                self.assertEqual(Y["hata"], [])
                self.assertAlmostEqual(kiris[0][2] - Y["taban"], KY - 460.0)
                self.assertEqual(any(ortusur(p[1], sg) for p in kiris), ustunde)
                self.assertAlmostEqual(Y["dip_aciklik"]["siginma"][0], deger)
                self.assertEqual(Y["dip_engel"]["siginma"], engel)


class KarsiAgirlikTabani(unittest.TestCase):
    def test_alt_paten_tabana(self):
        #  Tamponu tam ezilmişken alt patenin altı tabandan:  kaide + tampon boyu
        #  100 − ezilme 90 − paten boyu 100 = kaide − 90.  Kaide 50'de 40 mm
        #  tabanın altında ( denetim 8 Eki:  çizim ve bölüm 11 UYGUN diyordu ).
        for kaide, carpar in ((50, True), (89, True), (90, False), (91, False)):
            Y, _g = _yerlesim(
                {
                    **TEMEL,
                    "agirlik_tampon_baba": kaide,
                    "agirlik_tampon_ezilme": 90,
                    "son_kat_yuksekligi": 5000,
                }
            )
            hata = [h for h in Y["hata"] if "kuyu tabanına çarpıyor" in h]
            with self.subTest(kaide=kaide):
                self.assertAlmostEqual(Y["agirlik_alt"]["alt_paten"] - Y["taban"], kaide - 90.0)
                self.assertEqual(bool(hata), carpar, Y["hata"])
                if carpar:
                    self.assertIn(f"tabanın {90 - kaide:g} mm altında", hata[0])
                    self.assertIn(hata[0], Y["diger"])  # bölüm 11'e de gider


class KarsiAgirlikTavani(unittest.TestCase):
    def test_makine_dairelide_kasnak_tavana(self):
        #  Makine daireli, ağırlık paten arası 4.300, kasnak ø 1.040.  En üst
        #  konumda ( kabin tam ezilmiş tamponunda + 0,035 v² ) çerçevenin altı:
        #  tampon üstü −1.600 + 300 + 100 = −1.200, + ağırlık çarpma arası 150
        #  + kabinin 150 + 90 + 35 = son kattan −775;  üstü −775 + 4.300 − 100
        #  ( paten çerçevenin dışında ) = 3.425;  kasnağın tepesi 3.425 − 110
        #  + 520 = 3.835.  Kuyu tavanının en alt kısmı son kat − 150 ( tavan
        #  kirişi payı ):  son kat 3.985'te tam sınırda.  Denetim ( 8 Eki ) son
        #  kat 3.825'te kasnağın tavana girdiğini bulmuştu;  yalnız rayın
        #  kılavuz payı ( 100 ) denetlendiği için UYGUN çıkıyordu.
        for son_kat, carpar in ((3825, True), (3984, True), (3985, False), (3986, False)):
            Y, _g = _yerlesim(
                {
                    **TEMEL,
                    **ODA,
                    "son_kat_yuksekligi": son_kat,
                    "agirlik_paten_arasi": 4300,
                    "agirlik_kasnak_capi": 1040,
                    "agirlik_genisligi": 1100,
                }
            )
            hata = [h for h in Y["hata"] if "tavana çarpıyor" in h]
            with self.subTest(son_kat=son_kat):
                self.assertEqual(bool(hata), carpar, Y["hata"])
                if carpar:
                    self.assertIn("karşı ağırlık kasnağı tepesi 3835 mm", hata[0])
                    self.assertIn(f"( kuyu tavanı ) {son_kat - 150:g} mm", hata[0])


class Tabliye(unittest.TestCase):
    def test_sifir_kabul_negatif_ret(self):
        #  Tabliye yüksekliği oda zemininden tabliyenin üstüne:  zemin tabliyeyle
        #  aynı hizadaysa 0 ( alanın açıklaması, donanim.makine_dairesi kabul
        #  ediyordu;  köprü "sıfırdan büyük olmalı" diye reddediyor, hesap
        #  "HESAP EKSİK" diyordu — denetim 8 Eki ).
        g0 = {**TEMEL, **ODA}
        s = uygulama_hesabi.hesapla({**g0, "tabliye_yuksekligi": 0})
        g, hata = kopru.cizim_girdisi(s["girdi"])
        self.assertEqual(hata, [])
        self.assertEqual(g["makine_dairesi"]["tabliye_yuksekligi"], 0.0)
        self.assertEqual(dusey.yerlesim(g)["hata"], [])
        self.assertFalse(s["ozet"].get("eksik_hesap"))
        s = uygulama_hesabi.hesapla({**g0, "tabliye_yuksekligi": -10})
        g, hata = kopru.cizim_girdisi(s["girdi"])
        self.assertIsNone(g)
        self.assertTrue(any("negatif olamaz" in h for h in hata), hata)


class TekTanim(unittest.TestCase):
    def test_parcalar_plan_ve_kotlarla_ayni(self):
        #  Parçanın plandaki yeri kuyu planının elemanı, kotları kabin_kotlari:
        #  kuyu dibi, kesit ve hesap aynı sayıyı görür.
        Y, _g = _yerlesim({**DIP, "kuyu_dibi": 1400})
        plan = {}
        for el in Y["KD"]["taban"]:
            if el.get("ad") in ("sase_kiris", "sase_dikme"):
                plan.setdefault(el["ad"], []).append((el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"]))
        dip = Y["dip"]
        for ad, plan_ad, alt, ust in (
            (hareketli.ALT_KIRIS, "sase_kiris", "alt_kiris_alt", "alt_kiris_ust"),
            (hareketli.UST_KIRIS, "sase_kiris", "ust_kiris_alt", "ust_kiris_ust"),
            (hareketli.DIKME, "sase_dikme", "alt_kiris_alt", "ust_kiris_ust"),
        ):
            p = [x for x in Y["dip_parcalar"] if x[0] == ad]
            with self.subTest(ad):
                self.assertEqual(sorted(x[1] for x in p), sorted(plan[plan_ad]))
                self.assertTrue(all((x[2], x[3]) == (dip[alt], dip[ust]) for x in p))


if __name__ == "__main__":
    unittest.main()
