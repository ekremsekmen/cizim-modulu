"""ÇİZİM ŞERİDİNİN ADLARI ( 20 Kas — yayın öncesi arayüz taslağı B7 ).

Ekranın tuvalinin altındaki şerit her çizimi bir düğmeyle açar.  Ad başlıktan türetiliyordu:
sorunlu kipte düşey kesitler kurulamayınca başlıklardaki seviye harfi ( C-C … ) düşer ve kuyu
planı, kuyu dibi, delik planı üçü de "Kuyu" oluyordu.  Artık her çizim kısa adını kimliğinden
taşır ( cizimler.KISA_ADLAR — /api/uygulama/cizimler'in "kisa"sı );  ekran harfi başlıktan
ayrıca okur.  Burada:  her çizimin adı var, hiçbir düzende iki düğme aynı adı taşımaz."""

import re
import unittest

from cizim import cizimler
from cizim import grup
from testler.test_grup import ikili, yanit
from testler.test_olcu_kaynagi import _veri

HARF = re.compile(r"(?:^|\s)([A-ZÇĞİÖŞÜ]-[A-ZÇĞİÖŞÜ])(?=\s|$)")


def serit_adlari(d):
    """Şeritte görünen adlar ( ekran:  CizimSeridi — harf varsa önünde )."""
    out = []
    for c in d["cizimler"]:
        h = HARF.search(c["baslik"].partition("(")[0])
        out.append(f"{h.group(1)} {c['kisa']}" if h else c["kisa"])
    return out


class KisaAdlar(unittest.TestCase):
    def test_her_cizimin_adi_var_ve_tek(self):
        self.assertEqual(set(cizimler.KISA_ADLAR), set(cizimler.CIZIMLER))
        adlar = list(cizimler.KISA_ADLAR.values()) + [grup.KISA]
        self.assertEqual(len(adlar), len(set(adlar)))
        #  Seviye harfi adda değil ( başlıktan ayrıca okunur )
        self.assertFalse([a for a in adlar if HARF.search(a)])

    def test_duzenlerde_adlar_tek(self):
        vakalar = {
            "MRL": _veri(),
            "makine daireli": _veri(True),
            #  Sorunlu kip:  kesitler kurulamaz, başlıklarda harf yok ( eskiden üç "Kuyu" )
            "sorunlu": _veri(kuyu_genisligi=1600),
            "tek kuyu": ikili(),
        }
        for ad, v in vakalar.items():
            with self.subTest(ad):
                d = yanit(v)
                self.assertTrue(d["cizimler"], d.get("hata"))
                self.assertTrue(all(c["kisa"] for c in d["cizimler"]), [c["ad"] for c in d["cizimler"]])
                s = serit_adlari(d)
                self.assertEqual(len(s), len(set(s)), s)
        #  Sorunlu kipte harf gerçekten düşer:  adlar yine ayrı
        d = yanit(vakalar["sorunlu"])
        self.assertFalse(d["aktif"])
        self.assertIn("Kuyu planı", serit_adlari(d))
        #  Tek kuyuda kuyunun ortak planı kendi adıyla
        self.assertIn(grup.KISA, [c["kisa"] for c in yanit(vakalar["tek kuyu"])["cizimler"]])


if __name__ == "__main__":
    unittest.main()
