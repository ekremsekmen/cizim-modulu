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

Ölçümün ayrıntılı dökümü:  cikti/araclar/kalite_karnesi.py ( git dışı )."""

import collections
import unittest

from cizim import geometri
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


def karne(e, olcek):
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
                bulgu = karne(c["elemanlar"], c["olcek"])
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
        bulgu = karne(e, 20)
        for kural in ("yazı yazıya", "tekrar", "parça kenarına", "alan yazısı taşar"):
            self.assertTrue(bulgu[kural], kural)


if __name__ == "__main__":
    unittest.main()
