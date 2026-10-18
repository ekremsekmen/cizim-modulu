"""ÖN YÜZÜN SUNUMU — hesap/main.py · kök.

Derlenmiş React dosyaları ( on-yuz/dist ) programın kökünde sunulur:  uygulamanın
kendi adresleri ( /uygulama/abc ) index.html'e düşer, yönlendirmeyi React
yapar;  içerik özetli dosyalar uzun süre önbellekte kalır, index.html her
seferinde sorulur.  Derleme yoksa program yine açılır, nasıl derleneceğini
söyler.  API ve çizim yazı tipi bu yollarla gölgelenmez;  geçiş dönemi adresi
/yeni köke yönlenir.  Testler gerçek derlemeye bağlı değil:  geçici bir dist
kurulur.
"""

import asyncio
import os
import tempfile
import unittest
from unittest import mock

import main


def _al(yol, sorgu=""):
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
        "query_string": sorgu.encode(),
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
            durum, _b, govde = _al("/")
        self.assertEqual(durum, 503)
        self.assertIn("npm run build", govde.decode())

    def test_api_etkilenmez(self):
        with tempfile.TemporaryDirectory() as bos, mock.patch.object(main, "ON_YUZ", bos):
            durum, _b, govde = _al("/api/saglik")
        self.assertEqual(durum, 200)
        self.assertIn(b"calisiyor", govde)


class Derlenmis(unittest.TestCase):
    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        kok = self._gecici.name
        os.makedirs(os.path.join(kok, "assets"))
        with open(os.path.join(kok, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!doctype html><title>on yuz</title><div id='kok'></div>")
        with open(os.path.join(kok, "assets", "index-AbC123.js"), "w", encoding="utf-8") as f:
            f.write("console.log('on yuz')")
        with open(os.path.join(kok, "assets", "pdf.worker-Xy9.mjs"), "w", encoding="utf-8") as f:
            f.write("export {}")
        self._yama = mock.patch.object(main, "ON_YUZ", kok)
        self._yama.start()

    def tearDown(self):
        self._yama.stop()
        self._gecici.cleanup()

    def test_giris_sayfasi_her_seferinde_sorulur(self):
        durum, b, govde = _al("/")
        self.assertEqual(durum, 200)
        self.assertIn(b"<div id='kok'>", govde)
        self.assertEqual(b["cache-control"], "no-cache")

    def test_uygulamanin_adresleri_giris_sayfasina_duser(self):
        for yol in ("/uygulama/abc123", "/avan/trafik", "/ofis-standardi"):
            durum, _b, govde = _al(yol)
            self.assertEqual(durum, 200, yol)
            self.assertIn(b"<div id='kok'>", govde, yol)

    def test_eski_yeni_adresi_koke_yonlenir(self):
        for yol, hedef in (("/yeni", "/"), ("/yeni/", "/"), ("/yeni/avan/trafik", "/avan/trafik")):
            durum, b, _g = _al(yol)
            self.assertEqual((durum, b["location"]), (301, hedef), yol)
        #  sorgu da taşınır ( paylaşılmış çizim adresi )
        durum, b, _g = _al("/yeni/uygulama/abc", "cizim=kuyu_plani")
        self.assertEqual((durum, b["location"]), (301, "/uygulama/abc?cizim=kuyu_plani"))

    def test_api_golgelenmez(self):
        durum, _b, govde = _al("/api/saglik")
        self.assertEqual(durum, 200)
        self.assertIn(b"calisiyor", govde)
        #  bilinmeyen uç sayfa değil 404 ( JSON )
        durum, b, govde = _al("/api/yok-boyle-bir-uc")
        self.assertEqual(durum, 404)
        self.assertIn("json", b["content-type"])
        self.assertNotIn(b"<div id='kok'>", govde)

    def test_cizim_yazi_tipi_sunulur(self):
        """SVG'nin "CizimYazi"sı:  ekran onu /yazi'den yükler ( on-yuz/src/styles.css )."""
        durum, b, govde = _al("/yazi/LiberationSans-Regular.ttf")
        self.assertEqual(durum, 200)
        self.assertGreater(len(govde), 100000)

    def test_ozetli_dosya_uzun_sure_onbellekte(self):
        durum, b, govde = _al("/assets/index-AbC123.js")
        self.assertEqual((durum, govde), (200, b"console.log('on yuz')"))
        self.assertIn("immutable", b["cache-control"])
        self.assertIn("javascript", b["content-type"])

    def test_modul_isci_betik_turunde(self):
        """pdf.js işçisi modül olarak yüklenir:  .mjs betik türünde gitmeli."""
        _d, b, _g = _al("/assets/pdf.worker-Xy9.mjs")
        self.assertIn("javascript", b["content-type"])

    def test_eksik_dosya_404_giris_sayfasi_degil(self):
        """Eski derlemenin betiği istenirse index.html dönmek tarayıcıda MIME hatası olur."""
        durum, _b, govde = _al("/assets/index-Eski.js")
        self.assertEqual(durum, 404)
        self.assertNotIn(b"<div id='kok'>", govde)

    def test_klasor_disina_cikilamaz(self):
        durum, _b, govde = _al("/assets/../../../hesap/main.py")
        self.assertEqual(durum, 404)
        self.assertNotIn(b"import", govde)


if __name__ == "__main__":
    unittest.main()
