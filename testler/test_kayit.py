"""KAYIT ( logging ) — uçların genel except'i hatayı kullanıcıya ileti olarak
döndürür;  sunucunun kaydında da izi kalmalı ( uclar/uc_ortak.hata_kaydi )."""

import logging
import unittest

from uclar import cizim_uclari
from uclar import uygulama_uclari
from uclar.uc_ortak import hata_kaydi


class HataKaydi(unittest.TestCase):
    def setUp(self):
        self.log = logging.getLogger("test.kayit")

    def test_girdi_reddi_bilgi_duzeyinde(self):
        with self.assertLogs(self.log, level="DEBUG") as k:
            try:
                raise ValueError("Pafta çizilemiyor:  X")
            except ValueError as e:
                hata_kaydi(self.log, e)
        self.assertEqual([r.levelno for r in k.records], [logging.INFO])
        self.assertIn("Pafta çizilemiyor", k.output[0])
        self.assertIsNone(k.records[0].exc_info)

    def test_beklenmeyen_hata_iziyle(self):
        with self.assertLogs(self.log, level="DEBUG") as k:
            try:
                {}["yok"]
            except KeyError as e:
                hata_kaydi(self.log, e)
        self.assertEqual([r.levelno for r in k.records], [logging.ERROR])
        self.assertIsNotNone(k.records[0].exc_info)  # izi ( traceback ) var
        self.assertIn("KeyError", k.output[0])


class UcunKaydi(unittest.TestCase):
    def test_cizim_ucu_beklenmeyen_hatayi_kaydeder(self):
        #  Uç kullanıcıya iletiyi döndürür ve hatayı izleriyle kaydeder
        import json
        from unittest import mock

        with (
            mock.patch.object(uygulama_uclari, "_asansor_girdileri", side_effect=KeyError("bozuk")),
            self.assertLogs(cizim_uclari.log, level="ERROR") as k,
        ):
            yanit = cizim_uclari.api_cizimler({"asansorler": [{}]})
        self.assertEqual(json.loads(yanit.body), {"aktif": False, "hata": ["ÇİZİM HATASI: 'bozuk'"]})
        self.assertIsNotNone(k.records[0].exc_info)


if __name__ == "__main__":
    unittest.main()
