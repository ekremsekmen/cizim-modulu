"""4. ADIMIN KARARLARI ( sözlük sayfası, k01 – k12 ) — uygulananların testi.

k02  makaralı KABİN pateni seçilince çizim durur ( ölçüleri gelene kadar );
     karşı ağırlığınki çizilir ( referans projede makaralı )
k06  çift sarımda çizim durur ( bugünkü gibi — test_kopru de sınar )
k11  karşı ağırlık dolgusunun çerçeveye sığması denetlenir
k12  çizimin bütün ürün ölçüleri tek katalogda:  hesabın Sabitler sekmesi"""

import os
import sys
import unittest
from collections import Counter

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_yol = os.path.join(KOK, "hesap")
if _yol not in sys.path:
    sys.path.append(_yol)

from cizim import kopru as CK
from cizim import olculer as CO
from cizim import sabitler as CS
from engine.uygulama import girdi as UG
from engine.uygulama import hesap as UY
from engine.uygulama import mukavemet as MK
from engine.uygulama import sabitler as US

MD = {"mk_yok": False, "mk_uzunluk": 3000, "mk_genislik": 2500}


def _A(**ek):
    return UG.tamamla({**UG.varsayilanlar(), **ek})


def _bolum(s, kimlik):
    return next(b for b in s["bolumler"] if b["kimlik"] == kimlik)


class MakaraliPaten(unittest.TestCase):
    """k02:  çizim yalnız kaymalı patenin ölçüsünü bilir."""

    def test_cizim_durur(self):
        g, hata = CK.cizim_girdisi(_A(paten_tipi="Makaralı"))
        self.assertIsNone(g)
        self.assertTrue(any(h.startswith("Kabin paten tipi makaralı") for h in hata), hata)

    def test_bolum_11_hesap_eksik(self):
        #  Paten açıklıkları kaymalı patenin yüksekliğiyle ölçülürdü:  ölçülmez
        s = UY.hesapla({"paten_tipi": "Makaralı"})
        self.assertTrue(s["aktif"], s.get("hata"))
        b = _bolum(s, "siginma_alanlari")
        self.assertIn("makaralı", b["eksik_hesap"])
        #  Ray hesabı çizimden bağımsızdır:  makaralı patenin formülüyle sürer
        self.assertIsNone(_bolum(s, "kabin_raylari").get("eksik_hesap"))

    def test_karsi_agirlikta_cizilir(self):
        #  Referans projenin ağırlık patenleri makaralı:  çizimin ölçüleri ondan
        for ek in ({}, {"agirlik_paten_tipi": "Makaralı"}):
            with self.subTest(ek=ek):
                g, hata = CK.cizim_girdisi(_A(**ek))
                self.assertEqual(hata, [])


class CiftSarim(unittest.TestCase):
    """k06:  çizim halatı kasnaktan bir kez geçirir;  çift sarımda durur."""

    def test_cizim_durur(self):
        A = _A(kanal_sekli="Yarım Daire Kanal (Çift Sarım)", sarilma_acisi=None)
        g, _h = CK.cizim_girdisi(A)
        self.assertTrue(any("Çift sarımlı kanal" in h for h in CK.tutarlilik(g, A)))


