"""BİLİNEN SINIR ile PROGRAMIN HATASI ayrı ( cizim/sorun.py CizimKurulamaz ).

21 Eki son denetimi:  sorunlu kipte kesitlerin kurulamaması yerleşimin eksik
sözlüğünden doğan KeyError 'S' / 'M' / 'taban' / 'oda' ile yönetiliyordu;  13
yer hatayı log.debug ile yutuyordu — programlama hatası bilinen sınırdan
ayrılamıyor, ancak istisnaları izleyen ayrı bir araçla görülüyordu.  Şimdi:

  1.  Durmuş yerleşim ( sorun.durdu ) eski sözlüğün aynısıdır;  olmayan
      geometri okununca CizimKurulamaz.
  2.  Bilinen düzenlerde ( test_sorunlu_cizim BILINEN ) çizim CizimKurulamaz verir.
  3.  Yedek yollar yalnız bilinen sınırı ( ve girdi reddini ) sessizce
      karşılar;  programın hatası yükselir ya da kayda ERROR yazılır
      ( testler/conftest.py beklenmeyen ERROR'da testi kırar ).
"""

import pickle
import unittest
from unittest import mock

from cizim import cizimler
from cizim import donanim
from cizim import dusey
from cizim import kopru
from cizim import makine_dairesi
from cizim import olculer
from cizim import pafta
from cizim import sorun
from cizim import sorunlu
from uclar import cizim_uclari
from testler import test_sorunlu_cizim
from testler.test_olcu_kaynagi import DUZENLER


class DurmusYerlesim(unittest.TestCase):
    def test_eski_sozlugun_aynisi(self):
        d = sorun.durdu(["a"])
        self.assertEqual(d, {"hata": ["a"]})
        self.assertNotIn("taban", d)
        self.assertIsNone(d.get("taban"))
        self.assertEqual(d["hata"], ["a"])

    def test_olmayan_geometri_cizim_kurulamaz(self):
        d = sorun.durdu([sorun.Sorun("Kaide odaya sığmıyor.", ("kaide",))])
        with self.assertRaises(sorun.CizimKurulamaz) as k:
            d["S"]
        self.assertEqual(k.exception.hata, d["hata"])
        self.assertEqual(str(k.exception), "Kaide odaya sığmıyor.")
        #  Programlama hatasının türlerinden değil;  girdi reddi de değil
        self.assertNotIsInstance(k.exception, (KeyError, ValueError))
        self.assertIsInstance(k.exception, sorun.BILINEN)

    def test_onbellekte_aynen(self):
        """İstek içi önbellek yerleşimleri pickle'la kopyalar ( istek_onbellegi )."""
        d = pickle.loads(pickle.dumps(sorun.durdu(["a"]), protocol=pickle.HIGHEST_PROTOCOL))
        self.assertIsInstance(d, sorun.Durdu)
        with self.assertRaises(sorun.CizimKurulamaz):
            d["M"]
        e = pickle.loads(pickle.dumps(sorun.CizimKurulamaz(["x", "y"])))
        self.assertEqual((e.hata, str(e)), (["x", "y"], "x"))


class BilinenDuzenler(unittest.TestCase):
    def test_kurulamayan_cizim_cizim_kurulamaz_verir(self):
        """BILINEN düzenlerin kurulamayan çizimleri KeyError değil CizimKurulamaz
        ile durur ( ekranın "kurulamayan" listesi aynı — test_sorunlu_cizim )."""
        for (md, alan, deger), bilinen in test_sorunlu_cizim.VAKALAR.items():
            if not bilinen:
                continue
            g = test_sorunlu_cizim._g(test_sorunlu_cizim._veri(md, **{alan: deger}))
            for ad in pafta.sira(g):
                if cizimler.CIZIMLER[ad][2].partition("  (")[0] not in bilinen:
                    continue
                with self.subTest(md=md, alan=alan, cizim=ad), sorunlu.kip():
                    with self.assertRaises(sorun.CizimKurulamaz):
                        cizimler.CIZIMLER[ad][1](g)

    def test_kip_kapaliyken_yerlesim_durmus(self):
        g = test_sorunlu_cizim._g(test_sorunlu_cizim._veri(False, agirlik_yeri="Arka"))
        Y = dusey.yerlesim(g)
        self.assertIsInstance(Y, sorun.Durdu)
        self.assertTrue(Y["hata"])


