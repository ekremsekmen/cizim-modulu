"""GELİŞTİRME ARAÇLARI ( araclar/ ) — taramanın hüküm karşılaştırması bir
değişikliği kaçırırsa tarama boşuna "geçti" der."""

import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if KOK not in sys.path:
    sys.path.insert(0, KOK)

from araclar import tarama as T  # noqa: E402

KAYIT = {"ana": {"A": {"durum": "çizildi", "sebep": ""}, "B": {"durum": "ret", "sebep": "X sığmıyor"}}}


class Karsilastirma(unittest.TestCase):
    def test_ayni_hukum_fark_yok(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": []},
            {"ad": "B", "durum": "ret", "hata": ["X sığmıyor", "Y de"]},
        ]
        self.assertEqual(T.karsilastir("ana", sonuc, KAYIT), [])

    def test_hukum_ve_sebep_degisimi(self):
        sonuc = [
            {"ad": "A", "durum": "ret", "hata": ["Z yok"]},
            {"ad": "B", "durum": "ret", "hata": ["W yok"]},
        ]
        f = T.karsilastir("ana", sonuc, KAYIT)
        self.assertEqual(
            f, ["A:  çizildi → ret  ( Z yok )", "B:  ret → ret  ( W yok )  ·  önceki sebep:  X sığmıyor"]
        )

    def test_sorun_cokme_ve_eksik_duzen(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": ["kuyu_plani: NaN kabin"]},
            {"ad": "C", "durum": "çöktü", "ayrinti": "KeyError"},
        ]
        f = T.karsilastir("ana", sonuc, KAYIT)
        self.assertIn("düzen artık taranmıyor:  B", f)
        self.assertIn("yeni düzen ( kayıtta yok ):  C  →  çöktü", f)
        self.assertIn("SORUN  A:  kuyu_plani: NaN kabin", f)
        self.assertIn("ÇÖKTÜ  C:  KeyError", f)

    def test_kayit_butun_gruplari_kapsar(self):
        import json

        with open(T.HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)
        self.assertEqual(sorted(kayit), sorted(T.GRUPLAR))
        self.assertEqual(
            {g: len(v) for g, v in kayit.items()}, {g: sum(1 for _ in T.duzenler(g)) for g in T.GRUPLAR}
        )


if __name__ == "__main__":
    unittest.main()
