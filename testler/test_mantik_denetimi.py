"""MANTIKSIZ GİRDİLER ( kullanıcı:  "başka mantıksızlık var mı" — 4 Eki ).

Girilen değer ya kullanılır ya hesap durur:
  1. kabin iç yüksekliği ve kat kapısı yüksekliği en az 2.000 mm ( TS EN 81-20
     m.5.4.1 · m.5.3.1.1 ) — eskiden 1.500'lük kabin sessizce çiziliyordu
  2. kapı kabinden yüksek olamaz — eskiden 2.600'lük kapı 2.000'lik kabine
  3. tampon adedi tam sayı ve sıfır değil — eskiden 0 ve 1,5 sessizce 1
  4. iki tamponda "tamponlar arası" girilir — eskiden istenip formda kutusu yoktu
  5. kuyunun geometrisi kurulamıyorsa ( kabin kuyuya sığmıyor … ) hesap da durur —
     eskiden çizim reddederken hesap kuruluyordu ( özette "engelleyici" ).
  6. 0 anlamsız olan ölçüler ( karşı ağırlık, makine ağırlığı, tampon ezilmesi,
     regülatör … ) sıfırdan büyük ( 13 Eki )."""

import json
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from uclar import cizim_uclari
from motor.uygulama import mukavemet_girdi
from motor.uygulama import uygulama_hesabi

from testler import test_yerlesim_saglamligi
from uclar import uygulama_istegi


def _calistir(**ek):
    """( çizim ucu , hesap ) — standart 800 kg, makine dairesiz."""
    v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
    v["asansorler"][0].update(ek)
    cizim = json.loads(cizim_uclari.api_cizimler(v).body)
    try:
        asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
    except uygulama_istegi.GecersizGirdi as e:  # kapıdan geçmedi:  uç bunu döndürür
        return cizim, {"aktif": False, "hata": e.hatalar}
    return cizim, uygulama_hesabi.hesapla_coklu(asansorler, ortak)


class Yukseklikler(unittest.TestCase):
    def test_iki_metreden_alcak_kabin_ve_kapi(self):
        for ek, metin in (
            ({"kabin_ic_yuksekligi": 1500}, "Kabin iç yüksekliği 1500 mm"),
            ({"kapi_yuksekligi": 1800}, "Kat kapısı yüksekliği 1800 mm"),
        ):
            with self.subTest(ek):
                cizim, hesap = _calistir(**ek)
                self.assertFalse(cizim.get("aktif"))
                self.assertTrue(any(h.startswith(metin) for h in cizim["hata"]), cizim["hata"])
                self.assertFalse(hesap.get("aktif"))
                self.assertTrue(any(h.startswith(metin) for h in hesap["hata"]), hesap["hata"])

    def test_kapi_kabinden_yuksek_olamaz(self):
        cizim, hesap = _calistir(kapi_yuksekligi=2600)
        for d in (cizim, hesap):
            self.assertFalse(d.get("aktif"))
            self.assertTrue(any("kabin iç yüksekliğinden" in h for h in d["hata"]), d["hata"])
        #  2.200'lük kabinin üst kirişi tavanın ( 2.260 ) üstünde kalsın:  paten arası
        #  en az 2.200 + 60 + 460 = 2.720 ( varsayılan 2.660 — 2.000'lik kabin, 8 Eki )
        self.assertTrue(
            _calistir(kapi_yuksekligi=2000, kabin_ic_yuksekligi=2200, kabin_paten_arasi=2720)[0].get("aktif")
        )


