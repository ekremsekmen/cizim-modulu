"""YENİ ÖN YÜZÜN SUNUMU — hesap/main.py · /yeni.

Derlenmiş React dosyaları ( on-yuz/dist ) /yeni altında sunulur:  uygulamanın
kendi adresleri ( /yeni/uygulama/abc ) index.html'e düşer, yönlendirmeyi React
yapar;  içerik özetli dosyalar uzun süre önbellekte kalır, index.html her
seferinde sorulur.  Derleme yoksa program yine açılır, /yeni nasıl
derleneceğini söyler.  Testler gerçek derlemeye bağlı değil:  geçici bir
dist kurulur.
"""

import asyncio
import os
import tempfile
import unittest
from unittest import mock

import main


def _al(yol):
    """Uygulamaya doğrudan ASGI GET isteği:  ( durum, başlıklar, gövde )."""
    giden = []

    async def al():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def gonder(m):
        giden.append(m)

    kapsam = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": yol,
        "raw_path": yol.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("127.0.0.1", 80),
    }
    asyncio.run(main.app(kapsam, al, gonder))
    bas = giden[0]
    basliklar = {k.decode().lower(): v.decode() for k, v in bas["headers"]}
    return bas["status"], basliklar, b"".join(m.get("body", b"") for m in giden[1:])


class Derlenmemis(unittest.TestCase):
    def test_nasil_derlenecegini_soyler(self):
        with tempfile.TemporaryDirectory() as bos, mock.patch.object(main, "ON_YUZ", bos):
            durum, _b, govde = _al("/yeni/")
        self.assertEqual(durum, 503)
        self.assertIn("npm run build", govde.decode())

    def test_eski_arayuz_etkilenmez(self):
        with tempfile.TemporaryDirectory() as bos, mock.patch.object(main, "ON_YUZ", bos):
            durum, _b, govde = _al("/")
        self.assertEqual(durum, 200)
        self.assertIn(b"<html", govde.lower())


class Derlenmis(unittest.TestCase):
    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        kok = self._gecici.name
        os.makedirs(os.path.join(kok, "assets"))
        with open(os.path.join(kok, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!doctype html><title>yeni</title><div id='kok'></div>")
        with open(os.path.join(kok, "assets", "index-AbC123.js"), "w", encoding="utf-8") as f:
            f.write("console.log('yeni')")
        with open(os.path.join(kok, "assets", "pdf.worker-Xy9.mjs"), "w", encoding="utf-8") as f:
            f.write("export {}")
        self._yama = mock.patch.object(main, "ON_YUZ", kok)
        self._yama.start()

    def tearDown(self):
        self._yama.stop()
        self._gecici.cleanup()

    def test_giris_sayfasi_her_seferinde_sorulur(self):
        for yol in ("/yeni", "/yeni/"):
            durum, b, govde = _al(yol)
            self.assertEqual(durum, 200, yol)
            self.assertIn(b"<div id='kok'>", govde)
            self.assertEqual(b["cache-control"], "no-cache")

    def test_uygulamanin_adresleri_giris_sayfasina_duser(self):
        for yol in ("/yeni/uygulama/abc123", "/yeni/avan/trafik", "/yeni/ofis-standardi"):
            durum, _b, govde = _al(yol)
            self.assertEqual(durum, 200, yol)
            self.assertIn(b"<div id='kok'>", govde, yol)

    def test_ozetli_dosya_uzun_sure_onbellekte(self):
        durum, b, govde = _al("/yeni/assets/index-AbC123.js")
        self.assertEqual((durum, govde), (200, b"console.log('yeni')"))
        self.assertIn("immutable", b["cache-control"])
        self.assertIn("javascript", b["content-type"])

    def test_modul_isci_betik_turunde(self):
        """pdf.js işçisi modül olarak yüklenir:  .mjs betik türünde gitmeli."""
        _d, b, _g = _al("/yeni/assets/pdf.worker-Xy9.mjs")
        self.assertIn("javascript", b["content-type"])

    def test_eksik_dosya_404_giris_sayfasi_degil(self):
        """Eski derlemenin betiği istenirse index.html dönmek tarayıcıda MIME hatası olur."""
        durum, _b, govde = _al("/yeni/assets/index-Eski.js")
        self.assertEqual(durum, 404)
        self.assertNotIn(b"<div id='kok'>", govde)

    def test_klasor_disina_cikilamaz(self):
        durum, _b, govde = _al("/yeni/assets/../../../hesap/main.py")
        self.assertEqual(durum, 404)
        self.assertNotIn(b"import", govde)


if __name__ == "__main__":
    unittest.main()
