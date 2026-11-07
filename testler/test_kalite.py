"""KALİTE KAPISI — çizim kalitesinin ölçülebilir kuralları ( 13 Eki, çizim kalitesi
5. adımı;  kullanıcı:  "hedefli düzeltme + kalite kapısı" ).

Altın düzenlerin ( testler/altin_cizim — 30 çizilen düzen, her birinde bütün
çizimler ) elemanları üzerinde sayılır:  altın testi bugünkü çıktının altınla
birebir aynı olduğunu denetler, bu test altının kalitesini.  Kötüleşen bir
değişiklik altın yenilenince burada kırılır.

  · yazı yazıya binmez ( etiket ve ölçü yazısı;  kutular yazi_kutusu )
  · aynı aralık iki kez ölçülmez ( ISO 129-1 — kuyu üstünde iki yanda aynı
    zincir, kasnak düzenlemesinde Ø ile HALAT ARASI vardı );  kimlikli iki
    ölçü ( ayrı parçalar ) rastlantıyla çakışabilir — geometri.tekrarlari_at
  · yazı bir parçanın kenarına binmez ( geometri.parca_kenarlari;  yerleşimin
    kendi kıl payıyla:  2 mm — kâğıtta 0,1 mm )
  · alanın adı ( geometri.alan_yazisi:  sığınma, çalışma alanı ) kendi
    kutusunun içindedir

Bugün sıfır olmayan kusurlar ( maskenin sildiği kenar, ölçünün üstünden geçen
ölçü, kopuk ölçü yazısı, betondan geçen halat — araclar/karne ) CIRCIRLA
tutulur:  sayıları kayıttan artamaz ( KaliteKarnesi;  26 Eki kalite denetimi ).
6 Kas çizim denetiminin kuralları da ( yanlış aralıktaki / bitişik / taşan ölçü
yazısı, uzak ölçü, kuyunun dışındaki etiket, B-B'de kapının yazısı, işaret
birliği ) karnede;  görünüşler arası tutarlılık kesin kural ( GorunuslerArasi )."""

import collections
import unittest

from araclar import gorunus
from araclar import karne
from cizim import eleman
from cizim import geometri
from cizim import kesit_parcalari
from cizim import uslup
from testler import altin_cizim

#  Yerleşimin kenar denetimindeki kıl payı ( geometri.etiketleri_ayir,
#  _YaziYerleri:  kutu 2 mm küçültülerek bakılır — 1/20'de;  ölçekle büyür )
KIL_PAYI = 2.0
ALANLAR = ("siginma", "calisma_alani")


def _yazilar(e):
    return [
        x
        for x in e
        if (x["tip"] == "yazi" and x.get("katman") != "CERCEVE") or (x["tip"] == "olcu" and x.get("yazi"))
    ]


