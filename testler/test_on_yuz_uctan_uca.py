"""ÖN YÜZ — GERÇEK TARAYICIDA UÇTAN UCA ( 19 Eki )

Eski arayüzün tarayıcı testleri ( TEST 5 arayüz · 6 dosya geri yükleme · 13
canlı hesap ) onunla birlikte kalktı;  bunlar yeni ön yüzün ( on-yuz/,
React ) karşılıklarıdır.  Birim testleri ( vitest ) ve sunucu sözleşmesi
( test_on_yuz_sozlesmesi ) parçaları denetler;  burada parçalar birlikte,
gerçek sunucu ve gerçek tarayıcıyla:

  1  örnek proje:  ekranın hükmü ve çizimleri sunucunun yanıtıyla aynı
  2  canlı hesap:  girdi değişince ekran taze hesabı gösterir, geride kalan
     yanıt öne geçmez;  beyan yükü değişince kabin kütlesi tablodan gelir
  3  proje dosyası:  .uygulama ve .avan kaydet → aç → aynı istek, aynı hesap;
     iki asansör ayrı kalır
  4  ölçü kutusu:  ölçüye tıkla → kaynakları;  yeni değer → girdi değişir
  5  teslim:  onaysız paket kapalı;  onaylı ZIP iner, içinde PDF ve .uygulama
  6  adresler:  bilinmeyen proje açılışa döner;  /yeni köke yönlenir
  Hiçbir testte konsol hatası yok.

Seçiciler rol ve ad üzerinden ( aria-label, düğme metni ) — biçime bağlı değil.

Ön yüzün DERLENMİŞ hâlini dener:  kontrol.py ( uctan_uca;  tam denetimde ön
yüz derlendikten sonra ) koşar.  Doğrudan pytest'te KONTROL_UCTAN_UCA=1 ister;
yoksa atlanır ( ve neden atlandığı görünür ).  Program kendi açtığı boş bir
portta koşar:  açık bir programa dokunmaz.
"""

import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import zipfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(KOK, "on-yuz", "dist", "index.html")
ZAMAN = 60_000  # ms — çizim ve paket isteği için

ATLA = None
if os.environ.get("KONTROL_UCTAN_UCA") != "1":
    ATLA = "uçtan uca:  kontrol.py uctan_uca ( ya da KONTROL_UCTAN_UCA=1 ) ile koşar"
elif not os.path.isfile(DIST):
    ATLA = "ön yüz derlenmemiş:  python -m araclar.on_yuz_derle"
else:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        ATLA = "playwright kurulu değil"


def _bos_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Izleyici:
    """Sayfanın istekleri:  hesap ve çizim istek / yanıt çiftleri, yoldaki
    istek sayısı ( sakinleşmeyi beklemek için ) ve konsol hataları."""

    UCLAR = ("/api/uygulama/coklu", "/api/uygulama/cizimler", "/api/avan", "/api/trafik")

    def __init__(self, sayfa):
        self.sayfa = sayfa
        self.yolda = 0
        self.ciftler = {u: [] for u in self.UCLAR}
        self.hatalar = []
        sayfa.on("request", self._istek)
        sayfa.on("requestfinished", self._bitti)
        sayfa.on("requestfailed", self._bitti)
        sayfa.on("pageerror", lambda e: self.hatalar.append(f"pageerror:  {e}"))
        sayfa.on("console", lambda m: m.type == "error" and self.hatalar.append(f"console:  {m.text}"))

    def _istek(self, r):
        if "/api/" in r.url:
            self.yolda += 1

    def _bitti(self, r):
        if "/api/" not in r.url:
            return
        self.yolda -= 1
        uc = next((u for u in self.UCLAR if r.url.endswith(u)), None)
        yanit = r.response() if r.failure is None else None
        if uc and yanit is not None and yanit.ok:
            self.ciftler[uc].append((json.loads(r.post_data or "{}"), yanit.json()))

    def sakin(self, sure=900):
        """Yolda istek kalmayıp `sure` ms öyle durana kadar bekler ( ön yüz girdiyi
        280 ms bekletip gönderir )."""
        son_hareket = time.time()
        bitis = time.time() + ZAMAN / 1000
        while time.time() < bitis:
            self.sayfa.wait_for_timeout(100)
            if self.yolda > 0:
                son_hareket = time.time()
            elif (time.time() - son_hareket) * 1000 >= sure:
                return
        raise AssertionError("sayfa sakinleşmedi:  istekler bitmiyor")

    def son(self, uc):
        self.sakin()
        assert self.ciftler[uc], f"{uc} isteği gitmedi"
        return self.ciftler[uc][-1]


