"""ÇİZİMİN ÇERÇEVESİ ( 20 Kas, kullanıcı:  "kesitlerin etrafındaki dümdüz çizgiyi kesik çizgili
yapalım … fazla büyük çerçeveye ihtiyaç yok, minimum dikdörtgen … kesitlerin hiç bir şeyi
bozulmasın, yalnız etrafında çizilen çerçeve" ).

  · en küçük dikdörtgen:  çizimin kapsayanı, her yanda geometri.CERCEVE_PAYI ( kâğıtta 5 mm —
    19 Kas'a dek 15 );  başlık şeride sığmazsa açıklaması ikinci satıra iner ( 3,5 mm — kullanıcı
    "evet, iki satır" ), yine sığmazsa çerçeve iki yana genişler;
  · çizgisi kesik ( ISO 128:  0,50 kalemde 6 · 1,5 mm ):  DXF'te katmanın çizgi tipi ( polilin,
    AutoCAD köşelerinde çizgiyle başlatır ), PDF'te ve ekranda her kenar köşeden köşeye tam
    çizgiyle — desen çevre boyunca akınca köşelerin 6'da 1'i boşluğa düşüyordu;
  · sayfanın çerçevesi ve anteti ( elektrik projesi, ayrı sayfalı PDF ) düz kalır ( SAYFA );
  · kesit bugünkü çerçevesiyle sütuna sığmıyorsa kırılır ( kuyu_kesiti._yukseklik — o günün projelerinde
    hiçbir kesit değişmedi;  altın çıktı da kilitler ).
"""

import math
import re
import unittest

from cizim import dxf, eleman, elektrik, geometri, kuyu_kesiti, pdf, svg, uslup
from testler import test_elektrik


def _kutu(e):
    return next(x for x in e if x.get("katman") == "CERCEVE" and x["tip"] == "dikdortgen")


def _oturur(boy, dizi):
    """Kesik dizisi ( çizgi, boşluk ) `boy`a oturuyor mu:  n tam çizgi ve n − 1 boşluk."""
    a, b = dizi
    n = (boy + b) / (a + b)
    return n >= 2 - 1e-6 and abs(n - round(n)) < 1e-3


class _Tuval:
    """reportlab tuvalinin çizgilerini kesik dizileriyle toplar."""

    def __init__(self):
        self.cizgiler, self.dizi = [], []

    #  Yöntem adları reportlab'ınkiler
    def setDash(self, dizi=None, faz=0):
        self.dizi = list(dizi or [])

    def line(self, *p):
        self.cizgiler.append((p, self.dizi))

    def rect(self, *p, **_k):
        self.cizgiler.append((("rect",) + p, self.dizi))

    def setStrokeColor(self, *_a):
        pass

    def setLineWidth(self, *_a):
        pass


class EnKucukDikdortgen(unittest.TestCase):
    def test_cizimin_kapsayani_ve_pay(self):
        for olcek in (20, 50):
            k = olcek / 20.0
            p = geometri.CERCEVE_PAYI * k
            self.assertAlmostEqual(p / olcek, 5.0)  # kâğıtta 5 mm
            #  Başlıktan geniş çizim:  çerçeve kapsayan + pay;  altta künye şeridi
            c = _kutu(
                geometri.cerceveli([eleman.dikdortgen("KABIN", 0, 0, 9000 * k, 3000 * k)], "PLAN", olcek)
            )
            self.assertAlmostEqual(c["x"], -p)
            self.assertAlmostEqual(c["g"], 9000 * k + 2 * p)
            self.assertAlmostEqual(c["y"] + c["d"], 3000 * k + p)
            self.assertAlmostEqual(c["y"], -p - geometri.KUNYE_SERIDI * k)