def _ust(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def kapi_bulgulari(e, olcek):
    """{ kural:  [ bulgu ] } — boş liste temiz."""
    k = olcek / 20.0
    yazilar = _yazilar(e)
    kutular = [(x, geometri.yazi_kutusu(x)) for x in yazilar]
    bulgu = collections.defaultdict(list)
    for i, (a, ka) in enumerate(kutular):
        for b, kb in kutular[i + 1 :]:
            if _ust(ka, kb):
                bulgu["yazı yazıya"].append((a["metin"], b["metin"]))
    araliklar = collections.defaultdict(list)
    for o in e:
        if o["tip"] == "olcu":
            araliklar[geometri.olcu_araligi(o)].append(o)
    bulgu["tekrar"] = [
        a for a, liste in araliklar.items() if len(liste) > 1 and any(not o.get("ad") for o in liste)
    ]
    kenarlar = geometri.parca_kenarlari(e)
    for x, kx in kutular:
        if any(geometri.kenar_kesisir(s, kx, KIL_PAYI * k) for s in kenarlar):
            bulgu["parça kenarına"].append(x["metin"])
    alanlar = [geometri.sinir([x]) for x in e if x.get("ad") in ALANLAR and x["tip"] == "dikdortgen"]
    for x, kx in kutular:
        if x.get("ad") != "alan_adi":
            continue
        ox, oy = (kx[0] + kx[2]) / 2.0, (kx[1] + kx[3]) / 2.0
        alan = next((a for a in alanlar if a[0] < ox < a[2] and a[1] < oy < a[3]), None)
        if alan is None or not (
            alan[0] <= kx[0] and kx[2] <= alan[2] and alan[1] <= kx[1] and kx[3] <= alan[3]
        ):
            bulgu["alan yazısı taşar"].append(x["metin"])
    return bulgu


class KaliteKapisi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.altin = altin_cizim.oku()

    def test_altin_duzenlerin_kalitesi(self):
        cizilen = 0
        for duzen, kayit in self.altin.items():
            for ad, c in (kayit.get("cizimler") or {}).items():
                cizilen += 1
                bulgu = kapi_bulgulari(c["elemanlar"], c["olcek"])
                for kural, liste in bulgu.items():
                    with self.subTest(duzen=duzen, cizim=ad, kural=kural):
                        self.assertEqual(liste, [])
        self.assertGreater(cizilen, 250)  # 30 düzen × 9 – 10 çizim

    def test_kapi_bozuk_cizimi_yakalar(self):
        #  Kapının kendisi:  yapay bozuk çizimde her kural bir bulgu verir
        from cizim import eleman

        e = [
            eleman.dikdortgen("KABIN", 0, 0, 1000, 1000),
            eleman.yazi(1000, 500, "KABİN"),  # kenarın üstünde
            eleman.yazi(1010, 520, "İKİNCİ"),  # öbür yazıya biner
            eleman.olcu("yatay", (0, 0), (1000, 0), -200, "1000"),
            eleman.olcu("yatay", (0, 0), (1000, 0), -300, "1000"),  # tekrar
            eleman.ad(eleman.dikdortgen("SIGINMA", 2000, 0, 300, 300), "siginma"),
            eleman.ad(eleman.yazi(2150, 150, "SIĞINMA ALANI ÇOK UZUN"), "alan_adi"),  # taşar
        ]
        geometri.yazilari_yerlestir(e)
        bulgu = kapi_bulgulari(e, 20)
        for kural in ("yazı yazıya", "tekrar", "parça kenarına", "alan yazısı taşar"):
            self.assertTrue(bulgu[kural], kural)


def _olcu(yon, bas, son, kot, yazi_yeri):
    """Yazısı verilen yerde ölçü:  yatay ( bas, son ) x'te, düşey y'de."""
    a, b = ((bas, 0), (son, 0)) if yon == "yatay" else ((0, bas), (0, son))
    x, y = yazi_yeri
    return eleman.olcu(yon, a, b, kot, yazi={"x": x, "y": y, "aci": 0 if yon == "yatay" else 90, "h": 70.0})


class KaliteKarnesi(unittest.TestCase):
    """CIRCIR ( araclar/karne, 26 Eki ):  ölçülen kusurların sayısı her altın
    düzenin her çiziminde kayıttadır ( testler/kalite_karnesi.json ).  Sayı
    artarsa kötüleşme;  azalırsa iyileşme — kayıt bilerek yenilenir
    ( python -m araclar.karne --yenile ), iyileşme geri gelemez."""

    def test_altin_duzenlerin_karnesi_kayitla_ayni(self):
        kotu, iyi = karne.farklar(karne.oku(karne.ALTIN_KAYDI), karne.altin_karnesi())
        self.assertEqual(kotu, [], "kötüleşme:  çizimde yeni kusur")
        self.assertEqual(iyi, [], "iyileşme:  kaydı yenile — python -m araclar.karne --yenile")

    def test_her_kural_bozuk_cizimi_yakalar(self):
        h = uslup.NORMAL
        w = eleman.yazi_eni("PANO", h)
        govde_ust = 50 + (uslup.BUYUK_HARF - uslup.TABAN) * h  # ortası 50'deki yazının büyük harf tepesi
        kot = []
        kesit_parcalari.kot_isareti(kot, 15000, 0, "+1,00", 1.0)
        e = [
            #  maskesi kenarı siler:  kutusu kenardan 5 mm uzakta, maskesi 8,75 taşar
            eleman.dikdortgen("KABIN", 0, 0, 1000, 1000),
            eleman.yazi(1000 + w / 2 + 5, 500, "PANO"),
            #  başka bir ölçünün çizgisi yazının ortasından geçer
            _olcu("yatay", 2000, 3000, 0, (2500, 50)),
            _olcu("dusey", -500, 500, 2500, (2550, 300)),
            #  başka bir ölçünün kısa uzatma çizgisi yazının tepesine 3 mm iner
            _olcu("yatay", 4000, 5000, 0, (4500, 50)),
            _olcu("yatay", 4500, 6000, govde_ust - 3 + uslup.SAPLAMA * 20, (5250, govde_ust + 50)),
            #  ok yazının içinden geçer, ucu yazıdan uzak
            eleman.yazi(7000, 0, "YAZI"),
            eleman.ok("YAZI", 6700, 0, 7300, 0),
            #  ölçü yazısı çizgisinden 200 uzakta
            _olcu("yatay", 8000, 9000, 0, (8500, 200)),
            #  halat betonun içinden
            eleman.dikdortgen("TARAMA", 10000, 0, 1000, 150, tip="tarama"),
            eleman.cizgi("HALAT", 10500, -500, 10500, 500),
            #  etiket ölçü çizgisinin üstünde:  maskesi çizgiyi siler
            _olcu("yatay", 12000, 13000, 0, (12500, 50)),
            eleman.yazi(12200, 0, "YAZI"),
            #  ölçü çizgisi kot işaretinin üçgeninden geçer ( yazısından uzak )
            *kot,
            _olcu("dusey", -300, 400, 14980, (14900, -250)),
            *self._alti_kasim_ornekleri(),
        ]
        b = karne.karne(e, 20)
        for kural in karne.KURALLAR:
            if kural in karne.CIZIME_BAGLI:
                continue  # test_uzak_olcu_yalniz_giris_ve_kapi_kesitinde
            with self.subTest(kural=kural):
                self.assertEqual(len(b[kural]), 1, b[kural])

    @staticmethod
    def _alti_kasim_ornekleri():
        """6 Kas kurallarının ( çizim denetimi ) birer örneği, öbür örneklerden uzakta."""
        w = eleman.yazi_eni("1000", 70.0)
        uzun = eleman.olcu(
            "dusey",
            (0, 900),
            (0, 1000),
            30000,
            "İLK KONSOL 100",
            yazi={"x": 30060, "y": 1300, "aci": 90, "h": 70.0},
        )
        return [
            #  "100"ün yazısı 1000'in aralığında ( aynı zincir )
            _olcu("yatay", 22000, 23000, 0, (22800, 50)),
            _olcu("yatay", 23000, 23100, 0, (22200, 50)),
            #  iki ölçü yazısı arası 1 mm:  "1000 1000" tek söz gibi
            _olcu("yatay", 26000, 27000, 0, (27000 - 10 - w / 2, 60)),
            _olcu("yatay", 27000, 28000, 0, (27000 + 10 + w / 2, 60)),
            #  açıklamalı yazı çizimin parçalarının ( en üstü 1.000 ) üstüne taşar
            uzun,
            #  kuyu ( SW ) 40.000 … 41.000;  karşı ağırlığın etiketi dışında, oksuz
            eleman.dikdortgen("KUYU-DUVAR", 40000, 0, 1000, 1000),
            eleman.olcu(
                "yatay", (40000, 0), (41000, 0), -200, "SW1000", yazi={"x": 40500, "y": -150, "h": 70.0}
            ),
            eleman.ad(eleman.yazi(42000, 500, "KARŞI AĞIRLIK"), "agirlik_yazi"),
            #  B-B:  katın adı "0", kapısında "1"
            eleman.ad(eleman.yazi(50000, 1100, "0"), "durak_adi"),
            eleman.ad(eleman.yazi(50500, 1200, "1"), "durak_no"),
            #  çap Ø ile
            eleman.yazi(55000, 0, "Ø 320"),
        ]

    def test_uzak_olcu_yalniz_giris_ve_kapi_kesitinde(self):
        #  Giriş görünüşünde ve kapı yan kesitinde ölçü ölçtüğü özelliğin yanında
        #  olmalı:  "160" / "240" buton yuvasının 70 mm üstünde havadaydı ( 6 Kas );
        #  planda ve kesitte dış sıralar bilerek uzaktır — sayılmaz
        e = [
            eleman.dikdortgen("KAPI", 0, 0, 1000, 2000),
            _olcu("yatay", 0, 1000, -200, (500, -150)),  # 10 mm:  yakın
            _olcu("yatay", 0, 1000, 3000, (500, 3050)),  # 50 mm:  uzak
            _olcu("yatay", 200, 700, -400, (450, -350)),  # 200 / 700'de özellik yok
        ]
        for cizim in karne.UZAK_CIZIMLER:
            with self.subTest(cizim=cizim):
                self.assertEqual(karne.karne(e, 20, cizim)["uzak_olcu"], [("1000", 50.0), ("500", None)])
        self.assertEqual(karne.karne(e, 20, "kuyu_plani")["uzak_olcu"], [])
        self.assertEqual(karne.karne(e, 20)["uzak_olcu"], [])

    def test_kapi_yazisi_kat_adiyla_ayni_temiz(self):
        #  Kapının yazısı altındaki en yakın kat adıyla aynıysa bulgu yok;  kabinin
        #  arkasında kalan ( yazısız ) kapı sayılmaz
        e = [
            eleman.ad(eleman.yazi(0, 1100, "-1"), "durak_adi"),
            eleman.ad(eleman.yazi(500, 1200, "-1"), "durak_no"),
            eleman.ad(eleman.yazi(0, 4100, "0"), "durak_adi"),
            eleman.ad(eleman.yazi(500, 4200, "0"), "durak_no"),
            eleman.ad(eleman.yazi(0, 7100, "1"), "durak_adi"),
        ]
        self.assertEqual(karne.karne(e, 20)["kapi_no_kat_adi"], [])
        e[3] = eleman.ad(eleman.yazi(500, 4200, "2"), "durak_no")
        self.assertEqual(karne.karne(e, 20)["kapi_no_kat_adi"], [("0", "2")])

    def test_maske_yalniz_once_cizilen_olcuyu_siler(self):
        #  Ölçü yazısının maskesi kendinden önce çizilen ölçünün çizgisini
        #  siler;  sonra çizilen onun üstünden geçer ( maske_olcu_siliyor
        #  saymaz — harfe değiyorsa olcu_yaziyi_kesiyor sayar ).  Ucu ( ölçünün
        #  sınırı ) maskenin altında kalan ölçü de sayılır.
        yazili = _olcu("yatay", 2000, 3000, 0, (2500, 50))
        alttaki = _olcu("yatay", 2400, 2800, 40, (2600, 300))
        self.assertEqual(karne.karne([alttaki, yazili], 20)["maske_olcu_siliyor"][0][0], "1000")
        self.assertEqual(karne.karne([yazili, alttaki], 20)["maske_olcu_siliyor"], [])
        ucu = _olcu("dusey", 80, 600, 2550, (2600, 340))  # çizgisinin 0,2 mm'si maskede
        self.assertEqual(karne.karne([ucu, yazili], 20)["maske_olcu_siliyor"], [("1000", 0.2, 1)])

    def test_yaziya_binen_cizgi_cizim_sirasindan_bagimsiz(self):
        #  Önce çizilen çizgiyi yazının maskesi keser, sonra çizilen yazının
        #  üstünden geçer:  ikisi de kusur ( kuyu dibinde "162,5" "615"in
        #  çizgisindeydi — 26 Eki )
        yazili = _olcu("yatay", 2000, 3000, 0, (2500, 50))
        kesen = _olcu("dusey", -500, 500, 2500, (2550, 300))
        for e in ([yazili, kesen], [kesen, yazili]):
            with self.subTest(ilk=e[0]["yon"]):
                self.assertEqual(karne.karne(e, 20)["olcu_yaziyi_kesiyor"], [("1000", "1000")])

    def test_temiz_cizimde_bulgu_yok(self):
        #  Kot işaretinin üçgeni ölçü çizgisinden kâğıtta 3 mm uzakta
        kot = []
        kesit_parcalari.kot_isareti(kot, 5000, 0, "+1,00", 1.0)
        e = [
            *kot,
            _olcu("dusey", -300, 400, 4900, (4830, 50)),
            eleman.dikdortgen("KABIN", 0, 0, 1000, 1000),
            eleman.yazi(500, 500, "KABİN"),
            _olcu("yatay", 0, 1000, -200, (500, -150)),
            _olcu("yatay", 0, 1000, -300, (500, -250)),
            eleman.yazi(2000, 500, "YAZI"),
            eleman.ok("YAZI", 1900, 500, 1100, 500),
            eleman.dikdortgen("TARAMA", 3000, 0, 1000, 150, tip="tarama"),
            eleman.cizgi("HALAT", 3500, 200, 3500, 900),
        ]
        self.assertEqual(karne.sayilar(e, 20), {})

    def test_maske_kutusu_pdfin_ortusu(self):
        #  Çizimin baktığı kutu PDF'in çizdiği örtüdür:  taban ortanın 0,35 em
        #  altında, alt uzantı 0,21 em, her yanda 0,125 em pay — 90°'de alt
        #  uzantı +x yanına döner
        h, w = 70.0, 200.0
        pay = uslup.maske_payi(h)
        k = uslup.maske_kutusu(0, 0, w, h)
        self.assertAlmostEqual(k[0], -w / 2 - pay)
        self.assertAlmostEqual(k[1], -0.35 * h - 0.21 * h - pay)
        self.assertAlmostEqual(k[3], -0.35 * h + uslup.BUYUK_HARF * h + pay)
        d = uslup.maske_kutusu(0, 0, w, h, aci=90)
        self.assertAlmostEqual(d[2], 0.35 * h + 0.21 * h + pay)
        self.assertAlmostEqual(d[1], -w / 2 - pay)
        #  yazi_kutusu ( ± h / 2 ) maskenin içinde kalmaz:  alt yanda taşar
        el = eleman.yazi(0, 0, "PANO")
        self.assertLess(geometri.maske_kutusu(el)[1], geometri.yazi_kutusu(el)[1])


if __name__ == "__main__":
    unittest.main()


class HalatBetonda(unittest.TestCase):
    """KALİTE PLANI 5. adım ( F5 ):  halat kesilen betonun içinden düz çizgiyle
    geçmez.  Kuyu kesitlerinde betonun içindeki parçası kesik ( görünmeyen kenar —
    ISO 128 ), kesit düzlemindeki delikte döşeme açılır;  kasnak düzenlemesinde
    döşeme halatların deliklerinde kesilir.  Eskiden makine daireli bütün
    düzenlerde 1.482 bulgu ( tarama ).  Halat bölünür ama kısalmaz."""

    DUZENLER = (
        (630, "Sağ", {}),
        (630, "Sol", {"aski_duzeni": "Kabin üstü"}),
        (1000, "Arka", {"aski_duzeni": "Kabin üstü"}),
        (630, "Sağ", {"aski_orani": 1}),
        (1275, "Sol", {}),
    )

    @staticmethod
    def _boy(e, katmanlar):
        return sum(
            ((x["x2"] - x["x1"]) ** 2 + (x["y2"] - x["y1"]) ** 2) ** 0.5
            for x in e
            if x["tip"] == "cizgi" and x.get("katman") in katmanlar and x.get("ad") == "aski_halati"
        )

    def test_halat_betondan_gecmez_ve_kisalmaz(self):
        from unittest import mock

        from cizim import kasnak_duzeni, kuyu_kesiti
        from testler.test_yerlesim_saglamligi import duzen_girdisi, standart_istek

        for Q, yer, ek in self.DUZENLER:
            g, _A, _h = duzen_girdisi(standart_istek(Q, False, yer, **ek))
            for ad, ciz in (
                ("A-A", kuyu_kesiti.yan_kesit),
                ("B-B", kuyu_kesiti.on_kesit),
                ("kasnak", kasnak_duzeni.ciz),
            ):
                with self.subTest(Q=Q, yer=yer, ek=ek, cizim=ad):
                    e = ciz(g)
                    self.assertEqual(karne._halatlar(e, 1.0), [])
                    if ad == "kasnak":
                        continue
                    #  Bölünmeden önceki halat ( gizleme kapalı ) ile aynı boy
                    with mock.patch.object(kesit_parcalari, "betondaki_halati_gizle", lambda e: None):
                        eski = ciz(g)
                    self.assertAlmostEqual(
                        self._boy(e, ("HALAT", "GIZLI")), self._boy(eski, ("HALAT",)), places=3
                    )

    def test_bolme_cizginin_ucunu_ve_adini_korur(self):
        e = [
            eleman.dikdortgen("TARAMA", 0, 100, 500, 200, tip="tarama"),
            eleman.ad(eleman.cizgi("HALAT", 250, 0, 250, 400), "aski_halati"),
        ]
        kesit_parcalari.betondaki_halati_gizle(e)
        parcalar = [(x["katman"], x["y1"], x["y2"]) for x in e if x["tip"] == "cizgi"]
        self.assertEqual(parcalar, [("HALAT", 0, 100), ("GIZLI", 100, 300), ("HALAT", 300, 400)])
        self.assertTrue(all(x.get("ad") == "aski_halati" for x in e if x["tip"] == "cizgi"))


class GorunuslerArasi(unittest.TestCase):
    """Aynı parça planlarda, A-A'da ve B-B'de aynı yerde ( araclar/gorunus — 6 Kas
    çizim denetimi;  26 Eki'de yalnız ağırlık ve tamponlar 96 / 96 bakılmıştı ).
    Taramada da sorun olarak ( araclar/tarama )."""

    def test_altin_duzenlerde_ayni_yerde(self):
        adlar = set()
        for duzen, kayit in altin_cizim.oku().items():
            if "cizimler" not in kayit:
                continue
            cz = {ad: c["elemanlar"] for ad, c in kayit["cizimler"].items()}
            with self.subTest(duzen=duzen):
                self.assertIsNotNone(gorunus.kuyu_genisligi(cz))
                self.assertEqual(gorunus.sorunlar(cz), [])
            for k in gorunus.KESITLER:
                adlar |= set(gorunus.parcalar(cz.get(k, ())))
        #  Karşılaştırma boş geçmesin:  raylar, tamponlar, kabin, ağırlık, kapılar …
        self.assertGreater(len(adlar), 30)

    def test_bozuk_gorunusu_yakalar(self):
        G = 2000.0

        def ray(katman, x0, y0, x1, y1, ad):
            return eleman.ad(eleman.dikdortgen(katman, x0, y0, x1 - x0, y1 - y0), ad)

        cz = {
            "kuyu_plani": [ray("RAY", 0, 500, 100, 600, "kabin_ray")],
            #  A-A:  u = y ( 500 … 600 );  B-B:  u = G − x ( 1.900 … 2.000 )
            "kuyu_kesiti_yan": [ray("RAY", 500, 0, 600, 3000, "kabin_rayi")],
            "kuyu_kesiti_on": [ray("RAY", 1900, 0, 2000, 3000, "kabin_rayi")],
        }
        self.assertEqual(gorunus.sorunlar(cz, G), [])
        #  B-B'de ray 50 kaymış;  A-A'da ray kısa ( sabit parçanın kotu )
        cz["kuyu_kesiti_on"] = [ray("RAY", 1850, 0, 1950, 3000, "kabin_rayi")]
        cz["kuyu_kesiti_yan"] = [
            ray("RAY", 500, 0, 600, 3000, "kabin_rayi"),
            ray("RAY", 500, 3000, 600, 3500, "kabin_rayi"),
        ]
        s = gorunus.sorunlar(cz, G)
        self.assertEqual(len(s), 2, s)
        self.assertTrue(s[0].startswith("kuyu_kesiti_on: Kabin rayı"), s)
        self.assertTrue(s[1].startswith("A-A ↔ B-B: Kabin rayı"), s)
