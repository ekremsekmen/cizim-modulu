"""UYGULAMA PROJESİ KAPAĞI — her asansörün tablosu projeden ( 22 Eki ).

Kapağın asansör bölümü ( kapasite … ölçek ) uygulama paketinde kullanıcının
yazdıklarıyla basılıyordu:  yazmazsa boş, iki asansörde 2. asansör hiç yoktu.
Şimdi her asansörün kendi tablosu alt alta basılır ( ciktilar/kapak_cikti ),
değerler hesabın girdisinden / sonucundan ve paketin çizimlerinden türer
( motor/uygulama/uygulama_kapagi.py ), yazılan değer ezer.

Hücreye sığma:  basılan bütün yazıların kutuları birbirine binmez ( taşan
değer yandaki hücrenin yazısına biner ).
"""

import io
import unittest
import zipfile
from unittest import mock

from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from ciktilar import kapak_cikti
from hesap_girdi import ASANSOR, ORTAK, SABITLER

#  Dört farklı asansör ( örnek projenin asansöründen ) — hepsinin hesabı ve çizimi kurulur
FARKLAR = [
    {},
    {"asansor_adi": "ASANSÖR 2", "durak_adedi": 8, "seyir_mesafesi": 21.0},
    {"asansor_adi": "ASANSÖR 3", "beyan_hizi": 1.0},
    {
        "asansor_adi": "ASANSÖR 4",
        "asansor_tipi": "Yük-insan asansörü",
        "beyan_hizi": 1.0,
        "durak_adedi": 6,
        "seyir_mesafesi": 15.0,
    },
]

#  Hücrelerin en uzun gerçekçi değerleri
UZUN = {
    "block": "A",
    "capacity": "1000 kg / 13 kişi",
    "speed": "1,60 m/s",
    "stops": "12",
    "travel": "33,00 m",
    "cabin_width": "1100",
    "cabin_depth": "2100",
    "standard": "TS EN 81-20",
    "elevator_class": "Sınıf I",
    "suspension": "2:1",
    "elevator_count": "4",
    "drive_type": "Elektrikli",
    "rail_size": "T125 / T90",
    "motor_power": "11,3 kW",
    "scale": "1/20 1/50",
}


def _veri(adet, kapak=None):
    return {
        "asansorler": [dict(ASANSOR, **FARKLAR[i]) for i in range(adet)],
        "proje_geneli": dict(ORTAK),
        "sabitler": dict(SABITLER),
        "asansor": 0,
        "kapak_sayfasi": kapak if kapak is not None else {"owner": "X"},
    }


def _yazilar(kapak, asansorler=None):
    """Kapağa basılan yazılar:  [ ( metin , sol , alt , sağ , üst ) ] — sayfa puntosu.
    Döndürülmüş yazılar ( "İMZASI" ) sayılmaz."""
    kayit = []
    asil = canvas.Canvas

    class Kayitli(asil):
        def drawString(self, x, y, metin, *a, **kw):
            kayit.append((x, y, metin, self._fontname, self._fontsize, tuple(self._currentMatrix)))
            return super().drawString(x, y, metin, *a, **kw)

    with mock.patch.object(canvas, "Canvas", Kayitli):
        kapak_cikti.pdf_baytlari(kapak, asansorler)
    kutular = []
    for x, y, metin, yazi_tipi, boy, (a, b, c, d, e, f) in kayit:
        if b or c:
            continue
        en = pdfmetrics.stringWidth(metin, yazi_tipi, boy)
        kutular.append((metin, a * x + e, d * y + f, a * (x + en) + e, d * (y + 0.7 * boy) + f))
    return kutular


def _binenler(kutular, pay=0.3):
    return [
        (p[0], q[0])
        for i, p in enumerate(kutular)
        for q in kutular[i + 1 :]
        if p[1] < q[3] - pay and q[1] < p[3] - pay and p[2] < q[4] - pay and q[2] < p[4] - pay
    ]


