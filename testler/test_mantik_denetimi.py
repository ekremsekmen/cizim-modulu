"""MANTIKSIZ GİRDİLER ( kullanıcı:  "başka mantıksızlık var mı" — 4 Eki ).

Girilen değer ya kullanılır ya hesap durur:
  1. kabin iç yüksekliği ve kat kapısı yüksekliği en az 2.000 mm ( TS EN 81-20
     m.5.4.1 · m.5.3.1.1 ) — eskiden 1.500'lük kabin sessizce çiziliyordu
  2. kapı kabinden yüksek olamaz — eskiden 2.600'lük kapı 2.000'lik kabine
  3. tampon adedi tam sayı ve sıfır değil — eskiden 0 ve 1,5 sessizce 1
  4. iki tamponda "tamponlar arası" girilir — eskiden istenip formda kutusu yoktu
  5. kuyunun geometrisi kurulamıyorsa ( kabin kuyuya sığmıyor … ) hesap da durur —
     eskiden çizim reddederken hesap kuruluyordu ( özette "engelleyici" )."""

import json
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _yol in (os.path.join(KOK, "hesap"), os.path.join(KOK, "testler")):
    if _yol not in sys.path:
        sys.path.append(_yol)

from api import cizim as UC  # noqa: E402
from api import uygulama as UYG  # noqa: E402
from engine.uygulama import hesap as E_UYG  # noqa: E402

import test_yerlesim_saglamligi as Y  # noqa: E402


def _calistir(**ek):
    """( çizim ucu , hesap ) — standart 800 kg, makine dairesiz."""
    v = Y._veri(800, True, "Sağ")
    v["asansorler"][0].update(ek)
    cizim = json.loads(UC.api_cizimler(v).body)
    asansorler, ortak = UYG._asansor_girdileri(v)
    return cizim, E_UYG.hesapla_coklu(asansorler, ortak)


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
        from cizim import kopru as CK, kuyu_dibi as CKD
        from engine.uygulama import girdi as E_UGR

        v = Y._veri(800, True, "Sağ", kabin_tampon_adedi=2, kabin_tampon_arasi=600)
        ham, _i, proje = UC._istek(v)
        g, hata = CK.cizim_girdisi(E_UGR.tamamla(ham), None, proje, 1)
        t = CKD.yerlesim(g)["kabin_tamponlari"]
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


if __name__ == "__main__":
    unittest.main()
