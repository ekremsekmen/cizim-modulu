"""KÂĞIT ENİ ( 19 Kas, kullanıcı:  "projeyi indirirken 60 cm ya da 90 cm seçebilmeliyim … hiç bir şey
bozulmasın" ) — taslak projelerde ve ofisin gerçek projelerinde İKİ ENLE paftanın yerleşimi:

  · binme yok:  hesap sayfaları, elektrik projeleri, kapak hücresi, notlar ve çizimler birbirine binmez
    ( çizimler arasında en az pafta.ARA );
  · taşma yok:  hepsi çerçevenin içinde, çizimler çerçeveden KENAR içeride, her sütun kâğıda sığar;
  · çizimlerin içi aynı:  yerleşim yalnız öteler — iki kâğıtta çizimler birebir aynı;  tek ayrım düşey
    kesitin kırığı ( kullanıcı 19 Kas:  "sığıyorsa zaten kırılmasına gerek yok" — 90 cm'de 880 mm'ye
    dek kırılmaz;  kırılırsa en az 60 cm'deki kadar uzun kalır );
  · yerleşim belirli ( aynı girdi → aynı yerler ) ve milisaniyenin altında.

HAFİF:  her proje bir kez hesaplanır, çizimleri her kâğıda bir kez kurulur;  yerleşim saf geometridir
( pafta.yerlesim, dxf_cikti._yerlesim ) — DXF / PDF yazılmaz.  Paketin DXF'inde blokların aynılığı ve
INSERT'lerin yalnız ötelemesi test_pdf.Serit'te ( bir proje, iki en )."""

import copy
import itertools
import json
import time
import unittest

from cizim import elektrik, geometri, pafta
from ciktilar import dxf_cikti
from motor.uygulama import uygulama_hesabi
from testler import altin_cizim
from testler.test_gercek_projeler import CIZILENLER
from testler.test_taslaklar import TASLAKLAR, istek
from testler.test_yerlesim_saglamligi import standart_istek
from uclar import cizim_uclari, uygulama_istegi

#  Kâğıda göre kırılan çizimler ( pafta.cizim_listesi:  azami = sütunun yüksekliği × 50 )
KESITLER = ("kuyu_kesiti_yan", "kuyu_kesiti_on")
#  Asansör başına hesap sayfası:  uygulama projesinin PDF'i 1000 kg MRL'de 22 sayfa ( 19 Kas ölçümü );
#  ızgara sayfanın içeriğine bakmaz, yalnız sayısına
SAYFA = 22


def _projeler():
    d = {f"taslak {t['kimlik']}": istek(t) for t in TASLAKLAR}
    duzen = altin_cizim.duzenler()
    for ad in [*CIZILENLER, "BAR 2515"]:
        d[f"gerçek {ad}"] = duzen[f"gerçek {ad}"]
    #  8 durak, 21 m:  kesit 60 cm'de kırılır, 90 cm'de tam sığar
    d["standart 1000 MRL"] = standart_istek(1000, True, "Sağ")
    #  İki asansör:  her birinin çizimleri ayrı sütunlarda ( pafta._sutunlar gruplar )
    iki = standart_istek(1000, True, "Sağ")
    iki["asansorler"].append(standart_istek(630, True, "Sağ")["asansorler"][0])
    d["iki asansör"] = iki
    return d


def _gler(veri):
    """Paketin çizim girdileri ( uygulama_uclari._uygulama_paketi gibi:  hesapla birlikte )."""
    v = copy.deepcopy(veri)
    asansorler, ortak = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
    s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    cizim = cizim_uclari.girdiler(v, asansorler, ortak, s, "KAGIT ENI")
    return [g for g, _h in cizim], [h for _g, hata in cizim for h in hata]


def _iz(e):
    """Çizimin elemanlarının parmak izi ( sıra dahil )."""
    return json.dumps(e, sort_keys=True, default=str)


