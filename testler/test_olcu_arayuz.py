"""Ölçü düzenlemenin gecikmiş yanıtları; Node varsa unittest keşfine de katılır."""
from pathlib import Path
import shutil
import subprocess
import unittest


class OlcuArayuz(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Arayüz yarış testleri için Node gerekli")
    def test_gecikmis_yanitlar(self):
        sonuc = subprocess.run(
            [shutil.which("node"), "--test", str(Path(__file__).with_name("olcu_arayuz.test.cjs"))],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(sonuc.returncode, 0, sonuc.stdout + sonuc.stderr)