class KapakCizici(unittest.TestCase):
    def test_tek_asansorde_form_degismez(self):
        #  Avan kapağı ( asansorler yok ) ile tek tablolu uygulama kapağı aynı
        #  yerlere aynı yazıları basar;  çok asansör etiketi yok
        d = dict(UZUN, owner="X")
        self.assertEqual(_yazilar(d), _yazilar(d, [d]))
        self.assertNotIn("1. ASANSÖR", [m for m, *_ in _yazilar(d)])

    def test_dort_asansore_kadar_tek_sayfa_ve_sigar(self):
        for adet in range(1, 5):
            with self.subTest(adet=adet):
                kutular = _yazilar({"owner": "X"}, [dict(UZUN, block=str(i)) for i in range(adet)])
                self.assertEqual(_binenler(kutular), [])
                metinler = [m for m, *_ in kutular]
                for i in range(1, adet + 1):
                    if adet > 1:
                        self.assertIn(f"{i}. ASANSÖR", metinler)
                self.assertEqual(metinler.count("Taşıma Kapasitesi"), adet)
                self.assertEqual(metinler.count("1000 kg / 13 kişi"), adet)
                b = kapak_cikti.pdf_baytlari({"owner": "X"}, [UZUN] * adet)
                self.assertEqual(len(PdfReader(io.BytesIO(b)).pages), 1)

    def test_alt_kutular_kayar_baslik_yerinde(self):
        k = kapak_cikti
        tek, alt_, yazi = k.yerlesim(1)  # tek asansörde form aynı ( eşlemeler birim )
        self.assertEqual([tek[0](201.3), alt_(555.5), yazi], [201.3, 555.5, 1.0])
        for adet in range(2, 5):
            with self.subTest(adet=adet):
                tablolar, asagi, yazi = k.yerlesim(adet)
                self.assertEqual(len(tablolar), adet)
                #  Tablolar arasında TABLO_ARA, mühendisler sonuncudan ARA kadar aşağıda
                for ust, alt in zip(tablolar, tablolar[1:]):
                    self.assertAlmostEqual(alt(k.SATIR[0]) - ust(k.SATIR[-1]), k.TABLO_ARA, places=6)
                self.assertAlmostEqual(asagi(k.MUHENDIS_UST) - tablolar[-1](k.SATIR[-1]), k.ARA, places=6)
                #  Sayfanın altı yerinden oynamaz;  başlık kutusu daralmaz
                self.assertAlmostEqual(asagi(k.SAYFA_ALT), k.SAYFA_ALT, places=6)
                self.assertAlmostEqual(
                    asagi(k.BASLIK_ALT) - asagi(k.BASLIK_UST), k.BASLIK_ALT - k.BASLIK_UST, places=6
                )
                #  Daralan kutular en küçük boylarının altına inmez ( kutu iki kez yazılabilir )
                for ust, alt, _boy in k.DARALAN:
                    en_kucuk = min(b for u, a, b in k.DARALAN if (u, a) == (ust, alt))
                    self.assertGreaterEqual(asagi(alt) - asagi(ust), en_kucuk - 1e-6)
                self.assertGreater(k.daralma_payi(), 0)
                #  Satırlar yazılarıyla aynı oranda incelir ( dört asansörde biraz )
                for esle in tablolar:
                    for a, b in zip(k.SATIR, k.SATIR[1:]):
                        self.assertAlmostEqual(esle(b) - esle(a), (b - a) * yazi, places=6)
                self.assertGreaterEqual(yazi, 0.8)
        #  İki asansörde imza alanlarından önce boş kaşe kutusu daralır ( 60 pt'ye kadar )
        _t, asagi, _y = k.yerlesim(2)
        self.assertAlmostEqual(asagi(k.BOS_ALT) - asagi(k.BOS_UST), 60.0, places=6)
        self.assertLess(asagi(k.MUHENDIS_ALT) - asagi(k.MUHENDIS_IMZA), k.MUHENDIS_ALT - k.MUHENDIS_IMZA)
        #  İki ve üç asansörde satırlar ve yazılar tam boy
        self.assertEqual([k.yerlesim(adet)[2] for adet in (2, 3)], [1.0, 1.0])

    def test_degerler_siyah_yazilar_tek_boyda(self):
        #  "Temiz ve düzgün" ( kullanıcı 22 Eki ):  bütün değerler aynı boyda, siyah
        kayit = []
        asil = canvas.Canvas

        class Kayitli(asil):
            def drawString(self, x, y, metin, *a, **kw):
                kayit.append((metin, self._fontsize, self._fillColorObj.hexval()))
                return super().drawString(x, y, metin, *a, **kw)

        #  ( mühendis / firma satırlarının numaraları 1 … 5 değer sayılmaz )
        degerler = {v for k_, v in UZUN.items() if k_ != "block"} - {str(i) for i in range(1, 6)}
        for adet in (1, 3, 4):
            kayit.clear()
            with mock.patch.object(canvas, "Canvas", Kayitli):
                kapak_cikti.pdf_baytlari({}, [UZUN] * adet)
            self.assertEqual({renk for _m, _b, renk in kayit}, {"0x000000"})
            boy = kapak_cikti.DEGER * kapak_cikti.yerlesim(adet)[2]
            self.assertEqual({b for m, b, _r in kayit if m in degerler}, {boy})

    def test_her_alan_her_tabloda_basilir(self):
        from motor.uygulama import uygulama_kapagi

        tablolar = [{a: f"{a[:3]}{i}" for a in uygulama_kapagi.ALANLAR} for i in range(3)]
        metinler = {m for m, *_ in _yazilar({}, tablolar)}
        for t in tablolar:
            self.assertEqual({v for v in t.values() if v not in metinler}, set())

    def test_kalin_etiket_kendi_eniyle_sigar(self):
        #  "1. ASANSÖR" normal yazının eniyle ölçülünce yandaki başlığa biniyordu
        kutular = _yazilar({}, [{}, {}, {}])
        self.assertEqual(_binenler(kutular), [])


