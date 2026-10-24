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
     iki asansör ayrı kalır;  eski dosyanın onay kutusu sunucunun okuduğu seçenek;
     kaldırılan asansörün sonucu ve kapak değeri kalana geçmez ( avanda trafik
     sütununun kartı da gider )
  4  ölçü kutusu:  ölçüye tıkla → kaynakları;  yeni değer → girdi değişir
  5  teslim:  onaysız paket kapalı;  onaylı ZIP iner, içinde PDF ve .uygulama;
     çizimde sorun varken paket kapalı, hesap PDF'i açık
  7  sorunlu çizim:  kural sağlanmasa da çizim ekranda, sorunlu parça kırmızı;
     karttaki soruna tıklanınca tuval onun yerine yakınlaşır;  "Düzeltme öner"
     doğrulanmış düzeltmeleri getirir, "Uygula" kutuya yazar, sorun kalkar;
     girdi değişince eski çizimin düzeltmeleri uygulanamaz
  8  sunucuya ulaşılamazsa:  ekran söyler, "Yeniden dene" sunucu dönünce açar;
     indirme yarıda kopunca da söyler;  kapak önizlemesi pdf.js işçisini kapatır
  9  arıza matrisi:  ekranın konuştuğu her uç × her arıza türü — ekran söyler,
     sayfa çökmez, arıza kalkınca düzelir ( PR'da iki tür;  ARIZA_HEPSI=1 beşi )
  10 kaynak sayacı:  aynı işlemler tekrarlanınca açık işçi, nesne adresi,
     dinleyici ve yoldaki istek büyümez
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
        #  Yoldaki istekler ( adres, başladığı an ) ve bütün isteklerin sayısı:
        #  sakinleşmezse ileti hangisinin takıldığını ya da durmadan istek
        #  gittiğini söyler ( CI'da bir kez sebebi görünmeden düştü — 21 Eki )
        self.suren = {}
        self.sayi = 0
        #  Sayfa yeniden yüklenirken ( goto / reload ) yoldaki istekler:  yeni
        #  belge gelince iptal olurlar, ama Playwright onlar için ne
        #  requestfinished ne requestfailed gönderir — sayaçta kalırlar.  21 Eki:
        #  "Avan proje" kartı testi reload sırasında yoldaki alanlar isteği yüzünden
        #  60 sn bekleyip düşüyordu ( bilgisayar yüklüyken;  isteği 3 sn
        #  geciktiren sunucuyla her seferinde üretildi ).
        self.eski = set()
        self.ciftler = {u: [] for u in self.UCLAR}
        self.hatalar = []
        sayfa.on("request", self._istek)
        sayfa.on("requestfinished", self._bitti)
        sayfa.on("requestfailed", self._bitti)
        sayfa.on("framenavigated", self._yeni_belge)
        sayfa.on("pageerror", lambda e: self.hatalar.append(f"pageerror:  {e}"))
        sayfa.on("console", lambda m: m.type == "error" and self.hatalar.append(f"console:  {m.text}"))

    def _istek(self, r):
        if r.is_navigation_request() and r.frame == self.sayfa.main_frame:
            self.eski = set(self.suren)
        if "/api/" in r.url:
            self.yolda += 1
            self.sayi += 1
            self.suren[id(r)] = (f"{r.method} {r.url.split('/api/', 1)[1]}", time.time())

    def _yeni_belge(self, cerceve):
        """Yeni belge geldi:  yeniden yüklemeden önce yolda kalanlar iptal oldu."""
        if cerceve != self.sayfa.main_frame:
            return
        for k in self.eski & set(self.suren):
            self.suren.pop(k)
            self.yolda -= 1
        self.eski = set()

    def _bitti(self, r):
        if "/api/" not in r.url or self.suren.pop(id(r), None) is None:
            return  # iptal sayılıp düşülmüş istek geç bitti
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
        ilk_sayi = self.sayi
        while time.time() < bitis:
            self.sayfa.wait_for_timeout(100)
            if self.yolda > 0:
                son_hareket = time.time()
            elif (time.time() - son_hareket) * 1000 >= sure:
                return
        simdi = time.time()
        yolda = [f"{ad} ( {simdi - t:.0f} sn )" for ad, t in self.suren.values()]
        raise AssertionError(
            f"sayfa sakinleşmedi:  istekler bitmiyor — beklerken {self.sayi - ilk_sayi} istek gitti, "
            f"yolda {self.yolda}:  {yolda}"
        )

    def son(self, uc):
        self.sakin()
        assert self.ciftler[uc], f"{uc} isteği gitmedi"
        return self.ciftler[uc][-1]


class _SahteSayfa:
    def __init__(self):
        self.main_frame = object()
        self.olay = {}

    def on(self, ad, f):
        self.olay[ad] = f


class _SahteIstek:
    def __init__(self, sayfa, url, gezinti=False):
        self.url, self.method, self.frame = url, "GET", sayfa.main_frame
        self.failure, self.post_data, self._gezinti = None, None, gezinti

    def is_navigation_request(self):
        return self._gezinti

    def response(self):
        return None


class IzleyiciSayaci(unittest.TestCase):
    """Tarayıcısız:  yoldaki istek sayacı ( 21 Eki — reload sırasında iptal olan
    istek için olay gelmiyor, sayaç takılı kalıyordu )."""

    def test_yeniden_yuklemede_iptal_olan_istek_duser(self):
        s = _SahteSayfa()
        iz = Izleyici(s)
        eski = _SahteIstek(s, "http://x/api/uygulama/alanlar")
        s.olay["request"](eski)
        s.olay["request"](_SahteIstek(s, "http://x/", gezinti=True))  # reload
        s.olay["framenavigated"](s.main_frame)
        yeni = _SahteIstek(s, "http://x/api/uygulama/alanlar")
        s.olay["request"](yeni)
        s.olay["requestfinished"](yeni)
        self.assertEqual((iz.yolda, iz.suren), (0, {}))
        s.olay["requestfinished"](eski)  # geç gelen olay sayacı eksiye düşürmez
        self.assertEqual(iz.yolda, 0)

    def test_tek_sayfa_gezintisi_yoldaki_istegi_dusurmez(self):
        s = _SahteSayfa()
        iz = Izleyici(s)
        s.olay["request"](_SahteIstek(s, "http://x/api/avan"))
        s.olay["framenavigated"](s.main_frame)  # pushState:  belge isteği yok
        self.assertEqual(iz.yolda, 1)


class ArizaMatrisiKapsami(unittest.TestCase):
    """Tarayıcısız:  ön yüzün çağırdığı her uç arıza matrisinde — yeni uç matrise
    girmeden bu test geçmez ( 24 Eki:  sessiz hata yolları uç uç bulunuyordu )."""

    def test_on_yuzun_her_ucu_matriste(self):
        import glob
        import inspect

        kaynak = "".join(
            open(p, encoding="utf-8").read()
            for p in glob.glob(os.path.join(KOK, "on-yuz", "src", "**", "*.ts*"), recursive=True)
            if ".test." not in p
        )
        uclar = set(re.findall(r'"(/api/[a-z_/-]+)"', kaynak))
        uclar |= {f"/api/indir/{u}" for u in re.findall(r'(?:indir\(|uc=)"([a-z-]+)"', kaynak)}
        self.assertGreater(len(uclar), 10, uclar)
        matris = "".join(
            inspect.getsource(getattr(OnYuzUctanUca, ad))
            for ad in ("test_ariza_matrisi_uygulama", "test_ariza_matrisi_avan", "test_ariza_matrisi_diger")
        )
        self.assertEqual(sorted(u for u in uclar if f'"{u}"' not in matris), [], "matriste olmayan uçlar")


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

    def test_eski_dosyanin_onay_kutusu_sunucunun_okudugu_secenek(self):
        """24 Eki ( dış inceleme ):  makine yükünün yolu eskiden onay kutusuydu;
        eski dosyanın işaretsizi ( false ) sunucuda "Bina yapısına" okunur
        ( makine_yuk_yolu ).  Ön yüz tanımayıp varsayılana ( "Kılavuz raylara" )
        döndürüyordu:  proje başka bir yük yoluyla hesaplanıyordu."""
        eski = {
            "__mod": "uygulama",
            "__surum": 1,
            "alanlar": {
                "mk_proje_adi": "Eski",
                "m_mk_yok": True,
                "__muk_adet": 1,
                "__muk_asansorler": [{"makine_raya_biniyor": False}],
            },
        }
        self.sayfa.goto(self.url + "/")
        with tempfile.TemporaryDirectory() as klasor:
            dosya = os.path.join(klasor, "eski.uygulama")
            with open(dosya, "w", encoding="utf-8") as f:
                json.dump(eski, f)
            with self.sayfa.expect_file_chooser() as secici:
                self.sayfa.get_by_role("button", name="Dosya seç").click()
            secici.value.set_files(dosya)
            self.sayfa.wait_for_url(re.compile(r"/uygulama/[0-9a-z]{6,}$"))
        istek, _hesap = self.iz.son("/api/uygulama/coklu")
        self.assertEqual(istek["asansorler"][0].get("makine_raya_biniyor"), "Bina yapısına")
        self.assertIn("Bina yapısına", self.alan_kutusu("makine_raya_biniyor").inner_text())
        bildirim = self.sayfa.get_by_role("status").inner_text()
        self.assertIn('"eski.uygulama" açıldı.', bildirim)
        self.assertNotIn("varsayılana döndü", bildirim)

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

            #  Uygulama kısmı avan dosyasını açmaz:  açık hata, sayfa ve avan projesi yerinde
            avan_kaydi = self.sayfa.evaluate("localStorage.getItem('asansor:avan')")
            self.ornek_projeyi_ac()
            adres = self.sayfa.url
            self.sayfa.get_by_role("button", name=re.compile("Örnek proje")).first.click()
            with self.sayfa.expect_file_chooser() as secici:
                self.sayfa.get_by_role("button", name="Dosyadan aç").click()
            secici.value.set_files(dosya)
            self.sayfa.get_by_text(
                "Bu bir avan projesi dosyası — avan ekranından ya da açılış sayfasından açın."
            ).wait_for()
            self.assertEqual(self.sayfa.url, adres)
            self.assertEqual(self.sayfa.evaluate("localStorage.getItem('asansor:avan')"), avan_kaydi)

            #  Açılış ikisini de alır, avan dosyası avan kısmında açılır
            self.sayfa.goto(self.url + "/")
            with self.sayfa.expect_file_chooser() as secici:
                self.sayfa.get_by_role("button", name="Dosya seç").click()
            secici.value.set_files(dosya)
            self.sayfa.wait_for_url(re.compile(r"/avan/trafik$"))

    def kayitli_asansorler(self):
        """Tarayıcıda kayıtlı projenin asansörleri ( aynı istek önbellekten yanıtlanır,
        ağdan görünmez — durum kaydın kendisinden okunur )."""
        self.iz.sakin()
        kimlik = self.sayfa.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return self.sayfa.evaluate(f"JSON.parse(localStorage.getItem('asansor:proje:{kimlik}')).asansorler")

    def sekmeler(self):
        return self.sayfa.get_by_role("navigation", name="Asansörler").get_by_role(
            "button", name=re.compile(r"^(?!.*kaldır)")
        )

    def test_kaldirilan_asansorun_sonucu_kalanda_gorunmez(self):
        """Sırayı kaydıran kaldırmada son hesap eski dizilişindir:  sonuç asansöre
        sırasıyla eşlendiği için 1.'nin ( hepsi uygun ) hükümleri 2.'nin
        sekmesinde görünüyordu ( 21 Eki ).  Yeni hesap tutulurken sonuç yok;
        gelince 2.'nin kendi hükmü ( kuyu 2.300:  uygun değil bölüm var )."""
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.iz.sakin()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.assertGreater(self.sayaclar()[0], 0)
        tutulan = []
        self.sayfa.route("**/api/uygulama/coklu", lambda r: tutulan.append(r))
        try:
            self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first.click()
            self.sayfa.wait_for_timeout(1500)  # girdi gecikmesi geçsin, yeni hesap tutulsun
            self.assertTrue(tutulan, "yeni hesap istenmedi")
            metin = self.sayfa.get_by_role("complementary", name="Uygunluk").inner_text()
            m = re.search(r"(\d+)\s*uygun değil\s*(\d+)\s*uygun", metin)
            self.assertFalse(
                m and int(m.group(2)) > 0, f"kaldırılan asansörün hükümleri görünüyor:  {metin[:200]}"
            )
        finally:
            for r in tutulan:
                r.continue_()
            self.sayfa.unroute("**/api/uygulama/coklu")
        self.iz.sakin()
        self.assertGreater(self.sayaclar()[0], 0)

    def test_asansor_eklenir_kaldirilir_geri_alinir(self):
        self.ornek_projeyi_ac()
        ekle = self.sayfa.get_by_role("button", name="Asansör ekle")
        ekle.click()
        ekle.click()
        #  Eklenen asansöre geçilir;  ad kopyalanmaz ( "Asansör 3" )
        self.assertEqual(self.sekmeler().count() - 1, 3)  # ekle düğmesi de bir düğme
        self.assertEqual(
            self.sayfa.get_by_role("button", name="Asansör 3", exact=True).get_attribute("aria-current"),
            "page",
        )
        self.secim_yap("beyan_yuku", "1.000")
        once, _h = self._hesap_istegi()
        self.assertEqual([x.get("beyan_yuku") for x in once["asansorler"]][2], "1000")

        #  Ortadaki kaldırılır:  sıra korunur
        self.sayfa.get_by_role("button", name="Asansör 2 asansörünü kaldır").click()
        sonra, _h = self._hesap_istegi()
        self.assertEqual(sonra["asansorler"], [once["asansorler"][0], once["asansorler"][2]])
        #  Geri alınır:  üç asansör, aynı girdiler
        self.sayfa.get_by_role("status").get_by_role("button", name="Geri al").click()
        self.assertEqual(self.kayitli_asansorler(), once["asansorler"])
        self.assertEqual(self.sekmeler().count() - 1, 3)
        #  Tek asansörde kaldırma düğmesi yok
        for _ in range(2):
            self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first.click()
        self.assertEqual(self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).count(), 0)

    def kayitli_kapak(self):
        self.iz.sakin()
        kimlik = self.sayfa.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return self.sayfa.evaluate(f"JSON.parse(localStorage.getItem('asansor:proje:{kimlik}')).kapak")

    def test_kaldirilan_asansorun_kapak_degeri_kalana_gecmez(self):
        """24 Eki ( Codex ):  kapağın asansöre özgü değeri ( "capacity.1" ) asansörün
        sırasına bağlıdır;  1. asansör kaldırılınca kalan 1000 kg'lık asansörün
        tablosuna kaldırılanın değeri basılıyordu.  Kaldırılanınki silinir,
        sonrakiler kayar;  "Geri al" kapağı da döndürür, kapağa yazılınca kapanır."""
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.secim_yap("beyan_yuku", "1.000")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name=re.compile("Örnek proje")).first.click()
        bilgiler = self.sayfa.get_by_role("dialog", name="Proje bilgileri")
        bilgiler.get_by_role("button", name="Kapak sayfası").click()
        bilgiler.get_by_role("radio", name="1. asansör").click()
        bilgiler.get_by_label("Kapasite", exact=True).fill("1275 kg / 17 kişi")
        bilgiler.get_by_role("radio", name="2. asansör").click()
        bilgiler.get_by_label("Hız", exact=True).fill("1 m/s")
        self.sayfa.keyboard.press("Escape")
        bilgiler.wait_for(state="detached")
        once = {"capacity.1": "1275 kg / 17 kişi", "speed.2": "1 m/s"}
        self.assertEqual(self.kayitli_kapak(), once)

        self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first.click()
        self.assertEqual([a.get("beyan_yuku") for a in self.kayitli_asansorler()], ["1000"])
        self.assertEqual(self.kayitli_kapak(), {"speed.1": "1 m/s"})
        self.sayfa.get_by_role("status").get_by_role("button", name="Geri al").click()
        self.assertEqual(self.kayitli_kapak(), once)

        #  Kaldırmadan sonra kapağa yazılınca geri alma kapanır:  yazılanı ezerdi
        self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first.click()
        geri_al = self.sayfa.get_by_role("status").get_by_role("button", name="Geri al")
        self.assertEqual(geri_al.count(), 1)
        self.sayfa.get_by_role("button", name=re.compile("Örnek proje")).first.click()
        kapak = bilgiler.get_by_role("button", name="Kapak sayfası")
        if kapak.get_attribute("aria-expanded") != "true":
            kapak.click()
        bilgiler.get_by_label("İl", exact=True).fill("Konya")
        self.sayfa.keyboard.press("Escape")
        bilgiler.wait_for(state="detached")
        self.assertEqual(geri_al.count(), 0)
        self.assertEqual(self.kayitli_kapak(), {"speed.1": "1 m/s", "city": "Konya"})

    def test_yeni_avan_projesi_oncekini_geri_alir(self):
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut', N: '10'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: 'Eski avan'}}))"""
        )
        self.sayfa.reload()
        self.iz.sakin()
        kayit = "JSON.parse(localStorage.getItem('asansor:avan'))"
        self.sayfa.get_by_role("button", name="Yeni avan projesi").click()
        istek, _y = self.iz.son("/api/trafik")
        self.assertNotIn("bina_tipi", istek["girdiler"])
        #  Yeni projenin tek, boş sütunu:  sütunlar olduğu gibi gider, kapasitesizi
        #  sunucu atar ( ekrandaki numarası korunsun — 21 Eki )
        self.assertEqual(istek["girdiler"]["asansorler"], [{}])
        self.assertEqual(self.sayfa.evaluate(kayit)["kapak"], {})
        self.sayfa.get_by_role("button", name="Geri al").click()
        self.iz.sakin()
        eski = self.sayfa.evaluate(kayit)
        self.assertEqual(
            (eski["trafik"], eski["kapak"]),
            ({"bina_tipi": "Konut", "N": "10"}, {"project_title": "Eski avan"}),
        )

    def test_ornek_proje_gercek_ve_her_bolumu_uygun(self):
        """Örnek gerçekte var olan bir asansör ( on-yuz/src/lib/ornek.ts ):  hiçbir
        bölüm "uygun değil" değil, çizimler kurulur;  tarayıcıda kalmış ESKİ
        örnek ( boş değerli, sürümsüz ) açılınca yenilenir."""
        self.ornek_projeyi_ac()
        self.assertEqual(self.sayaclar()[0], 0)
        _istek, hesap = self.iz.son("/api/uygulama/coklu")
        self.assertTrue(hesap["ozet"]["tumu_uygun"], hesap["ozet"])
        _istek, cizim = self.iz.son("/api/uygulama/cizimler")
        self.assertTrue(cizim["aktif"], cizim.get("hata"))
        kimlik = self.sayfa.url.rstrip("/").rsplit("/", 1)[-1]
        self.assertEqual(self.kayitli_asansorler()[0].get("beyan_yuku"), "1275")
        self.sayfa.evaluate(
            f"""(() => {{ const k = 'asansor:proje:{kimlik}';
                const p = JSON.parse(localStorage.getItem(k));
                delete p.ornekSurumu;  p.asansorler = [{{}}];
                localStorage.setItem(k, JSON.stringify(p)); }})()"""
        )
        self.sayfa.goto(self.url + "/")
        self.ornek_projeyi_ac()
        self.assertTrue(self.sayfa.url.endswith(kimlik))
        self.assertEqual(self.kayitli_asansorler()[0].get("beyan_yuku"), "1275")

    def test_ornek_proje_tektir_ve_sifirlanir(self):
        self.ornek_projeyi_ac()
        ilk = self.sayfa.url
        ornek = self.kayitli_asansorler()
        self.secim_yap("beyan_yuku", "1.000")
        self.sayfa.goto(self.url + "/")
        self.ornek_projeyi_ac()
        #  Aynı örnek açılır ( yeni kopya değil ), değeri durur
        self.assertEqual(self.sayfa.url, ilk)
        ornekler = self.sayfa.evaluate(
            "JSON.parse(localStorage.getItem('asansor:projeler')).filter(x => x.ornek).length"
        )
        self.assertEqual(ornekler, 1)
        self.assertEqual(self.kayitli_asansorler()[0].get("beyan_yuku"), "1000")
        self.sayfa.get_by_role("button", name="Örneği sıfırla").click()
        self.assertEqual(self.kayitli_asansorler(), ornek)

    def test_iki_sekme_ayni_projeyi_esitler(self):
        self.ornek_projeyi_ac()
        adres = self.sayfa.url
        ikinci = self.baglam.new_page()
        iz2 = Izleyici(ikinci)
        ikinci.goto(adres)
        iz2.sakin()

        def beyan(sayfa):
            return sayfa.get_by_role("complementary", name="Girdiler").get_by_role(
                "combobox", name=self.ad("beyan_yuku"), exact=True
            )

        #  Birinci sekmede değişen ikincide görünür
        self.secim_yap("beyan_yuku", "1.000")
        iz2.sakin()
        ikinci.get_by_role("complementary", name="Girdiler").get_by_label("Alan ara").fill(
            self.ad("beyan_yuku")
        )
        self.assertEqual(beyan(ikinci).inner_text().strip(), "1.000")
        #  İkincide eklenen asansör birinciye geçer;  birincinin değişikliği ezilmez
        ikinci.get_by_role("button", name="Asansör ekle").click()
        iz2.sakin()
        kayit = self.kayitli_asansorler()
        self.assertEqual(len(kayit), 2)
        self.assertEqual(kayit[0].get("beyan_yuku"), "1000")
        self.assertEqual(self.sekmeler().count() - 1, 2)
        #  Birincide silinince ikinci söyler ve projeyi yeniden yazmaz
        self.sayfa.get_by_role("button", name=re.compile("Örnek proje")).first.click()
        self.sayfa.get_by_role("button", name="Projeyi sil").click()
        self.sayfa.get_by_role("button", name="Sil", exact=True).click()
        uyari = ikinci.get_by_role("alert").filter(has_text="başka bir sekmede silindi")
        uyari.wait_for()
        kimlik = adres.rsplit("/", 1)[-1]
        ikinci.get_by_role("button", name="Asansör ekle").click()
        iz2.sakin()
        self.assertIsNone(ikinci.evaluate(f"localStorage.getItem('asansor:proje:{kimlik}')"))
        self.assertEqual(iz2.hatalar, [])

    def test_avan_geri_al_sayfa_yenilenince_durur(self):
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: 'Eski avan'}}))"""
        )
        self.sayfa.reload()
        self.sayfa.get_by_role("button", name="Yeni avan projesi").click()
        self.iz.sakin()
        self.sayfa.reload()
        self.sayfa.get_by_role("button", name="Geri al").click()
        self.iz.sakin()
        kayit = self.sayfa.evaluate("JSON.parse(localStorage.getItem('asansor:avan'))")
        self.assertEqual(kayit["kapak"], {"project_title": "Eski avan"})
        #  Bildirim kapandı:  bir daha yenilenince çıkmaz
        self.sayfa.reload()
        self.iz.sakin()
        self.assertEqual(self.sayfa.get_by_role("button", name="Geri al").count(), 0)

    def test_acilistaki_avan_karti_yeni_proje_baslatir(self):
        """Açılıştaki "Avan proje" kartı açık projeyi açıyordu ( 21 Eki ):  yeni
        proje başlatır, önceki "Geri al" ile döner;  "Son projeler" satırı açık
        projeye dönmeye devam eder."""
        self.sayfa.goto(self.url + "/")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: 'Eski avan'}}))"""
        )
        self.sayfa.reload()
        self.sayfa.get_by_role("link", name=re.compile(r"^Avan proje")).click()
        self.sayfa.get_by_role("button", name="Geri al").wait_for()
        self.iz.sakin()
        kayit = self.sayfa.evaluate("JSON.parse(localStorage.getItem('asansor:avan'))")
        self.assertEqual(kayit["kapak"], {})
        self.sayfa.get_by_role("button", name="Geri al").click()
        self.iz.sakin()
        kayit = self.sayfa.evaluate("JSON.parse(localStorage.getItem('asansor:avan'))")
        self.assertEqual(kayit["kapak"], {"project_title": "Eski avan"})

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
        #  Bir kutu, bir değişiklik:  ikinci "Uygula" ilk değişikliği görmeden
        #  hesaplanıyordu ( kutu açıldığı andaki girdilerle konuşur;  21 Eki )
        self.assertTrue(kutu.get_by_role("button", name="Uygula").is_disabled())
        self.assertTrue(kutu.get_by_text("ölçüye yeniden tıklayın").is_visible())

    def _olcuyu_ac(self, desen=r"^Ölçü KUYU DİBİ"):
        olcu = self.sayfa.get_by_role("button", name=re.compile(desen)).first
        olcu.scroll_into_view_if_needed()
        olcu.focus()
        self.sayfa.keyboard.press("Enter")
        kutu = self.sayfa.get_by_role("dialog", name=re.compile(r"^Ölçü "))
        kutu.get_by_role("button", name="Uygula").wait_for()
        return olcu, kutu

    def test_olcu_kutusu_degisen_girdiyle_uygulanmaz(self):
        """22 Eki ( dış inceleme ):  kutu açıkken başka bir girdi ( kuyu genişliği )
        değişti, kutu eski girdiyle hesaplayıp "doğrulandı" dedi, yazılan değer
        yeni girdinin üstüne binip başka bir ölçü kurdu.  Artık "Uygula" kapanır;
        aynı ölçüye yeniden tıklamak güncel girdiyle açar.  Yanıt yoldayken kutu
        kapanırsa geç gelen değişiklik projeye yazılmaz."""
        self.ornek_projeyi_ac()
        _olcu, kutu = self._olcuyu_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2220")
        self.iz.sakin()
        self.assertTrue(kutu.get_by_role("button", name="Uygula").is_disabled())
        self.assertIn("Girdiler kutu açıldıktan sonra değişti", kutu.inner_text())
        #  Yeniden tıklama güncel girdiyle yeni kutu açar
        olcu, kutu = self._olcuyu_ac()
        self.assertTrue(kutu.get_by_role("button", name="Uygula").is_enabled())
        self.assertNotIn("Girdiler kutu açıldıktan sonra değişti", kutu.inner_text())

        #  Yanıt yoldayken kutu kapanır:  geç yanıt yazılmaz
        once = self.kayitli_asansorler()
        eski = int(re.search(r"\d+", olcu.get_attribute("aria-label").replace(".", "")).group())
        tutulan = []
        self.sayfa.route("**/api/uygulama/olcu_degistir", lambda r: tutulan.append(r))
        try:
            kutu.get_by_role("textbox").fill(str(eski + 50))
            kutu.get_by_role("button", name="Uygula").click()
            for _ in range(100):
                if tutulan:
                    break
                self.sayfa.wait_for_timeout(100)
            self.assertTrue(tutulan, "ölçü isteği gitmedi")
            self.sayfa.keyboard.press("Escape")
            kutu.wait_for(state="detached")
        finally:
            for r in tutulan:
                r.continue_()
            self.sayfa.unroute("**/api/uygulama/olcu_degistir")
        self.sayfa.wait_for_timeout(1500)
        self.assertEqual(self.kayitli_asansorler(), once)

    def test_olcu_hedefi_guncel_cizimde_dogrulanir_ve_sonradan_gecersizlesir(self):
        """Kuyu değişince 420 yerine 430 üreten senaryo; onay yalnız yeni
        çizim gelince görünür ve sonraki girdi değişiminde kaldırılır."""
        self.ornek_projeyi_ac()
        olcu = self.sayfa.locator('figure[data-cizim="kuyu_plani"] .olcu[data-olcu="4"]')
        self.assertEqual(olcu.get_attribute("aria-label"), "Ölçü 425")

        def ac():
            olcu.scroll_into_view_if_needed()
            olcu.focus()
            self.sayfa.keyboard.press("Enter")
            kutu = self.sayfa.get_by_role("dialog", name=re.compile(r"^Ölçü "))
            kutu.get_by_role("button", name="Uygula", exact=True).wait_for()
            return kutu

        kutu = ac()
        self.alan_kutusu("kuyu_genisligi").fill("2220")
        self.iz.sakin()
        self.assertTrue(kutu.get_by_role("button", name="Uygula", exact=True).is_disabled())
        kutu = ac()
        kutu.get_by_role("textbox").fill("420")
        tutulan = []
        self.sayfa.route("**/api/uygulama/cizimler", lambda r: tutulan.append(r))
        try:
            with self.sayfa.expect_response(lambda r: r.url.endswith("/api/uygulama/olcu_degistir")) as yanit:
                kutu.get_by_role("button", name="Uygula", exact=True).click()
            d = yanit.value.json()
            self.assertTrue(d["aktif"], d)
            if d.get("uyarilar"):
                kutu.get_by_role("button", name="Yine de uygula", exact=True).click()
            kutu.get_by_text("Değişiklik uygulandı; çizim güncelleniyor.").wait_for()
            self.assertNotIn("Çizim yeniden kuruldu", kutu.inner_text())
        finally:
            self.sayfa.unroute("**/api/uygulama/cizimler")
            for rota in tutulan:
                rota.continue_()
        self.iz.sakin()
        self.assertEqual(olcu.get_attribute("aria-label"), "Ölçü 420")
        self.assertIn("ölçü 420 mm", kutu.inner_text())
        self.alan_kutusu("kuyu_genisligi").fill("2240")
        self.iz.sakin()
        self.assertIn("Girdiler kutu açıldıktan sonra değişti", kutu.inner_text())
        self.assertNotIn("Çizim yeniden kuruldu", kutu.inner_text())

    def test_yakinda_net_ve_olcu_kutusu_tuvale_sigar(self):
        """20 Eki ( kullanıcı:  "ölçüyü belirleyen kutucuğun tamamı görünmüyor,
        çizim ekranı bulanıklaşıyor" ):  yakınlaşma durunca levhanın CSS ölçeği
        1'e döner, çizimler kendi boyunda yeniden çizilir ( Safari büyütülmüş
        resim gösteriyordu );  kaynağı çok ölçünün kutusu kısa pencerede de
        tuvale, araç şeridinin altına sığar, listesi kayar, "Uygula" görünür."""
        self.sayfa.set_viewport_size({"width": 1280, "height": 560})
        self.ornek_projeyi_ac()
        plan = self.sayfa.locator('figure[data-cizim="kuyu_plani"]').bounding_box()
        self.sayfa.mouse.move(plan["x"] + plan["width"] / 2, plan["y"] + plan["height"] / 2)
        for _ in range(12):
            self.sayfa.mouse.wheel(0, -120)
        self.sayfa.wait_for_timeout(500)
        levha = "document.querySelector('figure[data-cizim]').parentElement"
        self.assertTrue(self.sayfa.evaluate(f"{levha}.style.transform").endswith("scale(1)"))
        en = self.sayfa.evaluate(
            "(() => { const f = document.querySelector('figure[data-cizim=\"kuyu_plani\"]');"
            "  return [parseFloat(f.style.width), f.getBoundingClientRect().width] })()"
        )
        self.assertAlmostEqual(en[0], en[1], delta=1.0)
        self.sayfa.get_by_role("button", name="Sığdır").click()
        self.sayfa.wait_for_timeout(300)
        #  Kaynağı en az 6 olan bir kuyu planı ölçüsü
        tuval = self.sayfa.locator(".bg-tuval").bounding_box()
        olculer = self.sayfa.locator('figure[data-cizim="kuyu_plani"] .olcu')
        kutu = self.sayfa.get_by_role("dialog", name=re.compile(r"^Ölçü "))
        for j in range(olculer.count()):
            olculer.nth(j).focus()
            self.sayfa.keyboard.press("Enter")
            kutu.get_by_role("radiogroup").wait_for()
            if kutu.get_by_role("radio").count() >= 6:
                break
            self.sayfa.keyboard.press("Escape")
        else:
            self.fail("kaynağı 6'dan çok ölçü yok")
        self.sayfa.wait_for_timeout(300)
        k = kutu.bounding_box()
        self.assertGreaterEqual(k["y"], tuval["y"] + 60)
        self.assertLessEqual(k["y"] + k["height"], tuval["y"] + tuval["height"])
        self.assertTrue(kutu.get_by_role("button", name="Uygula").is_visible())
        liste = kutu.get_by_role("radiogroup")
        self.assertEqual(liste.evaluate("u => getComputedStyle(u).overflowY"), "auto")

    def test_parca_adi_ve_vurgusu(self):
        """Parçanın üstüne gelince adı yazar ( sunucunun data-ad'ı ) ve o parçanın
        bütün öğeleri vurgulanır;  fare çıkınca ikisi de kalkar."""
        self.ornek_projeyi_ac()
        ray = self.sayfa.locator('figure[data-cizim="kuyu_plani"] [data-parca^="kabin_ray-"]').first
        kutu = ray.bounding_box()
        self.sayfa.mouse.move(kutu["x"] + kutu["width"] / 2, kutu["y"] + kutu["height"] / 2)
        ipucu = self.sayfa.get_by_role("tooltip")
        ipucu.wait_for()
        #  Vurgulanan TEK parça ( bütün öğeleri ) ve ipucu onun adı — üst üste
        #  gelenlerden en küçüğü:  rayın ortasında ray tırnağı olabilir
        vurgulu = self.sayfa.locator(".parca-ustunde")
        self.assertGreater(vurgulu.count(), 0)
        kimlikler = {vurgulu.nth(j).get_attribute("data-parca") for j in range(vurgulu.count())}
        self.assertEqual(len(kimlikler), 1, kimlikler)
        self.assertEqual(ipucu.inner_text().strip(), vurgulu.first.get_attribute("data-ad"))
        self.sayfa.mouse.move(1, 1)
        ipucu.wait_for(state="hidden")
        self.assertEqual(vurgulu.count(), 0)

    # ------------------------------------------------------------ 7 sorunlu çizim
    def test_sorunlu_cizim_ekranda_parcasi_kirmizi(self):
        """Kuyu 2200 → 2300:  sol boşluk 500'ü aşar, korkuluk 1,10 m olur ve
        tavana sığmaz ( 19 Eki ölçümü ).  Çizim yine gelir;  sorunun parçaları
        kırmızı;  soruna tıklayınca tuval o çizimde parçaya yakınlaşır ( bütün
        kesit sığınca tepedeki korkuluk okunmuyordu );  düzelince işaret kalkar."""
        self.ornek_projeyi_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        istek, cizim = self.iz.son("/api/uygulama/cizimler")
        self.assertEqual(istek["asansorler"][0]["kuyu_genisligi"], "2300")
        self.assertFalse(cizim["aktif"])
        self.assertEqual(self.sayfa.locator("figure[data-cizim]").count(), len(cizim["cizimler"]))
        kart = self.sayfa.get_by_role("alert")
        self.assertIn("Çizim uygun değil", kart.inner_text())
        (sorun,) = cizim["sorunlar"]
        self.assertTrue(sorun["parcalar"])
        kirmizi = self.sayfa.locator(".parca-sorunlu")
        self.assertGreater(kirmizi.count(), 0)
        adlar = {kirmizi.nth(j).get_attribute("data-ad") for j in range(kirmizi.count())}
        self.assertEqual(adlar, set(sorun["parcalar"]))

        kart.get_by_role("button", name=sorun["metin"]).click()
        secili = self.sayfa.locator(f'figure[data-cizim="{sorun["cizim"]}"] .parca-sorun-secili')
        secili.first.wait_for(state="attached")
        self.sayfa.wait_for_timeout(400)
        tuval = self.sayfa.locator(".bg-tuval").bounding_box()
        #  Görünür öğeler ( boyutsuz öğenin kutusu yok )
        kutular = [
            k
            for j in range(secili.count())
            if (k := secili.nth(j).bounding_box()) and (k["width"] or k["height"])
        ]
        self.assertTrue(kutular)
        ust = min(k["y"] for k in kutular)
        alt = max(k["y"] + k["height"] for k in kutular)
        #  Parçalar tuvalin içinde ve okunacak boyda
        self.assertGreaterEqual(ust, tuval["y"])
        self.assertLessEqual(alt, tuval["y"] + tuval["height"])
        self.assertGreater(alt - ust, 80, kutular)
        #  Yakınlaştı ( hepsi sığdığındaki görünümden büyük ) — A-A'ya gidip bütün
        #  kuyuyu sığdırınca %63'e uzaklaşıyordu
        arac = self.sayfa.locator("[data-tuval-arac]").first.inner_text()
        self.assertGreater(int(re.search(r"(\d+)%", arac).group(1)), 100, arac)

        #  Açılıştaki girdiye dönüş:  yanıt önbellekten ( istek gitmeyebilir ) — ekrana bakılır
        self.alan_kutusu("kuyu_genisligi").fill("2200")
        self.sayfa.get_by_role("alert").wait_for(state="detached")
        self.assertEqual(self.sayfa.locator(".parca-sorunlu, .parca-sorun-secili").count(), 0)

    def test_duzeltme_oner_ve_uygula(self):
        """Kuyu 2200 → 2300 ( korkuluk tavana sığmaz ):  düzeltmeler gelir —
        kuyu genişliğinin sınırı 2230 ( son değişiklik:  ön yüz son temiz
        girdiyi gönderir ) ve son kat 4515 ( türev );  "Uygula" kutuya yazar,
        sorun kalkar ( uclar/care_uclari.py )."""
        self.ornek_projeyi_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        kart = self.sayfa.get_by_role("alert")
        with self.sayfa.expect_response(
            lambda r: r.url.endswith("/api/uygulama/care"), timeout=30_000
        ) as yanit:
            kart.get_by_role("button", name="Düzeltme öner").click()
        d = yanit.value.json()
        self.assertTrue(d["aktif"], d)
        oneriler = {o["anahtar"]: o["yeni"] for c in d["careler"] for o in c["oneriler"]}
        self.assertEqual((oneriler["kuyu_genisligi"], oneriler["son_kat_yuksekligi"]), (2230, 4515))
        liste = kart.get_by_role("list", name="Düzeltmeler")
        liste.wait_for()
        self.assertIn("bina ölçüsü", liste.inner_text())
        kart.get_by_role("button", name=re.compile(r"^Kuyu genişliği 2\.230 yap$")).click()
        self.sayfa.get_by_role("alert").wait_for(state="detached")
        self.assertEqual(self.alan_kutusu("kuyu_genisligi").input_value(), "2230")
        istek, cizim = self.iz.son("/api/uygulama/cizimler")
        self.assertEqual(istek["asansorler"][0]["kuyu_genisligi"], "2230")
        self.assertTrue(cizim["aktif"], cizim.get("hata"))

    def test_duzeltme_asansorune_yazilir(self):
        """İkiz asansörler ( eklenen asansör 1. asansörün kopyası ):  sorunun
        metni ikisinde aynı.  1.'nin düzeltmeleri 2.'nin kartında görünmez —
        istek bütün asansörleri taşır, sekme değişince aynı kalıyordu;  "Uygula"
        1. için bulunan değeri 2.'ye yazıyordu ( 20 Eki ).  2.'nin düzeltmeleri
        kendisinin:  hiç temiz çizimi olmadığından son değişikliğin sınırı
        ( kuyu 2.230 ) yok, türevden son kat 4.515 var;  yalnız 2.'ye yazılır."""
        self.ornek_projeyi_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.iz.sakin()
        birinci, ikinci = self.sekmeler().nth(0), self.sekmeler().nth(1)
        birinci.click()
        self.iz.sakin()

        def care_iste():
            kart = self.sayfa.get_by_role("alert")
            with self.sayfa.expect_response(
                lambda r: r.url.endswith("/api/uygulama/care"), timeout=30_000
            ) as yanit:
                kart.get_by_role("button", name="Düzeltme öner").click()
            kart.get_by_role("list", name="Düzeltmeler").wait_for()
            return yanit.value.request.post_data_json["asansor"], kart

        self.assertEqual(care_iste()[0], 0)
        ikinci.click()
        self.iz.sakin()
        kart = self.sayfa.get_by_role("alert")
        self.assertIn("Korkuluk – kuyu tavanı", kart.inner_text())
        self.assertEqual(kart.get_by_role("list", name="Düzeltmeler").count(), 0)
        self.assertEqual(kart.get_by_role("button", name="Yeniden ara").count(), 0)

        asansor, kart = care_iste()
        self.assertEqual(asansor, 1)
        self.assertEqual(
            kart.get_by_role("button", name=re.compile(r"^Kuyu genişliği 2\.230 yap$")).count(), 0
        )
        son_kat = re.escape(self.ad("son_kat_yuksekligi"))
        kart.get_by_role("button", name=re.compile(rf"^{son_kat} 4\.515 yap$")).click()
        self.sayfa.get_by_role("alert").wait_for(state="detached")
        self.assertEqual(
            [(a.get("kuyu_genisligi"), a.get("son_kat_yuksekligi")) for a in self.kayitli_asansorler()],
            [("2300", "4250"), ("2300", "4515")],
        )

    def test_duzeltme_degisen_girdiyle_uygulanmaz(self):
        """24 Eki ( dış inceleme ):  girdi değişince yeni çizim gelene kadar eski
        çizimin düzeltmeleri kartta kalıyor, "Uygula" eski girdide sınanmış değeri
        yeni girdinin üstüne yazıyordu.  Yeni çizim beklenirken ne düzeltmeler ne
        arama düğmesi görünür;  girdi ekrandaki çizimin girdisine dönünce aynı
        girdinin sınanmış düzeltmeleri geri gelir."""
        self.ornek_projeyi_ac()
        kuyu = self.alan_kutusu("kuyu_genisligi")
        kuyu.fill("2300")
        self.iz.sakin()
        kart = self.sayfa.get_by_role("alert")
        with self.sayfa.expect_response(lambda r: r.url.endswith("/api/uygulama/care"), timeout=30_000):
            kart.get_by_role("button", name="Düzeltme öner").click()
        liste = kart.get_by_role("list", name="Düzeltmeler")
        liste.wait_for()
        uygula = kart.get_by_role("button", name=re.compile(r" yap$"))
        arama = kart.get_by_role("button", name=re.compile(r"^(Düzeltme öner|Yeniden ara)$"))
        self.assertGreater(uygula.count(), 0)
        tutulan = []
        self.sayfa.route("**/api/uygulama/cizimler", lambda r: tutulan.append(r))
        try:
            #  Girdi değişir, yeni çizim yolda tutulur:  ekranda eski çizim ve sorunu
            kuyu.fill("2310")
            for _ in range(100):
                if tutulan:
                    break
                self.sayfa.wait_for_timeout(100)
            self.assertTrue(tutulan, "çizim isteği gitmedi")
            self.assertIn("Korkuluk – kuyu tavanı", kart.inner_text())
            self.assertEqual((liste.count(), uygula.count(), arama.count()), (0, 0, 0))
            #  Ekrandaki çizimin girdisine dönüş:  onun düzeltmeleri yine geçerli
            kuyu.fill("2300")
            liste.wait_for()
            self.assertGreater(uygula.count(), 0)
        finally:
            for r in tutulan:
                r.continue_()
            self.sayfa.unroute("**/api/uygulama/cizimler")
        self.iz.sakin()
        self.assertEqual(self.kayitli_asansorler()[0].get("kuyu_genisligi"), "2300")

    # ------------------------------------------------------------ 5 teslim
    def test_teslim_onaysiz_kapali_onayli_paket_iner(self):
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim = self.sayfa.get_by_role("dialog", name="Teslim")
        #  Paketin içeriğinde elektrik projesi de yazar ( 23 Eki:  pakette vardı, listede yoktu );
        #  tam eşleşme:  çekmecenin açıklaması da "elektrik projesi" der
        teslim.get_by_text("Elektrik projesi", exact=True).wait_for()
        self.assertIn("asansör başına bir A3 sayfa", teslim.inner_text())
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

    def test_teslim_sorunlu_cizimde_paket_kapali_hesap_pdf_acik(self):
        self.ornek_projeyi_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim = self.sayfa.get_by_role("dialog", name="Teslim")
        teslim.get_by_text(re.compile(r"Çizimde 1 sorun var")).wait_for()
        teslim.get_by_role("checkbox").check()
        self.assertTrue(teslim.get_by_role("button", name=re.compile("Paketi indir")).is_disabled())
        self.assertTrue(teslim.get_by_role("button", name="Yalnız hesap PDF'i").is_enabled())

    def test_reddedilen_asansor_ekrani_cokertmez_teslimi_kapatir(self):
        """22 Eki ( dış inceleme ):  ikinci asansöre dar kuyu ( 1000 ) girilince
        yanıt yine aktif, reddedilenin bölümleri yok — ekran olmayan listeyi
        okuyup çöküyordu, yenilemek de kurtarmıyordu ( proje kayıtlı ).  Artık
        sebebi görünür, teslim kapanır;  yenilenen sayfa açılır."""
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.iz.sakin()
        self.alan_kutusu("kuyu_genisligi").fill("1000")
        _istek, hesap = self.iz.son("/api/uygulama/coklu")
        self.assertTrue(hesap["aktif"])
        self.assertFalse(hesap["asansorler"][1]["aktif"])
        self.assertIn("2 nolu asansör", self.sayfa.get_by_role("alert").inner_text())
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim = self.sayfa.get_by_role("dialog", name="Teslim")
        teslim.get_by_text(re.compile(r"2 nolu asansör hesaplanamadı")).wait_for()
        teslim.get_by_role("checkbox").check()
        self.assertTrue(teslim.get_by_role("button", name=re.compile("Paketi indir")).is_disabled())
        #  Kayıtlı proje yeniden açılır ( eskiden yenilemede de çöküyordu )
        self.sayfa.reload()
        self.iz.sakin()
        self.sayfa.get_by_role("button", name="Teslim").wait_for()

    def test_hesap_gorunumunde_duzelen_cizim_teslimi_kapatmaz(self):
        """22 Eki ( dış inceleme ):  çizimde sorun varken hesap görünümüne geçilip
        girdi düzeltildi;  hesap görünümünde çizim istenmediği için eski sorunlu
        çizim teslimi kapatıyordu.  Teslim açılınca son girdinin çizimi istenir."""
        self.ornek_projeyi_ac()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.sayfa.get_by_role("radio", name="Hesap").click()
        self.iz.sakin()
        self.alan_kutusu("kuyu_genisligi").fill("2200")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim = self.sayfa.get_by_role("dialog", name="Teslim")
        self.iz.sakin()
        self.assertNotIn("Çizimde 1 sorun var", teslim.inner_text())
        teslim.get_by_role("checkbox").check()
        self.assertTrue(teslim.get_by_role("button", name=re.compile("Paketi indir")).is_enabled())
        #  Ters yön:  hesap görünümünde bozulan çizim teslimde yakalanır
        self.sayfa.keyboard.press("Escape")
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name="Teslim").click()
        teslim.get_by_text(re.compile(r"Çizimde 1 sorun var")).wait_for()
        self.assertTrue(teslim.get_by_role("button", name=re.compile("Paketi indir")).is_disabled())

    # ------------------------------------------------------------ 8 sunucuya ulaşılamazsa
    def test_baslangic_verisi_gelmezse_ekran_soyler_yeniden_dener(self):
        """24 Eki ( dış inceleme ):  avan ekranı /api/secenekler düşünce hata
        göstermeden "Yükleniyor"da kalıyordu;  ofis standardı ve tablolar da
        ( /api/uygulama/alanlar ).  Ulaşılamadığı söylenir;  "Yeniden dene"
        sunucu dönünce ekranı açar."""
        for adres, uc, acilan in (
            ("/avan/trafik", "**/api/secenekler", self.sayfa.get_by_role("navigation", name="Adımlar")),
            (
                "/ofis-standardi",
                "**/api/uygulama/alanlar",
                self.sayfa.get_by_role("heading", name="Ofis standardı"),
            ),
            ("/tablolar", "**/api/uygulama/alanlar", self.sayfa.get_by_role("heading", name="Tablolar")),
        ):
            self.sayfa.route(uc, lambda r: r.fulfill(status=503, body="kapalı"))
            self.sayfa.goto(self.url + adres)
            hata = self.sayfa.get_by_role("alert")
            hata.get_by_role("button", name="Yeniden dene").wait_for(timeout=15_000)
            self.assertIn("Sunucuya ulaşılamadı", hata.inner_text(), adres)
            self.sayfa.unroute(uc)
            hata.get_by_role("button", name="Yeniden dene").click()
            acilan.wait_for()
            self.assertEqual(hata.count(), 0, adres)
            self.iz.sakin()
        #  Tarayıcı düşen isteği konsola yazar ( beklenen )
        self.iz.hatalar = [h for h in self.iz.hatalar if "503" not in h]

    def _bekle(self, kosul, ileti, sure=15):
        son = time.time() + sure
        while not kosul():
            self.assertLess(time.time(), son, ileti)
            self.sayfa.wait_for_timeout(100)

    def test_avan_trafik_dusunce_proje_inmez(self):
        """24 Eki ( sınıf taraması ):  /api/trafik düşünce sonuç silinip köprü
        kalmıyordu, "Projeyi indir" açıktı — paket asansörsüz avan hesabıyla
        ( yalnız topraklama ) iniyordu;  avan adımı "Önce trafik hesabı" diyordu.
        İndirme kapanır, sebep söylenir, "Yeniden dene" sunucu dönünce açar."""
        self.sayfa.goto(self.url + "/avan/trafik")
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
        self.sayfa.goto(self.url + "/avan/trafik")
        self.iz.son("/api/avan")
        indir = self.sayfa.get_by_role("button", name="Projeyi indir")
        self._bekle(indir.is_enabled, "örnek avan projesi indirilemiyor")

        self.sayfa.route("**/api/trafik", lambda r: r.fulfill(status=503, body="kapalı"))
        self.sayfa.get_by_label("③ Kat sayısı N").fill("11")
        serit = self.sayfa.get_by_role("alert").filter(has_text="Sunucuya ulaşılamadı")
        serit.get_by_role("button", name="Yeniden dene").wait_for(timeout=15_000)
        self.assertTrue(indir.is_disabled())
        self.sayfa.get_by_role("link", name=re.compile("Avan hesapları")).click()
        self.sayfa.get_by_text("Trafik hesabı alınamadı").wait_for()
        self.assertEqual(self.sayfa.get_by_text("Önce trafik hesabı").count(), 0)

        self.sayfa.unroute("**/api/trafik")
        serit.get_by_role("button", name="Yeniden dene").click()
        serit.wait_for(state="detached")
        self._bekle(indir.is_enabled, "sunucu dönünce indirme açılmadı")
        istek, _avan = self.iz.son("/api/avan")
        self.assertTrue(any(a.get("aktif") for a in istek["girdiler"]["asansorler"]), istek)
        self.iz.hatalar = [h for h in self.iz.hatalar if "503" not in h]

    def test_baglanti_kopunca_yeniden_dene_gunceller(self):
        """24 Eki ( sınıf taraması ):  hesap / çizim isteği düşünce kart "bağlantı
        gelince kendiliğinden güncellenir" diyordu;  istek yalnız tarayıcının
        bağlantısı kopup gelince yeniden gider — sunucu yeniden başlayınca ekran
        girdi değişene kadar takılı kalıyordu.  "Yeniden dene" ister."""
        self.ornek_projeyi_ac()
        for uc in ("**/api/uygulama/coklu", "**/api/uygulama/cizimler"):
            self.sayfa.route(uc, lambda r: r.fulfill(status=503, body="kapalı"))
        self.alan_kutusu("kuyu_genisligi").fill("2210")
        kart = self.sayfa.get_by_role("alert").filter(has_text="Bağlantı yok")
        kart.get_by_role("button", name="Yeniden dene").wait_for(timeout=15_000)
        self.assertNotIn("kendiliğinden", kart.inner_text())

        for uc in ("**/api/uygulama/coklu", "**/api/uygulama/cizimler"):
            self.sayfa.unroute(uc)
        kart.get_by_role("button", name="Yeniden dene").click()
        kart.wait_for(state="detached")
        istek, hesap = self.iz.son("/api/uygulama/coklu")
        self.assertEqual(istek["asansorler"][0]["kuyu_genisligi"], "2210")
        self.assertTrue(hesap["aktif"], hesap.get("hata"))
        self.iz.hatalar = [h for h in self.iz.hatalar if "503" not in h]

    def test_kapak_onizlemesi_hata_yanitini_soyler(self):
        """24 Eki ( sınıf taraması ):  ağ geçidinin JSON olmayan hatası ( 502 )
        PDF diye çizilmeye çalışılıyor, pdf.js'in reddi yutuluyor, önizleme
        sonsuza dek dönüyordu.  Hata ve okunamayan PDF söylenir."""
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: 'Kapak deneme'}}))"""
        )
        uc = "**/api/indir/kapak-pdf"
        #  Yanıt başarılı ama PDF değil:  pdf.js okuyamaz
        self.sayfa.route(uc, lambda r: r.fulfill(status=200, content_type="application/pdf", body="bozuk"))
        self.sayfa.goto(self.url + "/avan/kapak")
        self.sayfa.get_by_role("alert").filter(has_text="Önizleme açılamadı").wait_for(timeout=15_000)
        self.sayfa.unroute(uc)

        #  Ağ geçidinin HTML hatası:  sebebi ve "Yeniden dene"
        self.sayfa.route(
            uc, lambda r: r.fulfill(status=502, content_type="text/html", body="<html>502</html>")
        )
        self.sayfa.get_by_label("Kapak başlığı").fill("Kapak deneme 2")
        hata = self.sayfa.get_by_role("alert").filter(has_text="Sunucu yanıt vermedi ( 502 )")
        hata.get_by_role("button", name="Yeniden dene").wait_for(timeout=15_000)
        self.sayfa.unroute(uc)
        hata.get_by_role("button", name="Yeniden dene").click()
        hata.wait_for(state="detached")
        main = self.sayfa.get_by_role("main")
        self._bekle(lambda: main.locator(".animate-spin").count() == 0, "önizleme çizilmedi")
        self.assertEqual(self.sayfa.get_by_role("alert").count(), 0)
        self.iz.hatalar = [h for h in self.iz.hatalar if "502" not in h]

    def _avan_kapagi(self, baslik="Kapak deneme"):
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """b => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: b}}))""",
            baslik,
        )
        self.sayfa.goto(self.url + "/avan/kapak")

    def test_kapak_onizlemesi_iscisini_kapatir(self):
        """24 Eki ( Codex ):  pdf.js her önizlemede yeni bir işçi ( Web Worker ) açıyor,
        kapatmıyordu — altı güncellemeden sonra altısı da çalışıyordu, kapaktan
        çıkınca da kapanmıyordu.  Sayfa çizilince belge işçisiyle kapanır."""
        self.sayfa.add_init_script(
            """(() => {
                const W = window.Worker;
                window.__isci = { acilan: 0, kapanan: 0 };
                window.Worker = class extends W {
                    constructor(...a) { super(...a); window.__isci.acilan++; }
                    terminate() { window.__isci.kapanan++; return super.terminate(); }
                };
            })()"""
        )
        self._avan_kapagi()
        isci = lambda: self.sayfa.evaluate("window.__isci")
        for i in range(1, 4):
            if i > 1:
                self.sayfa.get_by_label("Kapak başlığı").fill(f"Kapak deneme {i}")
            self._bekle(lambda n=i: isci()["acilan"] >= n, f"{i}. önizleme gelmedi")
            self._bekle(
                lambda: isci()["acilan"] == isci()["kapanan"], f"önizlemenin işçisi kapanmadı:  {isci()}"
            )
        self.assertEqual(self.sayfa.get_by_role("main").locator(".animate-spin").count(), 0)
        self.assertEqual(self.sayfa.get_by_role("alert").count(), 0)
        #  Kapaktan çıkınca açık işçi kalmaz
        self.sayfa.get_by_role("link", name=re.compile("Trafik hesabı")).click()
        self.sayfa.wait_for_url(re.compile(r"/avan/trafik$"))
        s = isci()
        self.assertEqual(s["acilan"], s["kapanan"], s)

    def test_indirme_yarida_kopunca_soyler(self):
        """24 Eki ( Codex ):  dosya inerken bağlantı kopunca ( gövde yarıda ) indirme
        reddediliyor, düğme sessizce eski hâline dönüyordu — dosya yok, ileti yok.
        Yanıtın ilk parçası gelip akış koparılır ( Playwright'ın route'u gövdeyi
        yarıda kesemez )."""
        self._avan_kapagi()
        self._bekle(
            lambda: self.sayfa.get_by_role("main").locator(".animate-spin").count() == 0, "önizleme çizilmedi"
        )
        self.sayfa.evaluate(
            """() => {
                const F = window.fetch.bind(window);
                window.fetch = async (u, o) => {
                    const r = await F(u, o);
                    if (!String(u).endsWith('/api/indir/kapak-pdf')) return r;
                    const okuyucu = r.body.getReader();
                    const akim = new ReadableStream({ async start(c) {
                        const { value } = await okuyucu.read();
                        if (value) c.enqueue(value);
                        c.error(new TypeError('network error'));
                    } });
                    return new Response(akim, { status: r.status, headers: r.headers });
                };
            }"""
        )
        inen = []
        self.sayfa.on("download", lambda d: inen.append(d))
        dugme = self.sayfa.get_by_role("button", name="PDF", exact=True)
        dugme.click()
        self.sayfa.get_by_text("Dosya inerken bağlantı koptu").wait_for(timeout=15_000)
        self.assertTrue(dugme.is_enabled())
        self.assertEqual(inen, [])

    def test_avan_trafik_sutunu_kaldirilinca_karti_da_gider(self):
        """24 Eki ( sınıf taraması ):  avan kartları trafiğin verdiği asansörlerin
        sırasıyladır;  2. sütun kaldırılınca kartı yerinde kalıyor, 3. sütunun
        asansörü 2.'nin kabin ve kuyu ölçüleriyle hesaplanıyordu."""
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut', bina_yuksekligi: '30', yapi_yuksekligi: '31', N: '10', h: '3',
                         hizli1: '20', hizli2: '2'},
                ekNufus: [],
                trafikAsansorleri: [
                    {P: '8', kapi_genisligi: '800', kapi_tipi: 'Teleskopik Otomatik'},
                    {P: '13', kapi_genisligi: '900', kapi_tipi: 'Teleskopik Otomatik'},
                    {P: '10', kapi_genisligi: '900', kapi_tipi: 'Teleskopik Otomatik'}],
                ortak: {mk_yok: 'true', temel_a: '20', temel_b: '15'},
                avanAsansorleri: [
                    {tanim: 'A', Hk: '34', kuyu_genisligi: '1600', kabin_boyu: '1250', kabin_genisligi: '1000'},
                    {tanim: 'B', Hk: '34', kuyu_genisligi: '2000', kabin_boyu: '1500', kabin_genisligi: '1400'},
                    {tanim: 'C', Hk: '34', kuyu_genisligi: '1800', kabin_boyu: '1400', kabin_genisligi: '1100'},
                    {}],
                kapak: {project_title: 'Sütun deneme'}}))"""
        )
        self.sayfa.goto(self.url + "/avan/trafik")
        kart = lambda istek: [
            (a["tanim"], a["kapasite"], a["kabin_genisligi"])
            for a in istek["girdiler"]["asansorler"]
            if a["aktif"]
        ]
        istek, _avan = self.iz.son("/api/avan")
        self.assertEqual(kart(istek), [("A", "8", "1000"), ("B", "13", "1400"), ("C", "10", "1100")])
        self.sayfa.get_by_role("button", name="2. asansörü kaldır").click()
        istek, avan = self.iz.son("/api/avan")
        self.assertEqual(kart(istek), [("A", "8", "1000"), ("C", "10", "1100")])
        self.assertTrue(all(a["aktif"] for a in avan["asansorler"][:2]), avan)

    def test_avan_sonradan_secilen_kapasite_kartlari_kaydirmaz(self):
        """Sınıf taraması ( rastgele işlem dizisi ):  yeni avan projesinde 1. sütunun
        kapasitesi seçili gelmez.  2. sütunun kapasitesi seçilip 1. kart ( onun
        asansörü ) doldurulduktan sonra 1. sütuna kapasite seçilince kart kime gider?"""
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut', bina_yuksekligi: '30', yapi_yuksekligi: '31', N: '10', h: '3',
                         hizli1: '20', hizli2: '2'},
                ekNufus: [],
                trafikAsansorleri: [{kapi_genisligi: '800', kapi_tipi: 'Teleskopik Otomatik'},
                                    {P: '13', kapi_genisligi: '900', kapi_tipi: 'Teleskopik Otomatik'}],
                ortak: {mk_yok: 'true', temel_a: '20', temel_b: '15'},
                avanAsansorleri: [{tanim: 'B', Hk: '34', kuyu_genisligi: '2000', kabin_boyu: '1500',
                                   kabin_genisligi: '1400'}, {}, {}, {}],
                kapak: {project_title: 'Kapasite deneme'}}))"""
        )
        self.sayfa.goto(self.url + "/avan/trafik")
        istek, _avan = self.iz.son("/api/avan")
        aktif = [a for a in istek["girdiler"]["asansorler"] if a["aktif"]]
        self.assertEqual([(a.get("tanim"), a["kapasite"]) for a in aktif][:1], [("B", "13")])
        self.sayfa.get_by_label("1. asansör ⑧ Kapasite").click()
        self.sayfa.get_by_role("option", name="8 kişi", exact=True).click()
        istek, _avan = self.iz.son("/api/avan")
        aktif = {a["kapasite"]: a.get("tanim") for a in istek["girdiler"]["asansorler"] if a["aktif"]}
        self.assertEqual(aktif.get("13"), "B", f"13 kişilik asansörün kartı kaydı:  {aktif}")

    def test_duzeltmenin_son_temiz_girdisi_kendi_asansorunun(self):
        """Düzeltme öner son değişikliği asansörün SON TEMİZ girdisine göre arar;
        o girdi asansörün sırasıyla tutuluyor.  1. asansör kaldırılınca 2.'nin
        isteğine 1.'nin girdisi gidiyor mu?"""
        self.ornek_projeyi_ac()
        self.sayfa.get_by_role("button", name="Asansör ekle").click()
        self.alan_kutusu("kuyu_derinligi").fill("2750")
        self.iz.sakin()
        self.alan_kutusu("kuyu_genisligi").fill("2300")
        self.iz.sakin()
        self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first.click()
        self.iz.sakin()
        with self.sayfa.expect_request(
            lambda r: r.url.endswith("/api/uygulama/care"), timeout=30_000
        ) as istek:
            self.sayfa.get_by_role("alert").get_by_role("button", name="Düzeltme öner").click()
        onceki = (json.loads(istek.value.post_data) or {}).get("onceki") or {}
        self.assertIn(
            (onceki.get("asansor") or {}).get("kuyu_derinligi"),
            ("2750", None),
            "kaldırılan 1. asansörün son temiz girdisi gitti",
        )

    def test_asansor_sayisi_degisince_cizim_eski_listeyle_istenmez(self):
        """Sınıf taraması ( sıra / bayat eşleşme ):  ekleme, kaldırma ve geri almadan
        sonra seçili sıra yeni listenindir;  gecikmeli istek 300 ms eski listeyle
        gidiyordu — eklemede sunucu sırayı kırpıp son asansörün çizimini, kaldırmada
        kaldırılanınkini döndürüyordu ( yoldaki hesap yanıtı da eski sırayla gelip
        kaldırılanın hükümlerini kalanın sekmesine koyabiliyordu )."""
        self.ornek_projeyi_ac()
        giden = []

        def dinle(r):
            if r.url.endswith("/api/uygulama/cizimler"):
                g = json.loads(r.post_data)
                giden.append((len(g["asansorler"]), g["asansor"]))

        self.sayfa.on("request", dinle)

        def dene(adim, dugme, sayi, gitmeli=None):
            giden.clear()
            dugme.click()
            self.iz.sakin()
            #  Aynı girdinin çizimi önbellekten gelir ( istek gitmeyebilir ):  eski listeyle giden olmamalı
            self.assertEqual([g for g in giden if g[0] != sayi], [], f"{adim}:  çizim eski listeyle istendi")
            if gitmeli:
                self.assertIn(gitmeli, giden, f"{adim}:  yeni listenin çizimi istenmedi")

        dene("ekleme", self.sayfa.get_by_role("button", name="Asansör ekle"), 2, (2, 1))
        #  Kalan asansör 1.'nin kopyası olmasın:  kaldırmadan sonraki istek önbellekte olmaz
        self.alan_kutusu("kuyu_derinligi").fill("2750")
        self.iz.sakin()
        kaldir = self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).first
        dene("kaldırma", kaldir, 1, (1, 0))
        dene("geri alma", self.sayfa.get_by_role("status").get_by_role("button", name="Geri al"), 2)

    # ------------------------------------------------------------ 9 arıza matrisi
    #  24 Eki ( sınıf taraması ):  sessiz hata yolları birer birer bulunuyordu.  Ekranın
    #  konuştuğu her uç × her arıza:  ekran bir şey söyler ( sonsuza dek dönmez, sayfa
    #  hatası yok ), arıza kalkınca düzelir.  Arıza fetch'in sarmalıyla ( Playwright'ın
    #  route'u gövdeyi yarıda kesemez );  sessionStorage '__ariza' = { yol , tur }
    #  sayfa yenilense de durur.  ret:  sunucunun gerçek reddinin biçimi ( main.py
    #  IstekBoyutu, 413 ) — iletisi ekranda görünmeli.
    ARIZA_BETIGI = """(() => {
        const F = window.fetch.bind(window);
        window.__ariza = 0;
        window.fetch = async (girdi, secenek) => {
            let a = null;
            try { a = JSON.parse(sessionStorage.getItem('__ariza') || 'null'); } catch {}
            const adres = typeof girdi === 'string' ? girdi : girdi.url;
            if (!a || !adres.includes(a.yol)) return F(girdi, secenek);
            window.__ariza++;
            const yanit = (govde, durum, tur) =>
                new Response(govde, { status: durum, headers: { 'Content-Type': tur } });
            if (a.tur === 'baglanti') throw new TypeError('Failed to fetch');
            if (a.tur === 'sayfa') return yanit('<html><body>502 Bad Gateway</body></html>', 502, 'text/html');
            if (a.tur === 'ret')
                return yanit(JSON.stringify({ aktif: false, hata: ['DENEME REDDİ'] }), 413, 'application/json');
            if (a.tur === 'bozuk') return yanit('<html>bozuk</html>', 200, 'application/json');
            const r = await F(girdi, secenek);
            const okuyucu = r.body.getReader();
            return new Response(new ReadableStream({ async start(c) {
                const { value } = await okuyucu.read();
                if (value) c.enqueue(value.slice(0, Math.max(1, value.length >> 1)));
                c.error(new TypeError('network error'));
            } }), { status: r.status, headers: r.headers });
        };
    })()"""
    #  Beş türün matrisi ~6–7 dk:  PR'da gerçek hata bulan iki tür koşar ( sunucunun
    #  reddi, yarıda kesilen yanıt );  beşi birden ARIZA_HEPSI=1 ile — Actions'ta elle
    #  başlatılan Denetim de beşini koşar ( ön yüzün sunucuyla konuşması değişince ).
    ARIZALAR = (
        ("baglanti", "sayfa", "ret", "bozuk", "kesik")
        if os.environ.get("ARIZA_HEPSI") == "1"
        else ("ret", "kesik")
    )
    #  Ekranın arızayı söylediği sözler ( "DENEME REDDİ":  sunucunun ret iletisi )
    ARIZA_SOZU = (
        "ulaşılamadı",
        "yanıt vermedi",
        "okunamadı",
        "koptu",
        "alınamadı",
        "açılamadı",
        "Bağlantı yok",
        "DENEME REDDİ",
    )

    def _ariza_kur(self, yol=None, tur=None):
        if not self.sayfa.url.startswith(self.url):
            return  # boş sayfada sessionStorage yok;  sayfa açılınca kurulur
        self.sayfa.evaluate(
            "a => a ? sessionStorage.setItem('__ariza', JSON.stringify(a)) : sessionStorage.removeItem('__ariza')",
            {"yol": yol, "tur": tur} if yol else None,
        )

    def _sozler(self):
        metin = self.sayfa.evaluate("document.body.innerText")
        return {s for s in self.ARIZA_SOZU if s in metin}

    def _arizalari_dene(self, ad, yol, hazirla, tetik, bulgular, duzelt=None, sure=15, get=False):
        """Her arıza türünde:  hazırla ( arızasız ) → arıza → tetik → ekran söyler mi →
        arıza kalkar → "Yeniden dene" ( yoksa duzelt, o da yoksa tetik ) → düzelir mi.
        duzelt=False:  düzelme denenmez ( paket gibi uzun istekler );  sure:  yanıtın
        en uzun süresi ( sn );  get:  gövdesiz istek — boyut reddi ( ret ) olmaz."""
        for i, tur in enumerate(self.ARIZALAR):
            if get and tur == "ret":
                continue
            on = f"{ad} · {tur}"
            self._ariza_kur()
            #  Önceki türde sayfa çöktüyse ( yönlendiricinin hata ekranı ) baştan açılır
            if getattr(self, "_cokmus", False):
                self.sayfa.reload()
                self.iz.sakin()
                self._cokmus = False
            hazirla(i)
            self.iz.sakin()
            once = self._sozler()
            h0 = len(self.iz.hatalar)
            self.sayfa.evaluate("window.__ariza = 0")
            self._ariza_kur(yol, tur)
            try:
                tetik(i)
            except Exception as e:  # noqa: BLE001 — bulgu olarak yazılır
                bulgular.append(f"{on}:  tetiklenemedi ( {str(e).splitlines()[0][:160]} )")
                continue
            yeni, son = set(), time.time() + sure
            while time.time() < son:
                yeni = self._sozler() - once
                if yeni:
                    break
                self.sayfa.wait_for_timeout(200)
            if not self.sayfa.evaluate("window.__ariza"):
                bulgular.append(f"{on}:  istek gitmedi ( tetik yanlış )")
            elif not yeni:
                donuyor = self.sayfa.locator(".animate-spin").count()
                bulgular.append(f"{on}:  ekran bir şey söylemedi{' — dönüp duruyor' if donuyor else ''}")
            elif tur == "ret" and "DENEME REDDİ" not in yeni:
                bulgular.append(
                    f"{on}:  sunucunun ret iletisi görünmedi ( ekranda:  {', '.join(sorted(yeni))} )"
                )
            hatalar = self.iz.hatalar[h0:]
            del self.iz.hatalar[h0:]
            if hatalar:
                bulgular.append(f"{on}:  sayfa / konsol hatası:  {[h[:200] for h in hatalar[:2]]}")
                self._cokmus = True
            self._ariza_kur()
            if not yeni or duzelt is False:
                continue
            dene = self.sayfa.get_by_role("button", name="Yeniden dene")
            try:
                if dene.count() and dene.first.is_visible():
                    dene.first.click()
                else:
                    (duzelt or tetik)(i)
            except Exception as e:  # noqa: BLE001
                bulgular.append(f"{on}:  düzeltilemedi ( {str(e).splitlines()[0][:160]} )")
                continue
            kalan, son = yeni, time.time() + max(20, sure)
            while time.time() < son:
                kalan = self._sozler() & yeni
                if not kalan:
                    break
                self.sayfa.wait_for_timeout(250)
            if kalan:
                bulgular.append(f"{on}:  arıza kalkınca düzelmedi ( ekranda:  {', '.join(sorted(kalan))} )")
            del self.iz.hatalar[h0:]

    def test_ariza_matrisi_uygulama(self):
        self.sayfa.add_init_script(self.ARIZA_BETIGI)
        b = []
        self.ornek_projeyi_ac()
        adres = self.sayfa.url

        def ac(i):
            self.sayfa.keyboard.press("Escape")
            if self.sayfa.url != adres or self._sozler():
                self.sayfa.goto(adres)
                self.iz.sakin()

        def kuyu(deger):
            return lambda i: self.alan_kutusu("kuyu_genisligi").fill(str(deger + 5 * i))

        def olcu(kaydir):
            def ac_(i):
                o = self.sayfa.get_by_role("button", name=re.compile(r"^Ölçü ")).nth(3 + 7 * i + kaydir)
                o.scroll_into_view_if_needed()
                o.focus()
                self.sayfa.keyboard.press("Enter")

            return ac_

        def olcu_kutusu(i):
            ac(i)
            #  Önceki türün değişikliğiyle çizim yenilenirken açılan kutu "ölçüye yeniden tıklayın" der
            self.iz.sakin()
            self._olcuyu_ac()

        def uygula(i):
            kutu = self.sayfa.get_by_role("dialog", name=re.compile(r"^Ölçü "))
            olcu_ = self.sayfa.get_by_role("button", name=re.compile(r"^Ölçü KUYU DİBİ")).first
            eski = int(re.search(r"\d+", olcu_.get_attribute("aria-label").replace(".", "")).group())
            kutu.get_by_role("textbox").fill(str(eski + 10 * (i + 1)))
            kutu.get_by_role("button", name="Uygula").click()

        def teslim(paket):
            def ac_(i):
                ac(i)
                self.alan_kutusu("kuyu_genisligi").fill("2200")
                self.iz.sakin()
                self.sayfa.get_by_role("button", name="Teslim").click()
                if paket:
                    self.sayfa.get_by_role("dialog", name="Teslim").get_by_role("checkbox").check()

            return ac_

        def sorunlu(i):
            ac(i)
            self.alan_kutusu("kuyu_genisligi").fill(str(2300 + i))
            self.iz.sakin()

        self._arizalari_dene(
            "form şeması", "/api/uygulama/alanlar", ac, lambda i: self.sayfa.reload(), b, get=True
        )
        self._arizalari_dene("hesap", "/api/uygulama/coklu", ac, kuyu(2205), b, duzelt=kuyu(2180))
        self._arizalari_dene("çizim", "/api/uygulama/cizimler", ac, kuyu(2207), b, duzelt=kuyu(2182))
        self._arizalari_dene("ölçü kaynağı", "/api/uygulama/olcu", ac, olcu(0), b, duzelt=olcu(1))
        self._arizalari_dene("ölçü değiştir", "/api/uygulama/olcu_degistir", olcu_kutusu, uygula, b)
        pdf = lambda i: self.sayfa.get_by_role("button", name="Yalnız hesap PDF'i").click()
        self._arizalari_dene("hesap PDF'i", "/api/indir/uygulama-pdf", teslim(False), pdf, b)
        paket = lambda i: self.sayfa.get_by_role("button", name=re.compile("Paketi indir")).click()
        self._arizalari_dene(
            "teslim paketi", "/api/indir/uygulama-dwg", teslim(True), paket, b, duzelt=False, sure=180
        )
        oner = lambda i: self.sayfa.get_by_role("alert").get_by_role("button", name="Düzeltme öner").click()
        self._arizalari_dene("düzeltme öner", "/api/uygulama/care", sorunlu, oner, b, sure=60)
        self.assertEqual(b, [], "\n" + "\n".join(b))

    def test_ariza_matrisi_avan(self):
        self.sayfa.add_init_script(self.ARIZA_BETIGI)
        b = []
        self.sayfa.goto(self.url + "/avan/trafik")
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

        def adim(yol):
            def h(i):
                if not self.sayfa.url.endswith(yol) or self._sozler():
                    self.sayfa.goto(self.url + yol)
                    self.iz.sakin()
                if yol.endswith("kapak"):
                    main = self.sayfa.get_by_role("main")
                    self._bekle(lambda: main.locator(".animate-spin").count() == 0, "önizleme çizilmedi", 30)

            return h

        def kutu(secici, deger):
            return lambda i: self.sayfa.locator(secici).fill(str(deger + i))

        pdf = lambda i: self.sayfa.get_by_role("button", name="PDF", exact=True).click()
        baslik = lambda i: self.sayfa.get_by_label("Kapak başlığı").fill(f"Avan deneme {i}")
        self._arizalari_dene(
            "seçenekler", "/api/secenekler", adim("/avan/trafik"), lambda i: self.sayfa.reload(), b, get=True
        )
        n = self.sayfa.get_by_label("③ Kat sayısı N")
        self._arizalari_dene(
            "trafik",
            "/api/trafik",
            adim("/avan/trafik"),
            lambda i: n.fill(str(11 + i)),
            b,
            duzelt=lambda i: n.fill(str(21 + i)),
        )
        self._arizalari_dene(
            "avan hesabı",
            "/api/avan",
            adim("/avan/hesaplar"),
            kutu("#a-kuyu_genisligi", 1810),
            b,
            duzelt=kutu("#a-kuyu_genisligi", 1830),
        )
        self._arizalari_dene("trafik PDF'i", "/api/indir/trafik-pdf", adim("/avan/trafik"), pdf, b)
        self._arizalari_dene("avan PDF'i", "/api/indir/avan-pdf", adim("/avan/hesaplar"), pdf, b)
        self._arizalari_dene(
            "kapak önizlemesi",
            "/api/indir/kapak-pdf",
            adim("/avan/kapak"),
            baslik,
            b,
            duzelt=lambda i: self.sayfa.get_by_label("Kapak başlığı").fill(f"Avan yeni {i}"),
        )
        self._arizalari_dene("kapak PDF'i", "/api/indir/kapak-pdf", adim("/avan/kapak"), pdf, b)
        paket = lambda i: self.sayfa.get_by_role("button", name="Projeyi indir").click()
        self._arizalari_dene(
            "avan paketi", "/api/indir/proje-dwg", adim("/avan/trafik"), paket, b, duzelt=False, sure=180
        )
        self.assertEqual(b, [], "\n" + "\n".join(b))

    def test_ariza_matrisi_diger(self):
        self.sayfa.add_init_script(self.ARIZA_BETIGI)
        self.sayfa.goto(self.url + "/")
        b = []

        def sayfa(yol):
            def h(i):
                self.sayfa.goto(self.url + yol)

            return h

        yenile = lambda i: self.sayfa.reload()

        def avan_sekmesi(i):
            #  Avanın seçenekleri yalnız Avan sekmesi seçilince istenir
            self.sayfa.reload()
            self.sayfa.get_by_role("radio", name="Avan").click()

        for ad, uc, yol, tetik in (
            ("ofis standardı ( uygulama )", "/api/uygulama/alanlar", "/ofis-standardi", yenile),
            ("ofis standardı ( avan )", "/api/secenekler", "/ofis-standardi", avan_sekmesi),
            ("tablolar", "/api/uygulama/alanlar", "/tablolar", yenile),
        ):
            self._arizalari_dene(ad, uc, sayfa(yol), tetik, b, get=True)
        with tempfile.TemporaryDirectory() as klasor:
            dosya = os.path.join(klasor, "deneme.uygulama")
            with open(dosya, "w", encoding="utf-8") as f:
                json.dump(
                    {"__mod": "uygulama", "__surum": 1, "alanlar": {"m_adet": "1", "__muk_asansorler": [{}]}},
                    f,
                )

            def sec(i):
                with self.sayfa.expect_file_chooser() as secici:
                    self.sayfa.get_by_role("button", name="Dosya seç").click()
                secici.value.set_files(dosya)

            def acilista_dusmus(i):
                #  Açılış şemayı sayfa açılırken alır;  orada düştüyse dosya açılınca yeniden ister
                self.sayfa.reload()
                sec(i)

            self._arizalari_dene(
                "açılışta dosya açma",
                "/api/uygulama/alanlar",
                sayfa("/"),
                acilista_dusmus,
                b,
                duzelt=sec,
                get=True,
            )
        self.assertEqual(b, [], "\n" + "\n".join(b))

    # ------------------------------------------------------------ 10 kaynak sayacı
    #  Aynı işlemler sayfa içinde ( yenilemeden ) tekrar tekrar:  açık işçi, nesne
    #  adresi, aralık, gözlemci, window / document dinleyicisi ve yoldaki istek başa
    #  döner mi?  Tam yenileme her şeyi sıfırlar — gezinme pushState ile.
    SAYAC_BETIGI = """(() => {
        const s = window.__kaynak = { isci: 0, adres: 0, aralik: 0, gozlemci: 0, istek: 0, dinleyici: {} };
        const W = window.Worker;
        window.Worker = class extends W {
            constructor(...a) { super(...a); s.isci++; }
            terminate() { s.isci--; return super.terminate(); }
        };
        const adresler = new Set(), ac = URL.createObjectURL, kapa = URL.revokeObjectURL;
        URL.createObjectURL = (o) => { const u = ac.call(URL, o); adresler.add(u); s.adres = adresler.size; return u; };
        URL.revokeObjectURL = (u) => { adresler.delete(u); s.adres = adresler.size; return kapa.call(URL, u); };
        const araliklar = new Set(), si = window.setInterval, ci = window.clearInterval;
        window.setInterval = (...a) => { const k = si.apply(window, a); araliklar.add(k); s.aralik = araliklar.size; return k; };
        window.clearInterval = (k) => { araliklar.delete(k); s.aralik = araliklar.size; return ci.call(window, k); };
        for (const ad of ['ResizeObserver', 'MutationObserver', 'IntersectionObserver']) {
            const G = window[ad];
            if (!G) continue;
            window[ad] = class extends G {
                observe(...a) { if (!this.__izliyor) { this.__izliyor = true; s.gozlemci++; } return super.observe(...a); }
                disconnect() { if (this.__izliyor) { this.__izliyor = false; s.gozlemci--; } return super.disconnect(); }
            };
        }
        const kimlik = new WeakMap(), kayitli = new Set();
        let n = 0;
        const anahtar = (h, t, f, o) => {
            if (!kimlik.has(f)) kimlik.set(f, ++n);
            return h + '|' + t + '|' + kimlik.get(f) + '|' + (typeof o === 'boolean' ? o : !!(o && o.capture));
        };
        const say = () => {
            const d = {};
            for (const k of kayitli) { const t = k.split('|').slice(0, 2).join(':'); d[t] = (d[t] || 0) + 1; }
            s.dinleyici = d;
        };
        const ekle = EventTarget.prototype.addEventListener, cikar = EventTarget.prototype.removeEventListener;
        EventTarget.prototype.addEventListener = function (t, f, o) {
            if ((this === window || this === document) && f && !(o && o.once)) {
                const k = anahtar(this === window ? 'window' : 'document', t, f, o);
                kayitli.add(k);
                if (o && o.signal) o.signal.addEventListener('abort', () => { kayitli.delete(k); say(); });
                say();
            }
            return ekle.call(this, t, f, o);
        };
        EventTarget.prototype.removeEventListener = function (t, f, o) {
            if ((this === window || this === document) && f) { kayitli.delete(anahtar(this === window ? 'window' : 'document', t, f, o)); say(); }
            return cikar.call(this, t, f, o);
        };
        const F = window.fetch.bind(window);
        window.fetch = (...a) => { s.istek++; return F(...a).finally(() => { s.istek--; }); };
    })()"""

    def _git(self, yol):
        """Sayfa içi gezinme ( yönlendirici popstate'i dinler ):  sayfa yenilenmez."""
        self.sayfa.evaluate(
            "y => { history.pushState({}, '', y); dispatchEvent(new PopStateEvent('popstate')); }", yol
        )
        self.iz.sakin()

    def _kaynak_dongusu(self, proje):
        self._git(proje)
        ekle = self.sayfa.get_by_role("button", name="Asansör ekle")
        ekle.click()
        self.iz.sakin()
        self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).last.click()
        self.sayfa.get_by_role("status").get_by_role("button", name="Geri al").click()
        self.sayfa.get_by_role("button", name=re.compile(r"asansörünü kaldır$")).last.click()
        self.iz.sakin()
        self._olcuyu_ac()
        self.sayfa.keyboard.press("Escape")
        for dugme in ("Teslim", re.compile("Örnek proje")):
            self.sayfa.get_by_role("button", name=dugme).first.click()
            self.sayfa.get_by_role("dialog").first.wait_for()
            self.sayfa.keyboard.press("Escape")
            self.sayfa.get_by_role("dialog").first.wait_for(state="detached")
        self._git(proje + "?gorunum=hesap")
        self._git(proje)
        for yol in ("/avan/trafik", "/avan/hesaplar", "/avan/kapak"):
            self._git(yol)
        main = self.sayfa.get_by_role("main")
        self._bekle(lambda: main.locator(".animate-spin").count() == 0, "önizleme çizilmedi", 30)
        with self.sayfa.expect_download():
            self.sayfa.get_by_role("button", name="PDF", exact=True).click()
        for yol in ("/avan/trafik", "/tablolar", "/ofis-standardi", "/"):
            self._git(yol)
        self.sayfa.wait_for_timeout(3500)  # indirmenin adresi 3 sn sonra bırakılır
        return self.sayfa.evaluate("JSON.parse(JSON.stringify(window.__kaynak))")

    def test_kaynak_sayaci_tekrarda_buyumez(self):
        self.sayfa.add_init_script(self.SAYAC_BETIGI)
        self.sayfa.goto(self.url + "/avan/trafik")
        self.sayfa.evaluate(
            """() => localStorage.setItem('asansor:avan', JSON.stringify({
                trafik: {bina_tipi: 'Konut'}, ekNufus: [], trafikAsansorleri: [{P: '8'}],
                ortak: {}, avanAsansorleri: [{}, {}, {}, {}], kapak: {project_title: 'Kaynak deneme'}}))"""
        )
        self.ornek_projeyi_ac()
        proje = "/" + self.sayfa.url.split("/", 3)[3]
        sayimlar = [self._kaynak_dongusu(proje) for _ in range(4)]
        duz = [
            {
                **{k: v for k, v in s.items() if k != "dinleyici"},
                **{f"dinleyici {t}": n for t, n in s["dinleyici"].items()},
            }
            for s in sayimlar
        ]
        artan = {
            k: [d.get(k, 0) for d in duz] for k in set().union(*duz) if duz[3].get(k, 0) > duz[1].get(k, 0)
        }
        self.assertEqual(artan, {}, f"tekrarla büyüyen kaynaklar:  {artan}\nsayımlar:  {duz}")
        self.assertEqual((duz[3]["isci"], duz[3]["istek"], duz[3]["adres"]), (0, 0, 0), duz[3])

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