class PatenArasi(unittest.TestCase):
    """Kabin paten arası boşsa kabin iç yüksekliği + 660:  şase kabini sarar
    ( tasarim/alanlar.KABIN_PATEN_PAYI — LiftDesigner'ın 2.000'lik kabininde
    2.660;  12 Eki ).  Eskiden sabit 2.660'tı:  2.200'lük kabinde üst kiriş
    tavana giriyor, çizim duruyordu.  Hesap ile çizim aynı h'yi kullanır;
    girilen değer değiştirilmez."""

    def _h(self, **ek):
        v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
        v["asansorler"][0].update(kapi_yuksekligi=2000, **ek)
        asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        ((g, hata),) = cizim_uclari.girdiler(v, asansorler, ortak, s if s.get("aktif") else None, "P")
        self.assertIsNotNone(g, hata)
        self.assertTrue(s.get("aktif"), s.get("hata"))
        A = mukavemet_girdi.tamamla(asansorler[0] | ortak)
        self.assertEqual(A["kabin_paten_arasi"], g["dusey"]["kabin_paten_arasi"])
        return g["dusey"]["kabin_paten_arasi"]

    def test_bossa_kabin_yuksekliginden(self):
        self.assertEqual(self._h(kabin_ic_yuksekligi=2000, kabin_paten_arasi=None), 2660)
        self.assertEqual(self._h(kabin_ic_yuksekligi=2200, kabin_paten_arasi=None), 2860)
        cizim, _hesap = _calistir(kapi_yuksekligi=2000, kabin_ic_yuksekligi=2200, kabin_paten_arasi=None)
        self.assertTrue(cizim.get("aktif"), cizim.get("hata"))

    def test_bozuk_deger_kurala_cevrilmez(self):
        #  Kural yalnız BOŞ alanda:  motora "x" gelirse doğrulama durdurur ( Gy'de
        #  1 Eki'den beri sessizce DBGW − 60'a çevriliyor, hesap kuruluyordu — 12
        #  Eki ).  Ekranda form okunamayan yazımı zaten reddeder ( uc_ortak._RED,
        #  uç hesap yapmaz );  açık motora formdan geçmeden gelen girdideydi.
        for alan in ("kabin_paten_arasi", "agirlik_genisligi"):
            with self.subTest(alan):
                v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
                asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
                asansorler[0][alan] = "x"
                hesap = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
                self.assertFalse(hesap.get("aktif"))
                self.assertTrue(any("sayı olmalı" in h for h in hesap["hata"]), hesap["hata"])

    def test_girilen_degismez(self):
        self.assertEqual(self._h(kabin_ic_yuksekligi=2200, kabin_paten_arasi=3000), 3000)
        cizim, _hesap = _calistir(kapi_yuksekligi=2000, kabin_ic_yuksekligi=2400, kabin_paten_arasi=2660)
        self.assertFalse(cizim.get("aktif"))
        self.assertTrue(any("kabin tavanına giriyor" in h for h in cizim["hata"]), cizim["hata"])


class KuralKaynagi(unittest.TestCase):
    """Boş alan kuralla dolduysa rapor kaynağını "KURAL · …" yazar ( 13 Eki —
    eskiden Gy ve h boşken "GİRİŞ" yazıyordu:  girilmiş sanılıyordu );  girilen
    değer "GİRİŞ"."""

    def _kaynaklar(self, **ek):
        v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
        v["asansorler"][0].update(ek)
        asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        self.assertTrue(s.get("aktif"), s.get("hata"))
        adimlar = [a for b in s["asansorler"][0]["bolumler"] for a in b.get("adimlar", [])]
        return {
            a["sembol"]: a["kaynak"]
            for a in adimlar
            if a.get("aciklama") in ("Patenler arası düşey mesafe", "Karşı ağırlık genişliği")
        }

    def test_bos_alan_kural_yazar(self):
        k = self._kaynaklar(kabin_paten_arasi=None, agirlik_genisligi=None, kabin_ic_yuksekligi=2200)
        self.assertEqual(k["h"], "KURAL  ·  kabin iç yüksekliği + 660")
        self.assertTrue(k["Gy"].startswith("KURAL  ·  "), k)

    def test_girilen_giris_yazar(self):
        k = self._kaynaklar(kabin_paten_arasi=2900, agirlik_genisligi=800)
        self.assertEqual(k, {"h": "GİRİŞ", "Gy": "GİRİŞ"})


class SifirOlamaz(unittest.TestCase):
    """0 anlamsız olan ölçüler hesabı durdurur ( tasarim/alanlar:  pozitif — 13 Eki:
    karşı ağırlığın genişliği ve derinliği, makine ağırlığı, tamponların ezilmesi,
    regülatörün gergi ağırlığı ve devreye girme hızı 0 girilince hesap
    kuruluyordu ).  Formda olmayan, çizimden ölçülenler ( ray ve halat boyları,
    dolgu yüksekliği ) motoru doğrudan çağırana karşı korunur."""

    def test_formdaki_sifir_kapida_durur(self):
        """Formdan gelen 0 isteğin kapısında durur ( uygulama_istegi — hesap ve
        çizim başlamaz );  motorun kendi denetimi doğrudan çağrıda aynı iletiyi verir."""
        for alan in (
            "agirlik_genisligi",
            "agirlik_derinligi",
            "makine_agirligi",
            "kabin_tampon_ezilme",
            "agirlik_tampon_ezilme",
            "reg_gergi_agirligi",
            "reg_devreye_hizi",
        ):
            with self.subTest(alan):
                v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
                v["asansorler"][0][alan] = 0
                with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                    uygulama_istegi.asansor_girdileri(v)
                self.assertTrue(any("sıfırdan büyük" in h for h in k.exception.hatalar), k.exception.hatalar)
                v["asansorler"][0].pop(alan)
                asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
                hesap = uygulama_hesabi.hesapla_coklu([{**asansorler[0], alan: 0}], ortak)
                self.assertFalse(hesap["asansorler"][0].get("aktif"))
                self.assertIn(k.exception.hatalar[0], hesap["asansorler"][0]["hata"])

    def test_cizimden_olculenler_motorda_durur(self):
        for alan in ("kabin_ray_boyu", "agirlik_ray_boyu", "reg_halat_boyu", "aski_halat_boyu"):
            with self.subTest(alan):
                v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
                asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
                g = mukavemet_girdi.tamamla(
                    {**mukavemet_girdi.varsayilanlar(), **ortak, **asansorler[0], alan: 0}
                )
                self.assertTrue(any("sıfırdan büyük" in h for h in mukavemet_girdi.dogrula(g)))


