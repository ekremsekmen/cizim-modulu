"""4. ADIMIN KARARLARI ( sözlük sayfası, k01 – k12 ) — uygulananların testi.

k02  makaralı KABİN pateni seçilince çizim durur ( ölçüleri gelene kadar );
     karşı ağırlığınki çizilir ( referans projede makaralı )
k06  çift sarımda çizim durur ( bugünkü gibi — test_kopru de sınar )
k11  karşı ağırlık dolgusunun çerçeveye sığması denetlenir
k12  çizimin bütün ürün ölçüleri tek katalogda:  hesabın Sabitler sekmesi"""

import os
import unittest
from collections import Counter

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import kopru
from cizim import olculer
from cizim import sabitler
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from motor.uygulama import mukavemet
from motor.uygulama import uygulama_sabitleri

MD = {"mk_yok": False, "mk_uzunluk": 3000, "mk_genislik": 2500}


def _A(**ek):
    return uygulama_girdisi.tamamla({**uygulama_girdisi.varsayilanlar(), **ek})


def _bolum(s, kimlik):
    return next(b for b in s["bolumler"] if b["kimlik"] == kimlik)


class MakaraliPaten(unittest.TestCase):
    """k02:  çizim yalnız kaymalı patenin ölçüsünü bilir."""

    def test_cizim_durur(self):
        g, hata = kopru.cizim_girdisi(_A(paten_tipi="Makaralı"))
        self.assertIsNone(g)
        self.assertTrue(any(h.startswith("Kabin paten tipi makaralı") for h in hata), hata)

    def test_bolum_11_hesap_eksik(self):
        #  Paten açıklıkları kaymalı patenin yüksekliğiyle ölçülürdü:  ölçülmez
        s = uygulama_hesabi.hesapla({"paten_tipi": "Makaralı"})
        self.assertTrue(s["aktif"], s.get("hata"))
        b = _bolum(s, "siginma_alanlari")
        self.assertIn("makaralı", b["eksik_hesap"])
        #  Ray hesabı çizimden bağımsızdır:  makaralı patenin formülüyle sürer
        self.assertIsNone(_bolum(s, "kabin_raylari").get("eksik_hesap"))

    def test_karsi_agirlikta_cizilir(self):
        #  Referans projenin ağırlık patenleri makaralı:  çizimin ölçüleri ondan
        for ek in ({}, {"agirlik_paten_tipi": "Makaralı"}):
            with self.subTest(ek=ek):
                g, hata = kopru.cizim_girdisi(_A(**ek))
                self.assertEqual(hata, [])


class CiftSarim(unittest.TestCase):
    """k06:  çizim halatı kasnaktan bir kez geçirir;  çift sarımda durur."""

    def test_cizim_durur(self):
        A = _A(kanal_sekli="Yarım Daire Kanal (Çift Sarım)", sarilma_acisi=None)
        g, _h = kopru.cizim_girdisi(A)
        self.assertTrue(any("Çift sarımlı kanal" in h for h in kopru.tutarlilik(g, A)))


