"""YERLEŞİMİN ÖLÇÜ LİSTESİ ( cizim/olculer.py ) — hesabın çizimden aldığı geometri.

Program hesabı kabin merkezini, eşiği, ray ve halat boylarını, kasnak
sayılarını ve makinenin kirişteki yerini artık kendi tahmin etmez:  çizimin
girdilerden kurduğu yerleşimden okur.  Bu testler ölçülerin tanımlarını,
hesaba girdiklerini ( raporda ÇİZİMDEN ) ve çizim kurulamayınca hesabın
kendi yaklaşığına döndüğünü sınar."""

import math
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import kopru
from cizim import makine_dairesi
from cizim import olculer
from cizim import sabitler
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from motor.uygulama import mukavemet

MD = {"mk_yok": False, "mk_uzunluk": 4000, "mk_genislik": 3000}


def _girdi(**ek):
    return uygulama_girdisi.tamamla({**uygulama_girdisi.varsayilanlar(), **ek})


def _olc(**ek):
    return uygulama_girdisi.yerlesim_olculeri(_girdi(**ek))


def _adimlar(s, bolum_no):
    b = next(b for b in s["bolumler"] if b["baslik"].startswith(f"{bolum_no} "))
    return {a.get("sembol"): a for a in b["adimlar"] if a.get("sembol")}


class Plan(unittest.TestCase):
    def test_kabin_merkezi_ve_esik_tanimi(self):
        #  Kabin merkezi:  ön yüz + derinlik / 2;  eşik kuvveti eşiğin ortasında
        #  ( m.5.7.2.3.6 ).  İkisi de kabin ray eksenine göre.
        gc, _h = kopru.cizim_girdisi(_girdi())
        S = sabitler.sabitler(gc.get("_cizim_sabitleri"))
        o = olculer.plan_olculeri(gc, S)
        kb, ray_y = gc["kabin"], gc["kabin_ray"]["kapi_arasi"]
        self.assertAlmostEqual(o["kabin_merkezi_x"], kb["on_pay"] + kb["derinlik"] / 2 - ray_y)
        self.assertAlmostEqual(
            o["kabin_merkezi_x"] - o["esik_x"], (kb["derinlik"] + S["kabin_esik_derinlik"]) / 2
        )
        #  Eşik kabin ray ekseninin önünde
        self.assertLess(o["esik_x"], 0)


class Kasnaklar(unittest.TestCase):
    def test_askiya_gore(self):
        bir = {"aski": {"duzen": "Doğrudan"}}
        iki = {"aski": {"duzen": "2:1"}}
        self.assertEqual(olculer.kasnak_sayilari(bir, None)["kasnak_tek_yon"], 0)
        self.assertEqual(olculer.kasnak_sayilari(bir, {"D": 400})["kasnak_tek_yon"], 1)
        self.assertEqual(olculer.kasnak_sayilari(bir, {"D": 400})["saptirma_agirlik_capi"], 400.0)
        k = olculer.kasnak_sayilari(iki, None)
        self.assertEqual(
            (
                k["kasnak_tek_yon"],
                k["kasnak_kabin_adedi"],
                k["kasnak_agirlik_adedi"],
                k["kasnak_ters_yon"],
                k["saptirma_agirlik_capi"],
            ),
            (2, 2, 1, 0, 0.0),
        )
        #  2:1 + saptırma:  ağırlık tarafında iki kasnak — en olumsuz kesit yine 2
        self.assertEqual(olculer.kasnak_sayilari(iki, {"D": 400})["kasnak_tek_yon"], 2)

    def test_makine_dairesinde_bir_bir_saptirmali(self):
        o = _olc(**MD, aski_orani=1)
        self.assertEqual(o["kasnak_tek_yon"], 1)
        self.assertGreater(o["saptirma_agirlik_capi"], 0)

    def test_halat_yolu_kurulamazsa_kasnak_ve_aci_yok(self):
        #  Tahrik kasnağı halat aralığından küçük:  ağırlık halatı içeride inmeli,
        #  saptırma kasnağıyla çözülmez.  Saptırma "yok" değil — bilinmiyor.
        g = _girdi(**MD, tahrik_kasnak_capi=320, halat_capi=8)
        gc, _h = kopru.cizim_girdisi(g)
        self.assertIsNone(kopru.sarim_acisi(gc))
        o = uygulama_girdisi.yerlesim_olculeri(g)
        for k in ("kasnak_tek_yon", "saptirma_agirlik_capi"):
            self.assertNotIn(k, o)


class Boylar(unittest.TestCase):
    def test_ray_ve_halat_boylari_kuyuya_uyar(self):
        g = _girdi()
        o = uygulama_girdisi.yerlesim_olculeri(g)
        seyir = g["seyir_mesafesi"]
        kuyu = g["kuyu_boyu"] / 1000.0
        for k in ("kabin_ray_boyu", "agirlik_ray_boyu"):
            self.assertTrue(seyir < o[k] <= kuyu, (k, o[k], seyir, kuyu))
        #  2:1:  kabin en alt durakta halat tepeden kabine iner, geri çıkar
        self.assertGreater(o["aski_halat_boyu"], 2 * seyir)
        #  Regülatör halatı:  iki kol + iki yarım sarım
        self.assertGreater(o["reg_halat_boyu"], 2 * seyir)

    def test_bir_bir_halat_kabin_baglantisinda_biter(self):
        o1, o2 = _olc(**MD, aski_orani=1), _olc(**MD, aski_orani=2)
        self.assertLess(o1["aski_halat_boyu"], o2["aski_halat_boyu"])


