"""YAYIN ÖNCESİ DENETİM 22 KAS — sunucu bulguları.

1.  "Düzeltme öner" ucu ( care_uclari.api_care ) bozuk gövdede içeride çöküyordu:
    sözlük olmayan asansör ( [ 1 , 2 ] ), sözlük olmayan proje geneli ya da önceki
    girdi → TypeError / ValueError, kullanıcıya genel "DÜZELTME HATASI" iletisi.
2.  Okunamayan yazım ( "abc", "1.200" ) iki asansörlü projede hangi asansörde
    olduğunu söylemiyordu;  kural dışı değer söylüyordu ( "2 nolu asansör:  … " ).
"""

import json
import unittest
from unittest import mock

from uclar import care_uclari, uygulama_istegi


def _yanit(r):
    return json.loads(r.body)


class DuzeltmeUcuBozukGovde(unittest.TestCase):
    def _care(self, veri):
        #  Beklenmeyen hata günlüğe yazılıp genel iletiye çevrilir:  günlüğe hiç düşmemeli
        with mock.patch.object(care_uclari, "hata_kaydi") as kayit:
            y = _yanit(care_uclari.api_care(veri))
        self.assertFalse(kayit.called, y)
        return y

    def test_sozluk_olmayan_asansor_acik_iletiyle_reddedilir(self):
        for asansorler in ([1, 2], ["x"], [{}, None], [[]]):
            with self.subTest(asansorler=asansorler):
                y = self._care({"asansorler": asansorler})
                self.assertFalse(y["aktif"])
                self.assertEqual(y["hata"], ["Asansör girdisi okunamadı."])

    def test_bozuk_proje_geneli_ve_onceki_cokertmez(self):
        for ek in (
            {"proje_geneli": "x"},
            {"proje_geneli": [1]},
            {"onceki": {"asansor": 5, "proje_geneli": "x"}},
            {"onceki": {"asansor": [1]}},
        ):
            with self.subTest(ek=ek):
                y = self._care({"asansorler": [{"kabin_genisligi": 1500}], **ek})
                self.assertIn("aktif", y)


class OkunamayanYazimAsansoruyle(unittest.TestCase):
    def _hata(self, veri):
        with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
            uygulama_istegi.asansor_girdileri(veri)
        return " ".join(k.exception.hatalar)

    def test_iki_asansorde_asansor_adiyla(self):
        h = self._hata({"asansorler": [{}, {"kabin_genisligi": "abc"}], "proje_geneli": {}})
        self.assertIn("2 nolu asansör:  Kabin genişliği = abc", h)
        h = self._hata({"asansorler": [{"asansor_adi": "A1", "kabin_genisligi": "1.200"}, {}], "proje_geneli": {}})
        self.assertIn("A1:  Kabin genişliği = 1.200", h)

    def test_tek_asansorde_ad_yok(self):
        h = self._hata({"asansorler": [{"kabin_genisligi": "abc"}], "proje_geneli": {}})
        self.assertIn("Kabin genişliği = abc", h)
        self.assertNotIn("nolu asansör", h)

    def test_ilk_asansordeki_bina_alani_bir_kez(self):
        """Eski istek:  bina alanı ilk asansörün içinde ( proje_geneli yok ) — adsız bir kez."""
        h = self._hata({"asansorler": [{"temel_a": "abc"}, {}]})
        self.assertEqual(h.count("= abc"), 1, h)
        self.assertNotIn("nolu asansör", h)


if __name__ == "__main__":
    unittest.main()