class Dolgu(unittest.TestCase):
    """k11:  gereken dolgu yüksekliği çerçevede kalandan büyük olamaz."""

    def test_kalan_yukseklik_cizimden(self):
        S = sabitler.SABIT
        #  çerçeve paten arasından bir paten boyu kısa ( patenler dışında — 8 Eki )
        for ek, pay in (
            ({}, S["paten_yukseklik"] + S["agirlik_kiris"] + S["agirlik_kasnak_ust"] + 400 / 2),
            ({"aski_orani": 1, **MD}, S["paten_yukseklik"] + 2 * S["agirlik_kiris"]),
        ):
            with self.subTest(ek=ek):
                g, _h = kopru.cizim_girdisi(_A(**ek))
                self.assertAlmostEqual(
                    olculer.hesap_olculeri(g)["agirlik_dolgu_yuksekligi"],
                    g["dusey"]["agirlik_paten_arasi"] - pay,
                )

    def test_denetim(self):
        s = uygulama_hesabi.hesapla({"beyan_yuku": 630})
        ara = s["ara"]
        gi = s["girdi"]
        Mcwt, Gx, Gy = gi["karsi_agirlik"], gi["agirlik_derinligi"], gi["agirlik_genisligi"]
        rho = uygulama_sabitleri.VARSAYILAN["dolgu_yogunlugu_barit"]
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
                s = uygulama_hesabi.hesapla(ek)
                gi = s["girdi"]
                self.assertEqual((gi["agirlik_derinligi"], gi["agirlik_paten_arasi"]), (155, 3400))
                self.assertLessEqual(
                    s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"]
                )
                self.assertTrue(_bolum(s, "agirlik_raylari")["sonuc"]["uygun"])

    def test_sigmayinca_uygun_degil(self):
        s = uygulama_hesabi.hesapla({"beyan_yuku": 1600})
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
        s = uygulama_hesabi.hesapla({"beyan_yuku": 1600, "agirlik_paten_arasi": h})
        self.assertLessEqual(s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"])
        #  Daha yoğun dolgu ( pik döküm ) sığar
        s = uygulama_hesabi.hesapla({"beyan_yuku": 1600, "agirlik_malzemesi": "Pik Döküm"})
        self.assertLessEqual(s["ara"]["agirlik_ray.dolgu_gereken"], s["ara"]["agirlik_ray.dolgu_kalan"])

    def test_yogunluk_sabitlerden(self):
        a = uygulama_hesabi.hesapla({"beyan_yuku": 630})["ara"]["agirlik_ray.dolgu_gereken"]
        b = uygulama_hesabi.hesapla({"beyan_yuku": 630, "_ofis": {"dolgu_yogunlugu_barit": 5600}})["ara"]
        self.assertAlmostEqual(b["agirlik_ray.dolgu_gereken"], a / 2.0)

    def test_motor_dogrudan_denetlemez(self):
        #  Motor asıl programdır:  çizim yoksa kontrol de yok
        b = _bolum(mukavemet.hesapla({"beyan_yuku": 1600}), "agirlik_raylari")
        self.assertFalse(any("Hd" in str(a.get("formul", "")) for a in b["adimlar"]))


class TekKatalog(unittest.TestCase):
    """k12:  çizimin her ürün ölçüsü hesabın Sabitler sekmesindedir."""

    def test_her_sabit_bir_bolumde(self):
        say = Counter(k for _b, _a, al in sabitler.BOLUMLER for k in al)
        self.assertEqual(set(say), set(sabitler.SABIT))
        self.assertEqual([k for k, n in say.items() if n > 1], [])
        self.assertLessEqual(sabitler.SIFIR_OLABILIR, set(sabitler.SABIT))

    def test_sabitler_sekmesinde(self):
        gruplar = [k for _b, _a, al in uygulama_sabitleri.GRUPLAR for k in al]
        self.assertEqual(sorted(gruplar), sorted(set(gruplar)))
        self.assertEqual(set(gruplar), set(uygulama_sabitleri.VARSAYILAN))
        for c, v in sabitler.SABIT.items():
            o = sabitler.ofis_adi(c)
            with self.subTest(sabit=c):
                self.assertEqual(uygulama_sabitleri.VARSAYILAN[o], v)
                self.assertEqual(uygulama_sabitleri.ARALIK[o], sabitler.aralik(c))
                self.assertIn(o, uygulama_sabitleri.ETIKET)
                self.assertEqual(kopru.OFIS_SABITLERI[o], c)
        self.assertEqual(kopru.OFIS_SABITLERI["tavan_payi"], "tavan_kirisi")

    def test_sabitlerden_cizime(self):
        g, _h = kopru.cizim_girdisi(_A(_ofis={"kasa_yan": 150, "bina_duvari": 0}))
        S = sabitler.sabitler(g["_cizim_sabitleri"])
        self.assertEqual(S["kasa_yan"], 150.0)
        self.assertEqual(S["bina_duvari"], 0.0)

    def test_aralik_disi_gecmez_hesap_durur(self):
        #  Hesabın reddettiği değer çizime de geçmez ( ray boyu sıfır olamaz )
        for ofis in ({"ray_boyu": 0}, {"paten_yukseklik": 1500}, {"kasa_yan": -5}):
            with self.subTest(ofis=ofis):
                self.assertEqual(kopru.cizim_sabitleri({"_ofis": ofis}), {})
                s = uygulama_hesabi.hesapla({"_ofis": ofis})
                self.assertFalse(s["aktif"])
                self.assertTrue(any("Ofis standardı" in h for h in s["hata"]), s["hata"])

    def test_avan_motoruna_gecmez(self):
        d = uygulama_girdisi._avan_sabitleri({"kasa_yan": 150, "U": 400})
        self.assertNotIn("kasa_yan", d)
        self.assertEqual(d["U"], 400)


if __name__ == "__main__":
    unittest.main()