class MakineYuku(unittest.TestCase):
    def test_makine_dairesinde_kaidenin_acikligi(self):
        #  Kaide halatlara ortalı ve makineyi sarar:  L dikine kirişlerin
        #  eksenleri arası;  dişlisiz 2:1'de kasnak açıklığın ortasında.
        g = _girdi(**MD)
        gc, _h = kopru.cizim_girdisi(g)
        Y = makine_dairesi.yerlesim(gc)
        o = uygulama_girdisi.yerlesim_olculeri(g)
        self.assertAlmostEqual(o["yan_yatak_boyu"], Y["kaide"]["L"])
        self.assertTrue(Y["kaide"]["ortali"])
        self.assertAlmostEqual(o["makine_yuku_x"], o["yan_yatak_boyu"] / 2.0)
        #  Girilen 1.400 kullanılmaz ( formda yok, çizimden )
        self.assertNotEqual(o["yan_yatak_boyu"], 1400)

    def test_raylara_oturan_kiris_acikligi_dbgw(self):
        gc, _h = kopru.cizim_girdisi(_girdi())
        o = _olc()
        self.assertAlmostEqual(o["yan_yatak_boyu"], gc["agirlik"]["ray_arasi"])
        self.assertTrue(0 < o["makine_yuku_x"] < o["yan_yatak_boyu"])

    def test_bina_yapisina_oturan_kiris_cizilmiyor(self):
        #  Karar 3:  duvardan duvara kiriş henüz çizilmiyor — açıklık yok,
        #  bölüm 2 HESAP EKSİK ( 1.400 sessizce kullanılmaz )
        o = _olc(makine_raya_biniyor="Bina yapısına")
        self.assertIsNone(o["yan_yatak_boyu"])
        self.assertNotIn("makine_yuku_x", o)
        s = uygulama_hesabi.hesapla({"makine_raya_biniyor": "Bina yapısına"})
        b2 = next(b for b in s["bolumler"] if b["baslik"].startswith("2 "))
        self.assertIn("HESAP EKSİK", b2.get("eksik_hesap") or "")
        self.assertIn("karar 3", b2["eksik_hesap"])


class Hesapta(unittest.TestCase):
    """Program hesabı ölçüleri kullanır ve raporda kaynağını yazar;  motor
    doğrudan çağrılınca ( hesap programının referans testleri ) eski
    yaklaşığıyla kalır."""

    @classmethod
    def setUpClass(cls):
        cls.s = uygulama_hesabi.hesapla({})
        cls.o = uygulama_girdisi.yerlesim_olculeri(_girdi())

    def test_kabin_raylari(self):
        a = _adimlar(self.s, 7)
        self.assertEqual(self.s["ara"]["kabin_ray.xc"], self.o["kabin_merkezi_x"])
        self.assertEqual(self.s["ara"]["kabin_ray.xi"], self.o["esik_x"])
        for k in ("xc", "xi"):
            self.assertTrue(a[k]["kaynak"].startswith(mukavemet.CIZIMDEN), (k, a[k]["kaynak"]))
        self.assertEqual(self.s["ozet"]["ray_boyu"], self.o["kabin_ray_boyu"])

    def test_aski_halati_ve_kasnaklar(self):
        self.assertEqual(self.s["ara"]["motor.lh"], self.o["aski_halat_boyu"])
        a = _adimlar(self.s, 4)
        self.assertTrue(a["Nps"]["kaynak"].startswith(mukavemet.CIZIMDEN), a["Nps"]["kaynak"])

    def test_motor_dogrudan_eski_yaklasikla(self):
        #  Hesap programının kendi motoru:  ölçü yok, kaynak ÇİZİMDEN yazmaz
        m = mukavemet.hesapla({})
        a = _adimlar(m, 7)
        self.assertFalse(a["xc"]["kaynak"].startswith(mukavemet.CIZIMDEN), a["xc"]["kaynak"])
        self.assertNotEqual(m["ara"]["kabin_ray.xc"], self.s["ara"]["kabin_ray.xc"])

    def test_girilen_aci_cizimden_yazmaz(self):
        #  Varsayılanın kaynak işareti girilen değere taşınmaz
        s = uygulama_hesabi.hesapla({"sarilma_acisi": 170})
        self.assertNotIn("sarilma_acisi", s["girdi"].get("_cizimden") or {})
        self.assertIn("sarilma_acisi", _girdi().get("_cizimden") or {})

    def test_makine_dairesi_x_ve_saptirma_ataleti(self):
        s = uygulama_hesabi.hesapla({**MD, "aski_orani": 1})
        o = _olc(**MD, aski_orani=1)
        self.assertEqual(s["ara"]["makine.X"], o["makine_yuku_x"])
        #  Sabit saptırma kasnağı:  halat hızı r·v → mDP = J / R² · r²  ( m.5.11.2.2 )
        self.assertTrue(math.isfinite(s["ara"]["tahrik.fren_alt.T2"]))


if __name__ == "__main__":
    unittest.main()