class YedekYollar(unittest.TestCase):
    """Yedek değer yalnız bilinen sınırda;  programın hatası yutulmaz, yükselir."""

    @classmethod
    def setUpClass(cls):
        cls.g = test_sorunlu_cizim._g(test_sorunlu_cizim._veri(True))  # makine daireli örnek

    def _ikisi(self, modul, ad, cagri):
        """Hedef bilinen sınırla dururken çağrının sonucu;  programın hatasıyla
        dururken çağrı o hatayı yükseltmeli."""
        with mock.patch.object(modul, ad, side_effect=sorun.CizimKurulamaz(["x"])):
            sonuc = cagri()
        with mock.patch.object(modul, ad, side_effect=TypeError("programın hatası")):
            with self.assertRaises(TypeError):
                cagri()
        return sonuc

    def test_kopru(self):
        g = self.g
        #  Oda kurulamazsa saptırma kasnağı sayılmaz:  2:1'in kabin ve ağırlık kasnakları
        self.assertEqual(
            self._ikisi(makine_dairesi, "yerlesim", lambda: kopru.kasnaklar(g)), [240.0, 240.0, 400.0]
        )
        self.assertIsNone(self._ikisi(makine_dairesi, "yerlesim", lambda: kopru.sarim_acisi(g)))

    def test_olculer(self):
        g = self.g
        tam = olculer.hesap_olculeri(g)
        sonuc = self._ikisi(makine_dairesi, "yerlesim", lambda: olculer.hesap_olculeri(g))
        self.assertTrue(sonuc)
        self.assertLess(set(sonuc), set(tam))
        sonuc = self._ikisi(donanim, "yerlesim", lambda: olculer.hesap_olculeri(g))
        self.assertLess(set(sonuc), set(tam))

    def test_olcu_kurucusu(self):
        ham, i, proje = cizim_uclari._istek(test_sorunlu_cizim._veri(True))
        kur, _taban = cizim_uclari._kurucu(ham, "kuyu_plani", proje, i + 1)
        self.assertIsNone(self._ikisi(kopru, "cizim_girdisi", lambda: kur({})))

    def test_paftada_olmayan_cizim_kurulmaz(self):
        """Makine dairesinde kuyu üstü planı paftada yok ( pafta.sira ):  ölçü
        kurucusu onu kurmaz.  Eskiden kurmaya çalışıyor, şasesiz makinenin
        TypeError'ı yutuluyordu ( makine dairesinde 1:1 )."""
        ham, i, proje = cizim_uclari._istek(DUZENLER["makine dairesinde 1:1"]())
        kur, taban = cizim_uclari._kurucu(ham, "kuyu_ustu", proje, i + 1)
        self.assertIsNone(kur({}))
        self.assertNotIn("g", taban)
        kur, _taban = cizim_uclari._kurucu(ham, "makine_dairesi", proje, i + 1)
        self.assertIsNotNone(kur({}))


class Ekran(unittest.TestCase):
    """Sorunlu kipte bir çizimin kurulamaması öteki çizimleri silmez;  bilinen
    sınır sessizdir, programın hatası kayıtta ERROR ( izle )."""

    def _cizim_bozuk(self, istisna):
        dog, _ciz, baslik = cizimler.CIZIMLER["kabin_ustu"]

        def bozuk(_g):
            raise istisna

        return mock.patch.dict(cizimler.CIZIMLER, {"kabin_ustu": (dog, bozuk, baslik)})

    def test_bilinen_sinir_sessiz_programin_hatasi_error(self):
        veri = test_sorunlu_cizim._veri(False, kuyu_genisligi=1600)  # sorunlu, hepsi kurulur
        tam = test_sorunlu_cizim._ekran(veri)
        self.assertFalse(tam["aktif"])
        self.assertEqual(tam["kurulamayan"], [])
        with (
            self._cizim_bozuk(sorun.CizimKurulamaz(["x"])),
            self.assertNoLogs(cizim_uclari.log, level="ERROR"),
        ):
            r = test_sorunlu_cizim._ekran(veri)
        self.assertEqual(r["kurulamayan"], ["KABİN ÜSTÜ PLANI"])
        self.assertEqual(len(r["cizimler"]), len(tam["cizimler"]) - 1)
        with (
            self._cizim_bozuk(TypeError("programın hatası")),
            self.assertLogs(cizim_uclari.log, "ERROR") as k,
        ):
            r = test_sorunlu_cizim._ekran(veri)
        self.assertEqual(r["kurulamayan"], ["KABİN ÜSTÜ PLANI"])
        self.assertEqual(len(r["cizimler"]), len(tam["cizimler"]) - 1)
        self.assertIsNotNone(k.records[0].exc_info)  # izi ( traceback ) var


if __name__ == "__main__":
    unittest.main()