@unittest.skipIf(ATLA, ATLA)
class OnYuzUctanUca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = _bos_port()
        cls.url = f"http://127.0.0.1:{cls.port}"
        cls.sunucu = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(cls.port),
                "--log-level",
                "warning",
            ],
            cwd=os.path.join(KOK, "hesap"),
        )
        for _ in range(120):
            try:
                with urllib.request.urlopen(cls.url + "/api/saglik", timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            cls.sunucu.terminate()
            raise RuntimeError("program açılamadı")
        cls.pw = sync_playwright().start()
        cls.tarayici = cls.pw.chromium.launch()
        with urllib.request.urlopen(cls.url + "/api/uygulama/alanlar", timeout=30) as c:
            cls.sema = json.load(c)
        cls.etiket = {a["anahtar"]: a["etiket"] for g in cls.sema["gruplar"] for a in g["alanlar"]}

    @classmethod
    def tearDownClass(cls):
        cls.tarayici.close()
        cls.pw.stop()
        cls.sunucu.terminate()
        cls.sunucu.wait(timeout=30)

    def setUp(self):
        #  Her test boş bir tarayıcıyla ( projeler localStorage'da )
        self.baglam = self.tarayici.new_context(
            viewport={"width": 1440, "height": 900}, accept_downloads=True
        )
        self.baglam.set_default_timeout(ZAMAN)
        self.sayfa = self.baglam.new_page()
        self.iz = Izleyici(self.sayfa)

    def tearDown(self):
        hatalar = self.iz.hatalar
        self.baglam.close()
        self.assertEqual(hatalar, [], "\n".join(hatalar))

    # ------------------------------------------------------------ yardımcılar
    def ornek_projeyi_ac(self):
        self.sayfa.goto(self.url + "/uygulama/ornek")
        self.sayfa.wait_for_url(re.compile(r"/uygulama/[0-9a-z]{6,}$"))
        self.iz.sakin()

    def ad(self, anahtar):
        """Alanın ekrandaki adı ( şemanın etiketi, açıklamasız ) — on-yuz etiketBol."""
        e = self.etiket[anahtar]
        return e[: e.index("(")].strip() if "(" in e else e.strip()

    def alan_kutusu(self, anahtar):
        """Alan aramayla öne getirilir ( kapalı grup ya da Gelişmiş'te olsa da )."""
        ara = self.sayfa.get_by_role("complementary", name="Girdiler").get_by_label("Alan ara")
        ara.fill(self.ad(anahtar))
        return self.sayfa.get_by_role("complementary", name="Girdiler").get_by_label(
            self.ad(anahtar), exact=True
        )

    def secim_yap(self, anahtar, gorunen):
        self.alan_kutusu(anahtar).click()
        self.sayfa.get_by_role("option", name=gorunen, exact=True).click()

    def sayaclar(self):
        metin = self.sayfa.get_by_role("complementary", name="Uygunluk").inner_text()
        m = re.search(r"(\d+)\s*uygun değil\s*(\d+)\s*uygun\s*(\d+)\s*bilgi", metin)
        self.assertIsNotNone(m, metin[:300])
        return tuple(int(x) for x in m.groups())

    # ------------------------------------------------------------ 1 örnek proje
    def test_ornek_proje_hukmu_ve_cizimleri_sunucununki(self):
        self.ornek_projeyi_ac()
        _istek, hesap = self.iz.son("/api/uygulama/coklu")
        bolumler = hesap["asansorler"][0]["bolumler"] + (hesap.get("proje_geneli") or [])
        beklenen = (
            sum(b["sonuc"] is not None and b["sonuc"].get("uygun") is False for b in bolumler),
            sum(b["sonuc"] is not None and b["sonuc"].get("uygun") is True for b in bolumler),
            sum(b["sonuc"] is None or b["sonuc"].get("uygun") is None for b in bolumler),
        )
        self.assertEqual(self.sayaclar(), beklenen)

        _istek, cizim = self.iz.son("/api/uygulama/cizimler")
        self.assertTrue(cizim["aktif"], cizim.get("hata"))
        #  Her çizim tuvalde, sunucunun SVG'siyle ( ölçüleri tıklanır )
        self.assertEqual(self.sayfa.locator("[data-cizim]").count(), len(cizim["cizimler"]))
        self.assertGreater(self.sayfa.get_by_role("button", name=re.compile(r"^Ölçü ")).count(), 50)
        #  Çizim yazı tipi yüklü ( SVG'nin "CizimYazi"sı;  yoksa Arial'a düşer )
        self.assertTrue(self.sayfa.evaluate("document.fonts.load('12px CizimYazi').then(f => f.length > 0)"))

    # ------------------------------------------------------------ 2 canlı hesap
    def test_canli_hesap_son_girdinin_sonucunu_gosterir(self):
        from motor.ortak import ofis

        self.ornek_projeyi_ac()
        #  İki değişiklik arka arkaya:  ilkinin yanıtı ikincisini ezmemeli
        self.secim_yap("beyan_yuku", "1.000")
        self.secim_yap("beyan_yuku", "630")
        istek, hesap = self.iz.son("/api/uygulama/coklu")
        a = istek["asansorler"][0]
        self.assertEqual(a["beyan_yuku"], "630")
        #  Yük değişti:  kabin kütlesi BOŞ gider ( tablodan ) — silinseydi varsayılan 700 olurdu
        self.assertEqual(a.get("kabin_agirligi"), "")
        tablo = ofis.bos_kabin_kutlesi(630)
        self.assertEqual(hesap["asansorler"][0]["girdi"]["kabin_agirligi"], tablo)
        #  Ekran son hesabın değerini gösterir
        kutu = self.alan_kutusu("kabin_agirligi")
        self.assertEqual(kutu.input_value(), "")
        self.assertEqual(kutu.get_attribute("placeholder"), f"{tablo:,.0f}".replace(",", "."))

    # ------------------------------------------------------------ 3 proje dosyası
    def _hesap_istegi(self):
        istek, hesap = self.iz.son("/api/uygulama/coklu")
        return {k: istek[k] for k in ("asansorler", "proje_geneli", "sabitler")}, hesap

    def test_uygulama_dosyasi_gidis_donus(self):
        self.ornek_projeyi_ac()
        #  İkinci asansör, birinciden farklı
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.iz.sakin()
        self.secim_yap("beyan_yuku", "1.000")
        once, hesap_once = self._hesap_istegi()
        self.assertEqual(len(once["asansorler"]), 2)
        self.assertNotEqual(once["asansorler"][0], once["asansorler"][1])

        self.sayfa.get_by_role("button", name=re.compile("Örnek proje")).first.click()
        with self.sayfa.expect_download() as indirme:
            self.sayfa.get_by_role("button", name="Dosyaya kaydet").click()
        with tempfile.TemporaryDirectory() as klasor:
            dosya = os.path.join(klasor, "proje.uygulama")
            indirme.value.save_as(dosya)
            self.assertEqual(json.load(open(dosya, encoding="utf-8"))["__mod"], "uygulama")
            #  Boş bir tarayıcıda açılır ( başka bilgisayar gibi )
            self.baglam.clear_cookies()
            self.sayfa.evaluate("localStorage.clear()")
            self.sayfa.goto(self.url + "/")
            for u in self.iz.ciftler.values():
                u.clear()
            with self.sayfa.expect_file_chooser() as secici:
                self.sayfa.get_by_role("button", name="Dosya seç").click()
            secici.value.set_files(dosya)
            self.sayfa.wait_for_url(re.compile(r"/uygulama/[0-9a-z]{6,}$"))
        sonra, hesap_sonra = self._hesap_istegi()
        self.assertEqual(sonra, once)
        self.assertEqual(hesap_sonra, hesap_once)

    def test_avan_dosyasi_gidis_donus(self):
        self.sayfa.goto(self.url + "/avan/trafik")
        #  Avan projesi:  bina, tek tip asansör, avan kartları ( ölçüler mm )
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut', bina_yuksekligi: '30', yapi_yuksekligi: '31', N: '10', h: '3',
                         hizli1: '20', hizli2: '2'},
                ekNufus: [],
                trafikAsansorleri: [{P: '8', kapi_genisligi: '800', kapi_tipi: 'Teleskopik Otomatik'}],
                ortak: {mk_yok: 'true', temel_a: '20', temel_b: '15'},
                avanAsansorleri: [{tanim: 'A', Hk: '34', kuyu_genisligi: '1800', kabin_boyu: '1400',
                                   kabin_genisligi: '1100'}, {}, {}, {}],
                kapak: {project_title: 'Avan deneme'}}))"""
        )
        self.sayfa.goto(self.url + "/avan/hesaplar")
        once, avan_once = self.iz.son("/api/avan")
        self.assertTrue(any(a.get("aktif") for a in avan_once["asansorler"]), avan_once)

        with self.sayfa.expect_download() as indirme:
            self.sayfa.get_by_role("button", name="Proje dosyası olarak kaydet").click()
        with tempfile.TemporaryDirectory() as klasor:
            dosya = os.path.join(klasor, "proje.avan")
            indirme.value.save_as(dosya)
            self.sayfa.evaluate("localStorage.clear()")
            self.sayfa.goto(self.url + "/avan/hesaplar")
            self.iz.sakin()
            for u in self.iz.ciftler.values():
                u.clear()
            with self.sayfa.expect_file_chooser() as secici:
                self.sayfa.get_by_role("button", name="Proje dosyasını aç").click()
            secici.value.set_files(dosya)
        self.assertIn("açıldı", self.sayfa.get_by_text(re.compile("açıldı")).first.inner_text())
        self.sayfa.get_by_role("link", name=re.compile("Avan hesapları")).click()
        sonra, avan_sonra = self.iz.son("/api/avan")
        self.assertEqual(sonra, once)
        self.assertEqual(avan_sonra, avan_once)

    # ------------------------------------------------------------ 4 ölçü kutusu
    def test_olcu_kutusu_girdiyi_degistirir(self):
        self.ornek_projeyi_ac()
        olcu = self.sayfa.get_by_role("button", name=re.compile(r"^Ölçü KUYU DİBİ")).first
        olcu.scroll_into_view_if_needed()
        olcu.focus()
        self.sayfa.keyboard.press("Enter")
        kutu = self.sayfa.get_by_role("dialog", name=re.compile(r"^Ölçü "))
        kutu.get_by_role("button", name="Uygula").wait_for()
        eski = int(re.search(r"\d+", olcu.get_attribute("aria-label").replace(".", "")).group())
        kutu.get_by_role("textbox").fill(str(eski + 50))
        with self.sayfa.expect_response(lambda r: r.url.endswith("/api/uygulama/olcu_degistir")) as yanit:
            kutu.get_by_role("button", name="Uygula").click()
        d = yanit.value.json()
        self.assertTrue(d["aktif"], d)
        self.assertEqual(d["olcu"], eski + 50)
        degisiklik = d["degisiklikler"][0]
        istek, _hesap = self.iz.son("/api/uygulama/coklu")
        yer = (
            istek["proje_geneli"]
            if degisiklik["anahtar"] in self.sema["proje_geneli"]
            else istek["asansorler"][0]
        )
        self.assertEqual(float(str(yer[degisiklik["anahtar"]]).replace(",", ".")), degisiklik["deger"])

    # ------------------------------------------------------------ 5 teslim
    def test_teslim_onaysiz_kapali_onayli_paket_iner(self):
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim = self.sayfa.get_by_role("dialog", name="Teslim")
        paket = teslim.get_by_role("button", name=re.compile("Paketi indir"))
        self.assertTrue(paket.is_disabled())
        teslim.get_by_role("checkbox").check()
        self.assertTrue(paket.is_enabled())
        with self.sayfa.expect_download(timeout=180_000) as indirme:
            paket.click()
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "paket.zip")
            indirme.value.save_as(yol)
            with open(yol, "rb") as f:
                adlar = zipfile.ZipFile(io.BytesIO(f.read())).namelist()
        self.assertTrue(any(a.endswith(".pdf") for a in adlar), adlar)
        self.assertTrue(any(a.endswith(".uygulama") for a in adlar), adlar)
        self.assertTrue(any(a.lower().endswith((".dxf", ".dwg")) for a in adlar), adlar)

    # ------------------------------------------------------------ 6 adresler
    def test_bilinmeyen_proje_acilisa_doner(self):
        self.sayfa.goto(self.url + "/uygulama/yokboyle1")
        self.sayfa.wait_for_url(self.url + "/")
        self.assertIn("bu tarayıcıda yok", self.sayfa.get_by_role("status").inner_text())

    def test_eski_yeni_adresi_koke_yonlenir(self):
        self.sayfa.goto(self.url + "/yeni/tablolar")
        self.assertEqual(self.sayfa.url, self.url + "/tablolar")
        self.sayfa.get_by_role("heading", name="Tablolar").first.wait_for()


if __name__ == "__main__":
    unittest.main()