def _kutular(liste):
    """( ad , grup , ölçek , ( en , boy ) pafta mm'si , parmak izi )."""
    out = []
    for grup, (ad, _baslik, olcek, e) in liste:
        x0, y0, x1, y1 = geometri.sinir(e)
        out.append((ad, grup, olcek, ((x1 - x0) / olcek, (y1 - y0) / olcek), _iz(e)))
    return out


def _ortusur(a, b, pay=0.0):
    return (
        a[0] < b[2] + pay - 1e-6
        and b[0] < a[2] + pay - 1e-6
        and a[1] < b[3] + pay - 1e-6
        and b[1] < a[3] + pay - 1e-6
    )


class KagitEni(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = {}
        for ad, veri in _projeler().items():
            gler, hata = _gler(veri)
            cls.S[ad] = (
                len(gler),
                hata,
                {k: _kutular(pafta._gruplu_bloklar(gler, k)) for k in pafta.KAGIT_ENLERI} if not hata else {},
            )

    def _yerlesim(self, ad, kagit):
        """Şeridin bütün kutuları:  ( çizimler [ ( ad, kutu ) ] , öbürleri [ ( ad, kutu ) ] , çerçevenin sağı )."""
        adet, _hata, cizimler = self.S[ad]
        sayfa, ayrilan = SAYFA * adet, elektrik.HUCRE * adet
        a4, tasti = dxf_cikti._yerlesim(sayfa, ayrilan, kagit)
        self.assertFalse(tasti)
        ey = dxf_cikti.elektrik_yerleri(sayfa, adet, kagit)
        liste = cizimler[kagit]
        yerler, sag = pafta.yerlesim(
            [b for _a, _g, _o, b, _i in liste],
            dxf_cikti.izgara_sagi(sayfa, ayrilan, kagit),
            kagit,
            [g for _a, g, _o, _b, _i in liste],
        )
        ciz = [(a, (x, y, x + b[0], y + b[1])) for (a, _g, _o, b, _i), (x, y) in zip(liste, yerler)]
        obur = [(f"A4 {i}", (x, y, x + dxf_cikti.A4_G, y + dxf_cikti.A4_Y)) for i, (x, y) in enumerate(a4)]
        obur += [(f"elektrik {i}", (x, y, x + elektrik.EN, y + elektrik.BOY)) for i, (x, y) in enumerate(ey)]
        obur += [
            ("kapak hücresi", pafta.KAPAK_HUCRESI),
            ("notlar", (pafta.BANT[0], pafta.KAPAK_HUCRESI[3], pafta.SERBEST[0], pafta.ust_kenar(kagit))),
        ]
        return ciz, obur, sag

    def test_cizimler_kurulur(self):
        for ad, (_n, hata, _c) in self.S.items():
            with self.subTest(ad):
                self.assertEqual(hata, [])

    def test_binme_ve_tasma_yok(self):
        for ad, kagit in itertools.product(self.S, pafta.KAGIT_ENLERI):
            with self.subTest(ad, kagit=kagit):
                ciz, obur, sag = self._yerlesim(ad, kagit)
                alt, ust = pafta.BANT[1], pafta.ust_kenar(kagit)
                #  Çerçeve:  hesap ızgarasının sağından ( SOL_PAY ) ve son çizimden ( KENAR ) kısa değil
                self.assertGreaterEqual(sag, max(k[2] for _a, k in obur) + dxf_cikti.SOL_PAY - 1e-6)
                for a, k in obur:
                    self.assertTrue(
                        pafta.BANT[0] - 1e-6 <= k[0]
                        and k[2] <= sag + 1e-6
                        and alt - 1e-6 <= k[1]
                        and k[3] <= ust + 1e-6,
                        (a, k),
                    )
                for a, k in ciz:
                    #  Sütuna sığmayan tek çizim ( en kısa kırık hâli bile uzun kesit — gerçek 800 KG 60 cm'de
                    #  583,9 mm ):  çerçevenin dikey ortasında, payı üstte ve altta eşit, çerçevenin içinde
                    h = k[3] - k[1]
                    pay = pafta.KENAR if h <= pafta.cizim_yuksekligi(kagit) + 1e-6 else (kagit - h) / 2
                    self.assertGreater(pay, 0.0, (a, h))
                    self.assertTrue(
                        k[2] <= sag - pafta.KENAR + 1e-6
                        and k[1] >= alt + pay - 1e-6
                        and k[3] <= ust - pay + 1e-6,
                        (a, k, sag),
                    )
                for (a, k), (b, m) in itertools.combinations(ciz, 2):
                    self.assertFalse(_ortusur(k, m, pafta.ARA), (a, b))
                for (a, k), (b, m) in itertools.product(ciz, obur):
                    self.assertFalse(_ortusur(k, m, pafta.KENAR), (a, b))
                for (a, k), (b, m) in itertools.combinations(obur, 2):
                    self.assertFalse(_ortusur(k, m), (a, b))

    def test_cizimlerin_ici_ayni(self):
        """İki kâğıtta aynı çizimler, aynı sırada, aynı ölçekte;  kesitler dışında birebir aynı ( yalnız
        öteleme ).  Kesit 90 cm'de kısalmaz ( en az 60 cm'deki kadar ), 90 cm'de sütununa sığar;  60 cm'de
        en kısa kırık hâli bile sütundan uzunsa çerçeveye sığar ( test_binme_ve_tasma_yok:  ortada )."""
        for ad, (_n, _h, c) in self.S.items():
            with self.subTest(ad):
                k6, k9 = c[600], c[900]
                self.assertEqual([(a, g, o) for a, g, o, _b, _i in k6], [(a, g, o) for a, g, o, _b, _i in k9])
                for (a, _g, _o, b6, i6), (_a, _g9, _o9, b9, i9) in zip(k6, k9):
                    #  Asansörün ( kuyu_kesiti_yan_2 ) ve kuyu grubunun kesitleri de
                    if "kuyu_kesiti" in a:
                        self.assertGreaterEqual(b9[1], b6[1] - 1e-6, a)
                        self.assertLessEqual(b9[1], pafta.cizim_yuksekligi(900) + 1e-6, a)
                        self.assertLess(b6[1], 600.0, a)
                    else:
                        self.assertEqual(i6, i9, a)

    def test_kesit_siginca_kirilmaz(self):
        """8 duraklı 21 m'lik düzen:  60 cm'de kesit kırık ( 580 mm'ye sığmaz ), 90 cm'de bütün katlarıyla —
        daha uzun ve 880 mm'nin altında."""
        _n, _h, c = self.S["standart 1000 MRL"]
        for (a, _g, _o, b6, _i6), (_a9, _g9, _o9, b9, _i9) in zip(c[600], c[900]):
            if a in KESITLER:
                self.assertGreater(b9[1], pafta.cizim_yuksekligi(600), a)
                self.assertGreater(b9[1], b6[1] + 1.0, a)

    def test_90_cm_seridi_kisa(self):
        for ad in self.S:
            with self.subTest(ad):
                self.assertLess(self._yerlesim(ad, 900)[2], self._yerlesim(ad, 600)[2])

    def test_yerlesim_belirli_ve_hizli(self):
        for ad, kagit in itertools.product(self.S, pafta.KAGIT_ENLERI):
            with self.subTest(ad, kagit=kagit):
                liste = self.S[ad][2][kagit]
                boyutlar, gruplar = [b for _a, _g, _o, b, _i in liste], [g for _a, g, _o, _b, _i in liste]
                bas = time.perf_counter()
                bir = pafta.yerlesim(boyutlar, None, kagit, gruplar)
                sure = time.perf_counter() - bas
                self.assertEqual(bir, pafta.yerlesim(boyutlar, None, kagit, gruplar))
                #  Ölçülen ~0,01 ms;  sınır yavaş CI makinesine pay bırakır
                self.assertLess(sure, 0.05)


if __name__ == "__main__":
    unittest.main()