class TamponAdedi(unittest.TestCase):
    def test_sifir_ve_kesirli_adet_durur(self):
        for n, hesap_metni in ((0, "sıfır olamaz"), (1.5, "tam sayı")):
            with self.subTest(n):
                cizim, hesap = _calistir(kabin_tampon_adedi=n)
                self.assertFalse(cizim.get("aktif"))
                self.assertFalse(hesap.get("aktif"))
                self.assertTrue(any(hesap_metni in h for h in hesap["hata"]), hesap["hata"])

    def test_uc_tampon_cizilmez_hesaplanir(self):
        cizim, hesap = _calistir(kabin_tampon_adedi=3)
        self.assertFalse(cizim.get("aktif"))
        self.assertIn("çizim 1 ya da 2 tampon çizer", cizim["hata"][0])
        self.assertTrue(hesap.get("aktif"))

    def test_iki_tamponda_aralari_formdan(self):
        cizim, _h = _calistir(kabin_tampon_adedi=2)
        self.assertFalse(cizim.get("aktif"))
        self.assertIn("Kabin tamponları arası", cizim["hata"][0])
        for ek in (
            {"kabin_tampon_adedi": 2, "kabin_tampon_arasi": 600},
            {"agirlik_tampon_adedi": 2, "agirlik_tampon_arasi": 400},
        ):
            with self.subTest(ek):
                self.assertTrue(_calistir(**ek)[0].get("aktif"))
        from cizim import kopru, kuyu_dibi
        from motor.uygulama import uygulama_girdisi

        v = test_yerlesim_saglamligi.standart_istek(
            800, True, "Sağ", kabin_tampon_adedi=2, kabin_tampon_arasi=600
        )
        ham, _i, proje = cizim_uclari._istek(v)
        g, hata = kopru.cizim_girdisi(uygulama_girdisi.tamamla(ham), None, proje, 1)
        t = kuyu_dibi.yerlesim(g)["kabin_tamponlari"]
        self.assertEqual(len(t), 2)
        self.assertAlmostEqual((t[1][0] + t[1][2]) / 2.0 - (t[0][0] + t[0][2]) / 2.0, 600)


class HesapGeometriyleDurur(unittest.TestCase):
    def test_kabin_kuyuya_sigmiyorsa_hesap_durur(self):
        cizim, hesap = _calistir(kuyu_genisligi=1000)
        self.assertFalse(cizim.get("aktif"))
        self.assertFalse(hesap.get("aktif"))
        self.assertTrue(any("kuyu genişliğinden" in h for h in hesap["hata"]), hesap["hata"])

    def test_cizimin_cizemedigi_duzende_hesap_surer(self):
        #  Makaralı kabin pateni:  çizim ölçüsünü bilmez, hesap kurulur
        cizim, hesap = _calistir(paten_tipi="Makaralı")
        self.assertFalse(cizim.get("aktif"))
        self.assertTrue(hesap.get("aktif"))


class IletiDili(unittest.TestCase):
    """Çizimin iletisi iç ad söylemez ( 19 Eki denetimi:  dar kuyuda
    "kapi.sol_pay: sıfırdan büyük olmalı ( -400.0 )" çıkıyordu )."""

    def test_dar_kuyu_kapinin_sigmadigini_soyler(self):
        r = json.loads(
            cizim_uclari.api_cizimler(
                {"asansorler": [{"kuyu_genisligi": "100"}], "proje_geneli": {}, "sabitler": {}, "asansor": 0}
            ).body
        )
        self.assertFalse(r["aktif"])
        metin = " ".join(r["hata"])
        self.assertIn("Kapı kuyuya sığmıyor", metin)
        self.assertIn("kuyu genişliğinden", metin)
        self.assertNotRegex(metin, r"\b[a-z_]+\.[a-z_]+:")

    def test_her_zorunlu_alanin_adi_var(self):
        from cizim import girdi

        isaretli = {"yeri", "duzen", "montaj", "kaciklik_y", "eksen_kaciklik"}
        adsiz = [
            f"{b}.{a}"
            for b, al in girdi.ZORUNLU.items()
            for a in al
            if a not in isaretli and f"{b}.{a}" not in girdi.ADLAR
        ]
        self.assertEqual(adsiz, [])


if __name__ == "__main__":
    unittest.main()