class Dolgu(unittest.TestCase):
    """k11:  gereken dolgu yüksekliği çerçevede kalandan büyük olamaz."""

    def test_kalan_yukseklik_cizimden(self):
        S = CS.SABIT
        #  çerçeve paten arasından bir paten boyu kısa ( patenler dışında — 8 Eki )
        for ek, pay in (
            ({}, S["paten_yukseklik"] + S["agirlik_kiris"] + S["agirlik_kasnak_ust"] + 400 / 2),
            ({"aski_orani": 1, **MD}, S["paten_yukseklik"] + 2 * S["agirlik_kiris"]),
        ):
            with self.subTest(ek=ek):
                g, _h = CK.cizim_girdisi(_A(**ek))
                self.assertAlmostEqual(
                    CO.hesap_olculeri(g)["agirlik_dolgu_yuksekligi"], g["dusey"]["agirlik_paten_arasi"] - pay
                )

    def test_denetim(self):
        s = UY.hesapla({"beyan_yuku": 630})
        ara = s["ara"]
        gi = s["girdi"]
        Mcwt, Gx, Gy = gi["karsi_agirlik"], gi["agirlik_derinligi"], gi["agirlik_genisligi"]
        rho = US.VARSAYILAN["dolgu_yogunlugu_barit"]
        self.assertAlmostEqual(ara["agirlik_ray.dolgu_gereken"], Mcwt / (rho * Gx * Gy * 1e-9))
        self.assertLessEqual(ara["agirlik_ray.dolgu_gereken"], ara["agirlik_ray.dolgu_kalan"])
        self.assertTrue(_bolum(s, "agirlik_raylari")["sonuc"]["uygun"])

    def test_varsayilan_asansorde_sigar(self):
        #  Kullanıcı kararları:  barit derinliği 155 ( standart blok ), çerçeve
        #  3.300 — patenler çerçevenin dışında olduğundan paten arası 3.400 ( 8 Eki ).
        #  Formun varsayılanında kabin ağırlığı boştur ( tablodan 800 kg:  karşı
        #  ağırlık 1.200 kg — 24 blok × 120 = 2.880 ≤ 2.980 );  motorunki 700.
        for ek in ({"kabin_agirligi": None}, {}):
            with self.subTest(ek=ek):
                s = UY.hesapla(ek)
                gi = s["girdi"]
                self.assertEqual((gi["agirlik_derinligi"], gi["agirlik_paten_arasi"]), (155, 3400))
                self.assertLessEqual(
                    s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"]
                )
                self.assertTrue(_bolum(s, "agirlik_raylari")["sonuc"]["uygun"])

    def test_sigmayinca_uygun_degil(self):
        s = UY.hesapla({"beyan_yuku": 1600})
        b = _bolum(s, "agirlik_raylari")
        self.assertFalse(b["sonuc"]["uygun"])
        self.assertIn("dolgusu çerçeveye sığmıyor", b["sonuc"]["metin"])
        #  Çare projenin sayısıyla:  gereken paten arası ( kalan yükseklik onunla
        #  birebir büyür );  o değer girilince sığar
        ara = s["ara"]
        h = (
            s["girdi"]["agirlik_paten_arasi"]
            + ara["agirlik_ray.dolgu_gereken"]
            - ara["agirlik_ray.dolgu_kalan"]
        )
        h = -(-h // 10) * 10
        self.assertIn(f"paten arası en az {h:,.0f} mm".replace(",", "."), b["sonuc"]["metin"])
        s = UY.hesapla({"beyan_yuku": 1600, "agirlik_paten_arasi": h})
        self.assertLessEqual(s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"])
        #  Daha yoğun dolgu ( pik döküm ) sığar
        s = UY.hesapla({"beyan_yuku": 1600, "agirlik_malzemesi": "Pik Döküm"})
        self.assertLessEqual(s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"])

    def test_yogunluk_sabitlerden(self):
        a = UY.hesapla({"beyan_yuku": 630})["ara"]["agirlik_ray.dolgu_gereken"]
        b = UY.hesapla({"beyan_yuku": 630, "_ofis": {"dolgu_yogunlugu_barit": 5600}})["ara"]
        self.assertAlmostEqual(b["agirlik_ray.dolgu_gereken"], a / 2.0)

    def test_motor_dogrudan_denetlemez(self):
        #  Motor asıl programdır:  çizim yoksa kontrol de yok
        b = _bolum(MK.hesapla({"beyan_yuku": 1600}), "agirlik_raylari")
        self.assertFalse(any("Hd" in str(a.get("formul", "")) for a in b["adimlar"]))


class TekKatalog(unittest.TestCase):
    """k12:  çizimin her ürün ölçüsü hesabın Sabitler sekmesindedir."""

    def test_her_sabit_bir_bolumde(self):
        say = Counter(k for _b, _a, al in CS.BOLUMLER for k in al)
        self.assertEqual(set(say), set(CS.SABIT))
        self.assertEqual([k for k, n in say.items() if n > 1], [])
        self.assertLessEqual(CS.SIFIR_OLABILIR, set(CS.SABIT))

    def test_sabitler_sekmesinde(self):
        gruplar = [k for _b, _a, al in US.GRUPLAR for k in al]
        self.assertEqual(sorted(gruplar), sorted(set(gruplar)))
        self.assertEqual(set(gruplar), set(US.VARSAYILAN))
        for c, v in CS.SABIT.items():
            o = CS.ofis_adi(c)
            with self.subTest(sabit=c):
                self.assertEqual(US.VARSAYILAN[o], v)
                self.assertEqual(US.ARALIK[o], CS.aralik(c))
                self.assertIn(o, US.ETIKET)
                self.assertEqual(CK.OFIS_SABITLERI[o], c)
        self.assertEqual(CK.OFIS_SABITLERI["tavan_payi"], "tavan_kirisi")

    def test_sabitlerden_cizime(self):
        g, _h = CK.cizim_girdisi(_A(_ofis={"kasa_yan": 150, "bina_duvari": 0}))
        S = CS.sabitler(g["_cizim_sabitleri"])
        self.assertEqual(S["kasa_yan"], 150.0)
        self.assertEqual(S["bina_duvari"], 0.0)

    def test_aralik_disi_gecmez_hesap_durur(self):
        #  Hesabın reddettiği değer çizime de geçmez ( ray boyu sıfır olamaz )
        for ofis in ({"ray_boyu": 0}, {"paten_yukseklik": 1500}, {"kasa_yan": -5}):
            with self.subTest(ofis=ofis):
                self.assertEqual(CK.cizim_sabitleri({"_ofis": ofis}), {})
                s = UY.hesapla({"_ofis": ofis})
                self.assertFalse(s["aktif"])
                self.assertTrue(any("Ofis standardı" in h for h in s["hata"]), s["hata"])

    def test_avan_motoruna_gecmez(self):
        d = UG._avan_sabitleri({"kasa_yan": 150, "U": 400})
        self.assertNotIn("kasa_yan", d)
        self.assertEqual(d["U"], 400)


if __name__ == "__main__":
    unittest.main()