class Turetme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from motor.uygulama import uygulama_kapagi
        from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

        cls.kapak = uygulama_kapagi
        v = _veri(4)
        s, yanit = uygulama_uclari._coklu_sonuc(v)
        assert yanit is None, yanit.body
        a, o = uygulama_istegi.asansor_girdileri(v)
        cizim = cizim_uclari.girdiler(v, a, o, s, "DENEME")
        assert all(not h for _g, h in cizim), cizim
        cls.sonuc = s
        cls.t = uygulama_kapagi.uygulamadan(s, [g for g, _h in cizim])

    def test_her_asansorun_kendi_degerleri(self):
        t = self.t
        self.assertEqual(len(t), 4)
        self.assertEqual([x["stops"] for x in t], ["11", "8", "11", "6"])
        self.assertEqual([x["travel"] for x in t], ["29,00 m", "21,00 m", "29,00 m", "15,00 m"])
        self.assertEqual([x["speed"] for x in t], ["1,60 m/s", "1,60 m/s", "1,00 m/s", "1,00 m/s"])
        #  İnsan asansörü Sınıf I;  yük-insan asansörünün sınıfı ikircikli — türetilmez
        self.assertEqual([x.get("elevator_class") for x in t], ["Sınıf I", "Sınıf I", "Sınıf I", None])
        for x in t:
            self.assertEqual(x["drive_type"], "Elektrikli")
            self.assertEqual(x["elevator_count"], "4")
            self.assertEqual(x["standard"], "TS EN 81-20")
            self.assertNotIn("block", x)  # türetilmez

    def test_degerler_hesabinki(self):
        #  Sayı uydurulmaz:  her değer hesabın girdisinden / sonucundan
        for x, a in zip(self.t, self.sonuc["asansorler"]):
            g, o = a["girdi"], a["ozet"]
            self.assertEqual(x["capacity"], f"{g['beyan_yuku']:g} kg / {o['kabin_kisi']:g} kişi")
            self.assertEqual(x["cabin_width"], f"{g['kabin_genisligi']:g}")
            self.assertEqual(x["cabin_depth"], f"{g['kabin_derinligi']:g}")
            self.assertEqual(x["suspension"], f"{g['aski_orani']:g}:1")
            self.assertEqual(x["motor_power"], f"{g['motor_gucu']:g} kW".replace(".", ","))
            #  Formun profilleri ISO adıyla:  kabin rayı / ağırlık rayı
            self.assertEqual(
                (g["kabin_ray_profili"], g["agirlik_ray_profili"]), ("89 x 62 x 15,88", "70 x 65 x 9")
            )
            self.assertEqual(x["rail_size"], "T89 / T70")
            self.assertEqual(x["scale"], "1/20 1/50")  # paftanın anteti gibi

    def test_hesabi_kurulamayan_asansorden_turetilmez(self):
        from motor.uygulama import uygulama_hesabi

        s = uygulama_hesabi.hesapla_coklu([dict(ASANSOR), dict(ASANSOR, kabin_genisligi=9000)], dict(ORTAK))
        self.assertTrue(s["aktif"])
        t = self.kapak.uygulamadan(s)
        self.assertEqual(t[1], {})
        self.assertEqual(t[0]["elevator_count"], "2")
        self.assertEqual(self.kapak.uygulamadan({"aktif": False, "hata": ["x"]}), [])

    def test_ray_adi(self):
        from motor.uygulama import mukavemet_tablolari

        #  Formun her profilinin adı var;  tablo dışı profil ölçüsüyle yazılır
        self.assertEqual(set(self.kapak.RAY_ADI), set(mukavemet_tablolari.RAY_PROFILLERI))
        self.assertEqual(self.kapak.ray_adi("89 x 62 x 15,88"), "T89")
        self.assertEqual(self.kapak.ray_adi("100 x 70 x 12"), "100×70")

    def test_yazilan_ezer(self):
        k = {"block": "A", "block.2": "B", "capacity": "8 kişi", "capacity.3": "  13   kişi ", "speed.2": ""}
        t = self.kapak.kapak_tablolari(k, self.t)
        self.assertEqual([x["block"] for x in t], ["A", "B", "A", "A"])
        self.assertEqual([x["capacity"] for x in t], ["8 kişi", "8 kişi", "13 kişi", "8 kişi"])
        self.assertEqual(t[1]["speed"], "1,60 m/s")  # boş yazılan ezmez
        #  Türetilen sözlükler değişmez
        self.assertNotIn("block", self.t[0])


class Paket(unittest.TestCase):
    def test_paketin_kapaginda_iki_asansor(self):
        from uclar import uygulama_uclari

        #  Proje adı ( kimlik ) büyük başlığa yazılmaz:  başlık belgenin adıdır
        v = _veri(2, {"project_title": "ÖRNEK KONUTLARI", "owner": "X", "block.2": "C", "speed": "9,99 m/s"})
        z = zipfile.ZipFile(io.BytesIO(uygulama_uclari.indir_uygulama_dwg(v).body))
        kapak = next(n for n in z.namelist() if n.endswith("Kapak.pdf"))
        metin = PdfReader(io.BytesIO(z.read(kapak))).pages[0].extract_text()
        for parca in ("1. ASANSÖR", "2. ASANSÖR", "ASANSÖR UYGULAMA PROJESİ", "800 kg / 10 kişi", "21,00 m"):
            self.assertIn(parca, metin)
        self.assertEqual(metin.count("9,99 m/s"), 2)  # yazılan hız ikisini de ezer
        self.assertNotIn("ÖRNEK KONUTLARI", metin)
        self.assertNotIn("1,60 m/s", metin)


if __name__ == "__main__":
    unittest.main()
