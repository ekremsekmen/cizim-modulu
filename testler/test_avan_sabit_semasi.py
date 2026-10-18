"""AVAN OFİS STANDARDININ FORMU — /api/secenekler → sabit_sema.

Yeni ön yüz avan sabitlerini bu şemadan çizer:  motora yeni bir sabit
eklenip şemaya yazılmazsa ekranda görünmez, kullanıcı değiştiremez.  Her
sabit bir gruba ve bir etikete sahip olmalı;  olmayan sabit listede durmamalı.
"""

import unittest

from motor.avan import avan_hesabi
from motor.avan import avan_sabitleri


class AvanSabitSemasi(unittest.TestCase):
    def setUp(self):
        self.sema = avan_sabitleri.sema()
        self.gruptakiler = [k for g in self.sema["gruplar"] for k in g["alanlar"]]

    def test_her_sabit_bir_grupta_bir_kez(self):
        self.assertEqual(sorted(self.gruptakiler), sorted(self.sema["varsayilan"]))

    def test_her_sabitin_etiketi_var(self):
        self.assertEqual(set(self.sema["etiket"]), set(self.sema["varsayilan"]))

    def test_yedek_sabit_listede_yok(self):
        for k in avan_hesabi.SABIT_B_YEDEK:
            self.assertNotIn(k, self.sema["varsayilan"])

    def test_iki_kaynak_cakismaz(self):
        """İki sözlük istekte tek "sabitler" olarak gider:  aynı anahtar ikisinde
        olursa biri ötekini sessizce ezer."""
        self.assertFalse(set(avan_hesabi.SABIT_B_VARSAYILAN) & set(avan_hesabi.OFIS_VARSAYILAN))

    def test_metin_sabitleri(self):
        self.assertEqual(self.sema["metin"], ["kablo_tipi"])


if __name__ == "__main__":
    unittest.main()