class IkiSatirliKunye(unittest.TestCase):
    """Tek satırlık başlık çizimden genişse açıklaması ( "  ( … )" ) ikinci satıra iner."""

    BB = "B-B KUYU DÜŞEY KESİTİ  ( arkadan kat kapılarına — kabin en üst durakta )"

    def _kunye(self, en, baslik, olcek=50, **ek):
        """en:  çizimin eni ( mm, gerçek ölçü — 1/50'de 7.000 kâğıtta 140 mm )."""
        k = olcek / 20.0
        e = geometri.cerceveli([eleman.dikdortgen("KABIN", 0, 0, en, 3000)], baslik, olcek, **ek)
        yazilar = [x for x in e if x.get("katman") == "CERCEVE" and x["tip"] == "yazi"]
        return _kutu(e), yazilar, k

    def test_aciklama_ikinci_satirda_cerceve_cizim_kadar(self):
        c, yazilar, k = self._kunye(7000, self.BB)
        bas, ack = yazilar
        self.assertEqual(bas["metin"], "B-B KUYU DÜŞEY KESİTİ   1/50")
        self.assertEqual(ack["metin"], "( arkadan kat kapılarına — kabin en üst durakta )")
        self.assertEqual((bas["yukseklik"], ack["yukseklik"]), (uslup.BASLIK * k, uslup.HARF * k))
        #  Çerçeve çizim kadar ( başlığa göre genişlemedi );  şerit iki satırlık
        p = geometri.CERCEVE_PAYI * k
        self.assertAlmostEqual(c["g"], 7000 + 2 * p)
        self.assertAlmostEqual(c["y"], -p - (geometri.KUNYE_SERIDI + geometri.ACIKLAMA_SATIRI) * k)
        #  İki satır şeridin içinde, üst üste binmeden;  başlığın satırı tek satırlık şeridinki
        x0, y0, x1, y1 = c["x"], c["y"], c["x"] + c["g"], -p
        kutular = [geometri.sinir([y]) for y in (bas, ack)]
        for a in kutular:
            self.assertTrue(x0 < a[0] and a[2] < x1 and y0 < a[1] and a[3] < y1, a)
        self.assertLess(kutular[1][3], kutular[0][1])
        self.assertAlmostEqual(bas["y"], -p - geometri.KUNYE_SERIDI * k / 2.0)

    def test_sigan_baslik_tek_satir(self):
        c, yazilar, k = self._kunye(20000, self.BB)
        self.assertEqual([y["metin"] for y in yazilar], [self.BB + "   1/50"])
        self.assertAlmostEqual(c["y"], -(geometri.CERCEVE_PAYI + geometri.KUNYE_SERIDI) * k)

    def test_ilk_satir_sigmazsa_iki_yana_genisler(self):
        """Kasnak düzenlemesi gibi dar çizimde iki satırın uzunu kadar, çizimin ortasında."""
        baslik = "KASNAK DÜZENLEMESİ  ( tahrik kasnağının ekseninden — halatlar ve sarım açısı )"
        c, yazilar, k = self._kunye(500, baslik, olcek=20)
        self.assertEqual(len(yazilar), 2)
        gerek = max(
            240 * k + eleman.yazi_eni(yazilar[0]["metin"], uslup.BASLIK * k),
            240 * k + eleman.yazi_eni(yazilar[1]["metin"], uslup.HARF * k),
        )
        self.assertAlmostEqual(c["g"], gerek)
        self.assertLess(c["g"], 240 * k + eleman.yazi_eni(baslik + "   1/20", uslup.BASLIK * k))
        self.assertAlmostEqual(c["x"] + c["g"] / 2.0, 250.0)

    def test_aciklamasiz_baslik_tek_satir_genisler(self):
        baslik = "KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI"
        c, yazilar, k = self._kunye(500, baslik, olcek=20)
        self.assertEqual([y["metin"] for y in yazilar], [baslik + "   1/20"])
        self.assertAlmostEqual(c["g"], 240 * k + eleman.yazi_eni(baslik + "   1/20", uslup.BASLIK * k))

    def test_sagdaki_yazi_ilk_satirda(self):
        c, yazilar, k = self._kunye(7000, self.BB, seritler=("PROJE  ·  ASANSÖR 1",))
        bas, ack, sag = yazilar
        self.assertEqual(sag["hiza"], "sag")
        self.assertAlmostEqual(sag["y"], bas["y"])
        #  Başlıkla arası 10 mm
        self.assertGreaterEqual(
            geometri.sinir([sag])[0] - geometri.sinir([bas])[2], 200 * k - 1e-6, (c["g"], ack["metin"])
        )


