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
tutulur:  sayıları kayıttan artamaz ( KaliteKarnesi;  26 Eki kalite denetimi )."""

import collections
import unittest

from araclar import karne
from cizim import eleman
from cizim import geometri
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
        ]
        b = karne.karne(e, 20)
        for kural in karne.KURALLAR:
            with self.subTest(kural=kural):
                self.assertEqual(len(b[kural]), 1, b[kural])

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
        e = [
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