class KesikCizgi(unittest.TestCase):
    def test_cerceve_kesik_sayfa_duz(self):
        des = uslup.DESENLER[uslup.KATMAN["CERCEVE"].desen]
        d = uslup.KATMAN["CERCEVE"].kalinlik
        #  ISO 128:  kesik çizgi 12 d, boşluk 3 d
        self.assertEqual([abs(v) * des.olcek for v in des.tanim], [12 * d, 3 * d])
        self.assertTrue(des.oturur)
        self.assertIsNone(uslup.KATMAN["SAYFA"].desen)
        #  Öbür kesik çizgiler ( gizli, eksen, alan ) eskisi gibi akar
        self.assertEqual([a for a, x in uslup.DESENLER.items() if x.oturur], ["CERCEVE"])
        #  Antet ve elektrik projesinin sayfası çizimin çerçevesi değil
        self.assertEqual(pdf.antet("P", "A1", "PLAN", "1/20", "SAYFA  1 / 1")[0]["katman"], "SAYFA")
        e = elektrik.ciz(test_elektrik._ornek())
        self.assertFalse([x for x in e if x.get("katman") == "CERCEVE"])
        self.assertTrue([x for x in e if x.get("katman") == "SAYFA" and x["tip"] == "dikdortgen"])

    def test_kenara_oturan_desen(self):
        for k in (1.0, 2.5):
            a, b = 6.0 * 20 * k, 1.5 * 20 * k
            for kagit in (20.0, 47.3, 100.0, 333.3, 1012.7):
                boy = kagit * 20 * k
                f = uslup.oturan_olcek("CERCEVE", boy, k)
                self.assertTrue(_oturur(boy, (a * f, b * f)), (k, kagit, f))
                self.assertLess(abs(f - 1.0), 0.2)
        #  İki çizgi sığmayan parça sürekli
        self.assertIsNone(uslup.oturan_olcek("CERCEVE", 6.0 * 20, 1.0))

    def test_dxf_polilin_katmanin_deseniyle(self):
        e = geometri.cerceveli([eleman.dikdortgen("KABIN", 0, 0, 2000, 1500)], "PLAN", 20)
        d = dxf.belge(e, olcek=20)
        self.assertEqual(d.layers.get("CERCEVE").dxf.linetype, uslup.DESENLER["CERCEVE"].dxf)
        (p,) = [x for x in d.modelspace().query("LWPOLYLINE") if x.dxf.layer == "CERCEVE"]
        self.assertTrue(p.closed)
        #  PLINEGEN yok:  AutoCAD her köşede çizgiyle başlar ve biter
        self.assertFalse(p.dxf.flags & 128)
        self.assertEqual(p.dxf.ltscale, uslup.DESENLER["CERCEVE"].olcek * 20)

    def test_pdf_ve_ekranda_her_kenar_koseden_koseye(self):
        for olcek in (20, 50):
            k = olcek / 20.0
            e = geometri.cerceveli([eleman.dikdortgen("KABIN", 0, 0, 2000 * k, 1500 * k)], "PLAN", olcek)
            c = _kutu(e)
            yari = uslup.KATMAN["CERCEVE"].kalinlik * 20 * k / 2.0
            #  PDF:  dört kenar, her biri yarım kalem uzamış ( köşenin dış karesi dolu ) ve oturmuş
            t = _Tuval()
            pdf._dikdortgen(t, c, k)
            self.assertEqual(len(t.cizgiler), 4)
            for (x1, y1, x2, y2), dizi in t.cizgiler:
                self.assertTrue(_oturur(math.hypot(x2 - x1, y2 - y1), dizi), (olcek, dizi))
            xs = [v for (x1, _y1, x2, _y2), _d in t.cizgiler for v in (x1, x2)]
            self.assertAlmostEqual(min(xs), c["x"] - yari)
            self.assertAlmostEqual(max(xs), c["x"] + c["g"] + yari)
            #  Künye şeridinin çizgisi de iki ucunda çizgiyle
            serit = next(x for x in e if x.get("katman") == "CERCEVE" and x["tip"] == "cizgi")
            t = _Tuval()
            pdf._desen(t, serit, k, serit["x2"] - serit["x1"])
            self.assertTrue(_oturur(serit["x2"] - serit["x1"], t.dizi))
            #  Ekran:  aynı dört kenar
            s = svg._dikdortgen(c, "#111111", f"{yari * 2:g}", k)
            kenarlar = re.findall(
                r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)"[^>]*'
                r'stroke-dasharray="([^"]+)"',
                s,
            )
            self.assertEqual(len(kenarlar), 4)
            for x1, y1, x2, y2, dizi in kenarlar:
                boy = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
                self.assertTrue(_oturur(boy, [float(v) for v in dizi.split()]), (olcek, dizi))


class KesitinKirigi(unittest.TestCase):
    def test_kirik_bugunku_cercevenin_yuksekligiyle(self):
        """Kesit, bugünkü çerçevesiyle sütuna sığmıyorsa kırılır ( 19 Kas:  "sığıyorsa kırılmasın" ):
        kırığın ölçtüğü yükseklik iki satırlı künyeli çerçeveninki;  tek satırlıda çerçeve daha kısa."""
        e = [eleman.dikdortgen("KUYU-DUVAR", 0, 0, 2000, 20000)]
        K = 2.5
        iki = _kutu(geometri.cerceveli(e, "A-A KUYU DÜŞEY KESİTİ  ( yan — kabin en alt durakta )", 50))
        self.assertAlmostEqual(kuyu_kesiti._yukseklik(e, K), iki["d"])
        tek = _kutu(geometri.cerceveli(e, "A-A", 50))
        self.assertLess(tek["d"], kuyu_kesiti._yukseklik(e, K))


if __name__ == "__main__":
    unittest.main()
